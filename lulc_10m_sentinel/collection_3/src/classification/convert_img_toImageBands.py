#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import glob
import time
import json
import copy
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
    'asset_input': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/Classifier/ClassifyV2', 
    # 'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
    'asset_output': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'year_inic': 2016,
    'year_end': 2025,
    'bioma': "CAATINGA",
    'version': 5,
}
lst_bands = [f'classification_{yy}' for yy in range(param['year_inic'], param['year_end'] + 1)]
maps_col = ee.ImageCollection(param['asset_input']).filter(ee.Filter.eq('version', param['version']))
lst_idCod = maps_col.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
print(f"============ we have {len(lst_idCod)} images =======================")

# for ii in lst_idCod:
#     print(ii)
# sys.exit()

def apply_merger(nbacia):
    # loading geometry bacim
    baciabuffer = (ee.FeatureCollection(param['asset_bacias_buffer'])
                        .filter(ee.Filter.eq('nunivotto4', _nbacia))
                        .geometry()
                        )
    
    map_bands = ee.Image().byte()
    for nyear in range(param['year_inic'], param['year_end'] + 1): 
        for idCod in lst_idCod:
            if f"_{nbacia}_" in idCod and str(nyear) in idCod:
                print(f" processing {nbacia} >> {nyear}")
                map_tmp = ee.Image(os.path.join(param['asset_input'], idCod)).rename(f'classification_{nyear}')
                ## juntando as bandas 
                map_bands = map_bands.addBands(map_tmp)

    mydict = {
            'id_bacias': nbacia,
            'version': param['version'],
            'biome': param['bioma'],
            'classifier': 'GTB',
            'collection': '2.0',
            'sensor': 'Sentinel S2',
            'source': 'geodatin'             
        }
    
    map_bands = ee.Image(map_bands.select(lst_bands)).set(mydict)
    print("verify ", map_bands.get('id_bacias').getInfo())
    map_bands = map_bands.set("system:footprint", baciabuffer.coordinates())
    name_export =  f"{_nbacia}_GTB_col2S2-v_{param['version']}"
    processoExportar(map_bands, baciabuffer, name_export)


 #exporta a imagem classificada para o asset
def processoExportar(mapaRF, regionB, nameB):
    nomeDesc = 'BACIA_'+ str(nameB)
    idasset =  os.path.join(param['asset_output'] , nomeDesc)
    
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId':idasset, 
        'region':ee.Geometry(regionB), #['coordinates'] .getInfo()
        'scale': 10, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"},
        # 'priority': 1000
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))



nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751', 
    '752', '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622'
]

# nameBacias = [ "755","7622","746","7591","7544","7443", "766", "757", "7764", "7671", "7422", "7564"]

for cc, _nbacia in enumerate(nameBacias[:]):
    print("-------------------.kml---------------------------------------------")
    print(f"-------- {cc}   classificando bacia nova {_nbacia} ----------------")   
    print("---------------------------------------------------------------------") 
    apply_merger(_nbacia)
