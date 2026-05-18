#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import ee
import gee
import time
import copy
import sys
import json
import collections
import pandas as pd
pd.set_option("mode.copy_on_write", True)
from pathlib import Path
collections.Callable = collections.abc.Callable

try:
    ee.Initialize(project= 'mapbiomas-caatinga-cloud') # project='ee-cartassol'
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


makeDict = False
asset_bacias_buffer = 'projects/ee-solkancengine17/assets/shape/bacias_hidrografica_caatinga_49_regions'
assetStast = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/statisticS2'

lstRegionsStat = [    
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746']
if makeDict: 
    dict_geral = {}
    for cc, nReg in enumerate(lstRegionsStat):        
        asset_shp = assetStast + '/' + nReg + '_stats'
        featCStattmp = ee.FeatureCollection(asset_shp)
        nsize = featCStattmp.size().getInfo()
        print("número de Feat == ", nsize)

        for nyear in range(2016, 2024):
            dictFeat = featCStattmp.filter(ee.Filter.eq('year', nyear)).first().getInfo()['properties']
            yearCourrent = int(dictFeat['year'])
            lstYear = [int(yy) for yy in dict_geral.keys()]
            if yearCourrent not in lstYear:
                dict_geral[str(yearCourrent)] = copy.deepcopy(dictFeat)
            else:
                dictTemp = dict_geral[str(yearCourrent)]
                for kk, vvv in dictFeat.items():
                    if kk != 'year' and kk != 'bacia':
                        print(f"addding {kk}  ==> {vvv} ")
                        dictTemp[kk] += vvv

                print(" DONE !")
                dict_geral[str(yearCourrent)] = dictTemp
        time.sleep(10)  # import time
    print("Feito todas as adições ")
    dict_means= {}
    for nyear, dictTemp in dict_geral.items():
        mydictTemp = copy.deepcopy(dictTemp)
        for indica, valor in dictTemp.items():
            print(f" year = {nyear} == {indica}   ==> {valor}")
            if indica != 'year' and indica != 'bacia':
                mydictTemp[indica] = round(int(mydictTemp[indica])/ 5, 3)

        dict_means[nyear] = mydictTemp

    # Convert and write JSON object to file
    with open("dict_stat_nyearReg.json", "w") as outfile: 
        json.dump(dict_means, outfile)

    print(" json << dict_stat_nyearReg >> saved ")

else:
    dict_geral = {}

    # Using json.load()
    with open('dict_stat_nyearReg.json') as dictJson:
        dict_geral = json.load(dictJson)

    for nyear, dictTemp in dict_geral.items():
        for indica, valor in dictTemp.items():
            print(f" year = {nyear} == {indica}   ==> {valor}")
    
    
    newDictToSave = {}
    for nyear, dictTemp in dict_geral.items():
        mydictTemp = copy.deepcopy(dictTemp)
        lstBands = []
        for kk in mydictTemp.keys():
            if 'y_min' in kk or 'an_min' in kk or 'v_min' in kk or 't_min' in kk or 'in_min' in kk: 
                print("adding ", kk)
                lstBands.append(kk)
        # valorMin
        for nband in lstBands:
            bandMax = nband[:-3]+ 'max'
            print(f" bandMin {nband}  bandMax {bandMax}")
            valor_min = copy.deepcopy(mydictTemp[bandMax])
            mydictTemp[bandMax] = mydictTemp[nband]
            mydictTemp[nband] = valor_min

        newDictToSave[nyear] = mydictTemp

    time.sleep(20)
    print(" comprovando dictionario  ")
    for nyear, dictTemp in newDictToSave.items():
        for indica, valor in dictTemp.items():
            print(f" year = {nyear} == {indica}   ==> {valor}")

    # Convert and write JSON object to file
    with open("dict_stat_nyearRegComp.json", "w") as outfile: 
        json.dump(newDictToSave, outfile)
    print(" json << dict_stat_nyearRegCorr >> saved ")

    