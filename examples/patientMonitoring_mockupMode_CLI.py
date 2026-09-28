import sys
import time

from caaos.core import patientMonitoring

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

patient = patientMonitoring.patientMonitoring()
inputPath = '../../data/'  # do not forghet the last /
outputPath = inputPath

patient.newJob(outputFile=outputPath + 'temp_monitoring.exp')

# total time of acquisition in seconds
totalTime_s = 120.0

# time to fill initial buffer in seconds before procecing data
initialBufferTime_s = 0

# use the following line to start acquisition
patient.startAcquisition(totalTime_sec=totalTime_s, samplingRate_Hz=100.0, initialBufferTime_sec=initialBufferTime_s,
                         mockupAcquisition=True, mockupInputEXPfile=inputPath + 'CG24HG.EXP')
# wait a few seconds to collect data.

# wait 30 seconds to allow the acquisition to start and the first data to be collected this is needed to avoid
# problems with the first signal update, which is called in the next line, specially for ARI.
# print('collecting data to fill part of the FIFO buffer for proper PSD calculations...')
# tools.timed_wait(30, update_interval=5)

# length of the FIFO bufffer. this is the length of the data used for the calculations
FIFOlengh_s = 15.0
# time interval between signal updates in seconds
interval_sec = 5.0

# set update signal update timer. This will update the signal display every interval_sec seconds and save new data to file if saveToFile=True
patient.initSignalUpdateTimer(interval_sec=interval_sec, FIFOlength_s=FIFOlengh_s, applyOperations=True,
                              saveToFile=True)

time.sleep(totalTime_s * 1.1)
print('data collected')

patient.stopAcquisition()

patient.saveJob(inputPath + 'temp_monitoring.job')
