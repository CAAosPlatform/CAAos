from __future__ import division, print_function

import ntpath
import os
import posixpath
from pathlib import Path, PureWindowsPath

import numpy as np

import ARsetup


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass


def splitPath(path):
    """
    splits a path between its components
    Ex:  /path/to/file.ext
            dirName: /path/to/   <-- includes last /!!
            filePrefixName: file
            fileExtension: .ext
    Parameters
    ----------
    path: string
        string representing a path
    Returns
    -------
        [dirName, filePrefixName, fileExtension]
    """
    dirName = os.path.dirname(path) + '/'
    filename_w_ext = os.path.basename(path)
    filePrefixName, fileExtension = os.path.splitext(filename_w_ext)

    return [dirName, filePrefixName, fileExtension]


def path2posixPath(absPathString):
    print('ERORR: This function was not tested yet!')
    exit(-1)
    # absPathString must be absolute path.
    if ntpath.isabs(absPathString):  # is windows
        tempPath = PureWindowsPath(pathString)
        tempPath = Path(tempPath)
    if posixpath.isabs(absPathString):  # is linux/mac
        tempPath = PurePosixPath(pathString)
        tempPath = Path(tempPath)

    return str(tempPath)


# case: 'upper', 'lower', None
def setFileExtension(file, extension, case=None):
    baseFile, _ = os.path.splitext(file)

    if case is None:
        extFile = extension
    else:
        if case.lower() == 'upper':
            extFile = extension.upper()
        if case.lower() == 'lower':
            extFile = extension.lower()

    if not extension.startswith('.'):
        extFile = '.' + extFile

    return baseFile + extFile


def lowerFileExtension(file):
    base, ext = os.path.splitext(file)
    return base + ext.lower()


def upperFileExtension(file):
    base, ext = os.path.splitext(file)
    return base + ext.upper()


def detect_peaks(x, mph=None, mpd=1, threshold=0, edge='rising', kpsh=False, MinPeakProminence=0, MinPeakProminenceSide='both', valley=False,
                 show=False, ax=None):
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
            mph = -mph

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
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]

    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size - 1:
        ind = ind[:-1]

    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]

    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx1 = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]), axis=0)
        ind = np.delete(ind, np.where(dx1 < threshold)[0])

    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) & (x[ind[i]] > x[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back the indices by their occurrence
        ind = np.sort(ind[~idel])

    # remove peaks with small Prominence
    if ind.size and MinPeakProminence > 0:
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if MinPeakProminenceSide.lower() in ['left', 'both']:
                # cumulative sum from ind[i] to the left, while dx>0
                cumsum = 0
                for j in reversed(range(ind[i])):
                    if dx[j] > 0:
                        cumsum += dx[j]
                    else:
                        break
                idel[i] = cumsum < MinPeakProminence

            if MinPeakProminenceSide.lower() in ['right', 'both']:
                # cumulative sum from ind[i] to the right, while dx<0
                cumsum = 0
                for j in range(ind[i], len(x) - 1):
                    if dx[j] < 0:
                        cumsum += abs(dx[j])
                    else:
                        break
                idel[i] = cumsum < MinPeakProminence
        # remove indices
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
            ax.plot(ind, x[ind], '+', mfc=None, mec='r', mew=2, ms=8, label='%d %s' % (ind.size, label))
            ax.legend(loc='best', framealpha=.5, numpoints=1)
        ax.set_xlim(-.02 * x.size, x.size * 1.02 - 1)
        ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
        yrange = ymax - ymin if ymax > ymin else 1
        ax.set_ylim(ymin - 0.1 * yrange, ymax + 0.1 * yrange)
        ax.set_xlabel('Data #', fontsize=14)
        ax.set_ylabel('Amplitude', fontsize=14)
        mode = 'Valley detection' if valley else 'Peak detection'
        ax.set_title('%s (mph=%s, mpd=%d, threshold=%s, edge=\'%s\')' % (mode, str(mph), mpd, str(threshold), edge))
        # plt.grid()
        plt.show()


if __name__ == '__main__':

    x = [0, 1, 2, 3, 2, 1, 2, 3, 2, 1, 0, 1, 2, 3, 2, 1, 0]
    print(x)
    y = detect_peaks(x, MinPeakProminence=2.1, MinPeakProminenceSide='right', valley=False, show=True)
    print(y)

from lxml import etree as ETree


# attribList: list of pairs [ [ key, value], ... ]
# if position=none, add to the end, otherwise add at the specified position
def ETaddElement(parent, tag, text=None, attribList=None, position=None):
    elem = ETree.Element(tag)

    if text is not None:
        elem.text = text
    if attribList is not None:
        for e in attribList:
            elem.attrib[e[0]] = e[1]

    if position is not None:
        parent.insert(position, elem)
    else:
        parent.append(elem)
    return elem


def getElemValueXpath(element,  # type: ETree
                      xpath,  # type: str
                      valType='int'  # type: str
                      ):
    """
    given a lxml.element or lxml.elementTree, returns the text of a sub element of the xpath

    WARNING: If there are more than one element at the xpath. this function will return the value of the first occurrence.
    Parameters
    ----------
    element: lxml.etree of lxml.element
        main element
    xpath: str
        xpath of one element. use xpath='.' to consider element itself.

    valType: str {'int', 'float', 'str', 'bool', 'list_int', 'list_float'}
        expected type of the value.

    Returns
    -------
    value:
        the value, already converted of the expected type

    Examples
    --------
    let the xml file be

    <?xml version="1.0" ?>
    <EITmodel>
        <current>
            <pattern>bipolar_skip</pattern>
            <skip>4</skip>
            <value unit="mA">10</value>
        </current>
        <FEMmodel>
            <general>
                <meshFile>./myMesh.msh</meshFile>
                <meshFileUnit>mm</meshFileUnit>
                <dimension>3</dimension>
                <height2D>2.0</height2D>
                <nElectrodes>2</nElectrodes>
            </general>
        </FEMmodel>
    </EITmodel>


    root = ETree.parse('xmlFile.xml'.getroot()  # EITmodel is the root in this example
    pattern = getElemValueXpath(root, xpath='current/pattern', valType='str')
    height = getElemValueXpath(root, xpath='FEMmodel/general/height2D', valType='float')
    """

    elemList = element.xpath(xpath)

    if len(elemList) == 0:
        print('ERROR! Xpath -> %s <- not found!' % xpath)
        exit()

    elemText = elemList[0].text

    return convStr(elemText, valType)


# 'int', 'float', 'str', 'bool', 'list_int', 'list_float'
def getElemAttrXpath(element,  # type: ETree
                     xpath,  # type: str
                     attrName,  # type: str
                     attrType='int'  # type: str
                     ):
    """
    given a lxml.element or lxml.elementTree, returns the text of a sub element of the xpath

    If there are more than one element at the xpath. this function will return the value of the first occurrence.
    Parameters
    ----------
    element: lxml.etree of lxml.element
        main element
    xpath: str
        xpath of one element. use xpath='.' to consider element itself.

    attrName: str
        name of the attribute

    attrType: str {'int', 'float', 'str', 'bool', 'list_int', 'list_float'}
        expected type of the attribute.

    Returns
    -------
    value:
        the value, already converted of the expected type

    Examples
    --------
    let the xml file be

    <?xml version="1.0" ?>
    <EITmodel>
        <current>
            <pattern>bipolar_skip</pattern>
            <skip>4</skip>
            <value unit="mA">10</value>
        </current>
    </EITmodel>


    root = ETree.parse('xmlFile.xml'.getroot()  # EITmodel is the root in this example
    currUnit = tools.getElemAttrXpath(root, xpath='current/value', attrName='unit', attrType='str')
    """
    elemList = element.xpath(xpath)

    if len(elemList) == 0:
        print('ERROR! Xpath -> %s <- not found!' % xpath)
        exit()

    elemAttr = elemList[0].attrib[attrName]

    return convStr(elemAttr, attrType)


def convStr(string,  # type: str
            outputType='int'  # type: str
            ):
    """
    given a string, converts it the specified type

    In case of list, it is expected that the string has the following format:
    '[1.0 2.0 3.0 4.0 ]' --> convert to a list of floats
    '[1 2 3 4 ]' --> convert to a list of integers

    Parameters
    ----------
    string: str
        string to be converted

    outputType: str {'int', 'float', 'str', 'bool', 'list_int', 'list_float'}
        expected type of the attribute.


    Returns
    -------
    value:
        the value, already converted of the expected type


    -------

    """

    if outputType not in ['int', 'float', 'str', 'bool', 'list_int', 'list_float']:
        print('Error: outputType -> %s <- not recognized. Valid options: int, float, str, bool, list_int, list_float' % outputType)
        exit(-1)

    if string == 'None':
        return None

    if outputType == 'int':
        return int(string)

    if outputType == 'float':
        return float(string)

    if outputType == 'str':
        return string

    if outputType == 'bool':
        if string.lower() == 'true':
            return True
        else:
            return False

    if outputType == 'list_int':
        listProcessed = string.strip('][').split()
        if listProcessed == '':
            return []
        else:
            return [int(x) for x in listProcessed]

    if outputType == 'list_float':
        listProcessed = string.strip('][').split()
        if listProcessed == '':
            return []
        else:
            return [float(x) for x in listProcessed]


class CARfreqRange():
    def __init__(self, freqSignal):

        self.freq = freqSignal

    # return the indices of freq within the specified range
    # this is an internal function. you probably does not need to call it explicitly
    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def _getRangeIndex(self, freqRange='ALL'):
        if freqRange.upper() in ['VLF', 'LF', 'HF']:
            fStart, fEnd = ARsetup.freqRangeDic[freqRange.upper()]
        elif freqRange.upper() == 'ALL':
            fStart = ARsetup.freqRangeDic['VLF'][0]
            fEnd = ARsetup.freqRangeDic['HF'][1]
        else:  # 'FULL'
            fStart = 0
            fEnd = self.freq[-1]
        return np.where((self.freq >= fStart) & (self.freq <= fEnd))

    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getFreq(self, freqRange='ALL'):
        indices = self._getRangeIndex(freqRange)
        return self.freq[indices]

    # freqRange (string)  'VLF', 'LF', 'HF', 'ALL' (default), 'FULL'
    def getSignal(self, signal, freqRange='ALL'):
        indices = self._getRangeIndex(freqRange)
        return signal[indices]

    def getStatistics(self, signal, freqRange='ALL'):
        max = self.getMax(signal, freqRange)
        min = self.getMin(signal, freqRange)
        avg = self.getAvg(signal, freqRange)
        std = self.getStd(signal, freqRange)

        return [avg, std, min, max]

    def getMax(self, signal, freqRange='ALL'):
        return np.nanmax(self.getSignal(signal, freqRange))

    def getMin(self, signal, freqRange='ALL'):
        return np.nanmin(self.getSignal(signal, freqRange))
        return minS

    def getAvg(self, signal, freqRange='ALL'):
        return np.nanmean(self.getSignal(signal, freqRange))
        return meanS

    def getStd(self, signal, freqRange='ALL'):
        return np.nanstd(self.getSignal(signal, freqRange), ddof=0)
        return stdS
