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
        'maxPixels': 1e9
    }
    statMean = img.reduceRegion(**pmtoRed);
    dict_statMean = statMean.getInfo()
    # print('viewer stats ', dict_statMean)
    return dict_statMean
    

def get_stats_standardDeviations(img, geomet):
    # // Add reducer output to the Features in the collection.
    pmtoRed = {
        'reducer': ee.Reducer.stdDev(),
        'geometry': geomet,
        'scale': 30,
        'maxPixels': 1e9
    }
    statstdDev = img.reduceRegion(**pmtoRed);
    dict_statstdDev = statstdDev.getInfo()
    # print('viewer stats Desvio padrão ', dict_statstdDev)
    return dict_statstdDev


params = {
    'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
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
# year = 2021
for year in range(2012, 2014):
    limitCaat = ee.FeatureCollection(params['asset_bacias']);
    collection = ee.ImageCollection(params['asset_mosaic_mapbiomas']).filter(
                            ee.Filter.eq('version', '1')).filter(
                                ee.Filter.eq('year', year)).filterBounds(
                                    limitCaat).select(lst_bnd);
    print(" viewer collections ", collection.size().getInfo());

    lst_ids = collection.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
    dict_All = {}
    dict_All['id_img'] = []
    for bnd in lst_bnd:
        dict_All[bnd + '_mean'] = []
        dict_All[bnd + '_stdDev'] = []

    cont = 0
    for cc, idim in enumerate(lst_ids[:]):
        print('processing # {} image {}'.format(cc, idim));
        imgtmp = collection.filter(ee.Filter.eq('system:index', idim)).first();
        mgeomet = imgtmp.geometry();
        lst_id = dict_All['id_img']
        lst_id.append(idim)
        dict_All['id_img'] = lst_id
        
        dict_mean = get_stats_mean(imgtmp, mgeomet);
        dict_stdDev = get_stats_standardDeviations(imgtmp, mgeomet);
        for bnd in lst_bnd:
            lst_mean = dict_All[bnd + '_mean']
            lst_stdDev = dict_All[bnd + '_stdDev']
            lst_mean.append(dict_mean[bnd])
            lst_stdDev.append(dict_stdDev[bnd])
            dict_All[bnd + '_mean'] = lst_mean
            dict_All[bnd + '_stdDev'] = lst_stdDev
        print("inseridooo ! ")

        cont = gerenciador(cont, params)
        
    # for kkey, vals in dict_All.items():
    #     for kk in range(len(vals)):
    #         print(kkey, va)

    df_stast = pd.DataFrame.from_dict(dict_All)
    df_stast.to_csv("all_statisticsL8" + str(year) + ".csv")
    print()