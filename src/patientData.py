#!/bin/python

"""
.. warning:: Include here brief description of this module
"""
import copy
import os
# -*- coding: utf-8 -*-
import sys
from datetime import datetime

import numpy as np
from lxml import etree as ETree
from scipy import signal as scipySignal

import tools
from ARI import ARIanalysis
from PSDestimator import PSDestimator
from signals import signal
from TFA import transferFunctionAnalysis

__version__ = '0.2'


class patientData():
    """
    Patient data base class

    This is the base class to process cerebral autoregulation data.

    Parameters
    ----------
    inputFile : str
        File with patient's data. Accepted files: **.EXP**, **.DAT** (Raw Data file) or **.PPO** (preprocessing operation file)

    """

    @staticmethod
    def getVersion():
        """
        Return the current version of the module

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        '0.1'
        """
        return __version__

    def __init__(self, inputFile, activeModule):
        # input file:  .EXP-DAT  or .JOB
        # activeModule- Valid options: 'preprocessing', 'ARanalysis'
        self.activeModule = activeModule

        [self.dirName, self.filePrefix, extension] = tools.splitPath(inputFile)

        self.hasRRmarks = False
        self.hasB2Bdata = False
        self.hasPSDdata_L = False
        self.hasPSDdata_R = False
        self.hasTFdata_L = False
        self.hasTFdata_R = False
        self.hasARIdata_L = False
        self.hasARIdata_R = False
        self.historySignals = []
        self.historyOperations = []

        if extension.lower() in ['.exp', '.dat']:
            self.newJob(inputFile)

        if extension.lower() in ['.job']:
            self.loadJob(inputFile)

    def newJob(self, inputFile_EXPDAT):
        # creates a new job with the input data file. This function also loads data from the EXP and DAT  files
        # this function should be called only for preprocessing steps
        self.EXPDATfileName = inputFile_EXPDAT
        # create operationsTree
        self.jobRootNode = ETree.Element('job')
        self.jobRootNode.set('version', self.getVersion())

        # create InputFile Element
        [dir, filePrefix, extension] = tools.splitPath(self.EXPDATfileName)
        tools.ETaddElement(self.jobRootNode, 'inputFile', text=filePrefix + extension, attribList=[['type', 'EXP_DAT']])

        # create a operations node for new operations
        self.createNewOperation()

        self.loadEXPDATfile()

    def loadJob(self, inputFile_Job):
        # parse JOB file into ETree
        parser = ETree.XMLParser(remove_blank_text=True)
        self.jobRootNode = ETree.parse(inputFile_Job, parser).getroot()
        self.EXPDATfileName = self.dirName + tools.getElemValueXpath(self.jobRootNode, xpath='inputFile', valType='str')

        self.createNewOperation()

        # import operationsFile
        for elem in self.jobRootNode.xpath('operationsFile'):
            pos = self.jobRootNode.index(elem)
            self.jobRootNode.remove(elem)
            self.importOperations(self.dirName + elem.text, pos, runOperations=False)

        self.loadEXPDATfile()

        # run all operations
        for elem in self.jobRootNode.xpath('operations/preprocessing'):
            self.runPreprocessingOperations(elem)
        if self.activeModule == 'ARanalysis':
            for elem in self.jobRootNode.xpath('operations/ARanalysis'):
                self.runARanalysisOperations(elem)

    def importOperations(self, inputFile_PPO_ARO, elemPosition=None, runOperations=False):
        # imports the operations contained in inputFile_ARO file
        # if elemPosition=None: add to the end

        # check for file type errors
        [dir, base, ext] = tools.splitPath(inputFile_PPO_ARO)
        # if (self.activeModule == 'preprocessing') and ext != '.ppo':
        #  print('ERROR: importOperations in ->Preprocessing<- module requires .ppo file! exiting...')
        #  exit(-1)

        parser = ETree.XMLParser(remove_blank_text=True)
        operationRootNode = ETree.parse(inputFile_PPO_ARO, parser).getroot()

        operationRootNode.attrib['imported'] = 'True'
        operationRootNode.attrib['operationsFile'] = os.path.basename(inputFile_PPO_ARO)
        if elemPosition is not None:
            self.jobRootNode.insert(elemPosition, operationRootNode)
        else:
            self.jobRootNode.append(operationRootNode)

        # creates a new operators Node
        self.createNewOperation()

        # run all operations
        if runOperations:
            if self.activeModule == 'preprocessing':
                for elem in operationRootNode.xpath('preprocessing'):
                    self.runPreprocessingOperations(elem)
            if self.activeModule == 'ARanalysis':
                for elem in self.jobRootNode.xpath('ARanalysis'):
                    self.runARanalysisOperations(elem)

    def _removeEmptyOperations(self, parentElement):
        "removes recursivelly empty elements"

        # source: https://stackoverflow.com/questions/12694091/python-lxml-how-to-remove-empty-repeated-tags
        def recursively_empty(e):
            if e.text:
                return False
            return all((recursively_empty(c) for c in e.iterchildren()))

        context = ETree.iterwalk(parentElement)
        for action, elem in context:
            if elem.tag == 'operations':
                parent = elem.getparent()
                if recursively_empty(elem):
                    parent.remove(elem)

    def createNewOperation(self):
        "creates new operations Nodes. Before that cleans up any empty operators Element in the Tree."
        # removes any empty operations Node
        self._removeEmptyOperations(self.jobRootNode)

        # create a operations node for new operations
        self.operationsNode = tools.ETaddElement(self.jobRootNode, 'operations', text=None, attribList=[['imported', 'False']])

        self.PPoperationsNode = tools.ETaddElement(self.operationsNode, 'preprocessing', text=None, attribList=None)
        if self.activeModule == 'ARanalysis':
            self.ARoperationsNode = tools.ETaddElement(self.operationsNode, 'ARanalysis', text=None, attribList=None)

    def storeState(self):
        self.historySignals.append(copy.deepcopy(self.signals))
        self.historyOperations.append(copy.deepcopy(self.PPoperationsNode))

    def undoState(self):
        del self.historyOperations[-1]
        del self.historySignals[-1]
        self.PPoperationsNode = copy.deepcopy(self.historyOperations[-1])
        self.signals = copy.deepcopy(self.historySignals[-1])

    def loadEXPDATHeader(self):
        """
        Load header data from raw data files **.exp**, **.dat**.

        This function is usually used in the begining to extract general information from the file. This function is automatically called from :meth:`loadData`

        **Header format**

        The expected header format is::

            Patient Name: XXXXX                                                       \\ H
            birthday:DD:MM:YYYY                                                       | E
            Examination:DD:M:YYYY HH:MM:SS                                            | A
            Sampling Rate: XXXHz                                                      | D
            Time	Sample	<CH_0_label>	<CH_1_label>	...   <CH_N_label>    | E    <- Labels: (columns separated by tabs)
            HH:mm:ss:ms	N	<CH_0_unit>	<CH_1_unit>	...   <CH_N_unit>     / R    <-  Units: (columns separated by tabs)
            00:00:00:00	0	0	45	...	14.8	                                  <-- table of data starts here
            00:00:00:10	1	0	46	...	16.8
            ...


        This function extracts only the following fields from the header

        * Examination date
        * Sampling Rate
        * Number of channels
        * Channel info: label and unit

        **Notes**

        * The examination date is stored as a :mod:`datetime` element in the attribute :attr:`examDate`.
        * The number of channels is stored in the attribute :attr:`nChannels`.
        * The sampling rate is stored in the attribute :attr:`samplingRate_Hz`. The value of this attribute is sent to instances of :class:`~signals.signal` after calling :meth:`loadData` and this attribute is removed after that
        * Channel labels and units are stored in the attribute :attr:`signalLabels` and :attr:`signalUnits`. The values of these attributes are sent to instances of :class:`~signals.signal` after calling :meth:`loadData`  and these attributes are removed after that

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadEXPDATHeader()
        >>> myCase.examDate
        datetime.datetime(2015, 12, 31, 12, 5, 30)  # 31st Jan 2015 - 12:05:30
        >>> myCase.samplingRate_Hz
        100.0
        >>> myCase.nChannels
        4
        >>> myCase.signalLabels
        ['Time', 'Sample', 'MCA_L_To_Probe_Env', 'MCA_R_To_Probe_Env', 'Analog_1', 'Analog_8']
        >>> myCase.signalUnits
        ['HH:mm:ss:ms', 'N', 'cm/s', 'cm/s', 'mV', 'mV']

        """
        file = open(self.EXPDATfileName, 'r')
        line = ''
        self.sizeHeader = 0

        # extract examination date
        while not line.startswith('Examination'):
            line = file.readline()
            self.sizeHeader += 1

        date = datetime.strptime(line[12:].split()[0], '%d:%m:%Y').date()
        time = datetime.strptime(line[12:].split()[1], '%H:%M:%S').time()
        self.examDate = datetime.combine(date, time)  #: Examination Date.

        # extract sampling frequency in Hz
        while not line.startswith('Sampling Rate'):
            line = file.readline()
            self.sizeHeader += 1

        self.samplingRate_Hz = float(line.split()[2].replace(',', '.').replace('Hz', ''))

        # next 2 lines should contain labels and units
        self.signalLabels = file.readline().rstrip().replace(' ', '_').replace('.', '').split('\t')
        self.signalUnits = file.readline().rstrip().split('\t')

        self.nChannels = len(self.signalUnits) - 2
        self.sizeHeader += 2

        file.close()

    def loadEXPDATfile(self):
        """
        Loads patient data from raw data files **.EXP**, **.DAT**.

        This function is used to load data files into memory. This function calls :meth:`loadHeader` internally, so you don't have to call it manually.

        **Notes**

        * Each channel information is stored in one instance of :class:`~signals.signal`. They are accessible via :class:`~signals.signals`

        * In the end of this function, the attributes :attr:`samplingRate_Hz`, :attr:`signalLabels` and :attr:`signalUnits` are removed. This information is passed to the instances of :class:`~signals.signal`

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadEXPDAT()
        >>> myCase.signals[0]
        <signals.signal instance at 0x7f8744e6e710>
        >>> s.signals[0].info()   # shows information of channel 0
        -------------------------------
        Channel: 0
        label: MCA_L_To_Probe_Env
        unit: cm/s
        sigType: None
        nPoints: 30676
        -------------------------------
        >>> myCase.signals[1].info()   # shows information of channel 1
        -------------------------------
        Channel: 1
        label: MCA_R_To_Probe_Env
        unit: cm/s
        sigType: None
        nPoints: 30676
        -------------------------------

        """
        self.loadEXPDATHeader()
        # create dtype of the file
        dtypes = ('U11', 'i4')  # col 0: time (11 char string)   col 1: frame (32 bit int)
        dtypes = dtypes + ('f8',) * self.nChannels  # the other columns will be treated as float (8bits)

        rawData = np.genfromtxt(self.EXPDATfileName, delimiter=None, skip_header=self.sizeHeader, autostrip=True, names=','.join(self.signalLabels),
                                dtype=dtypes)

        nPoints = len(rawData)

        self.signals = []
        for i in range(self.nChannels):
            label = self.signalLabels[i + 2]
            newSignal = signal(channel=i, label=label, unit=self.signalUnits[i + 2], data=rawData[label], samplingRate_Hz=self.samplingRate_Hz,
                               operationsXML=self.PPoperationsNode)
            self.signals.append(newSignal)

        del self.signalLabels
        del self.signalUnits
        del self.samplingRate_Hz

    def saveSIG(self, filePath, channelList=None, format='csv', register=True):
        """
        Save data to a text file.

        This function is usually used to save processed signals

        Parameters
        ----------
        filePath : string
            Full path to the file. Extension is not needed since a **.SIG** will be automatically added to the end of the filename. If path has an extension, this function will replace the extension by **.SIG**

        channelList : list of integers, optional
            List of channels to save. If `None` (default) then all channels are saved in the file.

        format : string, optional
            File format. Avaiable values: 'csv', 'numpy', 'simple_text'

        **Notes**

        * This function calls :meth:`~signals.signal.saveData` from each instance of :class:`~signals.signal` in the list of channels.

        * See :meth:`~signals.signal.saveData` for details about the output file format.

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> for i in range(x.nChannels):
        >>>    x.signals[i].resample(100,method='quadratic') # resamples all channels at 100Hz, using quadratic interpolation
        >>> myCase.signals[2].calibrate(80,120,method='percentile') # calibrates channel 2  (presure) between 80 and 120mmHg, using percentile method
        >>>
        >>> myCase.saveSignals(fileName='/full/path/output1.SIG',channelList=None)  # saves all channels in output1.SIG
        >>> myCase.saveSignals(fileName='/full/path/output2.SIG',channelList=[0,2])  # saves only channels 0 and 2 in output2.SIG

        """
        print('Saving signal data...')

        if channelList is None:
            channelList = list(range(self.nChannels))

        if format.lower() == 'csv':
            outputFile = tools.setFileExtension(filePath, '.csv', case='lower')
            with open(outputFile, 'w') as fOut:
                fOut.write('CHANNEL;' + ';'.join([str(self.signals[ch].channel) for ch in channelList]) + '\n')
                fOut.write('LABEL;' + ';'.join([self.signals[ch].label for ch in channelList]) + '\n')
                fOut.write('UNIT;' + ';'.join([self.signals[ch].unit for ch in channelList]) + '\n')
                fOut.write('SIGNAL_TYPE;' + ';'.join([str(self.signals[ch].sigType) for ch in channelList]) + '\n')
                fOut.write('SAMPLING_RATE_(Hz);' + ';'.join([str(self.signals[ch].samplingRate_Hz) for ch in channelList]) + '\n')
                fOut.write('N_SAMPLES;' + ';'.join([str(self.signals[ch].nPoints) for ch in channelList]) + '\n')
                fOut.write('-------DATA START-------;\n')

                # build tuple  (time;ch0,ch1,...)
                listSignals = [self.signals[0].getTimeVector()]  # add time
                stringHeader = 'TIME (s)'
                for ch in channelList:
                    listSignals.append(self.signals[ch].data)  # add signals
                    stringHeader += ';ch%d' % ch

                signals = np.vstack(tuple(listSignals))

                fOut.write(stringHeader + '\n')
                np.savetxt(fOut, signals.T, delimiter=';', fmt='%1.8e')
                fOut.write('-------DATA END-------;\n')

        if format.lower() == 'numpy':
            outputFile = tools.setFileExtension(filePath, '.npy', case='lower')

            # build a structured array
            data = [(self.signals[ch].channel, self.signals[ch].label, self.signals[ch].unit, str(self.signals[ch].sigType),
                     self.signals[ch].samplingRate_Hz, self.signals[ch].getTimeVector(), self.signals[ch].data) for ch in channelList]

            # find sizes
            sizeLabel = max([len(self.signals[ch].label) for ch in channelList])
            sizeUnit = max([len(self.signals[ch].unit) for ch in channelList])
            sizeSigType = max([len(str(self.signals[ch].sigType)) for ch in channelList])
            sizeData = max([self.signals[ch].data.size for ch in channelList])

            dt = np.dtype([('channel', np.int32), ('label', 'U%d' % sizeLabel), ('unit', 'U%d' % sizeUnit), ('sigType', 'U%d' % sizeSigType),
                           ('samplingRate_(Hz)', np.float64), ('time_(s)', np.float64, (sizeData,)), ('data', np.float64, (sizeData,))])

            x = np.array(data, dtype=dt)
            np.save(outputFile, x)

        if format.lower() == 'simple_text':
            outputFile = tools.setFileExtension(filePath, '.sig', 'lower')
            fileObj = open(outputFile, 'w')

            for i in channelList:
                self.signals[i].saveData(fileObj)

            fileObj.close()

        if register:
            xmlElement = ETree.Element('SIGsave')
            tools.ETaddElement(parent=xmlElement, tag='channels', text=str(channelList).replace(',', ''))
            tools.ETaddElement(parent=xmlElement, tag='fileName', text=os.path.basename(filePath))
            tools.ETaddElement(parent=xmlElement, tag='format', text=format.lower())
            self.PPoperationsNode.append(xmlElement)

        print('Ok!')

        # channelList: list or None.  List with the channels to save.

    def saveB2B(self, filePath, channelList=None, format='csv', register=True):
        """
        Save beat-to-beat data to a text file.


        Parameters
        ----------
        filePath : string
            Full path to the file. Extension is not needed since a **.B2B** will be automatically added to the end of the filename. If path has an extension, this function will replace the extension by **.B2B**

        channelList : list of integers, optional
            List of channels to save. If `None` (default) then all channels are saved in the file.

        format : string, optional
            File format. Avaiable values: 'csv', 'numpy', 'simple_text'

        **Notes**

        * This function will save beat-to-beat data only if Beat-to-beat analysis was performed before. See :meth:`getBeat2beat`.
        * This function calls :meth:`~signals.signal.saveB2B` from each instance of :class:`~signals.signal` in the list of channels.

        * See :meth:`~signals.signal.saveB2B` for details about the output  file format.

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> myCase.findRRmarks(refChannel=2,method='ampd') # find RR marks with channel 2 as reference and ampd method
        >>> myCase.getBeat2beat(resampleRate_Hz=5.0,resampleMethod='cubic') # extract beat-to beat data and resample at 5Hz
        >>>
        >>> myCase.saveBeat2beat(fileName='/full/path/output1.B2B',channelList=None)  # saves all channels in output1.SIG

        """
        if not self.hasB2Bdata:
            print('No beat-to-beat data was found. Canceling save...')
            return

        print('Saving beat-to-beat data...')

        if channelList is None:
            channelList = list(range(self.nChannels))

        if format.lower() == 'csv':
            outputFile = tools.setFileExtension(filePath, '.csv', case='lower')
            with open(outputFile, 'w') as fOut:
                fOut.write('CHANNEL;' + ';;;'.join([str(self.signals[ch].channel) for ch in channelList]) + '\n')
                fOut.write('LABEL;' + ';;;'.join([self.signals[ch].label for ch in channelList]) + '\n')
                fOut.write('UNIT;' + ';;;'.join([self.signals[ch].unit for ch in channelList]) + '\n')
                fOut.write('SIGNAL_TYPE;' + ';;;'.join([str(self.signals[ch].sigType) for ch in channelList]) + '\n')
                fOut.write('SAMPLING_RATE_(Hz);' + ';;;'.join([str(self.signals[ch].samplingRate_Hz) for ch in channelList]) + '\n')
                fOut.write('N_SAMPLES;' + ';;;'.join([str(self.signals[ch].beat2beatData.nPoints) for ch in channelList]) + '\n')
                fOut.write('-------DATA START-------;\n')

                # build tuple  (time;ch0,ch1,...)
                listSignals = [self.signals[0].beat2beatData.xData]  # add time
                stringHeader = 'TIME (s)'
                for ch in channelList:
                    avgVec = self.signals[ch].beat2beatData.avg
                    minVec = self.signals[ch].beat2beatData.min
                    maxVec = self.signals[ch].beat2beatData.max
                    listSignals += [avgVec, minVec, maxVec]
                    stringHeader += ';AVG ch%d;MIN ch%d;MAX ch%d' % (ch, ch, ch)

                signals = np.vstack(tuple(listSignals))

                fOut.write(stringHeader + '\n')
                np.savetxt(fOut, signals.T, delimiter=';', fmt='%1.8e')
                fOut.write('-------DATA END-------;\n')

        if format.lower() == 'numpy':
            outputFile = tools.setFileExtension(filePath, '.npy', case='lower')

            # build a structured array
            data = [(self.signals[ch].channel, self.signals[ch].label, self.signals[ch].unit, str(self.signals[ch].sigType),
                     self.signals[ch].samplingRate_Hz, self.signals[ch].beat2beatData.xData, self.signals[ch].beat2beatData.avg,
                     self.signals[ch].beat2beatData.min, self.signals[ch].beat2beatData.max) for ch in channelList]

            # find sizes
            sizeLabel = max([len(self.signals[ch].label) for ch in channelList])
            sizeUnit = max([len(self.signals[ch].unit) for ch in channelList])
            sizeSigType = max([len(str(self.signals[ch].sigType)) for ch in channelList])
            sizeData = max([self.signals[ch].beat2beatData.xData.size for ch in channelList])

            dt = np.dtype([('channel', np.int32), ('label', 'U%d' % sizeLabel), ('unit', 'U%d' % sizeUnit), ('sigType', 'U%d' % sizeSigType),
                           ('samplingRate_(Hz)', np.float64), ('time_(s)', np.float64, (sizeData,)), ('avg', np.float64, (sizeData,)),
                           ('min', np.float64, (sizeData,)), ('max', np.float64, (sizeData,))])

            x = np.array(data, dtype=dt)
            np.save(outputFile, x)

        if format.lower() == 'simple_text':
            outputFile = tools.setFileExtension(filePath, '.b2b', 'lower')
            fileObj = open(outputFile, 'w')

            for i in channelList:
                self.signals[i].saveB2B(fileObj)

            fileObj.close()

        if register:
            xmlElement = ETree.Element('B2Bsave')
            tools.ETaddElement(parent=xmlElement, tag='channels', text=str(channelList).replace(',', ''))
            tools.ETaddElement(parent=xmlElement, tag='fileName', text=os.path.basename(filePath))
            tools.ETaddElement(parent=xmlElement, tag='format', text=format.lower())
            self.PPoperationsNode.append(xmlElement)

        print('Ok!')

    def saveJob(self, fileName, mergeImported=False):
        """
        Save the history of operations applied to the file.

        This functions saves all operations applied to the data, in the correct order. This allows for re-run the analysis on the same file or apply the same set of operations to different cases.

        Parameters
        ----------
        fileName : string
            Full path to the file. If the path has an extension, this function will replace the extension by the corresponding default extension,
            based on :arg:`section` argument

            file extension. As default:
            - **.PPO**: (Preprocessing operations)
            - **.ARO**: (Autoregulation operations)

        mergeImported: bool, optional
            If True, any imported opereations will be merged into de job file. Otherwise only the link to the operation file will be kept.
            (Default: False)

        section: strings
            Describes the section of the operations to save. Use oe of the following: 'preprocessing', 'ARanalysis'

        **PPO/ARO file formats**

        See :ref:`ppo_aro_file_format_label` for details about **.PPO** and **.ARO** file formats.


        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> for i in range(x.nChannels):
        >>>    x.signals[i].resample(100,method='quadratic') # resamples all channels at 100Hz, using quadratic interpolation
        >>> myCase.signals[2].calibrate(80,120,method='percentile') # calibrates channel 2  (presure) between 80 and 120mmHg, using percentile method
        >>> myCase.findRRmarks(refChannel=2,method='ampd') # find RR marks with channel 2 as reference and ampd method
        >>> myCase.getBeat2beat(resampleRate_Hz=5.0,resampleMethod='cubic') # extract beat-to beat data and resample at 5Hz
        >>>
        >>> myCase.saveOperations(fileName='/full/path/output1.PPO')

        The resulting **.PPO** of this example is::

            <?xml version="1.0" ?>
            <patient examDate="2016-06-30 13:07:47" file="data.EXP" nChannels="4" sizeHeader="6" version="0.1">
                <resample>
                    <sampleRate unit="Hz">100</sampleRate>
                    <method>quadratic</method>
                    <channel>0</channel>
                </resample>
                <resample>
                    <sampleRate unit="Hz">100</sampleRate>
                    <method>quadratic</method>
                    <channel>1</channel>
                </resample>
                <resample>
                    <sampleRate unit="Hz">100</sampleRate>
                    <method>quadratic</method>
                    <channel>2</channel>
                </resample>
                <resample>
                    <sampleRate unit="Hz">100</sampleRate>
                    <method>quadratic</method>
                    <channel>3</channel>
                </resample>
                <findRRmarks>
                    <refChannel>2</refChannel>
                    <method>ampd</method>
                    <findPeaks>True</findPeaks>
                    <findValleys>False</findValleys>
                </findRRmarks>
                <beat2beat>
                    <resampleMethod>cubic</resampleMethod>
                    <resampleRate_Hz>5.0</resampleRate_Hz>
                </beat2beat>
            </patient>

        """

        outputTree = copy.deepcopy(self.jobRootNode)

        print('Saving .job data...')
        filePath = tools.setFileExtension(fileName, '.job', 'lower')

        # remove empty entities
        self._removeEmptyOperations(outputTree)

        # keep the links to the files in case mergeImported=False
        if not mergeImported:
            for position, elem in enumerate(outputTree):
                if elem.tag == 'operations':
                    if tools.getElemAttrXpath(elem, xpath='.', attrName='imported', attrType='bool'):
                        outputTree.remove(elem)
                        newElem = ETree.Element('operationsFile')
                        newElem.text = tools.getElemAttrXpath(elem, xpath='.', attrName='operationsFile', attrType='str')
                        outputTree.insert(position, newElem)

        x = ETree.tostring(outputTree, pretty_print=True, encoding='UTF-8', xml_declaration=True)

        fileOut = open(filePath, 'wb')

        fileOut.write(x)
        fileOut.close()
        print('Ok!')

    def runPreprocessingOperations(self, operationsElem):
        """
        Apply the operations previously loaded.

        **Note**

        This function os automatically called during the initialization  :meth:`__init__` if the input is a **.PPO** file.

        """
        for operation in operationsElem:
            if operation.tag not in ['resample', 'setlabel', 'synchronize', 'findRRmarks', 'B2Bcalc', 'setType', 'calibrate', 'LPfilter',
                                     'interpolate', 'cropInterval', 'insertPeak', 'removePeak', 'SIGsave', 'B2Bsave', 'B2B_LPfilter']:
                print('Operation \'%s\' not recognized. Exiting...' % operation.tag)
                exit()

            if operation.tag == 'setType':
                typeSignal = tools.getElemValueXpath(operation, xpath='type', valType='str')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                print('Setting Type channel=%d: %s' % (channel, typeSignal))
                if typeSignal == 'None':
                    typeSignal = None
                self.signals[channel].setType(typeSignal, register=False)

            if operation.tag == 'setlabel':
                label = tools.getElemValueXpath(operation, xpath='label', valType='str')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                print('Setting Label channel=%d: %s' % (channel, label))
                self.signals[channel].setLabel(label, register=False)

            if operation.tag == 'resample':
                sampleRate = tools.getElemValueXpath(operation, xpath='sampleRate', valType='float')
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                print('Resampling channel=%d: Fs= %f, method=%s' % (channel, sampleRate, method))
                self.signals[channel].resample(sampleRate, method, register=False)

            if operation.tag == 'calibrate':
                valMin = tools.getElemValueXpath(operation, xpath='valMin', valType='float')
                valMax = tools.getElemValueXpath(operation, xpath='valMax', valType='float')
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                segmentIdx = tools.getElemValueXpath(operation, xpath='segmentIndexes', valType='list_int')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                print('Calibrating channel= %d: method= %s, valMin=%f, valMax=%f' % (channel, method, valMin, valMax))
                self.signals[channel].calibrate(valMax, valMin, method, segmentIdx, register=False)

            if operation.tag == 'synchronize':
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                if method == 'correlation':
                    channelList = tools.getElemValueXpath(operation, xpath='channels', valType='list_int')
                    print('Synchronizing Channels %s: method=%s' % (str(channelList), method))
                    self.synchronizeSignals(channelList, method, ABPdelay_s=None, register=False)
                if method == 'fixedAPB':
                    ABPdelay_s = tools.getElemValueXpath(operation, xpath='ABPdelay_s', valType='float')
                    print('Synchronizing ABP channel: method=%s' % (method))
                    self.synchronizeSignals([], method, ABPdelay_s, register=False)

            if operation.tag == 'LPfilter':
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                if method == 'movingAverage' or method == 'median':
                    Ntaps = tools.getElemValueXpath(operation, xpath='Ntaps', valType='int')
                    print('Low Pass filter channel=%d: method=%s, Ntaps=%d' % (channel, method, Ntaps))
                    self.signals[channel].LPfilter(method, nTaps=Ntaps, order=None, register=False)
                if method == 'butterworth':
                    order = tools.getElemValueXpath(operation, xpath='order', valType='int')
                    print('Low Pass filter channel=%d: method=%s, Ntaps=%d' % (channel, method, Ntaps))
                    self.signals[channel].LPfilter(method, nTaps=None, order=order, register=False)

            if operation.tag == 'interpolate':
                frameStart = tools.getElemValueXpath(operation, xpath='frameStart', valType='int')
                frameEnd = tools.getElemValueXpath(operation, xpath='frameEnd', valType='int')
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                print('Interpolating channel=%d: start=%d, end=%d, method=%s' % (channel, frameStart, frameEnd, method))
                self.signals[channel].interpolate(frameStart, frameEnd, method, register=False)

            if operation.tag == 'cropInterval':
                frameStart = tools.getElemValueXpath(operation, xpath='frameStart', valType='int')
                frameEnd = tools.getElemValueXpath(operation, xpath='frameEnd', valType='int')
                RemoveSegment = tools.getElemValueXpath(operation, xpath='RemoveSegment', valType='bool')
                segmentIndexes = tools.getElemValueXpath(operation, xpath='segmentIndexes', valType='list_int')
                channel = tools.getElemValueXpath(operation, xpath='channel', valType='int')
                print('Cropping channel %s: start=%d, end=%d, removeSegment=%s' % (channel, frameStart, frameEnd, str(RemoveSegment)))
                self.signals[channel].cropInterval(frameStart, frameEnd, False, RemoveSegment, segmentIndexes)

            if operation.tag == 'findRRmarks':
                refChannel = tools.getElemValueXpath(operation, xpath='refChannel', valType='int')
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                findPeaks = tools.getElemValueXpath(operation, xpath='findPeaks', valType='bool')
                findValleys = tools.getElemValueXpath(operation, xpath='findValleys', valType='bool')
                print('Finding RRmarks: refChannel=%d method=%s findPeaks=%s findValleys=%s' % (refChannel, method, findPeaks, findValleys))
                self.findRRmarks(refChannel, method, findPeaks, findValleys, register=False)

            if operation.tag == 'insertPeak':
                newIdx = tools.getElemValueXpath(operation, xpath='newIdx', valType='int')
                isPeak = tools.getElemValueXpath(operation, xpath='isPeak', valType='bool')
                print('Inserting Peak: newIdx=%d, isPeak=%s' % (newIdx, str(isPeak)))
                self.insertPeak(newIdx, isPeak, register=False)

            if operation.tag == 'removePeak':
                Idx = tools.getElemValueXpath(operation, xpath='Idx', valType='int')
                isPeak = tools.getElemValueXpath(operation, xpath='isPeak', valType='bool')
                print('Removing Peak: Idx=%d, isPeak=%s' % (Idx, str(isPeak)))
                self.removePeak(Idx, isPeak, register=False)

            if operation.tag == 'SIGsave':
                channelList = tools.getElemValueXpath(operation, xpath='channels', valType='list_int')
                format = tools.getElemValueXpath(operation, xpath='format', valType='str')
                fileName = tools.getElemValueXpath(operation, xpath='fileName', valType='str')
                print('SIGsave: Channels%s filename=%s format=%s' % (str(channelList), fileName, format))
                self.saveSIG(self.dirName + fileName, channelList, format, register=False)

            if operation.tag == 'B2Bcalc':
                resampleMethod = tools.getElemValueXpath(operation, xpath='resampleMethod', valType='str')
                resampleRate_Hz = tools.getElemValueXpath(operation, xpath='resampleRate_Hz', valType='float')
                print('Extracting beat-to-beat data: resampleMethod=%s, Freq=%f' % (resampleMethod, resampleRate_Hz))
                self.getBeat2beat(resampleRate_Hz, resampleMethod, register=False)

            if operation.tag == 'B2Bsave':
                channelList = tools.getElemValueXpath(operation, xpath='channels', valType='list_int')
                format = tools.getElemValueXpath(operation, xpath='format', valType='str')
                fileName = tools.getElemValueXpath(operation, xpath='fileName', valType='str')
                print('B2Bsave: Channels%s filename=%s format=%s' % (str(channelList), fileName, format))
                self.saveB2B(self.dirName + fileName, channelList, format, register=False)

            if operation.tag == 'B2B_LPfilter':
                method = tools.getElemValueXpath(operation, xpath='method', valType='str')
                Ntaps = tools.getElemValueXpath(operation, xpath='Ntaps', valType='int')
                print('B2B LP filter: method=%s, Ntaps=%d' % (method, Ntaps))
                self.LPfilterBeat2beat(method, Ntaps, register=False)

    def runARanalysisOperations(self, operationsElem):
        """
            Apply the operations previously loaded.

            **Note**

            This function os automatically called during the initialization  :meth:`__init__` if the input is a **.PPO** file.

            """
        for operation in operationsElem:
            if operation.tag not in ['PSDwelch', 'PSDsave', 'TFA', 'TFAsave', 'TFAsaveStat', 'ARI', 'ARIsave']:
                print('Operation \'%s\' not recognized. Exiting...' % operation.tag)
                exit()

            if operation.tag == 'PSDwelch':
                useB2B = tools.getElemValueXpath(operation, xpath='useB2B', valType='bool')
                overlap = tools.getElemValueXpath(operation, xpath='overlap', valType='float')
                segmentLength_s = tools.getElemValueXpath(operation, xpath='segmentLength_s', valType='float')
                windowType = tools.getElemValueXpath(operation, xpath='windowType', valType='str')
                removeBias = tools.getElemValueXpath(operation, xpath='removeBias', valType='bool')
                filterType = tools.getElemValueXpath(operation, xpath='filterType', valType='str')
                nTapsFilter = tools.getElemValueXpath(operation, xpath='nTapsFilter', valType='int')
                print('Computing PSDwelch: useB2B=%s overlap=%f segmentLength_s=%f windowType=%s removeBias=%s filterType=%s  nTapsFilter=%d' % (
                    str(useB2B), overlap, segmentLength_s, windowType, str(removeBias), filterType, nTapsFilter))
                self.computePSDwelch(useB2B, overlap, segmentLength_s, windowType, removeBias, filterType, nTapsFilter, register=False)

            if operation.tag == 'PSDsave':
                fileName = tools.getElemValueXpath(operation, xpath='fileName', valType='str')
                format = tools.getElemValueXpath(operation, xpath='format', valType='str')
                freqRange = tools.getElemValueXpath(operation, xpath='freqRange', valType='str')
                print('PSDsave: freqRange%s filename=%s format=%s' % (freqRange, fileName, format))
                self.savePSD(self.dirName + fileName, format, freqRange, register=False)

            if operation.tag == 'TFA':
                estimatorType = tools.getElemValueXpath(operation, xpath='estimatorType', valType='str')
                print('TFA: estimatorType=%s' % estimatorType)
                self.computeTFA(estimatorType, register=False)

            if operation.tag == 'TFAsave':
                fileName = tools.getElemValueXpath(operation, xpath='fileName', valType='str')
                format = tools.getElemValueXpath(operation, xpath='format', valType='str')
                freqRange = tools.getElemValueXpath(operation, xpath='freqRange', valType='str')
                print('TFAsave: format=%s freqRange=%s fileName=%s' % (format, freqRange, fileName))
                self.saveTF(self.dirName + fileName, format, freqRange, register=False)

            if operation.tag == 'TFAsaveStat':
                fileName = tools.getElemValueXpath(operation, xpath='fileName', valType='str')
                plotFileFormat = tools.getElemValueXpath(operation, xpath='plotFileFormat', valType='str')
                remNegPhase = tools.getElemValueXpath(operation, xpath='remNegPhase', valType='bool')
                coheTreshold = tools.getElemValueXpath(operation, xpath='coheTreshold', valType='bool')
                print('TFAsaveStat: remNegPhase=%s coheTreshold=%s fileName=%s  plotFileFormat=%s' % (
                    str(remNegPhase), str(coheTreshold), fileName, plotFileFormat))
                self.saveTFAstatistics(self.dirName + fileName, plotFileFormat, coheTreshold, remNegPhase, register=False)

            if operation.tag == 'ARI':
                print('ARI:')
                self.computeARI(register=False)

            if operation.tag == 'ARIsave':
                fileName = tools.getElemValueXpath(operation, xpath='fileName', valType='str')
                format = tools.getElemValueXpath(operation, xpath='format', valType='str')
                print('ARIsave: format=%s fileName=%s' % (format, fileName))
                self.saveARI(self.dirName + fileName, format, register=False)

    def findChannel(self, attribute, identifier):
        """
        Get channel number given its identifier of an attribute

        Parameters
        ----------
        attribute : string {'label', 'type'}
            Attribute under consideration

        identifier: string
            Identifier of the channel

        Returns
        -------
        index : int or None.
            Index of the channel or `None` in case of failure.


        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> print(myCase.listChannels('label'))
        ['MCA_L_To_Probe_Env', 'MCA_R_To_Probe_Env', 'Analog_1', 'Analog_8']
        >>> print(myCase.findChannel('label','Analog_1'))
        2
        >>> print(myCase.findChannel('label','Analog_2'))
        None

        """
        try:
            return self.listChannels(attribute).index(identifier)
        except:
            return None

    def listChannels(self, attribute):
        """
        Return a list of values of the attribute from all channels

        Parameters
        ----------
        attribute : string {'label', 'type'}
            Attribute under consideration

        Returns
        -------
        attrs : list
            list containing the values of the attributes


        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> print(myCase.listChannels('label'))
        ['MCA_L_To_Probe_Env', 'MCA_R_To_Probe_Env', 'Analog_1', 'Analog_8']

        """
        if attribute.lower() == 'label':
            return [x.label for x in self.signals]
        if attribute.lower() == 'type':
            return [x.sigType for x in self.signals]

    def findRRmarks(self, refChannel, method='ampd', findPeaks=True, findValleys=False, register=True):
        """
        Find RR mark locations, given a reference signal.

        This function detect RR intervals, given a channel used as reference. The marks are detected by looking for its local maxima and/or minima. RR marks locations, in samples, are stored in :attr:`peakIdx` and/or `valleyIdx` respectively.


        Parameters
        ----------
        refChannel : int
            Channel number of the signal used as reference

        method : string  {'ampd', 'md'}
            peak detection algorithm. Default: 'ampd'
            * AMPD: Automatic Multiscale Peak Detection (AMPD) by Felix Scholkmann et al., 2012 <https://github.com/LucaCerina/ampdLib>
            * MD: Based on Marco Duarte's implementation <https://github.com/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb>

        findPeaks : bool, optional
            Detect local maxima of the signal. Default: True

        findValleys : bool, optional
            Detect local minima of the signal. Default: False

        register : bool, optional
            include this operation in the list of preprocessing operations. If False then the operation will not be stored.


        **Notes**

        * This function calls :meth:`~signals.signal.findPeaks` from each instance of :class:`~signals.signal` in the list of channels.

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> myCase.findRRmarks(refChannel=0,method='ampd',findPeaks=True,findValleys=False,register=False) # find local maxima using channel 0 as reference. Does not register the operation
        >>> myCase.removeRRmarks()  # remove RRmark information
        >>> myCase.findRRmarks(refChannel=2,method='ampd',findPeaks=True,findValleys=True,register=True) # find local maxima and minima using channel 2 as reference. Register the operation

        """
        [self.peakIdx, _, self.valleyIdx, _] = self.signals[refChannel].findPeaks(method, findPeaks, findValleys, register=False)
        self.hasRRmarks = True

        # register operation
        if register:
            xmlElement = ETree.Element('findRRmarks')
            tools.ETaddElement(parent=xmlElement, tag='refChannel', text=str(refChannel))
            tools.ETaddElement(parent=xmlElement, tag='method', text=method)
            tools.ETaddElement(parent=xmlElement, tag='findPeaks', text=str(findPeaks))
            tools.ETaddElement(parent=xmlElement, tag='findValleys', text=str(findValleys))
            self.PPoperationsNode.append(xmlElement)

    def insertPeak(self, newIdx, isPeak=True, register=True):
        """
        Insert extra peak/valley mark

        This function is used to insert a new RR mark to the list of peaks/valleys

        Parameters
        ----------
        newIdx : int
            indice of the new peak/valley

        isPeak : bool, optional
            Register the new index as a peak if True (default) or valley if False.

        register : bool, optional
            include this operation in the list of preprocessing operations. If False then the operation will not be stored.


        **Notes**

        * If a peak is already registered at the given `newIdx`, no peak is added and the function ends without any error or warning messages.
        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> myCase.findRRmarks(refChannel=2,method='ampd',findPeaks=True,findValleys=True,register=True)
        >>> myCase.insertPeak(1200,isPeak=True,register=True) # add a peak at 1200
        """
        if not self.hasRRmarks:
            return

        if isPeak:
            pos = np.searchsorted(self.peakIdx, newIdx)
            self.peakIdx = np.insert(self.peakIdx, pos, newIdx)
            self.peakIdx = np.unique(self.peakIdx)  # removes eventual repeated indexes
        else:
            pos = np.searchsorted(self.valleyIdx, newIdx)
            self.valleyIdx = np.insert(self.valleyIdx, pos, newIdx)
            self.valleyIdx = np.unique(self.valleyIdx)  # removes eventual repeated indexes

        # register operation
        if register:
            xmlElement = ETree.Element('insertPeak')
            tools.ETaddElement(parent=xmlElement, tag='newIdx', text=str(newIdx))
            tools.ETaddElement(parent=xmlElement, tag='isPeak', text=str(isPeak))
            self.PPoperationsNode.append(xmlElement)

    def removePeak(self, Idx, isPeak=True, register=True):
        """
        Remove a peak/valley mark

        This function is used to remove RR marks from the list of peaks/valleys

        Parameters
        ----------
        Idx : int
            indice of the peak/valley to be removed

        isPeak : bool, optional
            Removes a peak if True (default) or valley if False.

        register : bool, optional
            include this operation in the list of preprocessing operations. If False then the operation will not be stored.


        **Note**
        * If a peak is not registered at the given `Idx`, no peak is removed and the function ends without any error or warning messages.


        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> myCase.findRRmarks(refChannel=2,method='ampd',findPeaks=True,findValleys=True,register=True)
        >>> myCase.insertPeak(1200,isPeak=True,register=True) # add a peak at 1200
        >>> myCase.removePeak(1200,isPeak=True,register=True) # remove the peak at 1200
        """
        if not self.hasRRmarks:
            return

        if isPeak:
            pos = np.searchsorted(self.peakIdx, Idx)
            if pos == 0 or (pos == len(self.peakIdx) - 1):
                self.peakIdx = np.delete(self.peakIdx, pos)
                return
            else:
                if abs(Idx - self.peakIdx[pos - 1]) < abs(Idx - self.peakIdx[pos]):
                    self.peakIdx = np.delete(self.peakIdx, pos - 1)
                else:
                    self.peakIdx = np.delete(self.peakIdx, pos)
        else:
            pos = np.searchsorted(self.peakIdx, Idx)

            if pos == 0 or (pos == len(self.valleyIdx) - 1):
                self.valleyIdx = np.delete(self.valleyIdx, pos)
                return
            else:
                if abs(Idx - self.valleyIdx[pos - 1]) < abs(Idx - self.valleyIdx[pos]):
                    self.valleyIdx = np.delete(self.valleyIdx, pos - 1)
                else:
                    self.valleyIdx = np.delete(self.valleyIdx, pos)

        # register operation
        if register:
            xmlElement = ETree.Element('removePeak')
            tools.ETaddElement(parent=xmlElement, tag='Idx', text=str(Idx))
            tools.ETaddElement(parent=xmlElement, tag='isPeak', text=str(isPeak))
            self.PPoperationsNode.append(xmlElement)

    def removeRRmarks(self):
        """
        cleanup RR interval information

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> myCase.findRRmarks(refChannel=0,method='ampd',findPeaks=True,findValleys=False,register=False)
        >>> myCase.removeRRmarks()  # remove RRmark information

        """
        if not self.hasRRmarks:
            return

        try:
            del self.peakIdx
        except AttributeError:
            pass
        try:
            del self.valleyIdx
        except AttributeError:
            pass

        self.hasRRmarks = False

    def synchronizeSignals(self, channelList, method='correlation', ABPdelay_s=0.0, register=True):
        """
        Synchronize the channels


        Parameters
        ----------
        channelList : list of integers
            List of channels to synchronize. This argument is used only when method='correlation'

        method : string  {'correlation', 'fixedAPB'}
            synchronization method. Default: 'correlation'

            * fixedAPB: Based on Marco Duarte's implementation <https://github.com/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb>

        ABPdelay_s : float
            Arterial blood pressure fxed delay in seconds. This argument is used only when method='fixedAPB'.

        register : bool, optional
            include this operation in the list of preprocessing operations. If False then the operation will not be stored.


        **Algorithms**

        * Correlation: synchronization is based on the correlation between the channels. For each two channels, the delay is define by the index of the peak in correlation between the channels.

        * fixedABP: Only the arterial blood pressure (ABP) channel is delayed. The argument `ABPdelay_s` defines the delay, in seconds. This algorithms will look for the APB channel. See :meth:`~signals.signal.setType`.


        After the synchronization, each channel might be cropped on one or both sides to comply with the new timespan, defined by the time interval in common across all channels. See figure below.

        .. image:: ./images/sync.png
            :width: 900px
            :align: center

        **Example**

        >>> from patientData import patientData as pD
        >>> myCase=pD('data.EXP')
        >>> myCase.loadData()
        >>> myCase.synchronizeSignals(channelList=[0,1,2],method='correlation',ABPdelay_s=0.0,register=True) # synchronize channels 0, 1 and 2, using correlation method
        >>> myCase.signals[2].setType('ABP')
        >>> myCase.synchronizeSignals(channelList=None,method='fixedAPB',ABPdelay_s=0.2,register=True) # synchronize ABP channel, using the fixed delay method

        """

        self.removeRRmarks()
        delays = []

        if method == 'correlation':
            if len(channelList) == 0:
                return

            # delays with respect to ABP channel
            for s in self.signals:  # finds ABP channel  # delay in samples
                if s.sigType == 'ABP':
                    refChannel = s.channel

            for ch in channelList:
                # based on:  https://stackoverflow.com/questions/4688715/find-time-shift-between-two-similar-waveforms
                delaySamples = np.argmax(scipySignal.correlate(self.signals[refChannel].data, self.signals[ch].data)) - (
                  len(self.signals[refChannel].data) - 1)
                delays.append(delaySamples)
            delays = [-(x - max(delays)) for x in delays]

        if method == 'fixedAPB':
            for s in self.signals:  # finds ABP channel  # delay in samples
                if s.sigType == 'ABP':
                    delaySamples = int(ABPdelay_s * s.samplingRate_Hz)
                    delays.append(delaySamples)
                else:
                    delays.append(0)

            if ABPdelay_s < 0:
                delays = [x - delaySamples for x in delays]
            channelList = range(self.nChannels)

        length = []
        for ch in range(len(channelList)):
            channel = channelList[ch]
            delay = delays[ch]
            # print('ch: %d   delay:%d' %(channel,delay))
            self.signals[channel].cropFromLeft(delay, register=False)
            length.append(self.signals[channel].nPoints)

        minLength = min(length)
        for ch in range(self.nChannels):
            self.signals[ch].cropFromRight(self.signals[ch].nPoints - minLength, register=False)

        # register operation
        if register:
            xmlElement = ETree.Element('synchronize')
            tools.ETaddElement(parent=xmlElement, tag='method', text=method)
            if method == 'correlation':
                tools.ETaddElement(parent=xmlElement, tag='channels', text=str(channelList).replace(',', ''))
            if method == 'fixedAPB':
                tools.ETaddElement(parent=xmlElement, tag='ABPdelay_s', text=str(ABPdelay_s))
            self.PPoperationsNode.append(xmlElement)

    def getBeat2beat(self, resampleRate_Hz=100.0, resampleMethod='linear', register=True):

        self.hasB2Bdata = True
        for ch in range(self.nChannels):
            self.signals[ch].beat2beat(self.peakIdx, resampleRate_Hz, resampleMethod)  # print(self.signals[ch].beat2beatData.max)

        # register operation
        if register:
            xmlElement = ETree.Element('B2Bcalc')
            tools.ETaddElement(parent=xmlElement, tag='resampleMethod', text=resampleMethod)
            tools.ETaddElement(parent=xmlElement, tag='resampleRate_Hz', text=str(resampleRate_Hz))
            self.PPoperationsNode.append(xmlElement)

    def removeBeat2beat(self):
        if not self.hasB2Bdata:
            return

        for ch in range(self.nChannels):
            try:
                del self.signals[ch].beat2beatData
            except AttributeError:
                pass
        self.hasB2Bdata = False

    def LPfilterBeat2beat(self, method='movvalueingAverage', nTaps=5, register=True):

        if not self.hasB2Bdata:
            print('Error: B2Bdata not found...')
            return

        for s in self.signals:
            s.beat2beatData.LPfilter(method, nTaps)

        # register operation
        if register:
            xmlElement = ETree.Element('B2B_LPfilter')
            tools.ETaddElement(parent=xmlElement, tag='method', text=str(method))
            tools.ETaddElement(parent=xmlElement, tag='Ntaps', text=str(nTaps))
            self.PPoperationsNode.append(xmlElement)

    # filterType: valid values: 'triangular', 'rect', None (no filter)
    def computePSDwelch(self, useB2B=True, overlap=0.5, segmentLength_s=100, windowType='hanning', removeBias=True, filterType=None, nTapsFilter=3,
                        register=True):
        # find ABP and CBFV channels
        ABP_channel = None
        CBFv_R_channel = None
        CBFv_L_channel = None
        for s in self.signals:
            if s.sigType == 'ABP':
                ABP_channel = s.channel
            if s.sigType == 'CBFV_R':
                CBFv_R_channel = s.channel
            if s.sigType == 'CBFV_L':
                CBFv_L_channel = s.channel

        # left side
        if (ABP_channel is not None) and (CBFv_L_channel is not None):
            if useB2B:
                inputSignal = self.signals[ABP_channel].beat2beatData.avg
                outputSignal = self.signals[CBFv_L_channel].beat2beatData.avg
                Fs = self.signals[ABP_channel].beat2beatData.samplingRate_Hz
            else:
                inputSignal = self.signals[ABP_channel].data
                outputSignal = self.signals[CBFv_L_channel].data
                Fs = self.signals[ABP_channel].samplingRate_Hz

            self.PSD_L = PSDestimator(inputSignal, outputSignal, Fs, overlap, segmentLength_s, windowType, removeBias)
            self.PSD_L.computeWelch()
            self.hasPSDdata_L = True

            if filterType is not None:
                self.PSD_L.filterAll(filterType, nTapsFilter, keepFirst=True)
        else:
            self.hasPSDdata_L = False

        # right channel
        if (ABP_channel is not None) and (CBFv_R_channel is not None):
            if useB2B:
                inputSignal = self.signals[ABP_channel].beat2beatData.avg
                outputSignal = self.signals[CBFv_R_channel].beat2beatData.avg
                Fs = self.signals[ABP_channel].beat2beatData.samplingRate_Hz
            else:
                inputSignal = self.signals[ABP_channel].data
                outputSignal = self.signals[CBFv_R_channel].data
                Fs = self.signals[ABP_channel].samplingRate_Hz

            self.PSD_R = PSDestimator(inputSignal, outputSignal, Fs, overlap, segmentLength_s, windowType, removeBias)
            self.PSD_R.computeWelch()
            self.hasPSDdata_R = True

            if filterType is not None:
                self.PSD_R.filterAll(filterType, nTapsFilter, keepFirst=True)
        else:
            self.hasPSDdata_R = False

        if register:
            xmlElement = ETree.Element('PSDwelch')
            tools.ETaddElement(parent=xmlElement, tag='useB2B', text=str(useB2B))
            tools.ETaddElement(parent=xmlElement, tag='overlap', text=str(overlap))
            tools.ETaddElement(parent=xmlElement, tag='segmentLength_s', text=str(segmentLength_s))
            tools.ETaddElement(parent=xmlElement, tag='windowType', text=windowType)
            tools.ETaddElement(parent=xmlElement, tag='removeBias', text=str(removeBias))
            if filterType is None:
                tools.ETaddElement(parent=xmlElement, tag='filterType', text='None')
            else:
                tools.ETaddElement(parent=xmlElement, tag='filterType', text=filterType)
                tools.ETaddElement(parent=xmlElement, tag='nTapsFilter', text=str(nTapsFilter))
            self.ARoperationsNode.append(xmlElement)

    # fileName: file with .psd extension
    def savePSD(self, filePath, format='csv', freqRange='ALL', register=True):
        # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
        # format : string, optional
        #    File format. Avaiable values: 'csv', 'numpy', 'simple_text'

        if (not self.hasPSDdata_L) and (not self.hasPSDdata_R):
            print('No power spectrum data was found. Canceling save...')
            return

        print('Saving power spectrum density data')

        if format.lower() == 'simple_text':
            outputFile = tools.setFileExtension(filePath, '.psd', case='lower')
            if self.hasPSDdata_L and self.hasPSDdata_R:
                self.PSD_L.save(outputFile, 'L', writeMode='w')
                self.PSD_R.save(outputFile, 'R', writeMode='a')
            else:
                if self.hasPSDdata_L:
                    self.PSD_L.save(outputFile, 'L', writeMode='w')
                if self.hasPSDdata_R:
                    self.PSD_R.save(outputFile, 'R', writeMode='w')

        else:
            signals = []
            header = ''

            if self.hasPSDdata_L:
                freq_L = self.PSD_L.freqRangeExtractor.getFreq(freqRange)
                nPoints = len(freq_L)
                Sxx_L = self.PSD_L.freqRangeExtractor.getSignal(self.PSD_L.Sxx, freqRange)
                Syy_L = self.PSD_L.freqRangeExtractor.getSignal(self.PSD_L.Syy, freqRange)
                Sxy_L = self.PSD_L.freqRangeExtractor.getSignal(self.PSD_L.Sxy, freqRange)
                Syx_L = self.PSD_L.freqRangeExtractor.getSignal(self.PSD_L.Syx, freqRange)
                signals += [freq_L, Sxx_L, Syy_L, np.real(Sxy_L), np.imag(Sxy_L), np.real(Syx_L), np.imag(Syx_L)]
                header += 'freq (Hz);Sxx_L;Syy_L;Sxy_L (real part);Sxy_L (imag part);Syx_L (real part);Syx_L (imag part);'
            if self.hasPSDdata_R:
                freq_R = self.PSD_R.freqRangeExtractor.getFreq(freqRange)
                nPoints = len(freq_R)
                Sxx_R = self.PSD_R.freqRangeExtractor.getSignal(self.PSD_R.Sxx, freqRange)
                Syy_R = self.PSD_R.freqRangeExtractor.getSignal(self.PSD_R.Syy, freqRange)
                Sxy_R = self.PSD_R.freqRangeExtractor.getSignal(self.PSD_R.Sxy, freqRange)
                Syx_R = self.PSD_R.freqRangeExtractor.getSignal(self.PSD_R.Syx, freqRange)
                # add frequency vector only if there is no left PSD data
                if not self.hasPSDdata_L:
                    signals += [freq_R, Sxx_R, Syy_R, np.real(Sxy_R), np.imag(Sxy_R), np.real(Syx_R), np.imag(Syx_R)]
                    header += 'freq (Hz);Sxx_R;Syy_R;Sxy_R (real part);Sxy_R (imag part);Syx_R (real part);Syx_R (imag part);'
                else:
                    signals += [Sxx_R, Syy_R, np.real(Sxy_R), np.imag(Sxy_R), np.real(Syx_R), np.imag(Syx_R)]
                    header += 'Sxx_R;Syy_R;Sxy_R (real part);Sxy_R (imag part);Syx_R (real part);Syx_R (imag part);'

            if format.lower() == 'csv':
                outputFile = tools.setFileExtension(filePath, '.csv', case='lower')
                with open(outputFile, 'w') as fOut:
                    fOut.write('NPOINTS;%d\n' % nPoints)
                    fOut.write('-------DATA START-------;\n')
                    fOut.write(header + '\n')
                    signals = np.vstack(tuple(signals))
                    np.savetxt(fOut, signals.T, delimiter=';', fmt='%1.15e')
                    fOut.write('-------DATA END-------;\n')

            if format.lower() == 'numpy':
                outputFile = tools.setFileExtension(filePath, '.npy', case='lower')

                # build a structured array
                data = []
                if self.hasPSDdata_L:
                    data.append(('L', freq_L, Sxx_L, Syy_L, Sxy_L, Syx_L))
                if self.hasPSDdata_R:
                    data.append(('R', freq_R, Sxx_R, Syy_R, Sxy_R, Syx_R))

                dt = np.dtype(
                  [('side', 'U1'), ('freq_(Hz)', np.float64, (nPoints,)), ('Sxx', np.float64, (nPoints,)), ('Syy', np.float64, (nPoints,)),
                   ('Sxy', np.complex128, (nPoints,)), ('Syx', np.complex128, (nPoints,))])

                x = np.array(data, dtype=dt)
                np.save(outputFile, x)

        if register:
            xmlElement = ETree.Element('PSDsave')
            tools.ETaddElement(parent=xmlElement, tag='fileName', text=os.path.basename(filePath))
            tools.ETaddElement(parent=xmlElement, tag='format', text=format.lower())
            tools.ETaddElement(parent=xmlElement, tag='freqRange', text=freqRange)
            self.ARoperationsNode.append(xmlElement)

        print('Ok!')

    # estimatorType:  'H1'   or 'H2'
    def computeTFA(self, estimatorType='H1', register=True):

        if self.hasPSDdata_L:
            self.TFA_L = transferFunctionAnalysis(welchData=self.PSD_L)
            if estimatorType.upper() == 'H1':
                self.TFA_L.computeH1()
            if estimatorType.upper() == 'H2':
                self.TFA_L.computeH2()
            self.hasTFdata_L = True

        if self.hasPSDdata_R:
            self.TFA_R = transferFunctionAnalysis(welchData=self.PSD_R)
            if estimatorType.upper() == 'H1':
                self.TFA_R.computeH1()
            if estimatorType.upper() == 'H2':
                self.TFA_R.computeH2()
            self.hasTFdata_R = True

        # self.TFA_R.savePlot(fileNamePrefix=None)

        if register:
            xmlElement = ETree.Element('TFA')
            tools.ETaddElement(parent=xmlElement, tag='estimatorType', text=estimatorType)
            self.ARoperationsNode.append(xmlElement)

    # fileName: file with .tf extension
    def saveTF(self, filePath, format='csv', freqRange='ALL', register=True):
        # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'

        if (not self.hasTFdata_L) and (not self.hasTFdata_R):
            print('No transfer function data was found. Canceling save...')
            return

        if format.lower() == 'simple_text':
            outputFile = tools.setFileExtension(filePath, '.tf', case='lower')
            if self.hasTFdata_L and self.hasTFdata_L:
                self.TFA_L.save(outputFile, freqRange, 'L', writeMode='w')
                self.TFA_R.save(outputFile, freqRange, 'R', writeMode='a')
            else:
                if self.hasTFdata_L:
                    self.TFA_L.save(outputFile, freqRange, 'L', writeMode='w')
                if self.hasTFdata_L:
                    self.TFA_R.save(outputFile, freqRange, 'R', writeMode='w')

        else:
            signals = []
            header = ''
            if self.hasTFdata_L:
                freq_L = self.TFA_L.getFreq(freqRange)
                nPoints = len(freq_L)
                H_L = self.TFA_L.getH(freqRange)
                Gain_L = self.TFA_L.getGain(freqRange)
                Phase_deg_L = self.TFA_L.getPhase(freqRange) * 180.0 / np.pi
                Coherence_L = self.TFA_L.getCoherence(freqRange)
                signals += [freq_L, np.real(H_L), np.imag(H_L), Gain_L, Phase_deg_L, Coherence_L]
                header += 'freq (Hz);H_L (real part);H_L (imag part);Gain_L;Phase_deg_L;Coherence_L;'
            if self.hasTFdata_R:
                freq_R = self.TFA_R.getFreq(freqRange)
                nPoints = len(freq_R)
                H_R = self.TFA_R.getH(freqRange)
                Gain_R = self.TFA_R.getGain(freqRange)
                Phase_deg_R = self.TFA_R.getPhase(freqRange) * 180.0 / np.pi
                Coherence_R = self.TFA_R.getCoherence(freqRange)
                # add frequency vector only if there is no left PSD data
                if not self.hasTFdata_L:
                    signals += [freq_R, np.real(H_R), np.imag(H_R), Gain_R, Phase_deg_R, Coherence_R]
                    header += 'freq (Hz);H_R (real part);H_R (imag part);Gain_R;Phase_deg_R;Coherence_R;'
                else:
                    signals += [np.real(H_R), np.imag(H_R), Gain_R, Phase_deg_R, Coherence_R]
                    header += 'H_R (real part);H_R (imag part);Gain_R;Phase_deg_R;Coherence_R;'

            if format.lower() == 'csv':
                outputFile = tools.setFileExtension(filePath, '.csv', case='lower')
                with open(outputFile, 'w') as fOut:
                    fOut.write('NPOINTS;%d\n' % nPoints)
                    fOut.write('-------DATA START-------;\n')
                    fOut.write(header + '\n')
                    signals = np.vstack(tuple(signals))
                    np.savetxt(fOut, signals.T, delimiter=';', fmt='%1.15e')
                    fOut.write('-------DATA END-------;\n')

            if format.lower() == 'numpy':
                outputFile = tools.setFileExtension(filePath, '.npy', case='lower')

                # build a structured array
                data = []
                if self.hasTFdata_L:
                    data.append(('L', freq_L, H_L, Gain_L, Phase_deg_L, Coherence_L))
                if self.hasTFdata_L:
                    data.append(('R', freq_R, H_R, Gain_R, Phase_deg_R, Coherence_R))

                dt = np.dtype(
                  [('side', 'U1'), ('freq_(Hz)', np.float64, (nPoints,)), ('H', np.complex128, (nPoints,)), ('gain', np.float64, (nPoints,)),
                   ('phase_(deg)', np.float64, (nPoints,)), ('coherence', np.float64, (nPoints,))])

                x = np.array(data, dtype=dt)
                np.save(outputFile, x)

        if register:
            xmlElement = ETree.Element('TFAsave')
            tools.ETaddElement(parent=xmlElement, tag='fileName', text=os.path.basename(filePath))
            tools.ETaddElement(parent=xmlElement, tag='format', text=format.lower())
            tools.ETaddElement(parent=xmlElement, tag='freqRange', text=freqRange)
            self.ARoperationsNode.append(xmlElement)

        print('Ok!')

    def saveTFAstatistics(self, filePath, plotFileFormat, coheTreshold=False, remNegPhase=False, register=True):
        # plotFileFormat: valid formats:

        if plotFileFormat.lower() not in ['png', 'jpg', 'tif', 'pdf', 'svg', 'eps', 'ps']:
            print('TFA Plot file format \'%s\' not recognized. Exiting...' % plotFileFormat)
            exit()

        if (not self.hasTFdata_L) and (not self.hasTFdata_R):
            print('No transfer function data was found. Canceling save...')
            return

        outputFile = tools.setFileExtension(filePath, '.tfa', case='lower')
        if self.hasTFdata_L and self.hasTFdata_R:
            self.TFA_L.saveStatistics(outputFile, 'L', coheTreshold, remNegPhase, 'w')
            self.TFA_R.saveStatistics(outputFile, 'R', coheTreshold, remNegPhase, 'a')
        else:
            if self.hasTFdata_L:
                self.TFA_L.saveStatistics(outputFile, 'L', coheTreshold, remNegPhase, 'w')
            if self.hasTFdata_R:
                self.TFA_R.saveStatistics(outputFile, 'R', coheTreshold, remNegPhase, 'w')

        if self.hasTFdata_L:
            self.TFA_L.savePlot(fileNamePrefix=os.path.splitext(filePath)[0] + '_Left', fileType=plotFileFormat.lower(), coheTreshold=coheTreshold,
                                remNegPhase=remNegPhase, figDpi=250, fontSize=6)
        if self.hasTFdata_R:
            self.TFA_R.savePlot(fileNamePrefix=os.path.splitext(filePath)[0] + '_Right', fileType=plotFileFormat.lower(), coheTreshold=coheTreshold,
                                remNegPhase=remNegPhase, figDpi=250, fontSize=6)

        if register:
            xmlElement = ETree.Element('TFAsaveStat')
            tools.ETaddElement(parent=xmlElement, tag='fileName', text=os.path.basename(filePath))
            tools.ETaddElement(parent=xmlElement, tag='plotFileFormat', text=os.path.basename(plotFileFormat))
            tools.ETaddElement(parent=xmlElement, tag='remNegPhase', text=str(remNegPhase))
            tools.ETaddElement(parent=xmlElement, tag='coheTreshold', text=str(coheTreshold))
            self.ARoperationsNode.append(xmlElement)

    def computeARI(self, register=True):

        if self.hasTFdata_L:
            self.ARI_L = ARIanalysis(self.TFA_L.H, self.TFA_L.welch.Ts)
            self.hasARIdata_L = True

        if self.hasTFdata_R:
            self.ARI_R = ARIanalysis(self.TFA_R.H, self.TFA_R.welch.Ts)
            self.hasARIdata_R = True

        if register:
            xmlElement = ETree.Element('ARI')
            self.ARoperationsNode.append(xmlElement)

    def saveARI(self, filePath, format='csv', register=True):

        if (not self.hasARIdata_L) and (not self.hasARIdata_R):
            print('No ARI data was found. Canceling save...')
            return

        if format.lower() == 'simple_text':
            outputFile = tools.setFileExtension(filePath, '.ari', case='lower')
            if self.hasARIdata_L and self.hasARIdata_R:
                self.ARI_L.save(outputFile, 'L', writeMode='w')
                self.ARI_R.save(outputFile, 'R', writeMode='a')
            else:
                if self.hasARIdata_L:
                    self.ARI_L.save(outputFile, 'L', writeMode='w')
                if self.hasARIdata_R:
                    self.ARI_R.save(outputFile, 'R', writeMode='w')

        else:
            signals = []
            header = ''
            if self.hasARIdata_L:
                nPoints = self.ARI_L.nDuration
                signals += [self.ARI_L.timeVals, self.ARI_L.stepResponse, self.ARI_L.ARIbestFit]
                header += 'time (s);impulse_response_L;best_fit_curve_L;'
            if self.hasARIdata_R:
                nPoints = self.ARI_R.nDuration
                # add frequency vector only if there is no left PSD data
                if not self.hasARIdata_L:
                    signals += [self.ARI_R.timeVals, self.ARI_R.stepResponse, self.ARI_R.ARIbestFit]
                    header += 'time (s);impulse_response_R;best_fit_curve_R;'
                else:
                    signals += [self.ARI_R.stepResponse, self.ARI_R.ARIbestFit]
                    header += 'impulse_response_R;best_fit_curve_R;'

            if format.lower() == 'csv':
                outputFile = tools.setFileExtension(filePath, '.csv', case='lower')
                with open(outputFile, 'w') as fOut:
                    if self.hasARIdata_L:
                        fOut.write('ARI_INT_BEST_FIT_L;%d\n' % self.ARI_L.ARI_int)
                        fOut.write('ARI_FRAC_BEST_FIT_L;%f\n' % self.ARI_L.ARI_frac)
                    if self.hasARIdata_R:
                        fOut.write('ARI_INT_BEST_FIT_R;%d\n' % self.ARI_R.ARI_int)
                        fOut.write('ARI_FRAC_BEST_FIT_R;%f\n' % self.ARI_R.ARI_frac)
                    fOut.write('N_POINTS;%d\n' % nPoints)
                    fOut.write('-------DATA START-------;\n')
                    fOut.write(header + '\n')
                    signals = np.vstack(tuple(signals))
                    np.savetxt(fOut, signals.T, delimiter=';', fmt='%1.15e')
                    fOut.write('-------DATA END-------;\n')

            if format.lower() == 'numpy':
                outputFile = tools.setFileExtension(filePath, '.npy', case='lower')

                # build a structured array
                data = []
                if self.hasARIdata_L:
                    data.append(('L', self.ARI_L.ARI_int, self.ARI_L.ARI_frac, self.ARI_L.timeVals, self.ARI_L.stepResponse, self.ARI_L.ARIbestFit))
                if self.hasARIdata_R:
                    data.append(('R', self.ARI_R.ARI_int, self.ARI_L.ARI_frac, self.ARI_R.timeVals, self.ARI_R.stepResponse, self.ARI_R.ARIbestFit))

                dt = np.dtype([('side', 'U1'), ('ARI_int', np.int8), ('ARI_frac', np.float64), ('time_(s)', np.float64, (nPoints,)),
                               ('impulse_response', np.float64, (nPoints,)), ('ari_best_fit', np.float64, (nPoints,))])

                x = np.array(data, dtype=dt)
                np.save(outputFile, x)

        if register:
            xmlElement = ETree.Element('ARIsave')
            tools.ETaddElement(parent=xmlElement, tag='fileName', text=os.path.basename(filePath))
            tools.ETaddElement(parent=xmlElement, tag='format', text=format.lower())
            self.ARoperationsNode.append(xmlElement)

        print('Ok!')


if __name__ == '__main__':

    if sys.version_info.major == 2:
        sys.stdout.write('Sorry! This program requires Python 3.x\n')
        sys.exit(1)

    print(patientData.getVersion())

    if False:
        file = '../data/CG24HG.EXP'
    else:
        file = '../data/CG24HG_AR.job'

    x = patientData(file, activeModule='ARanalysis')

    [medias_G_L, _, _, _] = x.TFA_L.getGainStatistics(freqRange='LF', coheTreshold=True)
    print(x.listChannels('label'))
    print(x.findChannel('label', 'Analog_2'))

    x.saveSIG('../data/lixo.sig')

    # for i in range(x.nChannels):
    # x.signals[i].resample(51,method='quadratic')
    # x.signals[i].setLabel('signal_%d' % i)
    # x.signals[i].calibrate(i*10,i*20,method='percentile')
    # x.signals[i].info()
    # print(x.signals[i].data)
    # x.signals[i].cropFromRight(0)
    # x.signals[i].interpolate(2,2)
    # print(x.signals[i].data)

    # x.synchronizeSignals([1,2,0,3])

    # for i in range(x.nChannels):
    #    print(x.signals[i].data)

    # x.saveSignals('lixo.res')
    # x.findRRmarks(refChannel=0,method='md',findPeaks=True,findValleys=False)

    # print(x.peakIdx)
    # x.signals[4].cropInterval(6,12,register=True,RemoveSegment=True,segmentIndexes=peaks)
    # x.getBeat2beat(resampleRate_Hz=1.0,resampleMethod='linear')

    # for i in range(x.nChannels):
    #    print(x.signals[i].beat2beatData.max)
    #    print(x.signals[i].beat2beatData.min)
    #    print(x.signals[i].beat2beatData.avg)

    # x.saveOperations()
    # x.saveBeat2beat('lixo.b2b',[0,2])

    x.saveBeat2beat('../data/lixo.b2b')
    x.saveSignals('../data/lixo.sig')
