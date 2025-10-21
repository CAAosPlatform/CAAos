#!/bin/python

# -*- coding: utf-8 -*-
import numpy as np
from scipy import interpolate as scipyInterpolate
from scipy import signal as scipySignal


class beat2beat():
    """
    Class to compute beat-to-beat signals from a given signal and its beat indices.
    The beat-to-beat signals computed are the maximum, minimum, and average values within each
    beat interval.
    The class also provides methods to low-pass filter and resample the beat-to-beat signals
    """

    def __init__(self, data, beat_idx, data_samplingRate_Hz, resampleRate_Hz=5.0, resampleMethod='linear'):
        """
        Initialize the beat2beat object by computing the beat-to-beat signals.
        The beat-to-beat signals are computed as the maximum, minimum, and average values
        within each beat interval defined by the beat indices.

        Args:
            data (numpy.ndarray): input data signal
            beat_idx (numpy.ndarray): indices of the beats in the data signal
            data_samplingRate_Hz (float): sampling rate of the input data signal
            resampleRate_Hz (float): sampling rate after resampling the beat-to-beat signals. (Default is 5.0 Hz)
            resampleMethod (str): resampling interpolation method. Valid methods are:
                    STANDARD METHODS: 'linear' (default), 'nearest', 'previous', 'next'
                    SPLINE METHODS: 'zero', 'slinear', 'quadratic', 'cubic',
        """
        self.max = []
        self.min = []
        self.avg = []
        self.xData = beat_idx[0:-1] / data_samplingRate_Hz
        self.nPoints = self.xData.shape[0]

        for i in range(len(beat_idx) - 1):
            # compute max, min and avg valuea in each beat interval
            beatInvervalVals=data[beat_idx[i]:beat_idx[i + 1]]
            self.max.append(max(beatInvervalVals))
            self.min.append(min(beatInvervalVals))
            self.avg.append(np.mean(beatInvervalVals))
        self.max = np.array(self.max)
        self.min = np.array(self.min)
        self.avg = np.array(self.avg)

        self.resample(resampleRate_Hz, resampleMethod)

    def LPfilter(self, method='movingAverage', nTaps=5):
        """
        Apply a lowpass filter to the signal data.

        Args:
            method (str): type of filter.
                    - 'movingAverage': moving average filter (Default)

            nTaps (int): number of taps for the filter.
                         Must be odd number. Default is 5.

        Returns:
            none

        """
        if method == 'movingAverage':
            self.max = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.max)
            self.min = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.min)
            self.avg = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.avg)

    def resample(self, resampleRate_Hz, method='linear'):
        """
        Resample the beat-to-beat signals.

        Args:
            resampleRate_Hz (float): sampling rate after resampling the beat-to-beat signals. Value in Hertz.
            method (str): resampling interpolation method. Valid methods are:
                    STANDARD METHODS: 'linear' (default), 'nearest', 'previous', 'next'
                    SPLINE METHODS: 'zero', 'slinear', 'quadratic', 'cubic',
        Returns:
            None
        """

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
