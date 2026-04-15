#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
# cluster [WEKA CobWb ] == > https://link.springer.com/content/pdf/10.1007/BF00114265.pdf
'''
import os
import ee 
import gee
import json
import csv
import sys
import random 
# import arqParametros as arqParam

try:
  ee.Initialize()
  print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
  print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


params = {
    'assetBacia': 'users/diegocosta/baciasRecticadaCaatinga',
    'assetbase': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/',
    'assetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv4N4/',
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster/',
    'pmtClustLVQ': { 'numClusters': int(8), 'learningRate': float(0.001), 'epochs': int(1200)},
    'pmtClustXMeans': {
        'minClusters': int(7), 'maxClusters': 9, 
        'maxIterations': 20, 'useKD': True, 
        'distanceFunction': 'Manhattan', 'seed': 50
    },
    'splitRois': float(0.8),
    'numeroTask': 6,
    'numeroLimit': 70,
    'conta' : {
        '0': 'caatinga01',
        '10': 'caatinga02',
        '20': 'caatinga03',
        '30': 'caatinga04',
        '40': 'caatinga05',        
        '50': 'solkan1201',
        '60': 'diegoGmail',
        # '30': 'rodrigo',
        # '34': 'Rafael'        
    },
    'pmtRF': {
        'numberOfTrees': 60, 
        'variablesPerSplit': 6,
        'minLeafPopulation': 3,
        'maxNodes': 10,
        'seed': 0
        }
}

lst_class = [3,4,12,15,18,22,29,33]
list_anos = [k for k in range(1985,2023)]
# print('lista de anos', list_anos)
# lsNamesBacias = arqParam.listaNameBacias

lsNamesBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]
lsBacias = ee.FeatureCollection(params['assetBacia'])
# region bandsBefores
# bandNames = [
#     'afvi_median', 'afvi_median_dry', 'afvi_median_wet', 'avi_median', 'avi_median_dry', 'avi_median_wet', 
#     'awei_median', 'awei_median_dry', 'awei_median_wet', 'blue_median', 'blue_median_dry', 'blue_median_wet',
#     'blue_min', 'blue_stdDev', 'brba_median', 'brba_median_dry', 'brba_median_wet', 'brightness_median', 
#     'brightness_median_dry', 'brightness_median_wet', 'bsi_median', 'bsi_median_dry', 'bsi_median_wet', 
#     'cai_median', 'cai_median_dry', 'cai_stdDev', 'class', 'cvi_median', 'cvi_median_dry', 'cvi_median_wet', 
#     'dswi5_median', 'dswi5_median_dry', 'dswi5_median_wet', 'evi2_amp', 'evi2_median', 'evi2_median_dry', 
#     'evi2_median_wet', 'evi2_stdDev', 'gcvi_median', 'gcvi_median_1', 'gcvi_median_dry', 'gcvi_median_dry_1', 
#     'gcvi_median_wet', 'gcvi_median_wet_1', 'gcvi_stdDev', 'gemi_median', 'gemi_median_dry', 'gemi_median_wet', 
#     'gli_median', 'gli_median_dry', 'gli_median_wet', 'green_median', 'green_median_dry', 'green_median_texture', 
#     'green_median_wet', 'green_min', 'green_stdDev', 'iia_median', 'iia_median_dry', 'iia_median_wet', 'lswi_median', 
#     'lswi_median_dry', 'lswi_median_wet', 'mbi_median', 'mbi_median_dry', 'mbi_median_wet', 'ndvi_amp', 'ndvi_median', 
#     'ndvi_median_dry', 'ndvi_median_wet', 'ndvi_stdDev', 'ndwi_amp', 'ndwi_median', 'ndwi_median_1', 'ndwi_median_dry', 
#     'ndwi_median_dry_1', 'ndwi_median_wet', 'ndwi_median_wet_1', 'ndwi_stdDev', 'nir_contrast_median', 'nir_contrast_median_dry', 
#     'nir_contrast_median_wet', 'nir_median', 'nir_median_dry', 'nir_median_wet', 'nir_min', 'nir_stdDev', 'osavi_median', 
#     'osavi_median_dry', 'osavi_median_wet', 'pri_median', 'pri_median_dry', 'pri_median_wet', 'ratio_median', 'ratio_median_dry', 
#     'ratio_median_wet', 'red_contrast_median', 'red_contrast_median_dry', 'red_contrast_median_wet', 'red_median', 'red_median_dry', 
#     'red_median_wet', 'red_min', 'red_stdDev', 'ri_median', 'ri_median_dry', 'ri_median_wet', 'rvi_median', 'rvi_median_dry', 
#     'rvi_median_wet', 'savi_median', 'savi_median_dry', 'savi_median_wet', 'savi_stdDev', 'shape_median', 'shape_median_dry', 
#     'shape_median_wet', 'slope', 'swir1_median', 'swir1_median_dry', 'swir1_median_wet', 'swir1_min', 'swir1_stdDev', 'swir2_median', 
#     'swir2_median_dry', 'swir2_median_wet', 'swir2_min', 'swir2_stdDev', 'ui_median', 'ui_median_dry', 'ui_median_wet', 'wetness_median', 
#     'wetness_median_dry', 'wetness_median_wet'    
# ]
#endregion
bandNames = ["swir1_stdDev_1","nir_stdDev_1","green_stdDev_1","ratio_median_dry","gli_median_wet","dswi5_median_dry",
"ri_median","osavi_median","swir2_min","shape_median","mbi_median_dry","wetness_median_dry","green_median_texture_1",
"iia_median_wet","slopeA_1","brba_median_dry","nir_median","lswi_median_wet","red_min","rvi_median","green_min",
"gcvi_median_dry","shape_median_dry","cvi_median_dry","blue_median_dry","mbi_median","nir_median_dry_contrast",
"swir2_median_wet","ui_median_wet","red_median_wet","avi_median","nir_stdDev","swir1_stdDev","red_median_dry",
"gemi_median","osavi_median_dry","blue_median_dry_1","swir2_median_dry_1","brba_median","ratio_median",
"gli_median_dry","blue_min_1","wetness_median","green_median_wet","blue_median_wet_1","brightness_median_wet",
"blue_min","blue_median","red_median_contrast","swir1_min_1","evi_median","blue_stdDev_1","lswi_median_dry",
"blue_median_wet","cvi_median","red_stdDev_1","shape_median_wet","red_median_dry_1","swir2_median_wet_1",
"dswi5_median_wet","red_median_wet_1","afvi_median","ndwi_median","avi_median_wet","gli_median","evi_median_wet",
"nir_median_dry","gvmi_median","cvi_median_wet","swir2_min_1","iia_median","ndwi_median_dry","green_min_1",
"ri_median_dry","osavi_median_wet","green_median_dry","ui_median_dry","red_stdDev","nir_median_wet_1",
"swir1_median_dry_1","red_median_1","nir_median_dry_1","swir1_median_wet","blue_stdDev","bsi_median",
"slopeA","swir1_median","swir2_median","gvmi_median_dry","red_median","gemi_median_wet","lswi_median",
"brightness_median_dry","awei_median_wet","nir_min","afvi_median_wet","nir_median_wet","evi_median_dry",
"swir2_median_1","ndwi_median_wet","ratio_median_wet","swir2_stdDev","gcvi_median","ui_median","rvi_median_wet",
"green_median_wet_1","ri_median_wet","nir_min_1","rvi_median_1","swir1_median_dry","blue_median_1","green_median_1",
"avi_median_dry","gvmi_median_wet","wetness_median_wet","swir1_median_1","dswi5_median","swir2_stdDev_1",
"awei_median","red_min_1","mbi_median_wet","brba_median_wet","green_stdDev","green_median_texture","swir1_min",
"awei_median_dry","swir1_median_wet_1","gemi_median_dry","nir_median_1","red_median_dry_contrast","bsi_median_1",
"bsi_median_2","nir_median_contrast","green_median_dry_1","afvi_median_dry","gcvi_median_wet","iia_median_dry",
"brightness_median","green_median","swir2_median_dry"]
#=====================================#
# gerenciador de contas para controlar# 
# processos task no gee               #
#=====================================#
def gerenciador(cont):    

    numberofChange = [kk for kk in params['conta'].keys()]

    if str(cont) in numberofChange:
        
        gee.switch_user(params['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= params['numeroTask'], return_list= True)        
    
    elif cont > params['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

#salva ftcol para um assetindexIni
def saveToAsset(collection, name):    
    
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': params['outAsset'] + name           
    }
    
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()    
    print("exportando ROIs da bacia $s ...!", name)

def GetPolygonsfromFolder(NameBacias):
    
    getlistPtos = ee.data.getList(params['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])
    
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        # print(path_) 
        
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')

        if newName[0] == NameBacias:

            print(path_)

            FeatTemp = ee.FeatureCollection(path_)
    
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    ColectionPtos = ee.FeatureCollection(ColectionPtos)
        
    return  ColectionPtos

def selectClassClusterAgrupado (dictFeat):
    lstPoints = [kk for kk in dictFeat.values()]
    lstPoints.sort(reverse=True)
    print('lst de points ', lstPoints)
    lst_Keys = []
    count = 0
    if len(lstPoints)> 2:
        for val in lstPoints:
            if val > 150:
                count += 1
        count = count - 1
    else:
        count = 1
    print(" counts ", count)
    for kk, vv in dictFeat.items():
        if vv in lstPoints[: count]:
            lst_Keys.append(int(kk))  

    print("Os cluster com maiores valores são <- {} -> ".format(lst_Keys))
    return lst_Keys


def check_dir(file_name):
    if not os.path.exists(file_name):
        arq = open(file_name, 'w+')
        arq.close()

pathReg = "registros/lsBaciasROIsfeitasBalanCluster3.txt"
pathFolder = os.getcwd()
path_MGRS = os.path.join(pathFolder, pathReg)
baciasFeitas = []
check_dir(path_MGRS)
arqFeitos = open(pathReg, 'r')

baciasFeitas = [] 
for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

nameAssetFolder = params['assetROIs'].replace(params['assetbase'],'')[:-1]
pathArqFeitos = "registros/lsBaciasROIsfeitasBalanCluster_"  + nameAssetFolder + '.txt'
check_dir(pathArqFeitos)
arqFeitos = open(pathArqFeitos, 'a+')
pathCluster = "registros/RelatorioCluster_Outlier_" + nameAssetFolder + '.txt'
arqRelatorio = open(pathCluster, 'w+')
pathArqFaltan = "registros/bacias_years_comFalta_rois_" + nameAssetFolder + '.txt'
check_dir(pathArqFeitos)
arqFaltante = open(pathArqFaltan, 'a+')

lst_faltantes = open("registros/lista_ROIsv6N2cluster_faltantes.txt", 'r')
lstROIsFaltam = []
for linha in lst_faltantes:
    print(linha[:-1])
    lstROIsFaltam.append(linha[:-1])

a_file = open("registroBacia_Year_FeatsSel.json", "r")
dictFeatureImp = json.load(a_file)

cont = 20
for nbacias in lsNamesBacias[:]:
    
    texto = " procesando a bacia " + nbacias
    print(texto)

    for yyear in list_anos[:]:

        # if ((nbacias == '759') and (yyear == 2010)) or (
        #     (nbacias == '765') and (yyear == 1997)) or (
        #     (nbacias == '766') and (yyear == 2007)) or (
        #     (nbacias == '7619') and (yyear == 1999)) or (
        #     (nbacias == '7619') and (yyear == 2016)) or (
        #     (nbacias == '7422') and (yyear == 2004)):
            # 741_1985_c1
        nameFeat = nbacias + "_" + str(yyear) + "_c1"
        if nameFeat in lstROIsFaltam:
            print("Loading file from asset ", nameFeat)
            try:
                ROIsTempA = ee.FeatureCollection(params['assetROIs'] + nameFeat)               
                arqRelatorio.write(nameFeat + '\n')
                print("size FeatCol loading ", ROIsTempA.size().getInfo())                

                ROIsTempA = ROIsTempA.randomColumn('random')    
                trainingROI = ROIsTempA.filter(ee.Filter.lt('random', params['splitRois']))

                histo = trainingROI.aggregate_histogram('class').getInfo()
                texto = " Histograma para treinar {} ".format(histo)
                print(texto) 
                arqRelatorio.write(texto + '\n')
                classROIs = [k for k in histo.keys()] 
                print(f"contamos com {len(classROIs)} classes")
                
                # params['pmtClustLVQ']['numClusters'] = len(classROIs)
                bandas_lst = dictFeatureImp[nbacias][str(yyear)][:70]
                bandas_imports = [kk for kk in bandas_lst if kk in bandNames]
                # print("bandas carregadas ", bandas_imports , " \n size ", len(bandas_imports))
                # 
                XMeans = ee.Clusterer.wekaXMeans(**params['pmtClustXMeans']).train(
                                            trainingROI.select(bandas_imports), bandas_imports)
                # CLVQ = ee.Clusterer.wekaLVQ(**params['pmtClustLVQ']).train(trainingROI.select(bandas_imports), bandas_imports)
                # newROIsTempA = ROIsTempA.cluster(CLVQ, 'newclass')
                newROIsTempA = ROIsTempA.cluster(XMeans, 'newclass')

                texto = "iterando por classes"
                print(texto) 
                arqRelatorio.write(texto + '\n')
                colecaoPontos = ee.FeatureCollection([])
                for cc in classROIs:                                
                    itemClassRoi = newROIsTempA.filter(ee.Filter.eq("class", int(cc)))
                    histoTemp = itemClassRoi.aggregate_histogram('newclass').getInfo()

                    texto = "histograma cluster da classe " + str(cc)
                    print(texto)
                    arqRelatorio.write(texto + '\n')
                    texto = "{}".format(histoTemp)
                    print(texto)
                    arqRelatorio.write(texto + '\n')

                    selCCs = selectClassClusterAgrupado(histoTemp)

                    trainingROI = None
                    trainingROI = itemClassRoi.filter(ee.Filter.inList('newclass', selCCs))         
                    
                    texto = "classe {} com {} ptos".format(cc, trainingROI.size().getInfo())
                    print(texto)
                    arqRelatorio.write(texto + '\n')

                    colecaoPontos = colecaoPontos.merge(trainingROI)             

                texto = "Salvando a bacia {}".format(nbacias)
                print(texto)
                arqRelatorio.write(texto + '\n')
                arqFeitos.write(nameFeat + '\n')
                saveToAsset(colecaoPontos, str(nameFeat))
                cont = gerenciador(cont)

            except:
                print("not found file")
                arqFaltante.write(nameFeat + '\n')

arqFeitos.close()
arqRelatorio.close()
