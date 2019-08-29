#!/bin/python

# -*- coding: utf-8 -*-
import sys
if sys.version_info.major == 2:
    sys.stdout.write("Sorry! This program requires Python 3.x\n")
    sys.exit(1)
import numpy as np
import ARsetup
from scipy import signal
from matplotlib import pyplot as plt

class ARIanalysis():
    def __init__(self):
        pass

    # iputType:  'STEP'  'IMPULSE'
    def tiecksModel(self,
                    ARIindex,          # 0 to 9
                    fs=50.0,           # in Hz
                    Tresponse=15.0,    # in seconds
                    CBFcontrol=100.0,  # in cm/s
                    ABPcontrol=120.0,  # in mmHg
                    ABPcrit=12.0,      # in mmHg
                    iputType='STEP',
                    stepSize=-10,      # in mmHg
                    impulseIntensity=-10): # in mmHg
        
        if iputType.upper() == 'STEP':
            P=np.concatenate((ABPcontrol*np.ones(int(fs)),(ABPcontrol+stepSize)*np.ones(int(Tresponse*fs)))).reshape(-1, 1);
        if iputType.upper() == 'IMPULSE':
            P=ABPcontrol+(impulseIntensity*fs)*signal.unit_impulse(int(fs*(Tresponse+1)), int(fs)).reshape(-1, 1);
        
        T=ARsetup.ARIparamDict[ARIindex]['T']
        D=ARsetup.ARIparamDict[ARIindex]['D']
        K=ARsetup.ARIparamDict[ARIindex]['K']
        
        Ad= np.array([[ 1.0       , -1.0/(fs*T)    ],
                      [ 1.0/(fs*T), 1.0-2.0*D/(fs*T) ]])
        Bd= np.array([[1.0/(fs*T)],[0.0]])
        Cd= np.array([0.0,-K])
        Dd= np.array([1])

        sys = signal.StateSpace(Ad, Bd, Cd, Dd, dt=1/fs)

        dP = (P-ABPcontrol)/(ABPcontrol-ABPcrit)
        x0=np.array([2*D*dP[0][0], dP[0][0]])
        t_out,y_out,x_out = signal.dlsim(sys,u=dP,x0=x0)
        
        V =CBFcontrol*(1.0+y_out)

        return [t_out,V]
    
    def plotTiecks(self,t,V):
        fig, ax = plt.subplots(figsize=[8,5])
        ax.plot(t,V, c='k',linewidth=1,color='r')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Velocity (cm/s)')
        ax.grid(True)
        
        fig.tight_layout()
        
        plt.show()
            
if __name__ == '__main__':

    ARI = ARIanalysis()
    #for i in range(10):
    #    [t,V] = ARI.tiecksModel(i,iputType='IMPULSE',stepSize=-10,impulseIntensity=-110)
        #ARI.plotTiecks(t,V)
        #np.savetxt('%d.txt'%i,V)
        
    [t,V] = ARI.tiecksModel(7,iputType='STEP',stepSize=-10,impulseIntensity=-10)
    #[t,V] = ARI.tiecksModel(7,iputType='STEP',stepSize=-10,impulseIntensity=-10))
    ARI.plotTiecks(t,V)
