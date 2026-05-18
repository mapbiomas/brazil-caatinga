#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
import json
import csv
import sys
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
# sys.setrecursionlimit(1000000000)


options = {
    'asset_point_control': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/points_class_referencias/occTab_corr_Caatinga_maps_caat_col6_v5_4',
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv10/',
    "anoIntInit": 1985,
    "anoIntFin": 2019,
}

def filter_ptos_mal_classificadosCorr ( feat_pto):
    
    for yyear in range(1985,2018):
        layer_class = "classification_" + str(yyear)
        layer_ref = 'CLASS_' +  str(yyear) 
        # atualizando a propiedade         
        feat_pto = ee.Algorithms.If(
                            ee.Algorithms.IsEqual(ee.Feature(feat_pto).get(layer_ref), ee.Feature(feat_pto).get(layer_class)), 
                            ee.Feature(feat_pto).set('discorda_' + str(yyear), False),
                            ee.Feature(feat_pto).set('discorda_' + str(yyear), True),
                        )        
        
    return ee.Feature(feat_pto)

def saveToAsset(collection, name):

    optExp = {
        'collection': collection,
        'description': name,
        'assetId': options['outAsset'] + name
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()

    print("exportando ROIs da bacia $s ...!", name)

feat_pts_true = ee.FeatureCollection(options['asset_point_control'])
print("numero de pontos ", feat_pts_true.size().getInfo())
        
sfeat_pts_true = feat_pts_true.map(lambda feat: filter_ptos_mal_classificadosCorr(feat))

nameM = 'occTab_Caatinga_maps_col6'
saveToAsset(sfeat_pts_true, nameM)

   
