#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import json
import csv
import sys
import arqParametros as arqParams 
import argParam as feat_import

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
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV6_solo/',
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/ROIsXBacias_solo'},
    'asset_armonico': 'projects/nexgenmap/MapBiomas2/LANDSAT/mosaics-normalized',
    'anoInicial': 2018,
    'anoFinal': 2020,
    "anoIntInit": 2018,
    "anoIntFin": 2020,
    'sufix': "_03",    
    'lsBandasMap': [],
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta' : {
        '0': 'caatinga01',
        '6': 'caatinga02',
        '12': 'caatinga03',
        # '18': 'caatinga04',
        # '24': 'caatinga05',        
        # '28': 'solkan1201',
        # '32': 'diegoGmail',
        # '35': 'rodrigo',
        # '34': 'Rafael'        
    },
    'pmtRF': {
        'numberOfTrees': 25, 
        'variablesPerSplit': 5,
        'minLeafPopulation': 5,
        'bagFraction': 0.8,
        'seed': 0
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
    #print(regionB)
      
    nomeDesc = 'RF_BACIA_'+ str(nameB)
    # idasset = 
    idasset =  param['assetOut'] + nomeDesc
    
    print (idasset)
    
    optExp = {'image': mapaRF, 
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

#map do col anos
def map_col_pontos(table):
	mylist = table.get('id').split('/')
	FeatCPtos = ee.FeatureCollection(table.get('id')).map(lambda f: f.set('id', int(mylist[len(mylist) - 1])))
	return FeatCPtos


def GetPolygonsfromFolder(nBacias):
    
    getlistPtos = ee.data.getList(param['assetROIs'])

    ColectionPtos = ee.FeatureCollection([])
    print("bacias vizinhas ", nBacias)
   
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        # print(path_) 
        
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')
        # print(newName[0])
        if newName[0] in nBacias :
            # print(newName)
            FeatTemp = ee.FeatureCollection(path_)    
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


def ApplyReducers (img):      
    # img_sum =  ee.Image(img).reduce(ee.Reducer.sum())
    img_median = ee.Image(img).reduce(ee.Reducer.median())
    img_mean = ee.Image(img).reduce(ee.Reducer.mean())
    img_vari = ee.Image(img).reduce(ee.Reducer.variance())
    img_mode = ee.Image(img).reduce(ee.Reducer.mode())
    img_stdDev = ee.Image(img).reduce(ee.Reducer.stdDev())
    img_max = ee.Image(img).reduce(ee.Reducer.max())
    img_min = ee.Image(img).reduce(ee.Reducer.min())
    img_amp = img_max.subtract(img_min).rename('amplitude')

    return img_median.addBands(img_mean).addBands(img_vari) \
          .addBands(img_mode).addBands(img_stdDev).addBands(img_max) \
          .addBands(img_min).addBands(img_amp).copyProperties(img)


versao = '5'
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

imagens_armonica = ee.ImageCollection(param['asset_armonico']).filter(
                                ee.Filter.eq('method', 'harmonic'))

#nome das bacias que fazem parte do bioma7619
nameBacias = arqParams.listaNameBacias
print("carregando {} bacias hidrograficas ".format(len(nameBacias)))

#lista de anos
list_anos = [k for k in range(2018,2021)]
print('lista de anos entre 2018 e 2020', list_anos)
param['lsBandasMap'] = ['classification_' + str(kk) for kk in list_anos]
list_carta = arqParams.ls_cartas

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
bandNames = ['median', 'mean', 'variance', 'mode', 'stdDev', 'max', 'min', 'amplitude']

def iterandoXBacias(bacia, nomeBacia,  bRois):

    imglsClasxanos = ee.Image().byte()
    mydict = None
    primerAno = list_anos[0]
    selectBacia = bacia.filter(ee.Filter.eq('nunivotto3', nomeBacia)).first()
    selectBacia = selectBacia.geometry().buffer(2000)
    print("area ", selectBacia.area(0.1).getInfo())
    for ano in list_anos:
        
        #se o ano for 2018 utilizamos os dados de 2017 para fazer a classificacao
        bandActiva = 'classification_' + str(ano)        
        print( "banda activa: " + bandActiva)
        lookupIn = lookupIn = [3,4,12,21,22,29,33]
        lookupOut = [0,0,0,0,1,1,0]
        temptraining = bRois.filter(ee.Filter.eq('year', ano)).remap(
                                            lookupIn, lookupOut, 'class')        
        
        if primerAno == ano:
            
            #pega os dados de treinamento utilizando a geometria da bacia com buffer           
            print(" Distribuição dos pontos na bacia << {} >>".format(nomeBacia))
            print("===  {}  ===".format(temptraining.aggregate_histogram('class').getInfo()))            
        
        #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia    
        img_col_by_year = imagens_armonica.filter(ee.Filter.eq('year', ano))\
                                    .filterBounds(selectBacia)
                                    
        mosaicMapbiomas = img_col_by_year.map(lambda img : ApplyReducers(img))                           
        mosaicMapbiomas = ee.Image(mosaicMapbiomas.mosaic()).clip(selectBacia)
        
        # print("bandas ativas ", mosaicMapbiomas.bandNames().getInfo())
        print("bandas ativas ", bandNames)
        #cria o classificador com as especificacoes definidas acima 
        classifier = ee.Classifier.smileRandomForest(**param['pmtRF']).setOutputMode(
                                    'PROBABILITY').train(temptraining, 'class', bandNames)
        

        classified = mosaicMapbiomas.classify(classifier, bandActiva)
        classified = classified.gte(0.95)
        #print("classificando!!!! ")
        # verifica se o ano em questao eh o primeiro ano 
        # condition = ee.Algorithms.IsEqual(ano, primerAno)
        
        #se for o primeiro ano cria o dicionario e seta a variavel como
        #o resultado da primeira imagem classificada
        #print("addicionando classification bands")
        if primerAno == ano:
            #print ('entrou em 1985')
            imglsClasxanos = classified            
            mydict = {
                'id_bacia': _nbacia,
                'version': '6',
                'biome': param['bioma'],
                'collection': '6.0',
                'sensor': 'Landsat',
                'bacia': nomeBacia
            }
        #se nao, adiciona a imagem como uma banda a imagem que ja existia
        else:            
            imglsClasxanos = imglsClasxanos.addBands(classified)
    
    # i+=1
    
    #seta as propriedades na imagem classificada            
    imglsClasxanos = imglsClasxanos.select(param['lsBandasMap'])
    imglsClasxanos = imglsClasxanos.set(mydict)
    imglsClasxanos = imglsClasxanos.set("system:footprint", selectBacia.coordinates())
    
    nomec = _nbacia + '_' + 'RF-v6_solo_col6'
    #exporta bacia
    processoExportar(imglsClasxanos, selectBacia.coordinates(), nomec) #.bounds(1).getInfo()



## Revisando todos as Bacias que foram feitas 
registros_proc = "registros/lsBaciasClassifyfeitasv_6.txt"
baciasFeitas = []
try: 
    arqFeitos = open(registros_proc, 'r')
    for ii in arqFeitos.readlines():    
        ii = ii[:-1]
        # print(" => " + str(ii))
        baciasFeitas.append(ii)

    # if len(baciasFeitas) > 0:    
    #     print("listando Bacias Feitas")    
    #     for ii in baciasFeitas:
    #         print("==> " + ii)
    arqFeitos.close()
    arqFeitos = open(registros_proc, 'a+')
except:
    arqFeitos = open(registros_proc, 'w+')


cont = 0
nameBacias = ['751']
for _nbacia in nameBacias:
    
    # if _nbacia not in baciasFeitas:
        
    cont = gerenciador(cont) 
    print("--------------------------------------------------------")
    print("-----    classificando bacia " + _nbacia + "------------")   
    print("--------------------------------------------------------")     

    selectBacia = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).first() 
    baciasBuff = ftcol_bacias.filterBounds(selectBacia.geometry())    
    #lsNamesBacias = baciasBuff.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list').getInfo()
    #print("lista de Bacias vizinhas", lsNamesBacias) 
   
    lsNamesBacias = arqParams.dictBaciasViz[_nbacia]
    ROIs = GetPolygonsfromFolder(lsNamesBacias)    
    ROIs = ROIs.filter(ee.Filter.notNull(bandNames)) 
    # fROIs =  FiltrandoROIsXimportancia(ROIs, ftcol_bacias, _nbacia)   
    # print("filtrou as ROIs")  
    # mhistogram = ROIs.aggregate_histogram('class').getInfo()    
    # print(mhistogram)
    # print(ROIs.first().getInfo())

    iterandoXBacias(
                baciasBuff, 
                _nbacia,  
                ROIs)                             

    arqFeitos.write(_nbacia + '\n')

# arqFeitos.close()
