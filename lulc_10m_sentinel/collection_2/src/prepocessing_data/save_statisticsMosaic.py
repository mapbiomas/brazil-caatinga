#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import json
import csv
import sys
import pandas as pd
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise



#========================METODOS=============================
def gerenciador(cont, param):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]

    if str(cont) in numberofChange:
        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

lst_bnd = [
        "blue_median","green_median","red_median","nir_median",
        "swir1_median","swir2_median",         
        "blue_median_wet","green_median_wet","red_median_wet",
        "nir_median_wet","swir1_median_wet","swir2_median_wet",
        "blue_median_dry","green_median_dry","red_median_dry",
        "nir_median_dry","swir1_median_dry","swir2_median_dry", 
    ];
def get_stats_mean (img, geomet):
    #  Add reducer output to the Features in the collection.
    pmtoRed = {
        'reducer': ee.Reducer.mean(),
        'geometry': geomet,
        'scale': 30,
        'maxPixels': 1e13
    }
    statMean = img.reduceRegion(**pmtoRed);
    dict_statMean = statMean.getInfo()
    # print('viewer stats ', dict_statMean)
    return dict_statMean
    
def get_stats_min (img, geomet):
    #  Add reducer output to the Features in the collection.
    pmtoRed = {
        'reducer': ee.Reducer.min(),
        'geometry': geomet,
        'scale': 30,
        'maxPixels': 1e13
    }
    statMin = img.reduceRegion(**pmtoRed);
    dict_statMin = statMin.getInfo()
    # print('viewer stats Minimum', dict_statMin)
    return dict_statMin

def get_stats_max (img, geomet):
    #  Add reducer output to the Features in the collection.
    pmtoRed = {
        'reducer': ee.Reducer.max(),
        'geometry': geomet,
        'scale': 30,
        'maxPixels': 1e13
    }
    statMax = img.reduceRegion(**pmtoRed);
    dict_statMax = statMax.getInfo()
    # print('viewer stats Maximum', dict_statMax)
    return dict_statMax

def get_stats_standardDeviations(img, geomet):
    # // Add reducer output to the Features in the collection.
    pmtoRed = {
        'reducer': ee.Reducer.stdDev(),
        'geometry': geomet,
        'scale': 30,
        'maxPixels': 1e13
    }
    statstdDev = img.reduceRegion(**pmtoRed);
    dict_statstdDev = statstdDev.getInfo()
    # print('viewer stats Desvio padrão ', dict_statstdDev)
    return dict_statstdDev


def save_ROIs_toAsset(collection, name):
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': params['asset_output'] + "/" + name
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando ROIs da bacia $s ...!", name)

params = {
    'asset_mosaic_sentinel': 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
    'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/statisticS2',
    'biomes': ['CAATINGA','CERRADO','MATAATLANTICA'],
    'numeroTask': 6,
    'numeroLimit': 35,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',          
    }
};
listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]

featureBands = [
    'blue_median', 'blue_median_wet', 'blue_median_dry', 'blue_stdDev', 
    'green_median', 'green_median_dry', 'green_median_wet', 'green_median_texture', 
    'green_min', 'green_stdDev', 'red_median', 'red_median_dry', 'red_min', 
    'red_median_wet', 'red_stdDev', 'nir_median', 'nir_median_dry', 
    'nir_median_wet', 'nir_stdDev', 'red_edge_1_median', 'red_edge_1_median_dry', 
    'red_edge_1_median_wet', 'red_edge_1_stdDev', 'red_edge_2_median', 
    'red_edge_2_median_dry', 'red_edge_2_median_wet', 'red_edge_2_stdDev', 
    'red_edge_3_median', 'red_edge_3_median_dry', 'red_edge_3_median_wet', 
    'red_edge_3_stdDev', 'red_edge_4_median', 'red_edge_4_median_dry', 
    'red_edge_4_median_wet', 'red_edge_4_stdDev', 'swir1_median', 
    'swir1_median_dry', 'swir1_median_wet', 'swir1_stdDev', 'swir2_median', 
    'swir2_median_wet', 'swir2_median_dry', 'swir2_stdDev'
]

# year = 2021
for cc, nbacia in enumerate(listaNameBacias[:]):
    
    mgeomet = ee.FeatureCollection(params['asset_bacias_buffer']).filter(
                                        ee.Filter.eq('nunivotto4', nbacia)).geometry()

    collection = ee.ImageCollection(params['asset_mosaic_sentinel']).filter(
                                ee.Filter.inList('biome', params['biomes'])).filterBounds(
                                        mgeomet);
    
    featColHH = ee.FeatureCollection([])
    for year in range(2016, 2024):
        print('# {} processing mosaic  basin  {}  | year  {} '.format(cc, nbacia, year));
        collectionYY = collection.filter(ee.Filter.eq('year', year))
        # print(" viewer collections ", collectionYY.size().getInfo());

        collectionYY = collectionYY.mosaic().toInt16()
        # print(collectionYY.bandNames().getInfo())
        # break
        dictFeat = {}
        dictFeat['bacia'] = nbacia
        dictFeat['year'] = year
        
        for bnd in featureBands:
            dictFeat[bnd + '_mean'] = []
            dictFeat[bnd + '_stdDev'] = []    
            dictFeat[bnd + '_max'] = []
            dictFeat[bnd + '_min'] = []   

        # lst_id = dict_All[nbacia]
        # lst_id.append(idim)
        # dict_All['id_img'] = lst_id
        
        dict_mean = get_stats_mean(collectionYY, mgeomet);
        dict_min = get_stats_min(collectionYY, mgeomet);
        dict_max = get_stats_max(collectionYY, mgeomet);
        dict_stdDev = get_stats_standardDeviations(collectionYY, mgeomet);
        
        for bnd in featureBands:
            dictFeat[bnd + '_mean'] = dict_mean[bnd]
            dictFeat[bnd + '_stdDev'] = dict_stdDev[bnd]
            dictFeat[bnd + '_max'] = dict_min[bnd]
            dictFeat[bnd + '_min'] = dict_max[bnd]        

        feat_tmp = ee.Feature(mgeomet.centroid(), dictFeat)
        featColHH = featColHH.merge(ee.FeatureCollection([feat_tmp]))
    
    print("inseridooo ! ")
    name_exp = nbacia + '_stats'
    save_ROIs_toAsset(featColHH, name_exp)
