#! /usr/bin/python

# -*- coding: utf-8 -*-

import numpy as np
from PyQt5 import QtGui, QtWidgets

import ARIPlotWidget

# copy pyQtConf from signalPlotWidget to here
pyQtConf = ARIPlotWidget.pyQtConf


class plotArray(ARIPlotWidget.plotArray):

    def addNewPlot(self, yData=None, yUnit='adim', title=None, logY=False, legend=False):

        if self.side.upper() == 'R':
            self.xData = self.data.ARIARMA_R.timeVals
        else:
            self.xData = self.data.ARIARMA_L.timeVals

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
