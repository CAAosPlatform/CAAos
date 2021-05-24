#!/bin/python

# -*- coding: utf-8 -*-
import numpy as np
from scipy import fftpack as scipyFFTpack
from scipy import signal as scipySignal

import tools


def diferencaPedro(numpyData, file, label, isComplex=False):
    if isComplex:
        resultadoPedro = np.loadtxt(file).view(complex)
    else:
        resultadoPedro = np.loadtxt(file)
    print('maior erro em modulo %s : %f' % (label, np.amax(np.absolute(numpyData - resultadoPedro))))


# dataX, dataY:  numpy arrays, same lengths, same sampling frequency
# inputData:   float
# overlap:  float between 0.0 and 1.0
# segmentLength_s:  float
# windowType: string  values: 'hann' (default), 'tukey', 'boxcar', 'rectangular', 'hamming'
class PSDestimator():
    def __init__(self, dataX, dataY, samplingFrequency_Hz, overlap, segmentLength_s, windowType='hanning', detrend=False,unitX=None,unitY=None):

        # removing bias, based on Panerai's algorithm
        if detrend:
            detrendType='linear'
        else:
            detrendType = 'constant'
        self.dataX = scipySignal.detrend(dataX, type=detrendType)
        self.dataY = scipySignal.detrend(dataY, type=detrendType)

        self.unitX = unitX
        self.unitY = unitY

        self.Fs_Hz = samplingFrequency_Hz
        self.Ts = 1.0 / self.Fs_Hz
        self.overlap = overlap
        self.segmentLength = round(self.Fs_Hz * segmentLength_s)
        self.shiftSize = round((1.0 - self.overlap) * self.segmentLength)
        self.nSegments = int((len(self.dataX) - self.segmentLength) / self.shiftSize) + 1  # atention: in python 3.x, / is float division!
        self.windowType = windowType

    def computeWelch(self):
        self.buildWindow(self.windowType)
        self.DFTx, self.freq = self.DFT(self.dataX)
        self.DFTy, _ = self.DFT(self.dataY)

        self.Sxx = self.getAutoSpectrum(self.DFTx, forceReal=True)
        self.Syy = self.getAutoSpectrum(self.DFTy, forceReal=True)
        self.Sxy = self.getCrossSpectrum(self.DFTx, self.DFTy)
        self.Syx = self.getCrossSpectrum(self.DFTy, self.DFTx)

        self.freqRangeExtractor = tools.CARfreqRange(self.freq)

    def filterAll(self, filterType='rect', nTaps=2, keepFirst=True):
        self.Sxx = self.LPfilter(self.Sxx, filterType, nTaps, keepFirst)
        self.Syy = self.LPfilter(self.Syy, filterType, nTaps, keepFirst)
        self.Sxy = self.LPfilter(self.Sxy, filterType, nTaps, keepFirst)
        self.Syx = self.LPfilter(self.Syx, filterType, nTaps, keepFirst)

    # creates a window for welch method. You probably don't have to call it directly. See DFTwelch below.
    def buildWindow(self, windowType='hann'):
        self.windowType = windowType.lower()
        if self.windowType == 'hann':
            self.window = scipySignal.windows.hann(self.segmentLength,sym=False)
        elif self.windowType == 'tukey':
            self.window = scipySignal.windows.tukey(self.segmentLength,sym=False, alpha=0.5)
        elif self.windowType in ['boxcar', 'rectangular']:
            self.window = scipySignal.windows.boxcar(self.segmentLength,sym=False)
        elif self.windowType == 'hamming':
            self.window = scipySignal.windows.hamming(self.segmentLength,sym=False)

    def DFT(self, signal):
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
        # if nwindows==None:
        # adjust wlenght allowing for requested overlap and nwindows with
        # else:
        # wlenght = round(np.floor(freq*lenwind))

        DFTvalues = []

        for i in range(self.nSegments):
            startIdx = i * self.shiftSize
            endIdx = startIdx + self.segmentLength

            signalSegment = signal[startIdx:endIdx]

            signalSegment = signalSegment * self.window

            DFTvalues.append(scipyFFTpack.fft(signalSegment))  # FFT of equation 2 of notebook 3, page 36

        # frequency vector
        deltaF_Hz = self.Fs_Hz / self.segmentLength
        freqVals = np.arange(self.segmentLength) * deltaF_Hz

        return DFTvalues, freqVals

    def getAutoSpectrum(self, DFTx, forceReal=True):
        normWindowSq = np.linalg.norm(self.window) ** 2

        Sxx = np.zeros(self.segmentLength)
        for i in range(self.nSegments):
            if forceReal:  # see notebook 3, page 36 equation 5
                Sxx += np.multiply(np.conjugate(DFTx[i]), DFTx[i]).real * self.Ts / normWindowSq
            else:
                Sxx += np.multiply(np.conjugate(DFTx[i]), DFTx[i]) * self.Ts / normWindowSq

        Sxx /= self.nSegments  # divides by nSegments to compute the average Sxx
        return Sxx

    def getCrossSpectrum(self, DFTx, DFTy):
        normWindowSq = np.linalg.norm(self.window) ** 2

        Sxy = np.zeros(self.segmentLength,dtype=np.complex128)
        for i in range(self.nSegments):  # see notebook 3, page 36 equation 6
            Sxy += np.multiply(np.conjugate(DFTx[i]), DFTy[i]) * self.Ts / normWindowSq

        Sxy /= self.nSegments  # divides by nSegments to compute the average Sxy
        return Sxy

    def LPfilter(self, signal, filterType='triangular', nTaps=3, keepFirst=False):
        if keepFirst:
            temp = signal[0]
            signal[0] = signal[1]

        if filterType in ['rect', 'boxcar']:
            window = scipySignal.windows.boxcar(nTaps)
            window /= np.sum(window)
        elif filterType == 'triangular':
            window = scipySignal.windows.triang(nTaps)
            window /= np.sum(window)

        signal = scipySignal.filtfilt(window, [1.0], signal)

        if keepFirst:
            signal[0] = temp

        return signal

    def save(self, fileName, sideLabel='L', writeMode='w'):
        fileObj = open(fileName, 'w')

        np.set_printoptions(threshold=np.inf)

        fileObj.write('SIDE=%s\n' % sideLabel)
        fileObj.write('NPOINTS=%d\n' % len(self.freqRangeExtractor.getFreq(freqRange='ALL')))
        fileObj.write('UNIT_X=%s\n' % self.unitX)
        fileObj.write('UNIT_Y=%s\n' % self.unitY)
        fileObj.write('FREQ_HZ=%s\n' % np.array_str(self.freqRangeExtractor.getFreq(freqRange='ALL'), max_line_width=1000))
        fileObj.write('Sxx=%s\n' % np.array_str(self.freqRangeExtractor.getSignal(self.Sxx, freqRange='ALL'), max_line_width=1000))
        fileObj.write('Syy=%s\n' % np.array_str(self.freqRangeExtractor.getSignal(self.Syy, freqRange='ALL'), max_line_width=1000))
        fileObj.write('Sxy_REAL=%s\n' % np.array_str(np.real(self.freqRangeExtractor.getSignal(self.Sxy, freqRange='ALL')), max_line_width=1000))
        fileObj.write('Sxy_IMAG=%s\n' % np.array_str(np.imag(self.freqRangeExtractor.getSignal(self.Sxy, freqRange='ALL')), max_line_width=1000))
        fileObj.write('Syx_REAL=%s\n' % np.array_str(np.real(self.freqRangeExtractor.getSignal(self.Syx, freqRange='ALL')), max_line_width=1000))
        fileObj.write('Syx_IMAG=%s\n' % np.array_str(np.imag(self.freqRangeExtractor.getSignal(self.Syx, freqRange='ALL')), max_line_width=1000))
        fileObj.write('=' * 80 + '\n')

        fileObj.close()
