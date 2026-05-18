#!/usr/bin/env python2
# -*- coding: utf-8 -*-

##########################################################
## CRIPT DE EXPORTAÇÃO DO RESULTADO FINAL PARA O ASSET  ##
## DE mAPBIOMAS                                         ##
## Produzido por Geodatin - Dados e Geoinformação       ##
##  DISTRIBUIDO COM GPLv2                               ##
#########################################################
import ee
import os 
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


param = {
    'asset_caat_buffer': 'users/CartasSol/shapes/caatinga_buffer5km',
    'outputAsset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/classification-caa-ft', 
    'inputAsset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',  
    'inputAsset10': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2', 
    'biome': 'CAATINGA', #configure como null se for tema transversal
    'version_output': 8,
    'version_input': 7,
    'collection': 3.0,
    'source': 'geodatin',
    'setUniqueCount': True,
    'theme': None, 
}
classMapB = [ 0, 3, 4, 5, 6, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62,75]
classNew =  [27, 3, 4, 4, 4, 4,12,12,12,21,21,21,21,21,25,25,25,25,33,29,25,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21,49,50,21,25]

countFix = 0
# countFix = gerenciador(countFix, param) 
processExport = True
metadados = {}
bioma5kbuf = ee.FeatureCollection(param['asset_caat_buffer'])
bioma5kbuf = bioma5kbuf.map(lambda f: f.set('id_codigo', 1))
bioma5k_raster = bioma5kbuf.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0) 
bioma5kbuf = bioma5kbuf.geometry()
layerFloresta = None
imgColExp = (ee.ImageCollection(param['inputAsset'])
                    .filter(ee.Filter.eq('version', param['version_input']))
    )
layerAflo = ee.Image(param['inputAsset10']).eq(29).reduce(ee.Reducer.sum())
layerAflo = layerAflo.gt(0)

print("lista de bandas da imagem min \n ", imgColExp.size().getInfo())
imgColExp = imgColExp.min()

for ii, year in enumerate(range(2017, 2025)):  #        
    bandaAct = 'classification_' + str(year) 
    name = param['biome'] + '-' + str(year) + '-' + str(param['version_output'])
    imgExtraBnd = imgColExp.select(bandaAct)
    print("layer  ", imgExtraBnd.bandNames().getInfo() )
    # sys.exit()
    imgExtraBnd = imgExtraBnd.where(layerAflo.eq(1), 29)
    imgExtraBnd = imgExtraBnd.rename(bandaAct)
    
    imgYear = (imgExtraBnd.updateMask(bioma5k_raster)
                    .set('biome', param['biome'])
                    .set('year', year)
                    .set('version', str(param['version_output']))
                    .set('collection_id', param['collection'])
                    .set('description', 'versão pre-integrada da equipe Caatinga para a coleção 3.0 do Sentinel')
                    .set('source', param['source'])
                    .set('theme', None)
                    .set('territory', 'BRAZIL')
                    .set('system:footprint', bioma5kbuf)    
            )

    
    name = param['biome'] + '-' + str(year) + '-' + str(param['version_output'])
    if processExport:
        optExp = {   
            'image': imgYear.byte(), 
            'description': name, 
            'assetId': param['outputAsset'] + '/' + name, 
            'region': bioma5kbuf, #.getInfo()['coordinates']
            'scale': 10, 
            'maxPixels': 1e13,
            "pyramidingPolicy": {".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... banda  " + name + "..!")
    else:
        print(f"verficando => {name} >> {imgYear.bandNames().getInfo()}")
        
        # sys.exit()