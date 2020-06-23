#!/bin/python

# -*- coding: utf-8 -*-
import sys

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)
import numpy as np
import ARsetup
import math
from scipy import signal as scipySignal
from matplotlib import pyplot as plt
from scipy import fftpack as scipyFFTpack


def plot(x1, y1, x2=None, y2=None, xlabel='x', ylabel='y', title=None):
    fig, ax = plt.subplots(figsize=[8, 5])
    ax.plot(x1, y1, linewidth=1, color='r', marker='.')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    if x2 is not None:
        ax.hold(True)
        ax.plot(x2, y2, linewidth=1, color='b', marker='.')

    if title is not None:
        ax.set_title(title)

    fig.tight_layout()

    plt.show()


def testeFFT_IFFT():
    T = 0.33333;
    Ts = 0.01;
    N = 300
    x = np.arange(N) * Ts
    y = 2 * np.cos(2 * 3.1415 * x / T);
    plot(x, y)

    Y = scipyFFTpack.fft(y)
    f0 = (1 / Ts) / N
    freqVals = np.arange(N) * f0

    plot(freqVals, np.abs(Y))

    y1 = scipyFFTpack.ifft(Y)
    t1 = np.arange(N) * Ts

    plot(t1, y1)


class ARIanalysis():
    def __init__(self, transferFunction, samplingPeriod):
        self.TF = transferFunction
        self.Ts = samplingPeriod

    def computePatientImpulseResponse(self, Tresponse=20.0):

        self.impulseResponse = np.real(scipyFFTpack.ifft(self.TF))  # extracts only real part. imaginary part is just junk

        # Time vector
        self.timeVals = np.arange(self.TF.shape[0]) * self.Ts

        if Tresponse is not None and Tresponse > 0:
            idx = self.timeVals <= Tresponse
            self.timeVals = self.timeVals[idx]
            self.impulseResponse = self.impulseResponse[idx]

        self.Tresponse = self.timeVals[-1]
        self.nPoints = len(self.timeVals)

        if True:  # Gaussian lowpass filter
            nTaps = 5  # use odd number
            std_samples = 2
            GaussianWindow = scipySignal.gaussian(nTaps, std_samples)

            # normalizes Gaussian Window
            b = GaussianWindow / np.linalg.norm(GaussianWindow)
            a = [1]
            self.impulseResponse = scipySignal.filtfilt(b, a, self.impulseResponse)

        if False:
            order = 5
            fNyquist = 1.0 / (2.0 * self.Ts)
            fc_Hz = 0.5;  # in Hertz
            wc_norm = fc_Hz / fNyquist  # must be normalized from 0 to 1, where 1 is the Nyquist frequency
            [b, a] = scipySignal.butter(N=order, Wn=wc_norm, btype='low', analog=False, output='ba')
            self.impulseResponse = scipySignal.filtfilt(b, a, self.impulseResponse)

        # plot(self.timeVals,self.impulseResponse,xlabel='Time (s)',ylabel='Impulse response (cm/s)')

    def computeARI(self):
        numARI = 10
        normSQerror = np.zeros(numARI)

        for ARIidx in range(numARI):
            t, tiecksVals = self.tiecksModel(ARIidx, fs=1 / self.Ts,  # in Hz
                                             Tresponse=self.Tresponse,  # in seconds
                                             Tcontrol=0.0,  # in seconds
                                             CBFcontrol=100.0,  # in cm/s
                                             ABPcontrol=120.0,  # in mmHg
                                             ABPcrit=12.0,  # in mmHg
                                             iputType='IMPULSE', stepSize=-10,  # in mmHg
                                             impulseIntensity=10,  # in mmHg
                                             normalizeResponse=True)

            tiecksVals = self.adjustTieksModel(tiecksVals)

            # plot(t,tiecksVals,t,self.impulseResponse,title='ARI: %d' % ARIidx)

            SQerror = self.impulseResponse - tiecksVals
            normSQerror[ARIidx] = np.linalg.norm(SQerror)

        # find ARI idx of the best fit
        self.ARIidx = np.argmin(normSQerror)
        print(normSQerror)
        print('ARI best Fit: %d ' % self.ARIidx)

        _, self.ARIbestFit = self.tiecksModel(self.ARIidx, fs=1 / self.Ts,  # in Hz
                                              Tresponse=self.Tresponse,  # in seconds
                                              Tcontrol=0.0,  # in seconds
                                              CBFcontrol=100.0,  # in cm/s
                                              ABPcontrol=120.0,  # in mmHg
                                              ABPcrit=12.0,  # in mmHg
                                              iputType='IMPULSE', stepSize=-10,  # in mmHg
                                              impulseIntensity=10,  # in mmHg
                                              normalizeResponse=True)

        self.ARIbestFit = self.adjustTieksModel(self.ARIbestFit).reshape(1, -1)[0]

    # iputType:  'STEP'  'IMPULSE'
    def tiecksModel(self, ARIindex,  # 0 to 9
                    fs=50.0,  # in Hz
                    Tresponse=15.0,  # in seconds
                    Tcontrol=0.0,  # in seconds
                    CBFcontrol=100.0,  # in cm/s
                    ABPcontrol=120.0,  # in mmHg
                    ABPcrit=12.0,  # in mmHg
                    iputType='STEP', stepSize=-10,  # in mmHg
                    impulseIntensity=-10,  # in mmHg
                    normalizeResponse=False):

        if iputType.upper() == 'STEP':
            P = np.concatenate((ABPcontrol * np.ones(int(Tcontrol * fs)), (ABPcontrol + stepSize) * np.ones(int(Tresponse * fs) + 1))).reshape(-1, 1);
        if iputType.upper() == 'IMPULSE':
            P = ABPcontrol + (impulseIntensity * fs) * scipySignal.unit_impulse(int(fs * Tresponse) + 1, int(Tcontrol * fs)).reshape(-1, 1);

        dP = (P - ABPcontrol) / (ABPcontrol - ABPcrit)

        T = ARsetup.ARIparamDict[ARIindex]['T']
        D = ARsetup.ARIparamDict[ARIindex]['D']
        K = ARsetup.ARIparamDict[ARIindex]['K']

        Ad = np.array([[1.0, -1.0 / (fs * T)], [1.0 / (fs * T), 1.0 - 2.0 * D / (fs * T)]])
        Bd = np.array([[1.0 / (fs * T)], [0.0]])
        Cd = np.array([0.0, -K])
        Dd = np.array([1])

        sys = scipySignal.StateSpace(Ad, Bd, Cd, Dd, dt=1 / fs)

        dP0 = (ABPcontrol - ABPcontrol) / (ABPcontrol - ABPcrit)  # Dp0=0
        x0 = np.array([2 * D * dP0, dP0])
        t_out, y_out, x_out = scipySignal.dlsim(sys, u=dP, x0=x0)

        # replace initial value by  y_new[0]= y[0]-Delta_2_1
        delta = y_out[2] - y_out[1]
        y_out[0] = y_out[1] - delta

        V = CBFcontrol * (1.0 + y_out)

        if normalizeResponse:
            minV = np.amin(V)
            maxV = np.amax(V)
            if maxV > minV:
                V = (V - minV) / (maxV - minV)
            else:
                V = 0 * V

        return [t_out, V]  # removes the first point

    def adjustTieksModel(self, tiecksSignal):

        startSample = int(math.ceil(1 * (1.0 / self.Ts)))
        # define time range considered in the LMS
        finalTime = 6  # value in seconds

        if finalTime < self.Tresponse:
            finalSample = int(finalTime / self.Ts)
        else:
            finalSample = -1

        E = np.column_stack((tiecksSignal[startSample:finalSample], np.ones(self.impulseResponse[startSample:finalSample].shape)))
        param = np.linalg.pinv(E).dot(self.impulseResponse[startSample:finalSample])

        newSignal = tiecksSignal * param[0] + param[1]
        return newSignal

    def save(self, fileName, sideLabel='L', writeMode='w'):

        with open(fileName, writeMode) as fileObj:
            fileObj.write('SIDE=%s\n' % sideLabel)
            fileObj.write('RESPONSE_TIME_(S)=%s\n' % self.Tresponse)
            fileObj.write('ARI_BEST_FIT=%d\n' % self.ARIidx)
            fileObj.write('NPOINTS=%d\n' % self.nPoints)

            args = dict(max_line_width=np.inf, precision=8, separator=' ', floatmode='maxprec_equal', threshold=np.inf)
            fileObj.write('TIME_(S)=' + np.array2string(self.timeVals, **args) + '\n')
            fileObj.write('IMPULSE_RESPONSE=' + np.array2string(self.impulseResponse, **args) + '\n')
            fileObj.write('ARI_BEST_FIT_SIGNAL=' + np.array2string(self.ARIbestFit, **args) + '\n')

            fileObj.write('=' * 80 + '\n')


if __name__ == '__main__':

    TF = np.loadtxt('../codigoPedro/ARIpedro/lixo_TF_L.txt').view(complex)
    samplingFreq_Hz = 4

    ARI = ARIanalysis(TF, 1.0 / samplingFreq_Hz)

    ARI.computePatientImpulseResponse(Tresponse=10.0)
    ARI.computeARI()
    print(ARI.ARIidx)

    # for i in range(10):
    # [t,V] = ARI.tiecksModel(i,iputType='STEP',stepSize=-10,impulseIntensity=-110)
    # plot(t,V)
    # np.savetxt('%d.txt'%i,V)

    [t, V] = ARI.tiecksModel(7, iputType='STEP', stepSize=-10, impulseIntensity=-10)

    # [t,V] = ARI.tiecksModel(7,iputType='STEP',stepSize=-10,impulseIntensity=-10))  # plot(t,V,'Time (s)','Velocity (cm/s)')
