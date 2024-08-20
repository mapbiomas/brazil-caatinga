# !/usr/bin/env python
import glob
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import starmap
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score

from sklearn.model_selection import StratifiedKFold

from sklearn.pipeline import Pipeline
from sklearn.feature_selection import RFECV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
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
    'afvi_median', 'afvi_median_dry', 'afvi_median_wet', 'avi_median', 'avi_median_dry', 
    'avi_median_wet', 'awei_median', 'awei_median_dry', 'awei_median_wet', 'blue_median', 
    'blue_median_1', 'blue_median_dry', 'blue_median_dry_1', 'blue_median_wet', 
    'blue_median_wet_1', 'blue_min', 'blue_min_1', 'blue_stdDev', 'blue_stdDev_1', 
    'brba_median', 'brba_median_dry', 'brba_median_wet', 'brightness_median', 
    'brightness_median_dry', 'brightness_median_wet', 'bsi_median', 'bsi_median_1', 
    'bsi_median_2', 'cvi_median', 'cvi_median_dry', 'cvi_median_wet', 
    'dswi5_median', 'dswi5_median_dry', 'dswi5_median_wet', 'evi_median', 
    'evi_median_dry', 'evi_median_wet', 'gcvi_median', 'gcvi_median_dry', 
    'gcvi_median_wet', 'gemi_median', 'gemi_median_dry', 'gemi_median_wet', 'gli_median', 
    'gli_median_dry', 'gli_median_wet', 'green_median', 'green_median_1', 'green_median_dry', 
    'green_median_dry_1', 'green_median_texture', 'green_median_texture_1', 'green_median_wet', 
    'green_median_wet_1', 'green_min', 'green_min_1', 'green_stdDev', 'green_stdDev_1', 
    'gvmi_median', 'gvmi_median_dry', 'gvmi_median_wet', 'iia_median', 'iia_median_dry', 
    'iia_median_wet', 'lswi_median', 'lswi_median_dry', 'lswi_median_wet', 'mbi_median', 
    'mbi_median_dry', 'mbi_median_wet', 'ndwi_median', 'ndwi_median_dry', 'ndwi_median_wet', 
    'nir_median', 'nir_median_1', 'nir_median_contrast', 'nir_median_dry', 'nir_median_dry_1', 
    'nir_median_dry_contrast', 'nir_median_wet', 'nir_median_wet_1', 'nir_min', 'nir_min_1', 
    'nir_stdDev', 'nir_stdDev_1', 'osavi_median', 'osavi_median_dry', 'osavi_median_wet', 
    'ratio_median', 'ratio_median_dry', 'ratio_median_wet', 'red_median', 'red_median_1', 
    'red_median_contrast', 'red_median_dry', 'red_median_dry_1', 'red_median_dry_contrast', 
    'red_median_wet', 'red_median_wet_1', 'red_min', 'red_min_1', 'red_stdDev', 'red_stdDev_1', 
    'ri_median', 'ri_median_dry', 'ri_median_wet', 'rvi_median', 'rvi_median_1', 'rvi_median_wet', 
    'shape_median', 'shape_median_dry', 'shape_median_wet', 'slopeA', 'slopeA_1', 'swir1_median',
    'swir1_median_1', 'swir1_median_dry', 'swir1_median_dry_1', 'swir1_median_wet', 'swir1_median_wet_1', 
    'swir1_min', 'swir1_min_1', 'swir1_stdDev', 'swir1_stdDev_1', 'swir2_median', 'swir2_median_1', 
    'swir2_median_dry', 'swir2_median_dry_1', 'swir2_median_wet', 'swir2_median_wet_1', 'swir2_min', 
    'swir2_min_1', 'swir2_stdDev', 'swir2_stdDev_1', 'ui_median', 'ui_median_dry', 'ui_median_wet', 
    'wetness_median', 'wetness_median_dry', 'wetness_median_wet'
]
multiModels = False
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
    results = []
    names = []
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
    lstDF = []
    for dirCSV in dir_fileCSV:
        df_tmp = pd.read_csv(dirCSV[1])
        # removing unimportant columns of table files
        df_tmp = df_tmp.drop(['system:index', '.geo'], axis=1) 
        lstDF.append(df_tmp)    
    
    conDF  = pd.concat(lstDF, axis=0, ignore_index=True)
    print("temos {} filas ".format(conDF.shape))
    
    colunas = [kk for kk in df_tmp.columns]
    print("columns ", colunas)
    # sys.exit()
    colunas.remove('year')
    colunas.remove('class')
    try:
        colunas.remove('newclass')
        colunas.remove('random')
    except:
        print("")
    
    print(f"# {cc} loading train DF {df_tmp[colunas].shape} and ref {df_tmp['class'].shape}")
    
    X_train, X_test, y_train, y_test = train_test_split(df_tmp[colunas], df_tmp['class'], test_size=0.1, shuffle=False)

    # print(df_tmp.columns)
    # building_process_Model(df_tmp[colunas], df_tmp['class'])
    if multiModels:        
        # get the models to evaluate
        models = get_models()
        for name, model in models.items():
            scores = evaluate_model(model, X_train, y_train)
            print('>%s %.3f (%.3f)' % (name, np.mean(scores), np.std(scores)))
            print(scores)
    else:
        min_features_to_select = 2
        print("=========== get variaveis =============")    
        # gbm    
        skf = StratifiedKFold(n_splits=3)
        model = RandomForestClassifier()
        rfecv = RFECV(
                estimator=model,
                step=1,
                cv= skf,
                scoring= 'accuracy',
                min_features_to_select= min_features_to_select,
                n_jobs=2
            )

        rfecv.fit(conDF[colunas], conDF['class'])
        print(f"Optimal number of features: {rfecv.n_features_}")
        lstBandSelect = []
        limear = 30 
        if rfecv.n_features_ < 30: 
            limear = 30 - int(rfecv.n_features_)
        for cc, bndFeat in enumerate(colunas):
            # print("cc = ", cc, " <> ", bndFeat, " | ", rfecv.ranking_[cc], " | ", rfecv.support_[cc])
            if limear < 30: 
                if rfecv.ranking_[cc] < limear:
                    lstBandSelect.append(bndFeat)
                    # print(' adding ')
            else:
                if rfecv.ranking_[cc] < 4:
                    lstBandSelect.append(bndFeat)
                    # print(' adding ')

        return lstBandSelect, limear

def load_table_to_process(cc, dir_fileCSV):
    lstDF = []
    for dirCSV in dir_fileCSV:
        df_tmp = pd.read_csv(dirCSV[1])
        df_tmp = df_tmp.drop(['system:index', '.geo'], axis=1) 
        lstDF.append(df_tmp)
    
    conDF  = pd.concat(lstDF, axis=0, ignore_index=True)
    print("temos {} filas ".format(conDF.shape))
    colunas = [kk for kk in conDF.columns]
    
    # sys.exit()
    colunas.remove('year')
    colunas.remove('class')
    try:
        colunas.remove('newclass')
        colunas.remove('random')
    except:
        pass
    print("============ columns ================") # \n , colunas
    print(f"# {cc} loading train DF {conDF[colunas].shape} and ref {conDF['class'].shape}")
    # X_train, X_test, y_train, y_test = train_test_split(df_tmp[colunas], df_tmp['class'], test_size=0.1, shuffle=False)

    min_features_to_select = 1
    print("=========== get variaveis =============")    
    # gbm    
    skf = StratifiedKFold(n_splits=3)
    model = RandomForestClassifier()
    rfecv = RFECV(
            estimator=model,
            step=1,
            cv= skf,
            scoring= 'accuracy',
            min_features_to_select= min_features_to_select,
            n_jobs=2
        )

    rfecv.fit(conDF[colunas], conDF['class'])
    print(f"Optimal number of features: {rfecv.n_features_}")
    # print("ranking ", rfecv.ranking_)
    # print("")
    # print("Support ", rfecv.support_)
    lstBandSelect = []
    limear = 30 
    if rfecv.n_features_ < 30: 
        limear = 30 - int(rfecv.n_features_)
    for cc, bndFeat in enumerate(colunas):
        # print("cc = ", cc, " <> ", bndFeat, " | ", rfecv.ranking_[cc], " | ", rfecv.support_[cc])
        if limear < 30: 
            if rfecv.ranking_[cc] < limear:
                lstBandSelect.append(bndFeat)
                # print(' adding ')
        else:
            if rfecv.ranking_[cc] < 4:
                lstBandSelect.append(bndFeat)
                # print(' adding ')

    return lstBandSelect, limear

def filterLSTbyBacia_Year(lstDir, mbasin, nYear, prefix):
    lst_tmp = []
    for ndir in lstDir:  # ndir[1] name path file
        # print(ndir[1])
        if prefix + mbasin in ndir[1] and str(nYear) in ndir[1]:
            lst_tmp.append(ndir)
    return lst_tmp

def filterLSTbyBacia_YearTupla(lstDir, mbasin, nYear):
    lst_tmp = []
    cc = 0
    for ndir in lstDir:
        # print(ndir)
        if "/" + mbasin in ndir[1] and str(nYear) in ndir[1]:
            lst_tmp.append((cc, ndir[1]))            

    return lst_tmp

def getPathCSV (lstfolders):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])

    # folder of CSVs ROIs    
    lstpaths = []
    for npath in lstfolders:
        roisPathC = '/dados/' + npath
        mpathCC = pathparent + roisPathC
        lstpaths.append(mpathCC)
        print("add path of CSVs Rois is \n ==>",  mpathCC)
    
    return lstpaths, pathparent + '/dados/'

lstBacias = [
    '7421','741','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612', '7614','7615','7616','7617',
    '7618','7619', '7613'
]
lstYears = [str(kk) for kk in range(1985, 2023)]
print(lstYears)
# sys.exit()
lstFolders =  ['ROIs_Joins_GrBa/']#  ['Col9_ROIs_cluster/', 'Col9_ROIs_manual/']
nameFolder = lstFolders[0]
pathCSVsCCs, npathParent = getPathCSV(lstFolders)
print(f" numero {len(pathCSVsCCs)} conferindo  {pathCSVsCCs}")
# sys.exit()
byYear = True
byBacia = True
multiprocess = False

if __name__ == '__main__': 
    lst_pathCSV = []
    for mpath in pathCSVsCCs:
        lst_pathCSVcc = glob.glob(mpath + "*.csv")
        lst_pathCSV += lst_pathCSVcc

    dirCSVs = [(cc, kk) for cc, kk in enumerate(lst_pathCSV[:])]
    print(f"lista de path {len(dirCSVs)}")
    print(dirCSVs[0])
    # sys.exit()
    if multiprocess:
        # Create a pool with 4 worker processes 🍀
        dict_Bacia_year = []
        for nbacia in lstBacias:
            for year in lstYears:
                tpm_list = filterLSTbyBacia_YearTupla(dirCSVs, nbacia, year)
        with Pool(4) as procWorker:
            # The arguments are passed as tuples
            result = procWorker.starmap(
                            load_table_to_processing, 
                            iterable= dirCSVs, 
                            chunksize=5)
    else:
        cc = 0
        # for cc, mdir in dirCSVs:  
        for nbacia in ['777']: # lstBacias
            for year in lstYears:
                lstmDirs = filterLSTbyBacia_Year(dirCSVs, nbacia, year, "")  # "/"
                print(f"#  {cc}  processing {nbacia} and {year} == {lstmDirs}")
                # sys.exit()
                if cc > -1:
                    print(f"========== executando ============ \n => {lstmDirs}")
                    try:
                        lst_bnd_rank, nlimear = load_table_to_process(cc, lstmDirs)
                        nameFileSaved = lstmDirs[0][1].split("/")[-1][:-4] + '.txt'
                        print(" ✍️ saving ... ", nameFileSaved)
                        newdir = npathParent + "/results/" + nameFileSaved

                        with open(newdir, 'w+') as filesave:
                            for bndrank in lst_bnd_rank:
                                # print("número Rank ", rank)
                                filesave.write(bndrank + '\n')
                            filesave.write("limear_" + str(nlimear))
                    except:
                        print("=== Dado com Gap ==== ")
                cc += 1
        
        # sys.exit()