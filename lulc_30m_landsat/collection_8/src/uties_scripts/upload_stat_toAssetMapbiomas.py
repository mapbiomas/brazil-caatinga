#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import gee
import sys
import json
import pandas as pd
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



lst_bnd = [
        'blue_median_mean','blue_median_stdDev','green_median_mean', 
        'green_median_stdDev','red_median_mean','red_median_stdDev', 
        'nir_median_mean','nir_median_stdDev','swir1_median_mean', 
        'swir1_median_stdDev','swir2_median_mean','swir2_median_stdDev', 
        'blue_median_wet_mean','blue_median_wet_stdDev','green_median_wet_mean', 
        'green_median_wet_stdDev','red_median_wet_mean','red_median_wet_stdDev', 
        'nir_median_wet_mean','nir_median_wet_stdDev','swir1_median_wet_mean',
        'swir1_median_wet_stdDev', 'swir2_median_wet_mean','swir2_median_wet_stdDev', 
        'blue_median_dry_mean','blue_median_dry_stdDev', 'green_median_dry_mean',
        'green_median_dry_stdDev', 'red_median_dry_mean','red_median_dry_stdDev', 
        'nir_median_dry_mean', 'nir_median_dry_stdDev', 'swir1_median_dry_mean', 
        'swir1_median_dry_stdDev','swir2_median_dry_mean', 'swir2_median_dry_stdDev'
    ];


params = {
    'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/stats_mosaics',
    'pathStat': '/home/superusuario/Dados/mapbiomas/col8/stats/',
    'biomes': ['CAATINGA','CERRADO','MATAATLANTICA'],
    'numeroTask': 6,
    'numeroLimit': 35,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05'         
    }
};

# salva ftcol para um assetindexIni
def save_ROIs_toAsset(collection, name_exp):

    optExp = {
        'collection': collection,
        'description': name_exp,
        'assetId': params['asset_output'] + "/" + name_exp
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando a estadistica  $s ...!", name_exp)

collection = ee.ImageCollection(params['asset_mosaic_mapbiomas']).filter(
                            ee.Filter.eq('version', '1'))
dictCoord = {}

for year in range(1985, 2023):

    featColStats = ee.FeatureCollection([])
    limitCaat = ee.FeatureCollection(params['asset_bacias']);
    print(" viewer collections ", collection.size().getInfo());

    nameTable = 'all_statisticsL8' + str(year) + '.csv'
    df_stast = pd.read_csv(params['pathStat'] + nameTable)
    print("colunas de df ", df_stast.shape)
    # print(df_stast.columns)
    print(df_stast.head())
    lst_cartaskey = [kk for kk in dictCoord.keys()]
    for cc, row in enumerate(df_stast.iterrows()):        
            # print(row[0])
            # print(row[1])
            id_row = row[1]['id_img']
            carta = id_row[9:18]
            if carta not in lst_cartaskey:
                geo_img_tmp = collection.filter(ee.Filter.eq(
                            'system:index', id_row)).first().geometry()
                points = geo_img_tmp.centroid()
                print(cc," ", id_row)
                coordenadas = points.getInfo()['coordinates']
                print("coordenadas = ", coordenadas)
                dictCoord[carta] = coordenadas
            else:
                coordenadas = dictCoord[carta]
                points = ee.Geometry.Point(coordenadas)

            dict_tmp = {}
            dict_tmp['id_img'] = id_row
            for col in lst_bnd:
                dict_tmp[col] = row[1][col]
            print('blue_median_mean = ',dict_tmp['blue_median_mean'])

            feat_tmp = ee.Feature(points, dict_tmp)
            featColStats = featColStats.merge(ee.FeatureCollection([feat_tmp]))

    save_ROIs_toAsset(featColStats, nameTable[:-4])


with open('registrostats_cartas_mosaic.json', 'w') as fp:
        json.dump(dictCoord, fp)