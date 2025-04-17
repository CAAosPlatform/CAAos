import sys

from CAAos.core import patientProcessing

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

patient = patientProcessing.patientProcessing()
inputPath = '../../data/'  # do not foghet the last /
outputPath = inputPath

for i in range(1, 10):
    patient.newJob(inputPath + 'CG24HG.EXP')
    if True:
        patient.newJob( inputPath + 'CG24HG.EXP')
    else:
        patient.loadJob(inputPath + 'CG24HG_new.job', 'ARanalysis')

    patient.setActiveModule('ARanalysis')

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
