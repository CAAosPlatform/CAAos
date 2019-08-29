#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtGui,QtCore,QtWidgets
from customWidgets import signalTabWidget
from signalPlotWidget import plotArray

#dict format:  '#code' : (paramValue,'string name')
signalTypesDict= {0: ('none','None'),1: ('CBFV_R','CBFV R'),2: ('CBFV_L','CBFV L'), 3: ('ABP','ABP'),4:('ETCO2','ETCO2')}

class signalPropsWidget(QtWidgets.QWidget):
    
    def __init__(self,data):
        QtWidgets.QWidget.__init__(self)
        self.data=data
        self.initUI()
        
    def initUI(self):
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)
        
        #table with signal Information
        self.signalTab = signalPropsTab(['Label','Signal type'],[200,100],83)
        hbox.addWidget(self.signalTab)
        
        for s in self.data.signals:
            self.signalTab.addSignal(channel=s.channel,label=s.label,sigType=s.sigType)
        
        #apply button
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.applyButton.setFixedWidth(100)
        self.applyButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.applyButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.applyButton.clicked.connect(self.applyProps)
        hbox.addWidget(self.applyButton)
        hbox.addStretch(1)
        
        #plot area
        self.plotArea=plotArray(self.data)
        self.plotArea.plotAllsignals()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.plotArea,2)
        self.setLayout(vbox)
        
    def applyProps(self):
        for ch in self.signalTab.channels:
            channel = ch.channel
            self.data.signals[channel].setType(ch.sigType)
            self.data.signals[channel].setLabel(ch.label)
        self.applyButton.clearFocus()
        
        self.plotArea.replotAllsignals()

    def updateTab(self):
        self.plotArea.replotAllsignals()
        
class signalPropsTab(signalTabWidget):
    def __init__(self,colLabels,colSizes,colLabelsOffset):
        signalTabWidget.__init__(self,colLabels,colSizes,colLabelsOffset)
            
    def addSignal(self,channel,label='name',sigType=None):
        signal=channelSettings(channel,label,sigType,self.colSizes)
        self.vbox.addWidget(signal)
        self.channels.append(signal)
        self.nChannels=len(self.channels)
        
class channelSettings(QtWidgets.QWidget):    

    def __init__(self,channel,label,sigType,colSizes):
        QtWidgets.QWidget.__init__(self)
        self.channel=channel
        self.label=label
        self.sigType=sigType
        self.colSizes=colSizes
        self.initUI()
    
    def initUI(self):
        #layout
        hbox0 = QtWidgets.QHBoxLayout()
        hbox0.setAlignment(QtCore.Qt.AlignLeft)
        hbox0.setContentsMargins(0,0,0,0);
        self.setLayout(hbox0)

        # channel #
        channelSignal = QtWidgets.QLabel('Channel %d' % self.channel)
        channelSignal.setFixedWidth(70)
        
        # label
        labelSignal = QtWidgets.QLineEdit()
        labelSignal.setText(self.label)
        labelSignal.setFixedWidth(self.colSizes[0])
        labelSignal.editingFinished.connect(lambda: self.registerOptions('label'))
        labelSignal.returnPressed.connect(lambda: self.registerOptions('label'))
        labelSignal.textChanged.connect(lambda: self.registerOptions('label'))

        # signalType
        signalType = QtWidgets.QComboBox()
        signalType.setFixedWidth(self.colSizes[1])
        signalType.addItems([x[1] for x  in signalTypesDict.values()])
        for key, value in signalTypesDict.items():
            if value[0]==self.sigType:
                signalType.setCurrentIndex(key)
                break
        signalType.currentIndexChanged.connect(lambda: self.registerOptions('sigType'))
        
        #monta o layout
        hbox0.addWidget(channelSignal)
        hbox0.addWidget(labelSignal)
        hbox0.addWidget(signalType)
    
    def registerOptions(self,type):
        if type == 'label':
            self.label = self.sender().text().replace(' ','_')
        if type == 'sigType':
            self.sigType=signalTypesDict[self.sender().currentIndex()][0]

        
        
