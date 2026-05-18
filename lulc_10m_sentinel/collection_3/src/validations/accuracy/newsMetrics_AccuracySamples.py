#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformação
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import glob 

from tabulate import tabulate
import sys
import math
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.metrics import precision_score, recall_score
from sklearn.metrics import f1_score, jaccard_score
tqdm.pandas()


buildMetricsAcc = True
buildMetAggrements = True

listaNameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751',     
    '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752'
]
# get dir path of script 
npath = os.getcwd()
# get dir folder before to path scripts 
npath = str(Path(npath).parents[1])
print("path of CSVs Rois is \n ==>",  npath)

def set_all_sum_of_matrix_acc(matrix_acc):
	dimension = int(math.sqrt(matrix_acc.size))	
	matrix_a = np.zeros((dimension + 1, dimension + 1)).astype(np.int32)	
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
    print("size dataframe para confusion matrix", dfRefClass.shape)
    dfRefCC = dfRefClass.dropna(subset=['reference', 'classification'])
    print("   ", dfRefCC.shape)
    print("NaNs in X_new after imputation:", np.isnan(dfRefCC).sum())

    conf_matrix = confusion_matrix(
                        y_true= dfRefCC['reference'], 
                        y_pred= dfRefCC['classification'], 
                        labels= lstClassEst
                    )

    dimX, dimY = conf_matrix.shape
    quantid_arr = [0] * len(lstClassEst)
    allocat_arr = [0] * len(lstClassEst)
    exchange_arr = [0] * len(lstClassEst)
    shift_arr = [0] * len(lstClassEst)
    total = np.sum(conf_matrix)

    confMatrix = set_all_sum_of_matrix_acc(conf_matrix)    
    dfConfM =  pd.DataFrame(confMatrix, columns= lstClassEst + ["Total"], index= lstClassEst + ['Total'])        
               
    if showInfo:
        print(f" numero de colunas {dimX} | número de filas {dimY}")
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

def calculing_Aggrements_AccGlobal_ModelVers(dfacctmp, lst_regBacias):

    def calculing_Aggrements_AccGlobal(df_tmp, mbacia, typeFilter= 'Gap-fill', vers= 5, collections= 'Col10'):  

        def calcula_index_accuracy(dfYYs, myear):
            quantid, allocat, exchange, shift, confusMatrix = allocation_erros(dfYYs, False)            
            name = mbacia + "_" + typeFilter + "_" + str(myear) +  "_" + str(vers) + '.csv' 
            path_exportCM = os.path.join(npath, 'dados', 'conf_matrix', name)
            confusMatrix.to_csv(path_exportCM, index_label= 'classes')
            acc = accuracy_score(dfYY['reference'], dfYY['classification'])
            acc = round(acc * 100, 2)
            dicttmp["global_accuracy"] = [acc]

            # Calculing the value ended 
            quantidV = round(sum(quantid) / 2, 2)
            allocatV = (100 - acc) - quantidV
            exchangeV = round(sum(exchange) / 2, 2)
            shiftV = round(sum(shift) / 2, 2)
            dicttmp["quantity diss"] = [quantidV]
            dicttmp["alloc dis"] = [allocatV]
            dicttmp["exchange"] = [exchangeV]
            dicttmp["shift"] = [shiftV]
            dicttmp["year"] = [myear]
            dicttmp["version"] = [vers]
            dicttmp["filters_type"] = [typeFilter]
            dicttmp["Collections"] = [collections]
            dicttmp["Bacia"] = [mbacia]
            dfrow = pd.DataFrame.from_dict(dicttmp)
            return dfrow
        
        if collections == 'Col10':
            lastYear = 2023
        elif collections == 'collection90':
            lastYear = 2022
        elif collections == 'collection80':
            lastYear = 2021
        else:
            lastYear = 2020

        lstDfInd = []
        dicttmp = {}
        lstYY = list(range(1985, lastYear))
        lsDFF = []
        for nyear in lstYY:
            dfYY = df_tmp[[f'CLASS_{nyear}', f'classification_{nyear}']]
            print(dfYY.shape)
            dfYY.columns = ['reference', 'classification']
            lsDFF.append(dfYY)            
            print(f"=========== YEAR {nyear} =========== BACIA {mbacia}")       

            lstDfInd.append(calcula_index_accuracy(dfYY, nyear))
            # if mbacia != "Caatinga":
            #     sys.exit()

        # processando todos os anos 
        nyear = 'All'
        dfREfCC = pd.concat(lsDFF, axis= 0)
        lstDfInd.append(calcula_index_accuracy(dfREfCC, nyear))     

        return pd.concat(lstDfInd, axis= 0)


    lstDFagg = []
    lstfilters = list(dfacctmp.filters_type.unique())
    firstFilters = lstfilters[0]
    print(" >>>>>>>> ", firstFilters)
    if 'integration' == firstFilters:
        lstfilters = list(dfacctmp.Collections.unique())
        print("new list of filters", lstfilters)
    # sys.exit()
    for vversion in list(dfacctmp.version.unique()):
        for nfilter in lstfilters:
            print(f"tipo de filtro {nfilter} na versão {vversion} ")
            for reg in lst_regBacias:
                print('processing bacia ou região >> ', reg)
                if reg == 'Caatinga':
                    if 'integration' == firstFilters:
                        df_tmpr = dfacctmp[(dfacctmp['Collections'] == nfilter) & (dfacctmp['version'] == vversion)]
                    else:
                        df_tmpr = dfacctmp[(dfacctmp['filters_type'] == nfilter) & (dfacctmp['version'] == vversion)]
                else:
                    if 'integration' == firstFilters:
                        df_tmpr = dfacctmp[(dfacctmp['bacia'] == str(reg)) & (dfacctmp['Collections'] == nfilter)  & (dfacctmp['version'] == vversion)]
                    else:
                        df_tmpr = dfacctmp[(dfacctmp['bacia'] == str(reg)) & (dfacctmp['filters_type'] == nfilter)  & (dfacctmp['version'] == vversion)]
                print("bacias >> " , df_tmpr.bacia.unique())
                print(" tipo de filtro >> ", df_tmpr.filters_type.unique())
                colShow = ['CLASS_1985', 'classification_1985', 'bacia', 'filters_type', 'version' , 'Collections']  
                print(tabulate(df_tmpr[colShow].head(2), headers = 'keys', tablefmt = 'psql')) 
                # sys.exit() 
                if firstFilters == 'integration':             
                    dfAggtmp = calculing_Aggrements_AccGlobal(
                                    df_tmpr, reg, 
                                    typeFilter= firstFilters, 
                                    vers= vversion,
                                    collections= nfilter
                                )
                else:
                    dfAggtmp = calculing_Aggrements_AccGlobal(
                                    df_tmpr, reg, 
                                    typeFilter= nfilter, 
                                    vers= vversion,
                                    collections= 'Col10'
                                )
                print(tabulate(dfAggtmp.head(2), headers = 'keys', tablefmt = 'psql'))
                lstDFagg.append(dfAggtmp)
                # if reg != 'Caatinga':
                    # sys.exit()
    dfAggIndex =  pd.concat(lstDFagg, axis= 0)
    return dfAggIndex

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
        filtros = row['Filters']
        nbacia = row['Bacia']
        yyear = row['Years']
        colRef = "CLASS_" + str(yyear)
        colPre = "classification_" + str(yyear)

        
        if nbacia == 'Caatinga':
            df_tmp = tableAccYY[(tableAccYY['version'] == vers) & (
                            tableAccYY['filters_type'] == filtros)][[colRef, colPre]] 
        else:
            df_tmp = tableAccYY[(tableAccYY['version'] == vers) & (
                                tableAccYY['filters_type'] == filtros) & (
                                    tableAccYY['bacia'] == str(nbacia))][[colRef, colPre]]           

        df_tmp.columns = ['reference', 'classification']

        if showPrints:
            print("bacia {nbacia} | filtros {filtros} | version {vers} " )
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

def change_class_nameClass(row):
    dictRemapL3 =  {
        "FORMAÇÃO FLORESTAL": 3,
        "FORMAÇÃO SAVÂNICA": 4,        
        "MANGUE": 3,
        "RESTINGA HERBÁCEA": 3,
        "FLORESTA PLANTADA": 18,
        "FLORESTA INUNDÁVEL": 3,
        "CAMPO ALAGADO E ÁREA PANTANOSA": 12,
        "APICUM": 12,
        "FORMAÇÃO CAMPESTRE": 12,
        "AFLORAMENTO ROCHOSO": 29,
        "OUTRA FORMAÇÃO NÃO FLORESTAL":12,
        "PASTAGEM": 15,
        "CANA": 18,
        "LAVOURA TEMPORÁRIA": 18,
        "LAVOURA PERENE": 18,
        "MINERAÇÃO": 22,
        "PRAIA E DUNA": 22,
        "INFRAESTRUTURA URBANA": 22,
        "VEGETAÇÃO URBANA": 22,
        "OUTRA ÁREA NÃO VEGETADA": 22,
        "RIO, LAGO E OCEANO": 33,
        "AQUICULTURA": 33,
        "NÃO OBSERVADO": 27  
    }
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
        "OUTRA FORMAÇÃO NÃO FLORESTAL":12,
        "PASTAGEM": 21,
        "CANA": 21,
        "LAVOURA TEMPORÁRIA": 21,
        "LAVOURA PERENE": 21,
        "MINERAÇÃO": 22,
        "PRAIA E DUNA": 22,
        "INFRAESTRUTURA URBANA": 22,
        "VEGETAÇÃO URBANA": 22,
        "OUTRA ÁREA NÃO VEGETADA": 22,
        "RIO, LAGO E OCEANO": 33,
        "AQUICULTURA": 33,
        "NÃO OBSERVADO": 27  
    }
    
    for yyear in range(1985, 2023):
        nameCol = f"CLASS_{yyear}"
        row[nameCol] = dictRemapL2[row[nameCol]]
    return row

joinallTables = False
sobre_escrever = True
colectionFilters = False
if colectionFilters:
    base_path, input_path_CSVs = getPathCSV('acc/ptosAccCol10')
else:
    base_path, input_path_CSVs = getPathCSV('acc/ptosAccColBef')
print("path the base ", base_path)
print("path of CSVs from folder :  \n ==> ", input_path_CSVs)

lstColRef = ['CLASS_' + str(kk) for kk in range(1985, 2023)]
lstColPred = ['classification_' + str(kk) for kk in range(1985, 2023)]
lYears = [kk for kk in range(1985, 2023)]

# sys.exit()

mversion = ''
lstFilters = [ 
    'Gap-fill', 'TemporalJ3', 'TemporalAJ3', 'TemporalJ4', 'TemporalAJ4', 
    'TemporalJ5', 'TemporalAJ5', 'Spatial', 'Frequency'  
]
version_process = ['5'] 
# modelos += posclass
lst_df = []
if joinallTables:
    lst_paths = glob.glob(input_path_CSVs + '/*.csv')
    print(f' 📢 We load {len(lst_paths)} tables from folder  {input_path_CSVs.split("/")[-1]}')

    for cc, path in enumerate(lst_paths[:]): 
        # if cc == 0 or cc == len(lst_paths) - 1:
        # print(" loading 🕙 >> ", path.split("/")[-1])  
        nome_csv = path.split("/")[-1]    
        partes = nome_csv.split('_')    
        print(partes)
        if len(partes) > 5:
            filtro = partes[5] 
            colecao = partes[4] 
        else:
            filtro = partes[3]
            colecao = 'Col10'
        
        version = int(partes[-1][1:].replace('.csv', ''))

        df_CSV = pd.read_csv(path)       # , sep=',', encoding='iso-8859-1'         
        print(df_CSV.head())    
        # df_CSV = df_CSV.drop(['system:index', ".geo"], axis=1)

        print(f" 📢 loading 🕙 {nome_csv} size = <{df_CSV.shape}> | filtro << {filtro} >> | vers {version}")
        # preenchendo as colunas que faltam com informações no nome
        # removendo LAT LON PESO_AMOS bacia 
        # sys.exit()
        try:
            df_CSV = df_CSV[lstColRef + lstColPred + ['bacia']] 
        except:
            df_CSV = df_CSV[lstColRef + lstColPred[:-2] + ['bacia']]
        
        # if sobre_escrever:
        try:
            df_CSVA = df_CSV.progress_apply(change_class_nameClass, axis= 1)
            df_CSV = df_CSVA.copy()
        except:
            print(" As classes já estão convertidas ")

        df_CSV['filters_type'] = [filtro] * df_CSV.shape[0]         
        df_CSV['version'] = [version] * df_CSV.shape[0]
        df_CSV['Collections'] = [colecao] * df_CSV.shape[0]
        # add to list ofs Dataframes              , 'filters_type', 'versions'
        if sobre_escrever:
            # sobre escrever as matrices de entrada 
            df_CSV.to_csv(path)

        lst_df.append(df_CSV)
        print(f"para o modelo {nome_csv} we have {len(lst_df)}")

    showPrints = False
    dfacc = pd.concat(lst_df, axis= 0)
    print("size dataframe modifies ", dfacc.shape)
    if showPrints:
        print("colunas \n ", dfacc.columns)
    #
    print("list of versions ", dfacc['version'].unique())
    print("list of filters_type ", dfacc['filters_type'].unique())
    
    print("=================================================")
    # print(dfacc.head(10))
    colShow = ['CLASS_1985', 'classification_1985', 'bacia', 'filters_type', 'version' , 'Collections']  
    print(tabulate(dfacc[colShow].head(10), headers = 'keys', tablefmt = 'psql'))
    print("=================================================")

    lstClassRef = []
    lstClassPred = []
    classInic = [3,4, 9,10,12,15,18,21,22,27,29,33,50]
    classFin  = [3,4,12,12,12,21,21,21,22,27,22,33, 3]
    # for cc, colRef in enumerate(lstRef):
    dfacc[lstColRef] = dfacc[lstColRef].replace(classInic, classFin)  
    try:   
        dfacc[lstColPred] = dfacc[lstColPred].replace(classInic, classFin)
    except:
        dfacc[lstColPred[:-2]] = dfacc[lstColPred[:-2]].replace(classInic, classFin)

    # print("corregindo  os valores 0 e 27 ")
    print("remove class 27 from  dataset  size 93942")
    for colpred in lstColPred:
        dfacc = dfacc[dfacc[colpred] != 27]

    for colref in lstColRef:
        dfacc = dfacc[dfacc[colref] != 27]

    lstClassRef = [int(kk) for kk in dfacc[lstColRef].stack().drop_duplicates().tolist()]
    lstClassPred = [int(kk) for kk in dfacc[lstColPred].stack().drop_duplicates().tolist()]
    print(lstClassPred)
    lstClassRef.sort(reverse=False)
    lstClassPred.sort(reverse=False) 
    print(f" ⚠️ We have {lstClassRef} class from Refence Points {dfacc.shape}")
    print(f" ⚠️ We have {lstClassPred} class from Classifications Raster ")
    if colectionFilters: 
        path_save = os.path.join(base_path, 'dados','acc', 'occTab_corr_Caatinga_Collection10_v12.csv')   
    else:
        path_save = os.path.join(base_path, 'dados','acc', 'occTab_corr_Caatinga_Allfilter_version9.csv')  
    print('saving in >> ', path_save)
    dfacc.to_csv(path_save)
else:
    if colectionFilters: 
        path_input = os.path.join(base_path, 'dados','acc', 'occTab_corr_Caatinga_Collection10_v12.csv')   
    else:
        path_input = os.path.join(base_path, 'dados','acc', 'occTab_corr_Caatinga_Allfilter_version9.csv')   
    print('reading data from >> ', path_input)
    dfacc = pd.read_csv(path_input)
    print("=================================================")
    print(dfacc.head(10))
    print(dfacc.Collections.unique())
    colShow = ['CLASS_1985', 'classification_1985', 'bacia', 'filters_type', 'version' , 'Collections']  
    print(tabulate(dfacc[dfacc['filters_type'] == 'integration'][colShow].head(10), headers = 'keys', tablefmt = 'psql'))
    print("=================================================")
    dfacc['bacia'] = dfacc['bacia'].astype(str)
    print("size table ", dfacc.shape)
    print(dfacc.version.unique())
    print(dfacc.filters_type.unique())

    # sys.exit()

# sys.exit()
# Remap column values in inplace

version = 9
showPrints = True
# sys.exit()                    
if buildMetricsAcc: 
    # Make Dataframe by Year and by Basin
    # lstBacias = []
    # lstYear = []
    lstRegs = ['Caatinga'] + listaNameBacias                     


    # sys.exit()
    # .iloc[:1]
    # dfAccBa = dfAccYYBa.progress_apply(calculing_metrics_AccBacia, axis= 1)
    # dfAccBa = calculate_metrics_accuracy_modelsVers(dfacc, dfAccYYBa)
    # print("show the first row from table dfAccYYBa")
    # # print(dfAccBa.head())
    # print("the size table is ", dfAccBa.shape)

    # pathOutpout = base_path + '/dados/globalTables'
    # nameTablesGlob = "regMetricsAccs_All_Col10_v9.csv"   

    # print("====== SAVING GLOBAL ACCURACY BY YEARS =========== ")
    # dfAccBa.to_csv(os.path.join(pathOutpout, nameTablesGlob))
    # print(tabulate(dfAccYYBa.head(), headers = 'keys', tablefmt = 'psql'))
    # print("************************************************")
    # print(tabulate(dfAccYYBa.head(), headers = 'keys', tablefmt = 'psql'))

if buildMetAggrements:
    showPrints = True
    # Make Dataframe by Year and by Basin        
    # lstBacias = []
    # lstYear = []
    lstRegs = ['Caatinga'] + listaNameBacias

    # dfAggCalc = dfAgg.progress_apply(calculing_Aggrements_AccGlobal, axis= 1)
    print(list(dfacc.Collections.unique()))
    # sys.exit()
    # print(tabulate(dfacc[dfacc['bacia'] == '765'][colShow].head(10), headers = 'keys', tablefmt = 'psql'))
    dfAggCalc = calculing_Aggrements_AccGlobal_ModelVers(dfacc, lstRegs)
    # sys.exit()
    print("show the first row from table dfAggCalc")
    print(dfAggCalc.head())
    print("the size table is ", dfAggCalc.shape)
    
    # checked and Create the directory
    pathOutpout = base_path + '/dados/globalTables'
    # path = Path(pathOutpout)
    # path.mkdir(parents=True, exist_ok=True)   
    
    nameTablesGlob = "regAggrementsAcc_All_Col10_v9.csv"
    if colectionFilters:
        nameTablesGlob = "regAggrementsAcc_Collection10_v12.csv" # occTab_corr_Caatinga_Collection10_v12
    dfAggCalc.to_csv(os.path.join(pathOutpout, nameTablesGlob), index= False)
    # sys.exit()


    # else:
    #     print("  =================================================================")
    #     print(f"    the filtroes {filtro} don´t have all basin , show here {39 - len(lst_df)}")
    #     for dfBasin in lst_df:
    #         print(dfBasin['bacia'].iloc[0])