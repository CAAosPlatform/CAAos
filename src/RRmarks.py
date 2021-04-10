#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph as pg
from customWidgets import signalTabWidget
from signalPlotWidget import plotArray, pyQtConf, signalPlot

# dict format:  '#code' : (paramValue,'string name')
RRmethodDict = {0: ('md', 'MD'), 1: ('ampd', 'AMPD')}


class signalRRmarksWidget(QtWidgets.QWidget):

    def __init__(self, patientData):
        QtWidgets.QWidget.__init__(self)
        self.data = patientData
        self.initUI()

    def initUI(self):

        hboxA = QtWidgets.QHBoxLayout()
        hboxA.setAlignment(QtCore.Qt.AlignTop)

        self.signalTab = signalRRmarksTab(['Label', 'Sig. type'], [150, 80], 83)
        hboxA.addWidget(self.signalTab)

        for s in self.data.signals:
            self.signalTab.addSignal(channel=s.channel, label=s.label, sigType=s.sigType)

        formLayout = QtWidgets.QFormLayout()
        hboxA.addLayout(formLayout)

        # RRmarks method
        default = 1  # AMPD algorithm
        self.RRmethod = RRmethodDict[default][0]
        RRMethodWidget = QtWidgets.QComboBox()
        # RRMethodWidget.setFixedWidth(100)
        RRMethodWidget.addItems([x[1] for x in RRmethodDict.values()])
        RRMethodWidget.setCurrentIndex(default)
        RRMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('RRmethod'))

        formLayout.addRow('Method', RRMethodWidget)

        hboxB = QtWidgets.QHBoxLayout()
        # apply button
        self.findPeaksButton = QtWidgets.QPushButton('Find RR marks')
        # findPeaksButton.setFixedWidth(120)
        self.findPeaksButton.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.findPeaksButton.setStyleSheet('background-color:rgb(192,255,208)')  # light green
        self.findPeaksButton.clicked.connect(self.findpeaksRRmarks)
        hboxB.addWidget(self.findPeaksButton)

        # add mark button
        self.addButton = QtWidgets.QPushButton('Add Mark')
        # self.addButton.setFixedWidth(120)
        self.addButton.setEnabled(False)
        self.addButton.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.addButton.clicked.connect(lambda: self.editRRmark('add'))
        hboxB.addWidget(self.addButton)

        # remove mark button
        self.removeButton = QtWidgets.QPushButton('Remove Mark')
        # self.removeButton.setFixedWidth(120)
        self.removeButton.setEnabled(False)
        self.removeButton.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.removeButton.clicked.connect(lambda: self.editRRmark('remove'))
        hboxB.addWidget(self.removeButton)

        # heart rate plot area
        self.HRplotArea = heartRatePlotWidget()
        self.HRplotArea.setFixedHeight(200)
        self.HRplotArea.plot()
        self.HRplotArea.signal_selectionMoved.connect(self.adjustPlotArea)

        # hbox.addStretch(1)
        vboxA = QtWidgets.QVBoxLayout()
        vboxA.addLayout(hboxA)
        vboxA.addLayout(hboxB)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(vboxA)
        hbox.addWidget(self.HRplotArea)

        # plot area
        self.plotArea = plotArrayRRmarks(self.data)
        self.plotArea.plotAllsignals()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.plotArea)
        self.setLayout(vbox)

    def updateTab(self):
        self.plotArea.replotAllsignals()

        if self.data.hasRRmarks:
            self.plotArea.markPeaks(channel=0, peakIdx=self.data.peakIdx, valleyIdx=None)

            refChannel = [s.channel for s in self.data.signals if s.sigType == 'ABP']
            self.refChannel = refChannel[0]

            self.addButton.setEnabled(True)
            self.removeButton.setEnabled(True)
            self.HRplotArea.setData(RRmarks=self.data.peakIdx, samplingRate_Hz=self.data.signals[self.refChannel].samplingRate_Hz)
            self.HRplotArea.replot()
        else:
            self.plotArea.removePeaks()
            self.HRplotArea.resetPlot()
            self.addButton.setEnabled(False)
            self.removeButton.setEnabled(False)

        for ch in range(self.signalTab.nChannels):
            channel = self.signalTab.channels[ch]
            channel.updateLabels(self.data.signals[ch].label, self.data.signals[ch].sigType)

        # find if ABP signal was assigned to a channel
        hasABPchannel = False
        for ch in range(self.signalTab.nChannels):
            if self.data.signals[ch].sigType == 'ABP':
                hasABPchannel = True

        if not hasABPchannel:
            self.findPeaksButton.setEnabled(False)
            self.findPeaksButton.setText('Find RR marks\n\nPlease set\n ABP channel first')
            self.findPeaksButton.setStyleSheet('color:rgb(255,0,0)')
        else:
            self.findPeaksButton.setEnabled(True)
            self.findPeaksButton.setText('Find RR marks')
            self.findPeaksButton.setStyleSheet('color:rgb(0,0,0);background-color:rgb(192,255,208)')  # light green

    def registerOptions(self, type):
        if type == 'RRmethod':
            self.RRmethod = RRmethodDict[self.sender().currentIndex()][0]

    # creates a new RRmark plotItem widget
    def editRRmark(self, type):

        self.plotArea.removeRRmarkSelections()
        self.plotArea.addRRmarkSelections(type)

        self.HRplotArea.addSelection()

        for plot in self.plotArea.axes:
            if type == 'add':
                try:
                    plot.signal_addRRmark.disconnect()
                except:
                    pass
                plot.signal_addRRmark.connect(self.addRR)
                self.addButton.setStyleSheet('background-color:rgb(255,255,127)')  # light yellow
                self.addButton.clearFocus()
                self.removeButton.setStyleSheet('')
            if type == 'remove':
                try:
                    plot.signal_removeRRmark.disconnect()
                except:
                    pass
                plot.signal_removeRRmark.connect(self.removeRR)
                self.removeButton.setStyleSheet('background-color:rgb(255,255,127)')  # light yellow
                self.removeButton.clearFocus()
                self.addButton.setStyleSheet('')

    # add new RRmark to data
    def addRR(self):

        self.data.removeBeat2beat()

        peakIdX = self.plotArea.convXtoSample(self.sender().mousePos[0], roundMethod='nearest')
        # print('pos: ',self.sender().mousePos[0])
        # print('idx: ',peakIdX)
        self.data.insertPeak(peakIdX, isPeak=True)
        self.plotArea.markPeaks(channel=0, peakIdx=self.data.peakIdx, valleyIdx=None)
        self.HRplotArea.setData(RRmarks=self.data.peakIdx, samplingRate_Hz=self.data.signals[self.refChannel].samplingRate_Hz)
        self.HRplotArea.replot()

    #  remove RRmark from data
    def removeRR(self):

        self.data.removeBeat2beat()

        peakIdX = self.plotArea.convXtoSample(self.sender().mousePos[0], roundMethod='nearest')
        self.data.removePeak(peakIdX, isPeak=True)
        self.plotArea.markPeaks(channel=0, peakIdx=self.data.peakIdx, valleyIdx=None)
        self.HRplotArea.setData(RRmarks=self.data.peakIdx, samplingRate_Hz=self.data.signals[self.refChannel].samplingRate_Hz)
        self.HRplotArea.replot()

    def findpeaksRRmarks(self):

        self.data.removeBeat2beat()

        refChannel = [s.channel for s in self.data.signals if s.sigType == 'ABP']
        self.refChannel = refChannel[0]

        self.data.findRRmarks(self.refChannel, method=self.RRmethod, findPeaks=True, findValleys=False)
        self.plotArea.markPeaks(channel=0, peakIdx=self.data.peakIdx, valleyIdx=None)
        self.HRplotArea.setData(RRmarks=self.data.peakIdx, samplingRate_Hz=self.data.signals[self.refChannel].samplingRate_Hz)
        self.HRplotArea.replot()

        self.findPeaksButton.clearFocus()

        self.addButton.setEnabled(True)
        self.removeButton.setEnabled(True)

    def adjustPlotArea(self):
        minX, maxX = self.sender().selection.getRegion()
        self.plotArea.setLimits(xlim=[minX, maxX])


class signalRRmarksTab(signalTabWidget):
    def __init__(self, colLabels, colSizes, colLabelsOffset):
        signalTabWidget.__init__(self, colLabels, colSizes, colLabelsOffset)

    def addSignal(self, channel, label, sigType):
        signal = channelSettings(channel, label, sigType, self.colSizes)
        self.vbox.addWidget(signal)
        self.channels.append(signal)
        self.nChannels = len(self.channels)


class channelSettings(QtWidgets.QWidget):

    def __init__(self, channel, label, sigType, colSizes):
        QtWidgets.QWidget.__init__(self)
        self.channel = channel
        self.label = label
        self.sigType = sigType
        self.colSizes = colSizes
        self.initUI()

    def initUI(self):
        # layout
        hbox0 = QtWidgets.QHBoxLayout()
        hbox0.setAlignment(QtCore.Qt.AlignLeft)
        hbox0.setContentsMargins(0, 0, 0, 0);
        self.setLayout(hbox0)

        # text
        channelSignal = QtWidgets.QLabel('Channel %d' % self.channel)
        channelSignal.setFixedWidth(70)

        # label
        self.labelSignal = QtWidgets.QLabel(self.label)
        self.labelSignal.setFixedWidth(self.colSizes[0])

        # sigType
        self.signalType = QtWidgets.QLabel(str(self.sigType))
        self.signalType.setFixedWidth(self.colSizes[1])

        # monta o layout
        hbox0.addWidget(channelSignal)
        hbox0.addWidget(self.labelSignal)
        hbox0.addWidget(self.signalType)

    def updateLabels(self, label, sigType):
        self.label = label
        self.sigType = sigType
        self.labelSignal.setText(self.label)
        self.signalType.setText(str(self.sigType))


class heartRatePlotWidget(pg.GraphicsLayoutWidget):
    signal_selectionMoved = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(heartRatePlotWidget, self).__init__()
        self.selectionActive = False
        self.selectionPosition = [0, 10]
        self.resetPlot()

    def resetPlot(self):
        self.samplingRate_Hz = 0.0;
        self.xData = np.array([0.0, 1.0])
        self.yData = np.array([0.0, 0.0])
        self.Npoints = 2
        self.plot()

    # set Data vectors
    def setData(self, RRmarks, samplingRate_Hz):
        self.samplingRate_Hz = samplingRate_Hz
        self.xData = RRmarks[0:-1] / self.samplingRate_Hz  # ignores the last point. converts to seconds

        # computes the sample difference between peaks and converts to bpm
        self.yData = np.reciprocal(np.diff(RRmarks / (self.samplingRate_Hz))) * 60.0
        self.Npoints = len(self.xData)

        # replaces all frequencies above 250bpm by 250bpm to facilitate the visualization
        self.yData[self.yData > 250.0] = 250.0

    def plot(self):
        self.clear()
        self.axis = pg.PlotItem()

        title = pg.TextItem(text='Heart rate (bpm)', anchor=(0, 0), color=pyQtConf['textColor'], angle=0)
        title.setParentItem(self.axis)
        title.setPos(80, 0)

        # self.axis.setLabel('left', 'Heart rate','bpm')
        self.axis.showGrid(x=True, y=True)
        self.axis.setLabel('bottom', 'Time', 's')
        self.axis.setMouseEnabled(x=True, y=False)  # allows pan in X direction only
        self.axis.setLimits(xMin=0, xMax=self.xData[-1])  # limits the viewbox of the plot to xData range
        self.axis.enableAutoRange(y=True)
        self.signalCurve = self.axis.plot(x=self.xData, y=self.yData, pen=pg.mkPen(pyQtConf['plotColors']['red'], width=pyQtConf['plotLineWidth']))

        self.addItem(self.axis)

        # self.addSelection()

    # replot data without creating a new curve. It changes yData only. yData must be the same size
    def replot(self):
        self.signalCurve.setData(x=self.xData, y=self.yData)
        # self.update
        self.axis.setLimits(xMin=0, xMax=self.xData[-1])  # limits the viewbox of the plot to xData range
        self.axis.vb.setRange(xRange=(min(self.xData), max(self.xData)), yRange=(min(self.yData), max(self.yData)), update=True)

    # add a crop region to the plot.
    def addSelection(self):

        if not self.selectionActive:
            brush = pg.mkBrush(color=(200, 200, 200, 90))  # gray color
            self.selection = pg.LinearRegionItem(values=self.selectionPosition, orientation=pg.LinearRegionItem.Vertical, bounds=[0, self.xData[-1]])
            self.selection.setBrush(brush)
            self.selection.sigRegionChanged.connect(self.selectionChanged)

            self.selection.setZValue(10)
            self.axis.addItem(self.selection, ignoreBounds=True)
            self.selectionActive = True
            self.signal_selectionMoved.emit(True)

    # remove crop region
    def removeSelection(self):
        try:
            self.removeItem(self.selection)
            self.selectionActive = False
        except AttributeError:
            pass

    # adjusts the limits of the highlighted region
    def selectionChanged(self):
        self.selectionPosition = self.selection.getRegion()
        self.signal_selectionMoved.emit(True)


class signalPlotRRmarks(signalPlot):
    signal_RRmarkSelectionMoved = QtCore.pyqtSignal(bool)
    signal_addRRmark = QtCore.pyqtSignal(bool)
    signal_removeRRmark = QtCore.pyqtSignal(bool)

    def __init__(self, channel, xData=np.array([0, 1, 2]), xlabel='Time', xUnit='s', yData=[[np.array([1, 2, 3]), (255, 0, 0), 'signal']], yUnit='V',
                 title='signal', legend=False):
        super(signalPlotRRmarks, self).__init__(channel, xData, xlabel, xUnit, yData, yUnit, title)

    # activates events for mouse interaction. USE this function ONLY after adding it to a scene!
    def activateMouseEvents(self):
        self.scene().sigMouseMoved.connect(self.mousePosition)
        self.scene().sigMouseClicked.connect(self.mouseClick)
        self.scene().sigMouseMoved.connect(self.RRmarkMoved)
        self.scene().sigMouseClicked.connect(self.RRmarkClicked)

    def addRRmarkSelection(self, pos, type='add'):
        self.removeRRmarkSelection()

        if type == 'add':
            self.RRtype = 'add'
        if type == 'remove':
            self.RRtype = 'remove'

        self.RRmarkSelection = pg.InfiniteLine(pos, angle=90, pen=pyQtConf['linearRegionPen'], movable=True, bounds=[0, self.xData[-1]])

        self.addItem(self.RRmarkSelection, ignoreBounds=True)

        # self.scene().sigMouseMoved.connect(self.RRmarkMoved)

        # self.scene().sigMouseClicked.connect(self.RRmarkClicked)

    # used only to adjust all the vertical lines
    def RRmarkMoved(self):
        if self.mousePos is not None:
            try:
                self.RRmarkSelection.setValue(self.mousePos[0])
                self.signal_RRmarkSelectionMoved.emit(True)
            except AttributeError:
                pass

    # action taken when the user clicks
    def RRmarkClicked(self):
        if self.mousePos is not None:
            try:
                if self.RRtype == 'add':
                    self.signal_addRRmark.emit(True)
                if self.RRtype == 'remove':
                    self.signal_removeRRmark.emit(True)
            except AttributeError:
                pass

    # remove RRmark selection
    def removeRRmarkSelection(self):
        try:
            self.removeItem(self.RRmarkSelection)
            del self.RRtype
        except AttributeError:
            pass

        # self.scene().sigMouseMoved.disconnect(self.RRmarkMoved)

        # self.scene().sigMouseClicked.disconnect(self.RRmarkClicked)


class plotArrayRRmarks(plotArray):

    def __init__(self, patientData):
        super(plotArrayRRmarks, self).__init__(patientData)

    newPlotClass = signalPlotRRmarks

    # add RR region
    # selectionType:  'add','remove'
    def addRRmarkSelections(self, selectionType):
        [xlim, ylim] = self.getLimits()
        pos = xlim[0] + (xlim[1] - xlim[0]) / 2

        for plot in self.axes:
            plot.addRRmarkSelection(pos, selectionType)
            plot.signal_RRmarkSelectionMoved.connect(self.alignRRmarkSelection)

    # adjusts the limits of the highlighted region
    def alignRRmarkSelection(self):
        pos = self.sender().RRmarkSelection.value()
        for plot in self.axes:
            plot.RRmarkSelection.setValue(pos)

    # remove all RRmark selections
    def removeRRmarkSelections(self):
        for plot in self.axes:
            plot.removeRRmarkSelection()
