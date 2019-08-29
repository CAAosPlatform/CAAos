#! /usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtGui,QtCore,QtWidgets
from customWidgets import signalTabWidget
from signalPlotWidget import signalPlot,pyQtConf
import pyqtgraph as pg

#dict format:  '#code' : (paramValue,'string name')
filterMethodDict={0: ('movingAverage','Moving average')}
resampleFsMethodDict={0: ('min','Min'), 1: ('max','Max'), 2: ('custom','Custom')}
resampleInterpolationMethod={0: ('zero','Zero'), 1: ('linear','Linear'), 2: ('quadratic','Quadratic'), 3: ('cubic','Cubic')}


class signalBeat2beatWidget(QtWidgets.QWidget):
    signal_apply = QtCore.pyqtSignal(bool)
    
    def __init__(self,patientData):
        QtWidgets.QWidget.__init__(self)
        self.data=patientData
        self.initUI()
        
    def initUI(self):
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setAlignment(QtCore.Qt.AlignTop)
        
        formLayout = QtWidgets.QFormLayout()
        hbox.addLayout(formLayout)
        
        # Resampling method
        default=3 # quadratic
        self.resamplingMethod=resampleInterpolationMethod[default][0]
        resamplingMethodWidget = QtWidgets.QComboBox()
        resamplingMethodWidget.setFixedWidth(130)
        resamplingMethodWidget.addItems([x[1] for x  in resampleInterpolationMethod.values()])
        resamplingMethodWidget.setCurrentIndex(default)   
        resamplingMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('resamplingMethod'))
        
        formLayout.addRow('Resampling method',resamplingMethodWidget)
        
        # custom value option
        default=4.0
        self.customFs = QtWidgets.QDoubleSpinBox()
        self.customFs.setRange (2,10)
        self.customFs.setDecimals(0)
        self.customFs.setSingleStep(1)
        self.customFs.setFixedWidth(130)
        self.customFs.setValue(default)
        self.Fs_custom=default
        self.customFs.valueChanged.connect(lambda: self.registerOptions('CustomFs'))
        
        formLayout.addRow('Sampling freq. (Hz)',self.customFs)
        
        # filter method
        default=0  # moving average
        self.filterMethod=filterMethodDict[default][0]
        filterMethodWidget = QtWidgets.QComboBox()
        filterMethodWidget.setFixedWidth(130)
        filterMethodWidget.addItems([x[1] for x  in filterMethodDict.values()])
        filterMethodWidget.setCurrentIndex(default)  
        filterMethodWidget.currentIndexChanged.connect(lambda: self.registerOptions('filterMethod'))
        
        formLayout.addRow('Filter Type',filterMethodWidget)
        
        #apply beat to beat
        self.applyBeatButton = QtWidgets.QPushButton("Extract\nbeat-to-beat")
        self.applyBeatButton.setFixedWidth(100)
        self.applyBeatButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.applyBeatButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.applyBeatButton.clicked.connect(self.applyBeat)
        hbox.addWidget(self.applyBeatButton)
        
        #apply filter button
        self.applyFilterButton = QtWidgets.QPushButton("Filter")
        self.applyFilterButton.setFixedWidth(100)
        self.applyFilterButton.setEnabled(False)
        self.applyFilterButton.setSizePolicy( QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Preferred)
        self.applyFilterButton.setStyleSheet("background-color:rgb(192,255,208)") # light green
        self.applyFilterButton.clicked.connect(self.applyFilter)
        hbox.addWidget(self.applyFilterButton)
        hbox.addStretch(1)
                
        #plot area
        self.plotArea=plotArrayBeat2Beat(self.data)
        #self.plotArea.plotAllsignals()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.plotArea)
        self.setLayout(vbox)

    def updateTab(self):
        
        try:
            self.plotArea.plotAllsignals()
        except AttributeError:
            self.plotArea.clearAll()
        
        #enables/disables buttons
        if self.data.hasRRmarks:
            self.applyBeatButton.setEnabled(True)
        else:
            print('nao tem RR')
            self.applyBeatButton.setEnabled(False)
            self.plotArea.clearAll()
            
        self.applyFilterButton.setEnabled(self.data.hasB2Bdata)
            
            
    def registerOptions(self,type):
        if type == 'filterMethod':
            self.filterMethod=filterMethodDict[self.sender().currentIndex()][0]
        if type == 'resamplingMethod':
            self.resamplingMethod=resampleInterpolationMethod[self.sender().currentIndex()][0]
        if type == 'CustomFs':
            self.Fs_custom=self.sender().value()

    #synchronize signals
    def applyBeat(self):
        self.data.getBeat2beat(resampleRate_Hz=self.Fs_custom,resampleMethod=self.resamplingMethod)
        self.applyBeatButton.clearFocus()
        self.plotArea.plotAllsignals()
        self.applyFilterButton.setEnabled(True)

    #filter signals
    def applyFilter(self):
        self.data.LPfilterBeat2beat(method=self.filterMethod,nTaps=10)
        self.applyFilterButton.clearFocus()
        self.plotArea.replotAllsignals()

class plotArrayBeat2Beat(pg.GraphicsLayoutWidget):

    def __init__(self,patientData,nCols=1):
        super(plotArrayBeat2Beat,self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        self.data=patientData
        self.PlotNbr={}   # empty dictionary
        self.Nplots=0
        self.axes=[]
        self.numberOfColumns=nCols
                
    #plot all signals, destroying any previously created elements (axes, labels, etc)  SLOWER!
    def plotAllsignals(self):
        self.clearAll()
        
        self.xData=self.data.signals[0].beat2beatData.xData
        for s in self.data.signals:
            yData=[ [s.beat2beatData.avg,pyQtConf['plotColors']['blue'],'avg'] ]
            self.addNewPlot(channel=s.channel,title=s.label,yData=yData,yUnit=s.unit)
    
        #plot all signals, keeping any previously created elements (axes, labels, etc)   FASTER!
    def replotAllsignals(self):
        self.xData=self.data.signals[0].beat2beatData.xData
        for s in self.data.signals:
            yData=[s.beat2beatData.max,s.beat2beatData.avg,s.beat2beatData.min]
            self.axes[s.channel].replot(self.xData,yData)
            self.axes[s.channel].mysetTitle(s.label)
            
    # class to be instanced in addNewPlot funcion member
    newPlotClass = signalPlot
    
    #adds new plot. All the plots must have the same number of points
    def addNewPlot(self,channel,title,yData,yUnit):

        newPlot = self.newPlotClass(channel,self.xData,'Time','s',yData,yUnit=yUnit,title=title)
            
        if self.Nplots>0:
          
            #removes x ticks and X labels of the last plot
            self.axes[-1].hideXlabel()
            
            # links X axis between the plots so that if we move one plot, they all move together
            newPlot.setXLink(self.axes[0])

        self.addItem(newPlot)
        
        newPlot.activateMouseEvents()
        newPlot.signal_mouseClicked.connect(self.getClickPosition)
        
        self.axes.append(newPlot)
        self.PlotNbr[channel]=self.Nplots
        self.Nplots=len(self.axes)
        
        if self.Nplots % self.numberOfColumns==0:
            self.nextRow()
            
    #removes all plots
    def clearAll(self):
        self.clear()
        self.PlotNbr={}   # empty dictionary
        self.Nplots=0
        self.axes=[]
        
    #gets teh current mouse click position
    def getClickPosition(self):
        channel = self.sender().channel
        position = self.sender().mousePos
        #print('getClickPosition: channel: %d' % channel, ' position: %f,%f ' %(position[0],position[1]))
        return [channel,position]

    # converts X data to sample
    def convXtoSample(self,xVal,roundMethod='nearest'):
        if roundMethod =='floor':
            return int(math.floor(xVal*self.samplingRate_Hz))
        if roundMethod == 'ceil':
            return int(math.ceil(xVal*self.samplingRate_Hz))
        if roundMethod == 'nearest':
            return int(round(xVal*self.samplingRate_Hz))
        
    # return the limits of the viewport
    # returns [ [xmin,xmax] , [ymin,ymax] ]
    def getLimits(self):
        return self.axes[0].viewRange()  # any axes element will do. I am using channel 0
        
    # sets the limits of the viewport
    def setLimits(self,xlim=None,ylim=None):
        if xlim is not None:
            for plot in self.axes:
                plot.setXRange(xlim[0],xlim[1],padding=None)
        if ylim is not None:
            for plot in self.axes:
                plot.setYRange(ylim[0],ylim[1],padding=None)
