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





def getAllFeatsfromFolder (mpath, name_bacia):

    getParam = ee.data.getList(mpath)    
    featTotal = ee.FeatureCollection([])

    for item in getParam:        
        name = item['id'].split('/')[-1]
        if name_bacia in name:
            print("item = " + name)
            feat_tmp = ee.FeatureCollection(item['id'])
            
            featTotal = featTotal.merge(feat_tmp)
    

    return featTotal

param = {
    'asset_bacias' : 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'asset_folder' : {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv3'},
    
}


bacias = ee.FeatureCollection(param['asset_bacias'])

# 741_1857_1
lsBacias = arqParam.listaNameBacias

for nameB in lsBacias:

    rois_group = getAllFeatsfromFolder(param['asset_folder'], nameB)
    size_points = rois_group.size().getInfo()

    print("bacia = " + nameB + "  | with size = " + str(size_points))

