# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 16:15:07 2023

@author:  Renata Romanelli, Jhonnathan Rodrigues
"""
from matplotlib import pyplot as plt
import scipy
import statsmodels.api as sm
import numpy as np
import sys
import ARI


class ARIARMAanalysis(ARI.ARIcore):
    def __init__(self, X, Y, samplingFrequency_Hz, p=2, q=3, unitP=None, unitV=None):
        """
                 P                 Q
        y[n] + \sum a_i y[n-i] = \sum b_i x[n-i]
                i=1               i=1

                Y(z)      b_0 + b_1.z^{-1} + ... + b_Q.z^{-Q}     [ z^M ]     b_0.z^M + b_1.z^{M-1} + ... + b_Q.z^{M-Q}
        H(z) = ------ = --------------------------------------- x [-----] = --------------------------------------------- , where   M=max(P,Q)
                X(z)      1.0 + a_1.z^{-1} + ... + a_P.z^{-P}     [ z^M ]     1.0.z^M + a_1.z^{M-1} + ... + a_P.z^{M-P}

        X: ABP
        Y: CBFv
        p: Autoregresive order
        q: exogenous order
        """
        super().__init__(samplingPeriod=1 / samplingFrequency_Hz, unitP=unitP, unitV=unitV)

        self.X = X  # Ex (exogenous)
        self.Y = Y  # AR (autoregressive).
        self.P = int(p)  # Ordem dos coeficientes AR (autoregressive).
        self.Q = int(q)  # Ordem dos coeficientes Ex (exogenous).
        self.Fs_Hz = samplingFrequency_Hz

        # self.X -=np.mean(self.X)

        self.linearRegression()

        # variables necessary for ARIcore
        self.stepResponse = self.calcStepResponse()
        self.timeVals = np.array(range(len(X))) * self.Ts
        self.responseLength = len(self.timeVals)

        self.calcARI()

        self.stepResponse = self.stepResponse[:self.nDuration]
        self.timeVals = self.timeVals[:self.nDuration]
        self.ABPstep = self.ABPstep[:self.nDuration]

    def linearRegression(self):

        n_start = max(self.P, self.Q)
        if self.P > self.Q:
            nXstart = self.P - self.Q
        else:
            nXstart = 0
        if self.Q > self.P:
            nYstart = self.Q - self.P
        else:
            nYstart = 0

        # build Toeplitz matrices
        # exogenous
        firstRow = np.flip(self.X[nXstart:(nXstart + self.Q + 1)])
        firstCol = self.X[n_start:]

        Xtoeplitz = scipy.linalg.toeplitz(firstCol, firstRow)

        # autoregressive

        firstRow = np.flip(self.Y[nYstart:(nYstart + self.P + 1)])
        firstCol = self.Y[n_start:]

        Ytoeplitz = scipy.linalg.toeplitz(firstCol, firstRow)

        # linear regression
        y_meas = Ytoeplitz[:, 0]
        S = np.hstack((-Ytoeplitz[:, 1:], Xtoeplitz))
        coefs, residual, rankS, singValS = np.linalg.lstsq(S, y_meas)

        self.Xcoefs = np.zeros(max(self.P, self.Q) + 1)  # add one because order N has N+1 coefs.
        self.Ycoefs = np.zeros(max(self.P, self.Q) + 1)  # add one because order N has N+1 coefs.
        self.Ycoefs[0] = 1.0

        self.Ycoefs[1:(self.P + 1)] = coefs[0:(self.P)]
        self.Xcoefs[0:(self.Q+1)] = coefs[self.P:]

        self.ltiSystem = scipy.signal.dlti(self.Xcoefs, self.Ycoefs, dt=1 / self.Fs_Hz)

    def calcStepResponse(self):

        self.ABPstep = 1 * np.ones(len(self.X))  # Criando um Array que deverá ser implementado como step
        self.ABPstep[0:self.NsamplesBeforeImpuse] = 0  # Criando um step de 2 segundos

        t_out, y = scipy.signal.dlsim(self.ltiSystem, self.ABPstep, t=None, x0=None)
        return np.squeeze(y)


if __name__ == '__main__':

    if sys.version_info.major == 2:
        sys.stdout.write('Sorry! This program requires Python 3.x\n')
        sys.exit(1)

    file = '../../codigoARI_ARMA/P17.csv'
    data = np.loadtxt(file, skiprows=1, delimiter=';', max_rows=1399)

    ABP = data[:, 2]
    CBFv_L = data[:, 1]
    CBFv_R = data[:, 3]
    samplingFrequency_Hz = 1 / (data[1, 0] - data[0, 0])

    p = 3
    q = 3

    myARIARMA = ARIARMAanalysis(ABP, CBFv_L, samplingFrequency_Hz, p, q)

    fig, ax = plt.subplots()

    line1, = ax.plot(myARIARMA.timeVals, myARIARMA.stepResponse, label='stepResponse')

    line2, = ax.plot(myARIARMA.timeVals, myARIARMA.ABPstep, label='Pressure')

    plt.show()

    print('done!')
