#!/usr/bin/python

# -*- coding: utf-8 -*-

import os
from PyQt5 import QtCore, QtWidgets
from patientData import patientData
from powerSpectrumWidget import powerSpectrumWidget
from TFAWidget import TFAWidget
          
class autoregulation_GUI(QtWidgets.QWidget):
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
        toolbar.addAction('Close file',self.closeFile)
        return toolbar      

    def closeTool(self):
        self.parent().setWindowTitle(self.parent().name)
        self.close()

    def openFile(self):
        
        if self.data is not None:
            self.closeFile()
        
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

    def reloadFile(self):
        
        try:
            filename=self.fileName
        except AttributeError:
            return  
        
        if self.data is not None:
            self.closeFile()

        self.fileName=filename
        
        if not self.fileName:
            return
        
        self.data=patientData(self.fileName)
        
        self.createTabs()   

    #close EXP file
    def closeFile(self):
        self.fileName=None
        self.data=None
        
        self.tabWidget.close()
        
        self.parent().setWindowTitle(self.parent().name)
        
    def createTabs(self):
        
        #tab of tools
        self.tabWidget = QtWidgets.QTabWidget()
        #self.tabWidget.setMaximumHeight(300)
        
        # Power spectra estimation
        self.PSD=powerSpectrumWidget(self.data)
        self.tabWidget.addTab(self.PSD,'Power spectra')

        # TFA
        self.TFA = TFAWidget(self.data)
        self.tabWidget.addTab(self.TFA,'Transfer function analysis')

        self.tabWidget.currentChanged.connect(self.updateTabs)
        self.vbox.addWidget(self.tabWidget)
        
    #update tabs with new information
    def updateTabs(self):

        #print( self.sender().currentIndex() )
        
        if self.sender().currentIndex() == 0:
            self.PSD.updateTab()
        if self.sender().currentIndex() == 1:
            self.TFA.updateTab()
