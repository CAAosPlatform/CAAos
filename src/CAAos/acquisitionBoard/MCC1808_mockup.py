#!/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

import numpy as np
import uldaq
import threading
import time
import random

from CAAos.tools import tools

"""Class to create a mockup of the MCC 1808 acquisition board.
This class is used to simulate the behavior of the MCC 1808 board for testing purposes.
This class is not intended to be used in production code.
It is a mockup and does not implement any real functionality.
"""

inputEXPfile = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.EXP'

class DataAcquisitionSimulator:
    def __init__(self, samplingRate_Hz=100.0,nSamplesMax=1000):
        """
        Initialize the simulator.
        """
        self.interval = 1.0/samplingRate_Hz
        self.currentSample = 0
        self.running = False
        self.nSamplesMax = nSamplesMax  # Maximum number of samples to simulate
        self.thread = None

    def start(self):
        """Start the data acquisition in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._acquire_data)
            self.thread.daemon = True  # Ensures the thread exits when the main program ends
            self.thread.start()

    def stop(self):
        """Stop the data acquisition."""
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def _acquire_data(self):
        """Simulate data acquisition by adding one to the sampling counter"""
        while self.running:
            self.currentSample += 1
            if self.currentSample % 100==0:
                print(f'Simulated sample {self.currentSample}')
            time.sleep(self.interval)
            if self.currentSample == self.nSamplesMax:  # Simulate a finite number of samples
                print('Reached maximum number of samples, stopping acquisition.')
                self.running=False

class MCC1808_analogIn():
    def __init__(self, daqDevice):
        self.daqDevice = daqDevice
        self.simulator = None
    def getDevice(self):
        print('getting analog in device... (mockup version)')
        return None

    def __displayScanOptions(self, bit_mask):
        """Create a displays string for all scan options."""
        print('getting analog in device... (mockup version)')
        return None

    def confChannelQueue(self, channelConfList=[{'channel': 0, 'inputMode': 'SE', 'range': 'BIP10VOLTS'}], sampleRate=100, nSamplesPerChannel=1000):

        print('confChannelQueue... (mockup version)')
        self.channelConf = channelConfList
        self.sampleRate = sampleRate
        self.nSamplesPerChannel = nSamplesPerChannel
        self.nChannels = len(channelConfList)

        self.simulator = DataAcquisitionSimulator(self.sampleRate, nSamplesMax=self.nSamplesPerChannel)

        # load data from EXP file
        self.dataArrayNP,_ = self.loadDataFrom_EXP(inputEXPfile, channels=[0, 1, 2, 3])
        self.dataArrayNP = self.dataArrayNP[:,:self.nSamplesPerChannel]

        print('---- Analog input channel queue configuration ----')
        print('Sample Rate (per second)  : ', self.sampleRate)
        print('Nbr of samples per channel: ', self.nSamplesPerChannel)
        print('------------------------------------')

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

        print('----- MCC1808 mockup simulator -----')
        print('input File number of samples per channel: ', signals.shape[1])
        print('Nbr of channels: ', signals.shape[0])
        print('Sampling rate (Hz): ', samplingRate_Hz)
        print('total time with current sampling rate (s): ', signals.shape[1]/samplingRate_Hz)
        print('------------------------------------')

        return signals[channels, :], samplingRate_Hz

    def readData(self, flagWait=False):
        # Start the acquisition.
        #
        # When using the queue, the low_channel, high_channel, input_mode, and
        # range parameters are ignored since they are specified in queue_array.

        self.simulator.start()

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

        if self.simulator.running:
            status = 1
        else:
            status = 0

        current_index = self.simulator.currentSample
        current_total_count = self.simulator.currentSample * self.nChannels
        current_scan_count = self.simulator.currentSample

        if True:
            print('Collected samples (all channels) = ', current_total_count)
            print('Collected samples per channel = ', current_scan_count)
            print('current Buffer Idx = ', current_index, '\n')

        return status, current_scan_count, current_index, current_total_count

    def stopRead(self):
        self.simulator.stop()


class MCC1808_analogOut():
    def __init__(self, daqDevice):
        return

    def getDevice(self):
        print('getting analog out device... (mockup version)')
        return None

    def __displayScanOptions(self, bit_mask):
        """Create a displays string for all scan options."""
        print('getting analog in device... (mockup version)')
        return None

    def confChannelScan(self, signals=np.array([0, 1, 2]), sampleRate=100, continuous=False, zeroEnd=True):
        return None

    def writeData(self, flagWait=False):
        return

    def loadDataFrom_EXP(self, fileName, channels=[0, 1]):
        return None, None

    def normalizeData(self, data, maxV=10.0):
        return None

    def zeroOutput(self):
        return None

    def stopWrite(self):
        return None

    def getstatus(self):
        return None

class MCC1808():
    def __init__(self):
        """Initialize the MCC 1808 mockup acquisition board."""
        self.DAQdevice = 'Mockup MCC 1808 Device'
        self.AiDevice = MCC1808_analogIn(self.DAQdevice)
        self.AoDevice = MCC1808_analogOut(self.DAQdevice)

        self.connect()

    def getDevice(self):
        print('getting DAQ device... (mockup version)')
        return None

    def connect(self):
        print('connecting DAQ device... (mockup version)')

    def disconnect(self):
        print('disconnecting DAQ device... (mockup version)')
        self.AiDevice.stopRead()
        print('Done!')