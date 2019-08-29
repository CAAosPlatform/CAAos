#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtGui,QtCore,QtWidgets
from customWidgets import signalTabWidget
from signalPlotWidget import plotArray

#dict format:  '#code' : (paramValue,'string name')
filterMethodDict={0: ('movingAverage','Moving average')}
syncMethodDict={0: ('correlation','Correlation')}


class signalSyncFilterWidget(QtWidgets.QWidget):
    signal_apply = QtCore.pyqtSignal(bool)
    
    def __init__(self,patientData):
        QtWidgets.QWidget.__init__(self)
        self.data=patientData
        self.initUI()
        
    def initUI(self):
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)
        
        #table with signal Information
        self.signalTab = signalSyncFilterTab(['Label','Sig. type','Sync.','Filter'],[150,80,50,50],83)
        hbox.addWidget(self.signalTab)
        
        for s in self.data.signals:
            self.signalTab.addSignal(channel=s.channel,label=s.label,sigType=s.sigType)
        
        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)
        
        # sync method
        default=0  # correlation
        self.syncMethod=syncMethodDict[default][0]
        syndcMethodWidget = QtWidgets.QComboBox()
        syndcMethodWidget.setFixedWidth(130)
        syndcMethodWidget.addItems([x[1] for x  in syncMethodDict.values()])
        syndcMethodWidget.setCurrentIndex(default)  
        syndcMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('syncMethod'))
        
        formLayout.addRow('Sync. Method',syndcMethodWidget)
        
        # filter method
        default=0  # moving average
        self.filterMethod=filterMethodDict[default][0]
        filterMethodWidget = QtWidgets.QComboBox()
        filterMethodWidget.setFixedWidth(130)
        filterMethodWidget.addItems([x[1] for x  in filterMethodDict.values()])
        filterMethodWidget.setCurrentIndex(default)  
        filterMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('filterMethod'))
        
        formLayout.addRow('Filter Type',filterMethodWidget)
        
        #apply sync button
        self.applySyncButton = QtWidgets.QPushButton("Sync")
        self.applySyncButton.setFixedWidth(100)
        self.applySyncButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.applySyncButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.applySyncButton.clicked.connect(self.applySync)
        hbox.addWidget(self.applySyncButton)

        #apply filter button
        self.applyFilterButton = QtWidgets.QPushButton("Filter")
        self.applyFilterButton.setFixedWidth(100)
        self.applyFilterButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.applyFilterButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.applyFilterButton.clicked.connect(self.applyFilter)
        hbox.addWidget(self.applyFilterButton)
        hbox.addStretch(1)

        #plot area
        self.plotArea=plotArray(self.data)
        self.plotArea.plotAllsignals()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.plotArea)
        self.setLayout(vbox)

    def updateTab(self):
        self.plotArea.replotAllsignals()
        for ch in range(self.signalTab.nChannels):
            channel=self.signalTab.channels[ch]
            channel.updateLabels(self.data.signals[ch].label,self.data.signals[ch].sigType)
                
    def registerOptions(self,type):
        if type == 'syncMethod':
            self.syncMethod=syncMethodDict[self.sender().currentIndex()][0]
        if type == 'filterMethod':
            self.filterMethod=filterMethodDict[self.sender().currentIndex()][0]

    #synchronize signals
    def applySync(self):
        
        self.data.removeRRmarks()
        self.data.removeBeat2beat()
        
        listSyncSignals=[]
        for ch in range(self.signalTab.nChannels):
            channel=self.signalTab.channels[ch]
            if channel.sync:
                listSyncSignals.append(ch)
            
        self.data.synchronizeSignals(listSyncSignals,method=self.syncMethod)
        
        self.applySyncButton.clearFocus()
        self.plotArea.replotAllsignals()

    #filter signals
    def applyFilter(self):
        
        self.data.removeRRmarks()
        self.data.removeBeat2beat()
        
        for ch in range(self.signalTab.nChannels):
            channel=self.signalTab.channels[ch]
            if channel.filter:
                self.data.signals[ch].LPfilter(method=self.filterMethod,nTaps=3)

        self.applyFilterButton.clearFocus()
        self.plotArea.replotAllsignals()


class signalSyncFilterTab(signalTabWidget):
    def __init__(self,colLabels,colSizes,colLabelsOffset):
        signalTabWidget.__init__(self,colLabels,colSizes,colLabelsOffset)
            
    def addSignal(self,channel,label,sigType):
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
        self.sync=True
        self.filter=False
        self.colSizes=colSizes
        self.initUI()
    
    def initUI(self):
        #layout
        hbox0 = QtWidgets.QHBoxLayout()
        hbox0.setAlignment(QtCore.Qt.AlignLeft)
        hbox0.setContentsMargins(0,0,0,0);
        self.setLayout(hbox0)

        #text
        channelSignal = QtWidgets.QLabel('Channel %d' % self.channel)
        channelSignal.setFixedWidth(70)
        
        #label
        self.labelSignal = QtWidgets.QLabel(self.label)
        self.labelSignal.setFixedWidth(self.colSizes[0])
        
        #sigType
        self.signalType = QtWidgets.QLabel(str(self.sigType))
        self.signalType.setFixedWidth(self.colSizes[1])

        #sync
        syncSignal = QtGui.QCheckBox('', self)
        syncSignal.setFixedWidth(self.colSizes[2])
        syncSignal.setChecked(True)
        syncSignal.stateChanged.connect(lambda: self.registerContents('sync') )

        #filter
        filterSignal = QtGui.QCheckBox('', self)
        filterSignal.setFixedWidth(self.colSizes[3])
        filterSignal.setChecked(False)
        filterSignal.stateChanged.connect(lambda: self.registerContents('filter') )
        
        #monta o layout
        hbox0.addWidget(channelSignal)
        hbox0.addWidget(self.labelSignal)
        hbox0.addWidget(self.signalType)
        hbox0.addWidget(syncSignal)
        hbox0.addWidget(filterSignal)

    def updateLabels(self,label,sigType):
        self.label=label
        self.sigType=sigType
        self.labelSignal.setText(self.label)
        self.signalType.setText(str(self.sigType))
    
    def registerContents(self,type):
        if type == 'sync':
            self.sync = self.sender().isChecked()
        if type == 'filter':
            self.filter=self.sender().isChecked()
