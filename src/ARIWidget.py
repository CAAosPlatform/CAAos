#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from ARIPlotWidget import plotArray, pyQtConf
from customWidgets import ARIresultTable

plotFileFormatDict = {0: ('png', 'PNG'), 1: ('jpg', 'JPG'), 2: ('tif', 'TIF'), 3: ('pdf', 'PDF'), 4: ('svg', 'SVG'), 5: ('eps', 'EPS'),
                      6: ('ps', 'PS'), 7:('none','None')}


class ARIWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)

        # Response time
        # custom value option
        default = 10.0
        self.responseTime = default
        responseTimeWidget = QtWidgets.QDoubleSpinBox()
        responseTimeWidget.setRange(5, 30)
        responseTimeWidget.setFixedWidth(100)
        responseTimeWidget.setDecimals(1)
        responseTimeWidget.setSingleStep(0.5)
        responseTimeWidget.setValue(default)
        responseTimeWidget.setEnabled(True)
        responseTimeWidget.valueChanged.connect(lambda: self.registerOptions('responseTime'))

        formLayout.addRow('responseTime (s)', responseTimeWidget)

        # plot file format
        default = 0  # png
        self.plotFileFormat = plotFileFormatDict[default][0]
        plotFileFormatControl = QtWidgets.QComboBox()
        plotFileFormatControl.addItems([x[1] for x in plotFileFormatDict.values()])
        plotFileFormatControl.setCurrentIndex(default)
        plotFileFormatControl.currentIndexChanged.connect(lambda: self.registerOptions('plotFileFormat'))

        formLayout.addRow('Plot file format', plotFileFormatControl)

        # ARI button
        self.applyARIButton = QtWidgets.QPushButton('Compute ARI')
        self.applyARIButton.setFixedWidth(100)
        self.applyARIButton.setEnabled(False)
        self.applyARIButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        self.applyARIButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyARIButton.clicked.connect(self.applyARI)
        hbox.addWidget(self.applyARIButton)

        # Save button
        self.saveButton = QtWidgets.QPushButton('Save ARI data')
        self.saveButton.setFixedWidth(100)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.saveButton.clicked.connect(self.saveARI)
        hbox.addWidget(self.saveButton)

        # Create table
        self.resultTableLWidget = ARIresultTable()
        self.resultTableRWidget = ARIresultTable()
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
        if self.data.hasTFdata_L or self.data.hasTFdata_R:
            self.applyARIButton.setEnabled(True)
        else:
            self.applyARIButton.setEnabled(False)
        pass

        if self.data.hasARIdata_L or self.data.hasARIdata_R:
            self.saveButton.setEnabled(True)
        else:
            self.saveButton.setEnabled(False)

        # left side
        if self.data.hasARIdata_L:
            self.plotData(side='L')  # self.fillTableResults(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasARIdata_R:
            self.plotData(side='R')  # self.fillTableResults(side='R')
            self.fillTableResults(side='R')

        if self.data.hasTFdata_L or self.data.hasTFdata_R:
            self.applyARIButton.setEnabled(True)
            self.applyARIButton.setText('Compute ARI')
            self.applyARIButton.setStyleSheet('color:rgb(0,0,0);background-color:rgb(192,255,208)')  # light green
        else:
            self.applyARIButton.setEnabled(False)
            self.applyARIButton.setText('Compute ARI\n\nPlease run \nTFA first')
            self.applyARIButton.setStyleSheet('color:rgb(255,0,0)')

    def registerOptions(self, typeOpt):
        if typeOpt == 'responseTime':
            self.responseTime = self.sender().value()
        if typeOpt == 'plotFileFormat':
            self.plotFileFormat = plotFileFormatDict[self.sender().currentIndex()][0]
            if self.plotFileFormat.lower() == 'none':
                self.plotFileFormat = None

    # synchronize signals
    def applyARI(self):
        self.data.computeARI()
        self.applyARIButton.clearFocus()
        self.saveButton.setEnabled(True)

        # left side
        if self.data.hasARIdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasARIdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

    # side:  'L'  or 'R'
    def fillTableResults(self, side='L'):

        # select data
        if side.upper() == 'L':
            resultTable = self.resultTableLWidget
            ARIdata = self.data.ARI_L
        if side.upper() == 'R':
            resultTable = self.resultTableRWidget
            ARIdata = self.data.ARI_R

        resultTable.setError(ARIdata.TiecksErrors)
        resultTable.setBestFit(ARIdata.ARI_frac)


    def saveARI(self):
        self.parent().patientData = self.data
        fileExtension = '.ari'

        if self.data.hasARIdata_L or self.data.hasARIdata_R:
            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save autoregulation index data as',
                                                                                   self.data.dirName + self.data.filePrefix + fileExtension,
                                                                                   'Autoregulation index (.ari) (*.ari);;'
                                                                                   'CSV (.csv) (*.csv);;'
                                                                                   'Numpy (.npy) (*npy);;')
            if resultFileName:
                if '.csv' in selectedFilter:
                    fileFormat = 'csv'
                if '.npy' in selectedFilter:
                    fileFormat = 'numpy'
                if '.ari' in selectedFilter:
                    fileFormat = 'simple_text'

                self.data.saveARI(filePath = resultFileName, plotFileFormat = self.plotFileFormat, format=fileFormat, register=True)

    # side:  'L'  or 'R'
    def plotData(self, side='L'):

        # select data
        if side.upper() == 'L':
            plotArea = self.plotAreaL
            ARI_data = self.data.ARI_L
        if side.upper() == 'R':
            plotArea = self.plotAreaR
            ARI_data = self.data.ARI_R

        # create plots
        plotArea.clearAll()
        plotArea.addNewPlot(yData=[[ARI_data.stepResponse, pyQtConf['plotColors']['red'], 'Patient'],
                                   [ARI_data.ARIbestFit, pyQtConf['plotColors']['blue'], 'ARI(best fit)']],
                            yUnit='Velocity [ %s ]' % ARI_data.unitV, title='', logY=False, legend=True)

        # set limits
        maxImp = np.amax(ARI_data.stepResponse)
        minImp = np.amin(ARI_data.stepResponse)
        maxTiek = np.amax(ARI_data.ARIbestFit)
        minTiek = np.amin(ARI_data.ARIbestFit)
        plotArea.setLimits(xlim=[0, ARI_data.timeVals[-1]], ylim=[[min(minImp, minTiek), max(maxImp, maxTiek)]])
