#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformação
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import sys
import os 
import glob
import copy
import pandas as pd
from pathlib import Path
from tqdm import tqdm
tqdm.pandas()

def getPathCSV (nfolders):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[1])
    # folder of CSVs ROIs
    roisPathAcc = pathparent + '/dados/' + nfolders
    return pathparent, roisPathAcc

data_remap = True
if data_remap:
    classes = [3,4,12,21,22,27,29,33]
else:
    classes = [3,4,12,15,18,21,22,27,29,33] # 
classMapB = [ 0, 3, 4, 5, 6, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =  [27, 3, 4, 3, 3, 3,12,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21]
columnsInt = [
    'Forest Formation', 'Savanna Formation', 'Grassland', 'Pasture',
    'Agriculture', 'Mosaic of Uses', 'Non vegetated area', 'Rocky Outcrop', 'Water'
] # 
colors = [ 
    "#1f8d49", "#7dc975", "#d6bc74", "#edde8e", "#f5b3c8", 
    "#ffefc3", "#db4d4f", "#112013", "#FF8C00", "#0000FF"
] # 
# bacia_sel = '741'

dict_class = {
    '3': 'Forest Formation', 
    '4': 'Savanna Formation', 
    '12': 'Grassland', 
    '15': 'Pasture', 
    '18': 'Agriculture', 
    '21': 'Mosaic of Uses', 
    '22': 'Non vegetated area', 
    '27': 'Not Observed', 
    '29': 'Rocky Outcrop', 
    '33': 'Water'
}

dict_classNat = {
    '3': 'Natural', 
    '4': 'Natural', 
    '12': 'Natural', 
    '15': 'Antrópico', 
    '18': 'Antrópico', 
    '21': 'Antrópico', 
    '22': 'Antrópico', 
    '27': 'Not Observed',
    '29': 'Natural', 
    '33': 'Natural'
}
dict_ColorNat = {
    'Natural': '#32a65e',
    'Antrópico': '#FFFFB2',
    'Not Observed': "#112013",
}
dict_colors = {}
for ii, cclass in enumerate(classes):
    dict_colors[dict_class[str(cclass)]] = colors[ii]

dict_colors['Natural'] = '#32a65e'
dict_colors['Antrópico'] = '#FFFFB2'
dict_colors['cobertura'] = '#FFFFFF'

def set_columncobertura(nrow):
    nclasse = nrow['classe']
    nrow['cobertura'] = dict_class[str(nclasse)]
    nrow['cob_level1'] = dict_classNat[str(nclasse)]
    nrow['cob_color'] = dict_colors[dict_class[str(nclasse)]]
    nrow['nat_color'] = dict_ColorNat[dict_classNat[str(nclasse)]]
    nrow['total'] = 'cobertura'
    return nrow


base_path, input_path_CSVs = getPathCSV('areaBacia')
print("path the base ", base_path)
print("path of CSVs from folder :  \n ==> ", input_path_CSVs)

# sys.exit()
processCol9 = True
showlstGerral = True
filesAreaCSV = glob.glob(input_path_CSVs + '/*.csv')
print("==================================================================================")
print("========== LISTA DE CSVs  NO FOLDER areasPrioritCSV ==============================")

if showlstGerral:
    for cc, namFile in enumerate(filesAreaCSV):
        print(f" #{cc}  >>  {namFile.split("/")[-1]}")
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    print("==================================================================================")


if processCol9:
    modelos = [ 'GTB','RF'] # 'RF', "GTB"
    # 'Gap-fillV2','SpatialV2St1', 'FrequencyV2nat', 
    # posclass = ['FrequencyV2natUso','SpatialV2St3','TemporalV2J3'] # , 
    # 'SpatialV3', 'FrequencyV3St1', "Estavel" 'toExport', 'Gap-fill', 'Spatial', 'Temporal', 'Frequency',
    # 'SpatialV3su', 'TemporalV3J3','TemporalV3J4','TemporalV3J5'
    posclass = ["toExport"] # , ,''TemporalV3J4',FrequencyV3St1' 'FrequencyV3St2'. 'SpatialV3St1', 
    version_process = ['31'] # '5','9','10','11', '12', '15''16', '17',18, '22', '25'
    modelos = posclass
    for nmodel in modelos[:]:
        for vers in version_process:
            lstDF = []
            for pathLayerA in filesAreaCSV:
                nameFiles = pathLayerA.split("/")[-1]
                # areaXclasse_CAATINGA_Col9.0_GTB_Temporal_vers_9_757
                # areaXclasse_CAATINGA_Col9.0_GTB_vers_7_775
                partes = nameFiles.replace("areaXclasse_CAATINGA_Col9.0_", "").split("_")
                name_model = partes[0]
                version = partes[-2]
                if len(partes) > 4:
                    name_model = partes[1]
                if name_model == nmodel: 
                    print(f" model {name_model}   {version}")
                if str(nmodel) == str(name_model) and vers == version:                
                    nbacia = partes[-1].replace(".csv", "")
                    print(f" ====== loading {nameFiles} ========") 
                    dftmp = pd.read_csv(pathLayerA)
                    dftmp = dftmp.drop(['system:index', '.geo'], axis='columns')
                    dftmp["Models"] = name_model
                    dftmp["Bacia"] = nbacia
                    dftmp["version"] = version
                    print("ver tamanho ", dftmp.shape)
                    if dftmp.shape[0] > 0:
                        lstDF.append(dftmp)
            # sys.exit()
            if len(lstDF) == 42:   
                ndfArea = pd.concat(lstDF, ignore_index= True)
                print("columna ", ndfArea.columns)
                # ndfArea = ndfArea.sort_values(by='year')
                print(f" === 📲 We have now <<{ndfArea.shape[0]}>> row in the DataFrame Area ===")
                print(ndfArea.head())
                classInic = [ 0,3,4, 9,10,12,15,18,21,22,27,29,33,50]
                classFin  = [27,3,4,12,12,12,21,21,21,22,27,29,33, 3]
                if nmodel in posclass:
                    classInic = [ 0,3,4, 9,10,12,15,18,21,22,27,29,33,50]
                    classFin  = [27,3,4,12,12,12,21,21,21,22,27,29,33, 3]
                
                ndfArea['classe'] = ndfArea['classe'].replace(classInic, classFin) 
                ndfArea = ndfArea[ndfArea['classe'] != 27]
                # Remap column values in inplace
                # sys.exit()
                # get values uniques 
                lstVers = [kk for kk in ndfArea['version'].unique()]
                lstClasses = [kk for kk in ndfArea['classe'].unique()]
                lstYears = [kk for kk in ndfArea['year'].unique()]

                # def get_Values_Areas()
                lstInt = ['version','year','classe','area']
                dfTest = ndfArea[lstInt].groupby(['version','year','classe'], as_index= False).agg('sum')
                dfTest['Bacia'] = ['Caatinga'] * dfTest.shape[0]
                dfTest['Models'] = [nmodel] * dfTest.shape[0]
                print(" 🫵 size dfTest ", dfTest.shape)
                print(dfTest.head(10))

                ndfAllArea = pd.concat([ndfArea, dfTest], ignore_index= True)
                ndfAllArea = ndfAllArea.progress_apply(set_columncobertura, axis= 1)

                print(" size dfAreaBiome = ", ndfAllArea.shape)
                print(ndfAllArea.head())

                nameexport = f"/dados/globalTables/areaXclasse_CAATINGA_{nmodel}_vers_{vers}_Col9.0.csv"
                print("we going to export with name => ", nameexport)
                ndfAllArea.to_csv(base_path + nameexport)
                print(" -------- DONE ! --------------")
                print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                print("==================================================================================")
            
            else:
                print("================================================================")
                print(f"      the model  {nmodel} fails {42 - len(lstDF)} image  ")
                for areadf in lstDF:
                    print(areadf["Bacia"].iloc[0])
else:
    lstColection = ['Col71', 'Col80']
    for col in lstColection:
        cc = 0
        lstDF = []
        for pathLayerA in filesAreaCSV:
            nameFiles = pathLayerA.split("/")[-1]
            partes = nameFiles.replace("areaXclasse_CAAT", "").split("_")

            if col in nameFiles and '_CAAT_' in nameFiles:     
                cc += 1           
                nbacia = partes[-1].replace(".csv", "")
                print(f" ====== loading {nameFiles} ========") 
                dftmp = pd.read_csv(pathLayerA)
                dftmp = dftmp.drop(['system:index', '.geo'], axis='columns')
                dftmp["Colacao"] = col
                dftmp["Bacia"] = nbacia
                print(f" # {cc} >> ver tamanho ", dftmp.shape)
                if dftmp.shape[0] > 0:
                    lstDF.append(dftmp)
        # sys.exit()
        if len(lstDF) > 0:   
            ndfArea = pd.concat(lstDF, ignore_index= True)
            print("columna ", ndfArea.columns)
            # ndfArea = ndfArea.sort_values(by='year')
            print(f" === 📲 We have now <<{ndfArea.shape[0]}>> row in the DataFrame Area ===")
            print(ndfArea.head())
            print(ndfArea['classe'].unique())
            if not data_remap:
                ndfArea['classe'] = ndfArea['classe'].replace(classMapB, classNew) 
            # ndfArea = ndfArea[ndfArea['classe'] != 0]
            # get values uniques 
            lstClasses = [kk for kk in ndfArea['classe'].unique()]
            lstYears = [kk for kk in ndfArea['year'].unique()]
            
            print("lista de classes ", lstClasses)

            lstInt = ['Colacao','year','classe','area']
            dfTest = ndfArea[lstInt].groupby(['Colacao','year','classe'], as_index= False).agg('sum')
            dfTest['Bacia'] = ['Caatinga'] * dfTest.shape[0]
            dfTest['Colacao'] = [col] * dfTest.shape[0]
            print(" 🫵 size dfTest ", dfTest.shape)
            print(dfTest.head(10))

            ndfAllArea = pd.concat([ndfArea, dfTest], ignore_index= True)
            ndfAllArea = ndfAllArea.progress_apply(set_columncobertura, axis= 1)

            print(" size dfAreaBiome = ", ndfAllArea.shape)
            print(ndfAllArea.head())

            nameexport = f"/dados/globalTables/areaXclasse_CAATINGA_{col}_red.csv"
            print("we going to export with name Coleção => ", nameexport)
            ndfAllArea.to_csv(base_path + nameexport)
            print(" -------- DONE ! --------------")
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            print("==================================================================================")