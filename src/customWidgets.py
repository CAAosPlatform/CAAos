#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class signalTabWidget(QtWidgets.QWidget):
    def __init__(self, colLabels, colSizes, colLabelsOffset):
        QtWidgets.QWidget.__init__(self)
        self.nChannels = 0
        self.colSizes = colSizes
        self.colLabels = colLabels
        self.colLabelsOffset = colLabelsOffset
        self.initUI()
        self.addHeader()
        self.channels = []

    def initUI(self):

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.vbox)

    def addHeader(self):
        hbox0 = QtWidgets.QHBoxLayout()
        hbox0.setAlignment(QtCore.Qt.AlignLeft)
        self.vbox.addLayout(hbox0)

        if self.colLabelsOffset > 0:
            verticalSpacer = QtWidgets.QSpacerItem(self.colLabelsOffset, 0)
            hbox0.addItem(verticalSpacer)

        for i in range(len(self.colLabels)):
            label = QtWidgets.QLabel(self.colLabels[i], self)
            label.setFixedWidth(self.colSizes[i])
            hbox0.addWidget(label)

    def clearSignals(self):
        for ch in self.channels:
            ch.setParent(None)
        self.channels = []
        self.nChannels = 0


# TEMPLATE FOR addSignal function 
#   def addSignal(self,channel,label='name',max=10.0,min=0.0):
#        signal=channelSettings(channel,label,max,min,self.colSizes)
#        self.vbox.addWidget(signal)
#        self.channels.append(signal)
#        self.nChannels=len(self.channels)
#        return signal

class TFAresultTable(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.nChannels = 0
        self.nRows = 3  # does not include the label row
        self.nCols = 3  # does not include the label column
        self.colSizes = 130
        self.colLabels = ['VLF', 'LF', 'HF']
        self.rowLabels = ['Gain', 'Phase (deg)', 'Coherence']
        self.colLabelsOffset = 10
        self.initUI()
        self.setFixedWidth(300)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

    def initUI(self):
        self.grid = QtWidgets.QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setRowMinimumHeight(0, 30)
        self.grid.setColumnMinimumWidth(0, 50)
        self.setLayout(self.grid)
        self.initTable()
        self.setGain([0.0, 0.0, 0.0])
        self.setPhase([0.0, 0.0, 0.0])
        self.setCoherence([0.0, 0.0, 0.0])

    def initTable(self):
        # columns
        for i in range(self.nCols):
            text = QtWidgets.QLabel(self.colLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, 0, i + 1)
            text.setFixedWidth(50)
        # rows
        for i in range(self.nRows):
            text = QtWidgets.QLabel(self.rowLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignLeft)
            self.grid.addWidget(text, i + 1, 0)

        # cels
        for i in range(self.nRows):
            for j in range(self.nCols):
                text = QtWidgets.QLabel('{0:.3f}'.format(0), self)
                text.setAlignment(QtCore.Qt.AlignRight)
                self.grid.addWidget(text, i + 1, j + 1)

    def setValue(self, row, col, value):
        text = self.grid.itemAtPosition(row + 1, col + 1).widget()
        text.setText(str('{0:.3f}'.format(value)))

    def setGain(self, values):
        for i, v in enumerate(values):
            self.setValue(0, i, v)

    def setPhase(self, values):
        for i, v in enumerate(values):
            self.setValue(1, i, v)

    def setCoherence(self, values):
        for i, v in enumerate(values):
            self.setValue(2, i, v)


class ARIresultTable(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.nChannels = 0
        self.nRows = 1  # does not include the label row
        self.nCols = 10  # does not include the label column
        self.colSizes = 120
        self.colLabels = ['0','1','2','3','4','5','6','7','8','9']
        self.rowLabels = ['Error:']
        self.colLabelsOffset = 5
        self.initUI()
        #self.setFixedWidth(700)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

    def initUI(self):
        vboxL = QtWidgets.QVBoxLayout()
        self.grid = QtWidgets.QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setRowMinimumHeight(0, 10)
        self.grid.setColumnMinimumWidth(0, 20)

        #self.bestFitLabel = QtWidgets.QLabel('Best fit: ', self)

        vboxL.addLayout(self.grid)
        #vboxL.addWidget(self.bestFitLabel)

        self.setLayout(vboxL)
        self.initTable()
        self.setError([0.0,]*10)
        self.setBestFit(0)

    def initTable(self):

        # columns
        for i in range(self.nCols):
            text = QtWidgets.QLabel(self.colLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, 0, i + 1)
            text.setFixedWidth(50)

        # rows
        text = QtWidgets.QLabel('ARI:', self)
        text.setAlignment(QtCore.Qt.AlignRight)
        self.grid.addWidget(text, 0,0)
        text.setFixedWidth(50)

        for i in range(self.nRows):
            text = QtWidgets.QLabel(self.rowLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, i + 1, 0)

        # cels
        for i in range(self.nRows):
            for j in range(self.nCols):
                text = QtWidgets.QLabel('{0:.2f}'.format(0), self)
                text.setAlignment(QtCore.Qt.AlignRight)
                self.grid.addWidget(text, i + 1, j + 1)
        #best Fit
        self.grid.addWidget(QtWidgets.QLabel('Best Fit:', self), self.nRows+ 1, 0)
        self.bestFitLabel = QtWidgets.QLabel('0', self)
        self.bestFitLabel.setAlignment(QtCore.Qt.AlignRight)
        self.grid.addWidget(self.bestFitLabel, self.nRows+ 1, 1)

    def setError(self, values):
        row=0
        for i, v in enumerate(values):
            valueStr = str('{0:.2f}'.format(v))
            text = self.grid.itemAtPosition(row + 1, i + 1).widget()
            text.setText(valueStr)

    def setBestFit(self, bestARI):
        self.bestFitLabel.setText('{0:.2f}'.format(bestARI)    )


class MXresultTable(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.nChannels = 0
        self.nRows = 1  # does not include the label row
        self.nCols = 10  # does not include the label column
        self.colSizes = 100
        self.colLabels = [str(x+1) for x in range(self.nCols)]
        self.rowLabels = ['Mx:']
        self.colLabelsOffset = 5
        self.initUI()
        #self.setFixedWidth(700)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

    def initUI(self):
        vboxL = QtWidgets.QVBoxLayout()
        self.grid = QtWidgets.QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setRowMinimumHeight(0, 10)
        self.grid.setColumnMinimumWidth(0, 20)

        #self.bestFitLabel = QtWidgets.QLabel('Best fit: ', self)

        vboxL.addLayout(self.grid)
        #vboxL.addWidget(self.bestFitLabel)

        self.setLayout(vboxL)
        self.initTable()
        self.setMx([0.0,]*10)
        self.setAvgMx(0)

    def initTable(self):

        # columns
        for i in range(self.nCols):
            text = QtWidgets.QLabel(self.colLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, 0, i + 1)
            text.setFixedWidth(50)

        # rows
        text = QtWidgets.QLabel('Epoch', self)
        text.setAlignment(QtCore.Qt.AlignRight)
        self.grid.addWidget(text, 0,0)
        text.setFixedWidth(50)

        for i in range(self.nRows):
            text = QtWidgets.QLabel(self.rowLabels[i], self)
            text.setAlignment(QtCore.Qt.AlignRight)
            self.grid.addWidget(text, i + 1, 0)

        # cels
        for i in range(self.nRows):
            for j in range(self.nCols):
                text = QtWidgets.QLabel('', self)
                text.setAlignment(QtCore.Qt.AlignRight)
                self.grid.addWidget(text, i + 1, j + 1)
        #best Fit
        self.grid.addWidget(QtWidgets.QLabel('average Mx:', self), self.nRows+ 1, 0)
        self.averageMX = QtWidgets.QLabel('', self)
        self.averageMX.setAlignment(QtCore.Qt.AlignRight)
        self.grid.addWidget(self.averageMX, self.nRows + 1, 1)

    def setMx(self, values):
        row=0
        for i, v in enumerate(values):
            valueStr = str('{0:.2f}'.format(v))
            text = self.grid.itemAtPosition(row + 1, i + 1).widget()
            text.setText(valueStr)

    def setAvgMx(self, avgMx):
        self.averageMX.setText('{0:.2f}'.format(avgMx) )
