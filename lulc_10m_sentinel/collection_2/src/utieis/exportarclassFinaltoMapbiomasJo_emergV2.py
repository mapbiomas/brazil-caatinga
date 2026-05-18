#!/usr/bin/env python2
# -*- coding: utf-8 -*-

##########################################################
## CRIPT DE EXPORTAÇÃO DO RESULTADO FINAL PARA O ASSET  ##
## DE mAPBIOMAS                                         ##
## Produzido por Geodatin - Dados e Geoinformação       ##
##  DISTRIBUIDO COM GPLv2                               ##
#########################################################

import ee 
import gee
import json
import csv
import sys
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


def gerenciador(cont, paramet):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in paramet['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(paramet['conta'][str(cont)]))        
        gee.switch_user(paramet['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= paramet['numeroTask'], return_list= True)        
    
    elif cont > paramet['numeroLimit']:
        return 0
    
    cont += 1    
    return cont


param = {
    'asset_caat_buffer': 'users/CartasSol/shapes/caatinga_buffer5km',
    'outputAsset': 'projects/mapbiomas-workspace/COLECAO9/classificacao', 
    'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    'newinputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExportYY',  # BACIA_778_mixed_V244
    # projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport/BACIA_7742_mixed_V26
    'biome': 'CAATINGA', #configure como null se for tema transversal
    'version': 27,
    'collection': 9.0,
    'source': 'geodatin',
    'setUniqueCount': True,
    'theme': None, 
    'numeroTask': 0,
    'numeroLimit': 39,
    'conta' : {
        '0': 'caatinga01',   # 
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '25': 'solkan1201',    
        '30': 'solkanGeodatin',
        '35': 'diegoUEFS',
        # '16': 'superconta' 
    }

}
classMapB = [ 0, 3, 4, 5, 6, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =  [27, 4, 4, 4, 4, 4,12,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21,49,50,21]

countFix = 0
# countFix = gerenciador(countFix, param) 
processExport = True
metadados = {}
bioma5kbuf = ee.FeatureCollection(param['asset_caat_buffer']).geometry()
layerFloresta = None
imgColExp = ee.ImageCollection(param['outputAsset'])
print("lista de bandas da imagem min \n ", imgColExp.size().getInfo())

for ii, year in enumerate(range(1985, 2024)):  #     
    countFix = gerenciador(countFix, param)
    bandaAct = 'classification_' + str(year) 
    name = param['biome'] + '-' + str(year) + '-' + str(param['version'])
    imgExtraBnd = imgColExp.filter(ee.Filter.eq('system:index', name)).first()#.select([bandaAct], ['classification'])
    print("layer Florest ", imgExtraBnd.get('system:index').getInfo() )
    if year == 2022:
        layerFloresta = imgExtraBnd.eq(3)
    elif year == 2023:
        imgExtraBnd = imgExtraBnd.remap(classMapB, classNew)
        imgExtraBnd = imgExtraBnd.where(layerFloresta.eq(1), layerFloresta.multiply(3))
    
    imgYear = imgExtraBnd.clip(bioma5kbuf).set('biome', param['biome'])\
                    .set('year', year)\
                    .set('version', str(param['version'] + 2))\
                    .set('collection', param['collection'])\
                    .set('source', param['source'])\
                    .set('theme',None)\
                    .set('system:footprint', bioma5kbuf)    

    
    name = param['biome'] + '-' + str(year) + '-' + str(param['version'] + 1)
    if processExport:
        optExp = {   
            'image': imgYear.byte(), 
            'description': name, 
            'assetId': param['outputAsset'] + '/' + name, 
            'region': bioma5kbuf.getInfo()['coordinates'], #
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy": {".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... banda  " + name + "..!")
    else:
        print(f"verficando => {name} >> {imgYear.bandNames().getInfo()}")
        
        # sys.exit()