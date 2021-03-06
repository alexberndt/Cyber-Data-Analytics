"""
apply the ARMA prediction to the dataset

1) FFT analysis to remove signal noise
2) Discretization of filtered signals

# tutorial from https://bicorner.com/2015/11/16/time-series-analysis-using-ipython/#comments
# download data csv from http://www.sidc.be/silso/INFO/snytotcsv.php
"""
### IMPORT PACKAGES ###
import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pandas.tools.plotting import autocorrelation_plot
from statsmodels.graphics.api import qqplot
import scipy.fftpack as fftpk
import scipy.signal as sgnl
from matplotlib import pyplot as plt
from filter_data import filter, filter_F_PUxx, filter_S_PUxx, filter_P_Jxxx
# from discretize_data import discretizeBinary, discretizeSAX

from ARMA import fitARMA
from general_functions import standardize_dataset, standardize_dataset_train_2, standardize_dataset_test

# For trainingset2
L_Tselect = ["L_T1", "L_T2", "L_T3", "L_T4", "L_T5", "L_T7"]
F_PUselect = ["F_PU1", "F_PU2", "F_PU6", "F_PU7", "F_PU8", "F_PU10", "F_PU11"]
S_PUselect = ["S_PU2", "S_PU6", "S_PU7", "S_PU8", "S_PU10", "S_PU11"]
V_Pselect = ["F_V2", "S_V2"]
P_Jselect = ['P_J280', 'P_J269', 'P_J300', 'P_J256', 'P_J289', 'P_J415', 'P_J302', 'P_J306', 'P_J307', 'P_J317', 'P_J14', 'P_J422']

# list of uninteresting fields we are not interested in for analysis
listToDelete = ["L_T6", "S_PU1","S_PU3","S_PU4","S_PU5","S_PU9","F_PU3","F_PU4","F_PU5","F_PU9"]

def getBinaryDF(inputDF):

    binaryDF = inputDF.copy(deep=True)

    print 'Applying ARMA models and thresholds'
    #print inputDF.describe()

    # Remove signals that do not contain exciting information
    for deletefield in listToDelete:
        del binaryDF[deletefield]

    # Apply binary selection to Tank Levels
    print ' - L_Txx : tank level'
    for fieldname in L_Tselect:
        binaryDF[fieldname] = fitARMA(inputDF,fieldname,p=2,q=2,threshold=0.8) # 2

    # Apply binary selection to Pump Flow Rate
    print ' - F_PUxx : pump flow rate'
    for fieldname in F_PUselect:
        binaryDF[fieldname] = fitARMA(inputDF,fieldname,p=2,q=2,threshold=0.8)

    # Apply binary selection to Pump Switch Signals
    print ' - S_PUxx : pump switch'
    for fieldname in S_PUselect:
        binaryDF[fieldname] = fitARMA(inputDF,fieldname,p=2,q=2,threshold=0.8)

    # Apply binary selection to Valve
    print ' - V_Pxx : valve'
    for fieldname in V_Pselect:
        binaryDF[fieldname] = fitARMA(inputDF,fieldname,p=2,q=2,threshold=0.8)

    # Apply binary selection to PLC Signals
    print ' - P_Jxxx : PLC signal'
    for fieldname in P_Jselect:
        binaryDF[fieldname] = fitARMA(inputDF,fieldname,p=2,q=2,threshold=0.8)


    # print '\n binary'
    # print binaryDF.describe()

    print ' - Created database of thresholds for each signal...'
    print ' - Done'

    return binaryDF


def obtainFinalPrediction(binaryDF):

    # Create an empty dataframe which will store the predictions
    dfActualAttack = binaryDF["ATT_FLAG"].copy(deep=True)
    dfPrediction = binaryDF["ATT_FLAG"].copy(deep=True)

    # set all values to zero for dfPrediction
    dfPrediction = (dfPrediction > 2).astype(int)

    print 'applying scenario-based detection...'

    # Check for scenario 1 (attack 2) (anomaly in L_T1, P_J269)(binaryDF["L_T1"] == 1) &
    print ' - scenario 1'
    dfPrediction.loc[((binaryDF["L_T1"] == 1) & (binaryDF["P_J269"] == 1) & (binaryDF["F_V2"] == 1) & (binaryDF["F_PU8"] == 1) & (binaryDF["P_J306"] == 1))] = 1#0.1
    print ' - scenario 2'
    dfPrediction.loc[binaryDF["L_T1"] == 1] = 1#0.7

    # Check for scenario 2
    print ' - scenario 3'
    dfPrediction.loc[binaryDF["S_PU11"] == 1] = 1#0.2

    # Check for attack 3
    #dfPrediction.loc[((binaryDF["F_V2"] == 1) & (binaryDF["F_PU8"] == 1) & (binaryDF["F_PU10"] == 1) & (binaryDF["P_J306"] == 1))] = 0.3

    # Check for attack 4
    print ' - scenario 4'
    dfPrediction.loc[((binaryDF["S_PU6"] == 1) & (binaryDF["F_PU6"] == 1) & (binaryDF["S_PU7"] == 1) & (binaryDF["F_PU7"] == 1))] = 1#0.4

    # Check for scenario 5 (attack 1) (binaryDF["S_PU11"] == 1) &
    #dfPrediction.loc[(binaryDF["L_T7"] == 1)] = 0.5

    # Check for attack 5
    print ' - scenario 5'
    dfPrediction.loc[((binaryDF["S_PU6"] == 1) & (binaryDF["F_PU6"] == 1) & (binaryDF["F_PU7"] == 1))] = 1#0.6

    print ' - done'

    # Print Performance to console
    # tp = 0
	# fp = 0
	# tn = 0
	# fn = 0
	# for i in range(test_normalized.shape[0]):
	#     if(labels[i] == 1 and na[i] == 1):
	#         tp = tp + 1
	#     if(labels[i] == 0 and na[i] == 1):
	#         fp = fp + 1
	#     if(labels[i] == 0 and na[i] == 0):
	#         fn = fn + 1
	#     if(labels[i] == 1 and na[i] == 0):
	#         tn = tn + 1
	# print "TP: {} ".format(tp)
	# print "FP: {} ".format(fp)
	# print "FN: {} ".format(fn)
	# print "TN: {} ".format(tn)

    # DETERMINE PERFORMANCE METRICS
    shouldPlot = False
    print '\nPERFORMANCE METRICS\n'

    # True Positive Rate aka Recall
    PositiveTotal = dfActualAttack[dfActualAttack == 1].sum()
    totalpoints = dfActualAttack.sum()
    print 'Total datapoints: ' + str(totalpoints)
    print 'Total positive values: ' + str(PositiveTotal)

    # print dfPrediction.shape
    # print binaryDF.shape

    TPtotal = dfPrediction[((dfActualAttack == 1) & (dfPrediction == 1))].sum()
    print 'Total predicted positives: ' + str(TPtotal)
    TPR = float(TPtotal)/float(PositiveTotal)
    print 'TPR: ' + str(TPR)
    Recall = TPR
    print 'Recall: ' + str(Recall)

    # Precision
    FPtotal = dfPrediction[((dfActualAttack == 0) & (dfPrediction == 1))].sum()
    Precision = float(TPtotal)/float(TPtotal + FPtotal)
    print 'Precision: ' + str(Precision)

    # plot the prediction vs actual values
    if shouldPlot:
        fig = plt.figure(figsize=(8,4))
        ax1 = fig.add_subplot(111)

        ax1 = dfPrediction.plot(ax=ax1,label='prediction')
        ax1 = binaryDF["ATT_FLAG"].plot(ax=ax1,label='actual')
        ax1 = plt.title('Actual vs Predicted Attack using ARMA')
        plt.ylabel('Attack Bool')
        plt.legend()
        plt.grid()
        plt.show()

    return dfPrediction
