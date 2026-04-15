
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

param = {
    'asset_output':'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/',
    'asset_input' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv500m/',
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga"
}

#salva ftcol para um assetindexIni
def saveToAsset(collection, name):    
    
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': param['asset_output'] + name
    }
    
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    
    print("exportando ROIs da bacia $s ...!", name)


featColBacias = ee.FeatureCollection(param['asset_bacias'])
print("Loading bacias = ", featColBacias.size().getInfo())

featColBacias = featColBacias.map(lambda feat : feat.buffer(500))
saveToAsset(featColBacias, 'bacias_hidrograficaCaatbuffer500m')