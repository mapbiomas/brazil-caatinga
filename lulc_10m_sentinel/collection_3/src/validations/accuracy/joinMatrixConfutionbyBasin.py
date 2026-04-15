#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformação
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import glob 
import sys
import time
import math
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score, recall_score
# from sklearn.metrics import 
from sklearn.metrics import f1_score, jaccard_score
tqdm.pandas()

# get dir path of sc, 'RF'ript 
npath = os.getcwd()
# get dir folder before to path scripts 
npath = str(Path(npath).parents[1])
print("path of CSVs Rois is \n ==>",  npath)
pathcsvsMC = os.path.join(npath,'dados','conf_matrix')
print("path of CSVs Matrix is \n ==>",  pathcsvsMC)
version_process = ['5','6','7']
lstfilesCSVs = glob.glob(pathcsvsMC + '/*.csv')
print(f" we load {len(lstfilesCSVs)} tables ")
lst_filters = [
    'Gap-fill','TemporalJ3','TemporalJ4','TemporalJ5', 
    'TemporalAJ3','TemporalAJ4','TemporalAJ5','Spatial', 
    'Frequency', 'TemporalCCJ6'
]
lstDF_models = []
# for nfilter in lst_filters:
#     print(f"=========== {nfilter.split("/")[-1]} ========== ")
#     for vers in version_process:
for cc, pathfile in enumerate(lstfilesCSVs):        
    print(f"#{cc}   >>> {pathfile} ")       
    namefile = pathfile.split("/")[-1]
    partes = namefile.split("_")
    nbacia = partes[0]
    nfilter = partes[1]
    yyear = partes[-2]
    version = partes[-1].replace('.csv', '')
    collection = 'Col10'
    if nfilter == 'integration':
        collection = nfilter
    print(f"file {cc} | m POS- CLASS {nfilter} | year {yyear} | pathfile {pathfile.split("/")[-1]}")
    # sys.exit()
    dftmp = pd.read_csv(pathfile)
    dftmp['bacia'] = [nbacia] * dftmp.shape[0]
    dftmp['Filters'] = [nfilter] * dftmp.shape[0]
    dftmp['Collections'] = [collection] * dftmp.shape[0]
    dftmp['version'] = [version] * dftmp.shape[0]
    dftmp['year'] = [yyear] * dftmp.shape[0]
    # print(dftmp)
    lstDF_models.append(dftmp)
        
print("list tables  ",  len(lstDF_models))  # 1520
time.sleep(1)
# sys.exit()
if len(lstDF_models) >= 1000:        
    nametable = 'Matrices_Confusion_model_All_filters_vers.csv'
    dfModels = pd.concat(lstDF_models, axis=0, ignore_index=True)
    pathExp = npath + '/dados/globalTables/' + nametable
    dfModels.to_csv(pathExp)
    print(f" we save the table {nametable} with {dfModels.shape} shapes")
