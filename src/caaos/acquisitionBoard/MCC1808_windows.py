#!/bin/python

# -*- coding: utf-8 -*-

"""
Windows version of MCC1808.py. It exposes the same classes, methods and arguments
but uses the mcculw module (Universal Library) instead of uldaq.
"""

from __future__ import print_function

import ctypes
import time

import numpy as np
from mcculw import ul as uldaq
from mcculw.device_info import DaqDeviceInfo
from mcculw.enums import AnalogInputMode, FunctionType, InterfaceType, ScanOptions, Status, ULRange

from caaos.tools import tools


_AI_RANGES = {'BIP10VOLTS': ULRange.BIP10VOLTS,
              'BIP5VOLTS': ULRange.BIP5VOLTS,
              'UNI10VOLTS': ULRange.UNI10VOLTS,
              'UNI5VOLTS': ULRange.UNI5VOLTS}


def _displayScanOptions(bit_mask):
    """Create a displays string for all scan options."""
    options = [option.name for option in ScanOptions if option and (option & bit_mask) == option]
    if not options:
        options.append('DEFAULTIO')
    return ', '.join(options)


class _DaqDevice():
    """Thin wrapper around a board number created in the Universal Library."""

    def __init__(self, boardNum, descriptor):
        self.boardNum = boardNum
        self.descriptor = descriptor
        self.connected = False

    def get_descriptor(self):
        return self.descriptor

    def get_ai_device(self):
        return self if DaqDeviceInfo(self.boardNum).supports_analog_input else None

    def get_ao_device(self):
        return self if DaqDeviceInfo(self.boardNum).supports_analog_output else None

    def connect(self):
        # In mcculw the connection is established when the device is created
        self.connected = True

    def is_connected(self):
        return self.connected

    def disconnect(self):
        self.connected = False

    def release(self):
        uldaq.release_daq_device(self.boardNum)


class MCC1808_analogIn():
    def __init__(self, daqDevice):
        self.daqDevice = daqDevice
        self.device = self.getDevice()

        # scaled data (volts), acquisition runs in background
        self.scanOptions = ScanOptions.BACKGROUND | ScanOptions.SCALEDATA
        self.memHandle = None

    def getDevice(self):
        # Get the Analog In device object and verify that it is valid.
        try:
            # Get the AiDevice object and verify that it is valid.
            device = self.daqDevice.get_ai_device()
            if device is None:
                raise RuntimeError('Error: The DAQ device does not support analog input')

        except RuntimeError as error:
            device = None
            print('\n', error)

        return device

    def __displayScanOptions(self, bit_mask):
        return _displayScanOptions(bit_mask)

    def __freeBuffer(self):
        if self.memHandle:
            uldaq.win_buf_free(self.memHandle)
            self.memHandle = None

    def confChannelQueue(self, channelConfList=[{'channel': 0, 'inputMode': 'SE', 'range': 'BIP10VOLTS'}], sampleRate=100, nSamplesPerChannel=1000):
        """
        Configures the Analog Input Channel queue list
        Parameters
        ----------
        channelConfList: list of dictionaries with the following keys:
            channel: channel number
            inputMode: 'SE' (single ended) or 'DIFF' (diffential)
            range: range of values to be read
                    "BIP10VOLTS": -10 to +10 Volts
                    "BIP5VOLTS" :  -5 to  +5 Volts
                    "UNI10VOLTS":   0 to +10 Volts
                    "UNI5VOLTS" :   0 to  +5 Volts

            Ex: [{'channel':0, 'inputMode'=>'SE', 'range':'BIP10VOLTS', 'rate':100},
                 {'channel':1, 'inputMode'=>'DIFF', 'range':'BIP10VOLTS', 'rate':100}]

        sampleRate: sampling rate in Hz (200k maximum
        nSamplesPerChannel: number of samples per channel
        """
        boardNum = self.device.boardNum
        AiInfo = DaqDeviceInfo(boardNum).get_ai_info()
        self.channelConf = channelConfList
        self.sampleRate = sampleRate
        self.nSamplesPerChannel = nSamplesPerChannel
        self.nChannels = len(channelConfList)

        chanList = []
        gainList = []

        for chConf in self.channelConf:
            try:
                # Input Mode
                if chConf['inputMode'].upper() == 'SE':
                    inputMode = AnalogInputMode.SINGLE_ENDED
                    validChannelMax = AiInfo.num_chans
                elif chConf['inputMode'].upper() == 'DIFF':
                    inputMode = AnalogInputMode.DIFFERENTIAL
                    validChannelMax = AiInfo.num_chans // 2
                else:
                    raise RuntimeError('Error: Invalid input mode %s' % chConf['inputMode'])

                # channel number
                if chConf['channel'] > validChannelMax - 1:
                    raise RuntimeError(
                      'Error: The DAQ device does not support channel %d input. Maximum is %d ' % (chConf['channel'], validChannelMax - 1))

                # Range
                if chConf['range'].upper() not in _AI_RANGES:
                    raise RuntimeError('Error: Invalid range %s' % chConf['range'])

                uldaq.a_chan_input_mode(boardNum, chConf['channel'], inputMode)
                chanList.append(chConf['channel'])
                gainList.append(_AI_RANGES[chConf['range'].upper()])

            except RuntimeError as error:
                print('\n', error)

        # Load configuration queue
        uldaq.a_load_queue(boardNum, chanList, gainList, len(chanList))
        self.chanList = chanList
        self.gainList = gainList

        # create buffer array (scaled data: 64 bits float)
        self.__freeBuffer()
        nPoints = self.nChannels * self.nSamplesPerChannel
        self.memHandle = uldaq.scaled_win_buf_alloc(nPoints)
        if not self.memHandle:
            raise RuntimeError('Error: Failed to allocate memory for the analog input buffer')

        self.dataArray = ctypes.cast(self.memHandle, ctypes.POINTER(ctypes.c_double))

        for i in range(nPoints):
            self.dataArray[i] = 0.0

        # this array shares memory with the buffer so we can read this instead as a numpy array
        self.dataArrayNP = np.ctypeslib.as_array(self.dataArray, shape=(nPoints,)).reshape(self.nChannels, self.nSamplesPerChannel, order='F')

        print('---- Analog input channel queue configuration ----')
        print('Scan options: ', self.__displayScanOptions(self.scanOptions))
        print('Sample Rate (per second)  : ', self.sampleRate)
        print('Nbr of samples per channel: ', self.nSamplesPerChannel)
        for chConf in self.channelConf:
            print(' --> Channel: %d, Input Mode: %s, Range:%s' % (chConf['channel'], chConf['inputMode'], chConf['range']))
        print('------------------------------------')

    def readData(self, flagWait=False):
        # Start the acquisition.
        #
        # When using the queue, the low_channel and high_channel parameters are
        # ignored since they are specified in the queue.
        dummy = 0
        self.actualRate = uldaq.a_in_scan(self.device.boardNum, dummy, dummy, self.nChannels * self.nSamplesPerChannel, int(self.sampleRate),
                                       self.gainList[0], self.memHandle, int(self.scanOptions))

        if flagWait:
            print('AI device data read - Please wait')
            while self.getstatus()[0] == 1:
                time.sleep(0.01)
            print('done!')

    def getstatus(self):
        """
        Status:
           status==0 Idle
           status==1 Running

        transferStatus: progress of a scan operation.
            current_index: The index into the data buffer immediately following the last sample transferred.
            current_total_count: The total number of samples transferred since the scan started.
            current_scan_count: The number of samples per channel transferred since the scan started.
        """

        status, current_total_count, current_index = uldaq.get_status(self.device.boardNum, FunctionType.AIFUNCTION)
        current_scan_count = current_total_count // self.nChannels

        return int(status == Status.RUNNING), current_scan_count, current_index, current_total_count

    def stopRead(self):
        uldaq.stop_background(self.device.boardNum, FunctionType.AIFUNCTION)


class MCC1808_analogOut():
    def __init__(self, daqDevice):
        self.daqDevice = daqDevice
        self.device = self.getDevice()

        self.memHandle = None

    def getDevice(self):
        # Get the Analog Out device object and verify that it is valid.
        try:
            # Get the AoDevice object and verify that it is valid.
            device = self.daqDevice.get_ao_device()
            if device is None:
                raise RuntimeError('Error: The DAQ device does not support analog output')

        except RuntimeError as error:
            device = None
            print('\n', error)

        return device

    def __displayScanOptions(self, bit_mask):
        return _displayScanOptions(bit_mask)

    def confChannelScan(self, signals=np.array([0, 1, 2]), sampleRate=100, continuous=False, zeroEnd=True):
        """
        Configures the Analog Input Channel queue list
        Parameters
        ----------
        signals: numpy array with the signals. The limits of the DAC is +-10V
                1D array (nSamples):   one channel
                2D array (nChannel x nSamples): multiple channels


        sampleRate: sampling rate in Hz (500k maximum)
        continuous: continuous mode. If True, signals is sent to the output in infinite loop. To stop you need to call the function self.stop()
        zeroEnd: add a 0.0 sample after the last sample of the signal. used only when continuous=False
        """
        AoInfo = DaqDeviceInfo(self.device.boardNum).get_ao_info()
        self.signals = signals
        self.sampleRate = sampleRate
        self.range = ULRange.BIP10VOLTS

        self.scanOptions = ScanOptions.BACKGROUND | ScanOptions.SCALEDATA
        if continuous:
            self.scanOptions |= ScanOptions.CONTINUOUS

        # channel number
        try:
            if signals.ndim == 1:
                self.nChannels = 1
                self.nSamplesPerChannel = self.signals.shape[0]
            else:
                self.nChannels = 2
                self.nSamplesPerChannel = self.signals.shape[1]

            if self.nChannels > AoInfo.num_chans:
                raise RuntimeError('Error: The DAQ device does not support %d output channels. Maximum is %d ' % (self.nChannels, AoInfo.num_chans))

            if zeroEnd and not continuous:
                if self.nChannels == 1:
                    self.signals = np.append(self.signals, 0.0)
                if self.nChannels == 2:
                    self.signals = np.hstack((self.signals, np.zeros((self.nChannels, 1))))
                self.nSamplesPerChannel += 1

        except RuntimeError as error:
            print('\n', error)

        # create buffer array (scaled data: 64 bits float)
        if self.memHandle:
            uldaq.win_buf_free(self.memHandle)
            self.memHandle = None

        nPoints = self.nChannels * self.nSamplesPerChannel
        self.memHandle = uldaq.scaled_win_buf_alloc(nPoints)
        if not self.memHandle:
            raise RuntimeError('Error: Failed to allocate memory for the analog output buffer')

        self.dataArray = ctypes.cast(self.memHandle, ctypes.POINTER(ctypes.c_double))

        # flattening array, column=major
        signalFlattened = self.signals.flatten('F')
        for i, x in enumerate(signalFlattened):
            self.dataArray[i] = x

        print('---- Analog output channel configuration ----')
        print('Scan options: ', self.__displayScanOptions(self.scanOptions))
        print('Sample Rate (per second)  : ', self.sampleRate)
        print('Nbr of samples per channel: ', self.nSamplesPerChannel)
        print('------------------------------------')

        self.zeroOutput()

    def writeData(self, flagWait=False):
        # Start signal generation

        self.actualRate = uldaq.a_out_scan(self.device.boardNum, 0, self.nChannels - 1, self.nChannels * self.nSamplesPerChannel, self.sampleRate,
                                        self.range, self.memHandle, int(self.scanOptions))

        if flagWait:
            print('AO device data write - Please wait')
            while self.getstatus()[0] == 1:
                time.sleep(0.01)
            print('done!')

    def loadDataFrom_EXP(self, fileName, channels=[0, 1]):
        """
        Load data from a file
        """
        [dir, name, ext] = tools.splitPath(fileName)

        if ext[1:].upper() in ['EXP', 'DAT']:
            with open(fileName, 'r') as file:
                line = ''
                # extract sampling frequency in Hz
                while not line.startswith('Sampling Rate'):
                    line = file.readline()

                samplingRate_Hz = float(line.split()[2].replace(',', '.').replace('Hz', ''))

                # the next line should contain labels
                signalLabels = file.readline().rstrip().replace(' ', '_').replace('.', '').split('\t')
                nChannels = len(signalLabels) - 2

            headerSize = 7

            # create dtype of the file
            dtypes = ('U11', 'i4')  # col 0: time (11 char string)   col 1: frame (32 bit int)
            dtypes = dtypes + ('f8',) * nChannels  # the other columns will be treated as float (8bits)

            rawData = np.genfromtxt(fileName, delimiter=None, skip_header=headerSize - 1, autostrip=True, names=','.join(signalLabels), dtype=dtypes)

            # remove first two columns of array (time stamp and sample #)
            names = list(rawData.dtype.names)[2:]

            signals = []
            for i in range(len(names)):
                signals.append(rawData[names[i]])

            signals = np.array(signals)

        else:
            print('File extension not supported')
            return None, None

        return signals[channels, :], samplingRate_Hz

    def normalizeData(self, data, maxV=10.0):

        if data.ndim == 1:
            absMax = np.absolute(data).max()
            data = (maxV / absMax) * data

        if data.ndim > 1:
            for i in range(data.shape[0]):
                absMax = np.absolute(data[i]).max()
                data[i] = (maxV / absMax) * data[i]

        return data

    def zeroOutput(self):
        for ch in range(self.nChannels):
            uldaq.v_out(self.device.boardNum, ch, self.range, 0.0)

    def stopWrite(self):
        uldaq.stop_background(self.device.boardNum, FunctionType.AOFUNCTION)

    def getstatus(self):
        """
        Status:
           status==0 Idle
           status==1 Running

        transferStatus: progress of a scan operation.
            current_index: The index into the data buffer immediately following the last sample transferred.
            current_total_count: The total number of samples transferred since the scan started.
            current_scan_count: The number of samples per channel transferred since the scan started.
        """
        status, current_total_count, current_index = uldaq.get_status(self.device.boardNum, FunctionType.AOFUNCTION)
        current_scan_count = current_total_count // self.nChannels

        return int(status == Status.RUNNING), current_scan_count, current_index, current_total_count


class MCC1808():
    def __init__(self):
        self.boardNum = 0
        self.DAQdevice = self.getDevice()
        self.AiDevice = MCC1808_analogIn(self.DAQdevice)
        self.AoDevice = MCC1808_analogOut(self.DAQdevice)

    def getDevice(self):
        # Get the DAQ device object and verify that it is valid.
        interface_type = InterfaceType.ANY

        try:
            # Get descriptors for all of the available DAQ devices.
            uldaq.ignore_instacal()
            devices = uldaq.get_daq_device_inventory(interface_type)
            number_of_devices = len(devices)
            if number_of_devices == 0:
                raise RuntimeError('Error: No DAQ devices found')

            print('Found', number_of_devices, 'DAQ device(s):')
            for i in range(number_of_devices):
                print('  [', i, '] ', devices[i].product_name, ' (', devices[i].unique_id, ')', sep='')

            if number_of_devices > 1:
                descriptor_index = input('\nPlease select a DAQ device, enter a number' + ' between 0 and ' + str(number_of_devices - 1) + ': ')
                descriptor_index = int(descriptor_index)
                if descriptor_index not in range(number_of_devices):
                    raise RuntimeError('Error: Invalid descriptor index')
            else:
                descriptor_index = 0

            # Create the DAQ device from the descriptor at the specified index.
            uldaq.create_daq_device(self.boardNum, devices[descriptor_index])
            #daqDevice = _DaqDevice(self.boardNum, devices[descriptor_index])
            #print(daqDevice.descriptor.product_name)

        except (RuntimeError, uldaq.ULError) as error:
            print('\n', error)
            exit()

        return DaqDeviceInfo(self.boardNum)

    def disconnect(self):

        print('\nStopping', self.descriptor.dev_string, '- please wait...')

        # Stop the acquisition if it is still running.
        if hasattr(self.AiDevice, 'nChannels') and self.AiDevice.getstatus()[0] == 1:
            print('Stopping AI Device data collection - please wait...')
            self.AiDevice.stopRead()

        # Stop the signal generation if it is still running.
        if hasattr(self.AoDevice, 'nChannels') and self.AoDevice.getstatus()[0] == 1:
            print('Stopping AO Device data generation - please wait...')
            self.AoDevice.stopWrite()

        for dev in (self.AiDevice, self.AoDevice):
            if dev.memHandle:
                uldaq.win_buf_free(dev.memHandle)
                dev.memHandle = None

        if self.DAQdevice.is_connected():
            print('Disconnecting DAQ device - please wait...')
            self.DAQdevice.disconnect()

        print('Releasing DAQ device - please wait...')
        self.DAQdevice.release()
        print('Done!')
