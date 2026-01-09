#!/bin/python

# -*- coding: utf-8 -*-
import numpy as np
from lxml import etree as ETree
from scipy import interpolate as scipyInterpolate
from scipy import signal as scipySignal

from caaos.tools import ampdLib
from caaos.core.signals import signals_b2b
from caaos.tools import tools

class signal_poit_by_point(signal):
    """
    This class defines a signal object that is processed point by point. It inherits from the signal class.
    The signal object contains the signal data and its properties.
    It also contains methods to process the signal data and a beat2beat object to store the beat-to-beat signals.
    """
    def __init__(self, channel, label, unit, dataMaxLength, samplingRate_Hz, operationsXML):
        """
        This function initializes a signal object. The signal object contains the signal data and its properties.

        Args:
            channel (int): number of the channel.
            label (str): lable of the plots
            unit (str): unit of the signal
            dataMaxLength(int): maximum length of the signal data
            samplingRate_Hz (float): sampling rate in Hz
            operationsXML (lxml.etree._Element): XML element to store the operations performed on the signal
        """
        self.allData=np.zeros(dataMaxLength)
        self.latestDataIndex = -1  # index of the latest written data point

        #slice data to be passed to the parent class
        data= self.allData[:self.latestDataIndex]  # initialize with empty data

        super().__init__(channel, label, unit, data, samplingRate_Hz, operationsXML)


class signal():
    """
    This class defines a signal object. The signal object contains the signal data and its properties.
    It also contains methods to process the signal data and a beat2beat object to store the beat-to-beat signals.
    """
    def __init__(self, channel, label, unit, data, samplingRate_Hz, operationsXML):
        """
        This function initializes a signal object. The signal object contains the signal data and its properties.

        Args:
            channel (int): number of the channel.
            label (str): lable of the plots
            unit (str): unit of the signal
            data (numpy.ndarray): 1D numpy array with the signal data
            samplingRate_Hz (float): sampling rate in Hz
            operationsXML (lxml.etree._Element): XML element to store the operations performed on the signal
        """
        self.channel = channel
        self.label = label
        self.unit = unit
        self.sigType = None  # 'ABP','CBFV_L', 'CBFV_R', 'ETCO2', None
        self.data = data
        self.samplingRate_Hz = float(samplingRate_Hz)
        self.nPoints = self.data.shape[0]
        self.operationsXML = operationsXML

    def info(self):
        """
        Print the signal information.
        """
        print('-------------------------------')
        print('Channel: %d' % self.channel)
        print('label: ' + self.label)
        print('unit: ' + self.unit)
        print('sigType: ' + str(self.sigType))
        print('nPoints: %d' % self.nPoints)
        print('samplingRate (Hz): %g' % self.samplingRate_Hz)
        print('-------------------------------')

    def getTimeVector(self, t0=0.0):
        """
        Returns a vector with the time values of thesignal samples.

        Args:
            t0 (float): initial time in seconds. Default is 0.0 s.

        Returns:
            numpy.ndarray: vector with time values in seconds.
        """
        return t0 + np.arange(self.nPoints) / self.samplingRate_Hz

    def saveData(self, fileObj):
        """
        Save the signal data to a file object in the following format:

        CHANNEL=int
        LABEL=string
        UNIT=string
        SIGNAL_TYPE=string
        SAMPLING_RATE_HZ=float
        NPOINTS=int
        DATA=[ list of floats ]

        Args:
            fileObj (fileobj): output file object where data will be saved.

        Returns:
            None

        """
        fileObj.write('CHANNEL=%d\n' % self.channel)
        fileObj.write('LABEL=%s\n' % self.label)
        fileObj.write('UNIT=%s\n' % self.unit)
        fileObj.write('SIGNAL_TYPE=%s\n' % str(self.sigType))
        fileObj.write('SAMPLING_RATE_HZ=%g\n' % self.samplingRate_Hz)
        fileObj.write('NPOINTS=%d\n' % self.nPoints)

        string = np.array2string(self.data, max_line_width=np.inf, precision=8, separator=' ', floatmode='maxprec_equal', threshold=np.inf)
        fileObj.write('DATA=' + string + '\n')

        fileObj.write('=' * 80 + '\n')

    def saveB2B(self, fileObj):
        """
        Save the beat-to-beat data to a file object in  the following format:

        CHANNEL=int
        LABEL=string
        UNIT=string
        SIGNAL_TYPE=string
        SAMPLING_RATE_HZ=float
        NPOINTS=int
        TIME_(S)=[ list of floats ]
        MAX=[ list of floats ]    % maximum values of each beat
        MIN=[ list of floats ]    % minimum values of each beat
        AVG=[ list of floats ]    % average values of each beat

        Args:
            fileObj (fileobj): output file object where data will be saved.

        Returns:
            None

        """
        fileObj.write('CHANNEL=%d\n' % self.channel)
        fileObj.write('LABEL=%s\n' % self.label)
        fileObj.write('UNIT=%s\n' % self.unit)
        fileObj.write('SIGNAL_TYPE=%s\n' % str(self.sigType))
        fileObj.write('SAMPLING_RATE_HZ=%g\n' % self.beat2beatData.samplingRate_Hz)
        fileObj.write('NPOINTS=%d\n' % self.beat2beatData.nPoints)

        # same set of arguments will be passed to the array2string functions
        args = dict(max_line_width=np.inf, precision=8, separator=' ', floatmode='maxprec_equal', threshold=np.inf)
        fileObj.write('TIME_(S)=' + np.array2string(self.beat2beatData.xData, **args) + '\n')
        fileObj.write('MAX=' + np.array2string(self.beat2beatData.max, **args) + '\n')
        fileObj.write('MIN=' + np.array2string(self.beat2beatData.min, **args) + '\n')
        fileObj.write('AVG=' + np.array2string(self.beat2beatData.avg, **args) + '\n')

        fileObj.write('=' * 80 + '\n')

    def registerOperation(self, xmlElement):
        """
        This function add the channel number information to the operation ETree element and appends it to the operationsXML tree.
        Args:
            xmlElement (ETree.Element): element describing the operation to be registered.

        Returns:
            None
        """
        tools.ETaddElement(parent=xmlElement, tag='channel', text=str(self.channel), position=0)
        self.operationsXML.append(xmlElement)

    def setInfo(self,label=None,unit=None,sigType=None, register=True):
        """
        Set signal information. Any argument can be None, in this case the corresponding attribute will not be changed.

        Args:
            label (str): new label
            unit (str): new unit
            sigType (str): one of the following: 'ABP','CBFV_L', 'CBFV_R', 'ETCO2', None
            register (bool): whether to register the operation in the operations file. Default is True.

        Returns:
            None:
        """
        if label is not None:
            self.label = label
        if unit is not None:
            self.unit = unit
        if sigType is not None:
            self.sigType = sigType

        # register operation
        if register:
            xmlElement = ETree.Element('signalInfo')
            if label is not None:
                tools.ETaddElement(parent=xmlElement, tag='label', text=label)
            if unit is not None:
                tools.ETaddElement(parent=xmlElement, tag='unit', text=unit)
            if sigType is not None:
                tools.ETaddElement(parent=xmlElement, tag='type', text=sigType)
            self.registerOperation(xmlElement)

    # def setLabel(self, newLabel, register=True):
    #     """ this function is deprecated. Use setInfo instead"""
    #     self.label = newLabel
    #
    #     # register operation
    #     if register:
    #         xmlElement = ETree.Element('setLabel')
    #         tools.ETaddElement(parent=xmlElement, tag='label', text=newLabel)
    #         self.registerOperation(xmlElement)
    #
    # def setUnit(self, newUnit, register=True):
    #     """ this function is deprecated. Use setInfo instead"""
    #     self.unit = newUnit
    #
    #     # register operation
    #     if register:
    #         xmlElement = ETree.Element('setUnit')
    #         tools.ETaddElement(parent=xmlElement, tag='unit', text=newUnit)
    #         self.registerOperation(xmlElement)
    #
    # def setType(self, newType, register=True):
    #     """ this function is deprecated. Use setInfo instead"""
    #     self.sigType = newType
    #
    #     # register operation
    #     if register:
    #         xmlElement = ETree.Element('setType')
    #         tools.ETaddElement(parent=xmlElement, tag='type', text=newType)
    #         self.registerOperation(xmlElement)
    #
    # def findPeaksBySegments(self, segmentLengh_s=20.0):
    #     """ this function is deprecated. Use findPeaks instead"""
    #
    #     segmentLength = segmentLengh_s * self.samplingRate_Hz  # equivalent to 20seconds of data
    #     nSegments = int(self.nPoints / segmentLength)
    #     fmax_bpm = 200
    #     DeltaTMin = int(60.0 / float(fmax_bpm) * self.samplingRate_Hz)  # number of samples that represents a frequency of 220bpm
    #
    #     dataSegments = np.array_split(self.data, nSegments)
    #
    #     peakIdx = np.array([], dtype=int)
    #     valleyIdx = np.array([], dtype=int)
    #
    #     idxStart = 0
    #     for s in range(len(dataSegments)):
    #         data = dataSegments[s]
    #         sMax = np.percentile(data, 90.0)
    #         smph = np.percentile(data, 60.0)
    #         sMin = np.percentile(data, 10.0)
    #         prominence = (sMax - sMin) * 0.1
    #
    #         peakIdxSegment = tools.detect_peaks(data, mph=smph, mpd=DeltaTMin, threshold=0, edge='rising', kpsh=False, MinPeakProminence=prominence,
    #                                             MinPeakProminenceSide='left', valley=False)
    #
    #         valleyIdxSegment = []
    #         for i in peakIdxSegment:
    #             cumulativeProminence = 0
    #             idx = i
    #             dx = data[idx] - data[idx - 1]
    #             while idx >= 0 and (dx > 0 or cumulativeProminence < (sMax - sMin) * 0.5):
    #                 cumulativeProminence += dx
    #                 idx -= 1
    #                 dx = data[idx] - data[idx - 1]
    #
    #             if idx >= 0:
    #                 valleyIdxSegment.append(idx)
    #
    #         valleyIdxSegment = np.array(valleyIdxSegment)
    #         # print(valleyIdxSegment)
    #         peakIdx = np.append(peakIdx, peakIdxSegment + idxStart, axis=None)
    #         valleyIdx = np.append(valleyIdx, valleyIdxSegment + idxStart, axis=None)
    #         idxStart += data.shape[0]
    #
    #     # print(peakIdx)
    #     peakVal = self.data[peakIdx]
    #     valleyVal = self.data[valleyIdx]
    #
    #     return [peakIdx, peakVal, valleyIdx, valleyVal]

    def findPeaks(self, method='ampd', findPeaks=True, findValleys=False, register=False):
        """
        Find peaks and/or valleys in the signal data.

        Args:
            method (str): method to be used. Options are: 'ampd' (default), 'md' (deprecated)
            findPeaks (bool): whether to find peaks (default is True)
            findValleys (bool): whether to find valleys (default is False)
            register (bool): whether to register the operation in the operations file. Default is False.

        Returns:
            List[numpy.ndarray]: a list with four elements:
                - peakIdx: numpy array with the indexes of the peaks (None if findPeaks is False)
                - peakVal: numpy array with the values of the peaks (None if findPeaks is False)
                - valleyIdx: numpy array with the indexes of the valleys (None if findValleys is False)
                - valleyVal: numpy array with the values of the valleys (None if findValleys is False)

        """

        peakIdx = None
        peakVal = None
        valleyIdx = None
        valleyVal = None

        def removeNearbyPeaks(peakIdx, fmax_bpm = 250):
            # remove peaks that are too close to each other. For that we assume a maximum heart rate (defaults to 250bpm) and compute
            # the associated time between peaks. Any sucessive peak that is closer than this mininum time will be removed
            DeltaIdxMin = int(60.0 / float(fmax_bpm) * self.samplingRate_Hz)  # number of samples that represents a frequency of 250bpm

            temp = []
            for i in range(len(peakIdx) - 1):
                if peakIdx[i + 1] - peakIdx[i] > DeltaIdxMin:  # if they are not too  close
                    temp.append(peakIdx[i])
                else:
                    temp.append(max(peakIdx[i], peakIdx[i + 1]))  # otherwise adopt the largest index between these two peak candidates
            return temp

        if method.lower() == 'ampd':
            if findPeaks:

                peakIdx = ampdLib.ampdFast(self.data, 10, LSMlimit=0.2)
                # remove peaks that are too close to each other
                peakIdx = removeNearbyPeaks(peakIdx, fmax_bpm = 250) # 250 bmp max

            if findValleys:
                valleyIdx = ampdLib.ampdFast(-self.data, 10, LSMlimit=0.1)
                # remove peaks that are too close to each other
                valleyIdx = removeNearbyPeaks(valleyIdx, fmax_bpm = 250) # 250 bmp max

        if method.lower() == 'md':
            print('Find peaks: method "md" is deprecated. Use "ampd" instead.')
            print('Find peaks: method "md" is deprecated. Use "ampd" instead.')
            print('Find peaks: method "md" is deprecated. Use "ampd" instead.')
            fmax_bpm = 250
            sMax = np.percentile(self.data, 90.0)
            smph = np.percentile(self.data, 60.0)
            sMin = np.percentile(self.data, 10.0)
            prominence = (sMax - sMin) * 0.2

            DeltaTMin = int(60.0 / float(fmax_bpm) * self.samplingRate_Hz)  # number of samples that represents a frequency of 250bpm

            peakIdx = tools.detect_peaks(self.data, mph=smph, mpd=DeltaTMin, threshold=0, edge='rising', kpsh=False, MinPeakProminence=prominence,
                                         MinPeakProminenceSide='left', valley=False)

            if findValleys:
                valleyIdx = []
                for i in peakIdx:
                    cumulativeProminence = 0
                    idx = i
                    dx = self.data[idx] - self.data[idx - 1]
                    while idx >= 0 and (dx > 0 or cumulativeProminence < (sMax - sMin) * 0.5):
                        cumulativeProminence += dx
                        idx -= 1
                        dx = self.data[idx] - self.data[idx - 1]

                    valleyIdx.append(idx)

                valleyIdx = np.array(valleyIdx)

            if not findPeaks:
                peakIdx = None

        if findPeaks:
            peakIdx = np.unique(peakIdx)  # removes eventual repeated indexes
            peakVal = self.data[peakIdx]
        if findValleys:
            valleyIdx = np.unique(valleyIdx)  # removes eventual repeated indexes
            valleyVal = self.data[valleyIdx]

        # register operation
        if register:
            xmlElement = ETree.Element('findPeaksSignal')
            tools.ETaddElement(parent=xmlElement, tag='findPeaks', text=str(findPeaks))
            tools.ETaddElement(parent=xmlElement, tag='findValleys', text=str(findValleys))
            tools.ETaddElement(parent=xmlElement, tag='method', text=method)
            self.registerOperation(xmlElement)

        return [peakIdx, peakVal, valleyIdx, valleyVal]

    def yLimits(self, method='percentile', detrend=False, segmentIndexes=None):
        """
        Calculate the y-axis limits of the signal data.

        Args:
            method (str):
                    'absolute': uses the absolute min and max values of the signal
                    'percentile' (default): uses the 5th and 95th percentiles of the signal (default)
            detrend (bool): removes the linear trend of the signal before calculating the limits
            segmentIndexes (list or None):
                     - None (default) considers all data
                     - list: list with start and end indexes
        Returns:
            List[numpy.float64]:  [y_min, y_max]
        """
        min = 0
        max = 0

        if segmentIndexes is not None:
            data = self.data[segmentIndexes[0]:segmentIndexes[1]]
        else:
            data = self.data

        if detrend:
            data = scipySignal.detrend(data, type='linear')

        if method == 'absolute':
            max = np.amax(data)
            min = np.amin(data)

        if method == 'percentile':
            min = np.percentile(data, 5.0)
            max = np.percentile(data, 95.0)
        return [min, max]

    # if segmentIndexes=None (default) considers all data, otherwise it is expected a list with start and end indexes
    def calibrate(self, valMax, valMin, method='percentile', segmentIndexes=None, register=True):
        """
        Calibrate the signal data to a new range [valMin, valMax] using linear interpolation.
        Args:
            valMax (float): maximum value of the new range.
            valMin (float): minimum value of the new range.
            method (string):
                    'absolute': uses the absolute min and max values of the signal
                    'percentile' (default): uses the 5th and 95th percentiles of the signal (default)
            segmentIndexes (list or None):
                     - None (default) considers all data
                     - list: list with start and end indexes
            register (bool): whether to register the operation in the operations file. Default is True.

        Returns: None

        """

        if valMax <= valMin:
            return
        # print(segmentIndexes)
        [x1, x2] = self.yLimits(method=method, detrend=False, segmentIndexes=segmentIndexes)

        y2 = valMax
        y1 = valMin

        # linear interpolation
        ang_coef = (y2 - y1) / float(x2 - x1)

        self.data = ang_coef * (self.data - x1) + y1

        # register operation
        if register:
            xmlElement = ETree.Element('calibrate')
            tools.ETaddElement(parent=xmlElement, tag='valMin', text=str(valMin))
            tools.ETaddElement(parent=xmlElement, tag='valMax', text=str(valMax))
            tools.ETaddElement(parent=xmlElement, tag='method', text=str(method))
            tools.ETaddElement(parent=xmlElement, tag='segmentIndexes', text=str(segmentIndexes).replace(',', ''))
            self.registerOperation(xmlElement)

    def cropInterval(self, start, end, register=True, RemoveSegment=False, segmentIndexes=None):
        """
        Remove elements between start and end indexes, including these limits.

        Args:
            start (int): start index
            end (int): end index
            register (bool): whether to register the operation in the operations file. Default is True.
            RemoveSegment (bool):
                if True, the start and end indexes will be adjusted to the nearest segmentIndexes values.
                if False (default), the start and end indexes will be used as is.
            segmentIndexes (Union[None, None]):
                list with the start and end indexes of the segments.
                if RemoveSegment is True, this argument must be provided.
                if RemoveSegment is False (default), this argument will be ignored.

        Returns:
            None:
        """
        # register operation
        if register:
            xmlElement = ETree.Element('cropInterval')
            tools.ETaddElement(parent=xmlElement, tag='frameStart', text=str(start))
            tools.ETaddElement(parent=xmlElement, tag='frameEnd', text=str(end))
            tools.ETaddElement(parent=xmlElement, tag='RemoveSegment', text=str(RemoveSegment))
            tools.ETaddElement(parent=xmlElement, tag='segmentIndexes', text=str(segmentIndexes))
            self.registerOperation(xmlElement)

        if RemoveSegment:
            if len(segmentIndexes) > 0:
                end = segmentIndexes[np.searchsorted(segmentIndexes, end)]
                start = segmentIndexes[np.searchsorted(segmentIndexes, start) - 1]

        if (end + 1) > len(self.data) or start < 0 or (end + 1) < start:
            print('Invalid interval')
            return

        self.data = np.delete(self.data, range(start, end + 1))
        self.nPoints = self.data.shape[0]

    # remove the specified number of elements from right.
    def cropFromEnd(self, nElem, register=True):
        """
        Remove the specified number of elements from the end (most recent data points) of the signal data.

        Args:
            nElem (int): number of elements to be removed from the end of the signal data.
                Ex: if nelem=1, removes only one element from the end
            register (bool): whether to register the operation in the operations file. Default is True.

        Returns:
            None:
        """
        if nElem > self.nPoints:
            print('data does not have so many elements')
            return
        if nElem < 0:
            print('negative number of elements')
            return
        self.cropInterval(self.nPoints - nElem, self.nPoints - 1, register)

    # remove the specified number of elements from right. Ex: if nelem=1, removes only one element from left
    def cropFromStart(self, nElem, register=True):
        if nElem > self.nPoints:
            print('data does not have so many elements')
            return
        if nElem < 0:
            print('negative number of elements')
            return
        self.cropInterval(0, nElem - 1, register)

    def resample(self, newSampleRate, method='linear', register=True):
        """
        Resample the signal data to a new sampling rate using interpolation.

        Args:
            newSampleRate (float): new sampling rate in Hz
            method (string): interpolation method. Valid methods are:
                    STANDARD METHODS: 'linear' (default), 'nearest', 'previous', 'next'
                    SPLINE METHODS: 'zero', 'slinear', 'quadratic', 'cubic',
            register (bool): whether to register the operation in the operations file. Default is True.

        Returns:
            None.

        """
        xData = np.arange(self.nPoints) / self.samplingRate_Hz
        f = scipyInterpolate.interp1d(xData, self.data, kind=method, fill_value=(self.data[0], self.data[-1]), assume_sorted=True)

        xNew = np.arange(xData[0], xData[-1], 1.0 / newSampleRate)
        self.data = f(xNew)

        self.samplingRate_Hz = float(newSampleRate)
        self.nPoints = self.data.shape[0]

        # register operation
        if register:
            xmlElement = ETree.Element('resample')
            tools.ETaddElement(parent=xmlElement, tag='sampleRate', attribList=[['unit', 'Hz']], text=str(newSampleRate))
            tools.ETaddElement(parent=xmlElement, tag='method', text=str(method))
            self.registerOperation(xmlElement)

    def interpolate(self, start, end, method='linear', register=True):
        """
        Interpolate the signal data in the interval [start, end] indices, including the limits. The original
        values in this interval will be replaced by the interpolated values.

        Args:
            start (int):  start index
            end (int): end index
            method (string): 'linear' (default)
            register (bool): whether to register the operation in the operations file. Default is True.

        Returns:

        """
        if (end + 1) > len(self.data) or start < 0 or (end + 1) < start:
            print('Invalid interval')
            return

        nIntervals = end - start

        if nIntervals < 1:
            return

        if method == 'linear':
            deltaY = (self.data[end] - self.data[start]) / nIntervals

            for i in range(nIntervals):
                self.data[start + i] = self.data[start] + deltaY * i

        # register operation
        if register:
            xmlElement = ETree.Element('interpolate')
            tools.ETaddElement(parent=xmlElement, tag='frameStart', text=str(start))
            tools.ETaddElement(parent=xmlElement, tag='frameEnd', text=str(end))
            tools.ETaddElement(parent=xmlElement, tag='method', text=str(method))
            self.registerOperation(xmlElement)

    def LPfilter(self, method='movingAverage', nTaps=5, order=3, register=True):
        """
        Apply a lowpass filter to the signal data.
        OBSERVATION: The butterworth filter has a fixed cutoff frequency of 20Hz.

        Args:
            method (str): type of filter.
                    - 'movingAverage': moving average filter (Default)
                    - 'median': median filter
                    - 'butterworth': Butterworth filter

            nTaps (int): number of taps for the filter. Used for movingAverage and median only.
                         Must be odd number. Default is 5.
            order (int): order of the filter. used for butterworth only. Default is 3.
            register (bool): whether to register the filter in the operations file. Default is True.

        Filter description:
            - butterworth: cutoff frequency is fixed at 20Hz.

        Returns:

        """

        if nTaps % 2 == 0 and method != 'butterworth':
            print('nTaps is even. Must be odd number. Canceling LPfilter...')
            return

        if method == 'movingAverage':
            self.data = scipySignal.filtfilt([1.0 / nTaps, ] * nTaps, [1.0], self.data)

        if method == 'median':
            self.data = scipySignal.medfilt(self.data, kernel_size=nTaps)

        if method == 'butterworth':
            fNyquist = self.samplingRate_Hz / 2.0
            fc_Hz = 20  # in Hertz
            wc_norm = fc_Hz / fNyquist  # must be normalized from 0 to 1, where 1 is the Nyquist frequency
            [b, a] = scipySignal.butter(N=order, Wn=wc_norm, btype='low', analog=False, output='ba')
            self.data = scipySignal.filtfilt(b, a, self.data)

        # register operation
        if register:
            xmlElement = ETree.Element('LPfilter')
            tools.ETaddElement(parent=xmlElement, tag='method', text=str(method))
            if method == 'movingAverage' or method == 'median':
                tools.ETaddElement(parent=xmlElement, tag='Ntaps', text=str(nTaps))
            if method == 'butterworth':
                tools.ETaddElement(parent=xmlElement, tag='order', text=str(order))
            self.registerOperation(xmlElement)

    def beat2beat(self, beat_idx, resampleRate_Hz=100.0, resampleMethod='linear'):
        """
        Compute beat-to-beat data from the signal data.
        Args:
            beat_idx (numpy.ndarray): vector with the indexes of the detected beats (peaks)
            resampleRate_Hz (float): resampling rate in Hz (default is 100.0 Hz)
            resampleMethod (str): resampling method (default is 'linear'). Valid methods are:
                    STANDARD METHODS: 'linear', 'nearest', 'previous', 'next'
                    SPLINE METHODS: 'zero', 'slinear', 'quadratic', 'cubic',

        Returns:
            None:
        """
        self.beat2beatData = signals_b2b.beat2beat(self.data, beat_idx, self.samplingRate_Hz, resampleRate_Hz, resampleMethod)

        if False:
            #save beat to beat data to temp file for debug
            file='/home/fernando/servidor/programas/00_UFABC/pulmonaryHipertension/src/temp_b2b.txt'
            with open(file,'w') as f:
                for i in range(len(beat_idx) - 1):
                    #crop in intervals for saving
                    beatInvervalVals = self.data[beat_idx[i]:beat_idx[i + 1]]
                    np.savetxt(f,beatInvervalVals.reshape(1, beatInvervalVals.shape[0]),delimiter=';')
