import sys
import time

import numpy as np
from matplotlib import pyplot as plt

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

acquisitionMode = 'normal' # valid options:  normal, signal_generator, simulate_from_file, mockup
"""
 - 'normal': Normal mode
   Used channels: Ain0, Ain1, Ain2, Ain3
   No simulated data is passed to the analog input device. If nothing is connected to the analog input channels,
   the read values will be random noise.
 - 'signal_generator': Simulate acquisition mode
   Used channels: Ain4, Ain5, Ain6, Ain7
   Sinusoidal signals are generated in the analog output channels Aout0 and Aout1 and the analog input
   channels read these signals. This way we can check if the acquisition is working properly.
   Aout0 is sent to Ain0 and Ain1 and Aout1 is sent to Ain2 and Ain3.  
 - 'simulate_from_file': Simulate from file mode
   Used channels: Ain4, Ain5, Ain6, Ain7
    Simulated data is read from a file and sent to the analog output channels Aout0 and Aout1 and the analog input
   channels read these signals. This way we can check if the acquisition is working properly. 
   Aout0 is sent to Ain0 and Ain1 and Aout1 is sent to Ain2 and Ain3.  
 - 'mockup' mode:
    Used channels: Ain0, Ain1, Ain2, Ain3
    This mode uses the MCC1808_mockup.py module, which simulates the behavior of the MCC1808 board.
    Data is loaded from a file and sent to the output array. This mode does not use the physical board.
    You don't need to connect anything to the computer.
"""


if acquisitionMode.lower() in ['signal_generator', 'simulate_from_file']:
    channels = [4, 5, 6, 7]
if acquisitionMode.lower() in ['normal', 'mockup']:
    channels = [0,1,2,3]

if acquisitionMode.lower() == 'mockup':
    from caaos.acquisitionBoard.MCC1808_mockup import MCC1808
else:
    from caaos.acquisitionBoard.MCC1808 import MCC1808

if acquisitionMode.lower() == 'signal_generator':
    from caaos.acquisitionBoard.signalGenerator import signalGenerator

myDAQ = MCC1808()

if acquisitionMode.lower() == 'mockup':
    inputEXPfile = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.EXP'
    myDAQ.setInputEXPfile(inputEXPfile)

# ------------------------------------------
# analog input configuration
# ------------------------------------------

nChannels = len(channels)
AinConf = [{'channel': channels[i], 'inputMode': 'SE', 'range': 'BIP10VOLTS'} for i in range(nChannels)]
sampleRate = 100.0  # value in Hz
if True:
    nSamples = 1000
else:
    totalTime_min = 5.0
    nSamples = int(totalTime_min * 60 * sampleRate)


print('Acquisition mode: %s' % acquisitionMode)

myDAQ.AiDevice.confChannelQueue(AinConf, sampleRate, nSamples)

# ------------------------------------------
# analog output configuration
# ------------------------------------------

if acquisitionMode.lower() == 'simulate_from_file':
    nChannels = 2
    fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.EXP'
    data, sampleRate = myDAQ.AoDevice.loadDataFrom_EXP(fileName, channels=[0, 2])
    data = myDAQ.AoDevice.normalizeData(data, maxV=9.0)
    np.save('data_input.npy', data)

    # plt.plot(mysignalGenerator.times,mysignalGenerator.data.T)  # plt.show()
    myDAQ.AoDevice.confChannelScan(signals=data, sampleRate=sampleRate, continuous=True, zeroEnd=True)

if acquisitionMode.lower() == 'signal_generator':
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
if acquisitionMode.lower() in ['signal_generator', 'simulate_from_file']:
    myDAQ.AoDevice.writeData(flagWait=False)
    # time.sleep(2.0)  # in seconds
    # myDAQ.AoDevice.stopWrite()

cont = 0
while myDAQ.AiDevice.getstatus()[0] == 1:  # or myDAQ.AoDevice.getstatus()[0] == 1:
    Ai_currentScanSample = myDAQ.AiDevice.getstatus()[1]
    print('Analog in sample: %d' % Ai_currentScanSample)
    Ao_currentScanSample = myDAQ.AoDevice.getstatus()[1]
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
