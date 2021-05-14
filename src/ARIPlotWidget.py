#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtGui

import pyqtgraph as pg
import signalPlotWidget

# copy pyQtConf from signalPlotWidget to here
pyQtConf = signalPlotWidget.pyQtConf


class signalPlot(signalPlotWidget.signalPlot):

    # yData format: list of lists of the type [data_i,color_i,label_i]
    # where data_i is a numpy array
    def __init__(self, xData=np.array([0, 1, 2]), xlabel='Time', xUnit='s', yData=[[np.array([1, 2, 3]), (255, 0, 0), 'signal']], yUnit='V',
                 title='Signal', logY=False, legend=False):
        channel = 0
        super(signalPlot, self).__init__(channel, xData, xlabel, xUnit, yData, yUnit, title, legend)
        logX = False
        self.logY = logY
        self.setLogMode(logX, self.logY)


class plotArray(pg.GraphicsLayoutWidget):

    def __init__(self, patientData, side='R', nCols=1):
        super(plotArray, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        self.data = patientData
        self.side = side
        self.PlotNbr = {}  # empty dictionary
        self.Nplots = 0
        self.axes = []
        self.numberOfColumns = nCols

    # class to be instanced in addNewPlot funcion member
    newPlotClass = signalPlot

    # adds new plot. All the plots must have the same number of points
    # yData format: list of lists of the type [data_i,color_i,label_i]
    # where data_i is a numpy array or None
    def addNewPlot(self, yData=None, yUnit='adim', title=None, logY=False, legend=False):

        if self.side.upper() == 'R':
            self.xData = self.data.ARI_R.timeVals
        else:
            self.xData = self.data.ARI_L.timeVals

        self.Npoints = len(self.xData)

        yData = [[np.zeros(self.Npoints), c, l] if y is None else [y, c, l] for y, c, l in yData]

        newPlot = self.newPlotClass(self.xData, 'Time', 's', yData, yUnit=yUnit, title=title, logY=logY, legend=legend)

        if self.Nplots > 0:

            # removes x ticks and X labels of the last plot
            self.axes[-1].hideXlabel()

            # links X axis between the plots so that if we move one plot, they all move together
            newPlot.setXLink(self.axes[0])

        self.addItem(newPlot)

        newPlot.activateMouseEvents()
        newPlot.signal_mouseClicked.connect(self.getClickPosition)

        self.axes.append(newPlot)
        self.Nplots = len(self.axes)
        self.PlotNbr[self.Nplots - 1] = self.Nplots - 1

        if self.Nplots % self.numberOfColumns == 0:
            self.nextRow()

    # yData is an list of numpy arrays
    def replot(self, plotNbr, yData):
        self.axes[plotNbr].replot(None, yData,None)

        # self.axes[plotNbr].enableAutoRange(y=True) # 2019/july: pyqtgraph v.0.10.0  It seems logy plot have a bug that crashes when we reset Yrange. This line is a quick fix for the issue

    # removes all plots
    def clearAll(self):
        self.clear()
        self.PlotNbr = {}  # empty dictionary
        self.Nplots = 0
        self.axes = []

        # gets teh current mouse click position

    def getClickPosition(self):
        self.clickChannel = self.sender().channel
        self.clickPosition = self.sender().mousePos
        # print('getClickPosition: channel: %d' % channel, ' position: %f,%f ' %(position[0],position[1]))
        return [self.clickChannel, self.clickPosition]

    # converts X data to sample
    def convXtoSample(self, xVal, roundMethod='floor'):
        index = np.searchsorted(self.xData, xVal, side='left')
        if roundMethod == 'floor':
            return index
        if roundMethod == 'ceil':
            if index < len(self.xData):
                return index + 1
            else:
                return index

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
                if plot.logY:
                    plot.setYRange(np.log10(y[0]), np.log10(y[1]), padding=None, update=True)
                else:
                    plot.setYRange(y[0], y[1], padding=None, update=True)

    # add highlight region
    # selection type:  'interval','point'
    # channels:  'all' add to all avaiable channels,   list: list of channels
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
