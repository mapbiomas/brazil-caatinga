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


spectralBands = ['blue', 'red', 'green', 'nir', 'swir1', 'swir2'];
param = {
    'input_asset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_all',
    'asset_polygon': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/poligons_corretores',
    'inputAsset10': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    'asset_painel_sol': 'projects/mapbiomas-arida/energias/solar-panel-br-30m',
    "asset_bacias_buffer":  'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
    "asset_afloramento": 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/rockyoutcropcol10',
    'asset_restinga': 'projects/mapbiomas-arida/restinga_ibge_2014',
    "asset_pol_mancha" : 'users/CartasSol/shapes/mancha_florest',
    "asset_collectionId": 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    "output_asset": 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
    'versionOut' : 4,
    'versionInp' : 4,
    'last_year' : 2025,
    'first_year': 2016,
    'classMapB': [3, 4, 12, 21, 22, 25, 29, 33],
    'classNew':  [3, 4, 12, 21, 22, 22, 12, 33],
}

list_bacia_flo = [
        "7411", "7422", "7424", "7438", "7443", "745", "746", 
        "751", "752", "753", "7544", "7564", "7612", "7613", 
        "7614", "7619"
    ]
mapsCobertura = ee.Image(param['inputAsset10'])
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
    # listCoor = [
    #     [-56.44604894060301,-31.07051878963668],
    #     [-32.18823644060301,-31.07051878963668],
    #     [-32.18823644060301,-0.10841888037947958],
    #     [-56.44604894060301,-0.10841888037947958],
    #     [-56.44604894060301,-31.07051878963668]
    # ]
    # limiteBox = ee.Geometry.Polygon(listCoor)
    imgClass = (ee.ImageCollection(param['input_asset'])
                        .filter(ee.Filter.eq('version', param['versionInp']))
                        .filter(ee.Filter.eq('id_bacias', name_bacia ))
                )
    print(" we load ", imgClass.size().getInfo())
    imgClass = imgClass.first().updateMask(bacia_raster)
    print('  show metedata imgClass', imgClass.get('system:index').getInfo())

    shp_restinga = (ee.FeatureCollection(param['asset_restinga'])
                        .map(lambda feat : feat.set('id_codigo', 1)))
    raster_restinga = shp_restinga.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    raster_afloramento = ee.Image(param["asset_afloramento"]).selfMask().multiply(29)
    # raster_FV = ee.Image(param['asset_painel_sol']).set('system:footprint', limiteBox)
    # raster_FV = raster_FV
    # print("know the bands FotoVoltaicas ", raster_FV.bandNames().getInfo())

    # shp_pol_correct = ee.FeatureCollection(param['asset_polygon'])
    # lstLabel = shp_pol_correct.reduceColumns(ee.Reducer.toList(), ['label']).get('list')
    # lstLabel = ee.List(lstLabel).distinct().getInfo()


    class_output = ee.Image().byte()    
    lstyear = [yy for yy in range(param['first_year'], param['last_year'] + 1)]
    lst_yy_class = [f'classification_{yy}' for yy in lstyear]
    for nyear in lstyear:
        banda_activa = f'classification_{nyear}'
        rasterSpatialYear = imgClass.select(banda_activa)      
        rasterSpatialYear = rasterSpatialYear.remap(param['classMapB'], param['classNew'])    
        rasterSpatialYear = rasterSpatialYear.blend(raster_afloramento)
        maskRest = rasterSpatialYear.updateMask(raster_restinga).lt(22) # .multiply(50)
        rasterSpatialYear = rasterSpatialYear.where(maskRest.eq(1), 50)

        if nyear < 2025:
            cobertYY = mapsCobertura.select(banda_activa)
        else:
            cobertYY = mapsCobertura.select('classification_2024')

        if name_bacia in list_bacia_flo:
            poly_florest = ee.FeatureCollection(param["asset_pol_mancha"]).map(lambda feat: feat.set('idcod', 1))
            mask_florest = poly_florest.reduceToImage(['idCod'], ee.Reducer.first()).unmask(0) 
            
            # efetuar a mudança para floresta 
            rasterSpatialYear = rasterSpatialYear.where(cobertYY.updateMask(mask_florest).eq(3).And(rasterSpatialYear.eq(4)), 3)

        ## removendo as confussões de floresta com água
        regra = rasterSpatialYear.eq(33).And(cobertYY.neq(33))
        rasterSpatialYear = rasterSpatialYear.where(regra, cobertYY)

        ## removendo as confussões com solo 
        regra = rasterSpatialYear.eq(22).And(cobertYY.eq(21).Or(cobertYY.eq(15)))
        rasterSpatialYear = rasterSpatialYear.where(regra, 21)

        class_output = class_output.addBands(rasterSpatialYear.rename(banda_activa))  


    name_exp = f"filterMG_BACIA_{name_bacia}_GTB_V{param['versionOut']}"
    class_output = (class_output.updateMask(bacia_raster)
                .select(lst_yy_class)
                .set(
                    'version', param['versionOut'], 
                    'biome', 'CAATINGA',
                    'source', 'geodatin',
                    'model', "GTB",
                    'type_filter', 'gap_fill',
                    'collection', '3.0',
                    'id_bacias', name_bacia,
                    'sensor', 'Sentinel',
                    'system:footprint', geomBacia
                ))

    processoExportar(class_output,  name_exp, geomBacia)
    # sys.exit()

listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765',     
]


for cc, idbacia in enumerate(listaNameBacias[:]):   
    print("----- PROCESSING BACIA {} -------".format(idbacia))        
    apply_spatialFilterConn(idbacia)