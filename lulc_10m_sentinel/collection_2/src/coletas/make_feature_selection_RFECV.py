import os
import sys
import glob
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from numpy import set_printoptions
import matplotlib.pyplot as plt
from sklearn.feature_selection import RFE, RFECV
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split 

class processin_features_byYears(object):
    columns_features = [
        "afvi_median","afvi_median_dry","afvi_median_wet","avi_median",
        "avi_median_dry","avi_median_wet","awei_median","awei_median_dry","awei_median_wet",
        "blue_median","blue_median_dry","blue_median_wet","blue_stdDev","brba_median",
        "brba_median_dry","brba_median_wet","brightness_median","brightness_median_dry","brightness_median_wet",
        "bsi_median","bsi_median_1","bsi_median_2","cvi_median",
        "cvi_median_dry","cvi_median_wet","dswi5_median","dswi5_median_dry","dswi5_median_wet",
        "evi_median","evi_median_dry","evi_median_wet","gcvi_median","gcvi_median_dry",
        "gcvi_median_wet","gemi_median","gemi_median_dry","gemi_median_wet","gli_median",
        "gli_median_dry","gli_median_wet","green_median","green_median_dry","green_median_texture",
        "green_median_wet","green_min","green_stdDev","gvmi_median","gvmi_median_dry",
        "gvmi_median_wet","iia_median","iia_median_dry","iia_median_wet","lswi_median",
        "lswi_median_dry","lswi_median_wet","mbi_median","mbi_median_dry","mbi_median_wet",
        "nddi_median","nddi_median_dry","nddi_median_wet","ndvi_median","ndvi_median_dry",
        "ndvi_median_wet","ndwi_median","ndwi_median_dry","ndwi_median_wet","nir_median",
        "nir_median_contrast","nir_median_dry","nir_median_dry_contrast","nir_median_wet","osavi_median",
        "osavi_median_dry","osavi_median_wet","ratio_median","ratio_median_dry","ratio_median_wet",
        "red_edge_1_median","red_edge_1_median_dry","red_edge_1_median_wet","red_edge_1_stdDev","red_edge_2_median",
        "red_edge_2_median_dry","red_edge_2_median_wet","red_edge_2_stdDev","red_edge_3_median","red_edge_3_median_dry",
        "red_edge_3_median_wet","red_edge_3_stdDev","red_edge_4_median","red_edge_4_median_dry","red_edge_4_median_wet",
        "red_edge_4_stdDev","red_median","red_median_contrast","red_median_dry","red_median_dry_contrast",
        "red_median_wet","red_min","red_stdDev","ri_median","ri_median_dry",
        "ri_median_wet","rvi_median","rvi_median_1","rvi_median_wet","shape_median",
        "shape_median_dry","shape_median_wet","swir1_median","swir1_median_dry","swir1_median_wet",
        "swir1_stdDev","swir2_median","swir2_median_dry","swir2_median_wet","swir2_stdDev",
        "ui_median","ui_median_dry","ui_median_wet","wetness_median","wetness_median_dry",
        "wetness_median_wet"
    ]
    classe = "class"

    def __init__(self, Ns_estimators, learning_rates, path_features):
        self.dfROIs = None
        self.dfCC = None
        self.yearAct = None
        self.lstClass = None
        self.lst_N_estimators = Ns_estimators
        self.lst_learning_rate = learning_rates
        self.path_features = path_features
        self.betterPmtrosSet = 0
        self.dictpmtGTB = {}
        count = 0
        for ne in self.lst_N_estimators:
            for lr in self.lst_learning_rate:
                self.dictpmtGTB[str(count)] = [ne, lr]
                print(f"# {count + 1} mudando n_estimators= {ne} & learning_rate= {lr}")
                count += 1

    def get_data(self, myDF, nYear): 
        self.dfROIs = myDF
        self.yearAct = nYear
        self.lstClass = self.dfROIs[self.classe].unique().tolist()
        self.buildingPercentsofClass()
        
    def get_class_withSmallsize(self, dFrames, lstSearch):
        classeMin = []
        for cclass in lstSearch:
            nsize = dFrames[dFrames[self.classe] == cclass].shape[0]
            print(f" classe {cclass} == > size = {nsize}")
            if nsize < 4:
                classeMin.append(cclass)
        return classeMin
    
    def split_dataFrame(self, dFrame):
        # split data into inputs (X) and outputs (y)
        dFrameg1 = dFrame[dFrame[self.classe] == 4]  # para a classe 4
        dFrameg2 = dFrame[dFrame[self.classe] != 4]
        # lstClasses  = [kk for kk in self.lstClass if kk != 4]        
        
        maximoROIs = self.dfCC[self.dfCC['class'] != 4]['count'].max()
        maximoROIs += 150
        newlstDF = []        
        print("size dFrame4 ", dFrameg1.shape, " and the next class maximum is ", maximoROIs)
        # sampled the N samples fro dataframe stratified
        tmpDF = dFrameg1.sample(n= int(maximoROIs), random_state= np.random.seed(int(maximoROIs)))
        concDF  = pd.concat([tmpDF, dFrameg2], ignore_index=True) #
        print("temos {} filas ".format(concDF.shape))
        concDF.head()
        lstCCg1 = [3,4,15,18]
        lstCCg2 = [12,21,22,33]
        print(" ====> analisando size of class smaller ")
        lstclassMinM = self.get_class_withSmallsize(dFrame, lstCCg2)

        if len(lstclassMinM)  > 0:
            for ccm in lstclassMinM:
                print(" --- will be remove class ---", ccm)
                lstCCg2.remove(ccm)
            addFeatext = True
            
        dFrameg1 = concDF[concDF[self.classe].isin(lstCCg1)]
        dFrameg2 = concDF[concDF[self.classe].isin(lstCCg2)]
        
        # print(f" adding {int(propCC * maximoROIs)} samples from class [{cclass}]")
        # X = dataFrame[self.columns_features[:]]
        # y = dataFrame[self.classe]
        X_traing1, X_testg1, y_traing1, y_testg1 = train_test_split(
                            dFrameg1[self.columns_features[:]], dFrameg1[self.classe], 
                            train_size=0.02, 
                            random_state=1,
                            shuffle=True,
                            stratify = dFrameg1[self.classe]
                        )
        print(f"colected Xtrain {X_traing1.shape[0]} | Xtest {X_testg1.shape[0]} | " + 
                                f"ytrain {y_traing1.shape[0]} | ytest {y_testg1.shape[0]}")
        X_traing2, X_testg2, y_traing2, y_testg2 = train_test_split(
                            dFrameg2[self.columns_features[:]], dFrameg2[self.classe], 
                            train_size=0.3, 
                            random_state=1,
                            shuffle=True,
                            stratify = dFrameg2[self.classe]
                        )
        print(f"colected Xtrain {X_traing2.shape[0]} | Xtest {X_testg2.shape[0]} | " + 
                                f"ytrain {y_traing2.shape[0]} | ytest {y_testg2.shape[0]}")
        self.X_train = pd.concat([X_traing1, X_traing2], ignore_index=True)
        self.X_test = pd.concat([X_testg1, X_testg2], ignore_index=True)
        self.y_train = pd.concat([y_traing1, y_traing2], ignore_index=True)
        self.y_test = pd.concat([y_testg1, y_testg2], ignore_index=True)

        print(f" ==== know we have {self.X_train.shape} tro train ==== ")
        print(self.y_train.value_counts(normalize= True), self.y_train.value_counts())


    def buildingPercentsofClass(self):
        self.dfCC = self.dfROIs['class'].value_counts()
        self.dfCC = self.dfCC.reset_index()
        # get total number of classes
        total = np.sum(self.dfCC['count'].tolist())
        print(f"total = {total}")
        self.dfCC['percent'] = round((self.dfCC['count'] * 100)/ total, 2)
        self.dfCC['Years'] = np.ones(self.dfCC.shape[0]).astype(int) * self.yearAct
        # print(dfCC)
        print(f" == the CLASS of rois distribuided in {self.yearAct} are == \n ", self.dfCC)

    def processingMultiplesModels(self):
        # split the dataframe in stratify samples by class and balance class 4
        self.split_dataFrame(self.dfROIs)
        maximAcc = 0.0
        # get the models to evaluate
        models = self.get_models()
        # evaluate the models and store results
        results, names = list(), list()
        start = time.time()
        count = 1
        for name, model in models.items():
            print(f"#{count}/{len(models.items())} processing model {name}")
            scores = self.evaluate_model(model, self.X_train[self.columns_features[:]], self.y_train)
            results.append(scores)
            names.append(name)
            print('  >%s %.3f (%.3f)' % (name, np.mean(scores), np.std(scores)))
            if maximAcc < np.mean(scores):
                self.betterPmtrosSet = count - 1
                maximAcc = np.mean(scores)

            count += 1
        # plot model performance for comparison
        # plt.boxplot(results, labels=names, showmeans=True)
        # plt.show()
        end = time.time()
        tiempo = end - start
        if tiempo < 60:
            print(f"model trained in {tiempo} seconds")
        else:
            print(f"model trained in {tiempo/60} minutos")

    
    # get a list of models to evaluate
    def get_models(self):
        min_features_to_select = 7
        models = dict()
        
        # criando pipeline do modelos gradiente Boosting com varios paramentros
        cv = StratifiedKFold(3)
        for cc in range(len(self.dictpmtGTB.keys())):
            GTBmodel = GradientBoostingClassifier(
                            n_estimators= self.dictpmtGTB[str(cc)][0], 
                            learning_rate= self.dictpmtGTB[str(cc)][1], 
                            max_features= 7
                        )
            rfe = RFECV(
                    estimator=GTBmodel,
                    step=1,
                    cv=cv,
                    scoring="accuracy",
                    min_features_to_select=min_features_to_select,
                    # n_jobs=1,
                )

            models[str(cc)] = Pipeline(steps=[('s', rfe),('m', GTBmodel)])
        return models

    # evaluate a give model using cross-validation
    def evaluate_model(self, model, X, y):
        cv = StratifiedKFold(5)
        scores = cross_val_score(model, X, y, scoring='accuracy', cv=cv, n_jobs=1, error_score='raise')
        return scores

    def get_better_featuresSet(self,fixarNumbFeat, numbMin, regg, yyear):
        # Create a Path object
        path_name_file = self.path_features + f'/featuresSelectS2_{regg}_{yyear}.csv'
        file_path = Path(path_name_file)

        # Check if the file exists
        if file_path.exists():
            print(" ******* list of features selected was saved ********")

        else:
            self.split_dataFrame(self.dfROIs)
            
            GTBmodel = GradientBoostingClassifier(
                            n_estimators= self.dictpmtGTB[str(self.betterPmtrosSet)][0], 
                            learning_rate= self.dictpmtGTB[str(self.betterPmtrosSet)][1], 
                            max_features= 7, 
                            random_state=42
                        )

            start = time.time()
            # Minimum number of features to consider
            min_features_to_select =  7 
            cv = StratifiedKFold(3)
            rfecv = RFECV(
                estimator=GTBmodel,
                step=1,
                cv=cv,
                scoring="accuracy",
                min_features_to_select=min_features_to_select,
                n_jobs=-1,
            )
            rfecv.fit(self.X_train[self.columns_features], self.y_train)
            print(f"Optimal number of features: {rfecv.n_features_}")

            end = time.time()
            tiempo = end - start
            if tiempo < 60:
                print(f"model trained in {tiempo} seconds")
            else:
                print(f"model trained in {tiempo/60} minutos")

            ## valores ótimos aparecem com valor 1 no ranking
            lst_ranking = [(kk, cc) for cc, kk in enumerate(rfecv.ranking_) if kk < 2]
            print("quantos features otimos ", len(lst_ranking))
            numbNotOti = numbMin
            if fixarNumbFeat  and numbMin > len(lst_ranking):
                numbNotOti = numbMin - len(lst_ranking)
            print(f"Addicionando << {numbNotOti} >> features a mais não ótimas ")
            lst_ranking = [(kk, cc) for cc, kk in enumerate(rfecv.ranking_) if kk < numbNotOti]
            print("quantos features otimos ", len(lst_ranking))

            lstFeatSelect = []
            count = 1
            for kk, cc in lst_ranking:
                print(f"# {count} ranking {kk} | pos {cc} >> feature >> {self.columns_features[cc]}")
                lstFeatSelect.append(self.columns_features[cc])
                count += 1

            dict_result= {
                'ranking': lst_ranking,
                'features': lstFeatSelect
            }
            dfresult = pd.DataFrame.from_dict(dict_result)
            path_name_file = self.path_features + f'/featuresSelectS2_{regg}_{yyear}.csv'
            dfresult.to_csv(path_name_file, index= False)

            print("tabela salva em pasta do drive")






# fixar o número de variaveis
fixarNFeat = True
# número máximo de variaveis para o modelo das 144
numMin = 70
path_csvs = '/run/media/superuser/Almacen/mapbiomas/dadosCol9/ROIs_S2/shp_ROIs_S2_caat'
path_base = '/run/media/superuser/Almacen/mapbiomas/dadosCol9/ROIs_S2/featuresSet'
lstpathfiles = glob.glob(path_csvs + "/*.csv")
lstYear = list(range(2023, 2015, -1))
print(" year ", lstYear);
yyear = 2023

lstEstimadors = [20, 30, 40, 50, 60]
lstLearnRate = [0.001, 0.005, 0.01, 0.1] 
procFeatures_byYears = processin_features_byYears(lstEstimadors, lstLearnRate, path_base)
melhorModelo = 0
# sys.exit()
dictModel = {}
try:
    with open("dictBetterModelpmtSet.json", 'r') as fh:
        dictModel = json.load(fh)
    print("loaded dictModel => ", dictModel)
except:
    print("generate dictModel => {}")

count = 0
for ne in lstEstimadors:
    for lr in lstLearnRate:
        dictModel[str(count)] = [ne, lr]
        # print(f"# {count + 1} mudando n_estimators= {ne} & learning_rate= {lr}")
        count += 1

for cc, npath in enumerate(lstpathfiles[:2]):
    df_bacia = {}
    print("Loading ==> " + npath)
    nbacia = npath.split("_")[-1].replace('.csv', '')
    dftable = pd.read_csv(npath)
    dftable = dftable.drop(['system:index','.geo'], axis=1)
    print("  columns = ", dftable.columns)
    print(f" == Know how many rois have in the table == \n ", 
                                dftable.year.value_counts())

    dftableYY = dftable[dftable['year'] == yyear]
    procFeatures_byYears.get_data(dftableYY, yyear)
    lstKeysBa = [kk for kk in dictModel.keys()]

    if nbacia not in lstKeysBa:       
        procFeatures_byYears.processingMultiplesModels()
        melhorModelo = procFeatures_byYears.betterPmtrosSet
        dictModel[nbacia] = {
            'better_pmtSet': melhorModelo,
            'n_estimators': dictModel[str(melhorModelo)][0],
            'learning_rate': dictModel[str(melhorModelo)][1]
        }
        # Convert and write JSON object to file
        with open("dictBetterModelpmtSet.json", "w") as outfile: 
            json.dump(dictModel, outfile)
    else:
        df_bacia = dictModel[nbacia]
        print("selecionou model feito ", df_bacia)
        procFeatures_byYears.betterPmtrosSet = df_bacia['better_pmtSet']
        
    # sys.exit()
    for nyear in lstYear:
        dftableYY = dftable[dftable['year'] == nyear]
        procFeatures_byYears.get_data(dftableYY, nyear)
        procFeatures_byYears.get_better_featuresSet(fixarNFeat, numMin, nbacia, nyear)
        

        
    
