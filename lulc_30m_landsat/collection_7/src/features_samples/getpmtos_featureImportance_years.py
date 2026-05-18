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
from time import time
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
from sklearn.feature_selection import RFE
from numpy import set_printoptions
import arqParametros as arqParam


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

INPUT = os.getcwd()
INPUT = os.path.join(INPUT, "ROIscol7")
print("All data will loading from folder \n ====>  ", INPUT)

# define all feature of study 
columns_features = arqParam.allFeatures
classe = "class"
dictyear_feat_all = {}

for yyear in range(1985, 2020):
    print("#########################################################################")
    print("###################   Processing year = {} #######################\n".format(yyear))
        
    dataFyear = buildin_dataframefromCSVs (INPUT, yyear)
    upperMatrixCorr = get_show_matrix_correlation(dataFyear, columns_features, False)

    X = dataFyear[columns_features]
    y = dataFyear['class']

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)# Treinando modelo
    modelRF = RandomForestClassifier(
                                n_estimators=125, 
                                max_features=25)
    modelRF.fit(X_train, y_train)

    get_show_confusion_matrix(modelRF, X_test, y_test, columns_features, False)
    lst_feature_imp = get_feature_importance(modelRF, False)

    lst_var_importance = get_better_feature_uncorr(lst_feature_imp, upperMatrixCorr)

    # save feature    
    dictyear_feat_all[str(yyear)] = lst_var_importance
    print(lst_var_importance)

    
with open('registroYear_FeatsImp.json', 'w') as fp:
        json.dump(dictyear_feat_all, fp)