#!/bin/python

# -*- coding: utf-8 -*-
import numpy as np
from scipy import interpolate as scipyInterpolate
from scipy import signal as scipySignal


class beat2beat():

    # data_samplingRate_Hz: sampling rate associated to data and beat_idx indices
    # resampleRate_Hz: sampling rate after resampling the beat to beat signal
    # resampling method
    # valid methods:            'linear', 'nearest',
    # spline methods:           'zero', 'slinear', 'quadratic', 'cubic',
    # previoues or next values: 'previous', 'next'
    def __init__(self, data, beat_idx, data_samplingRate_Hz, resampleRate_Hz=5.0, resampleMethod='linear'):
        self.max = []
        self.min = []
        self.avg = []
        self.xData = beat_idx[0:-1] / data_samplingRate_Hz
        self.nPoints = self.xData.shape[0]

        for i in range(len(beat_idx) - 1):
            self.max.append(max(data[beat_idx[i]:beat_idx[i + 1]]))
            self.min.append(min(data[beat_idx[i]:beat_idx[i + 1]]))
            self.avg.append(np.mean(data[beat_idx[i]:beat_idx[i + 1]]))
        self.max = np.array(self.max)
        self.min = np.array(self.min)
        self.avg = np.array(self.avg)

        self.resample(resampleRate_Hz, resampleMethod)

    def LPfilter(self, method='movingAverage', nTaps=5):
        if method == 'movingAverage':
            self.max = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.max)
            self.min = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.min)
            self.avg = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.avg)

    def resample(self, resampleRate_Hz, method='linear'):
        xNew = np.arange(self.xData[0], self.xData[-1], 1.0 / resampleRate_Hz)

        # max
        f = scipyInterpolate.interp1d(self.xData, self.max, kind=method, fill_value=(self.max[0], self.max[-1]), assume_sorted=True)
        self.max = f(xNew)
        # min
        f = scipyInterpolate.interp1d(self.xData, self.min, kind=method, fill_value=(self.min[0], self.min[-1]), assume_sorted=True)
        self.min = f(xNew)
        # avg
        f = scipyInterpolate.interp1d(self.xData, self.avg, kind=method, fill_value=(self.avg[0], self.avg[-1]), assume_sorted=True)
        self.avg = f(xNew)

        self.xData = xNew
        self.nPoints = self.xData.shape[0]

        self.samplingRate_Hz = float(resampleRate_Hz)
