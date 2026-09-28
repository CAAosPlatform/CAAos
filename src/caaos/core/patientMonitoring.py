# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import numpy as np
from lxml import etree as ETree
from datetime import datetime

flagSimulateAcquisition = False  # flag to simulate acquisition

from caaos.acquisitionBoard.signalGenerator import signalGenerator
from caaos.core.patientProcessing import patientProcessing
from caaos.tools import tools
from caaos.core.signals.signals import signal
from caaos.tools.repeatedTimer import RepeatedTimer


class patientMonitoring(patientProcessing):

    def __init__(self):

        super().__init__()

        # default names
        # self.signalLabels = ['CBFv_L', 'CBFv_R', 'ABP', 'Channel 4']
        # self.signalUnits = ['cm/s', 'cm/s', 'mmHg', 'none']
        self.scheduleJob = None
        self.mockupAcquisition = False

    def newJob(self, outputFile='./temp.exp'):
        """
        Create a new job for patient monitoring.
        Args:
            outputFile: output data file for AR monitoring.   .EXP .DAT .CSV .PAR
        """

        self.DATAfileName = outputFile

        [self.dirName, self.filePrefix, extension] = tools.splitPath(self.DATAfileName)

        if extension.lower() not in ['.exp', '.dat', '.csv', '.par']:
            print('ERROR: newJob - wrong input data file type...')
            exit()

        if extension.upper() in ['.EXP', '.DAT']:
            self.DATAfileType = 'EXP_DAT'
        if extension.upper() in ['.CSV']:
            self.DATAfileType = 'CSV'
        if extension.upper() in ['.PAR']:
            self.DATAfileType = 'PAR'

        # create operationsTree
        self.jobRootNode = ETree.Element('job')
        self.jobRootNode.set('version', self.getVersion())

        # add acquisition setup to the tree
        dataNode = tools.ETaddElement(self.jobRootNode, tag='data', text=None, attribList=[['type', 'monitoring']])
        tools.ETaddElement(dataNode, 'outputFile', text=self.DATAfileName, attribList=[['type', self.DATAfileType]])

        # tools.printET(self.jobRootNode)
        self.setActiveModule('preprocessing')

        # load preprocessing operations
        self.import_PPO_ARO_Operations('AR_monitoring.PPO', None, runOperations=False)

        # tools.printET(self.jobRootNode)
        if True:
            self.setActiveModule('ARanalysis')
            self.import_PPO_ARO_Operations('AR_monitoring.ARO', None, runOperations=False)
        else:
            print('WARNING: Skipping loading of AR analysis operations for monitoring job!')

        # tools.printET(self.jobRootNode)
        # create operations node for new operations
        self.createNewOperation()

        tools.printET(self.jobRootNode)

    def startAcquisition(self, totalTime_sec=120.0, samplingRate_Hz=100, initialBufferTime_sec=0,
                         patientName='Patient_Name', birthDate='1:1:0001', mockupAcquisition=False,
                         mockupInputEXPfile=None):
        """
        Acquire data using the DAC board.
        Args:
            totalTime_sec: total time for data acquisition in seconds.
            samplingRate_Hz: sampling rate in Hz.
            initialBufferTime_sec: initial time to fill the buffer before starting processing.
            patientName: patient name.
            birthDate: patient birth date.
            mockupAcquisition: use mockup acquisition board for testing.
            mockupInputEXPfile: input EXP file for mockup acquisition board. Used only if mockupAcquisition=True.
        """

        # set acquisition configuration
        self.samplingRate_Hz = samplingRate_Hz
        self.nSamplesTotal = int(totalTime_sec * self.samplingRate_Hz)
        self.mockupAcquisition = mockupAcquisition

        # labels and units will be changed by the PPO  file later
        self.signalLabels = ['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4']
        self.signalUnits = ['none', 'none', 'none', 'none']

        self.nChannels = len(self.signalLabels)
        self.saveAcquisitionHeader(patientName, birthDate)

        tools.ETaddElement(self.jobRootNode.xpath('data'), 'samplingRate_Hz', text=str(self.samplingRate_Hz))

        if self.mockupAcquisition:
            print('WARNING: Using mockup acquisition board!')
            from caaos.acquisitionBoard.MCC1808_mockup import MCC1808
        else:
            from caaos.acquisitionBoard.MCC1808 import MCC1808

        # start collecting data
        self.myDAQ = MCC1808()

        if self.mockupAcquisition:
            self.myDAQ.setInputEXPfile(mockupInputEXPfile)

        # ------------------------------------------
        # analog input configuration
        # ------------------------------------------

        channels = [0, 1, 2, 3]

        AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(self.nChannels)]
        volt2velocity = 100 / 0.97  # (cm/s)/V  100cm/s=0,.97V. Dopplerbox manual, page 4-2

        self.myDAQ.AiDevice.confChannelQueue(AinConf, self.samplingRate_Hz, self.nSamplesTotal)

        self.sampledData = self.myDAQ.AiDevice.dataArrayNP

        # init signals with empty arrays
        for i in range(self.nChannels):
            newSignal = signal(channel=i, label=self.signalLabels[i], unit=self.signalUnits[i], data=np.array([]),
                               samplingRate_Hz=0.0, operationsXML=self.PPoperationsNode)
            self.signals.append(newSignal)

        # get start time instant
        self.startTime = datetime.now()

        # read data
        self.myDAQ.AiDevice.readData(flagWait=False)

        self.lastLoadedSample = 0

        if initialBufferTime_sec > 0:
            print('time to fill the buffer before starting processing...')
            tools.timed_wait(int(initialBufferTime_sec), update_interval=5)

        self.hasData = True

    def startAcquisitionSimulationMode(self, dataFileName, totalTime_sec=120.0, samplingRate_Hz=100,
                                       initialBufferTime_sec=0, patientName='Patient_Name', birthDate='1:1:0001'):
        """
        Acquire data using the DAC board. Use internal signal generator to simulate data.
        Args:
            totalTime_sec: total time for data acquisition in seconds.
            samplingRate_Hz: sampling rate in Hz.
            initialBufferTime_sec: initial time to fill the buffer before starting processing.
            patientName: patient name.
            birthDate: patient birth date.
        """

        # set acquisition configuration
        self.samplingRate_Hz = samplingRate_Hz
        self.nSamplesTotal = int(totalTime_sec * self.samplingRate_Hz)

        # labels and units will be changed by the PPO  file later
        self.signalLabels = ['Channel 1', 'Channel 1b', 'Channel 2', 'Channel 2b']
        self.signalUnits = ['none', 'none', 'none', 'none']

        self.nChannels = len(self.signalLabels)
        self.saveAcquisitionHeader(patientName, birthDate)

        tools.ETaddElement(self.jobRootNode.xpath('data'), 'samplingRate_Hz', text=str(self.samplingRate_Hz))

        from caaos.acquisitionBoard.MCC1808 import MCC1808

        # start collecting data
        self.myDAQ = MCC1808()

        print('WARNING: Using simulation mode for data acquisition!')

        # ------------------------------------------
        # analog output configuration
        # ------------------------------------------

        nChannels = 2
        data, sampleRate = self.myDAQ.AoDevice.loadDataFrom_EXP(dataFileName, channels=[0, 2])

        data = self.myDAQ.AoDevice.normalizeData(data, maxV=9.0)
        self.myDAQ.AoDevice.confChannelScan(signals=data, sampleRate=sampleRate, continuous=True, zeroEnd=True)

        # ------------------------------------------
        # analog input configuration
        # ------------------------------------------

        channels = [6, 7, 4, 5]  # Aout0 is connected to Ain6 and Ain7, Aout1 is connected to Ai4 and Ai5

        AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(self.nChannels)]
        volt2velocity = 100 / 0.97  # (cm/s)/V  100cm/s=0,.97V. Dopplerbox manual, page 4-2

        self.myDAQ.AiDevice.confChannelQueue(AinConf, self.samplingRate_Hz, self.nSamplesTotal)

        self.sampledData = self.myDAQ.AiDevice.dataArrayNP

        # init signals with empty arrays
        for i in range(self.nChannels):
            newSignal = signal(channel=i, label=self.signalLabels[i], unit=self.signalUnits[i], data=np.array([]),
                               samplingRate_Hz=0.0, operationsXML=self.PPoperationsNode)
            self.signals.append(newSignal)

        # get start time instant
        self.startTime = datetime.now()

        # read data
        self.myDAQ.AoDevice.writeData(flagWait=False)
        self.myDAQ.AiDevice.readData(flagWait=False)

        self.lastLoadedSample = 0

        if initialBufferTime_sec > 0:
            print('time to fill the buffer before starting processing...')
            tools.timed_wait(int(initialBufferTime_sec), update_interval=5)

        self.hasData = True

    def startAcquisitionSimulationModeOld(self, dataFileName, totalTime_sec=120.0, samplingRate_Hz=100,
                                          patientName='Patient Name', birthDate='1:1:0001'):
        """
        Acquire data using the DAC board. Use internal signal generator to simulate data.
        Args:
            totalTime_sec: total time for data acquisition in seconds.
            samplingRate_Hz: sampling rate in Hz.
            patientName: patient name.
            birthDate: patient birth date.
        """

        # set acquisition configuration
        self.samplingRate_Hz = samplingRate_Hz
        self.nSamplesTotal = int(totalTime_sec * self.samplingRate_Hz)

        # labels and units will be changed by the PPO  file later
        self.signalLabels = ['Channel 1', 'Channel 1b', 'Channel 2', 'Channel 2b']
        self.signalUnits = ['none', 'none', 'none', 'none']

        self.nChannels = len(self.signalLabels)
        self.saveAcquisitionHeader(patientName, birthDate)

        tools.ETaddElement(self.jobRootNode.xpath('data'), 'samplingRate_Hz', text=str(self.samplingRate_Hz))

        # start collecting data
        self.myDAQ = MCC1808()

        print('WARNING: Using simulation mode for data acquisition!')
        # ------------------------------------------
        # analog input configuration
        # ------------------------------------------

        channels = [6, 7, 4, 5]  # Aout0 is connected to Ain6 and Ain7, Aout1 is connected to Ai4 and Ai5

        AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(self.nChannels)]
        volt2velocity = 100 / 0.97  # (cm/s)/V  100cm/s=0,.97V. Dopplerbox manual, page 4-2

        self.myDAQ.AiDevice.confChannelQueue(AinConf, self.samplingRate_Hz, self.nSamplesTotal)

        # ------------------------------------------
        # analog output configuration
        # ------------------------------------------

        simulateAcquisition = True

        if simulateAcquisition:
            nChannels = 2
            data, sampleRate = self.myDAQ.AoDevice.loadDataFrom_EXP(dataFileName, channels=[0, 2])

        else:
            nChannels = 2
            sampleRate = self.samplingRate_Hz  # value in Hz
            nSamples = 100
            mysignalGenerator = signalGenerator(nChannels=2, length=nSamples, samplingFrequency=sampleRate)
            mysignalGenerator.sin(channelList=[0], amplitude=1.0, frequency=1.0, offset=0.0, phase_rad=0.0)
            mysignalGenerator.cos(channelList=[1], amplitude=1.0, frequency=1.0, offset=0.0, phase_rad=0.0)
            data = mysignalGenerator.data

        data = self.myDAQ.AoDevice.normalizeData(data, maxV=9.0)
        self.myDAQ.AoDevice.confChannelScan(signals=data, sampleRate=sampleRate, continuous=True, zeroEnd=True)

        # ------------------------------------------
        # start read/write
        # ------------------------------------------

        self.sampledData = self.myDAQ.AiDevice.dataArrayNP

        # init signals with empty arrays
        for i in range(self.nChannels):
            newSignal = signal(channel=i, label=self.signalLabels[i], unit=self.signalUnits[i], data=np.array([]),
                               samplingRate_Hz=0.0, operationsXML=self.PPoperationsNode)
            self.signals.append(newSignal)

        # read data
        self.myDAQ.AoDevice.writeData(flagWait=False)
        self.myDAQ.AiDevice.readData(flagWait=False)

        self.lastLoadedSample = 0

        self.hasData = True

    def initSignalUpdateTimer(self, interval_sec=30.0, FIFOlength_s=10.0, applyOperations=False, saveToFile=False):
        """
        Set the timer for signal update. This functions will periodically update the signals with measured data.
        Args:
            interval_sec: update time interval in seconds. This is the peridioc time to check for new data and
            process it in the platform.
            FIFOlength_s: length of the FIFO buffer in seconds. this is the length of data kept in the platform.
            applyOperations: apply any operations already stored to the signals.
            saveToFile: save data to file.

        Returns:

        """

        self.nSamplesFIFO = int(FIFOlength_s * self.samplingRate_Hz)

        if self.scheduleJob is not None and self.scheduleJob.is_running:
            self.scheduleJob.stop()
        self.scheduleJob = RepeatedTimer(interval_sec, self.updateSignals, applyOperations, saveToFile)

        # self.scheduleJob = RepeatedTimer(interval_sec, self.updateSignalsOld, updateAllData, applyOperations,saveToFile)

    def stopSignalUpdateTimer(self):
        """
        Stop the signal update timer.

        """
        if self.scheduleJob.is_running:
            self.scheduleJob.stop()

    def updateSignals(self, applyOperations=False, saveToFile=False):
        """
        Update the signal in FIFO mode, that is, keeping only the latest data up to a fixed length.
        The older data is shifted out and the oldest data is discarded to fit the FIFO buffer.
        This will also save new data to file if saveToFile=True.

        Args:
            applyOperations: apply any operations already stored to the signals.
            saveToFile: save data to file.

        Returns:
            True if there is new data to be collected, False otherwise.

        """
        if False:
            FIFOlength_s = 30.0
            self.nSamplesFIFO = int(FIFOlength_s * self.samplingRate_Hz)

        if self.lastLoadedSample >= self.nSamplesTotal:
            print('All data was collected. Returning...')
            self.stopSignalUpdateTimer()
            return False

        currentSample = self.getCurrentSamplePerChannel()

        self.currentTime = currentSample/self.samplingRate_Hz
        # number of new samples to be loaded
        newdataLength = currentSample - self.lastLoadedSample

        print('--------- Update signals -------------')
        print('Last loaded sample: %d' % self.lastLoadedSample)
        print('Current sample: %d' % currentSample)
        print('Current time (s): %d' % self.currentTime)
        print('New data length (samples): %d' % newdataLength)
        print('FIFO length (samples): %d' % self.nSamplesFIFO)

        if currentSample <= self.nSamplesFIFO:
            startSample = 0
            endSample = currentSample
        else:
            startSample = currentSample - self.nSamplesFIFO
            endSample = currentSample

        print('FIFO start Sample: %d' % startSample)
        print('FIFO end Sample: %d' % endSample)
        rawData = self.getAcquisitionData(startSample, endSample)

        # signals with new data
        for i in range(self.nChannels):
            self.signals[i].data = rawData[i, :]
            self.signals[i].samplingRate_Hz = self.samplingRate_Hz
            self.signals[i].nPoints = self.signals[i].data.shape[0]

        if saveToFile:
            # saves only new data
            if currentSample <= self.nSamplesFIFO:
                rawData = rawData[:, self.lastLoadedSample:currentSample]
            else:
                rawData = rawData[:, -newdataLength:]

            with open(self.DATAfileName, 'a') as file:
                print('------------ saving data--------------')
                print('raw data size: %d' % rawData.shape[1])
                for i in range(rawData.shape[1]):
                    time = self.examDate + timedelta(seconds=(self.lastLoadedSample + i) * 1.0 / self.samplingRate_Hz)
                    timeString = time.strftime("%H:%M:%S:%f")[:-4]  # build string
                    file.write('%s\t%d' % (timeString, self.currentSampleNumber))
                    for ch in range(self.nChannels):
                        file.write('\t%f' % rawData[ch, i])
                    file.write('\n')
                    self.currentSampleNumber += 1

        self.lastLoadedSample = currentSample

        if applyOperations:
            self.applyOperations()

        if self.hasARIdata_L:
            print('ARI_L: %f' % self.ARI_L.ARI_frac)
        if self.hasARIdata_R:
            print('ARI_R: %f' % self.ARI_R.ARI_frac)
        print('--------------------------------------')
        return True

    def updateSignalsOld(self, updateAllData=False, applyOperations=False, saveToFile=False):
        """
        Update the signals with more acquired data, up to latest sample.
        Args:
            updateAllData: if True, reload all data, from the first sample.
                           if False, load only new data, not modifying the previous data.
            applyOperations: apply any operations already stored to the signals.
            saveToFile: save data to file.

        Returns:
            True if there is new data to be collected, False otherwise.

        """
        currentSample = self.getCurrentSamplePerChannel()

        print('--------- Update signals -------------')
        print('Last loaded sample: %d' % self.lastLoadedSample)
        print('Current sample: %d' % currentSample)

        if self.lastLoadedSample == self.nSamplesTotal:
            print('All data was collected. Returning...')
            self.stopSignalUpdateTimer()
            return False

        if updateAllData:
            print('Reloading all data...')
            rawData = self.getAcquisitionData(startSample=0, endSample=currentSample)

            # signals with new data
            for i in range(self.nChannels):
                self.signals[i].data = rawData[i, :]
                self.signals[i].samplingRate_Hz = self.samplingRate_Hz
                self.signals[i].nPoints = self.signals[i].data.shape[0]
        else:
            rawData = self.getAcquisitionData(startSample=self.lastLoadedSample, endSample=currentSample)

            # concatenate signals with new data
            for i in range(self.nChannels):
                self.signals[i].data = np.concatenate([self.signals[i].data, rawData[i, :]])
                self.signals[i].samplingRate_Hz = self.samplingRate_Hz
                self.signals[i].nPoints = self.signals[i].data.shape[0]

        if saveToFile:
            if updateAllData:
                rawData = rawData[:, self.lastLoadedSample:currentSample]

            with open(self.DATAfileName, 'a') as file:
                print('-------------------------- saving data----------------------------')
                print('raw data size: %d' % rawData.shape[1])
                for i in range(rawData.shape[1]):
                    time = self.examDate + timedelta(seconds=(self.lastLoadedSample + i) * 1.0 / self.samplingRate_Hz)
                    examDate = self.examDate.strftime("%H:%M:%S:%f")[:-4]
                    timeString = time.strftime("%H:%M:%S:%f")[:-4]  # build string
                    file.write('%s\t%d' % (timeString, self.currentSampleNumber))
                    for ch in range(self.nChannels):
                        file.write('\t%f' % rawData[ch, i])
                    file.write('\n')
                    self.currentSampleNumber += 1

        self.lastLoadedSample = currentSample

        if applyOperations:
            self.applyOperations()

        print('--------------------------------------')
        return True

    def applyOperations(self):
        """
        Apply operations to the signals.
        """
        # run all operations

        if self.PPoperationsNode is not None:
            print('running preprocessing operations...')
            # tools.printET(self.PPoperationsNode)
            for elem in self.jobRootNode.xpath(
              'operations/preprocessing'):  # there might be more than one preprocessing operations
                self.runPreprocessingOperations(elem)

        if self.ARoperationsNode is not None:
            print('running AR operations...')
            # tools.printET(self.ARoperationsNode)
            for elem in self.jobRootNode.xpath(
              'operations/ARanalysis'):  # there might be more than one ARanalys operations
                self.runARanalysisOperations(elem)

    def getAcquisitionData(self, startSample=0, endSample=-1):
        """
        Get the acquired data from the DAC board.
        Args:
            startSample: start sample index.
            endSample: end sample index.

        Returns:
            sampledData: numpy array with the acquired data. Each row is a channel.

        """
        return np.copy(self.myDAQ.AiDevice.dataArrayNP[:, startSample:endSample])

    def getCurrentSamplePerChannel(self):
        """
        Get the current sample index.
        
        Returns:

        """

        status, current_scan_count, current_index, current_total_count = self.myDAQ.AiDevice.getstatus()

        return current_scan_count

    def saveAcquisitionHeader(self, patientName='', birthDate='1:1:0001'):
        # create EXP header file
        self.examDate = datetime.now()
        examDateStr = self.examDate.strftime("%d:%-m:%Y %H:%M:%S")  #: Examination Date.

        self.header = ["Patient Name:%s" % patientName, "birthday:%s" % birthDate, "Examination:%s" % examDateStr,
                       "Sampling Rate: %dHz" % self.samplingRate_Hz,
                       "Time\tSample\t%s\t%s\t%s\t%s" % (self.signalLabels[0], self.signalLabels[1],
                                                         self.signalLabels[2], self.signalLabels[3]),
                       "HH:mm:ss:ms\tN\t%s\t%s\t%s\t%s" % (self.signalUnits[0], self.signalUnits[1],
                                                           self.signalUnits[2], self.signalUnits[3])]

        self.currentSampleNumber = 0  # number of the sample to be registered in the file

        with open(self.DATAfileName, 'w') as self.file:
            for line in self.header:
                self.file.write(line + '\n')

    def stopAcquisition(self):
        self.stopSignalUpdateTimer()
        self.myDAQ.disconnect()
