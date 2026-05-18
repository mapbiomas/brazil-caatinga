#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
# sys.setrecursionlimit(1000000000)


param = {
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_colection_bjoined': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2',
    'asset_collection_by_year': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2Y',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2Y',
    'bioma': "CAATINGA",
    'version': 4,
}
def processoExportar(mapaRF, regionB, nomeDesc):
    idasset =  os.path.join(param['asset_output'] , nomeDesc)
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId':idasset, 
        'region':ee.Geometry(regionB), #['coordinates'] .getInfo()
        'scale': 30, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"},
        # 'priority': 1000
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))

lst_year = [yyear for yyear in range(2023, 2024)]
lstbaciabuffer = ee.FeatureCollection(param['asset_bacias_buffer'])
        
imColjoin = ee.ImageCollection(param['asset_colection_bjoined'])
lstIdCodjoin = imColjoin.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()

imColbyYear = ee.ImageCollection(param['asset_collection_by_year'])
lstIdCodbYear = imColbyYear.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
print(lstIdCodbYear)
lstExc = ['751', '7625']
lstNameBacias = [f'BACIA_{cbasin}_2024_GTB_col10-v_4' for cbasin in lstExc]
for nameIndex in lstIdCodjoin:
    nbacia = nameIndex.split('_')[1]
    print(f'load {nbacia} >> {nameIndex}')
    baciabuffer = lstbaciabuffer.filter(ee.Filter.eq('nunivotto4', nbacia))
    print(f"know about the geometry 'nunivotto4' >>  {nbacia} loaded < {baciabuffer.size().getInfo()} > geometry" ) 
    baciabuffer = baciabuffer.map(lambda f: f.set('id_codigo', 1))
    bacia_raster =  baciabuffer.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    baciabuffer = baciabuffer.geometry()
    for nyear in lst_year:
        newNameInd = f'BACIA_{nbacia}_{nyear}_GTB_col10-v_4'
        if newNameInd not in lstIdCodbYear and newNameInd not in lstNameBacias:
            imbyYear = imColjoin.filter(ee.Filter.eq('id_bacia', nbacia)).first()            
            imbyYear = imbyYear.select(f'classification_{nyear}')
            print("selected ", imbyYear.bandNames().getInfo())
            mydict = {
                    'id_bacia': nbacia,
                    'version': param['version'],
                    'biome': param['bioma'],
                    'classifier': 'GTB',
                    'collection': '10.0',
                    'sensor': 'Landsat',
                    'source': 'geodatin',  
                    'year': nyear              
                }                    
            imbyYear = imbyYear.set(mydict)
            imbyYear = imbyYear.set("system:footprint", baciabuffer.coordinates())
            processoExportar(imbyYear, baciabuffer, newNameInd)
