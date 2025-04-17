import sys

from matplotlib import pyplot as plt
import numpy as np

from CAAos.core.ARI import ARIARMA

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

myARIARMA = ARIARMA.ARIARMAanalysis(ABP, CBFv_L, samplingFrequency_Hz, p, q)

fig, ax = plt.subplots()

line1, = ax.plot(myARIARMA.timeVals, myARIARMA.stepResponse, label='stepResponse')

line2, = ax.plot(myARIARMA.timeVals, myARIARMA.ABPstep, label='Pressure')

plt.show()

print('done!')
