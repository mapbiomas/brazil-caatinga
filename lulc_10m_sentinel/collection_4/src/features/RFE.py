#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import os
import sys
import glob
import pandas as pd
import numpy as np
from icecream import ic
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.model_selection import cross_val_score
from sklearn.feature_selection import RFE
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

# References 
# https://www.kdnuggets.com/2020/10/feature-ranking-recursive-feature-elimination-scikit-learn.html

"""
Recursive Feature Elimination 
The first item needed for recursive feature elimination is an estimator; for example,
a linear model or a decision tree model.

These models have coefficients for linear models and feature importances in decision tree models.
In selecting the optimal number of features, the estimator is trained and the features are selected
via the coefficients, or via the feature importances. The least important features are removed. 
This process is repeated recursively until the optimal number of features is obtained.
"""

class methods_fromRFE():

    colunas =  [
        'afvi_median', 'afvi_median_dry', 'afvi_median_wet', 'avi_median', 'avi_median_dry', 'avi_median_wet', 'awei_median', 
        'awei_median_dry', 'awei_median_wet', 'blue_median', 'blue_median_1', 'blue_median_dry', 'blue_median_dry_1', 
        'blue_median_wet', 'blue_median_wet_1', 'blue_min', 'blue_min_1', 'blue_stdDev', 'blue_stdDev_1', 'brba_median', 
        'brba_median_dry', 'brba_median_wet', 'brightness_median', 'brightness_median_dry', 'brightness_median_wet', 
        'bsi_median', 'bsi_median_1', 'bsi_median_2', 'cvi_median', 'cvi_median_dry', 'cvi_median_wet', 'dswi5_median', 
        'dswi5_median_dry', 'dswi5_median_wet', 'evi_median', 'evi_median_dry', 'evi_median_wet', 'gcvi_median', 
        'gcvi_median_dry', 'gcvi_median_wet', 'gemi_median', 'gemi_median_dry', 'gemi_median_wet', 'gli_median', 
        'gli_median_dry', 'gli_median_wet', 'green_median', 'green_median_1', 'green_median_dry', 'green_median_dry_1', 
        'green_median_texture', 'green_median_texture_1', 'green_median_wet', 'green_median_wet_1', 'green_min', 'green_min_1', 
        'green_stdDev', 'green_stdDev_1', 'gvmi_median', 'gvmi_median_dry', 'gvmi_median_wet', 'iia_median', 'iia_median_dry', 
        'iia_median_wet', 'lswi_median', 'lswi_median_dry', 'lswi_median_wet', 'mbi_median', 'mbi_median_dry', 'mbi_median_wet', 
        'ndwi_median', 'ndwi_median_dry', 'ndwi_median_wet', 'nir_median', 'nir_median_1', 'nir_median_contrast', 'nir_median_dry', 
        'nir_median_dry_1', 'nir_median_dry_contrast', 'nir_median_wet', 'nir_median_wet_1', 'nir_min', 'nir_min_1', 'nir_stdDev', 
        'nir_stdDev_1', 'osavi_median', 'osavi_median_dry', 'osavi_median_wet', 'ratio_median', 'ratio_median_dry', 
        'ratio_median_wet', 'red_median', 'red_median_1', 'red_median_contrast', 'red_median_dry', 'red_median_dry_1', 
        'red_median_dry_contrast', 'red_median_wet', 'red_median_wet_1', 'red_min', 'red_min_1', 'red_stdDev', 'red_stdDev_1', 
        'ri_median', 'ri_median_dry', 'ri_median_wet', 'rvi_median', 'rvi_median_1', 'rvi_median_wet', 'shape_median', 
        'shape_median_dry', 'shape_median_wet', 'slope', 'slopeA', 'slopeA_1', 'slope_1', 'swir1_median', 'swir1_median_1', 
        'swir1_median_dry', 'swir1_median_dry_1', 'swir1_median_wet', 'swir1_median_wet_1', 'swir1_min', 'swir1_min_1', 
        'swir1_stdDev', 'swir1_stdDev_1', 'swir2_median', 'swir2_median_1', 'swir2_median_dry', 'swir2_median_dry_1', 
        'swir2_median_wet', 'swir2_median_wet_1', 'swir2_min', 'swir2_min_1', 'swir2_stdDev', 'swir2_stdDev_1', 'ui_median', 
        'ui_median_dry', 'ui_median_wet', 'wetness_median', 'wetness_median_dry', 'wetness_median_wet'
    ]

    def __init__(self, namepathroot, nameFolderSaved):
        self.namepathroot = namepathroot
        self.nameFolderSaved = nameFolderSaved

    def method_RFECV(self, X_train, y_train, nameExports):
        # namebacia = nnameFile.split('_')[0]
        # myear = nnameFile.split('_')[1]
        skf = RepeatedStratifiedKFold(n_splits=12, n_repeats=5, random_state=36)
        model = GradientBoostingClassifier()
        min_features_to_select = 6
        rfecv = RFECV(
                estimator=model,
                step=1,
                cv= skf,
                scoring= 'accuracy',
                min_features_to_select=min_features_to_select,
                n_jobs= 8
            )
        
        rfecv.fit(X_train, y_train)
        dict_inf = {        
            'features': X_train.columns,
            'rankin': rfe.ranking_,
            'support': rfe.support_
        }
        
        rf_df = pd.DataFrame.from_dict(dict_inf)
        namePathtmp = self.namepathroot + '/' + self.nameFolderSaved+ '/' + 'rfeCVOut_' + nameExports
        rf_df.to_csv(namePathtmp, index=False, sep=';')

    def method_RFE (self, X_train, y_train, nameExports):        
        model = GradientBoostingClassifier()
        rfe = RFE(
            estimator=GradientBoostingClassifier(), 
            n_features_to_select=6
        )

        pipe = Pipeline([('Feature Selection', rfe), ('Model', model)])
        skf = RepeatedStratifiedKFold(n_splits=12, n_repeats=5, random_state=36)
        n_scores = cross_val_score(pipe, X_train, y_train, scoring='accuracy', cv=skf, n_jobs=8)

        print("Saving data processesed ")
        # next step is to fit this pipeline to the dataset.
        pipe.fit(X_train, y_train)
        # building dataframe with results 
        dict_inf = {
            'features': X_train.columns,
            'rankin': rfe.ranking_,
            'support': rfe.support_
        }
        
        rf_df = pd.DataFrame.from_dict(dict_inf)
        namePathtmp = self.namepathroot + '/' + self.nameFolderSaved+ '/' + 'rfeOut_' + nameExports
        rf_df.to_csv(namePathtmp, index=False, sep=';')

    def load_table_to_process(self, cc, dir_fileCSV, metodo, nomeFile):    
        df_tmp = pd.read_csv(dir_fileCSV)
        df_tmp = df_tmp.drop(['system:index', '.geo'], axis='columns')
        if len(self.colunas) == 0:
            colunasDF = [kk for kk in df_tmp.columns]
            print(colunasDF)
            if 'year' in colunasDF:
                colunasDF.remove('year')
            if 'class' in colunasDF:
                colunasDF.remove('class')
            self.colunas = colunasDF
            
        for yyear in range(1985, 2023):
            # ic(f" Working year {yyear}")
            df_tmpYY =  df_tmp[df_tmp['year'] == yyear]
            # sys.exit()
            print(f" # {cc} 🚨 loading train DF {df_tmpYY[self.colunas].shape} and ref {df_tmpYY['class'].shape} by year {yyear}")
            dictClass = df_tmpYY['class'].value_counts()
            print("     classes:  ", [int(kk) for kk in dictClass.index.tolist()])
            print("  quantities:  ", dictClass.tolist())

            # X_train, X_test, y_train, y_test = train_test_split(df_tmp[colunas], df_tmp['class'], test_size=0.1, shuffle=False)
            # name_table = dir_fileCSV.replace('ROIsCSV/ROIsCol8/', '')
            nnomeFileE = nomeFile + "_" + str(yyear)
            print("get variaveis") 
            if metodo == 'RFE':
                self.method_RFE (df_tmpYY[self.colunas], df_tmpYY['class'], nnomeFileE)
            else:
                self.method_RFECV (df_tmpYY[self.colunas], df_tmpYY['class'], nnomeFileE)
        
def getPathCSV(folderROIs):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])
    print("path parents ", pathparent)
    # folder results of CSVs ROIs
    mpath_bndImp = pathparent + '/dados/' + folderROIs
    print("path of CSVs Rois is \n ==>",  mpath_bndImp)
    return mpath_bndImp, pathparent 

    
if __name__ == '__main__':
    lst_bacias_notA = ['7622', '764', '765', '766', '767']
    # lst_years = ['2015','2016','2017','2018']# ['2019','2020','2021']
    # lst_years = ['2006','2007','2008','2009'] #['2010','2011','2012']

    
    # /home/superusuario/Dados/mapbiomas/col8/features/
    # nameFolderCSV = "Col9_ROIs_cluster"
    # nameFolderCSV = "gradeROIsbasin"
    nameFolderCSV = "ROIs_Joins_GrBa"
    npathBase, pathroot = getPathCSV(nameFolderCSV)

    lst_pathCSV = glob.glob(npathBase + '/*.csv')
    dirCSVs = [(cc, kk) for cc, kk in enumerate(lst_pathCSV[:])]

    # print(lst_pathCSV)
    # # Create a pool with 4 worker processes
    # with Pool(4) as procWorker:
    #     # The arguments are passed as tuples
    #     result = procWorker.starmap(
    #                     load_table_to_processing, 
    #                     iterable= dirCSVs, 
    #                     chunksize=5)
    pathroot = os.path.join(pathroot, 'dados')
    folderOutREF = nameFolderCSV + '_REF'
    folderOutREFCV = nameFolderCSV + '_REFCV'
    pathOutREF = os.path.join(pathroot, folderOutREF)
    pathOutREFCV = os.path.join(pathroot, folderOutREFCV)
    try:    
        os.makedirs(pathOutREF, mode=0o777, exist_ok=False)
        os.makedirs(pathOutREFCV, mode=0o777, exist_ok=False)
        print(f"make folders folderOuts \n  ===>  {pathOutREF} \n  ===>  {pathOutREFCV}")
    except:
        print(f" === 🚨Yours analises will be save in ===== \n  ===>  {pathOutREF} \n  ===>  {pathOutREFCV}")
    
    # sys.exit()
    methodtoSeleting = 'RFE'
    if methodtoSeleting == 'RFE':
        methods_fromRFECC = methods_fromRFE(pathroot, folderOutREF)
    else:
        methods_fromRFECC = methods_fromRFE(pathroot, folderOutREFCV)
    
    for cc, mdir in dirCSVs[: 1]:        
        print("processing = ", mdir)
        nameFile = mdir.replace(npathBase, '')[1:]
        # print(nameFile)
        # sys.exit()
        print(f"========== executando ============ \n {mdir}")
        lst_rank = methods_fromRFECC.load_table_to_process(cc, mdir, methodtoSeleting, nameFile)  # 'RFE', 'RFECV'
