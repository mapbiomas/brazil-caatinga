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

nomeVetor = 'APA_R_Capivara'
sufixo = nomeVetor + '_col71'

param = {
    'inputAsset': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',     
    # 'assetVetor': 'users/data_sets_solkan/SHPs/APA_Guarajuba_limite',
    'assetVetor': 'users/data_sets_solkan/SHPs/APA_R_Capivara_limite',
    'collection': '7.1', # 
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXPORTcsv', 
    'lsClasses': [3,4,12,21,22,33,29],
}


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
# https://code.earthengine.google.com/5a7c4eaa2e44f77e79f286e030e94695
def calculateArea (image, pixelArea, geometry):

    pixelArea = pixelArea.addBands(image.rename('classe')).clip(geometry)#.addBands(
                                # ee.Image.constant(yyear).rename('year'))
    reducer = ee.Reducer.sum().group(1, 'classe')
    optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': param['scale'],
        'bestEffort': True, 
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)

    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

# pixelArea, imgMapa, bioma250mil

def iterandoXanoImCruda(imgAreaRef,  limite):
    classMapB = [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
    classNew = [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21]
    remap = True
  
    print("Loadding image Coleção 7.1 " )
    imgMapp = ee.Image(param['inputAsset']).clip(limite)  # para a 7.1

    imgAreaRef = imgAreaRef.clip(limite)
    areaGeral = ee.FeatureCollection([])    
    for year in range(1985, 2022):
        bandAct = "classification_" + str(year)
        if remap:
            newimgMap = imgMapp.select(bandAct).remap(classMapB, classNew)
        else:
            newimgMap = imgMapp.select(bandAct)#.remap(classMapB, classNew)
        areaTemp = calculateArea (newimgMap, imgAreaRef, limite)        
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year, 'nomeVetor', nomeVetor))
        areaGeral = areaGeral.merge(areaTemp)     
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
lstBands = ['classification_' + str(yy) for yy in range(1985, 2022)]
shpLimit = ee.FeatureCollection(param['assetVetor'])
pixelArea = ee.Image.pixelArea().divide(10000)
imgMapa = ee.ImageCollection(param['inputAsset']).select(lstBands)

nameCSV = "area_class_" + sufixo
print("Calculando a area ", nameCSV)
areaM = iterandoXanoImCruda(pixelArea, shpLimit)  
processoExportar(areaM, nameCSV)




    


