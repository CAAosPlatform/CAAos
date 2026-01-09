#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets


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



