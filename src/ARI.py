#!/bin/python

# -*- coding: utf-8 -*-
import sys
import glob

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)
import numpy as np
import ARsetup
from matplotlib import pyplot as plt
from scipy import fft as scipyFFT


def plot(x1, y1, x2=None, y2=None, xlabel='x', ylabel='y', title=None):
    fig, ax = plt.subplots(figsize=[8, 5])
    ax.plot(x1, y1, linewidth=1, color='r', marker='.')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    if x2 is not None:
        ax.plot(x2, y2, linewidth=1, color='b', marker='.')

    if title is not None:
        ax.set_title(title)

    fig.tight_layout()

    plt.show()


def plota1(F1, title):
    plt.figure()
    plt.suptitle(title)
    plt.plot(F1)
    plt.show()


def plota2(F1, F2, title, ylabel1=None, yLabel2=None):
    fig, axs = plt.subplots(2)
    fig.suptitle(title)
    axs[0].plot(F1)
    if ylabel1 is not None:
        axs[0].set_ylabel(ylabel1)
    axs[1].plot(F2)
    if yLabel2 is not None:
        axs[1].set_ylabel(yLabel2)
    plt.show()


def plotaH(H, title):
    plota2(np.real(H), np.imag(H), title, ylabel1='Real', yLabel2='Imag')

def fadeInFadeOutCosine(signal, width):
    """
    fade-in and fade-out signal with a cossine function of length width
    """
    signalLength = len(signal)
    width = min(int(signalLength / 2), width)

    # ADJUST NW
    for k in range(0, width):
        theta = 2 * np.pi / (2 * width) * k
        W = 0.5 * (1.0 - np.cos(theta))
        signal[k] *= W
        signal[signalLength - 1 - k] *= W
    return signal



def resampleSignal(X, ResampleFctor=1):
    # Resample signal X by linear interpolation by a ResampleFctor
    # Returns signal XBUF with dimension NX*NN
    L=len(X)
    if ResampleFctor == 1:
        xNew = X
    else:
        idx = 0
        xNew = np.zeros(L * ResampleFctor)
        for k in range(1, L):
            X1 = X[k - 1]
            X2 = X[k]
            for j in range(ResampleFctor):
                a = (X2 - X1) / (ResampleFctor - 1)
                b = X1
                xNew[idx] = a * j + b
                idx += 1
    return xNew


class ARIanalysis():
    def __init__(self, transferFunction, samplingPeriod):
        """See notebook 3, page 40 for implementation details"""
        self.TF = transferFunction
        self.Ts = samplingPeriod
        self.Lsignal = len(self.TF)

        self.TF = self.filterTF(self.TF)
        # plotaH(self.TF, 'Ganho e Fase - considerando simetria')
        [self.impulseResponse,self.timeVals] = self.computePatientImpulseResponse()
        self.stepResponse = self.computeStepResponse()
        [self.ARI_int,self.ARI_frac,self.ARIbestFit] = self.calcARI()
        
        self.stepResponse = self.stepResponse[:self.nDuration]
        self.timeVals = self.timeVals[:self.nDuration]

        # plot(self.timeVals[:self.nDuration], self.ARIbestFit, self.timeVals[:self.nDuration],
        #      self.stepResponse[:self.nDuration], xlabel='time(s)', ylabel='step response', title='ARI best fit')

    def filterTF(self, TF):
        """
        Filter input Transfer function, following Panerai's method.
        See notebook, page 40 and 40b

        Brief: breaks spectrum in 5 segments and make a fade-in fade-out using two cossines functions:
        segment   I: H_filtered=0.0
        segment  II: H_filtered=fade in with a cossine, from 0.0 to 1.0
        segment III: H_filtered=H_input
        segment  IV: H_filtered=fade out with a cossine, from 1.0 to 0.0
        segment   V: H_filtered=0.0
        """

        #------------------------------------
        # Panerai's ARI original parameters
        curFreq_FIR_Hz = 0.8  # XSPECTRA's de default value
        nCenter_fadeIn = 0
        nCenter_fadeOut = int(curFreq_FIR_Hz * self.Lsignal * self.Ts)  # verificar frequencia de corte 2
        NW1 = 3  # length of the segment II: L1=2*NW1+1
        NW2 = int(self.Lsignal / 16)  # length of the segment IV: L2=2*NW2+1
        # ------------------------------------

        # -----------------
        # sections I and II:  active only if nCenter_fadeIn>0
        # -----------------
        if nCenter_fadeIn > 0:
            nStart = max(0, int(nCenter_fadeIn - NW1))
            nEnd = int(nCenter_fadeIn + NW1)

            # segment I (zero)
            TF[:nStart] = 0

            # segment II (cossine window)
            for k in range(nStart, nEnd):
                theta = 2 * np.pi / (4 * NW1) * (k - nStart)
                TF[k] *= 0.5 * (1.0 - np.cos(theta))

        # -----------------
        # section III:  H_out=H_in, therefore we do nothing here =)
        # -----------------

        # -----------------
        # section IV and V
        # -----------------
        # Fade out H with a cosine curve at sample NCUT2, with width NW2 = NN / 16
        if nCenter_fadeOut < int(self.Lsignal / 2):  # trecho IV (janela cossenoidal)
            nStart = max(0, int(nCenter_fadeOut - NW2))
            nEnd = min(int(self.Lsignal / 2), int(nCenter_fadeOut + NW2))

            # segment IV (cossine window)
            for k in range(nStart, nEnd):
                theta = 2 * np.pi / (4 * NW2) * (k - nStart)
                TF[k] *= 0.5 * (1.0 + np.cos(theta))

            # segment V (zero)
            TF[nEnd:int(self.Lsignal / 2)] = 0

        # CONSIDER SIMMETRY of H (complex conjugate, reverse order)

        # example N=12

        #      0     1      2      3      4      5      6      7      8      9     10      11
        #   | dc |  f1  |  f2  |  f3  |  f4  |  f5  |  f6  | -f5  | -f4  |  f3  | -f2   | -f1  |
        #     ^                                        ^
        #     |                                        |
        #    DC                                     Nyquist
        #  DC and Nyquist do not repeat!

        TF[int(self.Lsignal / 2)] = 0  # nyquist term do not repeat!
        tempTF = np.conjugate(np.flip(TF[1:int(self.Lsignal / 2)]))  # note I am skipping the 0-th term (DC)
        TF[(int(self.Lsignal / 2)+1):] = tempTF

        return TF

    def computePatientImpulseResponse(self):
        """
        computes the ifft of the frequency response, rotates, fade-in-out
        See notebook, page 40 and 40b
        """

        #------------------------------------
        # Panerai's ARI original parameters
        lengthRotation1 = int(self.Lsignal / 2)  # rotate to the right  -->
        widthFade1 = 20
        self.impulseInstantSample = 64 #  In the end, this will be the sample of t=0, when the impulse happen
        lengthRotation2 = -(int(self.Lsignal / 2) - self.impulseInstantSample)   # rotate to the left    <--

        # lengh of the impulse response in the end
        self.responseLength = 128
        #------------------------------------

        # compute impulse response via fft. forward normalization to keep compatible with old code
        # extracts only real part. imaginary part is just junk
        impulseResponse = np.real(scipyFFT.ifft(self.TF, norm='forward'))

        # plota1(impulseResponse, 'Impulse response')
        # first rotation, half length of the signal to the right, followed by a fade-in-fadeout
        impulseResponse = np.roll(impulseResponse, lengthRotation1)
        impulseResponse = fadeInFadeOutCosine(impulseResponse, width=widthFade1)

        # rotate back to the left, but 64 samples less
        impulseResponse = np.roll(impulseResponse, lengthRotation2)

        # keeps only the first 128 samples.
        impulseResponse = impulseResponse[0:self.responseLength]

        # Time vector
        timeVals = np.arange(len(impulseResponse)) * self.Ts

        # plota1(impulseResponse, 'Impulse response')
        return [impulseResponse,timeVals]

    def computeStepResponse(self):
        """
        See notebook, page 40 and 40b
        """

        #------------------------------------
        # Panerai's ARI original parameters
        self.NsamplesBeforeImpuse=9
        #fade-in fade-out width before time integration
        widthFade = 20
        #------------------------------------

        # fade-in-out signal before time integration
        self.impulseResponse = fadeInFadeOutCosine(self.impulseResponse, width=widthFade)

        # plota1(self.impulseResponse, 'impulse response - cropped')

        # rotates signal to the left  to start at t=0
        nIntegrationStart = self.impulseInstantSample-1
        self.impulseResponse = np.roll(self.impulseResponse, -nIntegrationStart)

        # removes last NsamplesBeforeImpuse samples
        self.impulseResponse = self.impulseResponse[:-self.NsamplesBeforeImpuse]

        # time integration
        stepResponse = np.cumsum(self.impulseResponse) * self.Ts

        # adds NsamplesBeforeImpuse samples=0.0 to the beginning
        stepResponse = np.concatenate([np.zeros(self.NsamplesBeforeImpuse), stepResponse])

        # escala resultado
        stepResponse *= 0.1

        #plota1(stepResponse, 'step response')

        return stepResponse

    def calcARI(self):

        #------------------------------------
        # Panerai's ARI original parameters
        self.nDuration=50 # DURATION OF STEP RESPONSE FOR ARI ESTIMATION. For Ts=0.2s is equivalent to 10s

        if self.nDuration>self.responseLength/2:
            printf('ERROR: nDuration cannot be larger than self.responseLength. Exiting...')
            sys.exit()

        # resampling EXPANSION FACTOR
        if self.nDuration > 100:
            resampleFactor = 1  # DOES NOT EXPAND
        else:
            resampleFactor = 5

        # pressure step
        Pbefore=100.0
        Pafter=101.0
        #------------------------------------

        # create step pressure
        # copy 2x nDuration to have an excess. The excess will be thrown away latter
        VstepResponse=self.stepResponse[:(2*self.nDuration)]
        Pstep = Pafter * np.ones(2*self.nDuration)
        Pstep[:self.NsamplesBeforeImpuse] = Pbefore


        # check if we don't have negative averages in the begining of the signal. In this case end ARI.
        # this criteria was created by Panerai.
        if np.mean(VstepResponse[:int(self.nDuration/2)]) < 0 or np.mean(VstepResponse[:20]) < 0:
            print('Error: Negative CBFv mean. Exiting')
            return [None, None, None]

        [TiecksVresponse,TiecksError] = self.calcTiecksModel(Pstep, VstepResponse, self.nDuration, resampleFactor)

        # Find integer ARI from error
        errorMin = np.amax(TiecksError)
        ARI_int = np.where(TiecksError == errorMin)[0][0]
        print("integer ARI: %d " % ARI_int)

        # fractionary ARI
        ARI_temp = ARI_int
        if ARI_temp == 0:
            ARI_temp = 1
        if ARI_temp == 9:
            ARI_temp = 8

        # fit a parabola
        [c,b,a] = np.polynomial.polynomial.polyfit([ARI_temp - 1, ARI_temp, ARI_temp + 1],
                                                    [TiecksError[ARI_temp - 1], TiecksError[ARI_temp], TiecksError[ARI_temp + 1]], deg=2)

        if a < 0:
            #ARI is the x coordinate of the vertex of the parabola ARI=-b/(2a)
            ARI_frac = -b/(2*a)

            if ARI_frac < 0:
                ARI_frac = 0
            if ARI_frac > 9:
                ARI_frac = 9
        else:
            ARI_frac = ARI_int

        print("fractionary ARI: %f" % ARI_frac)

        # REVERSE EXPANSION BY DECIMATION
        TiecksBestARI_int = TiecksVresponse[ARI_int][resampleFactor * np.array(range(self.nDuration), dtype=int)]

        return [ARI_int,ARI_frac,TiecksBestARI_int]

    def calcTiecksModel(self, Pstep, VstepResponse,nDuration,  resampleFactor):
        # rememeber that Pstep, VstepResponse are 2*nDuration in length

        #------------------------------------
        # Panerai's ARI original parameters
        expAlpha=0.75
        #------------------------------------

        # resample Pnorm and VstepResponse by resampleFactor
        PstepResampled = resampleSignal(Pstep, resampleFactor)
        VstepResponseResampled = resampleSignal(VstepResponse, resampleFactor)

        # eliminates unnecessary elements.
        PstepResampled= PstepResampled[:resampleFactor*nDuration]
        VstepResponseResampled= VstepResponseResampled[:resampleFactor*nDuration]
        FsResampled = resampleFactor * (1.0 / self.Ts)


        # --------------------
        # tiecks model
        # --------------------
        CRCP = 12.0,  # in mmHg
        # normalized pressure
        PmeanControl = Pstep[0]  #average pressure before the step is constant. therefore the average equals the first sample
        Pnorm = (PstepResampled - PmeanControl) / (PmeanControl - CRCP)  # Dp0=0
        nDuration_Resampled = PstepResampled.shape[0]

        #plota2(VstepResponseResampled, Pnorm, title='caoos')

        TiecksVresponse = np.zeros([10, nDuration_Resampled])
        TiecksError = np.zeros(10)
        for ariIdx in range(10):
            x1 = np.zeros(nDuration_Resampled)
            x2 = np.zeros(nDuration_Resampled)

            T = ARsetup.ARIparamDict[ariIdx]['T']
            D = ARsetup.ARIparamDict[ariIdx]['D']
            K = ARsetup.ARIparamDict[ariIdx]['K']

            for k in range(1, nDuration_Resampled):
                x2[k] = x2[k - 1] + (x1[k - 1] - 2.0 * D * x2[k - 1]) / (FsResampled * T)
                x1[k] = x1[k - 1] + (Pnorm[k] - x2[k]) / (FsResampled * T)

            # check and ensure the solution does not explode
            x1[np.abs(x1) > 1e6] = 0.0
            x2[np.abs(x2) > 1e6] = 0.0

            # generate velocity model response
            TiecksVresponse[ariIdx] = abs(np.mean(VstepResponse[:nDuration])) * (1.0 + Pnorm - K * x2)
            TiecksVresponse[ariIdx][0] = TiecksVresponse[ariIdx][4]

            # exponencial moving average
            for k in range(1, nDuration_Resampled):
                TiecksVresponse[ariIdx][k] = expAlpha * TiecksVresponse[ariIdx][k - 1] + (1.0 - expAlpha) * TiecksVresponse[ariIdx][k]

            # normalize tiecks model to fit vResponse amplitude
            lengthWindow = 50 + 10  # 2 seconds + 10 samples  # following Panerai's method
            Vmax = np.amax(VstepResponseResampled[0:lengthWindow])

            if Vmax == 0.0: # panerai's check
                Vmax = 0.001

            idxVmax = np.where(VstepResponseResampled[0:lengthWindow] == Vmax)[0][0]

            xDen = TiecksVresponse[ariIdx][idxVmax] - TiecksVresponse[ariIdx][0]  # following Panerai's method

            if xDen == 0.0: # panerai's check
                xDen = 0.001

            a = (Vmax - VstepResponseResampled[0]) / xDen
            b = Vmax - a * TiecksVresponse[ariIdx][idxVmax]

            TiecksVresponse[ariIdx] = a * TiecksVresponse[ariIdx] + b
            #plota2(VstepResponseResampled, TiecksVresponse[ariIdx], title='caoos')

            # mean square error between vResponse and Vresponse from Tiecks (resampled signals)
            error = np.sqrt(np.square(VstepResponseResampled - TiecksVresponse[ariIdx]).mean())

            # normalized error
            TiecksError[ariIdx] = error / Vmax  # following Panerai's method

            if TiecksError[ariIdx] == 0.0: # panerai's check
                TiecksError[ariIdx] = 0.01

            # invert the error.
            TiecksError[ariIdx] = 1/TiecksError[ariIdx]

        return [TiecksVresponse,TiecksError]

    def save(self, fileName, sideLabel='L', writeMode='w'):

        with open(fileName, writeMode) as fileObj:
            fileObj.write('SIDE=%s\n' % sideLabel)
            fileObj.write('N_POINTS=%d\n' % self.nDuration)
            fileObj.write('ARI_INT_BEST_FIT=%d\n' % self.ARI_int)
            fileObj.write('ARI_FRAC_BEST_FIT=%.3f\n' % self.ARI_frac)
            fileObj.write('SAMPLING_PERIOD_(S)=%s\n' % self.Ts)

            args = dict(max_line_width=np.inf, precision=8, separator=' ', floatmode='maxprec_equal', threshold=np.inf)
            fileObj.write('TIME_(S)=' + np.array2string(self.timeVals, **args) + '\n')
            fileObj.write('STEP_RESPONSE=' + np.array2string(self.stepResponse, **args) + '\n')
            fileObj.write('ARI_BEST_FIT=' + np.array2string(self.ARIbestFit, **args) + '\n')

            fileObj.write('=' * 80 + '\n')

if __name__ == '__main__':
    # read data from Panerai

    runAll = True
    if runAll:
        with open('ARIresults_NEW.txt','w') as f:
            for file in glob.glob('../../codigoRenata/arquivosCSV/*.csv'):
                datax = np.loadtxt(file, skiprows=1, delimiter=',')
                samplingFreq_Hz = 5

                gain = np.array(datax[:, 5])
                phase = np.array(datax[:, 8])

                # Duplicates input. Panerai's code stores only the first half of the spectrum. Since Nyquist is lost. I am copying the pevious value as Nyquist
                gain = np.concatenate([gain, np.array([gain[-1]]), np.flip(gain[1:])])
                phase = np.concatenate([phase, np.array([phase[-1]]), -np.flip(phase[1:])])

                #plota2(gain, phase, 'Ganho e Fase - duplicados', ylabel1='Ganho', yLabel2='Fase')

                # compose transfer function
                angUnit = 'rad'
                if angUnit == 'deg':
                    phase *= np.pi / 180.0;

                # build transfer function from amplitude and phase
                TF = gain * np.exp(1j * phase)

                # run ARI
                myARI = ARIanalysis(TF, 1.0 / samplingFreq_Hz)
                #print("ARI: %d %f" % ( myARI.ARI_int, myARI.ARI_frac))
                #ARIanalysis.save('temp.ari', sideLabel='L', writeMode='w')
                f.write('%s; %f\n' %(file,myARI.ARI_frac))
    else:
        file = '../../codigoRenata/arquivosCSV/VOL05CA1_FR2.csv'
        datax = np.loadtxt(file, skiprows=1, delimiter=',')
        samplingFreq_Hz = 5

        gain = np.array(datax[:, 5])
        phase = np.array(datax[:, 8])

        # Duplicates input. Panerai's code stores only the first half of the spectrum. Since Nyquist is lost. I am copying the pevious value as Nyquist
        gain = np.concatenate([gain, np.array([gain[-1]]), np.flip(gain[1:])])
        phase = np.concatenate([phase, np.array([phase[-1]]), -np.flip(phase[1:])])

        # plota2(gain, phase, 'Ganho e Fase - duplicados', ylabel1='Ganho', yLabel2='Fase')

        # compose transfer function
        angUnit = 'rad'
        if angUnit == 'deg':
            phase *= np.pi / 180.0;

        # build transfer function from amplitude and phase
        TF = gain * np.exp(1j * phase)

        # run ARI
        myARI = ARIanalysis(TF, 1.0 / samplingFreq_Hz)
        #print("ARI: %d %f" % (myARI.ARI_int, myARI.ARI_frac))  # ARIanalysis.save('temp.ari', sideLabel='L', writeMode='w')
