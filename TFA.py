#!/bin/python

import copy
# -*- coding: utf-8 -*-
import sys

import numpy as np
from matplotlib import pyplot as plt

import ARsetup
import tools
from PSDestimator import PSDestimator


def diferencaPedro(numpyData, file, label, isComplex=False):
    if isComplex:
        resultadoPedro = np.loadtxt(file).view(complex)
    else:
        resultadoPedro = np.loadtxt(file)
    print('maior erro em modulo %s : %f' % (label, np.amax(np.absolute(numpyData - resultadoPedro))))


def ovelapAdjustment(sizeSignal, wlength, overlap):
    nSegments = np.floor((sizeSignal - wlength) / (wlength * (1 - overlap))) + 1  # atention: in python 3.x, / is float division!
    if nSegments > 0:
        shift = int((sizeSignal - wlength) / (nSegments - 1))  # atention: in python 3.x, / is float division!
        newOverlap = (wlength - shift) / wlength
    else:
        print('ERROR: window length larger than the signal!')
        newOverlap = overlap

    return newOverlap


class transferFunctionAnalysis():
    def __init__(self, welchData):
        self.welch = welchData
        self.nSegments = self.welch.nSegments
        self.freq = self.welch.freq
        self.Sxx = self.welch.Sxx
        self.Syy = self.welch.Syy
        self.Sxy = self.welch.Sxy
        self.Syx = self.welch.Syx
        self.freqRangeExtractor = tools.CARfreqRange(self.freq)

    def save(self, fileName, freqRange='ALL', sideLabel='L', writeMode='w'):
        # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'

        with open(fileName, writeMode) as fileObj:
            fileObj.write('ESTIMATOR_TYPE=%s\n' % self.Htype)
            fileObj.write('SIDE=%s\n' % sideLabel)
            fileObj.write('NPOINTS=%d\n' % len(self.getFreq(freqRange)))

            args = dict(max_line_width=np.inf, precision=8, separator=' ', floatmode='maxprec_equal', threshold=np.inf)
            fileObj.write('FREQ_(HZ)=' + np.array2string(self.getFreq(freqRange), **args) + '\n')
            fileObj.write('H_REAL=' + np.array2string(np.real(self.getH(freqRange, coheTreshold=False)), **args) + '\n')
            fileObj.write('H_IMAG=' + np.array2string(np.imag(self.getH(freqRange, coheTreshold=False)), **args) + '\n')
            fileObj.write('H_GAIN=' + np.array2string(self.getGain(freqRange, coheTreshold=False), **args) + '\n')
            fileObj.write(
                'H_PHASE_(DEG)=' + np.array2string(self.getPhase(freqRange, coheTreshold=False, remNegPhase=False) * 180 / np.pi, **args) + '\n')
            fileObj.write('H_COHERENCE=' + np.array2string(self.getCoherence(freqRange), **args) + '\n')

            fileObj.write('=' * 80 + '\n')

    def saveStatistics(self, fileName, sideLabel='L', coheTreshold=False, remNegPhase=False, writeMode='w'):

        print('Saving TFA statistics...')

        with open(fileName, writeMode) as fileObj:
            fileObj.write('SIDE=%s\n' % sideLabel)
            fileObj.write('COHERENCE_TRESHOLD=%s\n' % str(coheTreshold))
            fileObj.write('REMOVE_NEGATIVE_PHASE=%s\n' % str(remNegPhase))
            for r in ['VLF', 'LF', 'HF']:
                fileObj.write('-' * 30 + '\n')
                fileObj.write('FREQUENCY_RANGE=%s\n' % r)

                args = dict(max_line_width=np.inf, precision=8, separator=' ', floatmode='maxprec_equal', threshold=np.inf)
                fileObj.write('FREQ_(HZ)=' + np.array2string(self.getFreq(r), **args) + '\n')
                fileObj.write('H_REAL=' + np.array2string(np.real(self.getH(r, coheTreshold=False)), **args) + '\n')
                fileObj.write('H_IMAG=' + np.array2string(np.imag(self.getH(r, coheTreshold=False)), **args) + '\n')
                [gain_avg, gain_std, gain_min, gain_max] = self.getGainStatistics(r, coheTreshold)
                [phas_avg, phas_std, phas_min, phas_max] = self.getPhaseStatistics(r, coheTreshold, remNegPhase)
                [cohe_avg, cohe_std, cohe_min, cohe_max] = self.getCoherenceStatistics(r)
                fileObj.write('GAIN_AVG=%f\n' % gain_avg)
                fileObj.write('GAIN_STD=%f\n' % gain_std)
                fileObj.write('PHASE_DEG_AVG=%f\n' % (phas_avg * 180 / np.pi))
                fileObj.write('PHASE_DEG_STD=%f\n' % (phas_std * 180 / np.pi))
                fileObj.write('COHE_AVG=%f\n' % cohe_avg)
                fileObj.write('COHE_STD=%f\n' % cohe_std)
            fileObj.write('============================================\n')

        print('Ok!')

    # estimate H1
    def computeH1(self):
        self.Htype = 'H1'
        self.H = np.divide(self.Sxy, self.Sxx)
        self.coherence = np.divide(np.absolute(self.Sxy) ** 2, np.multiply(self.Sxx, self.Syy))

    # estimate H2
    def computeH2(self):
        self.Htype = 'H2'
        self.H = np.divide(self.Syy, self.Syx)
        self.coherence = np.divide(np.absolute(self.Sxy) ** 2, np.multiply(self.Sxx, self.Syy))

    # returns a copy of the signal with NaNs where coherence< limit
    # significanceAlpha: string. one of the following:  '1%', '5%', '10%'
    def applyCohTreshold(self, signal, significanceAlpha='5%'):
        temp = copy.deepcopy(signal)
        criticalValue = ARsetup.cohThresholdDict[significanceAlpha][self.nSegments]
        temp[self.coherence < criticalValue] = np.nan
        return temp

    def getFreq(self, freqRange='ALL'):
        return self.freqRangeExtractor.getFreq(freqRange)

    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'full'
    def getH(self, freqRange='ALL', coheTreshold=False):
        if coheTreshold:
            values = self.applyCohTreshold(self.H)
        else:
            values = self.H

        return self.freqRangeExtractor.getSignal(values, freqRange)

    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getCoherence(self, freqRange='ALL'):
        return self.freqRangeExtractor.getSignal(self.coherence, freqRange)

    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getGain(self, freqRange='ALL', coheTreshold=False):
        if coheTreshold:
            values = self.applyCohTreshold(np.absolute(self.H))
        else:
            values = np.absolute(self.H)

        return self.freqRangeExtractor.getSignal(values, freqRange)

    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getPhase(self, freqRange='ALL', coheTreshold=False, remNegPhase=False):
        if coheTreshold:
            values = self.applyCohTreshold(np.angle(self.H))
        else:
            values = np.angle(self.H)

        # remove negative phases
        if remNegPhase:
            values[(values < 0) & (self.freq < 0.1)] = np.nan

        return self.freqRangeExtractor.getSignal(values, freqRange)

    def getCoherenceStatistics(self, freqRange='ALL'):
        return self.freqRangeExtractor.getStatistics(self.coherence, freqRange)

    def getGainStatistics(self, freqRange='ALL', coheTreshold=False):
        if coheTreshold:
            values = self.applyCohTreshold(np.absolute(self.H))
        else:
            values = np.absolute(self.H)

        return self.freqRangeExtractor.getStatistics(values, freqRange)

    def getPhaseStatistics(self, freqRange='ALL', coheTreshold=False, remNegPhase=False):
        if coheTreshold:
            values = self.applyCohTreshold(np.angle(self.H))
        else:
            values = np.angle(self.H)

        # remove negative phases
        if remNegPhase:
            values[(values < 0) & (self.freq < 0.1)] = np.nan

        return self.freqRangeExtractor.getStatistics(values, freqRange)

    def savePlot(self, fileNamePrefix=None, fileType='png', coheTreshold=True, significanceAlpha='5%', remNegPhase=True, figDpi=250, fontSize=6):
        # fileType: 'png','jpg','tif','pdf','svg','eps','ps'
        fig, ax = plt.subplots(3, 1, sharex=True, figsize=[8, 5])
        freqRangeColors = ['#d5e5ff', '#d7f4d7', '#ffe6d5']
        # ---------------------
        # Gain Plot
        # ---------------------
        if coheTreshold:
            # dashed line
            ax[0].plot(self.getFreq('FULL'), self.getGain('FULL'), c='k', linewidth=1, linestyle=(0, (5, 5)), label='_nolegend_')

        ax[0].plot(self.getFreq('FULL'), self.getGain('FULL', coheTreshold=coheTreshold), c='k', linewidth=1.2, marker='o', markerSize=2.5)

        # ax[0].semilogy(self.getFreq('FULL'),abs(self.Syx), c='k',linewidth=1,label='_nolegend_')
        # ax[0].semilogy(self.getFreq('FULL'),abs(self.Sxy), c='b',linewidth=1,label='_nolegend_')
        # ax[0].semilogy(self.getFreq('FULL'),abs(self.Sxx), c='r',linewidth=1,label='_nolegend_')
        ax[0].set_ylabel('Gain [ adim. ]')
        # ax[0].legend(["Python"])
        ax[0].set_xlim([0, ARsetup.freqRangeDic['HF'][1]])
        ax[0].set_ylim([0, 1.05 * np.nanmax(self.getGain('ALL', coheTreshold=coheTreshold))])
        ax[0].grid(axis='x')

        # plot average horizontal lines for each frequency range
        ymin, ymax = ax[0].get_ylim()
        deltaY = ymax - ymin
        for i, fRange in enumerate(['VLF', 'LF', 'HF']):
            [mean, std, _, _] = self.getGainStatistics(fRange, coheTreshold)
            ax[0].hlines(mean, ARsetup.freqRangeDic[fRange][0], ARsetup.freqRangeDic[fRange][1], linestyle='dashed', color='red', linewidth=0.7)
            ax[0].axvspan(ARsetup.freqRangeDic[fRange][0], ARsetup.freqRangeDic[fRange][1], facecolor=freqRangeColors[i], alpha=1.0)
            ax[0].text(ARsetup.freqRangeDic[fRange][0], deltaY * 0.03 + mean, '$\mu=${0:.2f}'.format(mean) + '\n' + '$ \sigma=${0:.2f}'.format(std),
                       color='r', fontSize=fontSize)

        # ---------------------
        # Phase Plot
        # ---------------------
        if coheTreshold or remNegPhase:
            # dashed line
            ax[1].plot(self.getFreq('FULL'), self.getPhase('FULL') * 180 / np.pi, c='k', linewidth=1, linestyle=(0, (5, 5)), label='_nolegend_')
        ax[1].plot(self.getFreq('FULL'), self.getPhase('FULL', coheTreshold, remNegPhase) * 180 / np.pi, c='k', linewidth=1.2, marker='o',
                   markerSize=2.5)

        ax[1].set_ylabel('Phase [ degree ]')
        # ax[1].set_xlim([0,ARsetup.freqRangeDic['HF'][1]])
        ax[1].set_ylim([0, 1.05 * np.nanmax(self.getPhase('ALL', coheTreshold, remNegPhase)) * 180 / np.pi])
        ax[1].grid(axis='x')

        # plot average horizontal lines for each frequency range
        ymin, ymax = ax[1].get_ylim()
        deltaY = ymax - ymin
        for i, fRange in enumerate(['VLF', 'LF', 'HF']):
            [mean, std, _, _] = self.getPhaseStatistics(fRange, coheTreshold, remNegPhase)
            mean *= 180 / np.pi
            std *= 180 / np.pi
            ax[1].hlines(mean, ARsetup.freqRangeDic[fRange][0], ARsetup.freqRangeDic[fRange][1], linestyle='dashed', color='red', linewidth=0.7)
            ax[1].axvspan(ARsetup.freqRangeDic[fRange][0], ARsetup.freqRangeDic[fRange][1], facecolor=freqRangeColors[i], alpha=1.0)
            ax[1].text(ARsetup.freqRangeDic[fRange][0], deltaY * 0.03 + mean, '$\mu=${0:.2f}'.format(mean) + '\n' + '$ \sigma=${0:.2f}'.format(std),
                       color='r', fontSize=fontSize)

        # ---------------------
        # Coherence
        # ---------------------
        ax[2].plot(self.getFreq('FULL'), self.getCoherence('FULL'), c='k', linewidth=1.2, marker='o', markerSize=2.5)
        ax[2].set_ylabel('Coherence [ adim. ]')
        ax[2].set_xlabel('Frequency (Hz)')
        # ax[2].set_xlim([0,ARsetup.freqRangeDic['HF'][1]])
        ax[2].set_ylim([0, 1])
        ax[2].grid(axis='x')

        # plot average horizontal lines for each frequency range
        ymin, ymax = ax[2].get_ylim()
        deltaY = ymax - ymin
        for i, fRange in enumerate(['VLF', 'LF', 'HF']):
            [mean, std, _, _] = self.getCoherenceStatistics(fRange)
            ax[2].hlines(mean, ARsetup.freqRangeDic[fRange][0], ARsetup.freqRangeDic[fRange][1], linestyle='dashed', color='red', linewidth=0.7)
            ax[2].axvspan(ARsetup.freqRangeDic[fRange][0], ARsetup.freqRangeDic[fRange][1], facecolor=freqRangeColors[i], alpha=1.0)
            ax[2].text(ARsetup.freqRangeDic[fRange][0], deltaY * 0.03 + mean, '$\mu=${0:.2f}'.format(mean) + '\n' + '$ \sigma=${0:.2f}'.format(std),
                       color='r', fontSize=fontSize)

        # threshold grey region
        if coheTreshold:
            ax[2].axhspan(0, ARsetup.cohThresholdDict[significanceAlpha][self.nSegments], facecolor='0.9', alpha=1.0)

        fig.tight_layout()
        plt.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.95, wspace=None, hspace=0.1)

        if fileNamePrefix is not None:
            plt.savefig(fileNamePrefix + '.' + fileType, dpi=figDpi, format=fileType, transparent=True)
        else:
            plt.show()


if __name__ == '__main__':

    if sys.version_info.major == 2:
        sys.stdout.write('Sorry! This program requires Python 3.x\n')
        sys.exit(1)

    ABP = np.loadtxt('../codigoPedro/lixo_ABP.txt')
    CBFv_L = np.loadtxt('../codigoPedro/lixo_CBF_L.txt')
    samplingFrequency_Hz = 100

    overlap = 59.99 / 100  # overlap
    segmentLength_s = 102.4
    windowType = 'hanning'
    overlap_adjust = True
    if overlap_adjust:
        overlap = ovelapAdjustment(ABP.shape[0], segmentLength_s * samplingFrequency_Hz, overlap)

    # Power spectrum Estimation
    welch = PSDestimator(ABP, CBFv_L, samplingFrequency_Hz, overlap, segmentLength_s, windowType, removeBias=False)
    welch.computeWelch()
    welch.filterAll(filterType='rect', nTaps=2, keepFirst=True)
    # Start TF analysis
    TF = transferFunctionAnalysis(welchData=welch)
    TF.computeH1()

    welch.save(fileName='lixo.PSD', freqRange='ALL')
    TF.save(fileName='lixo.TF', sideLabel='R')
    if True:
        TF.savePlot(fileNamePrefix=None)
    else:
        TF.savePlot(fileNamePrefix='lixo', fileType='png', figDpi=250, fontSize=6)
        TF.savePlot(fileNamePrefix='lixo', fileType='svg', figDpi=250, fontSize=6)
        TF.savePlot(fileNamePrefix='lixo', fileType='pdf', figDpi=250, fontSize=6)
