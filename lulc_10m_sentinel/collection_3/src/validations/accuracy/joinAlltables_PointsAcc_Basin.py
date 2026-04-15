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
import pandas as pd
from pathlib import Path
from tabulate import tabulate
from tqdm import tqdm
tqdm.pandas()

def translate_class(row):

    dictRemapL2 =  {
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
        "OUTRA FORMAÇÃO NÃO FLORESTAL":4,
        "PASTAGEM": 21,
        "CANA": 21,
        "LAVOURA TEMPORÁRIA": 21,
        "LAVOURA PERENE": 21,
        "MINERAÇÃO": 22,
        "PRAIA E DUNA": 22,
        "INFRAESTRUTURA URBANA": 22,
        "VEGETAÇÃO URBANA": 22,
        "OUTRA ÁREA NÃO VEGETADA": 22,
        "0": 27,
        "3": 3,
        "21" : 21,
        "22" : 22,
        "RIO LAGO E OCEANO": 33,
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
        "33": 33,    
        "50": 4
    }
    # print(f"row reference > {row['reference']} | row classification > {row['classification']}")
    # typefilters = row['filters_type']    
    row['reference'] = dictRemapL2[str(row['reference'])]
    row['classification'] = dictRempCCL2[str(row['classification'])]
    return row

def translate_classification(row):
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
        "33": 33,    
        "50": 4
    }
    
    row['classification'] = dictRempCCL2[str(row['classification'])]
    return row
    

def concert_table_Acc(df_tmp):
    lstDFAc =[]
    for nyear in range(2016, 2024):
        col_ref = f'CLASS_{nyear}'
        col_class = f"classification_{nyear}"
        dft = df_tmp[[col_ref, col_class, 'bacia', 'filters_type']]  # 
        dft.columns = ['reference', 'classification', 'bacia', 'filters_type'] 
        dft = dft.fillna(0)
        # primerVal = dft['reference'].tolist()[0]
        # print("primeiro valor ", primerVal)
        print(f" >>> {col_ref} >>>>>> {col_class}")
        # print(dft['reference'].unique().tolist())
        dft = dft.apply(translate_class, axis= 1)
        # try:
        #     # print(int(primerVal))
        #     dft = dft.apply(translate_class, axis= 1)   
        #     # dft = dft.apply(translate_classification, axis= 1)         
        # except:
        #     dft = dft.apply(translate_class, axis= 1)
        
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
pathcsvsMC = os.path.join(npath,'dados','acuracia')
print("path of CSVs Matrix is \n ==>",  pathcsvsMC)
version_process = ['5','6','7','8','9']
lstfilesCSVs = glob.glob(pathcsvsMC + '/*.csv')
print(f" we load {len(lstfilesCSVs)} tables ")

lst_filters = [
    'Gap-fill', 'TemporalNJ3', 'TemporalNJ4', 'TemporalNJ5', 
    'TemporalAJ3', 'TemporalAJ4', 'TemporalAJ5', 'Spatial', 
    'Frequency', 'TemporalCCJ6', 'Spatials', 'SpatialsInt',
    'SpatialsAll'
]
lstDF_models = []

for cc, pathfile in enumerate(lstfilesCSVs):   
    print(f"=========== {pathfile.split("/")[-1]} ========== ")     
    # if nfilter in pathfile: #and "_" + vers + '.csv' in pathfile:         
        # print(pathfile)       
    namefile = pathfile.split("/")[-1]
    partes = namefile.split("_")
    print("partes >> ", partes)
    nfilter = partes[3]
    print("type of filters ", nfilter)
    if 'TemporalN' in namefile or 'TemporalA' in namefile:
        version = partes[-2][1:]
        janela = partes[-1].replace('.csv', '')
        nfilter += janela
    else:
        version = partes[-1].replace('.csv', '')[1:]
    #  
    print(f"file {cc} | m POS- CLASS| {nfilter}  version {version} | pathfile {pathfile.split("/")[-1]}")
    # sys.exit()
    dftmp = pd.read_csv(pathfile, quotechar='"')
    # print(dftmp.columns)
    colShow = ['CLASS_2016', 'classification_2016',  'classification_2022','bacia'] 
    print(tabulate(dftmp[colShow].head(2), headers = 'keys', tablefmt = 'psql'))
    dftmp['filters_type'] = [nfilter] * dftmp.shape[0]
    dfMod = concert_table_Acc(dftmp)

    # dfMod['filters_type'] = [nfilter] * dfMod.shape[0]
    dfMod['version'] = [version] * dfMod.shape[0]
    dfMod['Collections'] = 'Col2S2'

    print(tabulate(dfMod.head(), headers = 'keys', tablefmt = 'psql'))
    print("listando o valor da classe \n ", dfMod.classification.unique())
    # print(dftmp)
    lstDF_models.append(dfMod)
    # sys.exit()        
print("list tables  ",  len(lstDF_models))  # 1520
time.sleep(0.5)
# sys.exit() 
      
nametable = 'vals_Class_reference_model_All_Merger.csv'
dfModels = pd.concat(lstDF_models, axis=0, ignore_index=True)
pathExp = npath + '/dados/globalTables/' + nametable
dfModels.to_csv(pathExp, index= False, sep= ";")
print(f" we save the table {nametable} with {dfModels.shape} shapes")
