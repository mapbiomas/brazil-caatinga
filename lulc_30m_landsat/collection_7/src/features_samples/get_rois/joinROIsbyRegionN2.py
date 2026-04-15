#!/usr/bin/env python3
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

def getAllFeatsfromFolder(mpath):

    getParam = ee.data.getList(mpath)    

    feats_folder = []
    # featTotal = ee.FeatureCollection([])
    
    for item in getParam:
        # print(item)
        path_feat = item['id']
        feats_folder.append(path_feat)

    return feats_folder

#salva ftcol para um assetindexIni
def saveToAsset(collection, name):    
    asset_out = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv8/' + name 
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': asset_out          
    }
    
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()

    # optExp = {
    #         'collection': collection, 
    #         'description': name, 
    #         'folder': 'ROIscol7v2'          
    # }
    
    # task = ee.batch.Export.table.toDrive(**optExp)
    # task.start()
    
    print("exportando ROIs da bacia $s ...!", name)

asset_baciasN4 = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4'
feat_baciasN4 = ee.FeatureCollection(asset_baciasN4)

featfolder = {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv7'}
lst_allFeat = getAllFeatsfromFolder(featfolder)

# lsBacias = arqParam.listaNameBacias
lsBacias = [
        # '741','7421','7422','744','745','746','7492','751','752','753',
        # '754','755','756','757','758','759','7621','7622', '763','764',
        # '765','766', '767','771','772','773', '7741','7742','775','776',
        # '777','778','76111','76116','7612','7613','7614','7615','7616',
        '7617','7618','7619'
]
lst_properties = arqParam.allFeatures
# print(lst_properties)
dict_lstBacias = arqParam.dictlstBacias
for item in lsBacias[:]: 
    print("processing = ", item)
    lst_tmp = []
    for itemN4 in lst_allFeat:
        partes = itemN4.split('/')[-1].split('_')
        # print(partes)
        if item == partes[0]:
            print("    ", itemN4)
            lst_tmp.append(itemN4)

    featBN4 = ee.FeatureCollection([])
    for nitem in lst_tmp:
        feat_tmp = ee.FeatureCollection(nitem)
        # print(nitem, " " , feat_tmp.size().getInfo())
        feat_tmp = feat_tmp.filter(ee.Filter.notNull(lst_properties[:4]))
        # print(nitem, " " , feat_tmp.size().getInfo())
        featBN4 = featBN4.merge(feat_tmp)

    saveToAsset(featBN4, item + "_2")
