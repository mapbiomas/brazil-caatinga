#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

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
    'input_asset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',
    'inputAsset10': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    "asset_bacias_buffer":  'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    "output_asset": 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',
    'versionOut' : 6,
    'versionInp' : 5,
    'last_year' : 2025,
    'first_year': 2016,
    'classMapB': [3, 4, 12, 21, 22, 25, 29, 33],
    'classNew':  [3, 4, 12, 21, 22, 22, 12, 33],
    'numeroTask': 6,
    'numeroLimit': 16,
    'conta' : {
        '0': 'caatinga01',
        '4': 'caatinga02',
        '6': 'caatinga03',
        '8': 'caatinga04',
        '10': 'caatinga05',        
        '12': 'solkan1201',   
        '14': 'superconta'      
    }
}

layerAflo = ee.Image(param['inputAsset10']).eq(29).reduce(ee.Reducer.sum())
layerAflo = layerAflo.gt(0)
#exporta a imagem classificada para o asset
def processoExportar(mapaRF,  nomeDesc, geom_bacia):
    
    idasset =  os.path.join(param['output_asset'], nomeDesc)
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId': idasset, 
        'region': geom_bacia,  # .getInfo()['coordinates']
        'scale': 10, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"}
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))

def apply_spatialFilterConn(name_bacia):
    
    geomBacia = (ee.FeatureCollection(param['asset_bacias_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', name_bacia))
        )
    geomBacia = geomBacia.map(lambda f: f.set('id_codigo', 1))
    bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)            
    geomBacia = geomBacia.geometry()

    imgClass = (ee.ImageCollection(param['input_asset'])
                        .filter(ee.Filter.eq('version', param['versionInp']))
                        .filter(ee.Filter.eq('id_bacias', name_bacia ))
                )
    print(" we load ", imgClass.size().getInfo())
    # print(imgClass.aggregate_histogram('version').getInfo())
    imgClass = imgClass.first().updateMask(bacia_raster)
    print('  show metedata imgClass', imgClass.get('system:index').getInfo())

    class_output = ee.Image().byte()    
    lstyear = [yy for yy in range(param['first_year'], param['last_year'] + 1)]
    lst_yy_class = [f'classification_{yy}' for yy in lstyear]
    for nyear in lstyear:
        banda_activa = f'classification_{nyear}'
        rasterSpatialYear = imgClass.select(banda_activa)   
        ## addicionando a camada de Afloramento de uso e cobertura
        rasterSpatialYear = rasterSpatialYear.where(layerAflo.eq(1), 29)
        class_output = class_output.addBands(rasterSpatialYear.rename(banda_activa))  


    
    name_exp = f"filterSP_BACIA_{name_bacia}_GTB_V{param['versionOut']}"
    class_output = (class_output.updateMask(bacia_raster)
                .select(lst_yy_class)
                .set(
                    'version', param['versionOut'], 
                    'biome', 'CAATINGA',
                    'source', 'geodatin',
                    'model', "GTB",
                    'type_filter', 'merger',
                    'collection', '3.0',
                    'id_bacias', name_bacia,
                    'sensor', 'Sentinel',
                    'system:footprint', geomBacia
                ))

    processoExportar(class_output,  name_exp, geomBacia)
    # sys.exit()

def gerenciador(cont):    
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)    
    
    if str(cont) in numberofChange:
        
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 

        # tasks(n= param['numeroTask'], return_list= True) 
        # relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        # for lin in tarefas:            
        #     relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont


listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765'     
]
contador = 0
for cc, idbacia in enumerate(listaNameBacias[:]):   
    print("----- PROCESSING BACIA {} -------".format(idbacia))        
    # contador = gerenciador(contador)
    apply_spatialFilterConn(idbacia)