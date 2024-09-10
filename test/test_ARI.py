import sys
import numpy as np
import pytest

sys.path.append('../src/')
from ARI import ARIanalysis

'''Input files and expected fractional ARI'''
@pytest.mark.parametrize("inputFile_CSV,ARI_frac_out", [('./testData/ARI/DPOC01CA_FR1.csv', 4.776343), ('./testData/ARI/DPOC01CA_FR2.csv', 7.729330),
                                           ('./testData/ARI/DPOC03CA_FR1.csv', 6.403879), ('./testData/ARI/DPOC03CA_FR2.csv', 3.329951),
                                           ('./testData/ARI/DPOC04CA_FR1.csv', 5.858150), ('./testData/ARI/DPOC04CA_FR2.csv', 6.417877),
                                           ('./testData/ARI/DPOC05CA_FR1.csv', 2.666017), ('./testData/ARI/DPOC05CA_FR2.csv', 2.881955),
                                           ('./testData/ARI/DPOC06CA1_FR1.csv', 4.374967), ('./testData/ARI/DPOC06CA1_FR2.csv', 4.201312),
                                           ('./testData/ARI/DPOC2CA1_FR1.csv', 6.845117), ('./testData/ARI/DPOC2CA1_FR2.csv', 6.917811),
                                           ('./testData/ARI/P06BA1A2_FR1.csv', 3.901542), ('./testData/ARI/P06BA1A2_FR2.csv', 0.000000),
                                           ('./testData/ARI/P07BA1A1_FR1.csv', None), ('./testData/ARI/P07BA1A1_FR2.csv', None),
                                           ('./testData/ARI/P08BA1A1_FR1.csv', 0.961324), ('./testData/ARI/P08BA1A1_FR2.csv', 2.332953),
                                           ('./testData/ARI/P11BA1A1_FR1.csv', 1.720086), ('./testData/ARI/P11BA1A1_FR2.csv', 2.905094),
                                           ('./testData/ARI/P13BA1A1_FR1.csv', 5.204078), ('./testData/ARI/P13BA1A1_FR2.csv', 4.216722),
                                           ('./testData/ARI/P15BA2A1_FR1.csv', 0.000000), ('./testData/ARI/P15BA2A1_FR2.csv', 6.403091),
                                           ('./testData/ARI/P16BA1A1_FR1.csv', None), ('./testData/ARI/P16BA1A1_FR2.csv', None),
                                           ('./testData/ARI/P17BA1A1_FR1.csv', 7.332288), ('./testData/ARI/P17BA1A1_FR2.csv', 6.898586),
                                           ('./testData/ARI/P19BA1A1_FR1.csv', 2.139086), ('./testData/ARI/P19BA1A1_FR2.csv', 3.160573),
                                           ('./testData/ARI/P20BA1A1_FR1.csv', 2.935072), ('./testData/ARI/P20BA1A1_FR2.csv', 5.408069),
                                           ('./testData/ARI/P20BA1A1_FR2J.csv', 5.427335), ('./testData/ARI/P21BA1A1_FR1.csv', 4.027588),
                                           ('./testData/ARI/P21BA1A1_FR1J.csv', 4.021869), ('./testData/ARI/P21BA1A1_FR2.csv', 5.347768),
                                           ('./testData/ARI/P22BA1A1_FR1.csv', 7.998027), ('./testData/ARI/P22BA1A1_FR2.csv', 4.965860),
                                           ('./testData/ARI/VOL01CA1_FR1.csv', 6.476519), ('./testData/ARI/VOL01CA1_FR2.csv', 7.449243),
                                           ('./testData/ARI/VOL02CA1_FR1.csv', 7.959246), ('./testData/ARI/VOL02CA1_FR2.csv', 8.076318),
                                           ('./testData/ARI/VOL03CA1_FR1.csv', 3.911459), ('./testData/ARI/VOL03CA1_FR2.csv', 3.108706),
                                           ('./testData/ARI/VOL04CA1_FR1.csv', 0.000000), ('./testData/ARI/VOL04CA1_FR2.csv', 0.000000),
                                           ('./testData/ARI/VOL05CA1_FR1.csv', 6.886732), ('./testData/ARI/VOL05CA1_FR2.csv', 6.948741),
                                           ('./testData/ARI/VOL06CA1_FR1.csv', 5.018032), ('./testData/ARI/VOL06CA1_FR2.csv', 6.307586), ])

def test_caseA(inputFile_CSV,ARI_frac_out):
    datax = np.loadtxt(inputFile_CSV, skiprows=1, delimiter=',')
    samplingFreq_Hz = 5

    gain = np.array(datax[:, 5])
    phase = np.array(datax[:, 8])

    # Duplicates input. Panerai's code stores only the first half of the spectrum. Since Nyquist is lost. I am copying the pevious value as Nyquist
    gain = np.concatenate([gain, np.array([gain[-1]]), np.flip(gain[1:])])
    phase = np.concatenate([phase, np.array([phase[-1]]), -np.flip(phase[1:])])

    # build transfer function from amplitude and phase
    TF = gain * np.exp(1j * phase)

    # run ARI
    myARI = ARIanalysis(TF, 1.0 / samplingFreq_Hz)

    assert myARI.ARI_frac == pytest.approx(ARI_frac_out,rel=1e-6)

