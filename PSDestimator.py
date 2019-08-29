#!/bin/python

# -*- coding: utf-8 -*-
import sys
import numpy as np
import tools
from scipy import signal as scipySignal
from scipy import fftpack as scipyFFTpack

def diferencaPedro(numpyData,file,label,isComplex=False):
    if isComplex:
        resultadoPedro=np.loadtxt(file).view(complex)
    else:
        resultadoPedro=np.loadtxt(file)
    print("maior erro em modulo %s : %f" % (label,np.amax(np.absolute(numpyData-resultadoPedro))))

#dataX, dataY:  numpy arrays, same lengths, same sampling frequency
#inputData:   float
#overlap:  float between 0.0 and 1.0
#segmentLength_s:  float
#windowType: string  values: 'hanning' (default), 'tukey', 'boxcar', 'rectangular', 'hamming'
class PSDestimator():
    def __init__(self,dataX,dataY,samplingFrequency_Hz, overlap,segmentLength_s,windowType='hanning',removeBias=True):
        self.dataX=dataX
        self.dataY=dataY
        self.Fs_Hz=samplingFrequency_Hz
        self.Ts=1.0/self.Fs_Hz
        self.overlap=overlap
        self.segmentLength=int(self.Fs_Hz*segmentLength_s)
        self.shiftSize=int((1.0-self.overlap)*self.segmentLength)
        self.nSegments=int((len(self.dataX)-self.segmentLength)/self.shiftSize)+1  # atention: in python 3.x, / is float division!
        self.windowType=windowType
        self.removeBias=removeBias
    
    def computeWelch(self):
        self.buildWindow(self.windowType)
        self.DFTx,self.freq=self.DFT(self.dataX)
        self.DFTy,_        =self.DFT(self.dataY)

        #diferencaPedro(self.DFTx,'../codigoPedro/lixo_fftABP.txt','DFTx',isComplex=True)
        #diferencaPedro(self.DFTy,'../codigoPedro/lixo_fftCBF_L.txt','DFTy',isComplex=True)
        #diferencaPedro(self.freq,'../codigoPedro/lixo_freq.txt','freq',isComplex=False)

        self.Sxx=self.getAutoSpectrum(self.DFTx,forceReal=True)
        self.Syy=self.getAutoSpectrum(self.DFTy,forceReal=True)
        self.Sxy=self.getCrossSpectrum(self.DFTx,self.DFTy)
        self.Syx=self.getCrossSpectrum(self.DFTy,self.DFTx)
        
        self.freqRangeExtractor = tools.CARfreqRange(self.freq)
        
        #diferencaPedro(self.Sxx,'../codigoPedro/lixo_PxxABP.txt','Sxx',isComplex=True)
        #diferencaPedro(self.Syy,'../codigoPedro/lixo_PxxCBF_L.txt','Syy',isComplex=True)
        #diferencaPedro(self.Sxy,'../codigoPedro/lixo_Pxy_L.txt','Sxy',isComplex=True)

    
    def filterAll(self,filterType='rect',nTaps=2,keepFirst=True):
        self.Sxx=self.LPfilter(self.Sxx, filterType,nTaps,keepFirst)
        self.Syy=self.LPfilter(self.Syy, filterType,nTaps,keepFirst)
        self.Sxy=self.LPfilter(self.Sxy, filterType,nTaps,keepFirst)
        self.Syx=self.LPfilter(self.Syx, filterType,nTaps,keepFirst)
            
        #diferencaPedro(self.Sxx,'../codigoPedro/lixo_filtered_PxxABP.txt','Sxx_filtered',isComplex=True)
        #diferencaPedro(self.Syy,'../codigoPedro/lixo_filtered_PxxCBF_L.txt','Syy_filtered',isComplex=True)
        #diferencaPedro(self.Sxy,'../codigoPedro/lixo_filtered_Pxy_L.txt','Sxy_filtered',isComplex=True)
    
    #creates a window for welch method. You probably don't have to call it directly. See DFTwelch below.
    def buildWindow(self,windowType='hanning'):
        self.windowType=windowType.lower()
        if self.windowType=='hanning':
            self.window=scipySignal.windows.hann(self.segmentLength)
        elif self.windowType=='tukey':
            self.window=scipySignal.windows.tukey(self.segmentLength, alpha=0.5)
        elif self.windowType in ['boxcar', 'rectangular']:
            self.window=scipySignal.windows.boxcar(self.segmentLength)
        elif self.windowType=='hamming':
            self.window=scipySignal.windows.hamming(self.segmentLength)

    def DFT(self,signal):
        """
        Performs spectral analysys via Welch's method
        
        Parameters
        numpy array:  signal
        Float Overlap
        Integer segmentLength_s
        String windowType
        
        Returns
        Array frequency_axis: List containing equidistant frequency points for interval
        Array dftvalues: Matrix with number_of_windows lists of length window_lenght containing dftvalues for each window
        Integer Number of windows
        """
        #if nwindows==None:
            #adjust wlenght allowing for requested overlap and nwindows with 
        #else:
            #wlenght = round(np.floor(freq*lenwind))
        
        DFTvalues = []

        for i in range(self.nSegments):
            startIdx=i*self.shiftSize
            endIdx=startIdx+self.segmentLength
            
            signalSegment = signal[startIdx:endIdx]
            if self.removeBias:
                signalSegment = scipySignal.detrend(signalSegment,type='constant')

            signalSegment = signalSegment*self.window
            
            DFTvalues.append(scipyFFTpack.fft(signalSegment))

        #frequency vector
        deltaF_Hz=self.Fs_Hz/self.segmentLength
        freqVals=np.arange(self.segmentLength)*deltaF_Hz
        
        return DFTvalues,freqVals

    def getAutoSpectrum(self,DFTx,forceReal=True):
        normWindowSq=np.linalg.norm(self.window)**2
        
        Sxx=np.zeros(self.segmentLength)
        for i in range(self.nSegments):
            if forceReal: # see notebook 3, page 36
                Sxx = Sxx + np.multiply(np.conjugate(DFTx[i]), DFTx[i]).real*self.Ts/normWindowSq
            else:
                Sxx = Sxx + np.multiply(np.conjugate(DFTx[i]), DFTx[i])*self.Ts/normWindowSq
            
        Sxx/=self.nSegments  # divides by nSegments to compute the average Sxx
        return Sxx

    def getCrossSpectrum(self,DFTx,DFTy):
        normWindowSq=np.linalg.norm(self.window)**2

        Sxy=np.zeros(self.segmentLength)
        for i in range(self.nSegments): # see notebook 3, page 36
            Sxy = Sxy + np.multiply(np.conjugate(DFTx[i]), DFTy[i])*self.Ts/normWindowSq

        Sxy/=self.nSegments  # divides by nSegments to compute the average Sxy
        return Sxy
        
    def LPfilter(self,signal, filterType='triangular',nTaps=3,keepFirst=False):
        if keepFirst:
            temp=signal[0]
            signal[0]=signal[1]
            
        if filterType in ['rect', 'boxcar']:
            window=scipySignal.windows.boxcar(nTaps)
            window/=np.sum(window)
        elif filterType == 'triangular':
            window=scipySignal.windows.triang(nTaps)
            window/=np.sum(window)

        signal = scipySignal.filtfilt(window, [1.0], signal)

        if keepFirst:
            signal[0]=temp
            
        return signal
    
    def save(self, fileName,freqRange='ALL'):
        print('Saving .PSD data')
        fileObj=open(fileName,'w')

        fileObj.write('NPOINTS=%d\n' % len(self.freq))

        np.set_printoptions(threshold=np.inf)


        fileObj.write('FREQ_HZ=%s\n'  % np.array_str(self.freqRangeExtractor.getFreq(freqRange),max_line_width=1000))
        fileObj.write('Sxx=%s\n'      % np.array_str(self.freqRangeExtractor.getSignal(self.Sxx,freqRange),max_line_width=1000))
        fileObj.write('Syy=%s\n'      % np.array_str(self.freqRangeExtractor.getSignal(self.Syy,freqRange),max_line_width=1000))
        fileObj.write('Sxy_REAL=%s\n' % np.array_str(np.real(self.freqRangeExtractor.getSignal(self.Sxy,freqRange)),max_line_width=1000))
        fileObj.write('Sxy_IMAG=%s\n' % np.array_str(np.imag(self.freqRangeExtractor.getSignal(self.Sxy,freqRange)),max_line_width=1000))
        fileObj.write('Syx_REAL=%s\n' % np.array_str(np.real(self.freqRangeExtractor.getSignal(self.Syx,freqRange)),max_line_width=1000))
        fileObj.write('Syx_IMAG=%s\n' % np.array_str(np.imag(self.freqRangeExtractor.getSignal(self.Syx,freqRange)),max_line_width=1000))
        fileObj.write('='*80 + '\n' )

        fileObj.close()
        print('Ok!')
