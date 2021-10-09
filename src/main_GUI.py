#!/usr/bin/python

# -*- coding: utf-8 -*-
import platform
import sys


import matplotlib as mpl
mpl.use('Agg')

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

from PyQt5 import QtGui, QtCore, QtWidgets
from dataPreProcessing_GUI import dataPreProcessing_GUI
from autoregulation_GUI import autoregulation_GUI
from aboutCAAos import About


class GuiMain(QtWidgets.QMainWindow):
    patientData = None

    def __init__(self):
        super(GuiMain, self).__init__()
        self.initUI()

    def initUI(self):
        # status bar
        self.statusBar()

        # menu actions
        self.createActions()

        # menubar
        self.createMenus()

        # screen size and position
        self.resize(1400, 900)
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.name = 'CAAos Platform'
        self.setWindowTitle(self.name)

        self.setWaterark()

        self.show()

    # create actions

    def setWaterark(self):
        # create a label and add the logo
        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignCenter)
        pixmap = QtGui.QPixmap('./images/logo_800x591.png')  # .scaled(200, 200, QtCore.Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

        # add transparecy to the image
        effect = QtWidgets.QGraphicsOpacityEffect()
        label.setGraphicsEffect(effect)
        effect.setOpacity(0.4)

        self.setCentralWidget(label)

    def createActions(self):
        # Exit
        self.exitAct = QtWidgets.QAction(QtGui.QIcon('./images/exit.png'), self.tr('E&xit'), self)
        self.exitAct.setShortcut(self.tr('Ctrl+Q'))
        self.exitAct.setStatusTip(self.tr('Exit the application'))
        self.exitAct.triggered.connect(self.close)

        # preprocessing
        self.preProcessingAct = QtWidgets.QAction(self.tr('&Preprocessing'), self)
        self.preProcessingAct.setShortcut(self.tr('Ctrl+P'))
        self.preProcessingAct.setStatusTip(self.tr('Data Preprocessing tools'))
        self.preProcessingAct.triggered.connect(self.preProcessingData)

        # Autoregulation tools
        self.ARnalysisAct = QtWidgets.QAction(self.tr('&Autoregulation analysis'), self)
        self.ARnalysisAct.setShortcut(self.tr('Ctrl+T'))
        self.ARnalysisAct.setStatusTip(self.tr('Autoregulation tools'))
        self.ARnalysisAct.triggered.connect(self.AutoregulationAnalysis)

        # about
        self.aboutAct = QtWidgets.QAction(self.tr('&About'), self)
        self.aboutAct.triggered.connect(self.aboutCAAos)

    # build menus
    def createMenus(self):
        # menu File
        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.fileMenu.addAction(self.exitAct)

        # menu Editor
        self.fileMenu = self.menuBar().addMenu(self.tr('T&oolboxes'))
        self.fileMenu.addAction(self.preProcessingAct)
        self.fileMenu.addAction(self.ARnalysisAct)

        # menu Help
        self.fileMenu = self.menuBar().addMenu(self.tr('&Help'))
        self.fileMenu.addAction(self.aboutAct)

    def preProcessingData(self):
        # builds central widget in the main window
        self.Editor = dataPreProcessing_GUI(self.statusBar())
        self.setCentralWidget(self.Editor)

    def AutoregulationAnalysis(self):
        # builds central widges in the main window
        self.Editor = autoregulation_GUI(self.statusBar())
        self.setCentralWidget(self.Editor)

    def aboutCAAos(self):
        self.dialog = About(self)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #print(QtWidgets.QStyleFactory.keys())

    if platform.system() == 'Windows':
        # windows: ['windowsvista', 'Windows', 'Fusion']
        app.setStyle('Windows')

    if platform.system() == 'Linux':
        # linux: ['Breeze', 'Oxygen', 'Windows', 'Fusion']
        app.setStyle('Breeze')

    if platform.system() == 'Darwin':  # Mac
        # macintosh: ['macintosh', 'Windows', 'Fusion']
        app.setStyle('macintosh')

    app.setWindowIcon(QtGui.QIcon('./images/logo_32x32.png'))
    ex = GuiMain()
    sys.exit(app.exec_())
