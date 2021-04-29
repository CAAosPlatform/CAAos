#! /usr/bin/python

# -*- coding: utf-8 -*-

import math

import numpy as np
from PyQt5 import QtCore, QtGui

import pyqtgraph as pg

darkTheme = False

if darkTheme:
    pyQtConf = {  # Dark theme
        'backgroundColor': 'k', 'foregroundColor': 'w', 'textColor': (255, 255, 255),
        'plotColors': {'red': (255, 0, 0), 'green': (125, 221, 126), 'blue': (0, 170, 255), 'base': (255, 255, 255)},
        'linearRegionBrush': pg.mkBrush((200, 200, 200, 100)), 'linearRegionPen': pg.mkPen(color=(255, 0, 0, 255)), 'plotLineWidth': 1.0,
        'peakMarkSymbol': 'o', 'peakMarkSize': 5, 'peakMarkColor': (255, 0, 0)}
else:
    pyQtConf = {'backgroundColor': 'w', 'foregroundColor': 'k', 'textColor': (0, 0, 0),
                'plotColors': {'red': (255, 0, 0), 'green': (120, 255, 90), 'blue': (0, 100, 200), 'base': (0, 0, 0)},
                'linearRegionBrush': pg.mkBrush((50, 50, 50, 50)), 'linearRegionPen': pg.mkPen(color=(255, 0, 0, 255)), 'plotLineWidth': 2.0,
                'peakMarkSymbol': 'o', 'peakMarkSize': 5, 'peakMarkColor': (255, 0, 0)}

if pyQtConf['plotLineWidth'] == 1.0:
    pg.setConfigOption('antialias', False)  # turning it on will cause drop in performance
else:
    pg.setConfigOption('antialias', True)  # turning it on will cause drop in performance
pg.setConfigOption('background', pyQtConf['backgroundColor'])
pg.setConfigOption('foreground', pyQtConf['foregroundColor'])


class signalPlot(pg.PlotItem):
    signal_mouseClicked = QtCore.pyqtSignal(bool)
    signal_selectionMoved = QtCore.pyqtSignal(bool)

    # yData format: list of lists of the type [data_i,color_i,label_i]
    # where data_i is a numpy array
    def __init__(self, channel, xData=np.array([0, 1, 2]), xlabel='Time', xUnit='s', yData=[[np.array([1, 2, 3]), (255, 0, 0), 'signal']], yUnit='V',
                 title='Signal', legend=False):
        super(signalPlot, self).__init__()

        self.channel = channel
        self.xData = xData
        self.yData = yData

        self.mysetTitle(title)

        self.setLabel('left', yUnit)
        self.showGrid(x=True, y=True)
        self.setLabel('bottom', xlabel, units=xUnit)
        self.setMouseEnabled(x=True, y=False)  # allows pan in X direction only
        self.setLimits(xMin=0, xMax=self.xData[-1])  # limits the viewbox of the plot to xData range
        self.enableAutoRange(y=True)
        self.hasSelection = False

        self.axes['bottom']['item'].enableAutoSIPrefix(False)

        self.signalCurve = [self.plot(x=self.xData, y=y, pen=pg.mkPen(color, width=pyQtConf['plotLineWidth'], name=label)) for y, color, label in
                            self.yData]

        if legend:
            self.signalLegend()
        # self.signalCurve.curve.setClickable(True)
        # self.signalCurve.curve.sigClicked.connect(self.curveClicked)
        self.mousePos = None

    def mysetTitle(self, title):
        if title is None:
            return
        try:
            self.title.setText(title)
        except AttributeError:
            self.title = pg.TextItem(text=title, anchor=(0, 0), color=pyQtConf['textColor'], angle=0)
            self.title.setParentItem(self)
            self.title.setPos(80, 0)

    def signalLegend(self):
        self.legend = pg.LegendItem(offset=[-20, 10])
        self.legend.setParentItem(self)

        for i in range(len(self.signalCurve)):
            self.legend.addItem(self.signalCurve[i], self.yData[i][2])

    # activates events for mouse interaction. USE this function ONLY after adding it to a scene!
    def activateMouseEvents(self):
        self.scene().sigMouseMoved.connect(self.mousePosition)
        self.scene().sigMouseClicked.connect(self.mouseClick)

    def mousePosition(self, event):
        if self.sceneBoundingRect().contains(event):
            mousePoint = self.getViewBox().mapSceneToView(event)
            self.mousePos = [mousePoint.x(), mousePoint.y()]
        else:
            self.mousePos = None

    def mouseClick(self, event):
        if self.sceneBoundingRect().contains(event.scenePos()):
            # print('ch: %d' % self.channel, 'Click! at %f,%f' %(self.mousePos[0],self.mousePos[1]))
            self.signal_mouseClicked.emit(True)

    def curveClicked(self):
        print('channel %d clicked' % self.channel)

    # create a curve showing peaks and/or valleys
    def markPeaks(self, channel=0, peakIdx=None, valleyIdx=None):

        # temp_rand=np.random.rand(self.yData[peakIdx].shape[0])*0.2*max(self.yData[peakIdx])
        if peakIdx is not None:
            try:
                self.peakCurve.setData(self.xData[peakIdx], self.yData[channel][peakIdx])
            except AttributeError:
                self.peakCurve = self.plot(self.xData[peakIdx], self.yData[channel][peakIdx], pen=None, symbol=pyQtConf['peakMarkSymbol'],
                                           symbolPen=None, symbolSize=pyQtConf['peakMarkSize'], symbolBrush=pyQtConf['peakMarkColor'])

        if valleyIdx is not None:
            try:
                self.valleyCurve.setData(self.xData[valleyIdx], self.yData[channel][valleyIdx])
            except AttributeError:
                self.valleyCurve = self.plot(self.xData[valleyIdx], self.yData[channel][valleyIdx], pen=None, symbol=pyQtConf['peakMarkSymbol'],
                                             symbolPen=None, symbolSize=pyQtConf['peakMarkSize'], symbolBrush=pyQtConf['peakMarkColor'])

    def removePeaks(self):
        try:
            self.removeItem(self.peakCurve)
            del self.peakCurve
        except AttributeError:
            pass
        try:
            self.removeItem(self.valleyCurve)
            del self.valleyCurve
        except AttributeError:
            pass

    # hide xLabel of the plot
    def hideXlabel(self):
        self.axes['bottom']['item'].showLabel(False)

        if False:  # removes tick labels and keep grid where we want
            xax = self.getAxis('bottom')
            xax.setTicks([])  # removes tick labels
            y = range(0, 10)
            x = ['', ] * len(y)
            xdict = dict(enumerate(x))
            xax.setTicks([xdict.items()])

    # replot data without creating a new curve. It changes xData and yData only.
    # yData format: list of numpy arrays [ yData_i ]
    # yData_i must be the same size of xData. If xData=None, the current xData is used
    def replot(self, xData, yData):
        self.yData = yData

        if xData is not None:
            self.xData = xData

        for i in range(len(self.signalCurve)):
            self.signalCurve[i].setData(x=self.xData, y=self.yData[i])

        self.update
        M = max([y.max() for y in self.yData])
        m = min([y.min() for y in self.yData])
        self.vb.setRange(yRange=(m, M), update=True)

    # add a selection region to the plot.
    def addSelection(self, minX, maxX, type='interval'):
        self.removeSelection()

        if type == 'interval':
            self.selectionType = 'interval'
            self.selection = pg.LinearRegionItem(values=[minX, maxX], orientation=pg.LinearRegionItem.Vertical, bounds=[0, self.xData[-1]],
                                                 pen=pyQtConf['linearRegionPen'], brush=pyQtConf['linearRegionBrush'])
            self.selection.sigRegionChanged.connect(self.selectionChanged)
        if type == 'point':
            self.selectionType = 'point'
            self.selection = pg.InfiniteLine(pos=minX, angle=90, pen=pyQtConf['linearRegionPen'], movable=True, bounds=[0, self.xData[-1]])
            self.selection.sigPositionChanged.connect(self.selectionChanged)

        self.selection.setZValue(10)
        self.addItem(self.selection, ignoreBounds=True)
        self.hasSelection = True

    # remove crop region
    def removeSelection(self):
        try:
            self.removeItem(self.selection)
            del self.selectionType
            self.hasSelection = False
        except AttributeError:
            pass

    # used only to adjust all the vertical lines
    def selectionChanged(self):
        self.signal_selectionMoved.emit(True)


class plotArray(pg.GraphicsLayoutWidget):

    def __init__(self, patientData, nCols=1):
        super(plotArray, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        self.data = patientData
        self.PlotNbr = {}  # empty dictionary
        self.Nplots = 0
        self.axes = []
        self.numberOfColumns = nCols

    # plot all signals, destroying any previously created elements (axes, labels, etc)  SLOWER!
    def plotAllsignals(self, legend=False):
        self.clearAll()
        self.setXData(Npoints=self.data.signals[0].nPoints, samplingRate_Hz=self.data.signals[0].samplingRate_Hz, x0=0.0)

        for s in self.data.signals:
            self.addNewPlot(channel=s.channel, title=s.label, yData=[[s.data, pyQtConf['plotColors']['blue'], 'Ch %d) ' % s.channel + s.label]],
                            yUnit=s.unit, legend=legend)

    # plot all signals, keeping any previously created elements (axes, labels, etc)   FASTER!
    def replotAllsignals(self):
        self.setXData(Npoints=self.data.signals[0].nPoints, samplingRate_Hz=self.data.signals[0].samplingRate_Hz, x0=0.0)
        for s in self.data.signals:
            self.axes[s.channel].replot(self.xData, [s.data])
            self.axes[s.channel].mysetTitle('Ch %d) ' % s.channel + s.label)

    # set xData vector (the same for all plots
    def setXData(self, Npoints=100, samplingRate_Hz=100, x0=0.0):
        self.Npoints = Npoints
        self.samplingRate_Hz = samplingRate_Hz
        self.xData = x0 + np.arange(self.Npoints) / self.samplingRate_Hz

    # class to be instanced in addNewPlot funcion member
    newPlotClass = signalPlot

    # adds new plot. All the plots must have the same number of points
    # yData format: list of lists of the type [data_i,color_i,label_i]
    # where data_i is a numpy array or None
    def addNewPlot(self, channel, title, yData, yUnit, legend=False):

        yData = [[np.zeros(self.Npoints), c, l] if y is None else [y, c, l] for y, c, l in yData]

        newPlot = self.newPlotClass(channel, self.xData, 'Time', 's', yData, yUnit, title, legend)

        if self.Nplots > 0:

            # removes x ticks and X labels of the last plot
            self.axes[-1].hideXlabel()

            # links X axis between the plots so that if we move one plot, they all move together
            newPlot.setXLink(self.axes[0])

        self.addItem(newPlot)

        newPlot.activateMouseEvents()
        newPlot.signal_mouseClicked.connect(self.getClickPosition)

        self.axes.append(newPlot)
        self.PlotNbr[channel] = self.Nplots
        self.Nplots = len(self.axes)

        if self.Nplots % self.numberOfColumns == 0:
            self.nextRow()

    # mark peaks 
    def markPeaks(self, channel=0, peakIdx=None, valleyIdx=None):
        for plot in self.axes:
            plot.markPeaks(channel, peakIdx, valleyIdx)

    # mark peaks 
    def removePeaks(self):
        for plot in self.axes:
            plot.removePeaks()

    # removes all plots
    def clearAll(self):
        self.clear()
        self.PlotNbr = {}  # empty dictionary
        self.Nplots = 0
        self.axes = []

        # gets teh current mouse click position

    def getClickPosition(self):
        channel = self.sender().channel
        position = self.sender().mousePos
        # print('getClickPosition: channel: %d' % channel, ' position: %f,%f ' %(position[0],position[1]))
        return [channel, position]

    # converts X data to sample
    def convXtoSample(self, xVal, roundMethod='nearest'):
        if roundMethod == 'floor':
            return int(math.floor(xVal * self.samplingRate_Hz))
        if roundMethod == 'ceil':
            return int(math.ceil(xVal * self.samplingRate_Hz))
        if roundMethod == 'nearest':
            return int(round(xVal * self.samplingRate_Hz))

    # return the limits of the viewport
    # returns [ [xmin,xmax] , [ymin,ymax] ]
    def getLimits(self):
        return self.axes[0].viewRange()  # any axes element will do. I am using channel 0

    # sets the limits of the viewport
    # ylim:  list of lists of the type [ymin,ymax] or None, for each channel
    def setLimits(self, xlim=None, ylim=[None]):
        if xlim is not None:
            for plot in self.axes:
                plot.setXRange(xlim[0], xlim[1], padding=None, update=True)
        for plot, y in zip(self.axes, ylim):
            if y is not None:
                plot.setYRange(y[0], y[1], padding=None, update=True)

        plot.update

    # add highlight region
    # selection type:  'interval','point'
    # channels:  'all' add to all avaiable channels,   list: list of channels
    def addSelection(self, selectionType, channels='all'):
        if channels == 'all':
            channels = range(self.Nplots)

        [xlim, _] = self.getLimits()
        if selectionType == 'interval':
            minX = xlim[0] + (xlim[1] - xlim[0]) / 3
            maxX = xlim[1] - (xlim[1] - xlim[0]) / 3
        if selectionType == 'point':
            minX = xlim[0] + (xlim[1] - xlim[0]) / 2
            maxX = None

        for ch in channels:
            self.axes[ch].addSelection(minX, maxX, selectionType)

    # remove all highlighted regions
    # channels:  'all' add to all avaiable channels,   list: list of channels
    def removeSelections(self, channels='all'):
        if channels == 'all':
            channels = range(self.Nplots)

        for ch in channels:
            self.axes[ch].removeSelection()

    # adjusts the limits of the crop region
    # channels:  'all' add to all avaiable channels,   list: list of channels
    def adjusPosSelection(self, minX, maxX, channels='all'):
        if channels == 'all':
            channels = range(self.Nplots)

        for ch in channels:
            if self.axes[ch].selectionType == 'interval':
                self.axes[ch].selection.setRegion([minX, maxX])
            if self.axes[ch].selectionType == 'point':
                self.axes[ch].selection.setValue(minX)

    # adjusts the limits of the crop region
    # channels:  'all' add to all avaiable channels,   list: list of channels
    def lockSelection(self, lock=True, channels='all'):
        if channels == 'all':
            channels = range(self.Nplots)

        for ch in channels:
            self.axes[ch].selection.setMovable(not lock)

    # adjusts the limits of the highlighted regions across all channels
    def alignSelections(self):
        if self.sender().selectionType == 'interval':
            minX, maxX = self.sender().selection.getRegion()
        if self.sender().selectionType == 'point':
            minX = self.sender().selection.value()
            maxX = None

        self.adjusPosSelection(minX, maxX)

    # returns the position of the highlighted rgion
    # this function returns the limits in x units and also in samples
    # if selection type==interval, returns [minX,maxX,sampleMin,sampleMax]
    # if selection type==point, returns [minX,sampleMin]
    def getSelectionPos(self, channel):
        try:
            selectionType = self.axes[channel].selectionType
            if selectionType == 'interval':
                [minX, maxX] = self.axes[channel].selection.getRegion()
                sampleMin = self.convXtoSample(minX, 'ceil')
                sampleMax = self.convXtoSample(maxX, 'floor')

                if sampleMin < 0:
                    sampleMin = 0
                if sampleMax > self.Npoints:
                    sampleMax = self.Npoints - 1

                minX = self.xData[sampleMin]
                maxX = self.xData[sampleMax]

                return [minX, maxX, sampleMin, sampleMax]

            if selectionType == 'point':
                minX = self.axes[channel].selection.value()
                sampleMin = self.convXtoSample(minX, 'ceil')

                if sampleMin < 0:
                    sampleMin = 0

                minX = self.xData[sampleMin]

                return [minX, sampleMin]

        except AttributeError:
            print('no region selected')
            return None
