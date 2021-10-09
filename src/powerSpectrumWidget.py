#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

import ARsetup
from customWidgets import signalTabWidget
from spectrumPlotWidget import plotArray, pyQtConf

# dict format:  '#code' : (paramValue,'string name')
windowTypeDict = {0: ('hann', 'Hann'), 1: ('rectangular', 'Rectangular'), 2: ('tukey', 'Tukey'), 3: ('hamming', 'Hamming')}
#filterTypeDict = {0: ('none', 'None'), 1: ('rect', 'Rectangular'), 2: ('triangular', 'Triangular')}
filterTypeDict = { 0: ('triangular', 'Triangular')}


class powerSpectrumWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        self.signalTab = signalPSDTab(['Label', 'Sig. type'], [150, 80], 83)
        hbox.addWidget(self.signalTab)

        for s in self.data.signals:
            self.signalTab.addSignal(channel=s.channel, label=s.label, sigType=s.sigType)

        formLayoutA = QtWidgets.QFormLayout()
        hbox.addLayout(formLayoutA)

        formLayoutB = QtWidgets.QFormLayout()
        hbox.addLayout(formLayoutB)

        # segment Length
        default = 100.0
        segmentLength = QtWidgets.QDoubleSpinBox()
        segmentLength.setRange(10, 200)
        segmentLength.setDecimals(0)
        segmentLength.setSingleStep(1)
        # segmentLength.setFixedWidth(130)
        segmentLength.setValue(default)
        self.segmentLength_s = default
        segmentLength.valueChanged.connect(lambda: self.registerOptions('segmentLength'))

        formLayoutA.addRow('Segment Length (s)', segmentLength)

        # overlap
        default = 50.0
        overlapControl = QtWidgets.QDoubleSpinBox()
        overlapControl.setRange(0, 100)
        overlapControl.setDecimals(0)
        overlapControl.setSingleStep(1)
        # overlapControl.setFixedWidth(130)
        overlapControl.setValue(default)
        self.overlap = default / 100.0
        overlapControl.valueChanged.connect(lambda: self.registerOptions('overlap'))

        formLayoutA.addRow('Segment overlap (%)', overlapControl)

        # welch window
        default = 0  # hann
        self.windowType = windowTypeDict[default][0]
        windowTypeControl = QtWidgets.QComboBox()
        windowTypeControl.addItems([x[1] for x in windowTypeDict.values()])
        windowTypeControl.setCurrentIndex(default)
        windowTypeControl.currentIndexChanged.connect(lambda: self.registerOptions('windowType'))

        formLayoutA.addRow('Segment window type', windowTypeControl)

        # use B2B
        default = True
        self.useB2B = default
        useB2B = QtWidgets.QCheckBox('', self)
        # useB2B.setFixedWidth(30)
        useB2B.setChecked(self.useB2B)
        useB2B.stateChanged.connect(lambda: self.registerOptions('useB2B'))

        formLayoutB.addRow('Use beat-to-beat data', useB2B)

        # detrend
        default = False
        self.detrend = default
        detrend = QtWidgets.QCheckBox('', self)
        detrend.setChecked(self.detrend)
        detrend.stateChanged.connect(lambda: self.registerOptions('detrend'))

        formLayoutB.addRow('Detrend signals', detrend)

        # post processing filter
        default = 0  # triangular
        self.filterType = filterTypeDict[default][0]
        filterTypeControl = QtWidgets.QComboBox()
        filterTypeControl.addItems([x[1] for x in filterTypeDict.values()])
        filterTypeControl.setCurrentIndex(default)
        filterTypeControl.currentIndexChanged.connect(lambda: self.registerOptions('filterType'))

        #formLayoutB.addRow('PSD filter type', filterTypeControl)

        # filter Ntaps
        default = 3
        self.nTapsControl = QtWidgets.QDoubleSpinBox()
        self.nTapsControl.setRange(2, 10)
        self.nTapsControl.setDecimals(0)
        self.nTapsControl.setSingleStep(1)
        # overlapControl.setFixedWidth(130)
        self.nTapsControl.setValue(default)
        self.nTaps = default
        self.nTapsControl.valueChanged.connect(lambda: self.registerOptions('nTaps'))

        #formLayoutB.addRow('Number of taps', self.nTapsControl)

        # PSD button
        self.applyPSDButton = QtWidgets.QPushButton('Compute PSD')
        self.applyPSDButton.setFixedWidth(100)
        self.applyPSDButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.applyPSDButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyPSDButton.clicked.connect(self.applyPSDwelch)
        hbox.addWidget(self.applyPSDButton)

        # Save button
        self.saveButton = QtWidgets.QPushButton('Save PSD data')
        self.saveButton.setFixedWidth(100)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.saveButton.clicked.connect(self.savePSD)
        hbox.addWidget(self.saveButton)

        hbox.addStretch(1)

        # plot area
        self.plotAreaL = plotArray(self.data, side='L', nCols=1)
        vboxL = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel('Left')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont('SansSerif', 18, QtGui.QFont.Bold))
        vboxL.addWidget(text)
        vboxL.addWidget(self.plotAreaL)

        self.plotAreaR = plotArray(self.data, side='R', nCols=1)
        vboxR = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel('Right')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont('SansSerif', 18, QtGui.QFont.Bold))
        vboxR.addWidget(text)
        vboxR.addWidget(self.plotAreaR)

        # layout
        hboxPlot = QtWidgets.QHBoxLayout()
        hboxPlot.setAlignment(QtCore.Qt.AlignTop)
        hboxPlot.addLayout(vboxL)
        hboxPlot.addLayout(vboxR)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hboxPlot)
        self.setLayout(vbox)

    def updateTab(self):
        # left side
        if self.data.hasPSDdata_L:
            self.plotData(side='L')

        # right side
        if self.data.hasPSDdata_R:
            self.plotData(side='R')

        if self.data.hasPSDdata_L or self.data.hasPSDdata_R:
            self.saveButton.setEnabled(True)

    def registerOptions(self, type):
        if type == 'segmentLength':
            self.segmentLength_s = self.sender().value()
        if type == 'overlap':
            self.overlap = self.sender().value() / 100.0
        if type == 'windowType':
            self.windowType = windowTypeDict[self.sender().currentIndex()][0]
        if type == 'useB2B':
            self.useB2B = self.sender().isChecked()
        if type == 'detrend':
            self.detrend = self.sender().isChecked()
        if type == 'filterType':
            self.filterType = filterTypeDict[self.sender().currentIndex()][0]

            if self.filterType.lower() == 'none':
                self.filterType = None
                self.nTapsControl.setEnabled(False)
            else:
                self.nTapsControl.setEnabled(True)

        if type == 'nTaps':
            self.nTaps = self.sender().value()

    # synchronize signals
    def applyPSDwelch(self):

        # fixed as rectangular and Ntap=2 to match matlab code. Here I am filtering with filtfilt, resulting in a trinagular filter with Ntap=3
        self.nTaps=2
        self.filterType='rect'

        self.data.computePSDwelch(self.useB2B, self.overlap, self.segmentLength_s, self.windowType, self.detrend, filterType=self.filterType,
                                  nTapsFilter=self.nTaps)
        self.applyPSDButton.clearFocus()
        self.saveButton.setEnabled(True)

        # left side
        if self.data.hasPSDdata_L:
            self.plotData(side='L')

        # right side
        if self.data.hasPSDdata_R:
            self.plotData(side='R')

    def savePSD(self):
        self.parent().patientData = self.data
        fileExtension = '.psd'

        if self.data.hasPSDdata_L or self.data.hasPSDdata_R:
            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save power spectrum density data as',
                                                                                   self.data.dirName + self.data.filePrefix + fileExtension,
                                                                                   'Power Spectrum Density (.psd) (*.psd);;'
                                                                                   'CSV (.csv) (*.csv);;'
                                                                                   'Numpy (.npy) (*npy);;')
            if resultFileName:
                if '.csv' in selectedFilter:
                    fileFormat = 'csv'
                if '.npy' in selectedFilter:
                    fileFormat = 'numpy'
                if '.psd' in selectedFilter:
                    fileFormat = 'simple_text'

                self.data.savePSD(resultFileName, format=fileFormat, freqRange='ALL', register=True)

    # side:  'L'  or 'R'
    def plotData(self, side='L'):

        # select data
        if side.upper() == 'L':
            plotArea = self.plotAreaL
            PSDdata = self.data.PSD_L
        if side.upper() == 'R':
            plotArea = self.plotAreaR
            PSDdata = self.data.PSD_R

        # create plots
        if len(plotArea.axes) > 0:
            plotArea.replot(plotNbr=0, yData=[PSDdata.Sxx, PSDdata.Syy, abs(PSDdata.Sxy)])
        else:
            plotArea.addNewPlot(
                yData=[[PSDdata.Sxx, pyQtConf['plotColors']['red'], 'Auto ABP'], [PSDdata.Syy, pyQtConf['plotColors']['blue'], 'Auto CBFv'],
                       [abs(PSDdata.Sxy), pyQtConf['plotColors']['base'], 'Cross']], yUnit='Power Spectral Density', logY=True, legend=True)

        [_, _, SxxMin, SxxMax] = PSDdata.freqRangeExtractor.getStatistics(PSDdata.Sxx, freqRange='ALL')
        [_, _, SyyMin, SyyMax] = PSDdata.freqRangeExtractor.getStatistics(PSDdata.Syy, freqRange='ALL')
        [_, _, SxyMin, SxyMax] = PSDdata.freqRangeExtractor.getStatistics(abs(PSDdata.Sxy), freqRange='ALL')

        plotArea.setLimits(xlim=[ARsetup.freqRangeDic['VLF'][0], ARsetup.freqRangeDic['HF'][1]],
                           ylim=[[min(SxxMin, SyyMin, SxyMin), max(SxxMax, SyyMax, SxyMax)]])


class signalPSDTab(signalTabWidget):
    def __init__(self, colLabels, colSizes, colLabelsOffset):
        signalTabWidget.__init__(self, colLabels, colSizes, colLabelsOffset)

    def addSignal(self, channel, label, sigType):
        signal = channelSettings(channel, label, sigType, self.colSizes)
        self.vbox.addWidget(signal)
        self.channels.append(signal)
        self.nChannels = len(self.channels)


class channelSettings(QtWidgets.QWidget):

    def __init__(self, channel, label, sigType, colSizes):
        QtWidgets.QWidget.__init__(self)
        self.channel = channel
        self.label = label
        self.sigType = sigType
        self.colSizes = colSizes
        self.initUI()

    def initUI(self):
        # layout
        hbox0 = QtWidgets.QHBoxLayout()
        hbox0.setAlignment(QtCore.Qt.AlignLeft)
        hbox0.setContentsMargins(0, 0, 0, 0);
        self.setLayout(hbox0)

        # text
        channelSignal = QtWidgets.QLabel('Channel %d' % self.channel)
        channelSignal.setFixedWidth(70)

        # label
        self.labelSignal = QtWidgets.QLabel(self.label)
        self.labelSignal.setFixedWidth(self.colSizes[0])

        # sigType
        self.signalType = QtWidgets.QLabel(str(self.sigType).capitalize())
        self.signalType.setFixedWidth(self.colSizes[1])

        # monta o layout
        hbox0.addWidget(channelSignal)
        hbox0.addWidget(self.labelSignal)
        hbox0.addWidget(self.signalType)

    def updateLabels(self, label, sigType):
        self.label = label
        self.sigType = sigType
        self.labelSignal.setText(self.label)
        self.signalType.setText(str(self.sigType).capitalize())
