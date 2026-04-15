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


#salva ftcol para um assetindexIni
def saveToAsset(collection, name):    
    
    optExp = {
            'collection': collection, 
            'description': name, 
            'folder': 'ROIscol7v5'          
    }
    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start()
    
    print("exportando ROIs da bacia $s ...!", name)



asset_inp = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv5/'


lsBacias = arqParam.listaNameBacias
# '775',
# lsBacias = [
#         '773', '7741','7742','776','777','778','76111','76116','7612',
#         '7613','7614','7615','7616','7617','7618','7619'
# ]
for item in lsBacias:
    feat_exp = ee.FeatureCollection(asset_inp + item + '_j')

    saveToAsset(feat_exp, item + '_')