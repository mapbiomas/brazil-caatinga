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

dict_filter = {
    'Spatial/'  : 'filterSP_BACIA_',
    'Frequency/': 'filterFQ_BACIA_',
    'Temporal/': 'filterTP_BACIA_'
}
# keyAssetr = 'Spatial/'
# keyAssetr = 'Frequency/'
keyAssetr = 'Temporal/'
dict_KeyAsest = {
    'Spatial/' : '_Spv',
    'Frequency/': '_Fqv',
    'Temporal/': '_Tpv'
} 


path = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/CLASS/'
path = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/'
param = {
    # 'inputAsset': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',   
    # 'inputAsset': path + 'ClassCol8V10/',
    'inputAsset': path + keyAssetr,
    'collection': '8.0' ,  # '7.1'
    'geral':  True,
    'isImgCol': True,  
    'inBacia': True,
    'version': '5',
    'sufixo': '', 
    # 'sufixo': '_Spv2', 
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXPORT', 
    'lsClasses': [3,4,12,21,22,33,29],
    'numeroTask': 0,
    'numeroLimit': 37,
    'conta' : {
        '0': 'caatinga05'
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

def iterandoXanoImCruda(imgAreaRef, namBacia, limite):
    classMapB = [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
    classNew = [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21]
    nameImg = 'BACIA_' + namBacia + '_RF_col8'
    if 'POS-CLASS' in param['inputAsset'] :
        nameImg = dict_filter[keyAssetr] + namBacia + '_V' + param['version']
    else:
        nameImg = 'BACIA_' + namBacia + '_GTB_col8'
        # nameImg = 'BACIA_' + namBacia + '_RF_col8'    
    print("Loadding image " + nameImg)
    imgMapp = ee.Image(param['inputAsset'] + nameImg)   
    # imgMapp = ee.Image(param['inputAsset']).clip(limite)  # para a 7.1

    imgAreaRef = imgAreaRef.clip(limite)
    areaGeral = ee.FeatureCollection([])    
    for year in range(1985, 2023):
        bandAct = "classification_" + str(year)
        newimgMap = imgMapp.select(bandAct).remap(classMapB, classNew)
        areaTemp = calculateArea (newimgMap, imgAreaRef, limite)        
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year, 'bacia', namBacia))
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
lstBands = ['classification_' + str(yy) for yy in range(1985, 2023)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

gerenciador(0, param)

pixelArea = ee.Image.pixelArea().divide(10000)
imgMapa = ee.ImageCollection(param['inputAsset']).select(lstBands)
param['sufixo'] = dict_KeyAsest[keyAssetr] + param['version']
print("sufixo ", param['sufixo'])
# sys.exit()

# 100 arvores
nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]

listBacFalta = []
cont = 0
for _nbacia in nameBacias[:]:
    print("-------------------.kmkl-------------------------------------")
    print("--------    classificando bacia " + _nbacia + "-----------------")   
    print("--------------------------------------------------------") 
    nameCSV = 'areaXclasse_' + _nbacia + '_Col' + param['collection'] +  param['sufixo']
    baciabuffer = ee.FeatureCollection(param['asset_bacias_buffer']).filter(
                            ee.Filter.eq('nunivotto3', _nbacia)).first().geometry()
    try:
        areaM = iterandoXanoImCruda(pixelArea, _nbacia, baciabuffer)  
        processoExportar(areaM, nameCSV)
    except:
        print("=== BACIA {} WAS FAILED ====")



    


