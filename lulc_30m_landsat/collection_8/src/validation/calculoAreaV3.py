#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import sys
import arqParametros as arqParamet
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
sys.setrecursionlimit(1000000000)

path = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/CLASS/'
param = {
    # 'inputAsset': path + 'class_filtered_Tp',   
    'inputAsset': path + 'ClassCol8V2/',
    'collection': '7.0',
    'geral':  True,
    'isImgCol': True,  
    'inBacia': True,
    'version': '6',
    'sufixo': '_Cv7', 
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXPORT', 
    'lsClasses': [3,4,12,21,22,33,29],
    'numeroTask': 0,
    'numeroLimit': 37,
    'conta' : {
        '0': 'caatinga04'
    }
}

# arq_area =  arqParamet.area_bacia_inCaat

def gerenciador(cont, paramet):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in paramet['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(paramet['conta'][str(cont)]))        
        gee.switch_user(paramet['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= paramet['numeroTask'], return_list= True)        
    
    elif cont > paramet['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

##############################################
###     Helper function
###    @param item 
##############################################
def convert2featCollection (item):

    item = ee.Dictionary(item)

    feature = ee.Feature(ee.Geometry.Point([0, 0])).set(
        'classe', item.get('classe'),"area", item.get('sum'))
        
    return feature

#########################################################################
####     Calculate area crossing a cover map (deforestation, mapbiomas)
####     and a region map (states, biomes, municipalites)
####      @param image 
####      @param geometry
#########################################################################

def calculateArea (image, pixelArea, geometry):

    pixelArea = pixelArea.addBands(image.rename('classe'))#.addBands(
                                # ee.Image.constant(yyear).rename('year'))
    reducer = ee.Reducer.sum().group(1, 'classe')

    optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': param['scale'],
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)

    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

# pixelArea, imgMapa, bioma250mil

def iterandoXanoImCruda(imgAreaRef, imgMapp, limite):
    imgMapp = imgMapp.clip(limite)
    imgAreaRef = imgAreaRef.clip(limite)
    areaGeral = ee.FeatureCollection([])    
    for year in range(1985, 2022):
        bandAct = "classification_" + str(year) 
        areaTemp = calculateArea (imgMapp.select(bandAct), imgAreaRef, limite)        
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year))
        areaGeral = areaGeral.merge(areaTemp)      
    
    return areaGeral


def iterandoXano(imgAreaRef, limite):

    areaGeral = ee.FeatureCollection([])

    for year in range(1985, 2021): 
        
        if param['isImg'] == True:

            imgAct = 'classification_' + str(year)
            imgMap = ee.Image(param['inputAsset']).select(imgAct).clip(limite)
            
            if param['collection'] == '5.0':
                imgMap = imgMap.remap(param['classMapB'], param['classNew'])

        else:            
            
            imgAct = 'CAATINGA-' + str(year) + param['version']
            imgMap = ee.Image(param['inputAsset'] + imgAct).clip(limite)

        areaTemp = calculateArea (imgMap, imgAreaRef, limite, year)
        
        # areaTemp = areaTemp.map( lambda feat: feat.set('year', year))

        areaGeral = areaGeral.merge(areaTemp)

        if param['collection'] == '4.1' and year == 2018:
            break

    return areaGeral

        
#exporta a imagem classificada para o asset
def processoExportar(areaFeat, nameT):  
    
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': param["driverFolder"]        
        }
    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")      

#testes do dado
# https://code.earthengine.google.com/8e5ba331665f0a395a226c410a04704d
# https://code.earthengine.google.com/306a03ce0c9cb39c4db33265ac0d3ead
# get raster with area km2
lstBands = ['classification_' + str(yy) for yy in range(1985, 2023)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

gerenciador(0, param)

pixelArea = ee.Image.pixelArea().divide(10000)
imgMapa = ee.ImageCollection(param['inputAsset']).select(lstBands)

if param['version'] == '':
    imgMapa = ee.Image(imgMapa.min())
    nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_biome" + param['sufixo']

else:
    imgMapa = ee.Image(imgMapa.filter(
                        ee.Filter.eq('version', param['version'])).max())
    nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_biomeTempV" + param['version']

areaM = iterandoXanoImCruda(pixelArea, imgMapa, bioma250mil)  
processoExportar(areaM, nameCSV)



    


