# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets
from caaos.GUI.toolbox_ARmonitoring.metronome import RespiratoryMetronomeWidget


class monitoringControlWidget(QtWidgets.QWidget):
    """Floating window for activity marking and acquisition controls.

    Click times are recorded in data.activityEvents, in seconds counted from data.startTime.
    """

    closeJobRequested = QtCore.pyqtSignal()

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Acquisition control')

        self.startButton = QtWidgets.QPushButton('START ACTIVITY')
        self.endButton = QtWidgets.QPushButton('STOP ACTIVITY')
        self.closeJobButton = QtWidgets.QPushButton('CLOSE JOB')
        buttonStyle = 'font-size: 20px; font-weight: bold; color: black; background-color: %s;'
        self.startButton.setStyleSheet(buttonStyle % 'lightgreen')
        self.endButton.setStyleSheet(buttonStyle % '#ff9999')
        for button in (self.startButton, self.endButton):
            button.setMinimumSize(300, 100)
        self.closeJobButton.setMinimumHeight(90)
        self.closeJobButton.setStyleSheet('font-size: 24px; font-weight: bold;')
        self.startButton.clicked.connect(lambda: self.mark('START_ACTIVITY'))
        self.endButton.clicked.connect(lambda: self.mark('END_ACTIVITY'))
        self.closeJobButton.clicked.connect(self.closeJobRequested.emit)
        self.statusLabel = QtWidgets.QLabel('No activity recorded')

        activityButtons = QtWidgets.QHBoxLayout()
        activityButtons.addWidget(self.startButton)
        activityButtons.addWidget(self.endButton)

        self.metronome = RespiratoryMetronomeWidget(self)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(activityButtons)
        layout.addWidget(self.statusLabel)
        layout.addWidget(self.metronome)
        layout.addWidget(self.closeJobButton)
        self.setLayout(layout)

    def closeEvent(self, event):
        self.metronome.stop()
        if event.spontaneous():
            self.closeJobRequested.emit()
        super().closeEvent(event)

    def mark(self, eventName):
        elapsed_s = self.data.registerActivityEvent(eventName)
        if elapsed_s is not None:
            self.statusLabel.setText('%s at %.2f s' % (eventName, elapsed_s))
        else:
            self.statusLabel.setText('acquisition ended, cannot mark activity')