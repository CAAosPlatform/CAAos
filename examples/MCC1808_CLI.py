import sys
import time

import numpy as np
from matplotlib import pyplot as plt

from CAAos.acquisitionBoard.MCC1808 import MCC1808
from CAAos.acquisitionBoard.signalGenerator import signalGenerator

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

myDAQ = MCC1808()

simulateAcquisition = False

# ------------------------------------------
# analog input configuration
# ------------------------------------------

if simulateAcquisition:
    channels = [4, 5, 6, 7]
else:
    channels = [4, 5, 6, 7]

nChannels = len(channels)
AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(nChannels)]
sampleRate = 100.0  # value in Hz
if True:
    print('DEBUG Analog Read')
    nSamples = 1000
else:
    totalTime_min = 5.0
    nSamples = int(totalTime_min * 60 * sampleRate)

myDAQ.AiDevice.confChannelQueue(AinConf, sampleRate, nSamples)

# ------------------------------------------
# analog output configuration
# ------------------------------------------

if simulateAcquisition:
    nChannels = 2
    fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.EXP'
    data, sampleRate = myDAQ.AoDevice.loadDataFrom_EXP(fileName, channels=[0, 2])

    data = myDAQ.AoDevice.normalizeData(data, maxV=9.0)

    np.save('data_input.npy', data)

else:
    nChannels = 2
    sampleRate = 100.0  # value in Hz
    nSamples = 100
    mysignalGenerator = signalGenerator(nChannels=nChannels, length=nSamples, samplingFrequency=sampleRate)

    if nChannels == 1:
        mysignalGenerator.sin(channelList=[0], amplitude=1.0, frequency=10.0, offset=0.0, phase_rad=0.0)

    if nChannels == 2:
        mysignalGenerator.sin(channelList=[0], amplitude=1.0, frequency=1.0, offset=0.0, phase_rad=0.0)
        mysignalGenerator.sin(channelList=[1], amplitude=1.0, frequency=1.0, offset=0.0, phase_rad=0.0)

    data = mysignalGenerator.data

    # plt.plot(mysignalGenerator.times,mysignalGenerator.data.T)  # plt.show()

myDAQ.AoDevice.confChannelScan(signals=data, sampleRate=sampleRate, continuous=True, zeroEnd=True)

# ------------------------------------------
# start read/write
# ------------------------------------------

# read data
myDAQ.AiDevice.readData(flagWait=False)
# time.sleep(2.0)  # in seconds
# write data
myDAQ.AoDevice.writeData(flagWait=False)
# time.sleep(2.0)  # in seconds
# myDAQ.AoDevice.stopWrite()

cont = 0
while myDAQ.AiDevice.getstatus()[0] == 1:  # or myDAQ.AoDevice.getstatus()[0] == 1:
    Ai_currentScanSample = myDAQ.AiDevice.getstatus()[1]
    Ao_currentScanSample = myDAQ.AoDevice.getstatus()[1]
    print('Analog in sample: %d' % Ai_currentScanSample)
    print('Analog out sample: %d' % Ao_currentScanSample)
    time.sleep(2.0)  # in seconds

    np.save('data_%d.npy' % cont, myDAQ.AiDevice.dataArrayNP)
    cont += 1

# acquired data
data = myDAQ.AiDevice.dataArrayNP

plt.plot(data.T)
plt.grid()

plt.show()

myDAQ.disconnect()

print('done!')
