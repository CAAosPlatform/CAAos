#!/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

import numpy as np
import uldaq

from caaos.tools import tools


class MCC1808_analogIn():
    def __init__(self, daqDevice):
        self.daqDevice = daqDevice
        self.device = self.getDevice()

        self.scanOptions = uldaq.ScanOption.DEFAULTIO
        self.flags = uldaq.AInScanFlag.DEFAULT  # User data should be in scaled format (usually volts).

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
        """Create a displays string for all scan options."""
        options = []
        if bit_mask == uldaq.ScanOption.DEFAULTIO:
            options.append(uldaq.ScanOption.DEFAULTIO.name)
        for option in uldaq.ScanOption:
            if option & bit_mask:
                options.append(option.name)
        return ', '.join(options)

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
        AiInfo = self.device.get_info()
        self.channelConf = channelConfList
        self.sampleRate = sampleRate
        self.nSamplesPerChannel = nSamplesPerChannel
        self.nChannels = len(channelConfList)

        configQueueList = []

        for chConf in self.channelConf:
            queueElement = uldaq.AiQueueElement()

            try:
                # Input Mode
                if chConf['inputMode'].upper() == 'SE':
                    queueElement.input_mode = uldaq.AiInputMode.SINGLE_ENDED
                if chConf['inputMode'].upper() == 'DIFF':
                    queueElement.input_mode = uldaq.AiInputMode.DIFFERENTIAL

                # channel number
                validChannelMax = AiInfo.get_num_chans_by_mode(queueElement.input_mode)
                if chConf['channel'] > validChannelMax - 1:
                    raise RuntimeError(
                      'Error: The DAQ device does not support channel %d input. Maximum is %d ' % (chConf['channel'], validChannelMax - 1))

                queueElement.channel = chConf['channel']

                # Range
                if chConf['range'].upper() == 'BIP10VOLTS':
                    queueElement.range = uldaq.Range.BIP10VOLTS
                if chConf['range'].upper() == 'BIP5VOLTS':
                    queueElement.range = uldaq.Range.BIP5VOLTS
                if chConf['range'].upper() == 'UNI10VOLTS':
                    queueElement.range = uldaq.Range.UNI10VOLTS
                if chConf['range'].upper() == 'UNI5VOLTS':
                    queueElement.range = uldaq.Range.UNI5VOLTS

                configQueueList.append(queueElement)

            except RuntimeError as error:
                print('\n', error)

        # Load configuration queuehas_pacer
        self.device.a_in_load_queue(configQueueList)

        # create buffer array
        self.dataArray = uldaq.create_float_buffer(number_of_channels=self.nChannels, samples_per_channel=self.nSamplesPerChannel)

        for i in range(self.nChannels * self.nSamplesPerChannel):
            self.dataArray[i] = 0.0

        # this array shares memory with the buffer so we can read this instead as a numpy array
        self.dataArrayNP = np.ctypeslib.as_array(self.dataArray).reshape(self.nChannels, self.nSamplesPerChannel, order='F')

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
        # When using the queue, the low_channel, high_channel, input_mode, and
        # range parameters are ignored since they are specified in queue_array.
        dummy = 0
        self.actualRate = self.device.a_in_scan(low_channel=dummy, high_channel=dummy, input_mode=dummy, analog_range=dummy,
                                                samples_per_channel=self.nSamplesPerChannel, rate=self.sampleRate, options=self.scanOptions,
                                                flags=self.flags, data=self.dataArray)

        if flagWait:
            print('AI device data read - Please wait')
            self.device.scan_wait(wait_type=uldaq.WaitType.WAIT_UNTIL_DONE, timeout=-1)
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

        status, transferStatus = self.device.get_scan_status()
        if False:
            print('Collected samples (all channels) = ', transferStatus.current_total_count)
            print('Collected samples per channel = ', transferStatus.current_scan_count)
            print('current Buffer Idx = ', transferStatus.current_index, '\n')

        return status, transferStatus.current_scan_count, transferStatus.current_index, transferStatus.current_total_count

    def stopRead(self):
        self.device.scan_stop()


class MCC1808_analogOut():
    def __init__(self, daqDevice):
        self.daqDevice = daqDevice
        self.device = self.getDevice()

        self.flags = uldaq.AOutScanFlag.DEFAULT  # User data should be in scaled format (usually volts).

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
        """Create a displays string for all scan options."""
        options = []
        if bit_mask == uldaq.ScanOption.DEFAULTIO:
            options.append(uldaq.ScanOption.DEFAULTIO.name)
        for option in uldaq.ScanOption:
            if option & bit_mask:
                options.append(option.name)
        return ', '.join(options)

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
        AoInfo = self.device.get_info()
        self.signals = signals
        self.sampleRate = sampleRate
        self.range = uldaq.Range.BIP10VOLTS

        if continuous:
            self.scanOptions = uldaq.ScanOption.CONTINUOUS
        else:
            self.scanOptions = uldaq.ScanOption.DEFAULTIO

        # channel number
        try:
            if signals.ndim == 1:
                self.nChannels = 1
                self.nSamplesPerChannel = self.signals.shape[0]
            else:
                self.nChannels = 2
                self.nSamplesPerChannel = self.signals.shape[1]

            if self.nChannels > AoInfo.get_num_chans():
                raise RuntimeError('Error: The DAQ device does not support channel %d output. Maximum is %d ' % (chConf['channel'], validChannelMax))

            if zeroEnd and not continuous:
                if self.nChannels == 1:
                    self.signals = np.append(self.signals, 0.0)
                if self.nChannels == 2:
                    self.signals = np.hstack((self.signals, np.zeros((self.nChannels, 1))))
                self.nSamplesPerChannel += 1


        except RuntimeError as error:
            print('\n', error)

        # create buffer array
        self.dataArray = uldaq.create_float_buffer(number_of_channels=self.nChannels, samples_per_channel=self.nSamplesPerChannel)

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

        self.actualRate = self.device.a_out_scan(low_chan=0, high_chan=self.nChannels - 1, analog_range=self.range,
                                                 samples_per_channel=self.nSamplesPerChannel, rate=self.sampleRate, options=self.scanOptions,
                                                 flags=self.flags, data=self.dataArray)

        if flagWait:
            print('AO device data write - Please wait')
            self.device.scan_wait(wait_type=uldaq.WaitType.WAIT_UNTIL_DONE, timeout=-1)
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
            self.actualRate = self.device.a_out(channel=0, analog_range=self.range, flags=self.flags, data=0.0)

    def stopWrite(self):
        self.device.scan_stop()

    def getstatus(self):
        status, transferStatus = self.device.get_scan_status()
        """
        Status:
           status==0 Idle
           status==1 Running

        transferStatus: progress of a scan operation.
            current_index: The index into the data buffer immediately following the last sample transferred.
            current_total_count: The total number of samples transferred since the scan started.
            current_scan_count: The number of samples per channel transferred since the scan started.
        """
        if False:
            print('Collected samples (all channels) = ', transferStatus.current_total_count)
            print('Collected samples per channel = ', transferStatus.current_scan_count)
            print('current Buffer Idx = ', transferStatus.current_index, '\n')

        return status, transferStatus.current_scan_count, transferStatus.current_index, transferStatus.current_total_count


class MCC1808():
    def __init__(self):
        self.DAQdevice = self.getDevice()
        self.AiDevice = MCC1808_analogIn(self.DAQdevice)
        self.AoDevice = MCC1808_analogOut(self.DAQdevice)

        self.connect()

    def getDevice(self):
        # Get the DAQ device object and verify that it is valid.
        interface_type = uldaq.InterfaceType.ANY

        try:
            # Get descriptors for all of the available DAQ devices.
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
            daqDevice = uldaq.DaqDevice(devices[descriptor_index])
            print(daqDevice)

        except RuntimeError as error:
            print('\n', error)
            exit()

        return daqDevice

    def connect(self):
        # Establish a connection to the DAQ device.
        try:
            self.descriptor = self.DAQdevice.get_descriptor()
            print('\nConnecting to', self.descriptor.dev_string, '- please wait...')
            # For Ethernet devices using a connection_code other than the default
            # value of zero, change the line below to enter the desired code.
            self.DAQdevice.connect(connection_code=0)

            if self.AiDevice is not None:
                print("Analog in device: " + str(self.AiDevice.device.get_info()))
            else:
                print("Analog in device: None")

            if self.AoDevice is not None:
                print("Analog out device: " + str(self.AoDevice.device.get_info()))
            else:
                print("Analog out device: None")

        except RuntimeError as error:
            print('\n', error)

    def disconnect(self):

        print('\nStopping', self.descriptor.dev_string, '- please wait...')
        status, transfer_status = self.AiDevice.device.get_scan_status()

        # Stop the acquisition if it is still running.
        if status == uldaq.ScanStatus.RUNNING:
            print('Stopping AI Device data collection - please wait...')
            self.AiDevice.device.scan_stop()

        status, transfer_status = self.AoDevice.device.get_scan_status()
        # Stop the signal generation if it is still running.
        if status == uldaq.ScanStatus.RUNNING:
            print('Stopping AO Device data generation - please wait...')
            self.AoDevice.device.scan_stop()

        if self.DAQdevice.is_connected():
            print('Disconnecting DAQ device - please wait...')
            self.DAQdevice.disconnect()

        print('Releasing DAQ device - please wait...')
        self.DAQdevice.release()
        print('Done!')
