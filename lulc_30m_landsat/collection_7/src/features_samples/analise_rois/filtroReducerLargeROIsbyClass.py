#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
# cluster [WEKA CobWb ] == > https://link.springer.com/content/pdf/10.1007/BF00114265.pdf
'''

import ee 
import gee
import json
import csv
import sys
import random 
import arqParametros as arqParam
import collections
collections.Callable = collections.abc.Callable
try:
  ee.Initialize()
  print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
  print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
sys.setrecursionlimit(1000000000)



params = {
    'assetBacia': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv9'},
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv13/',
    'pmtClustLVQ': { 'numClusters': 8, 'learningRate': 0.000005, 'epochs': 800},
    'splitRois': 0.6,
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta' : {
        # '0': 'caatinga01',
        '0': 'caatinga02',
        '8': 'caatinga03',
        '16': 'caatinga04',
        '25': 'caatinga05',        
        '36': 'solkan1201',
        # '15': 'diegoGmail',
        # '0': 'rodrigo',
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


list_anos = [k for k in range(1985,2022)]
# print('lista de anos', list_anos)
lsNamesBacias = arqParam.listaNameBacias
lsBacias = ee.FeatureCollection(params['assetBacia'])

# bandNames = [
#     'median_gcvi','median_gcvi_dry','median_gcvi_wet','median_gvs','median_gvs_dry','median_gvs_wet',
#     'median_hallcover','median_ndfi','median_ndfi_dry','median_ndfi_wet', 'median_ndvi','median_ndvi_dry',
#     'median_ndvi_wet','median_nir_dry','median_nir_wet','median_savi_dry','median_savi_wet','median_swir1',
#     'median_swir2','median_swir1_dry','median_swir1_wet','median_swir2_dry', 'median_swir2_wet','median_nir',
#     'median_pri','median_red','median_savi','median_evi2','min_nir','min_red','min_swir1','min_swir2', 
#     'median_fns_dry','median_ndwi_dry','median_evi2_dry','median_sefi_dry','median_ndwi','median_red_dry',
#     'median_wefi_wet','median_ndwi_wet'      
# ]
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


def filtered_class_ROIs(feat_ROIs): 
    print("#### ======== TIRANDO OS 40 % =======#######")      
    sizefeatROI = feat_ROIs.size()
    thresholdCut = ee.Number(1000).divide(ee.Number(sizefeatROI))
    lstprop = feat_ROIs.first().propertyNames()         
    feat_ROIs = feat_ROIs.randomColumn('random')    
    trainingROI = feat_ROIs.filter(ee.Filter.lt('random', thresholdCut))  
    return trainingROI.select(lstprop)

a_file = open("registroYear_FeatsImp.json", "r")
dictFeatureImp = json.load(a_file)

# lsNamesBacias = [
#         '741','752','753',
#         '754','755','756','757','758','759','7621','7622', '763','764',
#         '765','766', '767','771','772','773', '7741','7742','775','776',
#         '777','778','76111','76116','7612','7613','7614','7615','7616',
#         '7617','7618','7619'
# ]
cont = 0
for nbacias in lsNamesBacias[:]:

    texto = " procesando a bacia " + nbacias
    print(texto)
    # arqRelatorio.write(texto + '\n')
    colecaoPontos = ee.FeatureCollection([])
    ROIsTemp = GetPolygonsfromFolder(nbacias)       

    for _ano in list_anos:

        texto = "processing year = " + str(_ano)
        print(texto)
        # arqRelatorio.write(texto + '\n')
        if _ano < 2020:
            bandas_imports = dictFeatureImp[str(_ano)]

        ROIsTempYear = ROIsTemp.filter(ee.Filter.eq('year', _ano))   
        ROIsTempYear = ROIsTempYear.filter(ee.Filter.notNull(bandas_imports))
        
        # texto = "iterando por classes"
        # print(texto) 
        # arqRelatorio.write(texto + '\n')
        lstClassnotF = [22,29,33]
        for cc in [3,4,12,15,18]:                
            itemClassRoi = ROIsTempYear.filter(ee.Filter.eq("class", int(cc)))
            sizeROIsclass = itemClassRoi.size()#.getInfo()
            print("clase ", cc, " tem valores de = ? ") # , sizeROIsclass
            
            colecaoPontos = ee.Algorithms.If(
                                    ee.Number(sizeROIsclass).gt(0),
                                    ee.Algorithms.If(
                                            ee.Number(sizeROIsclass).gte(1000),
                                            ee.FeatureCollection(colecaoPontos).merge(filtered_class_ROIs(itemClassRoi)), # com filtro  
                                            ee.FeatureCollection(colecaoPontos).merge(itemClassRoi) #  sem filtro 
                                    ),
                                    ee.FeatureCollection(colecaoPontos)
                                )

        # print('agora tem ', ee.FeatureCollection(colecaoPontos).size().getInfo()) 
        # sys.exit()
        ROIIntacto =  ROIsTempYear.filter(ee.Filter.inList('class', lstClassnotF))
        colecaoPontos = ee.FeatureCollection(colecaoPontos).merge(ROIIntacto)

    # sys.exit()
    texto = "Salvando a bacia {}".format(nbacias)
    print(texto)
    # arqRelatorio.write(texto + '\n')
    # arqFeitos.write(nbacias + '\n')
    saveToAsset(colecaoPontos, str(nbacias) + '_r1k')
    cont = gerenciador(cont)

# arqFeitos.close()
# arqRelatorio.close()
