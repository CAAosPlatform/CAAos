#! /usr/bin/python

# -*- coding: utf-8 -*-

import os
from PyQt5 import QtGui,QtCore,QtWidgets
from customWidgets import TFAresultTable
import numpy as np
from spectrumPlotWidget import plotArray,pyQtConf
import pyqtgraph as pg
import ARsetup

#dict format:  '#code' : (paramValue,'string name')
estimatorTypeDict={0: ('H1','H1=Sxy/Sxx'), 1: ('H2','H2=Syy/Syx')}


class TFAWidget(QtWidgets.QWidget):
    
    def __init__(self,patientData):
        QtWidgets.QWidget.__init__(self)
        self.data=patientData
        self.initUI()
        
    def initUI(self):
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)
                       
                       
        # H estimator type
        default=0
        self.estimatorType=estimatorTypeDict[default][0]
        estimatorTypeControl = QtWidgets.QComboBox()
        estimatorTypeControl.addItems([x[1] for x  in estimatorTypeDict.values()])
        estimatorTypeControl.setCurrentIndex(default)  
        estimatorTypeControl.currentIndexChanged.connect(lambda: self.registerOptions('estimatorType'))
        
        formLayout.addRow('H estimator method',estimatorTypeControl)
        
        
        #coherence Treshold
        default=True
        self.coherenceTreshold=default
        coheTreshControl = QtGui.QCheckBox('', self)
        #useB2B.setFixedWidth(30)
        coheTreshControl.setChecked(self.coherenceTreshold)
        coheTreshControl.stateChanged.connect(lambda: self.registerOptions('coheTresh') )
        
        formLayout.addRow('Use coherence Threshold',coheTreshControl)
        
        #negative Phase
        default=True
        self.removeNegPhase=default
        negativePhaseControl = QtGui.QCheckBox('', self)
        #useB2B.setFixedWidth(30)
        negativePhaseControl.setChecked(self.removeNegPhase)
        negativePhaseControl.stateChanged.connect(lambda: self.registerOptions('negativePhase') )
        
        formLayout.addRow('Ignore negative Phase',negativePhaseControl)
        
        #TFA button
        self.applyTFAButton = QtWidgets.QPushButton("Compute TFA")
        self.applyTFAButton.setFixedWidth(100)
        self.applyTFAButton.setEnabled(False)
        self.applyTFAButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.applyTFAButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.applyTFAButton.clicked.connect(self.applyTFA)
        hbox.addWidget(self.applyTFAButton)

        #Save button
        self.saveButton = QtWidgets.QPushButton("Save TFA data")
        self.saveButton.setFixedWidth(100)
        self.saveButton.setEnabled(False)
        self.saveButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.saveButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.saveButton.clicked.connect(self.saveTFA)
        hbox.addWidget(self.saveButton)
        
        # Create table
        self.resultTableLWidget = TFAresultTable()
        self.resultTableRWidget = TFAresultTable()
        hbox.addStretch(1)
        
        #plot area
        self.plotAreaL=plotArray(self.data,side='L',nCols=1)
        vboxL = QtWidgets.QVBoxLayout()
        text=QtWidgets.QLabel('Left')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont("SansSerif", 18, QtGui.QFont.Bold) )
        vboxL.addWidget(text)
        vboxL.addWidget(self.resultTableLWidget)
        vboxL.addWidget(self.plotAreaL)
        
        self.plotAreaR=plotArray(self.data,side='R',nCols=1)
        vboxR = QtWidgets.QVBoxLayout()
        text=QtWidgets.QLabel('Right')
        text.setAlignment(QtCore.Qt.AlignCenter)
        text.setFont(QtGui.QFont("SansSerif", 18, QtGui.QFont.Bold) )
        vboxR.addWidget(text)
        vboxR.addWidget(self.resultTableRWidget)
        vboxR.addWidget(self.plotAreaR)
        
        #layout
        hboxPlot = QtWidgets.QHBoxLayout()
        hboxPlot.setAlignment(QtCore.Qt.AlignTop)
        hboxPlot.addLayout(vboxL)
        hboxPlot.addLayout(vboxR)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hboxPlot)
        self.setLayout(vbox)
        
    def updateTab(self):
        if self.data.hasLdata or self.data.hasRdata:
            self.applyTFAButton.setEnabled(True)
        else:
            self.applyTFAButton.setEnabled(False)
        pass

    def registerOptions(self,type):
        if type == 'estimatorType':
            self.estimatorType= estimatorTypeDict[self.sender().currentIndex()][0]
        if type == 'coheTresh':
            self.coherenceTreshold=self.sender().isChecked()
        if type == 'negativePhase':
            self.removeNegPhase=self.sender().isChecked()

    #synchronize signals
    def applyTFA(self):
        self.data.computeTFA(estimatorType=self.estimatorType)
        self.applyTFAButton.clearFocus()
        self.saveButton.setEnabled(True)
        
        #left side
        if self.data.hasLdata:
            self.plotData(side='L')
            self.fillTableResults(side='L')

        #right side
        if self.data.hasRdata:
            self.plotData(side='R')
            self.fillTableResults(side='R')

    
    #side:  'L'  or 'R'
    def fillTableResults(self,side='L'):
        
        #select data
        if side.upper()=='L':
            resultTable=self.resultTableLWidget
            TFAdata=self.data.TFA_L
        if side.upper()=='R':
            resultTable=self.resultTableRWidget
            TFAdata=self.data.TFA_R
        
        #gain
        avg = [TFAdata.getGainStatistics(freqRange=range,coherenceTreshold=self.coherenceTreshold)[0] for range in  ['VLF', 'LF', 'HF']]
        std = [TFAdata.getGainStatistics(freqRange=range,coherenceTreshold=self.coherenceTreshold)[1] for range in  ['VLF', 'LF', 'HF']]
        resultTable.setGain(avg)
        
        #phase
        avg = [TFAdata.getPhaseStatistics(freqRange=range,coherenceTreshold=False,removeNegativePhase=self.removeNegPhase)[0]*180/np.pi for range in  ['VLF', 'LF', 'HF']]
        std = [TFAdata.getPhaseStatistics(freqRange=range,coherenceTreshold=False,removeNegativePhase=self.removeNegPhase)[1]*180/np.pi for range in  ['VLF', 'LF', 'HF']]
        resultTable.setPhase(avg)
            
        #coherence
        avg = [TFAdata.getCoherenceStatistics(freqRange=range)[0] for range in  ['VLF', 'LF', 'HF']]
        std = [TFAdata.getCoherenceStatistics(freqRange=range)[1] for range in  ['VLF', 'LF', 'HF']]
        resultTable.setCoherence(avg)
            
    def saveTFA(self):
        self.parent().patientData=self.data
        fileExtension='.tf'  # include the dot!
        
        if self.data.hasLdata or self.data.hasRdata:
            defaultDir=os.path.dirname(self.data.fileName)
            baseName=os.path.splitext(os.path.basename(self.data.fileName))[0]
            resultFileName,_ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', defaultDir + '/' + baseName + fileExtension, 'Transfer function (*.tf) (*.tf)')
        
        if resultFileName:
            if self.data.hasLdata and self.data.hasRdata:
                self.data.TFA_L.save(fileName=resultFileName,sideLabel='L',freqRange='ALL',writeMode='w')
                self.data.TFA_R.save(fileName=resultFileName,sideLabel='R',freqRange='ALL',writeMode='a')
            else:
                if self.data.hasLdata:
                    self.data.TFA_L.save(fileName=resultFileName,sideLabel='L',freqRange='ALL',writeMode='w')
                if self.data.hasRdata:
                    self.data.TFA_R.save(fileName=resultFileName,sideLabel='R',freqRange='ALL',writeMode='a')

            if self.data.hasLdata:
                self.data.TFA_L.savePlot(fileNamePrefix=os.path.splitext(resultFileName)[0] + '_Left',fileType='png',figDpi=250,fontSize=6)
            if self.data.hasRdata:
                self.data.TFA_R.savePlot(fileNamePrefix=os.path.splitext(resultFileName)[0] + '_Right',fileType='png',figDpi=250,fontSize=6)

    #side:  'L'  or 'R'
    def plotData(self,side='L'):
        
        #select data
        if side.upper()=='L':
            plotArea=self.plotAreaL
            TFAdata=self.data.TFA_L
        if side.upper()=='R':
            plotArea=self.plotAreaR
            TFAdata=self.data.TFA_R

        #create plots
        if len(plotArea.axes)>0:
            plotArea.replot(plotNbr=0,yData=TFAdata.getGain(freqRange='FULL'))
            plotArea.replot(plotNbr=1,yData=TFAdata.getPhase(freqRange='FULL')*180/np.pi)
            plotArea.replot(plotNbr=2,yData=TFAdata.getCoherence(freqRange='FULL'))
        else:
            plotArea.addNewPlot(yData=[[TFAdata.getGain(freqRange='FULL'),pyQtConf['plotColors']['base'],'Gain']],yUnit='adim',title='Gain',logY=False)
            plotArea.addNewPlot(yData=[[TFAdata.getPhase(freqRange='FULL')*180/np.pi,pyQtConf['plotColors']['base'],'Phase']],yUnit='degree',title='Phase',logY=False)
            plotArea.addNewPlot(yData=[[TFAdata.getCoherence(freqRange='FULL'),pyQtConf['plotColors']['base'],'Coherence']],yUnit='adim.',title='Coherence',logY=False)

        #set limits
        _,_,coheMin,coheMax = TFAdata.getCoherenceStatistics(freqRange='ALL')
        _,_,gainMin,gainMax = TFAdata.getGainStatistics(freqRange='ALL',coherenceTreshold=False)
        _,_,phasMin,phasMax = TFAdata.getPhaseStatistics(freqRange='ALL',coherenceTreshold=False,removeNegativePhase=False)
        plotArea.setLimits(xlim=[ARsetup.freqRangeDic['VLF'][0],ARsetup.freqRangeDic['HF'][1]],
                                    ylim=[[gainMin,gainMax],[phasMin*180/np.pi,phasMax*180/np.pi],[coheMin,coheMax]])
            
        # draw avg drawAvgLines
        avg = [TFAdata.getGainStatistics(freqRange=range,coherenceTreshold=self.coherenceTreshold)[0] for range in  ['VLF', 'LF', 'HF']]
        plotArea.markAvgRanges(plotNbr=0,avgValues=avg)
        avg = [TFAdata.getPhaseStatistics(freqRange=range,coherenceTreshold=False,removeNegativePhase=self.removeNegPhase)[0]*180/np.pi for range in  ['VLF', 'LF', 'HF']]
        plotArea.markAvgRanges(plotNbr=1,avgValues=avg)
        avg = [TFAdata.getCoherenceStatistics(freqRange=range)[0] for range in  ['VLF', 'LF', 'HF']]
        plotArea.markAvgRanges(plotNbr=2,avgValues=avg)
        
