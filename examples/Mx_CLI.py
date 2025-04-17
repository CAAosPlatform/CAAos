import sys

from CAAos.core.Mx import Mx
import numpy as np

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

file = '../../data/CG24HG.csv'
data = np.loadtxt(file, skiprows=3 + 1, delimiter=';', usecols=[1, 2, 3])

ABP = data[:, 2]
CBFv_L = data[:, 0]
CBFv_R = data[:, 1]
samplingFrequency_Hz = 100

epochLength_s = 10  # in seconds
blockLength_s = 2  # in seconds

MxL = Mx.meanFlowIdx(ABP, CBFv_L, samplingFrequency_Hz, epochLength_s, blockLength_s, unitX='cm/s', unitY='mmHg')
MxL.calcMx()
MxL.save('lixo.txt', sideLabel='L', writeMode='w')
MxL.savePlot(fileNamePrefix='lixo', fileType='png', figDpi=250)

print('done!')
