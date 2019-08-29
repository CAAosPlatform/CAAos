#!/bin/python

# -*- coding: utf-8 -*-
import numpy as np
from scipy import signal as scipySignal
from scipy import interpolate as scipyInterpolate
import tools
import ampdLib
import xml.etree.ElementTree as ET


class signal():
    def __init__(self,channel,label,unit,data,samplingRate_Hz,operationsXML):
        self.channel=channel
        self.label=label
        self.unit=unit
        self.sigType=None # 'ABP','CBFV_L', 'CBFV_R', 'ETCO2', None
        self.data=data
        self.samplingRate_Hz=float(samplingRate_Hz)
        self.nPoints=self.data.shape[0]
        self.operationsXML=operationsXML

    def info(self):
        print('-------------------------------')
        print('Channel: %d' % self.channel)
        print('label: ' + self.label)
        print('unit: '  + self.unit)
        print('sigType: ' + str(self.sigType))
        print('nPoints: %d' % self.nPoints)
        print('-------------------------------')

    def saveData(self,fileObj):
        fileObj.write('CHANNEL=%d\n' % self.channel)
        fileObj.write('LABEL=%s\n' % self.label)
        fileObj.write('UNIT=%s\n' % self.unit)
        fileObj.write('SIGNAL_TYPE=%s\n' % str(self.sigType))
        fileObj.write('SAMPLING_RATE_HZ=%g\n' % self.samplingRate_Hz)
        fileObj.write('NPOINTS=%d\n' % self.nPoints)

        np.set_printoptions(threshold=np.inf)

        fileObj.write('DATA=%s\n' % np.array_str(self.data,max_line_width=1000))
        fileObj.write('='*80 + '\n' )

        np.set_printoptions(threshold=1000) # default

    def saveB2B(self,fileObj):
        fileObj.write('CHANNEL=%d\n' % self.channel)
        fileObj.write('LABEL=%s\n' % self.label)
        fileObj.write('UNIT=%s\n' % self.unit)
        fileObj.write('SIGNAL_TYPE=%s\n' % str(self.sigType))
        fileObj.write('SAMPLING_RATE_HZ=%g\n' % self.beat2beatData.samplingRate_Hz)
        fileObj.write('NPOINTS=%d\n' % self.beat2beatData.nPoints)

        np.set_printoptions(threshold=np.inf)

        fileObj.write('TIME=%s\n' % np.array_str(self.beat2beatData.xData,max_line_width=500))
        fileObj.write('MAX=%s\n' % np.array_str(self.beat2beatData.max,max_line_width=500))
        fileObj.write('MIN=%s\n' % np.array_str(self.beat2beatData.min,max_line_width=500))
        fileObj.write('AVG=%s\n' % np.array_str(self.beat2beatData.avg,max_line_width=500))

        fileObj.write('='*80 + '\n' )
        
        np.set_printoptions(threshold=1000) # default
        
    def registerOperation(self,xmlElement):
        tools.TEsimple(parent=xmlElement,tag='channel',text=str(self.channel))
        self.operationsXML.append(xmlElement)
        
    def setLabel(self,newLabel,register=True):
        self.label=newLabel
        
        #register operation
        if register:
            xmlElement = ET.Element("setlabel")
            tools.TEsimple(parent=xmlElement,tag='label',text=newLabel)
            self.registerOperation(xmlElement)
        
    def setType(self,newType,register=True):
        self.sigType=newType
        
        #register operation
        if register:
            xmlElement = ET.Element("setType")
            tools.TEsimple(parent=xmlElement,tag='type',text=newType)
            self.registerOperation(xmlElement)

    def findPeaksBySegments(self,segmentLengh_s=20.0):
        segmentLength=segmentLengh_s*self.samplingRate_Hz   # equivalent to 20seconds of data
        nSegments=int(self.nPoints / segmentLength)
        fmax_bpm=200
        DeltaTMin=int( 60.0/float(fmax_bpm)*self.samplingRate_Hz )   # number of samples that represents a frequency of 220bpm
        
        dataSegments = np.array_split(self.data, nSegments)
        
        peakIdx = np.array([], dtype=int)
        valleyIdx = np.array([], dtype=int)
        
        idxStart=0
        for s in range(len(dataSegments)):
            data=dataSegments[s]
            sMax=np.percentile(data,90.0)
            smph=np.percentile(data,60.0)
            sMin=np.percentile(data,10.0)
            prominence=(sMax-sMin)*0.1

            peakIdxSegment=tools.detect_peaks(data, mph=smph, mpd=DeltaTMin, threshold=0, edge='rising',kpsh=False, MinPeakProminence=prominence,MinPeakProminenceSide='left',valley=False)

            valleyIdxSegment=[]
            for i in peakIdxSegment:
                cumulativeProminence=0
                idx=i
                dx=data[idx]-data[idx-1]
                while idx>=0 and (dx>0 or  cumulativeProminence<(sMax-sMin)*0.5):
                    cumulativeProminence+=dx
                    idx-=1
                    dx=data[idx]-data[idx-1]
                    
                if idx>=0:
                    valleyIdxSegment.append(idx)
                
            valleyIdxSegment=np.array(valleyIdxSegment)
            #print(valleyIdxSegment)
            peakIdx = np.append(peakIdx, peakIdxSegment+idxStart, axis=None)
            valleyIdx = np.append(valleyIdx, valleyIdxSegment+idxStart, axis=None)
            idxStart+=data.shape[0]
        
        #print(peakIdx)
        peakVal=self.data[peakIdx]
        valleyVal=self.data[valleyIdx]
      
        return [peakIdx,peakVal,valleyIdx,valleyVal]
 
    def findPeaks(self,method='ampd',findPeaks=True,findValleys=False,register=False):
        
        peakIdx=None
        peakVal=None
        valleyIdx=None
        valleyVal=None
                
        if method == 'ampd':
            if findPeaks:
                peakIdx=ampdLib.ampdFast(self.data, 10,LSMlimit = 0.2)
                
                fmax_bpm=250
                DeltaTMin=int( 60.0/float(fmax_bpm)*self.samplingRate_Hz )   # number of samples that represents a frequency of 250bpm
                temp=[]
                for i in range(len(peakIdx)-1):
                    if peakIdx[i+1]-peakIdx[i]>DeltaTMin:   # 5 samples appart
                        temp.append(peakIdx[i])
                    else:
                        temp.append(max(peakIdx[i],peakIdx[i+1]))
                peakIdx=temp
            
            
            if findValleys:
                valleyIdx=ampdLib.ampdFast(-self.data, 10,LSMlimit = 0.1)

        if method == 'md':
            fmax_bpm=250
            sMax=np.percentile(self.data,90.0)
            smph=np.percentile(self.data,60.0)
            sMin=np.percentile(self.data,10.0)
            prominence=(sMax-sMin)*0.2

            DeltaTMin=int( 60.0/float(fmax_bpm)*self.samplingRate_Hz )   # number of samples that represents a frequency of 250bpm

            peakIdx=tools.detect_peaks(self.data, mph=smph, mpd=DeltaTMin, threshold=0, edge='rising',kpsh=False, MinPeakProminence=prominence,MinPeakProminenceSide='left',valley=False)
            
            if findValleys:
                valleyIdx=[]
                for i in peakIdx:
                    cumulativeProminence=0
                    idx=i
                    dx=self.data[idx]-self.data[idx-1]
                    while idx>=0 and (dx>0 or  cumulativeProminence<(sMax-sMin)*0.5):
                        cumulativeProminence+=dx
                        idx-=1
                        dx=self.data[idx]-self.data[idx-1]
                        
                    valleyIdx.append(idx)
                    
                valleyIdx=np.array(valleyIdx)
                
            if not findPeaks:
                peakIdx=None

        if findPeaks:
            peakIdx= np.unique(peakIdx) # removes eventual repeated indexes
        if findValleys:
            valleyIdx= np.unique(valleyIdx) # removes eventual repeated indexes
                
        if findPeaks:
            peakVal=self.data[peakIdx]
            
        if findValleys:
            valleyVal=self.data[valleyIdx]
                
        #register operation
        if register:
            xmlElement = ET.Element("findPeaksSignal")
            tools.TEsimple(parent=xmlElement,tag='findPeaks',text=str(findPeaks))
            tools.TEsimple(parent=xmlElement,tag='findValleys',text=str(findValleys))
            tools.TEsimple(parent=xmlElement,tag='method',text=method)
            self.registerOperation(xmlElement)
                
      
        return [peakIdx,peakVal,valleyIdx,valleyVal]
    
    # if segmentIndexes=None (default) considers all data, otherwise it is expected a list with start and end indexes
    def yLimits(self,method='percentile',detrend=False,segmentIndexes=None):
        min=0
        max=0
        
        if segmentIndexes is not None:
            data=self.data[segmentIndexes[0]:segmentIndexes[1]]
        else:
            data=self.data

        if detrend:
            data=scipySignal.detrend(data,type='linear')

        if method == 'absolute':
            max=np.amax(data)
            min=np.amin(data)
            
        if method == 'percentile':
            min=np.percentile(data,5.0)
            max=np.percentile(data,95.0)
        return [min,max]
        
        
    # if segmentIndexes=None (default) considers all data, otherwise it is expected a list with start and end indexes
    def calibrate(self,valMax,valMin,method='percentile',segmentIndexes=None,register=True):
        
        if valMax<=valMin:
            return
        #print(segmentIndexes)
        [x1,x2]=self.yLimits(method=method,detrend=False,segmentIndexes=segmentIndexes)

        y2=valMax
        y1=valMin
        
        #linear interpolation        
        ang_coef=(y2-y1)/float(x2-x1)

        self.data = ang_coef * (self.data-x1) + y1
        
        #register operation
        if register:
            xmlElement = ET.Element("calibrate")
            tools.TEsimple(parent=xmlElement,tag='valMin',text=str(valMin))
            tools.TEsimple(parent=xmlElement,tag='valMax',text=str(valMax))
            tools.TEsimple(parent=xmlElement,tag='method',text=str(method))
            tools.TEsimple(parent=xmlElement,tag='segmentIndexes',text=str(segmentIndexes).replace(',',''))
            self.registerOperation(xmlElement)
    
    #remove elemetns betwen start/end, including these limits.
    def cropInterval(self,start,end,register=True,RemoveSegment=False,segmentIndexes=None):
        #register operation
        if register:
            xmlElement = ET.Element("cropInterval")
            tools.TEsimple(parent=xmlElement,tag='frameStart',text=str(start))
            tools.TEsimple(parent=xmlElement,tag='frameEnd',text=str(end))
            tools.TEsimple(parent=xmlElement,tag='RemoveSegment',text=str(RemoveSegment))
            tools.TEsimple(parent=xmlElement,tag='segmentIndexes',text=str(segmentIndexes))
            self.registerOperation(xmlElement)

        if RemoveSegment:
            if len(segmentIndexes) >0:
                end=segmentIndexes[np.searchsorted(segmentIndexes,end)]
                start=segmentIndexes[np.searchsorted(segmentIndexes,start)-1]
                
        if (end+1)>len(self.data) or start<0 or (end+1)<start:
            print('Invalid interval')
            return
        
        self.data = np.delete(self.data, range(start,end+1))
        self.nPoints=self.data.shape[0]

    # remove the specified number of elements from right. Ex: if nelem=1, removes only one element from right
    def cropFromRight(self,nElem,register=True):
        if nElem > self.nPoints:
            print('data does not have so many elements')
            return
        if nElem < 0:
            print('negative number of elements')
            return
        self.cropInterval(self.nPoints-nElem,self.nPoints-1,register)
    
    # remove the specified number of elements from right. Ex: if nelem=1, removes only one element from left
    def cropFromLeft(self,nElem,register=True):
        if nElem > self.nPoints:
            print('data does not have so many elements')
            return
        if nElem < 0:
            print('negative number of elements')
            return
        self.cropInterval(0,nElem-1,register)
    
    # valid methods:            'linear', 'nearest',
    # spline methods:           'zero', 'slinear', 'quadratic', 'cubic',
    # previoues or next values: 'previous', 'next'
    def resample(self,newSampleRate,method='linear',register=True):
        xData=np.arange(self.nPoints)/self.samplingRate_Hz
        f=scipyInterpolate.interp1d(xData, self.data, kind=method, fill_value=(self.data[0],self.data[-1]), assume_sorted=True)
        
        xNew = np.arange(xData[0],xData[-1],1.0/newSampleRate)
        self.data = f(xNew)
        
        self.samplingRate_Hz = float(newSampleRate)
        self.nPoints=self.data.shape[0]

        #register operation
        if register:
            xmlElement = ET.Element("resample")
            tools.TEsimple(parent=xmlElement,tag='sampleRate',attrib={'unit':'Hz'},text=str(newSampleRate))
            tools.TEsimple(parent=xmlElement,tag='method',text=str(method))
            self.registerOperation(xmlElement)
    
    # interpolate data in the interval [start,end], including the limits
    def interpolate(self,start,end,method='linear',register=True):
        if (end+1)>len(self.data) or start<0 or (end+1)<start:
            print('Invalid interval')
            return
        
        nIntervals=end-start
        
        if nIntervals <1:
            return
        
        if method =='linear':
            deltaY=(self.data[end]-self.data[start])/nIntervals
        
            for i in range(nIntervals):
                self.data[start+i] =self.data[start]+deltaY*i
        
        #register operation
        if register:
            xmlElement = ET.Element("interpolate")
            tools.TEsimple(parent=xmlElement,tag='frameStart',text=str(start))
            tools.TEsimple(parent=xmlElement,tag='frameEnd',text=str(end))
            tools.TEsimple(parent=xmlElement,tag='method',text=str(method))
            self.registerOperation(xmlElement)
            
    def LPfilter(self,method='movingAverage',nTaps=5,register=True):
        if method == 'movingAverage':
            self.data = scipySignal.filtfilt([1.0/nTaps,]*nTaps, [1.0], self.data)
    
        #register operation
        if register:
            xmlElement = ET.Element("LPfilter")
            tools.TEsimple(parent=xmlElement,tag='method',text=str(method))
            tools.TEsimple(parent=xmlElement,tag='Ntaps',text=str(nTaps))
            self.registerOperation(xmlElement)

    # resampling methods
    # valid methods:            'linear', 'nearest',
    # spline methods:           'zero', 'slinear', 'quadratic', 'cubic',
    # previoues or next values: 'previous', 'next'
    def beat2beat(self,beat_idx,resampleRate_Hz=100.0,resampleMethod='linear'):
        self.beat2beatData=beat2beat(self.data,beat_idx,self.samplingRate_Hz,resampleRate_Hz,resampleMethod)

class beat2beat():
    
    #data_samplingRate_Hz: sampling rate associated to data and beat_idx indices
    #resampleRate_Hz: sampling rate after resampling the beat to beat signal
    # resampling method
    # valid methods:            'linear', 'nearest',
    # spline methods:           'zero', 'slinear', 'quadratic', 'cubic',
    # previoues or next values: 'previous', 'next'
    def __init__(self,data,beat_idx,data_samplingRate_Hz,resampleRate_Hz=100.0,resampleMethod='linear'):
        self.max=[]
        self.min=[]
        self.avg=[]
        self.xData=beat_idx[0:-1]/data_samplingRate_Hz
        self.nPoints=self.xData.shape[0]
        
        for i in range(len(beat_idx)-1):
            self.max.append(max(data[beat_idx[i]:beat_idx[i+1]]))
            self.min.append(min(data[beat_idx[i]:beat_idx[i+1]]))
            self.avg.append(np.mean(data[beat_idx[i]:beat_idx[i+1]]))
        self.max=np.array(self.max)
        self.min=np.array(self.min)
        self.avg=np.array(self.avg)

        self.resample(resampleRate_Hz,resampleMethod)
        
    def LPfilter(self,method='movingAverage',nTaps=5):
        if method == 'movingAverage':
            self.max = scipySignal.filtfilt([1.0/nTaps,]*nTaps, [1.0], self.max)
            self.min = scipySignal.filtfilt([1.0/nTaps,]*nTaps, [1.0], self.min)
            self.avg = scipySignal.filtfilt([1.0/nTaps,]*nTaps, [1.0], self.avg)

    def resample(self,resampleRate_Hz,method='linear'):
        xNew = np.arange(self.xData[0],self.xData[-1],1.0/resampleRate_Hz)
        
        #max
        f=scipyInterpolate.interp1d(self.xData,self.max, kind=method, fill_value=(self.max[0],self.max[-1]), assume_sorted=True)
        self.max = f(xNew)
        #min
        f=scipyInterpolate.interp1d(self.xData,self.min, kind=method, fill_value=(self.min[0],self.min[-1]), assume_sorted=True)
        self.min = f(xNew)
        #avg
        f=scipyInterpolate.interp1d(self.xData,self.avg, kind=method, fill_value=(self.avg[0],self.avg[-1]), assume_sorted=True)
        self.avg = f(xNew)
        
        self.xData=xNew
        self.nPoints=self.xData.shape[0]
        
        self.samplingRate_Hz = float(resampleRate_Hz)
        
        
if __name__ == '__main__':
    
    x=signal(channel=0,label='aa',unit='cm/s',data=np.array([0,0,0]),samplingRate_Hz=100,operationsXML=ET.Element("temp"))
    x.info()
