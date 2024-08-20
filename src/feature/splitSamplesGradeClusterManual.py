#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import copy
import sys
import json
import os
import glob
from icecream import ic
from pathlib import Path
from tqdm import tqdm
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


param = {    
    'assetROIgradeBa': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisGradesgroupBuf',
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_shpGrade': 'projects/mapbiomas-arida/ALERTAS/auxiliar/basegrade30KMCaatinga',
    'assetROIsCC': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2clusterNN',
    'assetROIsMn': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2manualNN', 
    'asset_output': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisredDJoinsbyBaciaNN",
    'numeroTask': 6,
    'numeroLimit': 140,
    'conta' : {
        '0': 'caatinga01',
        '20': 'caatinga02',
        '40': 'caatinga03',
        '60': 'caatinga04',
        '80': 'caatinga05',        
        '100': 'solkan1201',
        '120': 'solkanGeodatin' 
    },
}

def GetPolygonsfromFolder(dictAsset):    
    getlistPtos = ee.data.getList(dictAsset)
    ColectionPtos = []
    # print("bacias vizinhas ", nBacias)

    for idAsset in tqdm(getlistPtos):         
        path_ = idAsset.get('id')        
        ColectionPtos.append(path_) 
        name = path_.split("/")[-1]
        if param['showAssetFeat']:
            print("Reading ", name)
        
    return ColectionPtos

#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, nameB, idPos):

    optExp = {
        'collection': ROIsFeat,
        'description': nameB,
        'assetId': param['asset_output'] + "/" + nameB,
        # 'priority': 8000
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start() 
    print(f" # {idPos} salvando ... " + nameB + " in asset ..!")

def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)            
    
    elif cont > param['numeroLimit']:
        return 0  
    cont += 1 
    return cont


nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766',
    # '767','771','772','773', '7741','7742','775','776',
    # '777',  '76111','76116','7612',
    # '7614','7615','7616','7617', '7618','7619', '7613'
]  # '778',

cont = gerenciador(0)

# consulting all file Samples saved by Basin and year 
# dictConsult = {'id': param['asset_output']}
# lstFeatSaved = GetPolygonsfromFolder(dictConsult)
# lstnameFeatsaved = [kk.split("/")[-1] for kk in lstFeatSaved]



for nbacia in nameBacias:
    print(" 🚨 loading ", nbacia )
    
    nameGradeBa = "bassinG_ROIs_" + nbacia + "_wl"
    featGradeBa = ee.FeatureCollection(param['assetROIgradeBa'] + "/" + nameGradeBa)
    for yyear  in range(1985, 2023):
        featAllSamples = ee.FeatureCollection([])
        totalAno = 0
        try:
            nameCluster = nbacia + "_" + str(yyear) +"_c1"
            featCluterYY = ee.FeatureCollection(param['assetROIsCC'] + "/" + nameCluster)
            sizeCC = featCluterYY.size().getInfo()
            totalAno += sizeCC
            print(f" {yyear} we have 📢 {sizeCC}  in cluster ")
            featAllSamples = featAllSamples.merge(featCluterYY)
        except:
            print(f"⚠️ We don´t have Samples by {nbacia} basin in year {yyear} ⚠️")

        featGradeBaYY = featGradeBa.filter(ee.Filter.eq('year', yyear))
        sizeGBa = featGradeBaYY.size().getInfo()
        totalAno += sizeGBa
        print(f" {yyear} we have 📢 {sizeGBa}  in ROIsGradeBacia ")
        dictClass = featGradeBaYY.aggregate_histogram('class').getInfo()
        print("    ", dictClass)
        featGradeBaYYnC412 = featGradeBaYY.filter(ee.Filter.inList('class', [4, 12, 15]).Not())
        namepropList = featGradeBaYYnC412.propertyNames()
        # só teste
        # print(featGradeBaYYnC412.aggregate_histogram('class').getInfo())        
        # preprocessing classe 4
        if '4' in dictClass.keys():
            print("processing 4")
            featGradeBaYYc4 = featGradeBaYY.filter(ee.Filter.eq('class', 4)).randomColumn('rand')
            limiarCut4 = float(3500 / dictClass['4'])
            featGradeBaYYc4 = featGradeBaYYc4.filter(ee.Filter.lt('rand', limiarCut4))
            featGradeBaYYc4 = featGradeBaYYc4.select(namepropList)

            featAllSamples = featAllSamples.merge(featGradeBaYYc4)

        # preprocessing class 12
        if '12' in dictClass.keys():
            print("processing 12")
            if dictClass['12'] > 600:
                featGradeBaYYc12 = featGradeBaYY.filter(ee.Filter.eq('class', 12)).randomColumn('rand')        
                limiarCut12 = float(600 / dictClass['12'])
                featGradeBaYYc12 = featGradeBaYYc12.filter(ee.Filter.lt('rand', limiarCut4))
                featGradeBaYYc12 = featGradeBaYYc12.select(namepropList)
            else: 
                featGradeBaYYc12 = featGradeBaYY.filter(ee.Filter.eq('class', 12))
            
            featAllSamples = featAllSamples.merge(featGradeBaYYc12)

        # preprocessing class 12
        if '15' in dictClass.keys():
            print("processing 15")
            if dictClass['15'] > 750:
                featGradeBaYYc15 = featGradeBaYY.filter(ee.Filter.eq('class', 15)).randomColumn('rand')        
                limiarCut15 = float(700 / dictClass['15'])
                featGradeBaYYc15 = featGradeBaYYc15.filter(ee.Filter.lt('rand', limiarCut4))
                featGradeBaYYc15 = featGradeBaYYc15.select(namepropList)
            else: 
                featGradeBaYYc15 = featGradeBaYY.filter(ee.Filter.eq('class', 15))
            
            featAllSamples = featAllSamples.merge(featGradeBaYYc15)

        # join Samples from grade coleted 
        featAllSamples = featAllSamples.merge(featGradeBaYYnC412)        
        

        if yyear == 2016 or yyear == 2021:
            # 741_2016_man
            try:
                nameManual = nbacia + "_" + str(yyear) +"_man"
                featmanualYY = ee.FeatureCollection(param['assetROIsMn'] + "/" + nameManual)
                sizeMn = featmanualYY.size().getInfo()
                totalAno += sizeMn
                print(f" {yyear} we have 📢 {sizeMn}  in ROIsGradeBacia ")
                featAllSamples = featAllSamples.merge(featmanualYY)
            except:
                print(f"⚠️ We don´t have Samples by {nbacia} basin in year {yyear} ⚠️")

        nameGrBaExp = "joined_ROIs_" + nbacia + "_" + str(yyear) +"_wl"
        processoExportar(featAllSamples, nameGrBaExp, yyear - 1985)
        cont = gerenciador(cont)

    