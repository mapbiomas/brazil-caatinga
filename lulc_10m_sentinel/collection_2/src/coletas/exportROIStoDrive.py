#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
import copy
import sys
from tqdm import tqdm
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

def save_ROIs_toDrive(collection, name):
    optExp = {
        'collection': collection,
        'description': name,
        'folder': 'shp_ROIs_S2_caat_red'
    }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start()
    print(f"exportando ROIs da bacia {name} to drive ...!")

param = {
    'asset_rois_basin': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2',
}


listaNameRegion = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]

for cc, nreg in enumerate(listaNameRegion[:]):

    name_export = 'rois_grade_' + nreg 
    idAssetFeat = param['asset_rois_basin'] + '/' + name_export
    featROIsreg = ee.FeatureCollection(idAssetFeat)
    print(f" region {nreg} with {featROIsreg.size().getInfo()} features")

    save_ROIs_toDrive(featROIsreg, name_export)
