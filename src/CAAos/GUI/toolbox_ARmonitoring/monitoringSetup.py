#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from CAAos.GUI.common import signalTabWidget
from CAAos.GUI.common import signalPlotWidget
from CAAos.GUI.toolbox_Preprocessing import signalProps

class monitoringSetupWidget(QtWidgets.QMainWindow):

    signal_patientName = QtCore.pyqtSignal()
    signal_birthDate = QtCore.pyqtSignal()
    signal_samplingRate = QtCore.pyqtSignal()
    signal_startMonitoring = QtCore.pyqtSignal()
    signal_updateInterval = QtCore.pyqtSignal()
    signal_totalTime = QtCore.pyqtSignal()
    signal_simulatePatient = QtCore.pyqtSignal()
    signal_simulatePatientPath = QtCore.pyqtSignal()

    def __init__(self, parent=None, samplingRate_Hz=100.0, patientName='Patient Name', birthdate='31:01:1900', updateInterval_s=5.0,
                 totalTime_s=10*60, simulatePatientPath=None):
        super().__init__(parent)

        self.samplingRate_Hz = samplingRate_Hz
        self.patientName = patientName
        self.birthdate = birthdate
        self.updateInterval_s = updateInterval_s
        self.totalTime_s = totalTime_s
        self.simulatePatientPath = simulatePatientPath
        self.initUI()

    def initUI(self):
        # Create a new window
        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setWindowTitle('Monitoring setup')

        # screen size and position
        self.resize(500, 600)
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Create layout
        vbox = QtWidgets.QVBoxLayout(self.centralwidget)
        formLayout = QtWidgets.QFormLayout()
        vbox.addLayout(formLayout)

        # simulate patient
        default = False
        self.simulatePatient = default
        simulatePatient = QtWidgets.QCheckBox('', self)
        simulatePatient.setChecked(self.simulatePatient)
        simulatePatient.stateChanged.connect(lambda: self.registerOptions('simulatePatient'))
        formLayout.addRow('Simulate patient', simulatePatient)

        # simulate patient path
        self.simulatePatientPathWidget = QtWidgets.QLineEdit()
        self.simulatePatientPathWidget.setText(self.simulatePatientPath)
        self.simulatePatientPathWidget.setFixedWidth(190)
        self.simulatePatientPathWidget.editingFinished.connect(lambda: self.registerOptions('simulatePatientPath'))
        self.simulatePatientPathWidget.returnPressed.connect(lambda: self.registerOptions('simulatePatientPath'))
        self.simulatePatientPathWidget.setEnabled(True)
        formLayout.addRow('Simulate patient path', self.simulatePatientPathWidget)


        # sampling rate (Hz)
        samplingRateWidget = QtWidgets.QDoubleSpinBox()
        samplingRateWidget.setRange(50, 1000)
        samplingRateWidget.setDecimals(0)
        samplingRateWidget.setSingleStep(50)
        samplingRateWidget.setFixedWidth(130)
        samplingRateWidget.setValue(self.samplingRate_Hz)
        samplingRateWidget.valueChanged.connect(lambda: self.registerOptions('samplingRate'))
        formLayout.addRow('Sampling rate (Hz)', samplingRateWidget)

        # patient name
        patientNameWidget = QtWidgets.QLineEdit()
        patientNameWidget.setText(self.patientName)
        patientNameWidget.setFixedWidth(190)
        patientNameWidget.editingFinished.connect(lambda: self.registerOptions('patientName'))
        patientNameWidget.returnPressed.connect(lambda: self.registerOptions('patientName'))
        # patientNameWidget.textChanged.connect(lambda: self.registerOptions('patName'))
        formLayout.addRow('Patient Name', patientNameWidget)

        # patient birthdate
        birthdateWidget = QtWidgets.QLineEdit()
        birthdateWidget.setText(self.birthdate)
        birthdateWidget.setFixedWidth(130)
        birthdateWidget.editingFinished.connect(lambda: self.registerOptions('birthDate'))
        birthdateWidget.returnPressed.connect(lambda: self.registerOptions('birthDate'))
        # birthdateWidget.textChanged.connect(lambda: self.registerOptions('birthDate'))
        formLayout.addRow('Birthdate', birthdateWidget)

        # update interval (s)
        samplingRateWidget = QtWidgets.QDoubleSpinBox()
        samplingRateWidget.setRange(1, 60)
        samplingRateWidget.setDecimals(2)
        samplingRateWidget.setSingleStep(1)
        samplingRateWidget.setFixedWidth(130)
        samplingRateWidget.setValue(self.updateInterval_s)
        samplingRateWidget.valueChanged.connect(lambda: self.registerOptions('updateInterval'))
        formLayout.addRow('Signal update interval (s)', samplingRateWidget)

        # total time (s)
        totalTimeWidget = QtWidgets.QDoubleSpinBox()
        totalTimeWidget.setRange(1, 60)
        totalTimeWidget.setDecimals(2)
        totalTimeWidget.setSingleStep(1)
        totalTimeWidget.setFixedWidth(130)
        totalTimeWidget.setValue(self.totalTime_s/60)  # convert to minutes for display
        totalTimeWidget.valueChanged.connect(lambda: self.registerOptions('totalTime_s'))
        formLayout.addRow('Total Acquisition time (min)', totalTimeWidget)
        # Add a submit button
        startButtonWidget = QtWidgets.QPushButton('Start monitoring')
        startButtonWidget.setFixedWidth(100)
        startButtonWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        startButtonWidget.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        startButtonWidget.clicked.connect(self.startMonitoring)
        formLayout.addWidget(startButtonWidget)

        # Set the layout to the window
        self.setLayout(vbox)

        # Show the window
        self.show()

    def registerOptions(self, type):
        if type == 'samplingRate':
            self.samplingRate_Hz = self.sender().value()
            self.signal_samplingRate.emit()
        if type == 'patientName':
            self.patientName = self.sender().text()
            self.signal_patientName.emit()
        if type == 'birthDate':
            self.birthdate = self.sender().text()
            self.signal_birthDate.emit()
        if type == 'updateInterval':
            self.updateInterval_s = self.sender().value()
            self.signal_updateInterval.emit()
        if type == 'totalTime_s':
            self.totalTime_s = self.sender().value()*60  # convert to seconds
            self.signal_totalTime.emit()
        if type == 'simulatePatient':
            self.simulatePatient = self.sender().isChecked()
            if self.simulatePatient:
                self.simulatePatientPathWidget.setEnabled(True)
            else:
                self.simulatePatientPathWidget.setEnabled(False)
            self.signal_simulatePatient.emit()
        if type == 'simulatePatientPath':
            self.simulatePatientPath = self.sender().text()
            self.signal_simulatePatientPath.emit()



    def startMonitoring(self):
        self.signal_startMonitoring.emit()

