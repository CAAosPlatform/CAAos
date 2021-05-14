#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore

import ARIPlotWidget
import ARsetup
import pyqtgraph as pg

# copy pyQtConf from signalPlotWidget to here
pyQtConf = ARIPlotWidget.pyQtConf


class signalPlot(ARIPlotWidget.signalPlot):

    def createFreqRegions(self, values=[[0.02, 0.07], [0.07, 0.20], [0.20, 0.50]], colors=['#d5e5ff', '#d7f4d7', '#ffe6d5']):
        alpha = '80'
        for i in range(len(values)):
            selection = pg.LinearRegionItem(values=values[i], orientation=pg.LinearRegionItem.Vertical, movable=False,
                                            brush=pg.mkBrush(color=colors[i] + alpha))
            selection.setZValue(-10)
            self.addItem(selection, ignoreBounds=True)

    def hLine(self, yVal=1.0, xInterval=[0, 1]):
        self.plot(xInterval, yVal * np.ones(2), pen=pg.mkPen(color='r', width=1, style=QtCore.Qt.DashLine))


class plotArray(ARIPlotWidget.plotArray):
    # class to be instanced in addNewPlot funcion member
    newPlotClass = signalPlot

    # adds new plot. All the plots must have the same number of points
    # yData format: list of lists of the type [data_i,color_i,label_i]
    # where data_i is a numpy array or None
    def addNewPlot(self, yData=None, yUnit='adim', title=None, logY=False, legend=False):

        if self.side.upper() == 'R':
            self.xData = self.data.PSD_R.freq
        else:
            self.xData = self.data.PSD_L.freq

        self.Npoints = len(self.xData)

        yData = [[np.zeros(self.Npoints), c, l] if y is None else [y, c, l] for y, c, l in yData]

        newPlot = self.newPlotClass(self.xData, 'Frequency', 'Hz', yData, yUnit=yUnit, title=title, logY=logY, legend=legend)

        # newPlot.addLegend(yLabel)
        newPlot.createFreqRegions(values=[ARsetup.freqRangeDic['VLF'], ARsetup.freqRangeDic['LF'], ARsetup.freqRangeDic['HF']],
                                  colors=[ARsetup.freqRangeColors['VLF'], ARsetup.freqRangeColors['LF'], ARsetup.freqRangeColors['HF']])

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

    def markAvgRanges(self, plotNbr=0, avgValues=[1.0, 1.0, 1.0]):
        for fRange, avgVal in zip(['VLF', 'LF', 'HF'], avgValues):
            self.axes[plotNbr].hLine(avgVal, ARsetup.freqRangeDic[fRange])
