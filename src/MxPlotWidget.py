#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

import ARIPlotWidget
import pyqtgraph as pg

# copy pyQtConf from signalPlotWidget to here
pyQtConf = ARIPlotWidget.pyQtConf

class plotArray(ARIPlotWidget.plotArray):

    # class to be instanced in addNewPlot funcion member
    newPlotClass = ARIPlotWidget.signalPlot

    # adds new plot. All the plots must have the same number of points
    # yData format: list of lists of the type [data_i,color_i,label_i]
    # where data_i is a numpy array or None
    def addNewPlot(self, yData=None, yUnit='adim', title=None, logY=False, legend=False):

        if self.side.upper() == 'R':
            self.xData = np.arange(self.data.Mx_R.nEpochs)
        else:
            self.xData = np.arange(self.data.Mx_L.nEpochs)

        self.Npoints = len(self.xData)

        yData = [[np.zeros(self.Npoints), c, l] if y is None else [y, c, l] for y, c, l in yData]

        newPlot = self.newPlotClass(self.xData, 'Epoch', '', yData, yUnit=yUnit, title=title, logY=logY, legend=legend)

        newPlot.signalCurve[0].setSymbol('o')
        newPlot.signalCurve[0].setSymbolPen(QtGui.QColor(0, 0, 0))
        newPlot.signalCurve[0].setPen(pg.mkPen(style=QtCore.Qt.DashLine))

        newPlot.setTicks(axis='x', values=self.xData+1)


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


        # set limits
        self.setLimits(xlim=[-1, len(self.xData)], ylim=[None])

        if self.Nplots % self.numberOfColumns == 0:
            self.nextRow()

    def markAvg(self, plotNbr=0, avgValue=1.0,legend=None):
        self.axes[plotNbr].hLine(avgValue, [self.xData[0], self.xData[-1]],legend)