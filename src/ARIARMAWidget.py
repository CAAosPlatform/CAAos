#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from ARIARMAPlotWidget import plotArray, pyQtConf
from customWidgets import ARIresultTable

plotFileFormatDict = {0: ('png', 'PNG'), 1: ('jpg', 'JPG'), 2: ('tif', 'TIF'), 3: ('pdf', 'PDF'), 4: ('svg', 'SVG'), 5: ('eps', 'EPS'),
                      6: ('ps', 'PS'), 7:('none','None')}


class ARIARMAWidget(QtWidgets.QWidget):

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

        # order P
        # custom value option
        default = 2
        self.orderP = default
        orderP_Widget = QtWidgets.QDoubleSpinBox()
        orderP_Widget.setRange(1, 5)
        orderP_Widget.setFixedWidth(100)
        orderP_Widget.setDecimals(0)
        orderP_Widget.setSingleStep(1)
        orderP_Widget.setValue(default)
        orderP_Widget.setEnabled(True)
        orderP_Widget.valueChanged.connect(lambda: self.registerOptions('orderP'))

        formLayout.addRow('order P', orderP_Widget)

        # order Q
        # custom value option
        default = 2
        self.orderQ = default
        orderQ_Widget = QtWidgets.QDoubleSpinBox()
        orderQ_Widget.setRange(1, 5)
        orderQ_Widget.setFixedWidth(100)
        orderQ_Widget.setDecimals(0)
        orderQ_Widget.setSingleStep(1)
        orderQ_Widget.setValue(default)
        orderQ_Widget.setEnabled(True)
        orderQ_Widget.valueChanged.connect(lambda: self.registerOptions('orderQ'))

        formLayout.addRow('order Q', orderQ_Widget)

        # plot file format
        default = 0  # png
        self.plotFileFormat = plotFileFormatDict[default][0]
        plotFileFormatControl = QtWidgets.QComboBox()
        plotFileFormatControl.addItems([x[1] for x in plotFileFormatDict.values()])
        plotFileFormatControl.setCurrentIndex(default)
        plotFileFormatControl.currentIndexChanged.connect(lambda: self.registerOptions('plotFileFormat'))

        formLayout.addRow('Plot file format', plotFileFormatControl)

        # ARI button
        self.applyARIButton = QtWidgets.QPushButton('Compute\nARI ARMA')
        self.applyARIButton.setFixedWidth(100)
        #self.applyARIButton.setEnabled(False)
        self.applyARIButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.applyARIButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyARIButton.clicked.connect(self.applyARIARMA)
        hbox.addWidget(self.applyARIButton)

        # Save button
        self.saveButton = QtWidgets.QPushButton('Save\nARI ARMA\ndata')
        self.saveButton.setFixedWidth(130)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.saveButton.clicked.connect(self.saveARIARMA)
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

        if self.data.hasARIARMAdata_L or self.data.hasARIARMAdata_R:
            self.saveButton.setEnabled(True)
        else:
            self.saveButton.setEnabled(False)


        # left side
        if self.data.hasARIARMAdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasARIARMAdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

    def registerOptions(self, typeOpt):
        if typeOpt == 'useB2B':
            self.useB2B = self.sender().isChecked()
        if typeOpt == 'orderP':
            self.orderP = self.sender().value()
        if typeOpt == 'orderQ':
            self.orderQ = self.sender().value()

        if typeOpt == 'plotFileFormat':
            self.plotFileFormat = plotFileFormatDict[self.sender().currentIndex()][0]
            if self.plotFileFormat.lower() == 'none':
                self.plotFileFormat = None

    # synchronize signals
    def applyARIARMA(self):
        self.data.computeARIARMA(useB2B=self.useB2B, orderP=self.orderP, orderQ=self.orderQ)
        self.applyARIButton.clearFocus()
        self.saveButton.setEnabled(True)

        # left side
        if self.data.hasARIARMAdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasARIARMAdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

    # side:  'L'  or 'R'
    def fillTableResults(self, side='L'):

        # select data
        if side.upper() == 'L':
            resultTable = self.resultTableLWidget
            ARIdata = self.data.ARIARMA_L
        if side.upper() == 'R':
            resultTable = self.resultTableRWidget
            ARIdata = self.data.ARIARMA_R

        resultTable.setError(ARIdata.TiecksErrors)
        resultTable.setBestFit(ARIdata.ARI_frac)


    def saveARIARMA(self):
        self.parent().patientData = self.data
        fileExtension = '.ariarma'

        if self.data.hasARIARMAdata_L or self.data.hasARIARMAdata_R:
            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save ARI ARMA data as',
                                                                                   self.data.dirName + self.data.filePrefix + '_ARI' + fileExtension,
                                                                                   'Autoregulation index (.ariarma) (*.ariarma);;'
                                                                                   'CSV (.csv) (*.csv);;'
                                                                                   'Numpy (.npy) (*npy);;')
            if resultFileName:
                if '.csv' in selectedFilter:
                    fileFormat = 'csv'
                if '.npy' in selectedFilter:
                    fileFormat = 'numpy'
                if '.ari' in selectedFilter:
                    fileFormat = 'simple_text'

                self.data.saveARIARMA(filePath = resultFileName, plotFileFormat = self.plotFileFormat, format=fileFormat, register=True)

    # side:  'L'  or 'R'
    def plotData(self, side='L'):

        # select data
        if side.upper() == 'L':
            plotArea = self.plotAreaL
            ARIARMA_data = self.data.ARIARMA_L
        if side.upper() == 'R':
            plotArea = self.plotAreaR
            ARIARMA_data = self.data.ARIARMA_R

        # create plots
        plotArea.clearAll()
        plotArea.addNewPlot(yData=[[ARIARMA_data.stepResponse, pyQtConf['plotColors']['red'], 'Patient'],
                                   [ARIARMA_data.ARIbestFit, pyQtConf['plotColors']['blue'], 'ARI(best fit)']],
                            yUnit='Velocity [ %s ]' % ARIARMA_data.unitV, title='', logY=False, legend=True)

        # set limits
        maxImp = np.amax(ARIARMA_data.stepResponse)
        minImp = np.amin(ARIARMA_data.stepResponse)
        maxTiek = np.amax(ARIARMA_data.ARIbestFit)
        minTiek = np.amin(ARIARMA_data.ARIbestFit)
        plotArea.setLimits(xlim=[0, ARIARMA_data.timeVals[-1]], ylim=[[min(minImp, minTiek), max(maxImp, maxTiek)]])
