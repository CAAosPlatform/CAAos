import sys
import glob

import numpy as np

from CAAos.core.TFA import PSDestimator
from CAAos.core.TFA import TFA

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

runAll = False

if not runAll:

    file = '../../CARNet_software/tfa_sample_data_1.txt'
    data = np.loadtxt(file, skiprows=1, delimiter='\t')

    time = data[:, 0]
    ABP = data[:, 1]
    CBFv_L = data[:, 2]
    CBFv_R = data[:, 3]
    samplingFrequency_Hz = 1 / np.mean(np.diff(time))

    overlap = 59.99 / 100  # overlap
    segmentLength_s = 102.4
    windowType = 'hann'
    overlap_adjust = True
    if overlap_adjust:
        overlap = TFA.ovelapAdjustment(ABP.shape[0], segmentLength_s * samplingFrequency_Hz, overlap)

    # Power spectrum Estimation
    for side in ['L', 'R']:
        if side == 'L':
            vData = CBFv_L
        if side == 'R':
            vData = CBFv_R
        welch = PSDestimator.PSDestimator(ABP, vData, samplingFrequency_Hz, overlap, segmentLength_s, windowType, detrend=False)
        welch.computeWelch()
        welch.filterAll(filterType='rect', nTaps=2, keepFirst=True)
        # welch.save(fileName='lixo_PSD.txt')
        # Start TF analysis
        TF = TFA.transferFunctionAnalysis(PSDdata=welch)
        TF.computeH1()

        TF.saveStatistics(fileName='lixo_TF_%s_stat.TF' % side, sideLabel=side, coheTreshold=True, remNegPhase=True, writeMode='w')

        # TF.save(fileName='lixo.TF', sideLabel='L', freqRange='ALL')
        if True:
            TF.savePlot(fileNamePrefix=None)
        else:
            TF.savePlot(fileNamePrefix='lixo', fileType='png', figDpi=250, fontSize=6)
            TF.savePlot(fileNamePrefix='lixo', fileType='svg', figDpi=250, fontSize=6)
            TF.savePlot(fileNamePrefix='lixo', fileType='pdf', figDpi=250, fontSize=6)

if runAll:
    with open('../../dataTestesTFA/outputCAAos.txt', 'w') as f:
        for file in sorted(glob.glob('../../dataTestesTFA/*.csv')):
            # file = '../../dataTestesTFA/P11BA1A1.csv'
            datax = np.loadtxt(file, skiprows=8, delimiter=';')
            samplingFreq_Hz = 5

            f.write('%s;' % file)

            time = datax[:, 0]
            ABP = datax[:, 7]
            CBFv_L = datax[:, 1]
            CBFv_R = datax[:, 4]
            samplingFrequency_Hz = 1 / np.mean(np.diff(time))

            overlap = 59.99 / 100  # overlap
            segmentLength_s = 102.4
            windowType = 'hann'
            overlap_adjust = True
            if overlap_adjust:
                overlap = TFA.ovelapAdjustment(ABP.shape[0], segmentLength_s * samplingFrequency_Hz, overlap)

            # Power spectrum Estimation
            for side in ['L', 'R']:
                if side == 'L':
                    vData = CBFv_L
                if side == 'R':
                    vData = CBFv_R
                welch = PSDestimator.PSDestimator(ABP, vData, samplingFrequency_Hz, overlap, segmentLength_s, windowType, detrend=False)
                welch.computeWelch()
                welch.filterAll(filterType='rect', nTaps=2, keepFirst=True)
                # welch.save(fileName='lixo_PSD.txt')
                # Start TF analysis
                TF = TFA.transferFunctionAnalysis(PSDdata=welch)
                TF.computeH1()

                print('Saving TFA statistics...')

                f.write('SIDE=%s;' % side)
                for r in ['VLF', 'LF', 'HF']:
                    [gain_avg, _, _, _] = TF.getGainStatistics(r, coheTreshold=True)
                    [phas_avg, _, _, _] = TF.getPhaseStatistics(r, coheTreshold=True, remNegPhase=True)
                    [cohe_avg, _, _, _] = TF.getCoherenceStatistics(r)

                    f.write('%f;%f;%f;' % (gain_avg, phas_avg, cohe_avg))

            f.write('\n')
