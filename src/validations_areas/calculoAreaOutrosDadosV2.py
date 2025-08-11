#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#  SCRIPT DE CALCULO DE AREA POR AREAS PRIORITARIAS DA CAATINGA
#  Produzido por Geodatin - Dados e Geoinformacao
#  DISTRIBUIDO COM GPLv2

#   Relação de camadas para destaques:
#   limite bioma Caatinga 
#   Novo limite do semiarido 2024
#   Camadas Raster:
#       Fogo
#       Agua
#       Alertas
#       Vegetação secundaria 

'''

import ee
import os 
# import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount) #
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

param = {
    'asset_Cover_Col10': 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification',  
    'asset_transicao': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_transitions_v1',
    'asset_annual_water': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_water_collection2_annual_water_coverage_v1',
    'asset_desf_vegsec': 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/DEFORESTATION/deforestation-secondary-vegetation',
    'asset_vegsec_age': ' projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_secondary_vegetation_age_v1',
    'asset_irrigate_agro': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_irrigated_agriculture_v1',
    "asset_semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
    "asset_biomas_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
    "asset_biomas_raster" : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'asset_fire_annual': 'projects/mapbiomas-public/assets/brazil/fire/collection3/mapbiomas_fire_collection3_annual_burned_coverage_v1',
    'asset_fire_acumulado': 'projects/mapbiomas-public/assets/brazil/fire/collection3/mapbiomas_fire_collection3_accumulated_burned_v1',
    'asset_vigor_pastagem': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_pasture_quality_v1',
    "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
    "br_estados_vector": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
    "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
    'scale': 30,
    # 'driverFolder': 'AREA-EXP-SEMIARIDO-24',
    'driverFolder': 'AREA-EXP-CAATINGA-24',
}

lst_nameAsset = [    
    # 'asset_annual_water',
    'asset_desf_vegsec',
    # 'asset_irrigate_agro',
    # 'asset_fire_annual',
    # 'asset_fire_acumulado'
    # 'asset_vegsec_age',
    # 'asset_vigor_pastagem'
]

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

    pixelArea = pixelArea.addBands(image.rename('classe'))#.clip(geometry)#.addBands(
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
# pixelArea, imgWater, limitGeometria, pref_bnd, nomegeometria, byYears, nameCSV
def iterandoXanoImCruda(layer_analises, shpBiomeGeom, name_export):
                      
    mask_Geometry = ee.FeatureCollection(shpBiomeGeom).reduceToImage(['id_codigo'], ee.Reducer.first())  
    shpBiomeGeom = ee.FeatureCollection(shpBiomeGeom).geometry() 
    
    imgAreaRef = (ee.Image.pixelArea().divide(10000)
                    .updateMask(mask_Geometry)                    
                )
    areaGeral = ee.FeatureCollection([])      
    print("Loadding image Cobertura Coleção 10 " )

    imgMapp = ee.Image(layer_analises)
    # print(imgMapp.bandNames().getInfo())
    # sys.exit()
    shpStateGeom = ee.FeatureCollection(param["br_estados_vector"]).map(lambda feat: feat.set('id_codigo', 1)) 
    lstEstCruz = [21,22,23,24,25,26,27,28,29,31,32]

    # print("---- SHOW ALL BANDS FROM MAPBIOKMAS MAPS -------\n ", imgMapp.bandNames().getInfo())
    dateInit = 1985
    dateEnd = 2024
    # if "_desf_veg_" in name_export:
    #     dateInit = 1986
    # elif 'water' in name_export:
    #     dateEnd = 2024

    for estadoCod in lstEstCruz[:]:
        areaGeral = ee.FeatureCollection([]) 
        print(f"processing Estado {dictEst[str(estadoCod)]} with code {estadoCod}")
        # maskRasterEstado = estados_raster.eq(estadoCod)
        shpStateGeomS = shpStateGeom.filter(ee.Filter.eq('CD_GEOCUF', str(estadoCod)))
        print("loaded geometry estado ", shpStateGeomS.size().getInfo())
        maskRasterEstado = shpStateGeomS.reduceToImage(['id_codigo'], ee.Reducer.first())
        shpStateGeomS = shpStateGeomS.geometry().intersection(shpBiomeGeom)
        rasterMapEstado = imgMapp.updateMask(maskRasterEstado)
        imgAreaRefEstado = imgAreaRef.updateMask(maskRasterEstado)
        # sys.exit()

        for year in range(dateInit, dateEnd + 1):          
            bandAct = "classification_" + str(year)
            newimgMap = rasterMapEstado.select(bandAct)
            print(f" ========  🫵 processing year {year} for mapbiomas map ===== {bandAct}")
            areaTemp = calculateArea (newimgMap, imgAreaRefEstado, shpStateGeomS)        
            areaTemp = areaTemp.map( lambda feat: feat.set(
                                                'year', year,                                                 
                                                'estado_name', dictEst[str(estadoCod)], # colocar o nome do estado
                                                'estado_codigo', estadoCod                           
                                            ))
            areaGeral = areaGeral.merge(areaTemp)
        
        nameCSV =  name_export + "_" + str(estadoCod)
        processoExportar(areaGeral, nameCSV)     
        # sys.exit() 
 
       
    


# pixelArea, imgWater, limitGeometria, pref_bnd, nomegeometria, byYears, nameCSV
def anoImCruda(imgAreaRef, mapaDelimitado, limite, preficoBnd, nameregion, nameExport, SiglaEst, idEstado):
    
    imgAreaRef = imgAreaRef.clip(limite)
    areaGeral = ee.FeatureCollection([])      
    print("Loadding image Cobertura Coleção 10 " )
    bandActive = ''
    intervalo = ''
    imgMapp = ee.Image(mapaDelimitado).clip(limite)
    if 'queimadas_accumalada' in nameExport:
        bandActive = "fire_accumulated_1986_2023"
        intervalo = '1986_2023'

    imgMapp = imgMapp.select(bandActive)  
    # print("---- SHOW ALL BANDS FROM MAPBIOKMAS MAPS -------\n ", imgMapp.bandNames().getInfo())

    areaTemp = calculateArea (imgMapp, imgAreaRef, limite)        
    areaTemp = areaTemp.map( lambda feat: feat.set(
                                        'year', 'intervalo', 
                                        'camada', preficoBnd[:-2],
                                        'region', nameregion                                               
                                    ))

    nameCSV = "stat_" + nameExport
    processoExportar(areaTemp, nameCSV)       



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
palette= {
    "0": '#ffffff', # 0: No data
    "1": '#faf5d1', # 1: Anthropogenic
    "2": '#3f7849', # 2: Primary Vegetation
    "3": '#5bcf20', # 3: Secondary Vegetation
    "4": '#ea1c1c', # 4: Suppression of Primary Vegetation
    "5": '#b4f792', # 5: Recovery to Secondary Vegetation
    "6": '#fe9934', # 6: Suppression of Secondary Vegetation
    "7": '#303149'  # 7: Other transitions
}
dictEstSigla = {
    '21': 'MA',
    '22': 'PI',
    '23': 'CE',
    '24': 'RN',
    '25': 'PB',
    '26': 'PE',
    '27': 'AL',
    '28': 'SE',
    '29': 'BA',
    '31': 'MG',
    '32': 'ES'
}
dictEst = {
    '21': 'MARANHÃO',
    '22': 'PIAUÍ',
    '23': 'CEARÁ',
    '24': 'RIO GRANDE DO NORTE',
    '25': 'PARAÍBA',
    '26': 'PERNAMBUCO',
    '27': 'ALAGOAS',
    '28': 'SERGIPE',
    '29': 'BAHIA',
    '31': 'MINAS GERAIS',
    '32': 'ESPÍRITO SANTO'
}
lstEstCruz = [21,22,23,24,25,26,27,28,29,31,32];

estados_raster = ee.Image(param["br_estados_raster"])
estados_shp = ee.FeatureCollection(param["br_estados_vector"])

exportar = False
byYears = False
# iterandoXanoImCruda(imgAreaRef, mapaDelimitado, limite, preficoBnd, nameregion):
sobreNomeGeom = "_Caatinga"
lst_limit = ['Caatinga','estados','Semiarido'] # 'estados','Caatinga', 'Semiarido'
print(' limite caatinga carregado ')

select_Caatinga = True
for name_lim in lst_limit[:1]: 

    if name_lim == 'Caatinga':
        limitGeometria = ee.FeatureCollection(param["asset_biomas_250"])
        limitGeometria = limitGeometria.filter(ee.Filter.eq("CD_Bioma", 2))

    elif name_lim == 'Semiarido':
        limitGeometria = ee.FeatureCollection(param["semiarido2024"])
    else:
        limitGeometria = ee.FeatureCollection(param["br_estados_vector"])

    print("=============== limite a Macro Selecionado ========== ", limitGeometria.size().getInfo())
    # limitGeometria = limitGeometria.geometry()
    limitGeometria = limitGeometria.map(lambda feat: feat.set('id_codigo', 1))

    id_est = " "
    for assetName in lst_nameAsset:        
        print("---- PROCESSING MAPS ", assetName)
        # sys.exit()
        if assetName == 'asset_annual_water':
            print("---- PROCESSING MAPS WATER ---------------")
            pref_bnd = "annual_water_coverage_"  
            nameCSV = f"area_class_water_{name_lim}"   
            imgWater = ee.Image(param["asset_annual_water"])#.updateMask(raster_base)       
            imgWaterEst = imgWater
            csv_table, exportar = iterandoXanoImCruda( imgWaterEst, limitGeometria, nameCSV)        

        elif assetName == 'asset_desf_vegsec':
            print("---- PROCESSING MAPS VEGETAÇÃO SECUNDARIA  ---------------")
            pref_bnd = "classification_"
            nameCSV = f"area_class_desf_veg_secundaria_{name_lim}" 
            version = '0-7-tra-3-2'
            # mapsdesfVegSec = ee.Image(param["asset_desf_vegsec"])#.updateMask(raster_base)
            mapsdesfVegSec = (ee.ImageCollection(param["asset_desf_vegsec"])
                                .filter(ee.Filter.eq('version', version)).mosaic())
            # mapsdesfVegSecEst = mapsdesfVegSec
            iterandoXanoImCruda(mapsdesfVegSec, limitGeometria, nameCSV)

        elif assetName == 'asset_irrigate_agro':
            print("---- PROCESSING MAPS AREAS IRRIGADAS ---------------")
            pref_bnd = "irrigated_agriculture_"
            nameCSV = f"area_class_irrigated_{name_lim}"
            mapsIrrigate = ee.Image(param["asset_irrigate_agro"])#.updateMask(raster_base)
            mapsIrrigateEst = mapsIrrigate
            csv_table, exportar = iterandoXanoImCruda(mapsIrrigateEst, limitGeometria, nameCSV)

        elif assetName == 'asset_fire_annual':
            print("---- PROCESSING MAPS AREAS QUEIMADAS ---------------")
            pref_bnd = f"burned_area_{name_lim}"
            nameCSV = f"area_class_queimadas_{name_lim}" 
            mapsFire = ee.Image(param["asset_fire_annual"])#.updateMask(raster_base)
            mapsFireEst = mapsFire
            csv_table, exportar = iterandoXanoImCruda(mapsFireEst, limitGeometria, nameCSV)

        elif assetName == 'asset_fire_acumulado':
            print("---- PROCESSING MAPS AREAS QUEIMADAS ---------------")
            pref_bnd = "burned_area_acc"
            nameCSV = f"area_class_queimadas_accumalada_{name_lim}" 
            mapsFireAcc = ee.Image(param["asset_fire_acumulado"])#.updateMask(raster_base)
            mapsFireAccEst = mapsFireAcc
            anoImCruda(mapsFireAccEst, limitGeometria, nameCSV)

        elif assetName == 'asset_vegsec_age':
            print("---- PROCESSING MAPS AREAS QUEIMADAS ---------------")
            pref_bnd = "vegsec_age"
            nameCSV = f"area_class_vegsec_age_{name_lim}"
            mapsVegSecAge = ee.Image(param["asset_vegsec_age"])#.updateMask(raster_base)
            mapsVegSecAge = mapsVegSecAge
            anoImCruda(mapsVegSecAge, limitGeometria, nameCSV)
