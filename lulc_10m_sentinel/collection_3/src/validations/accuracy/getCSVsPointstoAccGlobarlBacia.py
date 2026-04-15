#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import os
import sys
import collections
collections.Callable = collections.abc.Callable

from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
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


#========================METODOS=============================
def gerenciador(cont, param):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)
    
    if str(cont) in numberofChange:
        print(f"inicialize in account #{cont} <> {param['conta'][str(cont)]}")
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 
        
        # relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:   
            print(str(lin))         
            # relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    
    cont += 1    
    return cont

cont = 0
# cont = gerenciador(cont, param)


#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, nameT, porAsset):  

    if porAsset:
        if 'project' in nameT:
            asset_ids = param['assetpointLapig24rc']
            nameT = nameT.split("/")[-1]
        else:
            asset_ids = "projects/geo-data-s/assets/accuracy/" + nameT
        optExp = {
          'collection': ROIsFeat, 
          'description': nameT, 
          'assetId': asset_ids        
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nameT + "..!")
    else:
        optExp = {
            'collection': ROIsFeat, 
            'description': nameT, 
            'folder':"ptosAccCol10corr",
            # 'priority': 1000          
            }
        task = ee.batch.Export.table.toDrive(**optExp)
        task.start() 
        print("salvando ... " + nameT + "..!")
        # print(task.status())
    


#nome das bacias que fazem parte do bioma
nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764', '7581', '7625', '7584', '751',     
    '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752', '7691',  
] 

param = {
    'lsBiomas': ['CAATINGA'],
    'asset_bacias': 'projects/ee-solkancengine17/assets/shape/bacias_shp_caatinga_div_49_regions', # asset bacia revisado 
    'assetBiomas' : 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    # 'assetpointLapig23': 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col3_points_w_edge_and_edited_v2', 
    'assetpointLapig23': 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col4_points_w_edge_and_edited_v1',
    'assetpointLapig24rc': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/mapbiomas_85k_col4_points_w_edge_and_edited_v1_Caat',   
    'limit_bacias': "users/CartasSol/shapes/bacias_limit",
    'asset_caat_buffer': 'users/CartasSol/shapes/caatinga_buffer5km',
    # 'assetCol': "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger" ,
    # 'assetCol': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',

    # 'assetFilters': "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger" ,
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/TemporalA',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/TemporalN',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalN',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalA',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
    # 'assetFilters':  'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Frequency',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_int',
    # 'assetFilters':   'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_int',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_all',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_all',
    'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/transitionTest',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalCC',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/MergerV6',
    # 'asset_Map' : "projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1",
    # 'asset_Map': 'projects/mapbiomas-public/assets/brazil/lulc/collection7_1/mapbiomas_collection71_integration_v1',
    # 'asset_Map' : "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    'asset_Map' : "projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2",
    # 'assetCol6': path_asset + "class_filtered/maps_caat_col6_v2_4",
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,40,41,46,47,48,49,50,62],
    'classNew':  [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,21,21,21,21,21,21, 3,12,21],
    'classesMapAmp':  [3, 4, 3, 3,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,18,18,18,18,18,18, 3,12,18],
    'inBacia': True,
    'anoInicial': 2016,
    'anoFinal': 2023,  # 2019
    'numeroTask': 6,
    'numeroLimit': 2,
    'changeAcount': False,
    'conta' : {
        '0': 'solkanGeodatin'              
    },
    'lsProp': ['ESTADO','LON','LAT','PESO_AMOS','PROB_AMOS','REGIAO','TARGET_FID','UF'],
    "amostrarImg": False,
    'isImgCol': True
}

def change_value_class(feat):
    ## Load dictionary of class
    dictRemap =  {
        "FORMAÇÃO FLORESTAL": 3,
        "FORMAÇÃO SAVÂNICA": 4,        
        "MANGUE": 3,
        "RESTINGA HERBÁCEA": 3,
        "FLORESTA PLANTADA": 21,
        "FLORESTA INUNDÁVEL": 3,
        "CAMPO ALAGADO E ÁREA PANTANOSA": 12,
        "APICUM": 12,
        "FORMAÇÃO CAMPESTRE": 12,
        "AFLORAMENTO ROCHOSO": 22,
        "OUTRA FORMAÇÃO NÃO FLORESTAL":12,
        "PASTAGEM": 21,
        "CANA": 21,
        "LAVOURA TEMPORÁRIA": 21,
        "LAVOURA PERENE": 21,
        "MINERAÇÃO": 22,
        "PRAIA E DUNA": 22,
        "INFRAESTRUTURA URBANA": 22,
        "VEGETAÇÃO URBANA": 22,
        "OUTRA ÁREA NÃO VEGETADA": 22,
        "RIO, LAGO E OCEANO": 33,
        "AQUICULTURA": 33,
        "NÃO OBSERVADO": 27  
    }
    pts_remap = ee.Dictionary(dictRemap) 

    prop_select = [
        'BIOMA', 'CARTA','DECLIVIDAD','ESTADO','JOIN_ID','PESO_AMOS'
        ,'POINTEDITE','PROB_AMOS','REGIAO','TARGET_FID','UF', 'LON', 'LAT']
    
    feat_tmp = feat.select(prop_select)
    for year in range(param['anoInicial'], param['anoFinal'] + 1):
        nam_class = "CLASS_" + str(year)
        set_class = "CLASS_" + str(year)
        valor_class = ee.String(feat.get(nam_class))
        feat_tmp = feat_tmp.set(set_class, pts_remap.get(valor_class))
    
    return feat_tmp


def getPointsAccuraciaFromIC (imClass, isImgCBa, ptosAccCorreg, thisvers, exportByBasin, exportarAsset, subbfolder):
    """
    This function is responsible for collecting points of accuracy from a given image classification.

    Parameters:
    imClass (ee.Image): The image classification to collect points from.
    isImgCBa (bool): Whether to filter the image classification by bacia.
    ptosAccCorreg (ee.FeatureCollection): The points of accuracy to collect.
    modelo (str): The model used for classification.
    version (int): The version of the classification.
    exportByBasin (bool): Whether to export the collected points by bacia.
    exportarAsset (bool): Whether to export the collected points as an asset.
    subbfolder (str): The subfolder to include in the exported file name.

    export: (ee.FeatureCollection): the points of values label from classification and reference 
    Returns:
    None
    """
    
    print("Número de pontos ", ptosAccCorreg.size().getInfo())
    if isImgCBa:
        try:
            print("número de imagens da coleção ", imClass.size().getInfo())
        except:
            print("imagem única ", imClass.bandNames().getInfo())
            isImgCBa = False

    #lista de anos
    list_anos = [str(k) for k in range(param['anoInicial'], param['anoFinal'] + 1)]
    list_bandas = [f"classification_{k}" for k in range(param['anoInicial'], param['anoFinal'] + 1)]
    # print('lista de anos', list_anos)
    # update properties 
    lsAllprop = param['lsProp'].copy()
    for ano in list_anos:
        band = 'CLASS_' + str(ano)
        lsAllprop.append(band)

    # featureCollection to export colected 
    pointAll = ee.FeatureCollection([])
    ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

    sizeFC = ee.Number(0 )
    
    for cc, _nbacia in enumerate(nameBacias[:]):    
        # nameImg = 'mapbiomas_collection80_Bacia_v' + str(version) 
        print(f"-------  📢📢 processando img #  {cc} na bacia {_nbacia}  🫵 -------- ")
        baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto4', _nbacia)).geometry()    
        geomRecBacia = ee.FeatureCollection([ee.Feature(ee.Geometry(baciaTemp), {'id_codigo': 1})])
        maskRecBacia = geomRecBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0) 
        
        pointTrueTemp = ptosAccCorreg.filterBounds(baciaTemp)
        ptoSize = pointTrueTemp.size()#.getInfo()
        print(cc, " - bacia - ", _nbacia, " points Reference ")  
        sizeFC = sizeFC.add(ptoSize)
    
        if isImgCBa:
            mapClassBacia = imClass.filter(ee.Filter.eq('id_bacias', _nbacia))
            print(f"Número de image na Bacia {_nbacia} => {mapClassBacia.size().getInfo()}")
            mapClassBacia = ee.Image(mapClassBacia.first())
        else:
            print(" 🚨  reading the one image ")
            mapClassBacia = ee.Image().byte()            
            for band_act in list_bandas:
                mapClassBacia = mapClassBacia.addBands(
                                    ee.Image(imClass).updateMask(maskRecBacia)
                                    .remap(param['classMapB'], param['classNew']).rename(band_act)
                )
            mapClassBacia = mapClassBacia.select(list_bandas)
            # print(mapClassBacia.bandNames().getInfo())
            # sys.exit()
        try:
            #
            pointAccTemp = mapClassBacia.unmask(0).sampleRegions(
                collection= pointTrueTemp, 
                properties= lsAllprop, 
                scale= 10, 
                geometries= True
            )
            pointAccTemp = pointAccTemp.map(lambda Feat: Feat.set('bacia', _nbacia))
            # print("size of points Acc coletados ", pointAccTemp.size().getInfo())
            pointAll = ee.Algorithms.If(  
                            ee.Algorithms.IsEqual(ee.Number(ptoSize).eq(0), 1),
                            pointAll,
                            ee.FeatureCollection(pointAll).merge(pointAccTemp)
                        )
        except:
            print("⚠️ ERRO WITH LOADING IMAGE MAP 🚨")

    # if not exportByBasin:
    if 'col10' in param['asset_Map']:
        name = 'occTab_corr_Caatinga_Col8_' + str(thisvers) + "_Col8" 
    else:
        name =  f"occTab_corr_Caatinga_{subbfolder}_{thisvers}"
    
    processoExportar(pointAll, name, exportarAsset)
    print()
    print(" 📢 numero de ptos ", sizeFC.getInfo())

    # sys.exit()

if param['changeAcount']:
    gerenciador(0, param)

expPointLapig = False
knowImgcolg = True
param['isImgCol'] = True
param['inBacia'] = True
version = 5
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()
## os pontos só serão aqueles que representam a Caatinga 
caatingaBuffer = ee.FeatureCollection(param['asset_caat_buffer'])

if expPointLapig:
    ptsTrue = ee.FeatureCollection(param['assetpointLapig23']).filterBounds(caatingaBuffer)
    pointTrue = ptsTrue.map(lambda feat: change_value_class(feat))
    print("Carregamos {} points ".format(pointTrue.size().getInfo()))  # pointTrue.size().getInfo()
    print("know the first points ", pointTrue.first().getInfo())
    # sys.exit()
    processoExportar(ptsTrue, param['assetpointLapig24rc'], True)
    processoExportar(pointTrue, param['assetpointLapig24rc'] + '_reclass', True)
else:
    pointTrue = ee.FeatureCollection(param['assetpointLapig24rc'])    
    print("Carregamos {} points ".format(pointTrue.size().getInfo()))  # pointTrue.size().getInfo()
    # print("know the first points ", pointTrue.first().getInfo())



# sys.exit()
########################################################
#   porBacia -----  Image
#              |--  ImageCollection -> min() -> Image
#   porBioma -----  Image
#              |--  ImageCollection -> min() -> Image
#######################################################
subfolder= ''
janela = 3
isFilter = True
if isFilter and ('POS-CLASS' in param['assetFilters']  or 'toExport' in param['assetFilters']):
    subfolder = "_" + param['assetFilters'].split('/')[-1] + f"_Min_v{version}"
else:
    subfolder= 'cobertura'

if param['isImgCol']:
    if isFilter:
        print("reading filters ")
        mapClass = (ee.ImageCollection(param['assetFilters'])
                        .filter(ee.Filter.eq('version', version))
        )
        print("show versions ", mapClass.aggregate_histogram('version').getInfo())

        if 'Temporal' in param['assetFilters']:
            mapClass = mapClass.filter(ee.Filter.eq('janela', janela))
            subfolder += f'_J{janela}'
            print(mapClass.first().get('system:index').getInfo())

        if 'Gap-fill' in param['assetFilters']:
            mapClass = mapClass.filter(ee.Filter.eq('version', version))

    else:
        print("reading  classifications  ")
        mapClass = (ee.ImageCollection(param['assetCol'])   # .select(lstBands)
                        .filter(ee.Filter.eq('version', version))
        )
    # print(mapClass.first().getInfo())
    getid_bacia = mapClass.first().get('id_bacias').getInfo()
    if not getid_bacia:
        getid_bacia = mapClass.first().get('id_bacias').getInfo()
    print(f"we load bacia {getid_bacia}")
    
    # sys.exit()
    if knowImgcolg:
        print(f"versions quantity = {mapClass.aggregate_histogram('version').getInfo()}")

    if getid_bacia:         
        nameBands = 'classification'
        prefixo = ""
        propModel = 'classifier'
        
        print(f"########## 🔊 FILTERED BY VERSAO {version} 🔊 ###############") 
        mapClass = mapClass.filter(ee.Filter.eq('version', version))
        sizeimgCol = mapClass.size().getInfo()
        # refazer pelo minimo 
        # mapClass = mapClass.min() 

        print(f"===  🚨 # de mapas bacias na ImageCollection {sizeimgCol} no modelo GTB ===== {subfolder}") 
        # sys.exit()               
        if sizeimgCol > 0:
            # getPointsAccuraciaFromIC (imClass, isImgCBa, ptosAccCorreg, modelo, version, exportByBasin, exportarAsset)
            # imClass, isImgCBa, ptosAccCorreg, modelo, version, exportByBasin, exportarAsset, subbfolder
            getPointsAccuraciaFromIC (mapClass, True, pointTrue, version, False, False,  subfolder)

    else:
        print(f"########## 🔊 FILTERED BY VERSAO {version} 🔊 ###############")              
        mapClassYY = mapClass.filter(ee.Filter.eq('version', version))
        print(" 🚨 número de mapas bacias ", mapClass.size().getInfo())
        # print(mapClass.first().getInfo())
        # sys.exit()
        immapClassYY = ee.Image().byte()
        for yy in range(param['anoInicial'], param['anoFinal'] + 1):
            nmIm = 'CAATINGA-' + str(yy) + '-' + str(version)
            nameBands = 'classification_' + str(yy)
            imTmp = mapClassYY.filter(ee.Filter.eq('system:index', nmIm)).first().rename(nameBands)
            if yy == param['anoInicial']:
                immapClassYY = imTmp.byte()
            else:
                immapClassYY = immapClassYY.addBands(imTmp.byte())
        
        ### imageCollection converted in image Maps
        ### call to function samples  #######
        getPointsAccuraciaFromIC(immapClassYY, False, pointTrue, '', '', True, False, subfolder)

else:
    print("########## 🔊 LOADING MAP RASTER ###############")
    mapClassRaster = ee.Image(param['asset_Map']).byte()
    ### call to function samples  #######
    #                            imClass, isImgCBa, ptosAccCorreg, modelo, version, exportByBasin, exportarAsset,subbfolder
    subfolder = param['asset_Map'].split("/")[-1]
    getPointsAccuraciaFromIC(mapClassRaster, False, pointTrue, '1', True, False, subfolder)

