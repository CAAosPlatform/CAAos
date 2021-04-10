#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from customWidgets import signalTabWidget
from signalPlotWidget import plotArray

# dict format:  '#code' : (paramValue,'string name')
resampleFsMethodDict = {0: ('min', 'Min'), 1: ('max', 'Max'), 2: ('custom', 'Custom')}
resampleInterpolationMethod = {0: ('zero', 'Zero'), 1: ('linear', 'Linear'), 2: ('quadratic', 'Quadratic'), 3: ('cubic', 'Cubic')}
calibrationMethodDict = {0: ('absolute', 'Absolute'), 1: ('percentile', 'Percentiles 5/95')}
calibrationWindowDict = {0: ('alldata', 'All data'), 1: ('window10s', 'Window 10s'), 2: ('window5s', 'Window 5s'), 3: ('window2s', 'Window 2s')}


class resampleCalibrateWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)

        # Sampling frequency method
        default = 2  # custom
        self.fsMethod = resampleFsMethodDict[default][0]
        FsMethodWidget = QtWidgets.QComboBox()
        FsMethodWidget.setFixedWidth(100)
        FsMethodWidget.addItems([x[1] for x in resampleFsMethodDict.values()])
        FsMethodWidget.setCurrentIndex(default)
        FsMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('FsMethod'))

        formLayout.addRow('Frequency Type', FsMethodWidget)

        # Interpolation method
        default = 1  # linear
        self.interpMethod = resampleInterpolationMethod[default][0]
        interpMethodWidget = QtWidgets.QComboBox()
        interpMethodWidget.setFixedWidth(100)
        interpMethodWidget.addItems([x[1] for x in resampleInterpolationMethod.values()])
        interpMethodWidget.setCurrentIndex(default)
        interpMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('interpMethod'))

        formLayout.addRow('Method', interpMethodWidget)

        # custom value option
        default = 100.0
        self.customFs = QtWidgets.QDoubleSpinBox()
        self.customFs.setRange(10, 200)
        self.customFs.setFixedWidth(100)
        self.customFs.setDecimals(0)
        self.customFs.setSingleStep(1)
        self.customFs.setValue(default)
        self.Fs_custom = default
        self.customFs.setEnabled(True)
        self.customFs.valueChanged.connect(lambda: self.registerOptions('CustomFs'))

        formLayout.addRow('Sampling freq. (Hz)', self.customFs)

        # apply button
        self.resampleButton = QtWidgets.QPushButton('Resample')
        self.resampleButton.setFixedWidth(100)
        self.resampleButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        self.resampleButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.resampleButton.clicked.connect(self.resampleSignals)
        hbox.addWidget(self.resampleButton)

        # table with signal Information
        self.signalTab = signalCalibrationTab(['Label', 'Sig. type', 'Min', 'Max', 'Calibration method', 'Calibration window'],
                                              [150, 80, 80, 80, 150, 150], 83)
        hbox.addWidget(self.signalTab)

        for s in self.data.signals:
            [min, max] = s.yLimits(method='percentile', detrend=False)
            resampleWid = self.signalTab.addSignal(channel=s.channel, label=s.label, sigType=s.sigType, max=max, min=min)
            resampleWid.windowChange.connect(self.drawWindow)
            resampleWid.apply.connect(self.applyCalibration)

        hbox.addStretch(1)

        # plot area
        self.plotArea = plotArray(self.data)
        self.plotArea.plotAllsignals()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.plotArea)
        self.setLayout(vbox)

    def updateTab(self):
        self.plotArea.replotAllsignals()
        for ch in range(self.signalTab.nChannels):
            channel = self.signalTab.channels[ch]
            channel.updateLabels(self.data.signals[ch].label, self.data.signals[ch].sigType)

    def registerOptions(self, type):
        if type == 'FsMethod':
            self.fsMethod = resampleFsMethodDict[self.sender().currentIndex()][0]
            if self.fsMethod == 'custom':
                self.customFs.setEnabled(True)
            else:
                self.customFs.setEnabled(False)
        if type == 'interpMethod':
            self.interpMethod = resampleInterpolationMethod[self.sender().currentIndex()][0]

        if type == 'CustomFs':
            self.Fs_custom = self.sender().value()

    # resample the signals
    def resampleSignals(self):

        self.data.removeRRmarks()
        self.data.removeBeat2beat()

        if self.fsMethod == 'min':
            Fs = 1e100
            for s in self.data.signals:
                Fs = min(Fs, s.samplingRate_Hz)
        if self.fsMethod == 'max':
            Fs = -1e100
            for s in self.data.signals:
                Fs = max(Fs, s.samplingRate_Hz)
        if self.fsMethod == 'custom':
            Fs = self.Fs_custom

        # resample via interpolation
        for s in self.data.signals:
            s.resample(Fs, method=self.interpMethod)

        self.plotArea.replotAllsignals()
        self.resampleButton.clearFocus()

    # creates a new region selection element when the user clicks on 'new selection' under artefact removal
    def drawWindow(self):
        channel = self.sender().channel

        try:
            self.plotArea.axes[channel].removeSelection()
        except AttributeError:
            pass
        if self.sender().calWindow == 'window10s':
            self.plotArea.axes[channel].addSelection(minX=0, maxX=10, type='interval')
        if self.sender().calWindow == 'window5s':
            self.plotArea.axes[channel].addSelection(minX=0, maxX=5, type='interval')
        if self.sender().calWindow == 'window2s':
            self.plotArea.axes[channel].addSelection(minX=0, maxX=2, type='interval')

    def applyCalibration(self):

        self.data.removeBeat2beat()

        channel = self.sender().channel
        signal = self.data.signals[channel]

        if self.plotArea.axes[channel].hasSelection:
            limits = self.plotArea.getSelectionPos(channel)
            xMin, xMax, posMin, posMax = limits
            segmentIndexes = [posMin, posMax]
        else:
            segmentIndexes = None

        signal.calibrate(valMax=self.sender().max, valMin=self.sender().min, method=self.sender().calMethod, segmentIndexes=segmentIndexes)

        self.plotArea.replotAllsignals()


class signalCalibrationTab(signalTabWidget):
    def __init__(self, colLabels, colSizes, colLabelsOffset):
        signalTabWidget.__init__(self, colLabels, colSizes, colLabelsOffset)

    def addSignal(self, channel, label, sigType, max, min):
        signal = channelSettings(channel, label, sigType, max, min, self.colSizes)
        self.vbox.addWidget(signal)
        self.channels.append(signal)
        self.nChannels = len(self.channels)
        return signal


class channelSettings(QtWidgets.QWidget):
    apply = QtCore.pyqtSignal(bool)
    windowChange = QtCore.pyqtSignal(bool)

    def __init__(self, channel, label, sigType, max, min, colSizes):
        QtWidgets.QWidget.__init__(self)
        self.channel = channel
        self.label = label
        self.sigType = sigType
        self.max = max
        self.min = min
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

        # sigtype

        self.signalType = QtWidgets.QLabel(str(self.sigType))
        self.signalType.setFixedWidth(self.colSizes[1])

        # min
        minSignal = QtWidgets.QLineEdit()
        minSignal.setText('{0:.2f}'.format(self.min))
        minSignal.setFixedWidth(self.colSizes[2])
        onlyDouble = QtGui.QDoubleValidator()
        minSignal.setValidator(onlyDouble)
        minSignal.editingFinished.connect(lambda: self.registerContents('min'))
        minSignal.returnPressed.connect(lambda: self.registerContents('min'))
        minSignal.textChanged.connect(lambda: self.registerContents('min'))

        # max
        maxSignal = QtWidgets.QLineEdit()
        maxSignal.setText('{0:.2f}'.format(self.max))
        maxSignal.setFixedWidth(self.colSizes[3])
        maxSignal.setValidator(onlyDouble)
        maxSignal.editingFinished.connect(lambda: self.registerContents('max'))
        maxSignal.returnPressed.connect(lambda: self.registerContents('max'))
        maxSignal.textChanged.connect(lambda: self.registerContents('max'))

        # calibration method
        default = 0  # 'absolute'
        self.calMethod = calibrationMethodDict[default][0]
        calibrationMethod = QtWidgets.QComboBox()
        calibrationMethod.setFixedWidth(self.colSizes[4])
        calibrationMethod.addItems([x[1] for x in calibrationMethodDict.values()])
        calibrationMethod.setCurrentIndex(default)
        calibrationMethod.currentIndexChanged.connect(lambda: self.registerContents('calMethod'))

        # calibration window
        default = 0  # 'all Data'
        self.calWindow = calibrationWindowDict[default][0]
        calibrationWindow = QtWidgets.QComboBox()
        calibrationWindow.setFixedWidth(self.colSizes[4])
        calibrationWindow.addItems([x[1] for x in calibrationWindowDict.values()])
        calibrationWindow.setCurrentIndex(default)
        calibrationWindow.currentIndexChanged.connect(lambda: self.registerContents('calWindow'))

        # calibration button
        self.applyButton = QtWidgets.QPushButton('Calibrate')
        self.applyButton.setFixedWidth(100)
        self.applyButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyButton.clicked.connect(self.applyChanges)

        # monta o layout
        hbox0.addWidget(channelSignal)
        hbox0.addWidget(self.labelSignal)
        hbox0.addWidget(self.signalType)
        hbox0.addWidget(minSignal)
        hbox0.addWidget(maxSignal)
        hbox0.addWidget(calibrationMethod)
        hbox0.addWidget(calibrationWindow)
        hbox0.addWidget(self.applyButton)

    def updateLabels(self, label, sigType):
        self.label = label
        self.sigType = sigType
        self.labelSignal.setText(self.label)
        self.signalType.setText(str(self.sigType))

    def registerContents(self, type):
        if type == 'min':
            self.min = float(self.sender().text())
        if type == 'max':
            self.max = float(self.sender().text())
        if type == 'calMethod':
            self.calMethod = calibrationMethodDict[self.sender().currentIndex()][0]
        if type == 'calWindow':
            self.calWindow = calibrationWindowDict[self.sender().currentIndex()][0]
            self.windowChange.emit(True)

    def applyChanges(self):
        self.apply.emit(True)
        self.applyButton.clearFocus()
