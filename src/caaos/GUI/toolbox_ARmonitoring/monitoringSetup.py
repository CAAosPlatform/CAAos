#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from caaos.GUI.common import signalTabWidget
from caaos.GUI.common import signalPlotWidget
from caaos.GUI.toolbox_Preprocessing import signalProps

class monitoringSetupWidget(QtWidgets.QMainWindow):

    signal_patientName = QtCore.pyqtSignal()
    signal_birthDate = QtCore.pyqtSignal()
    signal_samplingRate = QtCore.pyqtSignal()
    signal_startMonitoring = QtCore.pyqtSignal()
    signal_updateInterval = QtCore.pyqtSignal()
    signal_totalTime = QtCore.pyqtSignal()
    signal_simulatePatient = QtCore.pyqtSignal()
    signal_boardMockup = QtCore.pyqtSignal()
    signal_simulatePatientPath = QtCore.pyqtSignal()
    signal_FIFOlength = QtCore.pyqtSignal()

    def __init__(self, parent=None, samplingRate_Hz=100.0, patientName='Patient Name', birthdate='31:01:1900', updateInterval_s=5.0,
                 totalTime_s=10*60, FIFO_lengh_s=30.0, simulatePatientPath=None):
        super().__init__(parent)

        self.samplingRate_Hz = samplingRate_Hz
        self.patientName = patientName
        self.birthdate = birthdate
        self.updateInterval_s = updateInterval_s
        self.totalTime_s = totalTime_s
        self.simulatePatientPath = simulatePatientPath
        # operation flags
        self.simulatePatient = False
        self.boardMockup = False
        self.FIFOlength_s = FIFO_lengh_s
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

        # operation mode: normal / simulate patient / mockup board
        # Use radio buttons so exactly one mode is selected
        self.mode = 'normal'  # one of: 'normal', 'simulate', 'mockup'
        modeGroupBox = QtWidgets.QGroupBox('Operation mode')
        modeLayout = QtWidgets.QVBoxLayout()

        self.normalModeRadio = QtWidgets.QRadioButton('Normal')
        self.simulatePatientRadio = QtWidgets.QRadioButton('Simulate patient: uses the board and simulates data acquisition using a pre-recorded file.')
        self.mockupBoardRadio = QtWidgets.QRadioButton('Mockup board: does not use the board and simulates data acquisition using a pre-recorded file.')
        self.normalModeRadio.setChecked(True)
        self.normalModeRadio.toggled.connect(lambda: self.registerOptions('mode'))
        self.simulatePatientRadio.toggled.connect(lambda: self.registerOptions('mode'))
        self.mockupBoardRadio.toggled.connect(lambda: self.registerOptions('mode'))

        modeLayout.addWidget(self.normalModeRadio)
        modeLayout.addWidget(self.simulatePatientRadio)
        modeLayout.addWidget(self.mockupBoardRadio)
        modeGroupBox.setLayout(modeLayout)
        formLayout.addRow(modeGroupBox)

        # simulate patient / mockup path input (enabled only for simulate or mockup modes)
        self.simulatePatientPathWidget = QtWidgets.QLineEdit()
        # populate only if a default path was provided
        if self.simulatePatientPath is not None:
            self.simulatePatientPathWidget.setText(self.simulatePatientPath)
        else:
            self.simulatePatientPathWidget.setText('')
        self.simulatePatientPathWidget.setFixedWidth(250)
        self.simulatePatientPathWidget.editingFinished.connect(lambda: self.registerOptions('simulatePatientPath'))
        self.simulatePatientPathWidget.returnPressed.connect(lambda: self.registerOptions('simulatePatientPath'))
        # enabled only when simulate or mockup is selected
        self.simulatePatientPathWidget.setEnabled(False)

        self.browseFileButton = QtWidgets.QPushButton('Browse...')
        self.browseFileButton.setFixedWidth(80)
        # enabled only when simulate or mockup is selected
        self.browseFileButton.setEnabled(False)

        # connect the browse button to a class method (avoid inner functions)
        self.browseFileButton.clicked.connect(lambda: self.registerOptions('choosePatientPath'))

        fileContainer = QtWidgets.QWidget()
        fileHBox = QtWidgets.QHBoxLayout()
        fileHBox.setContentsMargins(0, 0, 0, 0)
        # align children to the left inside the container
        fileHBox.setAlignment(QtCore.Qt.AlignLeft)
        fileHBox.addWidget(self.simulatePatientPathWidget)
        fileHBox.addWidget(self.browseFileButton)
        fileContainer.setLayout(fileHBox)
        # Prevent the container from expanding to fill the form's field space
        fileContainer.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

        formLayout.addRow('Simulate patient path', fileContainer)
        # Align the container to the left within the QFormLayout row
        formLayout.setAlignment(fileContainer, QtCore.Qt.AlignLeft)

        # sampling rate (Hz)
        self.samplingRateWidget = QtWidgets.QDoubleSpinBox()
        self.samplingRateWidget.setRange(50, 1000)
        self.samplingRateWidget.setDecimals(0)
        self.samplingRateWidget.setSingleStep(50)
        self.samplingRateWidget.setFixedWidth(130)
        self.samplingRateWidget.setValue(self.samplingRate_Hz)
        self.samplingRateWidget.valueChanged.connect(lambda: self.registerOptions('samplingRate'))
        formLayout.addRow('Sampling rate (Hz)', self.samplingRateWidget)

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
        samplingRateWidget.setRange(1, 600)
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

        # FIFO register duration (s)
        FIFOlengthWidget = QtWidgets.QDoubleSpinBox()
        FIFOlengthWidget.setRange(1, 60)
        FIFOlengthWidget.setDecimals(0)
        FIFOlengthWidget.setSingleStep(1)
        FIFOlengthWidget.setFixedWidth(130)
        FIFOlengthWidget.setValue(int(self.FIFOlength_s))  # convert to minutes for display
        FIFOlengthWidget.valueChanged.connect(lambda: self.registerOptions('FIFOlength_s'))
        formLayout.addRow('FIFO register length (s)', FIFOlengthWidget)

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

        if type == 'FIFOlength_s':
            self.FIFOlength_s = self.sender().value()
            self.signal_FIFOlength.emit()

        if type == 'mode':
            # Determine which radio is selected and update flags
            if self.normalModeRadio.isChecked():
                self.mode = 'normal'
                self.simulatePatient = False
                self.boardMockup = False
                self.simulatePatientPathWidget.setEnabled(False)
                self.browseFileButton.setEnabled(False)
                self.samplingRateWidget.setEnabled(True)
            elif self.simulatePatientRadio.isChecked():
                self.mode = 'simulate'
                self.simulatePatient = True
                self.boardMockup = False
                self.simulatePatientPathWidget.setEnabled(True)
                self.browseFileButton.setEnabled(True)
                self.samplingRateWidget.setEnabled(False)
                self.signal_simulatePatient.emit()
            elif self.mockupBoardRadio.isChecked():
                self.mode = 'mockup'
                self.boardMockup = True
                self.simulatePatient = False
                self.simulatePatientPathWidget.setEnabled(True)
                self.browseFileButton.setEnabled(True)
                self.samplingRateWidget.setEnabled(False)
                self.signal_boardMockup.emit()

        if type =='choosePatientPath':
            # only allow .EXP files
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select simulate patient file', '',
                                                            'EXP files (*.EXP *.exp)')
            self.simulatePatientPathWidget.setText(path)
            self.simulatePatientPath = path
            self.signal_simulatePatientPath.emit()

        if type == 'simulatePatientPath':
            self.simulatePatientPath = self.sender().text()
            self.signal_simulatePatientPath.emit()

    def startMonitoring(self):
        self.signal_startMonitoring.emit()

