#! /usr/bin/python

# -*- coding: utf-8 -*-

import os

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

import ARsetup
from customWidgets import TFAresultTable
from spectrumPlotWidget import plotArray, pyQtConf

# dict format:  '#code' : (paramValue,'string name')
estimatorTypeDict = {0: ('H1', 'H1=Sxy/Sxx'), 1: ('H2', 'H2=Syy/Syx')}
plotFileFormatDict = {0: ('png', 'PNG'), 1: ('jpg', 'JPG'), 2: ('tif', 'TIF'), 3: ('pdf', 'PDF'), 4: ('svg', 'SVG'), 5: ('eps', 'EPS'),
                      6: ('ps', 'PS'), 7:('none','None')}


class TFAWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)

        # H estimator type
        default = 0
        self.estimatorType = estimatorTypeDict[default][0]
        estimatorTypeControl = QtWidgets.QComboBox()
        estimatorTypeControl.addItems([x[1] for x in estimatorTypeDict.values()])
        estimatorTypeControl.setCurrentIndex(default)
        estimatorTypeControl.currentIndexChanged.connect(lambda: self.registerOptions('estimatorType'))

        formLayout.addRow('H estimator method', estimatorTypeControl)

        # coherence Treshold
        default = True
        self.coheTreshold = default
        coheTreshControl = QtWidgets.QCheckBox('', self)
        # useB2B.setFixedWidth(30)
        coheTreshControl.setChecked(self.coheTreshold)
        coheTreshControl.stateChanged.connect(lambda: self.registerOptions('coheTresh'))

        formLayout.addRow('Use coherence Threshold', coheTreshControl)

        # negative Phase
        default = True
        self.removeNegPhase = default
        negativePhaseControl = QtWidgets.QCheckBox('', self)
        # useB2B.setFixedWidth(30)
        negativePhaseControl.setChecked(self.removeNegPhase)
        negativePhaseControl.stateChanged.connect(lambda: self.registerOptions('negativePhase'))

        formLayout.addRow('Ignore negative Phase', negativePhaseControl)

        # plot file format
        default = 0  # png
        self.plotFileFormat = plotFileFormatDict[default][0]
        plotFileFormatControl = QtWidgets.QComboBox()
        plotFileFormatControl.addItems([x[1] for x in plotFileFormatDict.values()])
        plotFileFormatControl.setCurrentIndex(default)
        plotFileFormatControl.currentIndexChanged.connect(lambda: self.registerOptions('plotFileFormat'))

        formLayout.addRow('Plot file format', plotFileFormatControl)

        # TFA button
        self.applyTFAButton = QtWidgets.QPushButton('Compute TFA')
        self.applyTFAButton.setFixedWidth(100)
        self.applyTFAButton.setEnabled(False)
        self.applyTFAButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.applyTFAButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyTFAButton.clicked.connect(self.applyTFA)
        hbox.addWidget(self.applyTFAButton)

        # Save button
        self.saveButton = QtWidgets.QPushButton('Save TFA data')
        self.saveButton.setFixedWidth(100)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.saveButton.clicked.connect(self.saveTFA)
        hbox.addWidget(self.saveButton)

        # Create table
        self.resultTableLWidget = TFAresultTable()
        self.resultTableRWidget = TFAresultTable()
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
        if self.data.hasPSDdata_L or self.data.hasPSDdata_R:
            self.applyTFAButton.setEnabled(True)
        else:
            self.applyTFAButton.setEnabled(False)
        pass

        if self.data.hasTFdata_L or self.data.hasTFdata_R:
            self.saveButton.setEnabled(True)
        else:
            self.saveButton.setEnabled(False)

        # left side
        if self.data.hasTFdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasTFdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

        if self.data.hasPSDdata_L or self.data.hasPSDdata_R:
            self.applyTFAButton.setEnabled(True)
            self.applyTFAButton.setText('Compute TFA')
            self.applyTFAButton.setStyleSheet('color:rgb(0,0,0);background-color:rgb(192,255,208)')  # light green
        else:
            self.applyTFAButton.setEnabled(False)
            self.applyTFAButton.setText('Compute TFA\n\nPlease run\n PSD first')
            self.applyTFAButton.setStyleSheet('color:rgb(255,0,0)')

    def registerOptions(self, typeOpt):
        if typeOpt == 'estimatorType':
            self.estimatorType = estimatorTypeDict[self.sender().currentIndex()][0]
        if typeOpt == 'coheTresh':
            self.coheTreshold = self.sender().isChecked()
        if typeOpt == 'negativePhase':
            self.removeNegPhase = self.sender().isChecked()
        if typeOpt == 'plotFileFormat':
            self.plotFileFormat = plotFileFormatDict[self.sender().currentIndex()][0]
            if self.plotFileFormat.lower() == 'none':
                self.plotFileFormat = None

    # synchronize signals
    def applyTFA(self):
        self.data.computeTFA(estimatorType=self.estimatorType)
        self.applyTFAButton.clearFocus()
        self.saveButton.setEnabled(True)

        # left side
        if self.data.hasTFdata_L:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        # right side
        if self.data.hasTFdata_R:
            self.plotData(side='R')
            self.fillTableResults(side='R')

    # side:  'L'  or 'R'
    def fillTableResults(self, side='L'):

        # select data
        if side.upper() == 'L':
            resultTable = self.resultTableLWidget
            TFAdata = self.data.TFA_L
        if side.upper() == 'R':
            resultTable = self.resultTableRWidget
            TFAdata = self.data.TFA_R

        # gain
        avg = [TFAdata.getGainStatistics(freqRange=r, coheTreshold=self.coheTreshold)[0] for r in ['VLF', 'LF', 'HF']]
        std = [TFAdata.getGainStatistics(freqRange=r, coheTreshold=self.coheTreshold)[1] for r in ['VLF', 'LF', 'HF']]
        resultTable.setGain(avg)

        # phase
        avg = [TFAdata.getPhaseStatistics(freqRange=r, coheTreshold=self.coheTreshold, remNegPhase=self.removeNegPhase)[0] * 180 / np.pi for r in
               ['VLF', 'LF', 'HF']]
        std = [TFAdata.getPhaseStatistics(freqRange=r, coheTreshold=self.coheTreshold, remNegPhase=self.removeNegPhase)[1] * 180 / np.pi for r in
               ['VLF', 'LF', 'HF']]
        resultTable.setPhase(avg)

        # coherence
        avg = [TFAdata.getCoherenceStatistics(freqRange=r)[0] for r in ['VLF', 'LF', 'HF']]
        std = [TFAdata.getCoherenceStatistics(freqRange=r)[1] for r in ['VLF', 'LF', 'HF']]
        resultTable.setCoherence(avg)

    def saveTFA(self):
        self.parent().patientData = self.data
        fileExtension = '.tf'

        if self.data.hasTFdata_L or self.data.hasTFdata_R:
            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save transfer function analysis data as',
                                                                                   self.data.dirName + self.data.filePrefix + fileExtension,
                                                                                   'Transfer function (.tf) (*.tf);;'
                                                                                   'CSV (.csv) (*.csv);;'
                                                                                   'Numpy (.npy) (*npy);;')
            if resultFileName:
                if '.csv' in selectedFilter:
                    fileFormat = 'csv'
                if '.npy' in selectedFilter:
                    fileFormat = 'numpy'
                if '.tf' in selectedFilter:
                    fileFormat = 'simple_text'

                self.data.saveTF(resultFileName, format=fileFormat, freqRange='ALL', register=True)
                self.data.saveTFAstatistics(os.path.splitext(resultFileName)[0] + '_TFA.tfa', self.plotFileFormat, self.coheTreshold,
                                            self.removeNegPhase, register=True)

    # side:  'L'  or 'R'
    def plotData(self, side='L'):

        # select data
        if side.upper() == 'L':
            plotArea = self.plotAreaL
            TFAdata = self.data.TFA_L

        if side.upper() == 'R':
            plotArea = self.plotAreaR
            TFAdata = self.data.TFA_R

        plotArea.clearAll()
        # create plots
        if len(plotArea.axes) > 0:
            plotArea.replot(plotNbr=0, yData=[TFAdata.getGain(freqRange='FULL')])
            plotArea.replot(plotNbr=1, yData=[TFAdata.getPhase(freqRange='FULL') * 180 / np.pi])
            plotArea.replot(plotNbr=2, yData=[TFAdata.getCoherence(freqRange='FULL')])
        else:
            plotArea.addNewPlot(yData=[[TFAdata.getGain(freqRange='FULL'), pyQtConf['plotColors']['base'], 'Gain']], yUnit='Gain\n[ '
                                                                                                                           +TFAdata.unitH+' ]',
                                title='',
                                logY=False)
            plotArea.addNewPlot(yData=[[TFAdata.getPhase(freqRange='FULL') * 180 / np.pi, pyQtConf['plotColors']['base'], 'Phase']],
                                yUnit='Phase [ degree ]',
                                title='', logY=False)
            plotArea.addNewPlot(yData=[[TFAdata.getCoherence(freqRange='FULL'), pyQtConf['plotColors']['base'], 'Coherence']], yUnit='Coh. [ adim. ]',
                                title='', logY=False)

        # set limits
        _, _, coheMin, coheMax = TFAdata.getCoherenceStatistics(freqRange='ALL')
        _, _, gainMin, gainMax = TFAdata.getGainStatistics(freqRange='ALL', coheTreshold=False)
        _, _, phasMin, phasMax = TFAdata.getPhaseStatistics(freqRange='ALL', coheTreshold=False, remNegPhase=False)
        plotArea.setLimits(xlim=[ARsetup.freqRangeDic['VLF'][0], ARsetup.freqRangeDic['HF'][1]],
                           ylim=[[gainMin, gainMax], [phasMin * 180 / np.pi, phasMax * 180 / np.pi], [coheMin, coheMax]])

        # draw avg Lines
        avg = [TFAdata.getGainStatistics(freqRange=r, coheTreshold=self.coheTreshold)[0] for r in ['VLF', 'LF', 'HF']]
        plotArea.markAvgRanges(plotNbr=0, avgValues=avg)
        avg = [TFAdata.getPhaseStatistics(freqRange=r, coheTreshold=False, remNegPhase=self.removeNegPhase)[0] * 180 / np.pi for r in
               ['VLF', 'LF', 'HF']]
        plotArea.markAvgRanges(plotNbr=1, avgValues=avg)
        avg = [TFAdata.getCoherenceStatistics(freqRange=r)[0] for r in ['VLF', 'LF', 'HF']]
        plotArea.markAvgRanges(plotNbr=2, avgValues=avg)
