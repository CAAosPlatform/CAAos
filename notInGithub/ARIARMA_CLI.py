import sys
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import scipy.signal as signal
from pyqtgraph.parametertree import ParameterSystem

from caaos.core import patientProcessing
from caaos.tools import tools

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

#dir = '../../DadosRicardoNogueira/hipercapnia/'
dir = '../../DadosRicardoNogueira/hipocapnia/'


calcCases = False
calvAverages = True
filterAVG = False
flag_plot_patient= True

infoFile = dir + 'temp_patients_info.txt'

# ARI ARMA Parameters

# ARI ARMA analysis
window_length_s = 30.0
window_shift_s = 0.5  # value in seconds


for window_length_s in [ 30.0]: # value in seconds
    for orderP in [3]:  # usei 2 Autoregresive order (output)
        for orderQ in [1]: # usei 5 exogenous order (input)

            if calcCases:
                fInfo = open(dir + infoFile, 'w')

                for file in sorted(glob.glob(dir + '*.prn')):
                    [dir, baseName, exp] = tools.splitPath(file)

                    patient = patientProcessing.patientProcessing()
                    print('Processing file: ' + file)

                    # run the analysis from scratch
                    patient.newJob(file)

                    fInfo.write('-----------------------\nFILE=%s\n' % file)
                    fInfo.write('Npoints=%d\n' % patient.signals[0].nPoints)
                    fInfo.write('sRate(Hz)=%f\n' % patient.signals[0].samplingRate_Hz)
                    fInfo.write('totalTime(s)=%f\n' % (patient.signals[0].nPoints / patient.signals[0].samplingRate_Hz))

                    # load preprocessing operations or do it manually
                    if False:
                        patient.import_PPO_ARO_Operations('../examples/AR_monitoring.PPO', None, runOperations=True)
                    else:
                        patient.setSignalInfo(channel=0, label='ch1', unit='cm/s', sigType='CBFV_R', register=True)
                        patient.setSignalInfo(channel=1, label='ch2', unit='cm/s', sigType='CBFV_L', register=True)
                        patient.setSignalInfo(channel=2, label='ch3', unit='mmHg', sigType='ABP', register=True)
                        patient.setSignalInfo(channel=3, label='ch4', unit=None, sigType='ETCO2', register=True)

                        # synch signals
                        patient.synchronizeSignals([], method='fixedAPB', ABPdelay_s=0.9, register=True)

                        # calibration
                        patient.signals[0].calibrate(150.0, 20.0, 'percentile', segmentIndexes=None, register=True)
                        patient.signals[1].calibrate(150.0, 20.0, 'percentile', segmentIndexes=None, register=True)
                        patient.signals[2].calibrate(140.0, 90.0, 'percentile', segmentIndexes=None, register=True)

                        # find RRmarks
                        patient.findRRmarks(refChannel=2, method='ampd', findPeaks=True, findValleys=False, register=True)

                        # extract beat-to-beat data
                        B2B_Fs = 5.0;  # B2B sampling frequency in Hz
                        patient.getBeat2beat(resampleRate_Hz=5.0, resampleMethod='cubic', register=True)

                    patient.setActiveModule('ARanalysis')

                    # get total time in the dataset
                    totalTime = patient.signals[0].beat2beatData.getTimeVector()[-1]
                    timeStart_s = 0.0
                    timeEnd_s = timeStart_s + window_length_s

                    fout = open(dir + baseName + '_ARIARMA.csv', 'w')
                    fout.write('time (s);ABP (mmHg);CBF_L (cm/s);CBF_R (cm/s);ARIARMA_L;ARIARMA_R;activity\n')
                    while timeEnd_s <= totalTime:

                        patient.computeARIARMAregularized(useB2B=True, orderP=orderP, orderQ=orderQ, startTime_s=timeStart_s,
                                               endTime_s=timeEnd_s, register=False)

                        # set output time as the middle of the window
                        outputtime = (timeEnd_s+timeStart_s) / 2.0

                        #check if output time is in the basal, exercise or recovery phase
                        # basal: 5th channle is 10
                        # exercise: 5th channel is 50
                        # recovery: 5th channel is 10
                        currTimeIdxB2B=np.argmax(patient.signals[-1].beat2beatData.xData>outputtime)
                        if (patient.signals[-1].beat2beatData.avg[currTimeIdxB2B] > 25):
                            flagExercise = True
                        else:
                            flagExercise = False

                        fout.write('%1.3f;%1.3f;%1.3f;%1.3f;%1.3f;%1.3f;%d\n' % (outputtime, patient.signals[
                            2].beat2beatData.avg[currTimeIdxB2B],
                                                               patient.signals[1].beat2beatData.avg[currTimeIdxB2B],
                                                               patient.signals[0].beat2beatData.avg[currTimeIdxB2B],
                                                               patient.ARIARMA_L.ARI_frac,
                                                               patient.ARIARMA_R.ARI_frac, int(flagExercise)))
                        timeStart_s += window_shift_s
                        timeEnd_s += window_shift_s

                    fout.close()
                fInfo.close()

            if calvAverages:

                # load data
                patientList = []
                for file in sorted(glob.glob(dir + '*ARIARMA.csv')):
                    [dir, baseName, exp] = tools.splitPath(file)
                    data = np.loadtxt(file, delimiter=';', skiprows=1)
                    ariL = data[:, 4]
                    ariR = data[:, 5]
                    Ts = data[1, 0] - data[0, 0]
                    #data[(ariL == -1) | (ariL == 0) | (ariL == 9), 1] = np.nan
                    #data[(ariR == -1) | (ariR == 0) | (ariR == 9), 2] = np.nan
                    data[(ariL == -1), 4] = np.nan
                    data[(ariR == -1), 5] = np.nan
                    patDict={'file':file, 'data':data}
                    patientList.append(patDict)

                if flag_plot_patient:
                    fig, ax = plt.subplots(len(patientList), 2, sharey=True, sharex=True, figsize=(10, 20))

                    for i, pDict in enumerate(patientList):
                        p=pDict['data']
                        time=p[:, 0]
                        ABP=p[:, 1]
                        CBF_L=p[:, 2]
                        CBF_R=p[:, 3]
                        ARI_L=p[:, 4]
                        ARI_R=p[:, 5]
                        activityFlag=p[:, 6]
                        ax[i, 0].plot(time,ARI_L, 'b', label='ARIARMA L')
                        ax[i, 0].text(0, 0, pDict['file'].split('/')[-1], fontsize=8, color='k', verticalalignment='bottom',
                                       horizontalalignment='left')
                        ax[i, 0].set_ylabel('ARIARMA')
                        ax[i, 0].set_ylim(-0.5, 9.5)
                        ax[i, 0].set_xlim(0.0, p[-1,0])
                        ax[i, 0].grid()
                        ax[i, 0].xaxis.set_tick_params(labelbottom=True)

                        ax[i, 1].plot(time, ARI_R, 'r', label='ARIARMA R')
                        ax[i, 1].set_ylim(-0.5, 9.5)
                        ax[i, 1].set_xlim(left=0.0)
                        ax[i, 1].grid()
                        ax[i, 1].xaxis.set_tick_params(labelbottom=True)

                        #add backround to hightlight the exercise phase (yellow)
                        exerciseStartIdx = np.argwhere([activityFlag == 1])[0][-1]
                        exerciseEndtIdx = np.argwhere([activityFlag == 1])[-1][-1]

                        ax[i, 0].axvspan(time[exerciseStartIdx], time[exerciseEndtIdx], color="yellow", alpha=0.3,  zorder=-1)
                        ax[i, 1].axvspan(time[exerciseStartIdx], time[exerciseEndtIdx], color="yellow", alpha=0.3, zorder=-1)

                    ax[-1, 0].set_xlabel('time (s)')
                    ax[-1, 1].set_xlabel('time (s)')
                    ax[0, 0].set_title('Patients ARIARMA L')
                    ax[0, 1].set_title('Patients ARIARMA R')

                    fileName = dir + 'patients_ARI_P%d_Q%d_W%ds.png' % (orderP, orderQ, int(window_length_s))
                    plt.savefig(fileName, dpi=200, bbox_inches='tight')

                # find sampling frequency (assuming all patients have the same sampling frequency)
                Ts = patientList[0]['data'][1, 0] - patientList[0]['data'][0, 0]
                samplingFreq = 1 / Ts

                # set mininum length of the data to be plotted (since some patients have shorter recordings than others)
                Tmin_Inf_s = 50  # in seconds  janela 60s=50
                NpointMin = int(Tmin_Inf_s * samplingFreq)

                # remove patients with short data length
                for p in patientList:
                    if p['data'].shape[0] < NpointMin:
                        patientList.remove(p)

                # compute the median of the lengths
                values = [p['data'].shape[0] for p in patientList]
                values = np.array(values)
                medianL = int(np.median(values))

                # make all patients the same length by copying the last value if shorter or cropping it if longer
                for i, p in enumerate(patientList):
                    if p['data'].shape[0] < medianL:
                        patientList[i]['data']= np.vstack((p['data'], np.tile(p['data'][-1, :], (medianL - p['data'].shape[0], 1))))
                        # fix time columns
                        patientList[i]['data'][:, 0] = np.arange(0, medianL * Ts, Ts) + window_length_s/2
                    elif p['data'].shape[0] > medianL:
                        patientList[i]['data'] = p['data'][:medianL, :]

                # compute averages
                ABP_patients = np.array([p['data'][:, 1] for p in patientList])
                CBF_L = np.array([p['data'][:, 2] for p in patientList])
                CBF_R = np.array([p['data'][:, 3] for p in patientList])
                ARI_patients_L = np.array([p['data'][:, 4] for p in patientList])
                ARI_patients_R = np.array([p['data'][:, 5] for p in patientList])


                avg = np.zeros((medianL, 7))
                avg[:, 0] = patientList[0]['data'][:, 0]   # copy time
                avg[:, 1] = np.nanmean(ABP_patients, axis=0)
                avg[:, 2] = np.nanmean(CBF_L, axis=0)
                avg[:, 3] = np.nanmean(CBF_R, axis=0)
                avg[:, 4] = np.nanmean(ARI_patients_L, axis=0)
                avg[:, 5] = np.nanmean(ARI_patients_R, axis=0)
                avg[:, 6] = patientList[0]['data'][:, -1]  # copy activity

                if filterAVG:
                    a = [1]
                    b = [1, 1, 1]
                    avg[:, 1] = signal.filtfilt(b, a, avg[:, 1])
                    avg[:, 2] = signal.filtfilt(b, a, avg[:, 2])

                fileNamePrefix = dir + 'average_ARI_P%d_Q%d_W%ds' % (orderP, orderQ, int(window_length_s))
                with open(dir + fileNamePrefix + '.csv', 'w') as f:
                    f.write('time (s);ABP (mmHg);CBF_L (cm/s);CBF_R (cm/s);ARIARMA_L;ARIARMA_R;activity\n')
                    np.savetxt(f, avg, delimiter=';', fmt='%1.3f')

                fig, ax = plt.subplots(3, 2, sharex=True, figsize=(10, 4))

                ax[0,0].plot(avg[:, 0], avg[:, 1], 'k', label='ABP')
                ax[1,0].plot(avg[:, 0], avg[:, 2], 'b', label='CBF_L')
                ax[2,0].plot(avg[:, 0], avg[:, 4], 'r', label='ARIARMA L')
                ax[0,0].set_title('average (N=%d) Left  ' % len(patientList))

                ax[0,1].plot(avg[:, 0], avg[:, 1], 'k', label='ABP')
                ax[1,1].plot(avg[:, 0], avg[:, 3], 'b', label='CBF_R')
                ax[2,1].plot(avg[:, 0], avg[:, 5], 'r', label='ARIARMA R')
                ax[0,1].set_title('average (N=%d) Right  ' % len(patientList))

                ax[0,0].set_ylabel('ABP (mmHg)')
                ax[1,0].set_ylabel('CBF (cm/s)')
                ax[2,0].set_ylabel('ARIARMA')
                ax[2,0].set_xlabel('time (s)')
                ax[2,1].set_xlabel('time (s)')
                ax[2,0].set_ylim(-0.5,9.5)

                for i in range(3):
                    for j in range(2):
                        a=ax[i,j]
                        a.axvspan(60, 90, color="yellow", alpha=0.3, zorder=-1)

                        a.set_xlim(0, avg[:, 0].max())
                        a.xaxis.set_major_locator(matplotlib.ticker.IndexLocator(base=10, offset=0))
                        a.grid()



                plt.savefig(dir + fileNamePrefix + '.png', dpi=200, bbox_inches='tight')

                plt.show()

    print('done!')
