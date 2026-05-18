#!/usr/bin/env python
import glob
import pandas as pd
import numpy as np
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
colunas =  [
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
def method_RFECV(X_train, y_train, nameExports):
    skf = RepeatedStratifiedKFold(n_splits=2, n_repeats=5, random_state=36)
    model = GradientBoostingClassifier()
    min_features_to_select = 1
    rfecv = RFECV(
            estimator=model,
            step=1,
            cv= skf,
            scoring= 'accuracy',
            min_features_to_select=min_features_to_select,
            n_jobs=8
        )
    
    rfecv.fit(X_train, y_train)
    dict_inf = {
        'features': X_train.columns,
        'rankin': rfe.ranking_,
        'support': rfe.support_
    }
    
    rf_df = pd.DataFrame.from_dict(dict_inf)
    rf_df.to_csv('ROIsCSV/ROIsOut/rfeCVOut_' + nameExports, index=False, sep=';')

def method_RFE (X_train, y_train, nameExports):
    
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
    rf_df.to_csv('ROIsCSV/ROIsOut/rfeOut_' + nameExports, index=False, sep=';')

def load_table_to_process(cc, dir_fileCSV, metodo):
    
    df_tmp = pd.read_csv(dir_fileCSV)
    print(f"# {cc} loading train DF {df_tmp[colunas].shape} and ref {df_tmp['class'].shape}")
    # X_train, X_test, y_train, y_test = train_test_split(df_tmp[colunas], df_tmp['class'], test_size=0.1, shuffle=False)
    name_table = dir_fileCSV.replace('ROIsCSV/ROIsCol8/', '')
    
    print("get variaveis") 
    if metodo == 'RFE':
        method_RFE (df_tmp[colunas], df_tmp['class'], name_table)
    else:
        method_RFECV (df_tmp[colunas], df_tmp['class'], name_table)
        
      
    
if __name__ == '__main__':
    lst_bacias_notA = ['7622', '764', '765', '766', '767']
    # lst_years = ['2015','2016','2017','2018']# ['2019','2020','2021']
    # lst_years = ['2006','2007','2008','2009'] #['2010','2011','2012']

    lst_years = [str(kk) for kk in range(1985, 2023)]
    print("iniciar \n", lst_years)
    print()

    # /home/superusuario/Dados/mapbiomas/col8/features/
    npath = 'ROIsCSV/ROIsCol8/*.csv'
    lst_pathCSV = glob.glob(npath)
    dirCSVs = [(cc, kk) for cc, kk in enumerate(lst_pathCSV[:])]

    # print(lst_pathCSV)
    # # Create a pool with 4 worker processes
    # with Pool(4) as procWorker:
    #     # The arguments are passed as tuples
    #     result = procWorker.starmap(
    #                     load_table_to_processing, 
    #                     iterable= dirCSVs, 
    #                     chunksize=5)

    for cc, mdir in dirCSVs[: 1]:        
        print("processing = ", mdir)
        namebacia = mdir.replace('ROIsCSV/ROIsCol8/', '').split('_')[0]
        myear = mdir.replace('ROIsCSV/ROIsCol8/', '').split('_')[1]
       
        print(f"========== executando ============ {mdir}")
        lst_rank = load_table_to_process(cc, mdir, 'RFE')  # 'RFE', 'RFECV'
