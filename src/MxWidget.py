#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from MXPlotWidget import plotArray, pyQtConf
from customWidgets import MXresultTable

plotFileFormatDict = {0: ('png', 'PNG'), 1: ('jpg', 'JPG'), 2: ('tif', 'TIF'), 3: ('pdf', 'PDF'), 4: ('svg', 'SVG'), 5: ('eps', 'EPS'),
                      6: ('ps', 'PS'), 7: ('none', 'None')}


class MxWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)

        # use B2B
        default = True
        self.useB2B = default
        useB2B = QtWidgets.QCheckBox('', self)
        # useB2B.setFixedWidth(30)
        useB2B.setChecked(self.useB2B)
        useB2B.stateChanged.connect(lambda: self.registerOptions('useB2B'))

        formLayout.addRow('Use beat-to-beat data', useB2B)

        # epoch length in seconds
        # custom value option
        default = 60
        self.epochLength = default
        epochLengthWidget = QtWidgets.QDoubleSpinBox()
        epochLengthWidget.setRange(10, 60)
        epochLengthWidget.setFixedWidth(100)
        epochLengthWidget.setDecimals(0)
        epochLengthWidget.setSingleStep(5)
        epochLengthWidget.setValue(default)
        epochLengthWidget.setEnabled(True)
        epochLengthWidget.valueChanged.connect(lambda: self.registerOptions('epochLength'))

        formLayout.addRow('epoch length (s)', epochLengthWidget)

        # block length in seconds
        # custom value option
        default = 10
        self.blockLength = default
        blockLengthWidget = QtWidgets.QDoubleSpinBox()
        blockLengthWidget.setRange(1, 10)
        blockLengthWidget.setFixedWidth(100)
        blockLengthWidget.setDecimals(0)
        blockLengthWidget.setSingleStep(1)
        blockLengthWidget.setValue(default)
        blockLengthWidget.setEnabled(True)
        blockLengthWidget.valueChanged.connect(lambda: self.registerOptions('blockLength'))

        formLayout.addRow('block length (s)', blockLengthWidget)

        # plot file format
        default = 0  # png
        self.plotFileFormat = plotFileFormatDict[default][0]
        plotFileFormatControl = QtWidgets.QComboBox()
        plotFileFormatControl.addItems([x[1] for x in plotFileFormatDict.values()])
        plotFileFormatControl.setCurrentIndex(default)
        plotFileFormatControl.currentIndexChanged.connect(lambda: self.registerOptions('plotFileFormat'))

        formLayout.addRow('Plot file format', plotFileFormatControl)

        # MX button
        self.applyMXButton = QtWidgets.QPushButton('Compute Mx')
        self.applyMXButton.setFixedWidth(100)
        self.applyMXButton.setEnabled(False)
        self.applyMXButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.applyMXButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyMXButton.clicked.connect(self.applyMX)
        hbox.addWidget(self.applyMXButton)

        # Save button
        self.saveButton = QtWidgets.QPushButton('Save Mx data')
        self.saveButton.setFixedWidth(100)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.saveButton.clicked.connect(self.saveMX)
        hbox.addWidget(self.saveButton)

        # Create table
        self.resultTableLWidget = MXresultTable()
        self.resultTableRWidget = MXresultTable()
        hbox.addStretch(1)

        # plot area
        self.plotAreaL = plotArray(self.data, side='L', nCols=1)
        vboxL = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel('Left')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont('SansSerif', 18, QtGui.QFont.Bold))
        vboxL.addWidget(text)
        vboxL.addWidget(self.resultTableLWidget)
        vboxL.addWidget(self.plotAreaL)
        #
        self.plotAreaR = plotArray(self.data, side='R', nCols=1)
        vboxR = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel('Right')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont('SansSerif', 18, QtGui.QFont.Bold))
        vboxR.addWidget(text)
        vboxR.addWidget(self.resultTableRWidget)
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

        if self.data.hasMXdata_L or self.data.hasMXdata_R:
            self.saveButton.setEnabled(True)
        else:
            self.saveButton.setEnabled(False)

        # left side
        if self.data.hasMXdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasMXdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

        self.applyMXButton.setEnabled(True)
        self.applyMXButton.setText('Compute MX')
        self.applyMXButton.setStyleSheet('color:rgb(0,0,0);background-color:rgb(192,255,208)')  # light green

    def registerOptions(self, typeOpt):
        if typeOpt == 'epochLength':
            self.epochLength = self.sender().value()
        if typeOpt == 'blockLength':
            self.blockLength = self.sender().value()
        if typeOpt == 'plotFileFormat':
            self.plotFileFormat = plotFileFormatDict[self.sender().currentIndex()][0]
            if self.plotFileFormat.lower() == 'none':
                self.plotFileFormat = None
        if typeOpt == 'useB2B':
            self.useB2B = self.sender().isChecked()

        if self.epochLength < self.blockLength:
            self.applyMXButton.setEnabled(False)
            self.applyMXButton.setText('Compute MX\n\n epoch must be larger than block')
            self.applyMXButton.setStyleSheet('color:rgb(255,0,0)')
        else:
            self.applyMXButton.setEnabled(True)
            self.applyMXButton.setText('Compute MX')
            self.applyMXButton.setStyleSheet('color:rgb(0,0,0);background-color:rgb(192,255,208)')  # light green

    # synchronize signals
    def applyMX(self):
        self.data.computeMX(useB2B=self.useB2B, epochLength_s=self.epochLength, blockLength_s=self.blockLength, register=True)
        self.applyMXButton.clearFocus()
        self.saveButton.setEnabled(True)

        # left side
        if self.data.hasMXdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasMXdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

    # side:  'L'  or 'R'
    def fillTableResults(self, side='L'):

        # select data
        if side.upper() == 'L':
            resultTable = self.resultTableLWidget
            MXdata = self.data.Mx_L
        if side.upper() == 'R':
            resultTable = self.resultTableRWidget
            MXdata = self.data.Mx_R

        resultTable.setMx(MXdata.Mx)
        resultTable.setAvgMx(MXdata.MxAvg)

    def saveMX(self):
        self.parent().patientData = self.data
        fileExtension = '.mx'

        if self.data.hasMXdata_L or self.data.hasMXdata_R:
            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save autoregulation index data as',
                                                                                   self.data.dirName + self.data.filePrefix + '_MX' + fileExtension,
                                                                                   'Autoregulation index (.mx) (*.mx);;'
                                                                                   'CSV (.csv) (*.csv);;'
                                                                                   'Numpy (.npy) (*npy);;')
            if resultFileName:
                if '.csv' in selectedFilter:
                    fileFormat = 'csv'
                if '.npy' in selectedFilter:
                    fileFormat = 'numpy'
                if '.mx' in selectedFilter:
                    fileFormat = 'simple_text'

                self.data.saveMX(filePath=resultFileName, plotFileFormat=self.plotFileFormat, format=fileFormat, register=True)

    # side:  'L'  or 'R'
    def plotData(self, side='L'):

        # select data
        if side.upper() == 'L':
            plotArea = self.plotAreaL
            MX_data = self.data.Mx_L
        if side.upper() == 'R':
            plotArea = self.plotAreaR
            MX_data = self.data.Mx_R

        # create plots
        plotArea.clearAll()
        plotArea.addNewPlot(yData=[[MX_data.Mx, (0,0,0), 'Epochs']], yUnit='Mx', title='', logY=False, legend=False)
        plotArea.markAvg(plotNbr=0, avgValue=MX_data.MxAvg,legend=None)

