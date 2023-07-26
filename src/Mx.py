#!/bin/python

# -*- coding: utf-8 -*-
import numpy as np
from scipy import fftpack as scipyFFTpack
from scipy import signal as scipySignal
from matplotlib import pyplot as plt
import sys
import tools


# dataX, dataY:  numpy arrays, same lengths, same sampling frequency
# samplingFrequency_Hz: sampling frequency of the signal in Hertz
# epochLength_s: length of the epoch  where Pearson Correlation coef. is computed.
# blockLength_s: length of the block used to compute the averages. This number must be an integer divisor of 'epochLength_s'
class meanFlowIdx():
    def __init__(self, dataX, dataY, samplingFrequency_Hz, epochLength_s=30, blockLength_s=10, unitX=None, unitY=None):

        self.dataX = dataX
        self.dataY = dataY

        self.unitX = unitX
        self.unitY = unitY

        self.Fs_Hz = samplingFrequency_Hz
        self.Ts = 1.0 / self.Fs_Hz
        self.blockLength = int(self.Fs_Hz * blockLength_s)

        # number of blocks in one epoch, rounded to an integer
        self.nBlocks = int(epochLength_s / blockLength_s)

        # epoch length might be different from epochLength_s, ensuring we have an integer multiple of averages
        self.epochLength = int(self.Fs_Hz * epochLength_s)

        self.nEpochs = int(len(self.dataX) / self.epochLength)  # atention: in python 3.x, / is float division!

    def calcMx(self):
        # compute Mx for all epochs, without overlap
        pearsonCorrValues = []
        self.linearRegressionData = []

        for i in range(self.nEpochs):
            # extract epoch initial indice
            startIdx = i * self.epochLength
            [Mx, linearCoefs] = self.calcMxEpoch(startIdx, self.epochLength)
            pearsonCorrValues.append(Mx)
            self.linearRegressionData.append(linearCoefs)

        self.Mx = np.array(pearsonCorrValues)
        self.MxAvg = np.mean(self.Mx)

    def calcMxEpoch(self,epochIdxStart, epochLength):
        # computes the Pearson correlation coefficient for the specified epoch
        # extract epoch
        startIdx = epochIdxStart
        endIdx = epochIdxStart + epochLength

        epochX = self.dataX[startIdx:endIdx]
        epochY = self.dataY[startIdx:endIdx]

        #eliminate elements that do not belong the the integer number of blocks
        epochX = epochX[:self.nBlocks*self.blockLength]
        epochY = epochY[:self.nBlocks*self.blockLength]

        # split the epoch in blocks.
        blocksX = np.split(epochX, self.nBlocks)
        blocksY = np.split(epochY, self.nBlocks)

        avgX = np.array([np.average(x) for x in blocksX])
        avgY = np.array([np.average(x) for x in blocksY])

        #find the linear regression coefs y=ax+b
        [a, b] = self.linearRegression(avgX, avgY)

        Mx =np.corrcoef(avgX, avgY)[0, 1]  # extracts off diagonal element [0,1]

        return [Mx, { 'a':a, 'b':b, 'xData':avgX, 'yData':avgY }]

    def linearRegression(self,xData,yData):
        # fit a line epoch to the data
        #  y = ax + b
        M=np.vstack([xData, np.ones(len(xData))]).T

        [a, b] = np.linalg.lstsq(M, yData, rcond=None)[0]

        plot=False
        if plot:
            plt.plot(xData, yData, 'o', label='Original data', markersize=5)
            plt.plot(xData, a * xData + b, 'r', label='Fitted line')
            plt.legend()
            plt.show()

        return [a,b]

    def save(self, fileName, sideLabel='L', writeMode='w'):
        #write mode: 'w', 'a'

        with open(fileName, writeMode) as fileObj:
            np.set_printoptions(threshold=np.inf)

            fileObj.write('SIDE=%s\n' % sideLabel)
            fileObj.write('UNIT_X=%s\n' % self.unitX)
            fileObj.write('UNIT_Y=%s\n' % self.unitY)
            fileObj.write('nEpochs=%d\n' % self.nEpochs)
            fileObj.write('epochLength_s=%d\n' % round(self.epochLength/self.Fs_Hz))
            fileObj.write('blockLength_s=%d\n' % round(self.blockLength/self.Fs_Hz))
            fileObj.write('samplingFreq_Hz=%f\n' % self.Fs_Hz)
            fileObj.write('MxAvg=%f\n' % self.MxAvg)
            fileObj.write('Mx_epochs=%s\n' % np.array_str(self.Mx, max_line_width=1000))
            fileObj.write('=' * 80 + '\n')

    def savePlot(self, fileNamePrefix=None, fileType='png', figDpi=250):
        # fileType: 'png','jpg','tif','pdf','svg','eps','ps'

        # plot Epochs

        fig, axPlots = plt.subplots(1, self.nEpochs, figsize=[8, 2],sharey=True)

        #plot regression
        for i in range(self.nEpochs):
            data = self.linearRegressionData[i]
            ax = axPlots[i]
            Mx=self.Mx[i]
            ax.plot(data['xData'], data['yData'], 'ok', markersize=4)
            ax.plot(data['xData'], data['a'] * data['xData'] +  data['b'], 'r',linewidth=1)
            ax.grid(axis='both')
            ax.set_yticks([])
            ax.set_xticks([])
            #ax.set_title('window')
            #ax.set_xlim([np.amin(tempX), np.amax(tempX)])
            t = ax.text(0.02, 0.05, 'r=%.2f' % Mx, horizontalalignment='left', verticalalignment='bottom', transform=ax.transAxes, fontsize=7)
            t.set_bbox(dict(facecolor='red', alpha=0.3, linewidth=0, pad=0.2))
            t = ax.text(0.98, 0.01, 'ABP' % Mx, horizontalalignment='right', verticalalignment='bottom', transform=ax.transAxes, fontsize=7)
            t.set_bbox(dict(facecolor='gray', alpha=0.3, linewidth=0, pad=0.2))
            t = ax.text(0.02,0.98, 'CBFv' % Mx, horizontalalignment='left', verticalalignment='top', transform=ax.transAxes, fontsize=7,
                    rotation='vertical')
            t.set_bbox(dict(facecolor='gray', alpha=0.3, linewidth=0, pad=0.2))



        #axPlots[0].set_ylabel('Velocity [normalized]', fontsize=8)
        #axPlots[0].set_xlabel('Pressure [normalized]', fontsize=8)
        #ax.legend()
        #ax.set_ylim([np.min(self.), 1.05 * np.nanmax(self.getGain('ALL', coheTreshold=coheTreshold))])

        fig.tight_layout()
        plt.subplots_adjust(wspace = 0.05)

        if fileNamePrefix is not None:
            plt.savefig(fileNamePrefix + '_Epochs' + '.' + fileType, dpi=figDpi, format=fileType, transparent=True)
        else:
            plt.subplot_tool()
            plt.show()

        plt.close()
        # plot Mx

        fig, ax = plt.subplots(1, 1, figsize=[8, 5])

        ax.plot(np.arange(self.nEpochs)+1, self.Mx, 'o--', color='grey',linewidth=1.2,mfc='black', label='Epoch')
        ax.plot([0+1,self.nEpochs], self.MxAvg*np.ones(2), 'r--',linewidth=1.2, label='Average')

        ax.set_ylabel('Mx')
        ax.set_xlabel('Epoch')
        #ax.legend()
        ax.set_xlim([1-0.1, self.nEpochs+0.1])
        # ax.set_ylim([np.min(self.), 1.05 * np.nanmax(self.getGain('ALL', coheTreshold=coheTreshold))])
        ax.grid(axis='both')

        ax.set_xticks(np.arange(self.nEpochs)+1)

        ax.text(1.1, self.MxAvg*1.01, 'average Mx: %.2f ' % self.MxAvg, fontsize=9, horizontalalignment='left')


        fig.tight_layout()
        # plt.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.95, wspace=None, hspace=0.1)

        if fileNamePrefix is not None:
            plt.savefig(fileNamePrefix + '.' + fileType, dpi=figDpi, format=fileType, transparent=True)
        else:
            plt.show()

if __name__ == '__main__':

    if sys.version_info.major == 2:
        sys.stdout.write('Sorry! This program requires Python 3.x\n')
        sys.exit(1)

    file = '../../data/DPOC02CA1.csv'
    data = np.loadtxt(file, skiprows=15 + 1, delimiter=';', usecols=[2, 3, 4])

    ABP = data[:, 2]
    CBFv_L = data[:, 0]
    CBFv_R = data[:, 1]
    samplingFrequency_Hz = 100

    epochLength_s = 10  # in seconds
    blockLength_s = 2  # in seconds

    MxL = meanFlowIdx(ABP, CBFv_L, samplingFrequency_Hz, epochLength_s, blockLength_s,unitX='cm/s', unitY='mmHg')
    MxL.calcMx()
    MxL.save('lixo.txt',sideLabel='L',writeMode='w')
    MxL.savePlot(fileNamePrefix='lixo', fileType='png', figDpi=250)

    print('done!')
