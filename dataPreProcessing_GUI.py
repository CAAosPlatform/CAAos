#!/usr/bin/python

# -*- coding: utf-8 -*-

import os
from PyQt5 import QtCore, QtWidgets
from patientData import patientData
from signalProps import signalPropsWidget
from syncFilter import signalSyncFilterWidget
from artefactRemoval import artefactRemovalWidget
from resampleCalibrate import resampleCalibrateWidget
from RRmarks import signalRRmarksWidget
from beat2beat import signalBeat2beatWidget
          
class dataPreProcessing_GUI(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.data=None
        self.initUI()
                
    def initUI(self):
      
        #layout to add toolbar and the layouts
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)

        self.toolbar = self.createToolbar()
        self.vbox.addWidget(self.toolbar)
        
        self.setLayout(self.vbox)
        
    #create toolbar
    def createToolbar(self):        
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setStyleSheet("QToolBar {background: rgb(200,200,200)}")
        toolbar.addAction('Close',self.closeTool)
        toolbar.addAction('Open file',self.openFile)
        toolbar.addAction('Reload file',self.reloadFile)
        toolbar.addAction('Close file',self.closeEXPfile)
        toolbar.addAction('Save All',self.saveAll)
        toolbar.addAction('Save Operations',self.saveOperations)
        toolbar.addAction('Save Signals',self.saveSignals)
        toolbar.addAction('Save beat-to-beat',self.saveB2B)
        return toolbar      
    
    def closeTool(self):
        self.parent().setWindowTitle(self.parent().name)
        self.close()
        
    def openFile(self):
        
        if self.data is not None:
            self.closeEXPfile()
        
        if True:
            self.fileName,_ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select input file','','all (*.EXP *.exp  *.DAT *.dat *.PPO *.ppo);;Signal data (.exp .dat) (*.EXP *.exp  *.DAT *.dat);;Preprocessing operations (.ppo) (*.PPO *.ppo)')
        else:
            print('LOAD de arquivo abreviado! ver loadData_Gui.py, linha 94')
            self.fileName='/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.ppo'
        
        if not self.fileName:
            return

        self.parent().setWindowTitle(self.parent().name + ' - ' + self.fileName)
        
        self.data=patientData(self.fileName)
        
        self.createTabs()
        
    #open EXP file
    def reloadFile(self):
        
        try:
            filename=self.fileName
        except AttributeError:
            return  
        
        if self.data is not None:
            self.closeEXPfile()

        self.fileName=filename
        
        if not self.fileName:
            return
        
        self.data=patientData(self.fileName)
        
        self.createTabs()   
        
    #close EXP file
    def closeEXPfile(self):
        self.fileName=None
        self.data=None
        
        self.tabWidget.close()
        
        self.parent().setWindowTitle(self.parent().name)
            
    def createTabs(self):
        
        #tab of tools
        self.tabWidget = QtWidgets.QTabWidget()
        #self.tabWidget.setMaximumHeight(300)
        
        # signal Props
        self.signalProps=signalPropsWidget(self.data)
        self.tabWidget.addTab(self.signalProps,'Labels/Types')

        #resample
        self.resample = resampleCalibrateWidget(self.data)
        self.tabWidget.addTab(self.resample,'Resample/Calibrate')  
            
        # sync & filter
        self.syncFilter=signalSyncFilterWidget(self.data) 
        self.tabWidget.addTab(self.syncFilter,'Sync/Filter')

        # artefact remmoval
        self.artefactRemoval = artefactRemovalWidget(self.data)
        self.tabWidget.addTab(self.artefactRemoval,'Artefact removal')
        
        # RR marks
        self.RRdetection = signalRRmarksWidget(self.data)
        self.tabWidget.addTab(self.RRdetection,'RR detection')
        
        # beat 2 beat
        self.beat2beat = signalBeat2beatWidget(self.data)
        self.tabWidget.addTab(self.beat2beat,'Beat to beat')
            
            
        self.tabWidget.currentChanged.connect(self.updateTabs)
        self.vbox.addWidget(self.tabWidget)
        
    #update tabs with new information
    def updateTabs(self):

        #print( self.sender().currentIndex() )
        
        if self.sender().currentIndex() == 0:
            self.signalProps.updateTab()
        if self.sender().currentIndex() == 1: # not artefact removal
            self.resample.updateTab()
        if self.sender().currentIndex() == 2:
            self.syncFilter.updateTab()
        if self.sender().currentIndex() == 3:
            self.artefactRemoval.updateTab()
        if self.sender().currentIndex() == 4:
            self.RRdetection.updateTab()
        if self.sender().currentIndex() == 5:
            self.beat2beat.updateTab()

    def saveAll(self):
        fileOut=self.saveSignals()
        filePrefix=os.path.splitext(fileOut)[0]
        self.saveB2B(fileName=filePrefix + '.b2b')
        self.saveOperations(fileName=filePrefix + '.ppo')
        
    def saveSignals(self,fileName=None):
        self.parent().patientData=self.data
        fileExtension='.sig'  # include the dot!
        
        if fileName is None:
            defaultDir=os.path.dirname(self.fileName)
            baseName=os.path.splitext(os.path.basename(self.fileName))[0]
            
            resultFileName,_ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', defaultDir + '/' + baseName + fileExtension, 'Signals (.sig) (*.sig)')
            if resultFileName:
                self.data.saveSignals(resultFileName,channelList=None)
                    
            return resultFileName
        else:
            self.data.saveSignals(fileName,channelList=None)
        return fileName

    def saveB2B(self,fileName=None):
        self.parent().patientData=self.data
        fileExtension='.b2b'  # include the dot!
        
        try:
            temp=type(self.data.signals[0].beat2beatData)
            if fileName is None:
                defaultDir=os.path.dirname(self.fileName)
                baseName=os.path.splitext(os.path.basename(self.fileName))[0]
                
                resultFileName,_ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', defaultDir + '/' + baseName + fileExtension, 'Beat to Beat (*.b2b) (*.b2b)')
                if resultFileName:
                    self.data.saveBeat2beat(resultFileName,channelList=None)
                    
                return resultFileName
            else:
                self.data.saveBeat2beat(fileName,channelList=None)
                return fileName
    
        except AttributeError:
            return None
        
    def saveOperations(self,fileName=None):
        self.parent().patientData=self.data
        fileExtension='.ppo'  # include the dot!
        
        if fileName is None:
            defaultDir=os.path.dirname(self.fileName)
            baseName=os.path.splitext(os.path.basename(self.fileName))[0]
            
            resultFileName,_ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', defaultDir + '/' + baseName + fileExtension, 'Preprocessing operations (*.ppo) (*.ppo)')
            if resultFileName:
                self.data.saveOperations(resultFileName)
                    
            return resultFileName
        else:
            self.data.saveOperations(fileName)
            return fileName

