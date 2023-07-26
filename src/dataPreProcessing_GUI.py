#!/usr/bin/python

# -*- coding: utf-8 -*-

import os

from PyQt5 import QtCore, QtGui, QtWidgets

from artefactRemoval import artefactRemovalWidget
from beat2beat import signalBeat2beatWidget
from patientData import patientData
from resampleCalibrate import resampleCalibrateWidget
from RRmarks import signalRRmarksWidget
from signalProps import signalPropsWidget
from syncFilter import signalSyncFilterWidget


class dataPreProcessing_GUI(QtWidgets.QWidget):
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

        self.statusBar.showMessage('Ready.')

    def createToolbar(self):
        iconSetDir = './images/icons/'
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        stylesheet = 'QToolButton{padding: 0; margin: 0} QToolBar {background: rgb(200,200,200)}'
        toolbar.setStyleSheet(stylesheet)
        toolbar.setIconSize(QtCore.QSize(30, 30))

        self.closeAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'exitToolbox.png'), 'Close toolbox', self.closeTool)
        toolbar.addSeparator()
        self.newJobAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'newJob.png'), 'New job', self.newJob)
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
        # toolbar.addAction('Export operations', self.exportOperations)
        toolbar.addSeparator()
        self.saveSigAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'saveSIG.png'), 'Save Signals', self.saveSignals)
        self.saveSigAct.setEnabled(False)
        self.saveB2BAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'saveB2B.png'), 'Save beat-to-beat', self.saveB2B)
        self.saveB2BAct.setEnabled(False)
        self.saveAllAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'saveALL.png'), 'Save All', self.saveAll)
        self.saveAllAct.setEnabled(False)
        return toolbar

    def closeTool(self):
        self.parent().setWindowTitle(self.parent().name)
        self.parent().setWaterark()
        self.close()

    def newJob(self):
        self.statusBar.showMessage('Creating a new Job.')
        if self.data is not None:
            self.closeJob()

        if True:
            self.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select input data file', '',
                                                                     'All (.exp .dat .csv .PAR) (*.EXP *.exp *.DAT *.dat *.csv *.CSV *.PAR *.par)')
        else:
            print('LOAD de arquivo abreviado! ver dataPreProcessing_GUI.py, linha 64')
            self.fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG.EXP'
            self.fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/DPOC4CA1.PAR'

        if not self.fileName:
            return

        self.parent().setWindowTitle(self.parent().name + ' - ' + self.fileName)
        self.data = patientData(self.fileName, activeModule='preprocessing')
        self.createTabs()

        self.reloadJobAct.setEnabled(True)
        self.closeJobAct.setEnabled(True)
        self.saveJobAct.setEnabled(True)
        self.importOpAct.setEnabled(True)
        self.saveSigAct.setEnabled(True)
        self.saveB2BAct.setEnabled(self.data.hasB2Bdata)
        self.saveAllAct.setEnabled(True)

        self.statusBar.showMessage('Job created.')

    def loadJob(self):

        self.statusBar.showMessage('Loading job.')
        if self.data is not None:
            self.closeJob()

        if True:
            self.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select job file', '', 'Autoregulation jobs (*.job) (*.job)')
        else:
            print('LOAD de arquivo abreviado! ver dataPreProcessing_GUI.py, linha 85')
            self.fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/CG24HG_save.job'

        if not self.fileName:
            return

        self.statusBar.showMessage('Loading job. Please wait...')
        self.parent().setWindowTitle(self.parent().name + ' - ' + self.fileName)
        self.data = patientData(self.fileName, activeModule='preprocessing')
        self.createTabs()

        self.reloadJobAct.setEnabled(True)
        self.closeJobAct.setEnabled(True)
        self.saveJobAct.setEnabled(True)
        self.importOpAct.setEnabled(True)
        self.saveSigAct.setEnabled(True)
        self.saveB2BAct.setEnabled(self.data.hasB2Bdata)
        self.saveAllAct.setEnabled(True)

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
        self.data = patientData(self.fileName, activeModule='preprocessing')
        self.createTabs()

        self.reloadJobAct.setEnabled(True)
        self.closeJobAct.setEnabled(True)
        self.saveJobAct.setEnabled(True)
        self.importOpAct.setEnabled(True)
        self.saveSigAct.setEnabled(True)
        self.saveB2BAct.setEnabled(self.data.hasB2Bdata)
        self.saveAllAct.setEnabled(True)

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
        self.saveSigAct.setEnabled(False)
        self.saveB2BAct.setEnabled(False)
        self.saveAllAct.setEnabled(False)

        self.statusBar.showMessage('Job closed.')

    def importOperations(self):

        self.statusBar.showMessage('Importing operations.')
        if True:
            fileName_PPO, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select operations file', '', 'Preprocessing operations (.ppo) (*.ppo)')
        else:
            print('LOAD de arquivo abreviado! ver dataPreProcessing_GUI.py, linha 127')
            fileName_PPO = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/basic_SetLabel.ppo'

        if not fileName_PPO:
            return

        self.statusBar.showMessage('Importing operations. Please wait...')
        self.data.importOperations(self.data.dirName + os.path.basename(fileName_PPO), elemPosition=None, runOperations=True)

        self.saveB2BAct.setEnabled(self.data.hasB2Bdata)

        self.statusBar.showMessage('Operations imported.')

    def createTabs(self):

        # tab of tools
        self.tabWidget = QtWidgets.QTabWidget()
        # self.tabWidget.setMaximumHeight(300)

        # signal Props
        self.signalProps = signalPropsWidget(self.data)
        self.tabWidget.addTab(self.signalProps, 'Labels/Types')
        self.signalProps.updateTab()  # this update is needed since this tab is on the top at the begining

        # resample
        self.resample = resampleCalibrateWidget(self.data)
        self.tabWidget.addTab(self.resample, 'Resample/Calibrate')

        # sync & filter
        self.syncFilter = signalSyncFilterWidget(self.data)
        self.tabWidget.addTab(self.syncFilter, 'Sync/Filter')

        # artefact remmoval
        self.artefactRemoval = artefactRemovalWidget(self.data)
        self.tabWidget.addTab(self.artefactRemoval, 'Artefact removal')

        # RR marks
        self.RRdetection = signalRRmarksWidget(self.data)
        self.tabWidget.addTab(self.RRdetection, 'RR detection')

        # beat 2 beat
        self.beat2beat = signalBeat2beatWidget(self.data)
        self.tabWidget.addTab(self.beat2beat, 'Beat to beat')
        self.beat2beat.signal_apply.connect(lambda: self.saveB2BAct.setEnabled(True))

        self.tabWidget.currentChanged.connect(self.updateTabs)
        self.vbox.addWidget(self.tabWidget)

    def updateTabs(self):
        # update tabs with new information

        # print( self.sender().currentIndex() )
        if self.sender().currentIndex() == 0:
            self.signalProps.updateTab()
        if self.sender().currentIndex() == 1:  # not artefact removal
            self.resample.updateTab()
        if self.sender().currentIndex() == 2:
            self.syncFilter.updateTab()
        if self.sender().currentIndex() == 3:
            self.artefactRemoval.updateTab()
        if self.sender().currentIndex() == 4:
            self.RRdetection.updateTab()
        if self.sender().currentIndex() == 5:
            self.beat2beat.updateTab()

        self.saveB2BAct.setEnabled(self.data.hasB2Bdata)

    def saveAll(self):
        [fileOut, format] = self.saveSignals()
        filePrefix = os.path.splitext(fileOut)[0]
        if self.data.hasB2Bdata:
            self.saveB2B(fileName=filePrefix + '.b2b', fileFormat=format)
        self.saveJob(fileName=filePrefix + '.job')

    def saveSignals(self, fileName=None, fileFormat=None):

        self.statusBar.showMessage('Saving signals. Please wait...')
        # fileFormat: 'csv', 'numpy'.  used only if fileName is not None
        self.parent().patientData = self.data
        fileExtension = '.sig'

        if fileName is None:
            defaultDir = os.path.dirname(self.fileName)
            baseName = os.path.splitext(os.path.basename(self.fileName))[0]

            resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save signal data as',
                                                                                   defaultDir + '/' + baseName + fileExtension,
                                                                                   'Signals (.sig) (*.sig);;'
                                                                                   'CSV (.csv) (*.csv);;'
                                                                                   'Numpy (.npy) (*npy);;')
            if resultFileName:
                if '.csv' in selectedFilter:
                    fileFormat = 'csv'
                if '.npy' in selectedFilter:
                    fileFormat = 'numpy'
                if '.sig' in selectedFilter:
                    fileFormat = 'simple_text'

                self.data.saveSIG(resultFileName, channelList=None, format=fileFormat, register=True)
                self.statusBar.showMessage('Signals saved.')
                return [resultFileName, fileFormat]
        else:
            self.data.saveSIG(fileName, channelList=None, format=fileFormat, register=True)
            self.statusBar.showMessage('Signals saved.')
            return [fileName, fileFormat]

    def saveB2B(self, fileName=None, fileFormat=None):

        self.statusBar.showMessage('Saving beat-to-beat data.')
        # fileFormat: 'csv', 'numpy', 'simple_text'.  used only if fileName is not None
        self.parent().patientData = self.data
        fileExtension = '.b2b'

        if self.data.hasB2Bdata:
            temp = type(self.data.signals[0].beat2beatData)  # checks if there is B2B data
            if fileName is None:
                defaultDir = os.path.dirname(self.fileName)
                baseName = os.path.splitext(os.path.basename(self.fileName))[0]

                resultFileName, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save beat-top-beat data as',
                                                                                       defaultDir + '/' + baseName + fileExtension,
                                                                                       'Beat-to-beat (.b2b) (*.b2b);;'
                                                                                       'CSV (.csv) (*.csv);;'
                                                                                       'Numpy (.npy) (*npy);;')
                if resultFileName:
                    if 'CSV' in selectedFilter:
                        fileFormat = 'csv'
                    if 'Numpy' in selectedFilter:
                        fileFormat = 'numpy'
                    if '.b2b' in selectedFilter:
                        fileFormat = 'simple_text'

                    self.statusBar.showMessage('Saving beat-to-beat data. Please wait...')
                    self.data.saveB2B(resultFileName, channelList=None, format=fileFormat, register=True)
                    self.statusBar.showMessage('Beat-to-beat data saved.')

                    return [resultFileName, fileFormat]
            else:
                self.statusBar.showMessage('Saving beat-to-beat data. Please wait...')
                self.data.saveB2B(fileName, channelList=None, format=fileFormat, register=True)
                self.statusBar.showMessage('Beat-to-beat data saved.')
                return [fileName, fileFormat]
        else:
            print('WARNING: Case has no B2B data yet. Ignoring save...')
            self.statusBar.showMessage('WARNING: Case has no B2B data yet. Ignoring save...')
            return None

    def saveJob(self, fileName=None):

        self.statusBar.showMessage('Saving job data.')
        choice = QtWidgets.QMessageBox.question(self, '', 'Merge operations into the file?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
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
