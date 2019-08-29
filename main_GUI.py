#!/usr/bin/python

# -*- coding: utf-8 -*-

import sys
if sys.version_info.major == 2:
    sys.stdout.write("Sorry! This program requires Python 3.x\n")
    sys.exit(1)
from PyQt5 import QtGui,QtCore,QtWidgets
from dataPreProcessing_GUI import dataPreProcessing_GUI
from autoregulation_GUI import autoregulation_GUI



class GuiMain(QtWidgets.QMainWindow):
    
    patientData=None
    
    def __init__(self):
        super(GuiMain, self).__init__()
        self.initUI()
        
    def initUI(self):
        
        # status bar
        self.statusBar()
        #menu actions
        self.createActions()
        #menubar
        menubar = self.createMenus()

        # screen size and position
        self.resize(1400, 900)
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        self.name='openCARbox'
        self.setWindowTitle(self.name)
        self.show()
    
    # create actions
    def createActions(self):
        # Exit
        self.exitAct = QtWidgets.QAction(QtGui.QIcon(self.tr("./images/exit.png")),self.tr("E&xit"), self)
        self.exitAct.setShortcut(self.tr("Ctrl+Q"))
        self.exitAct.setStatusTip(self.tr("Exit the application"))
        self.exitAct.triggered.connect(self.close)
        
        # preprocessing
        self.preProcessingAct = QtWidgets.QAction(self.tr("&Preprocessing"), self)
        self.preProcessingAct.setShortcut(self.tr("Ctrl+P"))
        self.preProcessingAct.setStatusTip(self.tr("Data Preprocessing tools"))
        self.preProcessingAct.triggered.connect(self.preProcessingData)
        
        # Autoregulation tools
        self.ARnalysisAct = QtWidgets.QAction(self.tr("&Autoregulation analysis"), self)
        self.ARnalysisAct.setShortcut(self.tr("Ctrl+T"))
        self.ARnalysisAct.setStatusTip(self.tr("Autoregulation tools"))
        self.ARnalysisAct.triggered.connect(self.AutoregulationAnalysis)
        
        
                
    # build menus
    def createMenus(self):
        # menu File
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.exitAct)
        
        # menu Editor
        self.fileMenu = self.menuBar().addMenu(self.tr("T&ools"))
        self.fileMenu.addAction(self.preProcessingAct)
        self.fileMenu.addAction(self.ARnalysisAct)

    def preProcessingData(self):
        #builds central widges in the main window
        self.Editor = dataPreProcessing_GUI()
        self.setCentralWidget(self.Editor)
        
    def AutoregulationAnalysis(self):
        #builds central widges in the main window
        self.Editor = autoregulation_GUI()
        self.setCentralWidget(self.Editor)
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('./images/logo_32x32.png'))
    ex = GuiMain()
    sys.exit(app.exec_())  


