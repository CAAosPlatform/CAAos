#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from CAAos.GUI.toolbox_ARanalysis.ARI import ARIPlotWidget
from CAAos.GUI.conf.GUIsetup import pyQtConf

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
        if False:
            # I removed this option because it is not currently implemented
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
        self.applyARIButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.applyARIButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyARIButton.clicked.connect(self.applyARI)
        hbox.addWidget(self.applyARIButton)

        # Save button
        self.saveButton = QtWidgets.QPushButton('Save ARI data')
        self.saveButton.setFixedWidth(100)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.saveButton.clicked.connect(self.saveARI)
        hbox.addWidget(self.saveButton)

        # Create table
        self.resultTableLWidget = ARIresultTable()
        self.resultTableRWidget = ARIresultTable()
        hbox.addStretch(1)

        # plot area
        self.plotAreaL = ARIPlotWidget.plotArray(self.data, side='L', nCols=1)
        vboxL = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel('Left')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont('SansSerif', 18, QtGui.QFont.Bold))
        vboxL.addWidget(text)
        vboxL.addWidget(self.resultTableLWidget)
        vboxL.addWidget(self.plotAreaL)

        self.plotAreaR = ARIPlotWidget.plotArray(self.data, side='R', nCols=1)
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
            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save ARI data as',
                                                                                   self.data.dirName + self.data.filePrefix + '_ARI' + fileExtension,
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


class ARIresultTable(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.nChannels = 0
        self.nRows = 1  # does not include the label row
        self.nCols = 10  # does not include the label column
        self.colSizes = 120
        self.colLabels = ['0','1','2','3','4','5','6','7','8','9']
        self.rowLabels = ['Error:']
        self.colLabelsOffset = 5
        self.initUI()
        #self.setFixedWidth(700)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

    def initUI(self):
        vboxL = QtWidgets.QVBoxLayout()
        self.grid = QtWidgets.QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setRowMinimumHeight(0, 10)
        self.grid.setColumnMinimumWidth(0, 20)

        #self.bestFitLabel = QtWidgets.QLabel('Best fit: ', self)

        vboxL.addLayout(self.grid)
        #vboxL.addWidget(self.bestFitLabel)

        self.setLayout(vboxL)
        self.initTable()
        self.setError([0.0,]*10)
        self.setBestFit(0)

    def initTable(self):

        # columns
        for i in range(self.nCols):
            text = QtWidgets.QLabel(self.colLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, 0, i + 1)
            text.setFixedWidth(50)

        # rows
        text = QtWidgets.QLabel('ARI:', self)
        text.setAlignment(QtCore.Qt.AlignRight)
        self.grid.addWidget(text, 0,0)
        text.setFixedWidth(50)

        for i in range(self.nRows):
            text = QtWidgets.QLabel(self.rowLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, i + 1, 0)

        # cels
        for i in range(self.nRows):
            for j in range(self.nCols):
                text = QtWidgets.QLabel('{0:.2f}'.format(0), self)
                text.setAlignment(QtCore.Qt.AlignRight)
                self.grid.addWidget(text, i + 1, j + 1)
        #best Fit
        self.grid.addWidget(QtWidgets.QLabel('Best Fit:', self), self.nRows+ 1, 0)
        self.bestFitLabel = QtWidgets.QLabel('0', self)
        self.bestFitLabel.setAlignment(QtCore.Qt.AlignRight)
        self.grid.addWidget(self.bestFitLabel, self.nRows+ 1, 1)

    def setError(self, values):
        row=0
        for i, v in enumerate(values):
            valueStr = str('{0:.2f}'.format(v))
            text = self.grid.itemAtPosition(row + 1, i + 1).widget()
            text.setText(valueStr)

    def setBestFit(self, bestARI):
        self.bestFitLabel.setText('{0:.2f}'.format(bestARI)    )

