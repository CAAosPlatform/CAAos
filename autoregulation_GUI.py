#!/usr/bin/python

# -*- coding: utf-8 -*-

import os

from PyQt5 import QtCore, QtGui, QtWidgets

from ARIWidget import ARIWidget
from patientData import patientData
from powerSpectrumWidget import powerSpectrumWidget
from TFAWidget import TFAWidget


class autoregulation_GUI(QtWidgets.QWidget):
    def __init__(self, statusBar):
        QtWidgets.QWidget.__init__(self)
        self.statusBar = statusBar
        self.data = None
        self.initUI()

    def initUI(self):

        # layout to add toolbar and the layouts
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)

        self.toolbar = self.createToolbar()
        self.vbox.addWidget(self.toolbar)

        self.setLayout(self.vbox)

    def createToolbar(self):
        iconSetDir = './images/icons/'
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        stylesheet = 'QToolButton{padding: 0; margin: 0} QToolBar {background: rgb(200,200,200)}'
        toolbar.setStyleSheet(stylesheet)
        toolbar.setIconSize(QtCore.QSize(30, 30))

        self.closeAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'exitToolbox.png'), 'Close toolbox', self.closeTool)
        toolbar.addSeparator()
        self.loadJobAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'loadJob.png'), 'Load job', self.loadJob)
        self.reloadJobAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'reloadJob.png'), 'Reload job', self.reloadJob)
        self.reloadJobAct.setEnabled(False)
        self.closeJobAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'closeJob.png'), 'Close job', self.closeJob)
        self.closeJobAct.setEnabled(False)
        self.saveJobAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'saveJob.png'), 'Save Job', self.saveJob)
        self.saveJobAct.setEnabled(False)
        toolbar.addSeparator()

        self.importOpAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'importOP.png'), 'Import operations', self.importOperations)
        self.importOpAct.setEnabled(False)
        return toolbar

    def closeTool(self):
        self.parent().setWindowTitle(self.parent().name)
        self.parent().setWaterark()
        self.close()

    def loadJob(self):

        self.statusBar.showMessage('Loading job.')
        if self.data is not None:
            self.closeJob()

        if True:
            self.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select input data file', '', 'Autoregulation jobs (*.job) (*.job)')
        else:
            print('LOAD de arquivo abreviado! ver autoregulation_GUI.py, linha 64')
            self.fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG_AR.job'

        if not self.fileName:
            return

        self.statusBar.showMessage('Loading job. Please wait...')
        self.parent().setWindowTitle(self.parent().name + ' - ' + self.fileName)
        self.data = patientData(self.fileName, activeModule='ARanalysis')
        self.createTabs()

        self.reloadJobAct.setEnabled(True)
        self.closeJobAct.setEnabled(True)
        self.saveJobAct.setEnabled(True)
        self.importOpAct.setEnabled(True)

        self.statusBar.showMessage('Job loaded.')

    def reloadJob(self):

        try:
            filename = self.fileName
        except AttributeError:
            return

        if self.data is not None:
            self.closeJob()

        self.fileName = filename

        if not self.fileName:
            return

        self.statusBar.showMessage('Reloading job. Please wait...')
        self.data = patientData(self.fileName, activeModule='ARanalysis')
        self.createTabs()

        self.reloadJobAct.setEnabled(True)
        self.closeJobAct.setEnabled(True)
        self.saveJobAct.setEnabled(True)
        self.importOpAct.setEnabled(True)

        self.statusBar.showMessage('Job reloaded.')

    def closeJob(self):
        self.statusBar.showMessage('Closing job. Please wait...')
        self.fileName = None
        self.data = None

        self.tabWidget.close()

        self.parent().setWindowTitle(self.parent().name)

        self.reloadJobAct.setEnabled(False)
        self.closeJobAct.setEnabled(False)
        self.saveJobAct.setEnabled(False)
        self.importOpAct.setEnabled(False)

        self.statusBar.showMessage('Job closed.')

    def importOperations(self):

        self.statusBar.showMessage('Importing operations.')
        if True:
            fileName_ARO, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select operations file', '', 'Autoregulation operations (.aro) (*.aro)')
        else:
            print('LOAD de arquivo abreviado! ver autoregulation_GUI.py, linha 127')
            fileName_ARO = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/basic_SetLabel.aro'

        if not fileName_ARO:
            return

        self.statusBar.showMessage('Importing operations. Please wait...')
        self.data.importOperations(self.data.dirName + os.path.basename(fileName_ARO), elemPosition=None, runOperations=True)

        self.statusBar.showMessage('Operations imported.')

    def createTabs(self):

        # tab of tools
        self.tabWidget = QtWidgets.QTabWidget()
        # self.tabWidget.setMaximumHeight(300)

        # Power spectra estimation
        self.PSD = powerSpectrumWidget(self.data)
        self.tabWidget.addTab(self.PSD, 'Power spectra density (PSD)')
        self.PSD.updateTab()  # this update is needed since this tab is on the top at the begining

        # TFA
        self.TFA = TFAWidget(self.data)
        self.tabWidget.addTab(self.TFA, 'Transfer function analysis (TFA)')

        # ARI
        self.ARI = ARIWidget(self.data)
        self.tabWidget.addTab(self.ARI, 'Autoregulation index analysis (ARI)')

        self.tabWidget.currentChanged.connect(self.updateTabs)
        self.vbox.addWidget(self.tabWidget)

    # update tabs with new information
    def updateTabs(self):

        # print( self.sender().currentIndex() )

        if self.sender().currentIndex() == 0:
            self.PSD.updateTab()
        if self.sender().currentIndex() == 1:
            self.TFA.updateTab()
        if self.sender().currentIndex() == 2:
            self.ARI.updateTab()

    def saveJob(self, fileName=None):

        self.statusBar.showMessage('Saving job data.')
        choice = QtGui.QMessageBox.question(self, '', 'Merge operations into the file?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            merge = True
        else:
            merge = False

        self.parent().patientData = self.data
        fileExtension = '.job'  # include the dot!

        if fileName is None:
            defaultDir = os.path.dirname(self.fileName)
            baseName = os.path.splitext(os.path.basename(self.fileName))[0]

            defaultName = defaultDir + '/' + baseName + fileExtension
            resultFileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', defaultName, 'Autoregulation jobs (*.job) (*.job)')
            if resultFileName:
                self.data.saveJob(resultFileName, mergeImported=merge)
                self.statusBar.showMessage('Job saved.')

            return resultFileName
        else:
            self.data.saveJob(fileName, mergeImported=merge)
            self.statusBar.showMessage('Job saved.')
            return fileName
