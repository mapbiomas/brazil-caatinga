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
from tabulate import tabulate
from tqdm import tqdm
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score, recall_score
# from sklearn.metrics import 
from sklearn.metrics import f1_score, jaccard_score
tqdm.pandas()

def translate_class(row):
    dictRemap =  {
        "FORMAÇÃO FLORESTAL": 3,
        "FORMAÇÃO SAVÂNICA": 4,        
        "MANGUE": 3,
        "RESTINGA HERBÁCEA": 3,
        "FLORESTA PLANTADA": 21,
        "FLORESTA INUNDÁVEL": 3,
        "CAMPO ALAGADO E ÁREA PANTANOSA": 12,
        "APICUM": 12,
        "FORMAÇÃO CAMPESTRE": 12,
        "AFLORAMENTO ROCHOSO": 22,
        "OUTRA FORMAÇÃO NÃO FLORESTAL":12,
        "PASTAGEM": 21,
        "CANA": 21,
        "LAVOURA TEMPORÁRIA": 21,
        "LAVOURA PERENE": 21,
        "MINERAÇÃO": 22,
        "PRAIA E DUNA": 22,
        "INFRAESTRUTURA URBANA": 22,
        "VEGETAÇÃO URBANA": 22,
        "OUTRA ÁREA NÃO VEGETADA": 22,
        "RIO, LAGO E OCEANO": 33,
        "AQUICULTURA": 33,
        "NÃO OBSERVADO": 27  
    }
    dictRempCCL2 = {
        "0": 27,
        "3": 3,
        "4": 4,
        "12": 12,
        "15": 21,
        "18": 21,
        "21": 21,
        "22": 22,
        "25": 22,
        "29": 22,
        "33": 33
    }
    row['reference'] = dictRemap[row['reference']]
    row['classification'] = dictRempCCL2[str(row['classification'])]
    return row

def concert_table_Acc(df_tmp, ultima_year):
    lstDFAc =[]
    for nyear in range(1985, ultima_year + 1):
        col_ref = f'CLASS_{nyear}'
        col_class = f"classification_{nyear}"
        dft = df_tmp[[col_ref, col_class, 'bacia']]
        dft.columns = ['reference', 'classification', 'bacia']
        
        primerVal = dft['reference'].tolist()[0]
        # print("primeiro valor ", primerVal)
        try:
            print(int(primerVal))            
        except:
            dft = dft.apply(translate_class, axis= 1)
        
        dft = dft.copy()
        dft['years'] = [nyear] * dft.shape[0]        
        lstDFAc.append(dft)

    dfG = pd.concat(lstDFAc, ignore_index= True)
    return dfG


# get dir path of sc, 'RF'ript 
npath = os.getcwd()
# get dir folder before to path scripts 
npath = str(Path(npath).parents[1])
print("path of CSVs Rois is \n ==>",  npath)
pathcsvsMC = os.path.join(npath,'dados','acc','ptosAccColBef')
print("path of CSVs Matrix is \n ==>",  pathcsvsMC)

lstfilesCSVs = glob.glob(pathcsvsMC + '/*.csv')
print(f" we load {len(lstfilesCSVs)} tables ")

lstDF_models = []

for cc, pathfile in enumerate(lstfilesCSVs):   
    print(f"=========== {pathfile.split("/")[-1]} ========== ")     
    # if nfilter in pathfile: #and "_" + vers + '.csv' in pathfile:         
        # print(pathfile)       
    namefile = pathfile.split("/")[-1]
    partes = namefile.split("_")
    print("partes >> ", partes)
    nfilter = ''
    collection = partes[4]
    version = 1
    #  
    print(f"file {cc} | m POS- CLASS| {collection}  version {version} | pathfile {pathfile.split("/")[-1]}")
    # sys.exit()
    dftmp = pd.read_csv(pathfile)
    print(dftmp.columns)
    last_year = 2022
    if collection == 'collection71':
        last_year = 2021
    colShow = ['CLASS_1985', 'classification_1985',  f'classification_{last_year}', 'bacia'] 
    print(tabulate(dftmp[colShow].head(2), headers = 'keys', tablefmt = 'psql'))
    dfMod = concert_table_Acc(dftmp, last_year)
    dfMod['filters_type'] = [nfilter] * dfMod.shape[0]
    dfMod['version'] = [version] * dfMod.shape[0]
    dfMod['Collections'] = [collection] * dfMod.shape[0]
    print(tabulate(dfMod.head(), headers = 'keys', tablefmt = 'psql'))
    # print(dftmp)
    lstDF_models.append(dfMod)
    # sys.exit()        
print("list tables  ",  len(lstDF_models))  # 1520
time.sleep(1)

      
nametable = 'vals_Class_reference_Colections_Before.csv'
dfModels = pd.concat(lstDF_models, axis=0, ignore_index=True)
pathExp = npath + '/dados/globalTables/' + nametable
dfModels.to_csv(pathExp)
print(f" we save the table {nametable} with {dfModels.shape} shapes")
