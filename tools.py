from __future__ import division, print_function
import numpy as np
import ARsetup

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

def detect_peaks(x, mph=None, mpd=1, threshold=0, edge='rising',
                 kpsh=False, MinPeakProminence=0, MinPeakProminenceSide='both',valley=False, show=False, ax=None):

    """Detect peaks in data based on their amplitude and other features.

    Parameters
    ----------
    x : 1D array_like
        data.
    mph : {None, number}, optional (default = None)
        detect peaks that are greater than minimum peak height.
    mpd : positive integer, optional (default = 1)
        detect peaks that are at least separated by minimum peak distance (in
        number of data).
    threshold : positive number, optional (default = 0)
        detect peaks (valleys) that are greater (smaller) than `threshold`
        in relation to their immediate neighbors.
    edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
        for a flat peak, keep only the rising edge ('rising'), only the
        falling edge ('falling'), both edges ('both'), or don't detect a
        flat peak (None).
    kpsh : bool, optional (default = False)
        keep peaks with same height even if they are closer than `mpd`.
    valley : bool, optional (default = False)
        if True (1), detect valleys (local minima) instead of peaks.

    Returns
    -------
    ind : 1D array_like
        indeces of the peaks in `x`.

    Notes
    -----
    The detection of valleys instead of peaks is performed internally by simply
    negating the data: `ind_valleys = detect_peaks(-x)`
    
    The function can handle NaN's 

    See this IPython Notebook [1]_.
    
    __author__ = "Marcos Duarte, https://github.com/demotu/BMC"
    __version__ = "1.0.5"
    __license__ = "MIT"

    References
    ----------
    .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb

    Examples
    --------
    >>> from detect_peaks import detect_peaks
    >>> x = np.random.randn(100)
    >>> x[60:81] = np.nan
    >>> # detect all peaks and plot data
    >>> ind = detect_peaks(x, show=True)
    >>> print(ind)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # set minimum peak height = 0 and minimum peak distance = 20
    >>> detect_peaks(x, mph=0, mpd=20, show=True)

    >>> x = [0, 1, 0, 2, 0, 3, 0, 2, 0, 1, 0]
    >>> # set minimum peak distance = 2
    >>> detect_peaks(x, mpd=2, show=True)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # detection of valleys instead of peaks
    >>> detect_peaks(x, mph=0, mpd=20, valley=True, show=True)

    >>> x = [0, 1, 1, 0, 1, 1, 0]
    >>> # detect both edges
    >>> detect_peaks(x, edge='both', show=True)

    >>> x = [-2, 1, -2, 2, 1, 1, 3, 0]
    >>> # set threshold = 2
    >>> detect_peaks(x, threshold = 2, show=True)
    """

    x = np.atleast_1d(x).astype('float64')
    if x.size < 3:
        return np.array([], dtype=int)
    if valley:
        x = -x
        if mph is not None:
            mph=-mph
            
    # find indices of all peaks
    dx = x[1:] - x[:-1]
    # handle NaN's
    indnan = np.where(np.isnan(x))[0]
    if indnan.size:
        x[indnan] = np.inf
        dx[np.where(np.isnan(dx))[0]] = np.inf
    ine, ire, ife = np.array([[], [], []], dtype=int)
    if not edge:
        ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
    else:
        if edge.lower() in ['rising', 'both']:
            ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))

    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan-1, indnan+1))), invert=True)]
        
    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size-1:
        ind = ind[:-1]

    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]

    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx1 = np.min(np.vstack([x[ind]-x[ind-1], x[ind]-x[ind+1]]), axis=0)
        ind = np.delete(ind, np.where(dx1 < threshold)[0])
        
    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                    & (x[ind[i]] > x[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back the indices by their occurrence
        ind = np.sort(ind[~idel])
        
    # remove peaks with small Prominence
    if ind.size and MinPeakProminence>0:
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if MinPeakProminenceSide.lower() in ['left','both']:
                #cumulative sum from ind[i] to the left, while dx>0
                cumsum=0                
                for j in reversed(range(ind[i])):
                    if dx[j]>0:
                        cumsum+=dx[j]
                    else:
                        break
                idel[i]=cumsum<MinPeakProminence

            if MinPeakProminenceSide.lower() in ['right','both']:
                #cumulative sum from ind[i] to the right, while dx<0
                cumsum=0
                for j in range(ind[i],len(x)-1):
                    if dx[j]<0:
                        cumsum+=abs(dx[j])
                    else:
                        break
                idel[i]=cumsum<MinPeakProminence
        #remove indices
        ind = ind[~idel]


    if show:
        if indnan.size:
            x[indnan] = np.nan
        if valley:
            x = -x
            if mph is not None:
                mph = -mph
        _plot(x, mph, mpd, threshold, edge, valley, ax, ind)
        
    return ind

def _plot(x, mph, mpd, threshold, edge, valley, ax, ind):
    """Plot results of the detect_peaks function, see its help."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib is not available.')
    else:
        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(8, 4))

        ax.plot(x, '-bo', lw=1)
        if ind.size:
            label = 'valley' if valley else 'peak'
            label = label + 's' if ind.size > 1 else label
            ax.plot(ind, x[ind], '+', mfc=None, mec='r', mew=2, ms=8,
                    label='%d %s' % (ind.size, label))
            ax.legend(loc='best', framealpha=.5, numpoints=1)
        ax.set_xlim(-.02*x.size, x.size*1.02-1)
        ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
        yrange = ymax - ymin if ymax > ymin else 1
        ax.set_ylim(ymin - 0.1*yrange, ymax + 0.1*yrange)
        ax.set_xlabel('Data #', fontsize=14)
        ax.set_ylabel('Amplitude', fontsize=14)
        mode = 'Valley detection' if valley else 'Peak detection'
        ax.set_title("%s (mph=%s, mpd=%d, threshold=%s, edge='%s')"
                     % (mode, str(mph), mpd, str(threshold), edge))
        # plt.grid()
        plt.show()
        
if __name__ == '__main__':
        
    x= [0,1,2,3,2,1,2,3,2,1,0,1,2,3,2,1,0]
    print(x)
    y = detect_peaks(x, MinPeakProminence=2.1,MinPeakProminenceSide='right', valley=False,show=True)
    print(y)


import xml.etree.ElementTree as ET

class TEsimple(ET.Element):
    def __init__(self, tag, text=None, tail=None, parent=None, attrib={}, **extra):
        super(TEsimple, self).__init__(tag, attrib, **extra)

        if text:
            self.text = text
        if tail:
            self.tail = tail
        if not parent == None:
            parent.append(self)

# 'int', 'float', 'str', 'bool', 'list_int', 'list_float'
def convAtrib(operationNode,tagName,type='int'):
    
    atribText=operationNode.find(tagName).text

    if atribText == 'None':
        return None
    
    if type=='int':
        return int(atribText)
    
    if type=='float':
        return float(atribText)
    
    if type=='str':
        return atribText
    
    if type=='list_int':
        listProcessed=atribText.strip('][').split()
        if listProcessed=='':
            return []
        else:
            return [int(x) for x in listProcessed]
    
    if type=='list_float':
        listProcessed=atribText.strip('][').split()
        if listProcessed=='':
            return []
        else:
            return [float(x) for x in listProcessed]

    if type=='bool':
        if atribText == 'True':
            return True
        else:
            return False

        
class CARfreqRange():
    def __init__(self,freqSignal):

        self.freq=freqSignal

    # return the indices of freq within the specified range
    # this is an internal function. you probably does not need to call it explicitly
    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL' 
    def _getRangeIndex(self,freqRange='ALL'):
        if freqRange.upper() in ['VLF', 'LF', 'HF']:
            fStart,fEnd=ARsetup.freqRangeDic[freqRange.upper()]
        elif freqRange.upper() =='ALL':
            fStart=ARsetup.freqRangeDic['VLF'][0]
            fEnd=ARsetup.freqRangeDic['HF'][1]
        else:    # 'FULL'
            fStart=0
            fEnd=self.freq[-1]
        return np.where( (self.freq>=fStart) & (self.freq<=fEnd) )
    
    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getFreq(self,freqRange='ALL'):
        indices = self._getRangeIndex(freqRange)
        return self.freq[indices]
    
    #freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getSignal(self,signal,freqRange='ALL'):
        indices = self._getRangeIndex(freqRange)
        return signal[indices]

    def getStatistics(self,signal,freqRange='ALL'):
        max=self.getMax(signal,freqRange)
        min=self.getMin(signal,freqRange)
        avg=self.getAvg(signal,freqRange)
        std=self.getStd(signal,freqRange)
        
        return [avg,std,min,max]

    def getMax(self,signal,freqRange='ALL'):
        return np.nanmax(self.getSignal(signal,freqRange))

    def getMin(self,signal,freqRange='ALL'):
        return np.nanmin(self.getSignal(signal,freqRange))
        return minS

    def getAvg(self,signal,freqRange='ALL'):
        return np.nanmean(self.getSignal(signal,freqRange))
        return meanS

    def getStd(self,signal,freqRange='ALL'):
        return np.nanstd(self.getSignal(signal,freqRange), ddof=0)
        return stdS























        
        
    
