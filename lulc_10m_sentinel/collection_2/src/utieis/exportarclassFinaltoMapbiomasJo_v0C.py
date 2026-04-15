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
# import gee
import json
import csv
import sys
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount) # project='ee-cartassol'
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


# def gerenciador(cont, paramet):
#     #0, 18, 36, 54]
#     #=====================================#
#     # gerenciador de contas para controlar# 
#     # processos task no gee               #
#     #=====================================#
#     numberofChange = [kk for kk in paramet['conta'].keys()]
    
#     if str(cont) in numberofChange:

#         print("conta ativa >> {} <<".format(paramet['conta'][str(cont)]))        
#         gee.switch_user(paramet['conta'][str(cont)])
#         projAccount = get_project_from_account(param['conta'][str(cont)])
#         try:
#             ee.Initialize(project= projAccount) # project='ee-cartassol'
#             print('The Earth Engine package initialized successfully!')
#         except ee.EEException as e:
#             print('The Earth Engine package failed to initialize!')       
#         gee.tasks(n= paramet['numeroTask'], return_list= True)        
    
#     elif cont > paramet['numeroLimit']:
#         return 0
    
#     cont += 1    
#     return cont


param = {
    'asset_caat_buffer': 'users/CartasSol/shapes/caatinga_buffer5km',
    'outputAsset': 'projects/mapbiomas-workspace/COLECAO9-S2/classificacao', 
    'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/ilumination2',    
    'biome': 'CAATINGA', #configure como null se for tema transversal
    'version': 5,
    'collection': 2.0,
    'source': 'geodatin',
    'setUniqueCount': False,
    'theme': None, 
    'numeroTask': 0,
    'numeroLimit': 49,
    'conta' : {
        '0': 'caatinga01',   # 
        '2': 'caatinga02',
        '4': 'caatinga03',
        '6': 'caatinga04',
        '8': 'caatinga05',        
        '10': 'solkan1201',    
        '12': 'solkanGeodatin',
        # '14': 'diegoUEFS',
        '14': 'superconta' 
    }
}

nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
countFix = 14
# countFix = gerenciador(countFix, param)
processExport = True
metadados = {}
bioma5kbuf = ee.FeatureCollection(param['asset_caat_buffer']).geometry()


imgColExp = (ee.ImageCollection(param['inputAsset'])
                #   .filter(ee.Filter.eq('version', 4))
                #   .filter(ee.Filter.eq('type_filter', 'grassland'))
)
numMaps = imgColExp.size().getInfo()
print(f' We have {numMaps} imagens maps by basin in this asset')

# sys.exit()
# if numMaps != 42:
#     lstIds = imgColExpss.reduceColumns(ee.Reducer.toList(),['id_bacia']).get('list').getInfo()
#     print("lista de bacias ", lstIds)
#     sys.exit()

imgColExp = imgColExp.map(lambda img: ee.Image.cat(img).toByte()).max()
print("lista de bandas da imagem min \n ", imgColExp.bandNames().getInfo())

for ii, year in enumerate(range(2016, 2024)):  #    
    # if param['setUniqueCount']:
    #     countFix = gerenciador(countFix, param)
    #     countFix = 16
    # else:
    #     countFix = gerenciador(ii , param)
 
    bandaAct = 'classification_' + str(year) 
    # print("Banda activa: " + bandaAct)
    # img_banda = 'CAATINGA-' + str(year) +  '-' + str(param['version'])
    imgExtraBnd = imgColExp.select([bandaAct], ['classification'])
    imgYear = imgExtraBnd.clip(bioma5kbuf).set(
                    'biome', param['biome'],
                    'year', year,
                    'version', str(param['version'] + 2),
                    'collection', param['collection'],
                    'source', param['source'],
                    'theme',None,
                    'territory', 'BRAZIL',
                    'system:footprint', bioma5kbuf)    

    
    name = param['biome'] + '-' + str(year) + '-' + str(param['version'] + 2)
    if processExport:
        optExp = {   
            'image': imgYear.byte(), 
            'description': name, 
            'assetId': param['outputAsset'] + '/' + name, 
            'region': bioma5kbuf.getInfo()['coordinates'], #
            'scale': 10, 
            'maxPixels': 1e13,
            "pyramidingPolicy": {".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print(f"salvando ... banda {ii} " + name + "..!")
    else:
        print(f"verficando => {name} >> {imgYear.bandNames().getInfo()}")
        
        # sys.exit()