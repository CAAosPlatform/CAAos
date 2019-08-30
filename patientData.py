#!/bin/python

"""
.. warning:: Include here brief description of this module
"""
# -*- coding: utf-8 -*-
import sys
import os
import numpy as np
from scipy import signal as scipySignal
import tools
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
from signals import signal, beat2beat
from PSDestimator import PSDestimator
from TFA import transferFunctionAnalysis

__version__ = '0.1'

class patientData():
    """
    Patient data base class

    This is the base class to process cerebral autoregulation data.

    Parameters
    ----------
    inputFile : str
        File with patient's data. Accepted files: **.exp**, **.dat** (Raw Data file) or **.ppo** (preprocessing operation file)
        
    """

    @staticmethod
    def getVersion():
        """
        Returns the version of the module
        
        **Example**

        >>> from patientData import patientData as pD
        >>> x=pD('data.EXP')
        >>> print(x.getVersion())
        '0.1'
        """
        return __version__
    
    def __init__(self,inputFile):
        
        self.dirName,baseName=os.path.split(inputFile)
        self.filePrefix,fileExtension = os.path.splitext(baseName)
        self.hasRRmarks=False
        self.hasB2Bdata=False
        self.hasLdata=False
        self.hasRdata=False
        
        if fileExtension.lower() == '.ppo':
            self.operationsFile = inputFile
            self.loadOperations(self.operationsFile)
            self.fileName= os.path.join(self.dirName,self.operationsXML.get('file'))
            self.loadData()
            
            self.processOperations()
            
        if fileExtension.lower() in ['.exp','.dat']:
            self.fileName=inputFile
            self.operationsFile = os.path.join(self.dirName,self.filePrefix + '.ppo')

            #create operationsTree
            self.operationsXML = ET.Element("patient")
            self.operationsXML.set('file',baseName)
            self.operationsXML.set('version',self.getVersion())

            self.loadData()
            
        self.historySignals=[]
        self.historyOperations=[]
        
    def storeState(self):
        self.historySignals.append(copy.deepcopy(self.signals))
        self.historyOperations.append(copy.deepcopy(self.operationsXML))
    
    def undoState(self):
        del self.historyOperations[-1]
        del self.historySignals[-1]
        self.operationsXML=copy.deepcopy(self.historyOperations[-1])
        self.signals=copy.deepcopy(self.historySignals[-1])
        
    def loadHeader(self):
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
        * The number of channels is stored in the attribute :attr:`patientData.nChannels`.
        * The sampling rate is stored in the attribute :attr:`patientData.samplingRate_Hz`. The value of this attribute is sent to instances of :class:`~signals.signal` after calling :meth:`loadData` and this attribute is removed after that
        * Channel labels and units are stored in the attribute :attr:`patientData.signalLabels` and :attr:`patientData.signalUnits`. The values of these attributes are sent to instances of :class:`~signals.signal` after calling :meth:`loadData`  and these attributes are removed after that
        
        

        **Example**

        >>> from patientData import patientData as pD
        >>> x=pD('data.EXP')
        >>> x.loadHeader()
        >>> print(x.examDate)
        datetime.datetime(2016, 6, 30, 13, 7, 47)
        >>> print(x.samplingRate_Hz)
        datetime.datetime(2016, 6, 30, 13, 7, 47)
        100.0
        >>> print(x.nChannels)
        4
        >>> print(x.signalLabels)
        ['Time', 'Sample', 'MCA_L_To_Probe_Env', 'MCA_R_To_Probe_Env', 'Analog_1', 'Analog_8']
        >>> print(x.signalUnits)
        ['HH:mm:ss:ms', 'N', 'cm/s', 'cm/s', 'mV', 'mV']

        

        
        """
        file = open(self.fileName,'r')
        line=''
        self.sizeHeader=0
        
        #extract examination date
        while not line.startswith('Examination'):
          line=file.readline()
          self.sizeHeader+=1

        date = datetime.strptime(line[12:].split()[0], '%d:%m:%Y').date()
        time = datetime.strptime(line[12:].split()[1], '%H:%M:%S').time()
        self.examDate= datetime.combine(date,time)                       #: Examination Date.

        
        #extract sampling frequency in Hz
        while not line.startswith('Sampling Rate'):
          line=file.readline()
          self.sizeHeader+=1
          
        self.samplingRate_Hz=float(line.split()[2].replace('Hz',''))
        
        #next 2 lines should contain labels and units
        self.signalLabels=file.readline().rstrip().replace(' ','_').replace('.','').split('\t')
        self.signalUnits=file.readline().rstrip().split('\t')
        
        self.nChannels=len(self.signalUnits) - 2
        self.sizeHeader+=2
        
        file.close()
        self.operationsXML.set('sizeHeader',str(self.sizeHeader))
        self.operationsXML.set('examDate',str(self.examDate))
        self.operationsXML.set('nChannels',str(self.nChannels))
        
    def loadData(self):

        self.loadHeader()
        #create dtype of the file
        dtypes=("U11",'i4')   # col 0: time (11 char string)   col 1: frame (32 bit int)
        dtypes=dtypes + ('f8',)*self.nChannels  # the other columns will be treated as float (8bits)
        
        rawData=np.genfromtxt(self.fileName,delimiter=None,skip_header=self.sizeHeader,autostrip=True,names=','.join(self.signalLabels),dtype=dtypes)
      
        nPoints=len(rawData)
        
        self.signals=[]
        for i in range(self.nChannels):
            label=self.signalLabels[i+2]
            newSignal=signal(channel=i,label=label,unit=self.signalUnits[i+2],data=rawData[label],samplingRate_Hz=self.samplingRate_Hz,operationsXML=self.operationsXML)
            self.signals.append( newSignal )
      
        del self.signalLabels
        del self.signalUnits
        del self.samplingRate_Hz
        
    #channelList: list or None.  List with the channels to save. 
    def saveSignals(self, fileName,channelList=None):
        print('Saving .SIG data')
        fileObj=open(fileName,'w')
        
        if channelList is not None:
            for i in channelList:
                self.signals[i].saveData(fileObj)
        else:
            for i in range(self.nChannels):
                self.signals[i].saveData(fileObj)
        fileObj.close()
        print('Ok!')
        
    #channelList: list or None.  List with the channels to save. 
    def saveBeat2beat(self, fileName,channelList=None):
        print('Saving .B2B data')
        fileObj=open(fileName,'w')
        
        if channelList is not None:
            for i in channelList:
                self.signals[i].saveB2B(fileObj)
        else:
            for i in range(self.nChannels):
                self.signals[i].saveB2B(fileObj)
        fileObj.close()
        print('Ok!')
        
    def saveOperations(self,fileName=None):
        print('Saving .PPO data')

        rough_string = ET.tostring(self.operationsXML, 'utf-8')
        x = MD.parseString(rough_string).toprettyxml(indent="    ")

        if fileName is not None:
            fileOut=open(fileName,'w')
        else:
            fileOut=open(self.operationsFile,'w')
            
        fileOut.write(x)
        fileOut.close()
        print('Ok!')
    
    def loadOperations(self,fileName):
        tree=ET.parse(fileName)
        
        self.operationsXML = tree.getroot()
        #print('\nAll attributes:')
        #for elem in self.operationsXML:
            #for subelem in elem:
                ##print(subelem.attrib)
                #print(subelem.text)
        return

    def processOperations(self):
        for operation in self.operationsXML:
            if operation.tag not in ['resample','setlabel', 'syncronize', 'findRRmarks', 'beat2beat', 'setType', 'calibrate', 'LPfilter', 'interpolate', 'cropInterval', 'insertPeak', 'removePeak', 'B2B_LPfilter']:
                print('Operation \'%s\' not recognized. Exiting' % operation.tag)
                exit()

            if operation.tag == 'setType':
                typeSignal= tools.convAtrib(operation,'type',type='str')
                channel=    tools.convAtrib(operation,'channel',type='int')
                print('Setting Type channel=%d: %s' %(channel,typeSignal))
                if typeSignal=='None':
                    typeSignal=None
                self.signals[channel].setType(typeSignal,register=False)

            if operation.tag == 'setlabel':
                label=      tools.convAtrib(operation,'label',type='str')
                channel=    tools.convAtrib(operation,'channel',type='int')
                print('Setting Label channel=%d: %s' %(channel,label))
                self.signals[channel].setLabel(label,register=False)

            if operation.tag == 'resample':
                sampleRate= tools.convAtrib(operation,'sampleRate',type='float')
                method=     tools.convAtrib(operation,'method',type='str')
                channel=    tools.convAtrib(operation,'channel',type='int')
                print('Resampling channel=%d: Fs= %f, method=%s' %(channel,sampleRate,method))
                self.signals[channel].resample(sampleRate,method,register=False)

            if operation.tag == 'calibrate':
                valMin=     tools.convAtrib(operation,'valMin',type='float')
                valMax=     tools.convAtrib(operation,'valMax',type='float')
                method=     tools.convAtrib(operation,'method',type='str')
                segmentIdx= tools.convAtrib(operation,'segmentIndexes',type='list_int')
                channel=    tools.convAtrib(operation,'channel',type='int')
                print('Calibrating channel= %d: method= %s, valMin=%f, valMax=%f' %(channel,method,valMin,valMax))
                self.signals[channel].calibrate(valMax,valMin,method,segmentIdx,register=False)

            if operation.tag == 'syncronize':
                channelList= tools.convAtrib(operation,'channels',type='list_int')
                method=     tools.convAtrib(operation,'method',type='str')
                print('Syncronizing Channels %s: method=%s' %(str(channelList), method))
                self.synchronizeSignals(channelList,method,register=False)

            if operation.tag == 'LPfilter':
                Ntaps=      tools.convAtrib(operation,'Ntaps',type='int')
                method=     tools.convAtrib(operation,'method',type='str')
                channel=    tools.convAtrib(operation,'channel',type='int')
                print('Low Pass filter channel=%d: method=%s, Ntaps=%d' %(channel,method,Ntaps))
                self.signals[channel].LPfilter(method,Ntaps,register=False)

            if operation.tag == 'interpolate':
                frameStart=     tools.convAtrib(operation,'frameStart',type='int')
                frameEnd=       tools.convAtrib(operation,'frameEnd',type='int')
                method=     tools.convAtrib(operation,'method',type='str')
                channel=    tools.convAtrib(operation,'channel',type='int')
                print('Interpolating channel=%d: start=%d, end=%d, method=%s' %(channel,frameStart,frameEnd,method))
                self.signals[channel].interpolate(frameStart,frameEnd,method,register=False)
                
                
            if operation.tag == 'cropInterval':
                frameStart=     tools.convAtrib(operation,'frameStart',type='int')
                frameEnd=       tools.convAtrib(operation,'frameEnd',type='int')
                RemoveSegment=  tools.convAtrib(operation,'RemoveSegment',type='bool')
                segmentIndexes= tools.convAtrib(operation,'segmentIndexes',type='list_int')
                channel=        tools.convAtrib(operation,'channel',type='int')
                print('Cropping channel %s: start=%d, end=%d, removeSegment=%s' %(channel, frameStart,frameEnd,str(RemoveSegment)))
                self.signals[channel].cropInterval(frameStart,frameEnd,False,RemoveSegment,segmentIndexes)

            if operation.tag == 'findRRmarks':
                refChannel=  tools.convAtrib(operation,'refChannel',type='int')
                method=      tools.convAtrib(operation,'method',type='str')
                findPeaks=   tools.convAtrib(operation,'findPeaks',type='bool')
                findValleys= tools.convAtrib(operation,'findValleys',type='bool')
                print('Finding RRmarks: refChannel=%d method=%s findPeaks=%s findValleys=%s' %(refChannel,method,findPeaks,findValleys))
                self.findRRmarks(refChannel,method,findPeaks,findValleys,register=False)

            if operation.tag == 'insertPeak':
                newIdx=   tools.convAtrib(operation,'newIdx',type='int')
                isPeak=   tools.convAtrib(operation,'isPeak',type='bool')
                print('Inserting Peak: newIdx=%d, isPeak=%s' %(newIdx, str(isPeak)))
                self.insertPeak(newIdx,isPeak,register=False)

            if operation.tag == 'removePeak':
                Idx=      tools.convAtrib(operation,'Idx',type='int')
                isPeak=   tools.convAtrib(operation,'isPeak',type='bool')
                print('Removing Peak: Idx=%d, isPeak=%s' %(Idx, str(isPeak)))
                self.removePeak(Idx,isPeak,register=False)

            if operation.tag == 'beat2beat':
                resampleMethod=   tools.convAtrib(operation,'resampleMethod',type='str')
                resampleRate_Hz=  tools.convAtrib(operation,'resampleRate_Hz',type='float')
                print('Extracting beat-to-beat data: resampleMethod=%s, Freq=%f' %(resampleMethod, resampleRate_Hz))
                self.getBeat2beat(resampleRate_Hz,resampleMethod,register=False)

            if operation.tag == 'B2B_LPfilter':
                method=     tools.convAtrib(operation,'method',type='str')
                Ntaps=      tools.convAtrib(operation,'Ntaps',type='int')
                print('B2B LP filter: method=%s, Ntaps=%d' %(method,Ntaps))
                self.LPfilterBeat2beat(method,Ntaps,register=False)
                
    def registerOperation(self,xmlElement):
        self.operationsXML.append(xmlElement)
        
    def findChannelByLabel(self,label):
        return  self.listLabels().index(label)
    
    def listLabels(self):
        return [x.label for x in self.signals]
        
    def findDelay(self,refChannel,channel):
        # from:  https://stackoverflow.com/questions/4688715/find-time-shift-between-two-similar-waveforms
        delaySamples =  ( np.argmax(scipySignal.correlate(self.signals[refChannel].data,self.signals[channel].data))-(len(self.signals[refChannel].data)-1) )
        return delaySamples
    
    def findRRmarks(self,refChannel,method='ampd',findPeaks=True,findValleys=False,register=True):
        [self.peakIdx,_,self.valleyIdx,_] = self.signals[refChannel].findPeaks(method,findPeaks,findValleys,register=False)
        self.hasRRmarks=True
        
        #register operation
        if register:
            xmlElement = ET.Element("findRRmarks")
            tools.TEsimple(parent=xmlElement,tag='refChannel',text=str(refChannel))
            tools.TEsimple(parent=xmlElement,tag='method',text=method)
            tools.TEsimple(parent=xmlElement,tag='findPeaks',text=str(findPeaks))
            tools.TEsimple(parent=xmlElement,tag='findValleys',text=str(findValleys))
            self.registerOperation(xmlElement)
    
    def insertPeak(self,newIdx,isPeak=True,register=True):
        if not self.hasRRmarks:
            return
        
        if isPeak:
            pos = np.searchsorted(self.peakIdx,newIdx)
            self.peakIdx = np.insert(self.peakIdx, pos, newIdx)
            self.peakIdx = np.unique(self.peakIdx) # removes eventual repeated indexes
        else:
            pos = np.searchsorted(self.valleyIdx,newIdx)
            self.valleyIdx = np.insert(self.valleyIdx, pos, newIdx)
            self.valleyIdx = np.unique(self.valleyIdx) # removes eventual repeated indexes
        
        #register operation
        if register:
            xmlElement = ET.Element("insertPeak")
            tools.TEsimple(parent=xmlElement,tag='newIdx',text=str(newIdx))
            tools.TEsimple(parent=xmlElement,tag='isPeak',text=str(isPeak))
            self.registerOperation(xmlElement)

    def removePeak(self,Idx,isPeak=True,register=True):
        if not self.hasRRmarks:
            return
        
        if isPeak:
            pos = np.searchsorted(self.peakIdx,Idx)
            
            if pos==0 or (pos==len(self.peakIdx)-1):
                self.peakIdx = np.delete(self.peakIdx, pos)
                return
            else:
                if abs(Idx-self.peakIdx[pos-1]) < abs(Idx-self.peakIdx[pos]):
                    self.peakIdx = np.delete(self.peakIdx, pos-1)
                else:
                    self.peakIdx = np.delete(self.peakIdx, pos)
        else:
            pos = np.searchsorted(self.peakIdx,Idx)
            
            if pos==0 or (pos==len(self.valleyIdx)-1):
                self.valleyIdx = np.delete(self.valleyIdx, pos)
                return
            else:
                if abs(Idx-self.valleyIdx[pos-1]) < abs(Idx-self.valleyIdx[pos]):
                    self.valleyIdx = np.delete(self.valleyIdx, pos-1)
                else:
                    self.valleyIdx = np.delete(self.valleyIdx, pos)
        
        #register operation
        if register:
            xmlElement = ET.Element("removePeak")
            tools.TEsimple(parent=xmlElement,tag='Idx',text=str(Idx))
            tools.TEsimple(parent=xmlElement,tag='isPeak',text=str(isPeak))
            self.registerOperation(xmlElement)
    
    def removeRRmarks(self):
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
        
        self.hasRRmarks=False
            
    def synchronizeSignals(self,channelList,method='correlation',register=True):
        if len(channelList)==0:
            return
        
        self.removeRRmarks()
        
        if method == 'correlation':
            # delays with respect to channel 0
            delays=[]
            for ch in channelList:
                delays.append( self.findDelay(channelList[0],ch) )

            delays= [-(x-max(delays)) for x in delays]
            length=[]
            for ch in range(len(channelList)):
                channel=channelList[ch]
                delay=delays[ch]
                #print('ch: %d   delay:%d' %(channel,delay))
                self.signals[channel].cropFromLeft(delay,register=False)
                length.append(self.signals[channel].nPoints)
            
            minLength=min(length)
            for ch in range(self.nChannels):
                self.signals[ch].cropFromRight(self.signals[ch].nPoints-minLength,register=False)
            
        #register operation
        if register:
            xmlElement = ET.Element("syncronize")
            tools.TEsimple(parent=xmlElement,tag='channels',text=str(channelList).replace(',',''))
            tools.TEsimple(parent=xmlElement,tag='method',text=method)   
            self.registerOperation(xmlElement)
        
    def getBeat2beat(self,resampleRate_Hz=100.0,resampleMethod='linear',register=True):

        self.hasB2Bdata=True
        for ch in range(self.nChannels):
            self.signals[ch].beat2beat(self.peakIdx,resampleRate_Hz,resampleMethod)
            #print(self.signals[ch].beat2beatData.max)
            
        #register operation
        if register:
            xmlElement = ET.Element("beat2beat")
            tools.TEsimple(parent=xmlElement,tag='resampleMethod',text=resampleMethod)
            tools.TEsimple(parent=xmlElement,tag='resampleRate_Hz',text=str(resampleRate_Hz))
            self.registerOperation(xmlElement)
    
    def removeBeat2beat(self):
        if not self.hasB2Bdata:
            return
        
        for ch in range(self.nChannels):
            try:
                del self.signals[ch].beat2beatData
            except AttributeError:
                pass
        self.hasB2Bdata=False
        
    def LPfilterBeat2beat(self,method='movvalueingAverage',nTaps=5,register=True):
        if not self.hasB2Bdata:
            print('Error: B2Bdata not found...')
            return
        
        for s in self.signals:
            s.beat2beatData.LPfilter(method,nTaps)
            
        #register operation
        if register:
            xmlElement = ET.Element("B2B_LPfilter")
            tools.TEsimple(parent=xmlElement,tag='method',text=str(method))
            tools.TEsimple(parent=xmlElement,tag='Ntaps',text=str(nTaps))
            self.registerOperation(xmlElement)
    
    def computePSDwelch(self,useB2B=True,overlap=0.5,segmentLength_s=100,windowType='hanning',removeBias=True,filterSpectrum=False,filterType='triangular',nTapsFilter=3):
        #find ABP and CBFV channels
        ABP_channel=None
        CBFv_R_channel=None
        CBFv_L_channel=None
        for s in self.signals:
            if s.sigType=='ABP':
                ABP_channel=s.channel
            if s.sigType=='CBFV_R':
                CBFv_R_channel=s.channel
            if s.sigType=='CBFV_L':
                CBFv_L_channel=s.channel
        
        #left side
        if (ABP_channel is not None) and (CBFv_L_channel is not None):
            if useB2B:
                inputSignal=self.signals[ABP_channel].beat2beatData.avg
                outputSignal=self.signals[CBFv_L_channel].beat2beatData.avg
                Fs=self.signals[ABP_channel].beat2beatData.samplingRate_Hz
            else:
                inputSignal=self.signals[ABP_channel].data
                outputSignal=self.signals[CBFv_L_channel].data
                Fs=self.signals[ABP_channel].samplingRate_Hz

            
            self.PSD_L=PSDestimator(inputSignal,outputSignal,Fs, overlap,segmentLength_s,windowType,removeBias)
            self.PSD_L.computeWelch()
            self.hasLdata=True
            
            if filterSpectrum:
                self.PSD_L.filterAll(filterType,nTapsFilter,keepFirst=True)
        else:
            self.hasLdata=False
            
        #right channel
        if (ABP_channel is not None) and (CBFv_R_channel is not None):
            if useB2B:
                inputSignal=self.signals[ABP_channel].beat2beatData.avg
                outputSignal=self.signals[CBFv_R_channel].beat2beatData.avg
                Fs=self.signals[ABP_channel].beat2beatData.samplingRate_Hz
            else:
                inputSignal=self.signals[ABP_channel].data
                outputSignal=self.signals[CBFv_R_channel].data
                Fs=self.signals[ABP_channel].samplingRate_Hz

            self.PSD_R=PSDestimator(inputSignal,outputSignal,Fs, overlap,segmentLength_s,windowType,removeBias)
            self.PSD_R.computeWelch()
            self.hasRdata=True
            
            if filterSpectrum:
                self.PSD_R.filterAll(filterType,nTapsFilter,keepFirst=True)
        else:
            self.hasRdata=False
    
    # estimatorType:  'H1'   or 'H2'
    def computeTFA(self,estimatorType='H1'):
        
        if self.hasLdata:
            self.TFA_L=transferFunctionAnalysis(welchData=self.PSD_L)
            if  estimatorType.upper() == 'H1':
                self.TFA_L.computeH1()
            if  estimatorType.upper() == 'H2':
                self.TFA_L.computeH2()
                
        if self.hasRdata:
            self.TFA_R=transferFunctionAnalysis(welchData=self.PSD_R)
            if  estimatorType.upper() == 'H1':
                self.TFA_R.computeH1()
            if  estimatorType.upper() == 'H2':
                self.TFA_R.computeH2()

        
        #self.TFA_R.savePlot(fileNamePrefix=None)

if __name__ == '__main__':
    
    if sys.version_info.major == 2:
        sys.stdout.write("Sorry! This program requires Python 3.x\n")
        sys.exit(1)
    
    print(patientData.getVersion())
    
    if False:
        file='../data/CG21HG.dat'
    else:
        file='../data/CG21HG.ppo'
    if True:
        x=patientData(file)
    else:
        x=patientData('./simplesPeak.dat')

    print(x.examDate)

    print(x.listLabels())
    
    x.computePSDwelch(useB2B=True,overlap=0.5,segmentLength_s=100,windowType='hanning',removeBias=True,filterSpectrum=True,filterType='triangular',nTapsFilter=2)

    for i in range(x.nChannels):
        #x.signals[i].resample(51,method='quadratic')
        #x.signals[i].setLabel('signal_%d' % i)
        #x.signals[i].calibrate(i*10,i*20,method='percentile')
        x.signals[i].info()
        #print(x.signals[i].data)
        #x.signals[i].cropFromRight(0)
        #x.signals[i].interpolate(2,2)
        #print(x.signals[i].data)
        
    #x.synchronizeSignals([1,2,0,3])
    
    #for i in range(x.nChannels):
    #    print(x.signals[i].data)
        
    #x.saveSignals('lixo.res')
    #x.findRRmarks(refChannel=0,method='md',findPeaks=True,findValleys=False)
    
    #print(x.peakIdx)
    #x.signals[4].cropInterval(6,12,register=True,RemoveSegment=True,segmentIndexes=peaks)
    #x.getBeat2beat(resampleRate_Hz=1.0,resampleMethod='linear')    
    
    #for i in range(x.nChannels):
    #    print(x.signals[i].beat2beatData.max)
    #    print(x.signals[i].beat2beatData.min)
    #    print(x.signals[i].beat2beatData.avg)
        
    #x.saveOperations()
    #x.saveBeat2beat('lixo.b2b',[0,2])
    
    x.saveBeat2beat('../data/lixo.b2b')
    x.saveSignals('../data/lixo.sig')
    
    
