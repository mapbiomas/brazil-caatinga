#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import gee
import json
import csv
import copy
import sys
import math
import arqParametros as arqParams 
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
# sys.setrecursionlimit(1000000000)



#============================================================

param = {
    'bioma': "CAATINGA", #nome do bioma setado nos metadados
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classificationV8/',
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv5'},    
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21],
    'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    'janela': 3,
    'anoInicial': 1985,
    'anoFinal': 2021,
    'sufix': "_01",    
    'lsBandasMap': [],
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',        
        '35': 'solkan1201',
        # '36': 'rodrigo',
        # '35': 'diegoGmail',    
    },
    'pmtRF': {
        'numberOfTrees': 265, 
        'variablesPerSplit': 25,
        'minLeafPopulation': 1,
        'bagFraction': 0.8,
        'seed': 0
    },
    'pmtGTB': {
        'numberOfTrees': 96, 
        'shrinkage': 0.01, 
        'samplingRate': 0.8, 
        'loss': 'LeastAbsoluteDeviation', 
        'seed': 0
    },
    'pmtSVM' : {
        'decisionProcedure' : 'Margin', 
        'kernelType' : 'RBF', 
        'shrinking' : True, 
        'gamma' : 0.001
    } 

}
# print(param.keys())
print("vai exportar em ", param['assetOut'])
# print(param['conta'].keys())

#============================================================
#========================METODOS=============================
#============================================================

def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

#exporta a imagem classificada para o asset
def processoExportar(mapaRF, regionB, nameB):
    nomeDesc = 'RF_BACIA_'+ str(nameB)
    idasset =  param['assetOut'] + nomeDesc
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId':idasset, 
        'region':regionB.getInfo(), #['coordinates']
        'scale': 30, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"}
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))



def GetPolygonsfromFolder(nBacias):
    
    getlistPtos = ee.data.getList(param['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])
    print("bacias vizinhas ", nBacias)
   
    for idAsset in getlistPtos:         
        path_ = idAsset.get('id')
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')
        # print(newName[0])
        if str(newName[0]) in nBacias :
            # print("lindo ", str(newName[0]))
            FeatTemp = ee.FeatureCollection(path_)    
            # print(FeatTemp.size().getInfo())
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    ColectionPtos = ee.FeatureCollection(ColectionPtos)        
    return  ColectionPtos


def FiltrandoROIsXimportancia(nROIs, baciasAll, nbacia):

    print("aqui  ")
    limitCaat = ee.FeatureCollection('users/CartasSol/shapes/nCaatingaBff3000')
    # selecionando todas as bacias vizinhas 
    baciasB = baciasAll.filter(ee.Filter.eq('nunivotto3', nbacia))
    # limitando pelo bioma novo com buffer
    baciasB = baciasB.geometry().buffer(2000).intersection(limitCaat.geometry())
    # filtrando todo o Rois pela área construida 
    redROIs = nROIs.filterBounds(baciasB)
    mhistogram = redROIs.aggregate_histogram('class').getInfo()
    

    ROIsEnd = ee.FeatureCollection([])
    
    roisT = ee.FeatureCollection([])
    for kk, vv in mhistogram.items():
        print("class {}: == {}".format(kk, vv))
        
        roisT = redROIs.filter(ee.Filter.eq('class', int(kk)))
        roisT =roisT.randomColumn()
        
        if int(kk) == 4:

            roisT = roisT.filter(ee.Filter.gte('random',0.5))
            # print(roisT.size().getInfo())

        elif int(kk) != 21:

            roisT = roisT.filter(ee.Filter.lte('random',0.9))
            # print(roisT.size().getInfo())

        ROIsEnd = ROIsEnd.merge(roisT)
        # roisT = None
    
    return ROIsEnd

def check_dir(file_name):

    if not os.path.exists(file_name):
        arq = open(file_name, 'w+')
        arq.close()


versao = '1'
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
imagens_mosaic = ee.ImageCollection(param['asset_mosaic']).filter(
                            ee.Filter.eq('biome', 'CAATINGA'))
ftcol_baciasbuffer = ee.FeatureCollection(param['asset_bacias_buffer'])
#nome das bacias que fazem parte do bioma7619
nameBacias = arqParams.listaNameBacias
print("carregando {} bacias hidrograficas ".format(len(nameBacias)))

#lista de anos
list_anos = [k for k in range(param['anoInicial'], param['anoFinal'] + 1)]
print('lista de anos entre 1985 e 2020')
param['lsBandasMap'] = ['classification_' + str(kk) for kk in list_anos]
print(param['lsBandasMap'])
list_carta = arqParams.ls_cartas

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
bandNames = ['awei_median_dry', 'blue_stdDev', 'brightness_median', 'cvi_median_dry',]
a_file = open("registroYear_FeatsImp.json", "r")
dictFeatureImp = json.load(a_file)


def iterandoXBacias(baciabuffer, _nbacia, bRois):

    imglsClasxanos = ee.Image().byte()
    mydict = None
    baciabuffer = ee.Geometry(baciabuffer)
    # print("area ", baciabuffer.area(0.1).getInfo())
    bandas_imports = []
    for cc, ano in enumerate(range(1985, 2022)):
        
        #se o ano for 2018 utilizamos os dados de 2017 para fazer a classificacao
        bandActiva = 'classification_' + str(ano)        
        print( "banda activa: " + bandActiva)
        
        if ano < 2020:
            bandas_imports = dictFeatureImp[str(ano)]
            # print(type(bandas_imports))
            if 'slope' in bandas_imports:
                bandas_imports.remove('slope')
            # print(bandas_imports)
            
            
            # if 'red_min' not in bandas_imports:
            #     print("==== BANDA RED_MIN EXIST ===")
            # else:
            #     bandas_imports.remove('red_min')
            # #     print("show bandas de importancia \n", bandas_imports)
                
        # else:
        #     print("bandas de importancia 2020 \n", bandas_imports)
        # print("coletando  pontos nos anos ", ls_year_rois)
        
        ROIs_toTrain = ee.FeatureCollection(bRois).filter(ee.Filter.eq('year', ano))        
        # print()
        
        if param['anoInicial'] == ano and ano == 2021:            
            # pega os dados de treinamento utilizando a geometria da bacia com buffer           
            print(" Distribuição dos pontos na bacia << {} >>".format(_nbacia))
            print("===  {}  ===".format(ROIs_toTrain.aggregate_histogram('class').getInfo()))            
        
        #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia    
        mosaicMapbiomas = imagens_mosaic.filter(ee.Filter.eq('year', ano)
                                    ).filterBounds(baciabuffer).median()
        
        # print(mosaicMapbiomas.size().getInfo())
        ################################################################
        # listBandsMosaic = mosaicMapbiomas.bandNames().getInfo()
        # print("bandas ativas ", listBandsMosaic)
        # for bband in lsAllprop:
        #     if bband not in listBandsMosaic:
        #         print("Alerta com essa banda = ", bband)
        ###############################################################
        # print(ROIs_toTrain.size().getInfo())
        # ROIs_toTrain_filted = ROIs_toTrain.filter(ee.Filter.notNull(bandas_imports))
        # print(ROIs_toTrain_filted.size().getInfo())
        # lsAllprop = ROIs_toTrain_filted.first().propertyNames().getInfo()
        # print('PROPERTIES FEAT = ', lsAllprop)
        #cria o classificador com as especificacoes definidas acima 
        
        # classifierRF = ee.Classifier.smileRandomForest(**param['pmtRF'])\
        #                             .train(ROIs_toTrain, 'class', bandas_imports)

        # classifiedRF = mosaicMapbiomas.classify(classifierRF, bandActiva)
        # ee.Classifier.smileGradientTreeBoost(numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed)
        classifierGTB = ee.Classifier.smileGradientTreeBoost(**param['pmtGTB'])\
                                    .train(ROIs_toTrain, 'class', bandas_imports)

        classifiedGTB = mosaicMapbiomas.classify(classifierGTB, bandActiva)


        # ee.Classifier.libsvm(decisionProcedure, svmType, kernelType, shrinking, degree, gamma, coef0, cost, nu, terminationEpsilon, lossEpsilon, oneClass)
        # classifierSVM = ee.Classifier.libsvm(**param['pmtSVM'])\
        #                             .train(ROIs_toTrain, 'class', bandas_imports)

        # classifiedSVM = mosaicMapbiomas.classify(classifierSVM, bandActiva)
        # print("classificando!!!! ")

        # threeClassification  = classifiedRF.addBands(classifiedGTB).addBands(classifiedSVM)
        # threeClassification = threeClassification.reduce(ee.Reducer.mode(1))
        # threeClassification = threeClassification.rename(bandActiva)

        #se for o primeiro ano cria o dicionario e seta a variavel como
        #o resultado da primeira imagem classificada
        #print("addicionando classification bands")
        if param['anoInicial'] == ano:
            print ('entrou em 1985')
            imglsClasxanos = copy.deepcopy(classifiedGTB)
            
            mydict = {
                'id_bacia': _nbacia,
                'version': '1',
                'biome': param['bioma'],
                'collection': '7.0',
                'sensor': 'Landsat'                
            }
            imglsClasxanos = imglsClasxanos.set(mydict)
        #se nao, adiciona a imagem como uma banda a imagem que ja existia
        else:
            print("Adicionando o mapa do ano  ", ano)
            imglsClasxanos = imglsClasxanos.addBands(classifiedGTB)
    
    # i+=1
    # print(param['lsBandasMap'])
    # seta as propriedades na imagem classificada            
    imglsClasxanos = imglsClasxanos.select(param['lsBandasMap'])    
    imglsClasxanos = imglsClasxanos.clip(baciabuffer).set("system:footprint", baciabuffer.coordinates())
    
    nomec = _nbacia + '_' + 'RF_col7'
    # exporta bacia
    processoExportar(imglsClasxanos, baciabuffer.coordinates(), nomec) 
    # sys.exit()


## Revisando todos as Bacias que foram feitas 
registros_proc = "registros/lsBaciasClassifyfeitasv_1.txt"
pathFolder = os.getcwd()
path_MGRS = os.path.join(pathFolder, registros_proc)
baciasFeitas = []
check_dir(path_MGRS)

arqFeitos = open(path_MGRS, 'r')
for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

arqFeitos.close()
arqFeitos = open(path_MGRS, 'a+')

# nameBacias = [
#         '7421','744','746','754','756','7621','7622', '763',
#         '764','765','766', '767','776','777','778','7619'
# ]

# '7621','764','765','766','767'
cont = 0
for _nbacia in nameBacias[:]:
    
    # if _nbacia not in baciasFeitas:
        
    cont = gerenciador(cont) 
    print("-------------------.kmkl-------------------------------------")
    print("--------    classificando bacia " + _nbacia + "-----------------")   
    print("--------------------------------------------------------")     

    selectBacia = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).first()
    # https://code.earthengine.google.com/2f8ea5070d3f081a52afbcfb7a7f9d25 
    baciasBuff = ftcol_baciasbuffer.filter(ee.Filter.eq('nunivotto3', _nbacia)).first().geometry()
    
    #lsNamesBacias = baciasBuff.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list').getInfo()
    #print("lista de Bacias vizinhas", lsNamesBacias) 
   
    lsNamesBacias = arqParams.dictBaciasViz[_nbacia]
    # print(lsNamesBacias)
    ROIs = GetPolygonsfromFolder(lsNamesBacias) 
    newROIs = ROIs.filterBounds(baciasBuff)  
    # print("ROIs = ", ROIs.size().getInfo())    
    # mhistogram = ROIs.aggregate_histogram('class').getInfo()    
    # print(mhistogram)
    # print(ROIs.first().getInfo())

    iterandoXBacias(
                baciasBuff, 
                _nbacia,                  
                newROIs)                        

    arqFeitos.write(_nbacia + '\n')

arqFeitos.close()
