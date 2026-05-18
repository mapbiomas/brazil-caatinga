#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import glob
import sys
import os
import copy
import math
import json
import numpy as np 
import pandas as pd
from sklearn.svm import LinearSVC
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import chi2
from sklearn.feature_selection import SelectKBest
from sklearn.metrics import confusion_matrix, plot_confusion_matrix, accuracy_score
from sklearn import svm
from matplotlib.ticker import NullFormatter
from sklearn import manifold, datasets
import time
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
from sklearn.feature_selection import RFE
from numpy import set_printoptions
# import arqParametros as arqParam


def buildin_dataframefromCSVs (myfolder, year):
    allfiles = glob.glob(os.path.join(myfolder, "*.csv"))
    df_from_each_file = []

    zz = 0
    for cc, file in enumerate(allfiles):      
   
        # print('lindo de {} ==> {}'.format(cc ,file))        
        newdf = pd.read_csv(file)     
        newdf = newdf.drop(['system:index','.geo'], axis=1)
        df_from_each_file.append(newdf[newdf['year'] == year])
        zz += 1
        
    print("leiu {} de {} no folder".format(zz, len(allfiles)))

    concat_df  = pd.concat(df_from_each_file, axis=0, ignore_index=True)
    print("temos {} filas ".format(concat_df.shape))
    print(concat_df.head(3))

    return concat_df

def get_show_matrix_correlation(df_year, var_features, show):

    if show:
        plt.figure(figsize=(12, 14))
        varCorr = df_year[var_features].corr()
        sns.heatmap(varCorr,
                annot= False, fmt= '.2f', cmap= 'Greens')
        plt.title("correlação entre variaveis bacia " + bacia)
        plt.show()

    cor_matrix = df_year[var_features].corr().abs()
    upper_tri = cor_matrix.where(np.triu(np.ones(cor_matrix.shape), k=1).astype(np.bool_))
    return upper_tri


def get_show_confusion_matrix(modelo, XX_test, yy_test, col_features, show):

    if show:
        fig, ax = plt.subplots(figsize=(10, 10))
        plot_confusion_matrix(modelo, XX_test[columns_features], yy_test, ax=ax) 
        plt.show()  

    y_pred = modelo.predict(XX_test[col_features])
    matrix = confusion_matrix(y_test, y_pred)
    print("Matrix de correlation: \n ", matrix)

    varlorAcc = accuracy_score(yy_test, y_pred)
    print("Acurcia geral ====>  {}".format(varlorAcc))


def get_feature_importance(modeloRF, show):
    importances = pd.Series(data=modeloRF.feature_importances_, index=columns_features)
    importances = importances[importances[columns_features] > 0].sort_values(ascending = False)
    if show:
        plt.figure(figsize=(8,16))
        sns.barplot(x=importances, y=importances.index, orient='h').set_title('Importância de cada feature')

    return importances

def get_feature_importanceKScore(modeloRF, show):
    importances = pd.Series(data=modeloRF.feature_importances_, index=columns_features)
    importances = importances[importances[columns_features] > 0].sort_values(ascending = False)
    if show:
        plt.figure(figsize=(8,16))
        sns.barplot(x=importances, y=importances.index, orient='h').set_title('Importância de cada feature')

    return importances

def get_better_feature_uncorr(lst_imports, matrixCorr):
    
    ls_name_imp = []
    for cc, (name, _imp) in enumerate(lst_imports.iteritems()):
    #     print(cc, name, _imp)
        if cc == 0:
            # print(cc, name, _imp)
            ls_name_imp.append(name)
        else:
            anexar = True
            for nname in ls_name_imp:
                val_corr = matrixCorr[name][nname]
                if val_corr > 0.9:
                    anexar = False
                    
            if anexar:
                # print(cc, name, _imp)
                ls_name_imp.append(name)

    return ls_name_imp

def get_lst_features_selected(nmdir):
    ofile = open(nmdir)
    lst_features = []
    for line in ofile:
        lst_features.append(line[:-1])
    return lst_features

def get_yyear_intemedio(yyear_bef, yyear_aft):
    yyear_meio = 2012
    if yyear_bef < 2012 and yyear_aft > 2012:
        yyear_bef = 2012
    else:
        if (yyear_aft - yyear_bef) > 1:
            yyear_meio = int((yyear_aft + yyear_bef)/2)
        else:
            yyear_meio = yyear_aft

    return yyear_meio

def definir_year_from_lstYear(lst_new):
    lst_serie = []
    size_lst_arg = len(lst_new)
    year_threhold = 1985
    indicador = 0
    for yy in range(1985, 2023):
        if size_lst_arg > 1:
            if indicador == 0:            
                if yy < lst_new[indicador]:
                    lst_serie.append(lst_new[indicador])
                    # print(yy, " ", lst_serie)
                    if year_threhold == 1985:
                        year_threhold = get_yyear_intemedio(lst_new[indicador], lst_new[indicador + 1])
                        # print("atualizou ", year_threhold)
                else:
                    lst_serie.append(lst_new[indicador])
                    # print(yy, " ", lst_serie)
                    if yy == year_threhold:
                        indicador += 1
            
            elif indicador < size_lst_arg - 1:            
                if yy <= lst_new[indicador]:
                    lst_serie.append(lst_new[indicador])
                    # print(yy, " ", lst_serie)
                else:
                    year_threhold = get_yyear_intemedio(lst_new[indicador], lst_new[indicador + 1])
                    # print(year_threhold, ",", lst_new[indicador])
                    if year_threhold > lst_new[indicador]:
                        if yy < year_threhold:
                            lst_serie.append(lst_new[indicador])
                            # print(yy, " | ", lst_serie)
                        else:
                            indicador += 1
                            lst_serie.append(lst_new[indicador])
                            # print(yy, " ", lst_serie)
                # if indicador > 3:
                #     sys.exit()
            else:
                lst_serie.append(lst_new[indicador])
                # print(yy, " ", lst_serie)
        else:
            lst_serie.append(lst_new[indicador])

    return lst_serie

def remove_feature_with_1(row):
    feature = row['features']
    if '_1' in feature or '_2' in feature:
        row['remove'] = True
    else: 
        row['remove'] = False
    
    return row

INPUT = os.getcwd()
INPUT = os.path.join(INPUT, "ROIsCSV/ROIsCol8")
print("All data will loading from folder \n ====>  ", INPUT)

# define all feature of study 
# columns_features = arqParam.allFeatures
columns_features = [
    'afvi_median', 'afvi_median_dry', 'afvi_median_wet', 'avi_median', 'avi_median_dry', 'avi_median_wet', 
    'awei_median', 'awei_median_dry', 'awei_median_wet', 'blue_median', 'blue_median_dry', 'blue_median_wet',
    'blue_min', 'blue_stdDev', 'brba_median', 'brba_median_dry', 'brba_median_wet', 'brightness_median', 
    'brightness_median_dry', 'brightness_median_wet', 'bsi_median', 'bsi_median_dry', 'bsi_median_wet', 
    'cai_median', 'cai_median_dry', 'cai_stdDev', 'class', 'cvi_median', 'cvi_median_dry', 'cvi_median_wet', 
    'dswi5_median', 'dswi5_median_dry', 'dswi5_median_wet', 'evi2_amp', 'evi2_median', 'evi2_median_dry', 
    'evi2_median_wet', 'evi2_stdDev', 'gcvi_median', 'gcvi_median_1', 'gcvi_median_dry', 'gcvi_median_dry_1', 
    'gcvi_median_wet', 'gcvi_median_wet_1', 'gcvi_stdDev', 'gemi_median', 'gemi_median_dry', 'gemi_median_wet', 
    'gli_median', 'gli_median_dry', 'gli_median_wet', 'green_median', 'green_median_dry', 'green_median_texture', 
    'green_median_wet', 'green_min', 'green_stdDev', 'iia_median', 'iia_median_dry', 'iia_median_wet', 'lswi_median', 
    'lswi_median_dry', 'lswi_median_wet', 'mbi_median', 'mbi_median_dry', 'mbi_median_wet', 'ndvi_amp', 'ndvi_median', 
    'ndvi_median_dry', 'ndvi_median_wet', 'ndvi_stdDev', 'ndwi_amp', 'ndwi_median', 'ndwi_median_1', 'ndwi_median_dry', 
    'ndwi_median_dry_1', 'ndwi_median_wet', 'ndwi_median_wet_1', 'ndwi_stdDev', 'nir_contrast_median', 'nir_contrast_median_dry', 
    'nir_contrast_median_wet', 'nir_median', 'nir_median_dry', 'nir_median_wet', 'nir_min', 'nir_stdDev', 'osavi_median', 
    'osavi_median_dry', 'osavi_median_wet', 'pri_median', 'pri_median_dry', 'pri_median_wet', 'ratio_median', 'ratio_median_dry', 
    'ratio_median_wet', 'red_contrast_median', 'red_contrast_median_dry', 'red_contrast_median_wet', 'red_median', 'red_median_dry', 
    'red_median_wet', 'red_min', 'red_stdDev', 'ri_median', 'ri_median_dry', 'ri_median_wet', 'rvi_median', 'rvi_median_dry', 
    'rvi_median_wet', 'savi_median', 'savi_median_dry', 'savi_median_wet', 'savi_stdDev', 'shape_median', 'shape_median_dry', 
    'shape_median_wet', 'slope', 'swir1_median', 'swir1_median_dry', 'swir1_median_wet', 'swir1_min', 'swir1_stdDev', 'swir2_median', 
    'swir2_median_dry', 'swir2_median_wet', 'swir2_min', 'swir2_stdDev', 'ui_median', 'ui_median_dry', 'ui_median_wet', 'wetness_median', 
    'wetness_median_dry', 'wetness_median_wet'
]
classe = "class"
dictbacia_feat_all = {}

npath = 'ROIsCSV/dROIsV4Col8/*rank.csv'
lst_pathtxt = glob.glob(npath)

listaNameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]
lstBaciaF = []
for cc, item_bacia in enumerate(listaNameBacias[:]):
    print(f"# {cc + 1} loading geometry bacia {item_bacia}") 
    if item_bacia not in lstBaciaF:
        lstBaciaF.append(item_bacia) 
        dict_tmp = {}
        for mfile in lst_pathtxt:
            if item_bacia in mfile:
                print(mfile)
                myear = mfile.replace('ROIsCSV/dROIsV4Col8/', '').split('_')[1]
                dfyear = pd.read_csv(mfile)
                dfyear = dfyear.sort_values(by=['ranking'])
                dfyear = dfyear[dfyear['ranking'] > 1]
                dfyear = dfyear.apply(remove_feature_with_1, axis=1)
                time.sleep(2)
                print(dfyear.shape)
                if dfyear.shape[0] > 1:
                    dfyear = dfyear[dfyear['remove'] == False]
                    print(dfyear.head(28))
                    if dfyear.shape[0] > 60:
                        lst_feat = dfyear['features'].tolist()[:100]
                    else:
                        lst_feat = dfyear['features'].tolist() + lst_feat
                        lst_feat = lst_feat[:100]
                else:
                    # lst_feat = get_lst_features_selected(mfile)
                    print("==== loading features before =====")
                    print(lst_feat)
                    dict_tmp[myear] = lst_feat
                    
        dictbacia_feat_all[item_bacia] = dict_tmp

with open('lstInicialBacia_Year_FeatsSelNorm.json', 'w') as fp:
        json.dump(dictbacia_Yeat_Feat, fp)

# sys.exit()
dictbacia_Yeat_Feat = {}
for cc, item_bacia in enumerate(listaNameBacias[:]):
    # for yyear, lstFeat in dictYY.items():
    #     print(f"Bacia  {nbacia} YY {yyear} => {len(lstFeat)} ")
    #     print("          ", lstFeat[:5])
    dict_temp = {}
    yearsKeys = [int(yy) for yy in dictbacia_feat_all[item_bacia].keys()]
    yearsKeys.sort()
    print(" ", yearsKeys)
    newlstYears = definir_year_from_lstYear(yearsKeys)
    print(item_bacia, " ", len(newlstYears))
    for cc, yy in enumerate(range(1985, 2023)):
        dict_temp[str(yy)] = dictbacia_feat_all[item_bacia][str(newlstYears[cc])]
    
    dictbacia_Yeat_Feat[item_bacia] = dict_temp
## #   ==============================================================================
# for yyear in range(1985, 1986):  # 2022
#     print("#########################################################################")
#     print("###################   Processing year = {} #######################\n".format(yyear))
        
#     dataFyear = buildin_dataframefromCSVs (INPUT, yyear)
#     # if yyear == 1985:
#     #     colunas = [kk for kk in dataFyear.columns]
#     # print(colunas)
#     upperMatrixCorr = get_show_matrix_correlation(dataFyear, columns_features, False)

#     X = dataFyear[columns_features]
#     y = dataFyear['class']

#     X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)# Treinando modelo
#     modelRF = RandomForestClassifier(
#                                 n_estimators=225, 
#                                 max_features=30)
#     modelRF.fit(X_train, y_train)

#     get_show_confusion_matrix(modelRF, X_test, y_test, columns_features, False)
#     lst_feature_imp = get_feature_importance(modelRF, False)

# #     lst_var_importance = get_better_feature_uncorr(lst_feature_imp, upperMatrixCorr)

# #     # save feature    
# #     dictyear_feat_all[str(yyear)] = lst_var_importance
# #     print(lst_var_importance)

    
with open('regBacia_Year_FeatsSelfromManual.json', 'w') as fp:
        json.dump(dictbacia_Yeat_Feat, fp)