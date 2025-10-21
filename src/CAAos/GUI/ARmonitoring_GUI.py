#!/usr/bin/python

# -*- coding: utf-8 -*-

import os
import time

from PyQt5 import QtCore, QtGui, QtWidgets

from CAAos.core.patientMonitoring import patientMonitoring
from CAAos.GUI.toolbox_ARmonitoring.monitoringSetup import monitoringSetupWidget
from CAAos.GUI.toolbox_Preprocessing.artefactRemoval import artefactRemovalWidget
from CAAos.GUI.toolbox_Preprocessing.beat2beat import signalBeat2beatWidget
from CAAos.GUI.toolbox_Preprocessing.resampleCalibrate import resampleCalibrateWidget
from CAAos.GUI.toolbox_Preprocessing.RRmarks import signalRRmarksWidget
from CAAos.GUI.toolbox_Preprocessing.signalProps import signalPropsWidget
from CAAos.GUI.toolbox_Preprocessing.syncFilter import signalSyncFilterWidget

from CAAos.GUI.toolbox_ARanalysis.ARI import ARIWidget
from CAAos.GUI.toolbox_ARanalysis.ARIARMA import ARIARMAWidget
from CAAos.GUI.toolbox_ARanalysis.TFA import powerSpectrumWidget
from CAAos.GUI.toolbox_ARanalysis.TFA import TFAWidget
from CAAos.GUI.toolbox_ARanalysis.Mx import MxWidget

from CAAos.tools import tools



class ARmonitoring_GUI(QtWidgets.QWidget):
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

        self.closeJobAct = toolbar.addAction(QtGui.QIcon(iconSetDir + 'closeJob.png'), 'Close job', self.closeJob)
        self.closeJobAct.setEnabled(False)

        return toolbar

    def closeTool(self):
        self.parent().setWindowTitle(self.parent().name)
        self.parent().setWatermark()

        if self.data is not None:
            self.closeJob()
        self.close()

    def newJob(self):
        self.statusBar.showMessage('Creating a new Job.')
        if self.data is not None:
            self.closeJob()

        self.monitoringSamplingRate_Hz = 100.0
        self.patientName = 'Patient Name'
        self.birthdate = '31:01:1900'
        self.signalUpdateInterval_s = 2.0
        self.totalTime_s = 6 * 60.0  # 6 minutes
        self.simulatePatient = False
        self.simulatePatientPath = '../../data/CG24HG.EXP'

        self.monitoringSetup = monitoringSetupWidget(self, samplingRate_Hz=self.monitoringSamplingRate_Hz, patientName=self.patientName,
                                                     birthdate=self.birthdate, updateInterval_s = self.signalUpdateInterval_s,
                                                     totalTime_s=self.totalTime_s,simulatePatientPath = self.simulatePatientPath)
        self.monitoringSetup.signal_simulatePatient.connect(lambda: self.registerOptions('simulatePatient'))
        self.monitoringSetup.signal_simulatePatientPath.connect(lambda: self.registerOptions('simulatePatientPath'))
        self.monitoringSetup.signal_patientName.connect(lambda: self.registerOptions('patientName'))
        self.monitoringSetup.signal_birthDate.connect(lambda: self.registerOptions('birthdate'))
        self.monitoringSetup.signal_samplingRate.connect(lambda: self.registerOptions('sampingRate'))
        self.monitoringSetup.signal_updateInterval.connect(lambda: self.registerOptions('updateInterval'))
        self.monitoringSetup.signal_updateInterval.connect(lambda: self.registerOptions('totalTime'))
        self.monitoringSetup.signal_startMonitoring.connect(self.startMonitoring)

        self.closeJobAct.setEnabled(True)

    def closeJob(self):
        self.statusBar.showMessage('Closing job. Please wait...')
        self.fileName = None

        self.update_timer.stop()
        self.data.stopAcquisition()
        self.data = None

        self.tabWidget.close()

        self.parent().setWindowTitle(self.parent().name)


        self.monitoringSamplingRate_Hz = 100.0
        self.patientName = 'Patient Name'
        self.birthdate = '31:01:1900'
        self.signalUpdateInterval_s = 5.0
        self.simulatePatient = False
        self.simulatePatientPath = '../../data/CG24HG.EXP'

        self.closeJobAct.setEnabled(False)

        self.statusBar.showMessage('Job closed.')

    def registerOptions(self, type):
        if type == 'sampingRate':
            self.monitoringSamplingRate_Hz = self.sender().samplingRate_Hz
            #print(self.monitoringSamplingRate_Hz)
        if type == 'patientName':
            self.patientName = self.sender().patientName
            #print(self.patientName)
        if type == 'birthdate':
            self.birthdate = self.sender().birthdate
            #print(self.birthdate)
        if type == 'updateInterval':
            self.signalUpdateInterval_s = self.sender().updateInterval_s
            #print(self.signalUpdateInterval_s)
        if type == 'totalTime':
            self.totalTime_s = self.sender().totalTime_s
            #print(self.totalTime_s)
        if type == 'simulatePatient':
            self.simulatePatient = self.sender().simulatePatient
        if type == 'simulatePatientPath':
            self.simulatePatientPath = self.sender().simulatePatientPath

    def startMonitoring(self):

        self.monitoringSetup.close()
        self.data = patientMonitoring()

        self.parent().setWindowTitle(self.parent().name + ' - ' + 'Monitoring')

        if False:
            self.fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Select output data file', '',
                                                                     'All (.exp .dat .csv .PAR) (*.EXP *.exp *.DAT *.dat *.csv *.CSV *.PAR *.par)')
        else:
            #output file
            print('LOAD de arquivo abreviado! ver ARmonitoring_GUI.py, linha 146')

            self.fileName = '/home/fernando/servidor/programas/00_UFABC/ProjetoPosDocAngela/data/monitoring_%s_%s.EXP' % (tools.getCurrentTime(),
                                                                                                                          self.patientName)

        if not self.fileName:
            return

        # the ARO and PPO files are loaded inside this function
        self.data.newJob(outputFile=self.fileName)

        if self.simulatePatient:
            print('simulating patient: %s' % self.simulatePatientPath)
            self.data.startAcquisitionSimulationMode(self.simulatePatientPath, totalTime_sec=self.totalTime_s,
                                                     samplingRate_Hz=self.monitoringSamplingRate_Hz,
                                                     patientName=self.patientName, birthDate=self.birthdate)
        else:
            self.data.startAcquisition(totalTime_sec=self.totalTime_s, samplingRate_Hz=self.monitoringSamplingRate_Hz, patientName=self.patientName,
                                       birthDate=self.birthdate)

        # wait 110 seconds to allow the acquisition to start and the first data to be collected this is needed to avoid problems
        # with the first signal update, which is called in the next line, specially for ARI.
        tools.timed_wait(30, update_interval=5)

        self.data.initSignalUpdateTimer(interval_sec=self.signalUpdateInterval_s, updateAllData=True ,applyOperations=True,saveToFile=True)

        time.sleep(self.signalUpdateInterval_s+0.5) # wait one extra second to allow the first update to complete before updating the GUI
        self.createTabs()

        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(1000 * self.signalUpdateInterval_s)  # in milliseconds
        self.update_timer.setSingleShot(False)
        self.update_timer.timeout.connect(self.updateTabs)
        self.update_timer.start()

        # self.reloadJobAct.setEnabled(True)
        # self.closeJobAct.setEnabled(True)
        # self.saveJobAct.setEnabled(True)
        # self.importOpAct.setEnabled(True)
        # self.saveSigAct.setEnabled(True)
        # self.saveB2BAct.setEnabled(self.data.hasB2Bdata)
        # self.saveAllAct.setEnabled(True)

        self.statusBar.showMessage('Job created.')

    def createTabs(self):

        # tab of tools
        self.tabWidget = QtWidgets.QTabWidget()
        # self.tabWidget.setMaximumHeight(300)

        # signal Props
        self.signalProps = signalPropsWidget(self.data)
        self.tabWidget.addTab(self.signalProps, 'Labels/Types')
        #self.signalProps.setEnabled(False)
        #self.signalProps.updateTab()  # this update is needed since this tab is on the top at the begining

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

        # Power spectra estimation
        self.PSD = powerSpectrumWidget.powerSpectrumWidget(self.data)
        self.tabWidget.addTab(self.PSD, 'Power spectra density (PSD)')
        #self.PSD.updateTab()  # this update is needed because this tab is on the top at the begining

        # TFA
        self.TFA = TFAWidget.TFAWidget(self.data)
        self.tabWidget.addTab(self.TFA, 'Transfer function analysis (TFA)')

        # ARI
        self.ARI = ARIWidget.ARIWidget(self.data)
        self.tabWidget.addTab(self.ARI, 'Autoregulation index analysis (ARI)')

        if False:

            # ARI ARMA
            self.ARIARMA = ARIARMAWidget.ARIARMAWidget(self.data)
            self.tabWidget.addTab(self.ARIARMA, 'Autoregulation index analysis ARMA (ARI ARMA)')

            # Mx
            self.MX = MxWidget.MxWidget(self.data)
            self.tabWidget.addTab(self.MX, 'Mean Flow Index (nMx)')

        self.tabWidget.currentChanged.connect(self.updateTabs)
        self.vbox.addWidget(self.tabWidget)

    def updateTabs(self):
        # update tabs with new information

        current = self.tabWidget.currentIndex()

        # print( self.sender().currentIndex() )
        if current == 0:
            self.signalProps.updateTab()
        if current == 1:  # not artefact removal
            self.resample.updateTab()
        if current == 2:
            self.syncFilter.updateTab()
        if current == 3:
            self.artefactRemoval.updateTab()
        if current == 4:
            self.RRdetection.updateTab()
        if current == 5:
            self.beat2beat.updateTab()
        if current == 6:
            self.PSD.updateTab()
        if current == 7:
            self.TFA.updateTab()
        if current == 8:
            self.ARI.updateTab()
        if current == 9:
            self.ARIARMA.updateTab()
        if current == 10:
            self.MX.updateTab()

        # self.saveB2BAct.setEnabled(self.data.hasB2Bdata)
