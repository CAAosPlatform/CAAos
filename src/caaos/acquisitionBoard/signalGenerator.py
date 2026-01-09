from __future__ import print_function

import numpy as np


# -*- coding: utf-8 -*-

class signalGenerator():
    def __init__(self, nChannels=1, length=100, samplingFrequency=100.0):
        self.nChannels = nChannels
        self.length = length
        self.samplingFrequency = samplingFrequency
        self.samples = np.arange(0, self.length)
        self.times = self.samples / self.samplingFrequency
        self.data = np.zeros([self.nChannels, self.length])

    def sin(self, channelList=[0], amplitude=1.0, frequency=1.0, offset=0.0, phase_rad=0.0):
        for ch in channelList:
            self.data[ch, :] = amplitude * np.sin(2.0 * np.pi * frequency * self.times + phase_rad) + offset

    def cos(self, channelList=[0], amplitude=1.0, frequency=1.0, offset=0.0, phase_rad=0.0):
        for ch in channelList:
            self.data[ch] = amplitude * np.cos(2.0 * np.pi * frequency * self.times + phase_rad) + offset
