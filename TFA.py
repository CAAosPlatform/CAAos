#!/bin/python

# -*- coding: utf-8 -*-
import sys
import numpy as np
import tools
import ARsetup
from matplotlib import pyplot as plt
import copy
from PSDestimator import PSDestimator

def diferencaPedro(numpyData,file,label,isComplex=False):
    if isComplex:
        resultadoPedro=np.loadtxt(file).view(complex)
    else:
        resultadoPedro=np.loadtxt(file)
    print("maior erro em modulo %s : %f" % (label,np.amax(np.absolute(numpyData-resultadoPedro))))
    

def ovelapAdjustment(sizeSignal,wlength,overlap):
    nSegments=np.floor((sizeSignal-wlength)/(wlength*(1-overlap)))+1  # atention: in python 3.x, / is float division!
    if nSegments>0:
        shift=int((sizeSignal-wlength)/(nSegments-1))  # atention: in python 3.x, / is float division!
        newOverlap=(wlength-shift)/wlength
    else:
        print('ERROR: window length larger than the signal!')
        newOverlap=overlap
        
    return newOverlap

class transferFunctionAnalysis():
    def __init__(self,welchData):
        self.welch=welchData
        self.nSegments=self.welch.nSegments
        self.freq=self.welch.freq
        self.Sxx=self.welch.Sxx
        self.Syy=self.welch.Syy
        self.Sxy=self.welch.Sxy
        self.Syx=self.welch.Syx
        self.freqRangeExtractor = tools.CARfreqRange(self.freq)

    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL' 
    def save(self, fileName,sideLabel='L',freqRange='ALL',writeMode='w'):
        print('Saving .GPC data')

        fileObj=open(fileName,writeMode)
        
        
        fileObj.write('ESTIMATOR_TYPE=%s\n' % self.Htype)
        fileObj.write('SIDE=%s\n' % sideLabel)
        fileObj.write('NPOINTS=%d\n' % len(self.getFreq(freqRange)))

        np.set_printoptions(threshold=np.inf)

        fileObj.write('FREQ_HZ=%s\n' % np.array_str(self.getFreq(freqRange),max_line_width=1000))
        fileObj.write('H_REAL=%s\n' % np.array_str(np.real(self.getH(freqRange,coherenceTreshold=False)),max_line_width=1000))
        fileObj.write('H_IMAG=%s\n' % np.array_str(np.imag(self.getH(freqRange,coherenceTreshold=False)),max_line_width=1000))
        fileObj.write('H_GAIN=%s\n' % np.array_str(self.getGain(freqRange,coherenceTreshold=False),max_line_width=1000))
        fileObj.write('H_PHASE_DEG=%s\n' % np.array_str(self.getPhase(freqRange,coherenceTreshold=False,removeNegativePhase=False)*180/np.pi,max_line_width=1000))
        fileObj.write('H_COHERENCE=%s\n' % np.array_str(self.getCoherence(freqRange),max_line_width=1000))
        fileObj.write('='*80 + '\n' )

        fileObj.close()
        print('Ok!')
        
    #estimate H1
    def computeH1(self):
        self.Htype='H1'
        self.H=np.divide(self.Sxy,self.Sxx)
        self.coherence=np.divide(np.absolute(self.Sxy)**2,np.multiply(self.Sxx,self.Syy))

        #diferencaPedro(self.H,'../codigoPedro/lixo_TF_L.txt','TF_L',isComplex=True)
        #diferencaPedro(self.coherence,'../codigoPedro/lixo_Coh_L.txt','Coh_L',isComplex=False)

    #estimate H2
    def computeH2(self):
        self.Htype='H2'
        self.H=np.divide(self.Syy,self.Syx)
        self.coherence=np.divide(np.absolute(self.Sxy)**2,np.multiply(self.Sxx,self.Syy))

        #diferencaPedro(self.H,'../codigoPedro/lixo_TF_L.txt','TF_L',isComplex=True)
        #diferencaPedro(self.coherence,'../codigoPedro/lixo_Coh_L.txt','Coh_L',isComplex=False)

    #returns a copy of the signal with NaNs where coherence< limit
    def applyCohTreshold(self,signal):
        temp=copy.deepcopy(signal)
        temp[ self.coherence < ARsetup.cohThresholdDict[self.nSegments] ]=np.nan
        return temp

    def getFreq(self,freqRange='ALL'):
        return self.freqRangeExtractor.getFreq(freqRange)

    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'full'
    def getH(self,freqRange='ALL',coherenceTreshold=False):
        if coherenceTreshold:
            values = self.applyCohTreshold(self.H)
        else:
            values = self.H
            
        return self.freqRangeExtractor.getSignal(values,freqRange)

    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getCoherence(self,freqRange='ALL'):
        return self.freqRangeExtractor.getSignal(self.coherence,freqRange)

    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getGain(self,freqRange='ALL',coherenceTreshold=False):
        if coherenceTreshold:
            values = self.applyCohTreshold(np.absolute(self.H))
        else:
            values = np.absolute(self.H)
            
        return self.freqRangeExtractor.getSignal(values,freqRange)
    
    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getPhase(self,freqRange='ALL',coherenceTreshold=False,removeNegativePhase=False):
        if coherenceTreshold:
            values = self.applyCohTreshold(np.angle(self.H))
        else:
            values = np.angle(self.H)

        #remove negative phases
        if removeNegativePhase:
            values[ (values < 0) & (self.freq < 0.1) ]=np.nan
    
        return self.freqRangeExtractor.getSignal(values,freqRange)

    def getCoherenceStatistics(self,freqRange='ALL'):
        return self.freqRangeExtractor.getStatistics(self.coherence,freqRange)

    def getGainStatistics(self,freqRange='ALL',coherenceTreshold=False):
        if coherenceTreshold:
            values = self.applyCohTreshold(np.absolute(self.H))
        else:
            values = np.absolute(self.H)
            
        return self.freqRangeExtractor.getStatistics(values,freqRange)
    
    def getPhaseStatistics(self,freqRange='ALL',coherenceTreshold=False,removeNegativePhase=False):
        if coherenceTreshold:
            values = self.applyCohTreshold(np.angle(self.H))
        else:
            values = np.angle(self.H)

        #remove negative phases
        if removeNegativePhase:
            values[ (values < 0) & (self.freq < 0.1) ]=np.nan
            
        return self.freqRangeExtractor.getStatistics(values,freqRange)

    def savePlot(self,fileNamePrefix=None,fileType='png',figDpi=250,fontSize=6):
        fig, ax= plt.subplots(3,1, sharex=True, figsize=[8,5])
        freqRangeColors=['#d5e5ff','#d7f4d7','#ffe6d5'];
        #---------------------
        #Gain Plot
        #---------------------
        ax[0].plot(self.getFreq(freqRange='FULL'),self.getGain(freqRange='FULL'), c='k',linewidth=1,linestyle=(0, (5, 5)),label='_nolegend_')
        ax[0].plot(self.getFreq(freqRange='FULL'),self.getGain(freqRange='FULL',coherenceTreshold=True), c='k',linewidth=1.2,marker='o',markerSize=2.5)
        #ax[0].semilogy(self.getFreq(freqRange='FULL'),abs(self.Syx), c='k',linewidth=1,label='_nolegend_')
        #ax[0].semilogy(self.getFreq(freqRange='FULL'),abs(self.Sxy), c='b',linewidth=1,label='_nolegend_')
        #ax[0].semilogy(self.getFreq(freqRange='FULL'),abs(self.Sxx), c='r',linewidth=1,label='_nolegend_')
        ax[0].set_ylabel("Gain [ adim. ]")
        #ax[0].legend(["Python"])
        ax[0].set_xlim([0,ARsetup.freqRangeDic['HF'][1]])
        ax[0].set_ylim([0,1.05*np.nanmax(self.getGain(freqRange='ALL',coherenceTreshold=True))])
        ax[0].grid(axis='x')

        #plot average horizontal lines for each frequency range
        ymin, ymax = ax[0].get_ylim()
        deltaY=ymax-ymin
        for i,range in enumerate(['VLF', 'LF', 'HF']):
            [mean,std,_,_] = self.getGainStatistics(freqRange=range,coherenceTreshold=True)
            ax[0].hlines(mean,ARsetup.freqRangeDic[range][0],ARsetup.freqRangeDic[range][1],linestyle='dashed', color='red',linewidth=0.7)
            ax[0].axvspan(ARsetup.freqRangeDic[range][0],ARsetup.freqRangeDic[range][1], facecolor=freqRangeColors[i], alpha=1.0)
            ax[0].text(ARsetup.freqRangeDic[range][0], deltaY*0.03+mean, "$\mu=${0:.2f}".format(mean) + '\n' + "$ \sigma=${0:.2f}".format(std),color='r',fontSize=fontSize)
        
        #---------------------
        #Phase Plot
        #---------------------
        ax[1].plot(self.getFreq(freqRange='FULL'),self.getPhase(freqRange='FULL')*180/np.pi, c='k',linewidth=1,linestyle=(0, (5, 5)))
        ax[1].plot(self.getFreq(freqRange='FULL'),self.getPhase(freqRange='FULL',coherenceTreshold=True,removeNegativePhase=True)*180/np.pi, c='k',linewidth=1.2,marker='o',markerSize=2.5)
        ax[1].set_ylabel("Phase [ degree ]")
        #ax[1].set_xlim([0,ARsetup.freqRangeDic['HF'][1]])
        ax[1].set_ylim([0,1.05*np.nanmax(self.getPhase(freqRange='ALL',coherenceTreshold=True))*180/np.pi])
        ax[1].grid(axis='x')
        
        #plot average horizontal lines for each frequency range
        ymin, ymax = ax[1].get_ylim()
        deltaY=ymax-ymin
        for i,range in enumerate(['VLF', 'LF', 'HF']):
            [mean,std,_,_] = self.getPhaseStatistics(freqRange=range,coherenceTreshold=True,removeNegativePhase=True)
            mean*=180/np.pi
            std*=180/np.pi
            ax[1].hlines(mean,ARsetup.freqRangeDic[range][0],ARsetup.freqRangeDic[range][1],linestyle='dashed', color='red',linewidth=0.7)
            ax[1].axvspan(ARsetup.freqRangeDic[range][0],ARsetup.freqRangeDic[range][1], facecolor=freqRangeColors[i], alpha=1.0)
            ax[1].text(ARsetup.freqRangeDic[range][0], deltaY*0.03+mean, "$\mu=${0:.2f}".format(mean) + '\n' + "$ \sigma=${0:.2f}".format(std),color='r',fontSize=fontSize)
        
        #---------------------
        #Coherence
        #---------------------
        ax[2].plot(self.getFreq(freqRange='FULL'),self.getCoherence(freqRange='FULL'), c='k',linewidth=1.2,marker='o',markerSize=2.5)
        ax[2].set_ylabel("Coherence [ adim. ]")
        ax[2].set_xlabel("Frequency (Hz)")
        #ax[2].set_xlim([0,ARsetup.freqRangeDic['HF'][1]])
        ax[2].set_ylim([0,1])
        ax[2].grid(axis='x')
        
        #plot average horizontal lines for each frequency range
        ymin, ymax = ax[2].get_ylim()
        deltaY=ymax-ymin
        for i,range in enumerate(['VLF', 'LF', 'HF']):
            [mean,std,_,_] = self.getCoherenceStatistics(freqRange=range)
            ax[2].hlines(mean,ARsetup.freqRangeDic[range][0],ARsetup.freqRangeDic[range][1],linestyle='dashed', color='red',linewidth=0.7)
            ax[2].axvspan(ARsetup.freqRangeDic[range][0],ARsetup.freqRangeDic[range][1], facecolor=freqRangeColors[i], alpha=1.0)
            ax[2].text(ARsetup.freqRangeDic[range][0], deltaY*0.03+mean, "$\mu=${0:.2f}".format(mean) + '\n' + "$ \sigma=${0:.2f}".format(std),color='r',fontSize=fontSize)
        
        #threshold
        ax[2].axhspan(0,ARsetup.cohThresholdDict[self.nSegments], facecolor='0.9', alpha=1.0)

        fig.tight_layout()
        plt.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.95, wspace=None, hspace=0.1)
        
        if fileNamePrefix is not None:
            plt.savefig(fileNamePrefix + '.' + fileType,dpi=figDpi,format=fileType,transparent=True)
        else:
            plt.show()

if __name__ == '__main__':


    if sys.version_info.major == 2:
        sys.stdout.write("Sorry! This program requires Python 3.x\n")
        sys.exit(1)
    
    ABP=np.loadtxt('../codigoPedro/lixo_ABP.txt')
    CBFv_L=np.loadtxt('../codigoPedro/lixo_CBF_L.txt')
    samplingFrequency_Hz=100

    overlap=59.99/100 #overlap
    segmentLength_s=102.4
    windowType='hanning'
    overlap_adjust=True
    if overlap_adjust:
        overlap=ovelapAdjustment(ABP.shape[0],segmentLength_s*samplingFrequency_Hz,overlap)

    #Power spectrum Estimation
    welch=PSDestimator(ABP,CBFv_L,samplingFrequency_Hz, overlap,segmentLength_s,windowType,removeBias=False)
    welch.computeWelch()
    welch.filterAll(filterType='rect',nTaps=2,keepFirst=True)
    #Start TF analysis
    TF=transferFunctionAnalysis(welchData=welch)
    TF.computeH1()

    welch.save(fileName='lixo.PSD',freqRange='ALL')
    TF.save(fileName='lixo.TF',sideLabel='R',freqRange='ALL')
    if True:
        TF.savePlot(fileNamePrefix=None)
    else:
        TF.savePlot(fileNamePrefix='lixo',fileType='png',figDpi=250,fontSize=6)
        TF.savePlot(fileNamePrefix='lixo',fileType='svg',figDpi=250,fontSize=6)
        TF.savePlot(fileNamePrefix='lixo',fileType='pdf',figDpi=250,fontSize=6)
