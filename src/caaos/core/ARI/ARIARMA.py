# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 16:15:07 2023

@author:  Renata Romanelli, Jhonnathan Rodrigues
"""
import sys

import numpy as np
import scipy
from matplotlib import pyplot as plt
import copy

from caaos.core.ARI import ARI

class ARIARMAanalysis(ARI.ARIcore):
    def __init__(self, X, Y, samplingFrequency_Hz, p=2, q=3, unitP=None, unitV=None):
        """
        runs autoregressive ARI analysis with exogenous input (ARX). Note: ARX is often called ARMA model (
        autoregressive moving average) in dCA literature.

        y: CBFv output
        x: ABP input

                 P                 Q
        y[n] + \sum a_i y[n-i] = \sum b_j x[n-j]
                i=1               j=0

                Y(z)      b_0 + b_1.z^{-1} + ... + b_Q.z^{-Q}     [ z^M ]     b_0.z^M + b_1.z^{M-1} + ... + b_Q.z^{M-Q}
        H(z) = ------ = --------------------------------------- x [-----] = --------------------------------------------- , where   M=max(P,Q)
                X(z)      1.0 + a_1.z^{-1} + ... + a_P.z^{-P}     [ z^M ]     1.0.z^M + a_1.z^{M-1} + ... + a_P.z^{M-P}

        samplingFrequency_Hz: sampling frequency of the signal

        p: Autoregresive order (output)
        q: exogenous order (input)
        """
        super().__init__(samplingPeriod=1 / samplingFrequency_Hz, unitP=unitP, unitV=unitV)

        self.X = copy.deepcopy(X)  # Ex (exogenous)
        self.Y = copy.deepcopy(Y) # AR (autoregressive).
        self.P = int(p)  # Ordem dos coeficientes AR (autoregressive).
        self.Q = int(q)  # Ordem dos coeficientes Ex (exogenous).
        self.Fs_Hz = samplingFrequency_Hz

        if True:
            #fig, axs = plt.subplots(2,1)
            #axs[0].plot(self.X,'b')
            #axs[1].plot(self.Y,'b')
            #detrend signals before as recommended by Kyriaki Kostoglou, 2023 white pape
            scipy.signal.detrend(self.X,overwrite_data=True)
            scipy.signal.detrend(self.Y,overwrite_data=True)
            #axs[0].plot(self.X,'r')
            #axs[1].plot(self.Y,'r')
            #plt.show()

        self.linearRegression()

        # variables necessary for ARIcore
        self.stepResponse = self.calcStepResponse()
        self.timeVals = np.array(range(len(self.X))) * self.Ts
        self.responseLength = len(self.timeVals)

        self.calcARI(duration_s=10.0)

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

        Ytoeplitz = scipy.linalg.toeplitz(firstCol, firstRow) # the first column is the measured output, and will be
        # removed from the regression matrix S, so that the regression is done with respect to the measured output.

        # linear regression
        y_meas = Ytoeplitz[:, 0]
        Ytoeplitz = Ytoeplitz[:, 1:]  # remove the first column, which is the measured output, from the regression matrix S
        S = np.hstack((-Ytoeplitz, Xtoeplitz))

        if np.linalg.cond(S)>1e4:
            print('The matrix is ill-conditioned. condition number: %f' % np.linalg.cond(S))

        coefs, residual, rankS, singValS = np.linalg.lstsq(S, y_meas,rcond=None)

        self.coefsRaw=coefs

        self.Xcoefs = np.zeros(max(self.P, self.Q) + 1)  # add one because order N has N+1 coefs.
        self.Ycoefs = np.zeros(max(self.P, self.Q) + 1)  # add one because order N has N+1 coefs.
        self.Ycoefs[0] = 1.0

        self.Ycoefs[1:(self.P + 1)] = coefs[0:(self.P)]
        self.Xcoefs[0:(self.Q + 1)] = coefs[self.P:]

        self.ltiSystem = scipy.signal.dlti(self.Xcoefs, self.Ycoefs, dt=1 / self.Fs_Hz)

        #print('zeros:', self.ltiSystem.zeros)
        #print('poles:', self.ltiSystem.poles)

        fixStability = True
        if fixStability:
            #print('Fixing stability of the system by moving poles outside the unit circle to inside the unit circle.')
            #fix the poles to be inside the unit circle, as required for stability of discrete-time systems
            # Convert to ZerosPolesGain format
            sys_zpk = self.ltiSystem.to_zpk()

            poles = sys_zpk.poles
            for i,p in enumerate(poles):
                if abs(p) >= 1:
                    print('Pole outside unit circle: %f + %fj' % (p.real, p.imag))
                    poles[i] = 0.99 * p / abs(p)


            zeros = sys_zpk.zeros
            #zeros = np.array([z if abs(z) < 1 else 0.99 * z / abs(z) for z in sys_zpk.zeros])
            gain = sys_zpk.gain

            #print("zeros:", zeros)
            #print("poles:", poles)
            #print("gain:", gain)

            self.ltiSystem = scipy.signal.dlti(zeros, poles, gain, dt=1 / self.Fs_Hz)

            if False:
                t, y = scipy.signal.dimpulse(self.ltiSystem, n=len(self.X))

                fig0, ax0 = plt.subplots()
                ax0.step(t, np.squeeze(y), '.-', where='post')
                ax0.set_title("Impulse Response")
                ax0.set(xlabel='Sample number', ylabel='Amplitude')
                ax0.grid()
                plt.show()
                print('oi')


    def calcStepResponse(self):

        self.ABPstep = 1 * np.ones(len(self.X))  # Criando um Array que deverá ser implementado como step
        self.ABPstep[0:self.NsamplesBeforeImpuse] = 0  # Criando um step de 2 segundos

        t_out, y = scipy.signal.dlsim(self.ltiSystem, self.ABPstep, t=None, x0=None)
        y = np.squeeze(y)
        if False:
            plt.plot(t_out, y)
            plt.show()
        return y

class ARIARMAanalysisRegularized(ARIARMAanalysis):
    def __init__(self, X, Y, samplingFrequency_Hz, p=2, q=3, unitP=None, unitV=None, regParam=0.01,
                 referenceLTIvec=None):

        self.regParam=regParam
        self.referenceLTIvec=referenceLTIvec

        super().__init__(X, Y, samplingFrequency_Hz, p, q, unitP=None, unitV=None)


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

        Ytoeplitz = scipy.linalg.toeplitz(firstCol, firstRow) # the first column is the measured output, and will be
        # removed from the regression matrix S, so that the regression is done with respect to the measured output.

        # linear regression
        y_meas = Ytoeplitz[:, 0]
        Ytoeplitz = Ytoeplitz[:, 1:]  # remove the first column, which is the measured output, from the regression matrix S
        S = np.hstack((-Ytoeplitz, Xtoeplitz))

        if np.linalg.cond(S)>1e4:
            print('The matrix is ill-conditioned. condition number: %f' % np.linalg.cond(S))

        #Tikhonov regularization :   IE = ||Sx-y||^2 + alpha*||L(x-x^*)||^2
        if self.referenceLTIvec is not None:
            # regularization matrix
            L = np.eye(S.shape[1])
            # regularization vector
            b = self.referenceLTIvec
            # augmented system
            S_augmented = np.vstack((S, np.sqrt(self.regParam) * L))
            y_augmented = np.concatenate((y_meas, np.sqrt(self.regParam) * L @ b))
            coefs, residual, rankS, singValS = np.linalg.lstsq(S_augmented, y_augmented,rcond=None)
        else:
            coefs, residual, rankS, singValS = np.linalg.lstsq(S, y_meas,rcond=None)

        self.coefsRaw=coefs

        self.Xcoefs = np.zeros(max(self.P, self.Q) + 1)  # add one because order N has N+1 coefs.
        self.Ycoefs = np.zeros(max(self.P, self.Q) + 1)  # add one because order N has N+1 coefs.
        self.Ycoefs[0] = 1.0

        self.Ycoefs[1:(self.P + 1)] = coefs[0:(self.P)]
        self.Xcoefs[0:(self.Q + 1)] = coefs[self.P:]

        self.ltiSystem = scipy.signal.dlti(self.Xcoefs, self.Ycoefs, dt=1 / self.Fs_Hz)

        #print('zeros:', self.ltiSystem.zeros)
        #print('poles:', self.ltiSystem.poles)

        fixStability = True
        if fixStability:
            #print('Fixing stability of the system by moving poles outside the unit circle to inside the unit circle.')
            #fix the poles to be inside the unit circle, as required for stability of discrete-time systems
            # Convert to ZerosPolesGain format
            sys_zpk = self.ltiSystem.to_zpk()

            poles = sys_zpk.poles
            for i,p in enumerate(poles):
                if abs(p) >= 1:
                    print('Pole outside unit circle: %f + %fj' % (p.real, p.imag))
                    poles[i] = 0.99 * p / abs(p)


            zeros = sys_zpk.zeros
            #zeros = np.array([z if abs(z) < 1 else 0.99 * z / abs(z) for z in sys_zpk.zeros])
            gain = sys_zpk.gain

            #print("zeros:", zeros)
            #print("poles:", poles)
            #print("gain:", gain)

            self.ltiSystem = scipy.signal.dlti(zeros, poles, gain, dt=1 / self.Fs_Hz)

            if False:
                t, y = scipy.signal.dimpulse(self.ltiSystem, n=len(self.X))

                fig0, ax0 = plt.subplots()
                ax0.step(t, np.squeeze(y), '.-', where='post')
                ax0.set_title("Impulse Response")
                ax0.set(xlabel='Sample number', ylabel='Amplitude')
                ax0.grid()
                plt.show()
                print('oi')

