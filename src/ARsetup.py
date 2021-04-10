import numpy as np


freqRangeDic={'VLF':(0.02,0.07), 'LF':(0.07,0.20), 'HF':(0.20,0.50)}
freqRangeColors={'VLF':'#d5e5ff', 'LF':'#d7f4d7', 'HF':'#ffe6d5'}

#source White paper, Table I
#alpha=0.01
cohCriticalValues_alpha_1percent = {3: 0.43,  4: 0.33,  5: 0.27,  6: 0.23,
                                    7: 0.20,  8: 0.18,  9: 0.16, 10: 0.14,
                                   11: 0.13, 12: 0.12, 13: 0.11, 14: 0.10, 15: 0.10}

#alpha=0.05
cohCriticalValues_alpha_5percent = {3: 0.51,  4: 0.40,  5: 0.34,  6: 0.29,
                                    7: 0.25,  8: 0.22,  9: 0.20, 10: 0.18,
                                   11: 0.17, 12: 0.15, 13: 0.14, 14: 0.13, 15: 0.12}

#alpha=0.10
cohCriticalValues_alpha_10percent = {3: 0.65,  4: 0.54,  5: 0.46,  6: 0.40,
                                     7: 0.35,  8: 0.32,  9: 0.29, 10: 0.26,
                                    11: 0.24, 12: 0.22, 13: 0.21, 14: 0.19, 15: 0.18}

# coh critical values as a function of the significance level Alpha=0.01,0.05 and 0.1
cohThresholdDict = {'1%': cohCriticalValues_alpha_1percent, '5%': cohCriticalValues_alpha_5percent, '10%': cohCriticalValues_alpha_10percent}

ARIparamDict = {0: {'T': 2.00, 'D': 0.00, 'K': 0.00},
                1: {'T': 2.00, 'D': 1.60, 'K': 0.20},
                2: {'T': 2.00, 'D': 1.50, 'K': 0.40},
                3: {'T': 2.00, 'D': 1.15, 'K': 0.60},
                4: {'T': 2.00, 'D': 0.90, 'K': 0.80},
                5: {'T': 1.90, 'D': 0.75, 'K': 0.90},
                6: {'T': 1.60, 'D': 0.65, 'K': 0.94},
                7: {'T': 1.20, 'D': 0.55, 'K': 0.96},
                8: {'T': 0.87, 'D': 0.52, 'K': 0.97},
                9: {'T': 0.65, 'D': 0.50, 'K': 0.98}}
