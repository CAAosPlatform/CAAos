import sys
import time

from CAAos.core import patientMonitoring

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

patient = patientMonitoring.patientMonitoring()
inputPath = '../../data/'  # do not forghet the last /
outputPath = inputPath

patient.newJob( outputFile=outputPath + 'temp_monitoring.exp')

# use the following line to start a real acquisition
patient.startAcquisition(totalTime_sec=30.0, samplingRate_Hz=10.0, patientName="Temp", birthDate="01:01:1900")

# use the following line to start a simulation acquisition
# DO NOT use the simulation mode if you are using MCC1809mockup.py!
#simulationFile='/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.EXP'
#patient.startAcquisitionSimulationMode(simulationFile,totalTime_sec=30.0, samplingRate_Hz=10.0, patientName="Temp", birthDate="01:01:1900")

patient.initSignalUpdateTimer( interval_sec=5,saveToFile=True)

print('oi')

patient.stopAcquisition()
print('oi')

patient.saveSIG(outputPath + 'temp_monitoring.sig', channelList=[0, 1, 2, 3], format='csv', register=False)

if True:

    patient.saveJob(inputPath + 'temp_monitoring.job')

else:
    patient.loadJob(inputPath + 'CG24HG_new.job', 'ARanalysis')

# TFA analysis
patient.computeTFA(estimatorType='H1', register=True)
patient.saveTF(filePath=outputPath + 'lixo.tf', format='csv', freqRange='ALL', register=True)
patient.saveTFAstatistics(filePath=outputPath + 'lixo_stat.tf', plotFileFormat='png', coheTreshold=False, remNegPhase=True, register=True)

# ARI analysis
patient.computeARI(register=True)
patient.saveARI(filePath=outputPath + 'lixo.ari', plotFileFormat=None, format='csv', register=True)

# ARI ARMA analysis

patient.computeARIARMA(useB2B=True, orderP=2, orderQ=2, register=True)
patient.saveARIARMA(filePath=outputPath + 'lixo.ariarma', plotFileFormat=None, format='csv', register=True)

# MX analysis
patient.computeMX(useB2B=True, epochLength_s=60, blockLength_s=10, register=True)
patient.saveMX(filePath=outputPath + 'lixo.mx', plotFileFormat='png', format='simple_text', register=True)

patient.saveJob(fileName=outputPath + 'lixo.job')
patient.saveSIG(outputPath + 'lixo.sig')


print('fim!')