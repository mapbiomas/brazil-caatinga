# !/usr/bin/env python
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import starmap
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.model_selection import StratifiedKFold

from sklearn.pipeline import Pipeline
from sklearn.feature_selection import RFE
from sklearn.feature_selection import RFECV
from sklearn.linear_model import Perceptron
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from multiprocessing import Pool
# def plot_selectKBest(XValues, sscore):
#     X_indices = np.arange(XValues.shape[-1])
#     plt.figure(1)
#     plt.clf()
#     plt.bar(X_indices - 0.05, sscore, width=0.2)
#     plt.title("Feature univariate score")
#     plt.xlabel("Feature number")
#     plt.ylabel(r"Univariate score ($-Log(p_{value})$)")
#     plt.show()

# def Univariate_feature_selectionF_test (X_train, y_train):
#     selector = SelectKBest(f_classif, k=4)
#     selector.fit(X_train, y_train)
#     scores = -np.log10(selector.pvalues_)
#     scores /= scores.max()
#     plot_selectKBest(X_train, scores)
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

# get a list of models to evaluate
def get_models():
    models = dict()    
    # numberVar = len(colunas) - 5
    # building the three models 
    # cart# , n_features_to_select= numberVar
    # rfe = RFECV(estimator=DecisionTreeClassifier())
    # model = RandomForestClassifier()
    # models['cart'] = Pipeline(steps=[('s',rfe),('m',model)])
    # rf
    rfe = RFECV(estimator=RandomForestClassifier())
    model = DecisionTreeClassifier()
    models['rf'] = Pipeline(steps=[('s',rfe),('m',model)])
    # gbm
    rfe = RFECV(estimator=GradientBoostingClassifier())
    model = RandomForestClassifier()
    models['gbm'] = Pipeline(steps=[('s',rfe),('m',model)])
    #SVM
    # rfe = RFECV(estimator=SVC())
    # model = RandomForestClassifier()
    # models['svc'] = Pipeline(steps=[('s',rfe),('m',model)])

    return models

# evaluate a give model using cross-validation
def evaluate_model(nmodel, X, y):
    # cv = RepeatedStratifiedKFold(n_splits= 1, n_repeats=3, random_state=1)
    skf = StratifiedKFold(n_splits=5)
    scores = cross_val_score(nmodel, X, y, scoring='accuracy', cv=skf, n_jobs=2)
    return scores

def building_process_Model(X_train, y_train):
    # get the models to evaluate
    models = get_models()
    # evaluate the models and store results
    
    nmodel = starmap(lambda name, model: evaluate_model(model, X_train, y_train), models.items())
    for cc in range(10):
        scores = next(nmodel)
        print("Score ")
        print(scores)
        results.append(scores)
        name = models.keys()[cc]
        print("name = ", name)
        names.append(name)
        print('>%s %.3f (%.3f)' % (name, np.mean(scores), np.std(scores)))
    # plot model performance for comparison
    plt.boxplot(results, labels=names, showmeans=True)
    plt.show()

# loading table of ROIs and begining testing analises
def load_table_to_processing(cc, dir_fileCSV):
    df_tmp = pd.read_csv(dir_fileCSV)
    print(f"# {cc} loading train DF {df_tmp[colunas].shape} and ref {df_tmp['class'].shape}")
    X_train, X_test, y_train, y_test = train_test_split(df_tmp[colunas], df_tmp['class'], test_size=0.1, shuffle=False)


    # print(df_tmp.columns)
    # building_process_Model(df_tmp[colunas], df_tmp['class'])
    results, names = list(), list()
    # get the models to evaluate
    models = get_models()

    for name, model in models.items():
        scores = evaluate_model(model, X_train, y_train)
        print('>%s %.3f (%.3f)' % (name, np.mean(scores), np.std(scores)))
        print(scores)

def load_table_to_process(cc, dir_fileCSV):
    df_tmp = pd.read_csv(dir_fileCSV)
    print(f"# {cc} loading train DF {df_tmp[colunas].shape} and ref {df_tmp['class'].shape}")
    # X_train, X_test, y_train, y_test = train_test_split(df_tmp[colunas], df_tmp['class'], test_size=0.1, shuffle=False)

    min_features_to_select = 1
    print("get variaveis")    
    # gbm    
    skf = StratifiedKFold(n_splits=3)
    model = RandomForestClassifier()
    rfecv = RFECV(
            estimator=model,
            step=1,
            cv= skf,
            scoring= 'accuracy',
            min_features_to_select=min_features_to_select,
            n_jobs=2
        )

    rfecv.fit(df_tmp[colunas], df_tmp['class'])
    print(f"Optimal number of features: {rfecv.n_features_}")
    print("ranking ", rfecv.ranking_)
    print("")
    print("Support ", rfecv.support_)

    return rfecv.ranking_
    

if __name__ == '__main__':
    lst_bacias_notA = ['7622', '764', '765', '766', '767']
    # lst_years = ['2015','2016','2017','2018']# ['2019','2020','2021']
    # lst_years = ['2006','2007','2008','2009'] #['2010','2011','2012']

    lst_years = [str(kk) for kk in range(1985, 2000)]
    print("iniciar")
    print(lst_years)
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

    for cc, mdir in dirCSVs:        
        print("processing = ", mdir)
        namebacia = mdir.replace('ROIsCSV/ROIsCol8/', '').split('_')[0]
        myear = mdir.replace('ROIsCSV/ROIsCol8/', '').split('_')[1]
        # print(namebacia)
        if str(namebacia) in lst_bacias_notA and str(myear) in lst_years:
            print(f"========== executando ============ {mdir}")
            lst_rank = load_table_to_process(cc, mdir)

            newdir = mdir[:-4] + '.txt'
            filesave = open(newdir, 'w+')
            for rank in lst_rank:
                filesave.write(colunas[rank - 1] + '\n')
            
            filesave.close()