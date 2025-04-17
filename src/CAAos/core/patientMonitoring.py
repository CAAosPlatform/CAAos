# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import numpy as np

from lxml import etree as ETree

from CAAos.acquisitionBoard.MCC1808 import MCC1808
from CAAos.acquisitionBoard.signalGenerator import signalGenerator
from CAAos.core.patientProcessing import patientProcessing
from CAAos.tools import tools
from CAAos.core.signals.signals import signal
from CAAos.tools.repeatedTimer import RepeatedTimer


class patientMonitoring(patientProcessing):

    def __init__(self):
        super().__init__()

        #default names
        self.signalLabels = ['CBFv_L', 'CBFv_R', 'ABP', 'Channel 4']
        self.signalUnits = ['cm/s', 'cm/s', 'mmHg', 'none']
        self.scheduleJob = None

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

        self.setActiveModule('preprocessing')

        #load preprocessing operations
        self.import_PPO_ARO_Operations('AR_monitoring.PPO', None, runOperations=False)

        self.setActiveModule('ARanalysis')
        #self.import_PPO_ARO_Operations('AR_monitoring.ARO', None, runOperations=False)

        # create operations node for new operations
        self.createNewOperation()


    def startAcquisition(self, totalTime_sec=10.0, samplingRate_Hz=100, patientName='Patient Name', birthDate='1:1:0001'):
        """
        Acquire data using the DAC board.
        Args:
            totalTime_sec: total time for data acquisition in seconds.
        """

        # set acquisition configuration
        self.samplingRate_Hz = samplingRate_Hz
        self.signalLabels = ['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4']
        self.signalUnits = ['none', 'none', 'none', 'none']
        self.nChannels = len(self.signalLabels)
        self.saveAcquisitionHeader(patientName, birthDate)

        tools.ETaddElement(self.jobRootNode.xpath('data'), 'samplingRate_Hz', text=str(self.samplingRate_Hz))

        # start collecting data
        self.myDAQ = MCC1808()

        # ------------------------------------------
        # analog input configuration
        # ------------------------------------------

        channels = [0, 1, 2, 3]

        AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(self.nChannels)]
        volt2velocity = 100 / 0.97  # (cm/s)/V  100cm/s=0,.97V. Dopplerbox manual, page 4-2

        self.nSamplesTotal = int(totalTime_sec * self.samplingRate_Hz)

        self.myDAQ.AiDevice.confChannelQueue(AinConf, self.samplingRate_Hz, self.nSamplesTotal)

        self.sampledData = self.myDAQ.AiDevice.dataArrayNP

        # init signals with empty arrays
        for i in range(self.nChannels):
            newSignal = signal(channel=i, label=self.signalLabels[i], unit=self.signalUnits[i], data=np.array([]), samplingRate_Hz=0.0,
                               operationsXML=self.PPoperationsNode)
            self.signals.append(newSignal)

        # read data
        self.myDAQ.AiDevice.readData(flagWait=False)

        self.lastLoadedSample = 0

        # self.scheduleAcquisition(interval_sec=1.0)

        self.hasData = True

    def startAcquisitionSimulationMode(self, dataFileName, totalTime_sec=10.0, samplingRate_Hz=100, patientName='Patient Name', birthDate='1:1:0001'):
        """
        Acquire data using the DAC board. Use internal signal generator to simulate data.
        Args:
            totalTime_sec: total time for data acquisition in seconds.
        """

        # set acquisition configuration
        self.samplingRate_Hz = samplingRate_Hz
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

        channels = [4, 5, 6, 7]

        AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(self.nChannels)]
        volt2velocity = 100 / 0.97  # (cm/s)/V  100cm/s=0,.97V. Dopplerbox manual, page 4-2

        self.nSamplesTotal = int(totalTime_sec * self.samplingRate_Hz)

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
            newSignal = signal(channel=i, label=self.signalLabels[i], unit=self.signalUnits[i], data=np.array([]), samplingRate_Hz=0.0,
                               operationsXML=self.PPoperationsNode)
            self.signals.append(newSignal)

        # read data
        self.myDAQ.AoDevice.writeData(flagWait=False)
        self.myDAQ.AiDevice.readData(flagWait=False)

        self.lastLoadedSample = 0

        # self.scheduleAcquisition(interval_sec=1.0)

        self.hasData = True

    def initSignalUpdateTimer(self, interval_sec=30, updateAllData=False, applyOperations=False,saveToFile=False):
        """
        Set the timer for signal update. This functions will periodically update the signals with measured data.
        Args:
            interval_sec: interval time in seconds.
            updateAllData: if True, reload all data, from the first sample.
                           if False, load only new data, not modifying the previous data.
            applyOperations: apply any operations already stored to the signals.
            saveToFile: save data to file.

        Returns:

        """
        if self.scheduleJob is not None and self.scheduleJob.is_running:
            self.scheduleJob.stop()
        self.scheduleJob = RepeatedTimer(interval_sec, self.updateSignals, updateAllData, applyOperations, saveToFile)

    def stopSignalUpdateTimer(self):
        """
        Stop the signal update timer.

        """
        if self.scheduleJob.is_running:
            self.scheduleJob.stop()

    def updateSignals(self, updateAllData=False, applyOperations=False, saveToFile=False):
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

        print('Updating signals...')
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
                rawData = rawData[:, currentSample:]

            with open(self.DATAfileName, 'a') as file:
                for i in range(rawData.shape[1]):
                    time = self.examDate + timedelta(seconds=(self.lastLoadedSample + i) * 1.0 / self.samplingRate_Hz)
                    examDate = self.examDate.strftime("%H:%M:%S:%f")[:-4]
                    timeString = time.strftime("%H:%M:%S:%f")[:-4]  # build string
                    file.write('%s\t%d' % (timeString, i))
                    for ch in range(self.nChannels):
                        file.write('\t%f' % rawData[ch, i])
                    file.write('\n')

        self.lastLoadedSample = currentSample

        if applyOperations:
            self.applyOperations()

        return True

    def applyOperations(self):
        """
        Apply operations to the signals.
        """
        # run all operations

        if self.PPoperationsNode is not None:
            print('running preprocessing operations...')
            #tools.printET(self.PPoperationsNode)
            for elem in self.jobRootNode.xpath('operations/preprocessing'):  # there might be more than one preprocessing operations
                self.runPreprocessingOperations(elem)

        if self.ARoperationsNode is not None:
            print('running AR operations...')
            #tools.printET(self.ARoperationsNode)
            for elem in self.jobRootNode.xpath('operations/ARanalysis'): # there might be more than one ARanalys operations
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
        return self.myDAQ.AiDevice.dataArrayNP[:, startSample:endSample]

    def getCurrentSamplePerChannel(self):
        """
        Get the current sample index.
        
        Returns:

        """
        """
                Status:
                   status==0 Idle
                   status==1 Running

                transferStatus: progress of a scan operation.



                """
        status, transferStatus = self.myDAQ.AiDevice.device.get_scan_status()

        # current_index: The index into the data buffer immediately following the last sample transferred.
        current_index = transferStatus.current_index

        # current_total_count: The total number of samples transferred since the scan started.
        current_total_count = transferStatus.current_total_count

        # current_scan_count: The number of samples per channel transferred since the scan started.
        current_scan_count = transferStatus.current_scan_count

        return transferStatus.current_scan_count

    def saveAcquisitionHeader(self, patientName='', birthDate='1:1:0001'):
        # create EXP header file
        self.examDate = datetime.now()
        examDateStr = self.examDate.strftime("%d:%-m:%Y %H:%M:%S")  #: Examination Date.

        self.header = ["Patient Name:%s" % patientName, "birthday:%s" % birthDate, "Examination:%s" % examDateStr,
                       "Sampling Rate: %dHz" % self.samplingRate_Hz,
                       "Time\tSample\t%s\t%s\t%s\t%s" % (self.signalLabels[0], self.signalLabels[1], self.signalLabels[2], self.signalLabels[3]),
                       "HH:mm:ss:ms\tN\t%s\t%s\t%s\t%s" % (self.signalUnits[0], self.signalUnits[1], self.signalUnits[2], self.signalUnits[3])]

        with open(self.DATAfileName, 'w') as self.file:
            for line in self.header:
                self.file.write(line + '\n')

    def stopAcquisition(self):
        self.stopSignalUpdateTimer()
        self.myDAQ.disconnect()
