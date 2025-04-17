import glob
import sys


import numpy as np
from CAAos.core.ARI import ARI

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

# read data from Panerai

runAll = False

if runAll:
    with open('ARIresults_NEW.txt', 'w') as f:
        for file in glob.glob('../../codigoRenata/arquivosCSV/*.csv'):
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
            myARI = ARI.ARIanalysis(TF, 1.0 / samplingFreq_Hz)
            # print("ARI: %d %f" % ( myARI.ARI_int, myARI.ARI_frac))
            # ARIanalysis.save('temp.ari', sideLabel='L', writeMode='w')
            f.write('%s; %f\n' % (file, myARI.ARI_frac))

            myARI.savePlot(fileNamePrefix='lixo', fileType='png', figDpi=250)
            print('hi')

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
    myARI = ARI.ARIanalysis(TF,
                        1.0 / samplingFreq_Hz)  # print("ARI: %d %f" % (myARI.ARI_int, myARI.ARI_frac))  # ARIanalysis.save('temp.ari', sideLabel='L', writeMode='w')

    print("ARI: %d %f" % ( myARI.ARI_int, myARI.ARI_frac))
