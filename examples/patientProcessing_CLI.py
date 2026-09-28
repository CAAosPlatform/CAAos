import sys

from caaos.core import patientProcessing

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

patient = patientProcessing.patientProcessing()
inputPath = '../../data/'  # do not forget the last /
outputPath = inputPath

# run the analysis from scratch
patient.newJob(inputPath + 'CG24HG.EXP')

patient.setSignalInfo(channel=0, label='ch1', unit='cm/s', sigType='CBFV_L', register=True)
patient.setSignalInfo(channel=1, label='ch2', unit='cm/s', sigType='CBFV_R', register=True)
patient.setSignalInfo(channel=2, label='ch3', unit='mmHg', sigType='ABP', register=True)
patient.setSignalInfo(channel=3, label='ch4', unit=None, sigType='ETCO2', register=True)

# calibration
patient.signals[0].calibrate(100.0,50.0, 'absolute', segmentIndexes=None, register=True)
patient.signals[1].calibrate(100.0,50.0, 'absolute', segmentIndexes=None, register=True)
patient.signals[2].calibrate(80.0,40.0, 'absolute', segmentIndexes=None, register=True)

#synch signals
patient.synchronizeSignals( [], method='fixedAPB', ABPdelay_s=0.9, register=True)

#find RRmarks
patient.findRRmarks(refChannel=2, method='ampd', findPeaks=True, findValleys=False, register=True)

#extract beat-to-beat data
patient.getBeat2beat( resampleRate_Hz=5.0, resampleMethod='cubic', register=True)

patient.setActiveModule('ARanalysis')

# PSD analysis
patient.computePSDwelch(useB2B=True, overlap=0.5, segmentLength_s=100, windowType='hann', detrend=False,
                        filterType='rect', nTapsFilter=2, register=True)
patient.savePSD(filePath=outputPath + 'lixo_psd', format='csv', freqRange='ALL', register=True)

# TFA analysis
patient.computeTFA(estimatorType='H1', register=True)
patient.saveTF(filePath=outputPath + 'lixo_tf.tf', format='csv', freqRange='ALL', register=True)
patient.saveTFAstatistics(filePath=outputPath + 'lixo_stat.tf', plotFileFormat='png', coheTreshold=False,
                          remNegPhase=True, register=True)

# ARI analysis
patient.computeARI(register=True)
patient.saveARI(filePath=outputPath + 'lixo_ari', plotFileFormat=None, format='csv', register=True)

# ARI ARMA analysis

patient.computeARIARMA(useB2B=True, orderP=2, orderQ=2, register=True)
patient.saveARIARMA(filePath=outputPath + 'lixo_ariarma', plotFileFormat=None, format='csv', register=True)

# MX analysis
patient.computeMX(useB2B=True, epochLength_s=60, blockLength_s=10, register=True)
patient.saveMX(filePath=outputPath + 'lixo_mx', plotFileFormat='png', format='simple_text', register=True)

patient.saveJob(fileName=outputPath + 'lixo.job')
patient.saveSIG(outputPath + 'lixo_sig.sig')


#repeat the analysis now using the saved job.

patientB = patientProcessing.patientProcessing()
patientB.loadJob(inputPath + 'lixo.job', 'ARanalysis')

patientB.saveJob(fileName=outputPath + 'lixoB.job')
patientB.saveSIG(outputPath + 'lixoB_sig.sig')