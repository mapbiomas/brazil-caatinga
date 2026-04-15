#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''
import os
import sys
import math
import glob
import json
import pandas as pd
import numpy as np
from random import randint
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn.metrics import RocCurveDisplay, auc
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelBinarizer


def changeClass(XX, class_act):
    newXX = 0
    if int(XX) == int(class_act):
        newXX = 1
    return newXX


# def tranformar_dataframe(dftmp, lista_class):
#     for classe in lista_class:
#         transform_DFclass =  transform_DataFrame(classe)
#         dftmp = dftmp.apply(transform_DFclass.changeClass, axis= 1)
#     return dftmp


def getPathCSV (nfolder):
    # get dir path of script 
    pathroot = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(pathroot).parents[0])
    # folder of CSVs ROIs
    roisPath = '/dados/' + nfolder
    mpath = pathparent + roisPath
    print("path of CSVs Rois is \n ==>",  mpath)
    return pathparent, mpath


nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]

mpathRoot, pathJson = getPathCSV("regJSON/")
a_file = open(pathJson + "rest_lst_features_selected_bndC8.json", "r")
dictFeatureImp = json.load(a_file)
lstKeysDict = [kk for kk in dictFeatureImp.keys()]
sizeListFS = len(lstKeysDict)
print(f"We have {sizeListFS} keys [Basjn_Year] in dict Features selected  ")
nSelectKey = randint(0, sizeListFS)
keySelected = lstKeysDict[nSelectKey]
print(f"we show the list FS {nSelectKey} <> {keySelected}")
print(f"lst Features ", dictFeatureImp[keySelected])

nbacia = keySelected.split("_")[0]
yyear = keySelected.split("_")[1]
pathROIsCL = mpathRoot + '/dados/Col9_ROIs_cluster'
dirfileROIs = pathROIsCL + "/" + keySelected + "_c1.csv"
dfData = pd.read_csv(dirfileROIs)
dfData = dfData.drop(['system:index', '.geo'], axis=1) 
print(f" ✅ load {dfData.shape} datas from ROIs table")
print(dfData.head(2))
lstClasses = [kk for kk in dfData['class'].unique()]
print(" lista de classes ", lstClasses)

for nclass in lstClasses:
    dfData['class_' + str(nclass)] = dfData['class'].apply(lambda x: changeClass(x, nclass))
    print(" change ", dfData['class_' + str(nclass)].unique())

colunas = [kk for kk in dfData.columns]
print("columns ", colunas)

colunas.remove('year')
colunas.remove('class')
try:
    colunas.remove('newclass')
    colunas.remove('random')
except:
    print("")

# dfData = tranformar_dataframe(dfData, lstClasses)
print(f" ✅ new shape of DF Data {dfData.shape}")
# sys.exit()

# loading the best parameter on gradient tree boost classifier
b_file = open(pathJson +  "regBacia_Year_hiperPmtrosTuningfromROIs2Y.json", 'r')
dictHiperPmtTuning = json.load(b_file)
if int(yyear) > 2018:
    dictParam = dictHiperPmtTuning[nbacia]['2021']
else:
    dictParam = dictHiperPmtTuning[nbacia]['2016']
print(f" ✅ parameter from basin {nbacia} ==> {dictParam} ")


n_splits = 5
cv = StratifiedKFold(n_splits= n_splits, random_state=None, shuffle=False)
# classifier = RandomForestClassifier()
classifier = GradientBoostingClassifier(
            n_estimators=dictParam[1], 
            learning_rate= dictParam[0],
            max_depth=12, 
            random_state=0
        )
numcol = math.ceil(len(lstClasses)/2)
tprs = []
aucs = []
mean_fpr = np.linspace(0, 1, 100)
fig, ax = plt.subplots(numcol, 2,figsize=(16, 12))
for cc, nclass in enumerate(lstClasses):    
    nrow = int(cc / numcol )
    ncol = cc % numcol
    for fold, (train, test) in enumerate(cv.split(dfData[colunas], dfData['class_' + str(nclass)])):
        # print(f"size train index {len(train)}")
        # print(f"size test index {len(test)}")
        # # make binarize class for de list class 
        # label_binarizer = LabelBinarizer().fit(dfData['class'].iloc[train])
        # y_onehot_test = label_binarizer.transform(dfData['class'].iloc[test])
        # print("shape from y_onehot_test", y_onehot_test.shape)  # (n_samples, n_classes)
        # print("shape from label_binarizer ", label_binarizer.shape)
        # sys.exit()
        classifier.fit(dfData[colunas].iloc[train], dfData['class_'  + str(nclass)].iloc[train])
        viz = RocCurveDisplay.from_estimator(
            classifier,
            dfData[colunas].iloc[test],
            dfData['class_' + str(nclass)].iloc[test],
            name=f"ROC fold {fold}",
            alpha=0.3,
            lw=1,
            ax=ax[ncol, nrow],
            plot_chance_level=(fold == n_splits - 1),
        )
        interp_tpr = np.interp(mean_fpr, viz.fpr, viz.tpr)
        interp_tpr[0] = 0.0
        tprs.append(interp_tpr)
        aucs.append(viz.roc_auc)

    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    std_auc = np.std(aucs)
    ax[ncol, nrow].plot(
        mean_fpr,
        mean_tpr,
        color="b",
        label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
        lw=2,
        alpha=0.8,
    )

    std_tpr = np.std(tprs, axis=0)
    tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    ax[ncol, nrow].fill_between(
        mean_fpr,
        tprs_lower,
        tprs_upper,
        color="grey",
        alpha=0.2,
        label=r"$\pm$ 1 std. dev.",
    )

    ax[ncol, nrow].set(
        xlabel="False Positive Rate",
        ylabel="True Positive Rate",
        title=f"Mean ROC curve with variability\n(Positive label '{'class_' + str(nclass)}')",
    )
    ax[ncol, nrow].legend(fontsize=8, loc="lower right")
plt.show()


