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
sys.setrecursionlimit(1000000000)


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
        cont = 0
    
    cont += 1    
    return cont


param = {
    'correct_past_to_Grass' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/geom_correct21_12_7612_7613_76116',
    'otherinput': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_v1',
    'inputAsset': 'projects/mapbiomas-workspace/COLECAO7/classificacao',
    'outputAsset': 'projects/mapbiomas-workspace/COLECAO7/classificacao',   
    'biome': 'CAATINGA', #configure como null se for tema transversal
    'version': '5',
    'collection': 7.1,
    'source': 'geodatin',
    'theme': None, 
    'numeroTask': 0,
    'numeroLimit': 38,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '27': 'caatinga05',        
        '33': 'solkan1201',  
        # '28': 'rodrigo',
        # '32': 'diegoGmail'
    }
}

metadados = {}
lst_bacias = ['7612','7613','76116']
bioma250mil = ee.FeatureCollection('users/CartasSol/shapes/nCaatingaBff3000').geometry()
imgExtra = ee.ImageCollection(param['otherinput']).filter(ee.Filter.inList('id_bacia', lst_bacias)).min()
correct_past_to_Grassland = ee.Feature(ee.FeatureCollection(param['correct_past_to_Grass']).first())

for ii, year in enumerate(range(1985, 2022)):  #
    
    gerenciador(ii , param)
    bandaAct = 'classification_' + str(year) 
    imgExtraBnd = imgExtra.select(bandaAct)
    maskExtra = imgExtraBnd.gt(0).unmask(0)
    maskExtra = maskExtra.focalMin(10)
    imgExtraBnd = imgExtraBnd.updateMask(maskExtra).unmask(0)
    # print("Banda activa: " + bandaAct)
    img_banda = 'CAATINGA-' + str(year) +  '-' + param['version']
    imgClass = ee.Image(param['inputAsset'] + '/' + img_banda)
    
    print("###### change pixels with pastagem by grasland year [{}] ########".format(img_banda))
    geom_erro = ee.Geometry(correct_past_to_Grassland.geometry()).intersection(bioma250mil)
    feat_err1 = ee.Feature(bioma250mil.difference(geom_erro), {'value': 0})
    feat_err0 = ee.Feature(geom_erro, {'value': 1})
    feat_mask_err = ee.FeatureCollection([feat_err0, feat_err1])
    # área dentro do poligon com valores em 1
    img_mask_err = feat_mask_err.reduceToImage(['value'], ee.Reducer.first())
    img_21 = imgClass.eq(21)
    img18 = imgExtraBnd.eq(18).unmask(0)
    maskPixelVar = img_mask_err.multiply(img_21).multiply(img18)
    maskPixelVar = maskPixelVar.unmask(0)
    mask_area_inv = maskPixelVar.eq(0)
    mapallPixels = imgClass.updateMask(mask_area_inv).unmask(0).add(maskPixelVar.multiply(12))

    imgYear = mapallPixels.set('biome', param['biome'])\
                    .set('year', year)\
                    .set('version', param['version'])\
                    .set('collection', param['collection'])\
                    .set('source', param['source'])\
                    .set('system:footprint', bioma250mil)    

    
    name = param['biome'] + '-' + str(year) + '-7' 

    optExp = {   
        'image': imgYear.byte(), 
        'description': name, 
        'assetId': param['outputAsset'] + '/' + name, 
        'region': bioma250mil.getInfo()['coordinates'], #
        'scale': 30, 
        'maxPixels': 1e13,
        "pyramidingPolicy": {".default": "mode"}
    }

    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... banda  " + name + "..!")
    # sys.exit()