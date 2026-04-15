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
import math
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score, recall_score
# from sklearn.metrics import 
from sklearn.metrics import f1_score, jaccard_score
tqdm.pandas()


buildMetricsAcc = True
buildMetAggrements = True
modelos = ["GTB","RF"]
nameBacias = [
      '741', '7421','7422','744','745','746','751','752', '7492',
      '753', '754','755','756','757','758','759','7621','7622','763',
      '764','765','766','767','771','772','773', '7741','7742','775',
      '776','76111','76116','7612','7613','7614','7615', '777','778',
      '7616','7617','7618','7619'
]
# get dir path of script 
npath = os.getcwd()
# get dir folder before to path scripts 
npath = str(Path(npath).parents[1])
print("path of CSVs Rois is \n ==>",  npath)

def set_all_sum_of_matrix_acc(matrix_acc):

	dimension = int(math.sqrt(matrix_acc.size))	
	matrix_a = np.zeros((dimension + 1, dimension + 1)).astype(np.int16)	
	matrix_a[0:dimension, 0: dimension] = matrix_acc

	for ii in range(dimension):
		matrix_a[ii, dimension] = np.sum(matrix_a[ii, : dimension])
		matrix_a[dimension, ii] = np.sum(matrix_a[ :dimension, ii])
	matrix_a[dimension, dimension] = np.sum(matrix_a[0:dimension, 0:dimension])
	print(matrix_a)
	return matrix_a

def getPathCSV (nfolders):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[1])
    # folder of CSVs ROIs
    roisPathAcc = pathparent + '/dados/' + nfolders
    return pathparent, roisPathAcc

def allocation_erros (dfRefClass, showInfo):
    lstClassEst = [3,4,12,21,22,33]
    conf_matrix = confusion_matrix(
                        y_true= dfRefClass['reference'], 
                        y_pred= dfRefClass['classification'], 
                        labels= lstClassEst)
    dimX, dimY = conf_matrix.shape
    quantid_arr = [0] * len(lstClassEst)
    allocat_arr = [0] * len(lstClassEst)
    exchange_arr = [0] * len(lstClassEst)
    shift_arr = [0] * len(lstClassEst)
    total = np.sum(conf_matrix)

    confMatrix = set_all_sum_of_matrix_acc(conf_matrix)
    if showInfo:
        print(f" numero de colunas {dimX} | número de filas {dimY}")
        dfConfM =  pd.DataFrame(confMatrix, columns= lstClassEst + ["Total"], index= lstClassEst + ['Total'])        
        print(dfConfM)       

    
    # calculin errors by class
    for ii in range(dimX):
        # calculo do erro de quantidade
        dif_user_prod = abs(confMatrix[ii, dimX] - confMatrix[dimY, ii])
        calc = round((dif_user_prod/ total) * 100, 2)
        quantid_arr[ii] = calc

        # calculo do erro de Allocação 
        dif_min = 2 * min((confMatrix[ii, dimX] - confMatrix[ii, ii]), (confMatrix[dimX, ii] - confMatrix[ii, ii]))
        calc = round((dif_min/ total) * 100, 2)
        allocat_arr[ii] = calc

        # calculo dos erros de exchange
        suma = 0
        sum_dif = 0		
        for jj in range(dimX):
            if ii != jj:
                suma += min(confMatrix[ii, jj], confMatrix[jj, ii])
                sum_dif += abs(confMatrix[ii, jj] - confMatrix[jj, ii])

        calc = round(((suma * 2)/total) * 100, 2)
        exchange_arr[ii] = calc

        # calculo do erro de shift
        calc = round(((sum_dif - dif_user_prod)/total) * 100, 2)
        shift_arr[ii] = calc

    return quantid_arr, allocat_arr, exchange_arr, shift_arr, dfConfM



def user_prod_acc_err(mat_conf, dim):

	user_acc_arr = []
	prod_acc_arr = []
	user_err_arr = []
	prod_err_arr = []	

	suma_com = 0
	suma_omi = 0

	for ii in range(dim):
		# print("valor central ", mat_conf[ii, ii])
		# print("valor suma ",  mat_conf[ii, dim])
		calc = np.round_((mat_conf[ii, ii] / mat_conf[ii, dim]) * 100, decimals= 2)
		user_acc_arr.append(calc)
		user_err_arr.append(100 - calc)		
		
		calc = np.round_((mat_conf[ii, ii] / mat_conf[dim, ii]) * 100, decimals= 2)
		prod_acc_arr.append(calc)
		prod_err_arr.append(100 - calc)
		
		if ii < dim:
			# print(mat_conf[ii, ii + 1: dim])
			suma_com += np.sum(mat_conf[ii, ii + 1: dim]) 
			# print(suma_com)
			suma_omi += np.sum(mat_conf[ii + 1: dim, ii])

	# print("suma total ", mat_conf[dim, dim])
	# print("suma comisao ", suma_com)
	# print("suma omisao ", suma_omi)

	erro_com = np.round_((suma_com / mat_conf[dim, dim]) * 100, decimals= 2)
	erro_omi = np.round_((suma_omi / mat_conf[dim, dim]) * 100, decimals= 2)

	return user_acc_arr, prod_acc_arr, user_err_arr, prod_err_arr, erro_com, erro_omi

def calculing_Aggrements_AccGlobal_ModelVers(dfAggP, dfacctmp):

    def calculing_Aggrements_AccGlobal(row):  
        vers = row['Version']
        model = row['Models']
        nbacia = row['Bacia']
        yyear = row['Years']    
        colReferece = "CLASS_" + str(yyear)
        colPredicao = "classification_" + str(yyear)

        if nbacia == 'Caatinga':
            df_tmp = dfacctmp[(dfacctmp['version'] == vers) & (
                        dfacctmp['models'] == model)][[colReferece, colPredicao]]
        else:

            df_tmp = dfacctmp[(dfacctmp['version'] == vers) & (
                        dfacctmp['models'] == model) & (
                            dfacctmp['bacia'] == str(nbacia))][[colReferece, colPredicao]]           

        df_tmp.columns = ['reference', 'classification']
        registro = False
        if showPrints: 
            try:       
                print("dataframe filtrada \n ", df_tmp.head())
                print("número de classes ", df_tmp['classification'].unique())
                print(" size ",df_tmp.shape )
                registro = True
            except:
                registro = False    

        if df_tmp.shape[0] > 0:
            quantid, allocat, exchange, shift, confusMatrix = allocation_erros(df_tmp, showPrints)
            acc = accuracy_score(df_tmp['reference'], df_tmp['classification'])
            acc = round(acc * 100, 2)
            row["global_accuracy"] = acc
            # Calculing the value ended 
            quantidV = round(sum(quantid) / 2, 2)
            allocatV = (100 - acc) - quantidV
            exchangeV = round(sum(exchange) / 2, 2)
            shiftV = round(sum(shift) / 2, 2)
            row["quantity diss"] = quantidV
            row["alloc dis"] = allocatV
            row["exchange"] = exchangeV
            row["shift"] = shiftV
            name = npath + '/dados/conf_matrix/CM_' +  nbacia + "_" + model + "_" + str(yyear) +  "_" + str(vers) + '.csv' 
            confusMatrix.to_csv(name, index_label= 'classes')

        else:
            row["global_accuracy"] = 0
            row["quantity diss"] = 0
            row["alloc dis"] = 0
            row["exchange"] = 0
            row["shift"] = 0        
        return row
    
    dfAggP = dfAggP.progress_apply(calculing_Aggrements_AccGlobal, axis= 1)
    return dfAggP

def calculing_metricsAcc (dfTmp, showMatConf):    
    if showMatConf:
        conf_matrix = confusion_matrix(dfTmp['reference'], dfTmp['classification'])        
        print(conf_matrix)   
    
    precision = precision_score(dfTmp['reference'], dfTmp['classification'], average='macro')
    reCall = recall_score(dfTmp['reference'], dfTmp['classification'], average='macro')
    f1Score = f1_score(dfTmp['reference'], dfTmp['classification'], average='macro')
    acc = accuracy_score(dfTmp['reference'], dfTmp['classification'])
    accbal = balanced_accuracy_score(dfTmp['reference'], dfTmp['classification'])
    jaccard = jaccard_score(dfTmp['reference'], dfTmp['classification'], average='macro')

    if showMatConf:
        print("  uniques values references ", dfTmp['reference'].unique())
        print("  uniques values predictions ", dfTmp['classification'].unique())
        print("  Acuracia ", acc)
        print("  Acuracia balance", accbal)
        print("  precision ", precision)
        print("  reCall ", reCall)
        print("  f1 Score ", f1Score)
        print("  Jaccard ", jaccard)

    return acc, accbal, precision, reCall, f1Score, jaccard

                
def calculate_metrics_accuracy_modelsVers(tableAccYY, tableIndexCalc):
    
    def calculing_metrics_AccBacia(row):  
        vers = row['Version']
        model = row['Models']
        nbacia = row['Bacia']
        yyear = row['Years']
        colRef = "CLASS_" + str(yyear)
        colPre = "classification_" + str(yyear)

        
        if nbacia == 'Caatinga':
            df_tmp = tableAccYY[(tableAccYY['version'] == vers) & (
                            tableAccYY['models'] == model)][[colRef, colPre]] 
        else:
            df_tmp = tableAccYY[(tableAccYY['version'] == vers) & (
                                tableAccYY['models'] == model) & (
                                    tableAccYY['bacia'] == str(nbacia))][[colRef, colPre]]           

        df_tmp.columns = ['reference', 'classification']

        if showPrints:
            print("bacia {nbacia} | model {model} | version {vers} " )
            print("df_tmp  ", df_tmp.shape)
            print(df_tmp.head(2))
            

        if showPrints:        
            print("dataframe filtrada ", df_tmp.head())
        
        Acc, AccBal, precis, recall, f1score, jaccardS = calculing_metricsAcc (df_tmp, True)
        row["Accuracy"] = Acc
        row["Accuracy_Bal"] = AccBal
        row["Precision"] = precis
        row["ReCall"] = recall
        row["F1-Score"] = f1score
        row["Jaccard"] = jaccardS
        # sys.exit()
        return row
    tableIndexCalc = tableIndexCalc.progress_apply(calculing_metrics_AccBacia, axis= 1)
    return tableIndexCalc

base_path, input_path_CSVs = getPathCSV('acc/ptosAccCol9')
print("path the base ", base_path)
print("path of CSVs from folder :  \n ==> ", input_path_CSVs)

lstColRef = ['CLASS_' + str(kk) for kk in range(1985, 2023)]
lstColPred = ['classification_' + str(kk) for kk in range(1985, 2023)]
lYears = [kk for kk in range(1985, 2023)]

lst_paths = glob.glob(input_path_CSVs + '/*.csv')
print(f' 📢 We load {len(lst_paths)} tables from folder  {input_path_CSVs.split("/")[-1]}')
classificador = "GTB"
mversion = ''
modelos = ['RF','GTB'] #  
# 'Gap-fillV2','SpatialV2St1', 'FrequencyV2nat', 'FrequencyV2natUso','SpatialV2St3','TemporalV2J3'
#   'TemporalV3J3','TemporalV3J4','TemporalV3J5','SpatialV3','FrequencyV3', "Estavel" 
posclass = ['toExport']#  'TemporalV3J4','TemporalV3J5','toExport', 'FrequencyV3St1', 'SpatialV3St1', 
# 'TemporalV3J3','TemporalV3J4','TemporalV3J5'  , 'FrequencyV3St2'['SpatialV2'] # , 'Gap-fill', 'Spatial', 'Temporal', 'Frequency'
version_process = ['31'] # '5','9','10','11', '12', '15', '16', '17',  '25','40','41'
# modelos += posclass
for nmodel in posclass[:]:
    for vers in version_process[:]:
        lst_df = []
        for cc, path in enumerate(lst_paths[:]): 
            # if cc == 0 or cc == len(lst_paths) - 1:
            # print(" loading 🕙 >> ", path.split("/")[-1])      
            partes = path.split("/")[-1].split('_')
            # print("numero de partes ", len(partes))
            version = partes[-2]
            posClass = None
            bacia = partes[3]
            if "GTB_" + vers in path or "RF_" + vers in path:
                classificador = partes[4]
            else:
                classificador = partes[5] # posClass
                # bacia = partes[-4]
            if int(version) == 30:
                print(f" {len(partes)} | {bacia} classificador {nmodel} <> {classificador}| and {version} => {vers} >> {vers == version}")
            if str(nmodel) in str(classificador) and str(vers) == str(version): 
                print("rodando ")
                namecol = path.split("/")[-1]    
                df_CSV = pd.read_csv(path, sep=',', encoding='iso-8859-1')                
                df_CSV = df_CSV.drop(['system:index', ".geo"], axis=1)
                # if cc == 0 or cc == len(lst_paths) - 1:
                print(f" 📢 loading 🕙 {namecol} size = <{df_CSV.shape}> | model << {classificador} >> | bacia << {bacia} >> | vers {version}")
                # preenchendo as colunas que faltam com informações no nome
                # removendo LAT LON PESO_AMOS bacia 
                df_CSV = df_CSV[lstColRef + lstColPred]
                df_CSV['bacia'] = [str(bacia)] * df_CSV.shape[0]            
                df_CSV['version'] = [version] * df_CSV.shape[0]
                df_CSV['models'] = [classificador] * df_CSV.shape[0]
                # add to list ofs Dataframes             
                lst_df.append(df_CSV)
        print(f"para o modelo {nmodel} we have {len(lst_df)}")
        
        # if cc > 10:
        #     break
        if len(lst_df) >= 30:
            showPrints = False
            dfacc = pd.concat(lst_df, axis= 0)
            print("size dataframe modifies ", dfacc.shape)
            if showPrints:
                print("colunas \n ", dfacc.columns)
            # lstVers = [kk for kk in dfacc['version'].unique()]
            print("list of versions ", dfacc['version'].unique())
            print("list of versions ", dfacc['models'].unique())
            
            print("=================================================")
            print(dfacc.head(10))
            print("=================================================")
            # sys.exit()
            # classInic = [0 ,3,4, 9,10,12,15,18,21,22,27,29,33,50]
            # classFin  = [27,3,4,12,12,12,15,18,15,22,27,22,33, 3]
            # if nmodel in posclass:
            classInic = [3,4, 9,10,12,15,18,21,22,27,29,33,50]
            classFin  = [3,4,12,12,12,21,21,21,22,27,22,33, 3]
            # concat_df['class'] = concat_df['class'].replace([0,1,2,3,4],[0,1,0,0,1])
            # Remap column values in inplace
            lstClassRef = []
            lstClassPred = []
            # for cc, colRef in enumerate(lstRef):
            dfacc[lstColRef] = dfacc[lstColRef].replace(classInic, classFin) 
            dfacc[lstColPred] = dfacc[lstColPred].replace(classInic, classFin)

            # print("corregindo  os valores 0 e 27 ")
            print("remove class 27 from  dataset ")
            for colpred in lstColPred:
                dfacc = dfacc[dfacc[colpred] != 27]

            for colref in lstColRef:
                dfacc = dfacc[dfacc[colref] != 27]

            lstClassRef = [kk for kk in dfacc[lstColRef].stack().drop_duplicates().tolist()]
            lstClassPred = [kk for kk in dfacc[lstColPred].stack().drop_duplicates().tolist()]

            lstClassRef.sort(reverse=False)
            lstClassPred.sort(reverse=False) 
            print(f" ⚠️ We have {lstClassRef} class from Refence Points {dfacc.shape}")
            print(f" ⚠️ We have {lstClassPred} class from Classifications Raster ")

            showPrints = True
            # sys.exit()                    
            if buildMetricsAcc: 
                # Make Dataframe by Year and by Basin
                lstBacias = []
                lstYear = []
                lstRegs = ['Caatinga'] + nameBacias                     
                lstVersion = [vers] * len(lstRegs) * len(lYears)                    
                for nbacia in lstRegs:
                    lstBacias += [nbacia] * len(lYears)
                    lstYear += lYears

                print("Adding metrics Acc in the dictionary by Year")
                dictAcc = {
                    "Version": lstVersion,
                    "Models": [nmodel] * len(lstVersion),
                    "Bacia" : lstBacias,    
                    "Years": lstYear   
                }
                dfAccYYBa = pd.DataFrame.from_dict(dictAcc)
                print("size data frame by bacia", dfAccYYBa.shape)
                print("modelos ", dfAccYYBa["Models"].unique())
                print("versions ", dfAccYYBa["Version"].unique())
                print(dfAccYYBa.head())
                print(dfAccYYBa.tail())
                print("==========================================================")
                print("----------------------------------------------------------")
                print("")

                # sys.exit()
                # .iloc[:1]
                # dfAccBa = dfAccYYBa.progress_apply(calculing_metrics_AccBacia, axis= 1)
                dfAccBa = calculate_metrics_accuracy_modelsVers(dfacc, dfAccYYBa)
                print("show the first row from table dfAccYYBa")
                # print(dfAccBa.head())
                print("the size table is ", dfAccBa.shape)

                pathOutpout = base_path + '/dados/globalTables/'
                nameTablesGlob = f"regMetricsAccs_{nmodel}_vers_{vers}_Col9.csv"   

                print("====== SAVING GLOBAL ACCURACY BY YEARS =========== ")
                dfAccBa.to_csv(pathOutpout + nameTablesGlob)
                print(dfAccBa.head(10))
                print("************************************************")
                print(dfAccBa.tail(10))

            if buildMetAggrements:
                showPrints = True
                # Make Dataframe by Year and by Basin        
                lstBacias = []
                lstYear = []
                lstRegs = ['Caatinga'] + nameBacias
                
                lstVersion = [vers] * len(lstRegs) * len(lYears)    
                for nbacia in lstRegs:
                    lstBacias += [nbacia] * len(lYears)
                    lstYear += lYears

                print("Adding metrics Acc in the dictionary by Year")
                dictAcc = {
                    "Version": lstVersion,
                    "Models": [nmodel] * len(lstVersion),
                    "Bacia" : lstBacias,    
                    "Years": lstYear    
                }
                dfAgg = pd.DataFrame.from_dict(dictAcc)
                print("size data frame by bacia", dfAgg.shape)
                print("modelos ", dfAgg["Models"].unique())
                print(dfAgg.head())
                print(dfAgg.tail())
                print("==========================================================")
                print("----------------------------------------------------------")
                print("")
                # .iloc[:1]
                # dfAggCalc = dfAgg.progress_apply(calculing_Aggrements_AccGlobal, axis= 1)
                dfAggCalc = calculing_Aggrements_AccGlobal_ModelVers(dfAgg, dfacc)
                print("show the first row from table dfAggCalc")
                print(dfAggCalc.head())
                print("the size table is ", dfAggCalc.shape)
                
                # checked and Create the directory
                pathOutpout = base_path + '/dados/globalTables/'
                # path = Path(pathOutpout)
                # path.mkdir(parents=True, exist_ok=True)    
                nameTablesGlob = f"regAggrementsAcc_{nmodel}_vers_{vers}_Col9.csv"
                dfAggCalc.to_csv(pathOutpout + nameTablesGlob, index= False)
                # sys.exit()


    else:
        print("  =================================================================")
        print(f"    the model {nmodel} don´t have all basin , show here {39 - len(lst_df)}")
        for dfBasin in lst_df:
            print(dfBasin['bacia'].iloc[0])