#!/usr/bin/python

# -*- coding: utf-8 -*-
import os
import matplotlib as mpl

mpl.use('Agg')

from PyQt5 import QtGui, QtCore, QtWidgets
from caaos.GUI.preprocessing_GUI import preprocessing_GUI
from caaos.GUI.ARanalysis_GUI import ARanalysis_GUI
from caaos.GUI.ARmonitoring_GUI import ARmonitoring_GUI
from caaos.GUI.aboutCAAos_GUI import About
from caaos.tools import tools


class GuiMain(QtWidgets.QMainWindow):
    patientData = None

    def __init__(self):
        super().__init__()
        self.imageDir = tools.splitPath(os.path.abspath(__file__))[0] + 'images/'
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

        self.name = 'api Platform'
        self.setWindowTitle(self.name)

        self.setWatermark()

        self.show()

    # create actions

    def setWatermark(self):
        # create a label and add the logo
        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignCenter)
        pixmap = QtGui.QPixmap(self.imageDir + 'logo_800x591.png')  # .scaled(200, 200,
        # QtCore.Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

        # add transparency to the image
        effect = QtWidgets.QGraphicsOpacityEffect()
        label.setGraphicsEffect(effect)
        effect.setOpacity(0.4)

        self.setCentralWidget(label)

    def createActions(self):
        # Exit
        self.exitAct = QtWidgets.QAction(QtGui.QIcon(self.imageDir + 'icons/exit.png'), self.tr('E&xit'), self)
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

        # Autoregulation monitoring
        self.ARmonitoring = QtWidgets.QAction(self.tr('&Autoregulation monitoring'), self)
        self.ARmonitoring.setShortcut(self.tr('Ctrl+M'))
        self.ARmonitoring.setStatusTip(self.tr('Autoregulation monitoring'))
        self.ARmonitoring.triggered.connect(self.AutoregulationMonitoring)

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
        self.fileMenu.addAction(self.ARmonitoring)

        # menu Help
        self.fileMenu = self.menuBar().addMenu(self.tr('&Help'))
        self.fileMenu.addAction(self.aboutAct)

    def AutoregulationMonitoring(self):
        # builds central widget in the main window
        self.Editor = ARmonitoring_GUI(self.statusBar())
        self.setCentralWidget(self.Editor)

    def preProcessingData(self):
        # builds central widget in the main window
        self.Editor = preprocessing_GUI(self.statusBar())
        self.setCentralWidget(self.Editor)

    def AutoregulationAnalysis(self):
        # builds central widges in the main window
        self.Editor = ARanalysis_GUI(self.statusBar())
        self.setCentralWidget(self.Editor)

    def aboutCAAos(self):
        self.dialog = About(self)
