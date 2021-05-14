#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from signalPlotWidget import plotArray

# dict format:  '#code' : (paramValue,'string name')
regionTypeDict = {0: ('cycle', 'Cycle'), 1: ('interval', 'Interval')} #, 2: ('spike', 'Signal spike')}
removalMethodDict = {0: ('interpolate', 'Interpolate'), 1: ('crop', 'Crop'), 2: ('joinPeaks', 'join Peaks'), 3: ('none', 'SELECT METHOD')}

cycleRegionType_UnavailableMethods = [0, 1, 3]
intervalRegionType_UnavailableMethods = [3]
spikeRegionType_UnavailableMethods = [3]


class artefactRemovalWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)

        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)

        # region Type control
        default = 1  # Interval
        self.regionType = regionTypeDict[default][0]
        self.regionTypeWidget = QtWidgets.QComboBox()
        self.regionTypeWidget.setFixedWidth(150)
        self.regionTypeWidget.addItems([x[1] for x in regionTypeDict.values()])
        self.regionTypeWidget.setCurrentIndex(default)
        self.regionTypeWidget.currentIndexChanged.connect(lambda: self.registerOptions('regionType'))

        formLayout.addRow('Region Type', self.regionTypeWidget)

        # removal method
        default = 3  # None
        self.cutMethod = removalMethodDict[default][0]
        self.cutMethodWidget = QtWidgets.QComboBox()
        self.cutMethodWidget.setFixedWidth(150)
        self.cutMethodWidget.addItems([x[1] for x in removalMethodDict.values()])
        self.cutMethodWidget.setCurrentIndex(default)
        self.cutMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('cutMethod'))

        for i in intervalRegionType_UnavailableMethods:  # disables cut methodos of the default method
            self.cutMethodWidget.model().item(i).setEnabled(False)

        formLayout.addRow('Method', self.cutMethodWidget)

        # new region button
        self.newButton = QtWidgets.QPushButton('New selection')
        self.newButton.setFixedWidth(100)
        self.newButton.setEnabled(False)
        self.newButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        self.newButton.clicked.connect(self.newArtefactRegion)
        hbox.addWidget(self.newButton)

        # apply button
        self.applyButton = QtWidgets.QPushButton('Apply')
        self.applyButton.setFixedWidth(100)
        self.applyButton.setEnabled(False)
        self.applyButton.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        self.applyButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.applyButton.clicked.connect(self.removeArtefact)
        hbox.addWidget(self.applyButton)

        hbox.addStretch(1)

        # plot area
        self.plotArea = plotArrayArtefact(self.data)
        self.plotArea.plotAllsignals()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.plotArea)
        self.setLayout(vbox)

    def updateTab(self):
        self.plotArea.replotAllsignals()

        # find if ABP signal was assigned to a channel
        hasABPchannel = False
        for s in self.data.signals:
            if s.sigType == 'ABP':
                hasABPchannel = True

        if not hasABPchannel:
            self.applyButton.setEnabled(False)
            self.applyButton.setText('Remove\n\n Please set\n ABP channel\nfirst')
            self.applyButton.setStyleSheet('color:rgb(255,0,0)')
        else:
            self.applyButton.setEnabled(True)
            self.applyButton.setText('Remove')
            self.applyButton.setStyleSheet('color:rgb(0,0,0);background-color:rgb(192,255,208)')  # light green

    # register options
    def registerOptions(self, type):
        if type == 'regionType':
            self.regionType = regionTypeDict[self.sender().currentIndex()][0]

            for j in range(len(removalMethodDict)):
                self.cutMethodWidget.model().item(j).setEnabled(True)

            if self.regionType == 'cycle':
                for i in cycleRegionType_UnavailableMethods:
                    self.cutMethodWidget.model().item(i).setEnabled(False)
                    defaultMethod = 2  # 'join peaks'
                    methodEnable = True

            if self.regionType == 'interval':
                for i in intervalRegionType_UnavailableMethods:
                    self.cutMethodWidget.model().item(i).setEnabled(False)
                    defaultMethod = 3  # 'SELECT METHOD'
                    methodEnable = False

            if self.regionType == 'spike':
                for i in spikeRegionType_UnavailableMethods:
                    self.cutMethodWidget.model().item(i).setEnabled(False)
                    defaultMethod = 3  # 'SELECT METHOD'
                    methodEnable = False

            self.cutMethod = removalMethodDict[defaultMethod][0]
            self.cutMethodWidget.setCurrentIndex(defaultMethod)
            self.newButton.setEnabled(methodEnable)

        if type == 'cutMethod':
            self.cutMethod = removalMethodDict[self.sender().currentIndex()][0]

            if self.cutMethod != 'none':
                self.newButton.setEnabled(True)

    # creates a new region selection element when the user clicks on 'new selection' under artefact removal
    def newArtefactRegion(self):
        try:
            self.plotArea.removeSelections()
        except AttributeError:
            pass

        if self.regionType == 'interval':
            self.plotArea.addSelection(selectionType='interval')
        if self.regionType in ['cycle', 'spike']:
            self.plotArea.addSelection(selectionType='point')

        self.applyButton.setEnabled(True)
        self.newButton.clearFocus()

    # remove artefact
    def removeArtefact(self):

        self.data.removeRRmarks()
        self.data.removeBeat2beat()

        limits = self.plotArea.getSelectionPos(channel=0)

        if limits is None:  # if None, then the user clicked on 'Remove' without creating a new selection
            print('none')
            return

        # find segment indexes. use Pchannel
        if self.cutMethod in ['joinPeaks', 'spike']:
            ABPsignal = [s for s in self.data.signals if s.sigType == 'ABP']
            [peaksIdx, _, _, _] = ABPsignal[0].findPeaks(method='ampd', findPeaks=True, findValleys=False, register=False)

        if self.regionType == 'interval':

            xMin, xMax, posMin, posMax = limits

            if self.cutMethod in ['crop', 'joinPeaks']:
                for s in self.data.signals:
                    if self.cutMethod == 'crop':
                        s.cropInterval(posMin, posMax, RemoveSegment=False)
                    else:
                        s.cropInterval(posMin, posMax, RemoveSegment=True, segmentIndexes=peaksIdx)
                        # finds the start point to adjust the plot
                        start = peaksIdx[np.searchsorted(peaksIdx, posMin) - 1]
                        xMin = self.plotArea.xData[start]

                # recreate plots
                self.plotArea.replotAllsignals()
                self.plotArea.addSelection(selectionType='point')
                self.plotArea.adjusPosSelection(xMin, None)

            if self.cutMethod == 'interpolate':
                for s in self.data.signals:
                    s.interpolate(posMin, posMax, method='linear')

                # recreate plots
                self.plotArea.replotAllsignals()
                self.plotArea.addSelection(selectionType='interval')
                self.plotArea.adjusPosSelection(xMin, xMax)

        if self.regionType in ['cycle']:
            xMin, posMin = limits

            if self.cutMethod in ['joinPeaks']:
                for s in self.data.signals:
                    s.cropInterval(posMin, posMin + 1, RemoveSegment=True, segmentIndexes=peaksIdx)
                    # finds the start point
                    start = peaksIdx[np.searchsorted(peaksIdx, posMin) - 1]
                    xMin = self.plotArea.xData[start]

                # recreate plots
                self.plotArea.replotAllsignals()
                self.plotArea.addSelection(selectionType='point')
                self.plotArea.adjusPosSelection(xMin, None)

        if self.regionType in ['spike']:
            print('not implemented yet!')

        self.plotArea.lockSelection(True)
        self.applyButton.clearFocus()
        self.applyButton.setEnabled(False)


class plotArrayArtefact(plotArray):

    def __init__(self, patientData):
        super(plotArrayArtefact, self).__init__(patientData)

    # redefinition of this member function
    def addSelection(self, selectionType, channels='all'):
        if channels == 'all':
            channels = range(self.Nplots)

        [xlim, ylim] = self.getLimits()
        if selectionType == 'interval':
            minX = xlim[0] + (xlim[1] - xlim[0]) / 3
            maxX = xlim[1] - (xlim[1] - xlim[0]) / 3
        if selectionType == 'point':
            minX = xlim[0] + (xlim[1] - xlim[0]) / 2
            maxX = None

        for ch in channels:
            self.axes[ch].addSelection(minX, maxX, selectionType)
            self.axes[ch].signal_selectionMoved.connect(self.alignSelections)  # <-- ONLY ADDED LINE
