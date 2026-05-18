#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''
import os
import ee 
import gee
import json
import csv
import sys
import collections
collections.Callable = collections.abc.Callable

from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
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

    if str(cont) in numberofChange:
        
        gee.switch_user(param['conta'][str(cont)])
        # gee.init()    
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!')      
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

cont = 0
# cont = gerenciador(cont, param)


#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, nameT, porAsset):  

    if porAsset:
        optExp = {
          'collection': ROIsFeat, 
          'description': nameT, 
          'assetId':"users/mapbiomascaatinga04/" + nameT          
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nameT + "..!")
    else:
        optExp = {
            'collection': ROIsFeat, 
            'description': nameT, 
            'folder':"ptosAccCol9corr",
            # 'priority': 1000          
            }
        task = ee.batch.Export.table.toDrive(**optExp)
        task.start() 
        print("salvando ... " + nameT + "..!")
        # print(task.status())
    


#nome das bacias que fazem parte do bioma
nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
] 
dictFilters = {
    'Gap-fill': 'GF',
    'Spatial': 'SP',
    'Frequency': 'FQ',
    'Temporal': 'TP',
    'toExport': 'CO',
    'grass_Aflor': 'GA',
    'clean_water': 'CW'
}
param = {
    'lsBiomas': ['CAATINGA'],
    'asset_bacias': 'projects/ee-solkancengine17/assets/shape/bacias_shp_caatinga_div_49_regions',
    'assetBiomas' : 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'assetpointLapig23': 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col3_points_w_edge_and_edited_v2', 
    'assetpointLapig24rc': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/mapbiomas_85k_col3_points_w_edge_and_edited_v3_Caat_reclass',   
    'limit_bacias': "users/CartasSol/shapes/bacias_limit",
    'asset_caat_buffer': 'users/CartasSol/shapes/caatinga_buffer5km',
    'assetCol': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX" ,
    # 'assetColprob': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVY" ,
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Spatial',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV3',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/grass_Aflor',
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/clean_water',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Temporal',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/toExport',
    # 'asset_Map' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    # 'assetCol6': path_asset + "class_filtered/maps_caat_col6_v2_4",
    'classMapB': [3, 4, 5, 6, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62],
    'classNew':  [3, 4, 3, 3, 3,12,12,12,21,21,21,21,21,25,25,25,25,33,29,25,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21],
    'classesMapAmp':  [3, 4, 3, 3,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,18,18,18,18,18,18, 3,12,18],
    'inBacia': True,
    'anoInicial': 2016,
    'anoFinal': 2022,  # 2019
    'numeroTask': 6,
    'numeroLimit': 2,
    'changeAcount': True,
    'conta' : {
        '0': 'solkanGeodatin'  
        # '0': 'caatinga04',            
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
        "FLORESTA PLANTADA": 18,
        "FLORESTA INUNDÁVEL": 3,
        "CAMPO ALAGADO E ÁREA PANTANOSA": 12,
        "APICUM": 12,
        "FORMAÇÃO CAMPESTRE": 12,
        "AFLORAMENTO ROCHOSO": 29,
        "OUTRA FORMAÇÃO NÃO FLORESTAL":12,
        "PASTAGEM": 15,
        "CANA": 18,
        "LAVOURA TEMPORÁRIA": 18,
        "LAVOURA PERENE": 18,
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
    for year in range(1985, 2023):
        nam_class = "CLASS_" + str(year)
        set_class = "CLASS_" + str(year)
        valor_class = ee.String(feat.get(nam_class))
        feat_tmp = feat_tmp.set(set_class, pts_remap.get(valor_class))
    
    return feat_tmp


def getPointsAccuraciaFromIC (imClass, isImgCBa, ptosAccCorreg, modelo, thisvers, exportByBasin, exportarAsset,subbfolder):
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
    exportReference =False
    print("Número de pontos ", ptosAccCorreg.size().getInfo())
    print("número de imagens da coleção ", imClass.size().getInfo())
    #lista de anos
    list_anos = [str(k) for k in range(param['anoInicial'], param['anoFinal'] + 1)]
    # print('lista de anos', list_anos)
    # update properties 
    lsAllprop = param['lsProp'].copy()
    for ano in list_anos:
        band = 'CLASS_' + str(ano)
        lsAllprop.append(band)

    # featureCollection to export colected 
    pointAll = ee.FeatureCollection([])
    ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

    sizeFC = 0    
    for cc, _nbacia in enumerate(nameBacias[:]):    
        # nameImg = 'mapbiomas_collection80_Bacia_v' + str(version) 
        print(f"-------  📢📢 processando img #  {cc} na bacia {_nbacia}  🫵 -------- ")
        baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto4', _nbacia)).geometry()    

        pointTrueTemp = ptosAccCorreg.filterBounds(baciaTemp)
        ptoSize = pointTrueTemp.size().getInfo()
        print(cc, " - bacia - ", _nbacia, " points Reference ", ptoSize)  
        sizeFC += ptoSize
    
        if isImgCBa:
            mapClassBacia = imClass.filter(ee.Filter.eq('id_bacia', _nbacia))
            # print(f"Número de image na Bacia {_nbacia} => {mapClassBacia.size().getInfo()}")
            mapClassBacia = ee.Image(mapClassBacia.first())
        else:
            print(" 🚨  reading the one image ")
            mapClassBacia = ee.Image(imClass)
        try:
            #
            pointAccTemp = mapClassBacia.unmask(0).sampleRegions(
                collection= pointTrueTemp, 
                properties= lsAllprop, 
                scale= 30, 
                geometries= True
            )
            # pointAccTemp = pointAccTemp.map(lambda Feat: Feat.set('bacia', _nbacia))
            print("size of points Acc coletados ", pointAccTemp.size().getInfo())
            if exportByBasin:
                if 'col9/' in param['assetCol']:
                    if modelo != '':
                        name = 'occTab_corr_Caatinga_' + _nbacia + "_" + modelo + subbfolder + "_" + str(thisvers) + "_ColS2" 
                    else:
                        name = 'occTab_corr_Caatinga_' + _nbacia + "_" + str(thisvers) + "_ColS2" 
                else:
                    name =  'occTab_corr_Caatinga_' + param['asset_Map'].split('/')[-1]
                # export by basin             
                processoExportar(pointAccTemp, name, exportarAsset)
            else:
                pointAll = ee.Algorithms.If(  
                            ee.Algorithms.IsEqual(ee.Number(ptoSize).eq(0), 1),
                            pointAll,
                            ee.FeatureCollection(pointAll).merge(pointAccTemp)
                        )
        except:
            print("⚠️ ERRO WITH LOADING IMAGE MAP 🚨")

    if not exportByBasin:
        if 'col9/' in param['asset_Map']:
            if modelo != '':
                name = 'occTab_corr_Caatinga_ColS2_' + modelo + "_" + str(thisvers) + "_ColS2" 
            else:
                name = 'occTab_corr_Caatinga_ColS2_' + str(thisvers) + "_ColS2" 
        else:
            name =  'occTab_corr_Caatinga_' + param['asset_Map'].split('/')[-1]
        processoExportar(pointAll, name, exportarAsset)
    print()
    print(" 📢 numero de ptos ", sizeFC)

    # sys.exit()

expPointLapig = False
knowImgcolg = True
param['isImgCol'] = True
param['inBacia'] = True
version = '5'
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()
## os pontos só serão aqueles que representam a Caatinga 
caatingaBuffer = ee.FeatureCollection(param['asset_caat_buffer'])

if expPointLapig:
    ptsTrue = ee.FeatureCollection(param['assetpointLapig24rc']).filterBounds(caatingaBuffer)
    pointTrue = ptsTrue.map(lambda feat: change_value_class(feat))
    print("Carregamos {} points ".format(pointTrue.size().getInfo()))  # pointTrue.size().getInfo()
    print("know the first points ", pointTrue.first().getInfo())
    processoExportar(ptsTrue, param['assetpointLapig'].split("/")[-1], False)
    processoExportar(pointTrue, param['assetpointLapig'].split("/")[-1] + '_reclass', False)
else:
    pointTrue = ee.FeatureCollection(param['assetpointLapig24rc'])    
    print("Carregamos {} points ".format(pointTrue.size().getInfo()))  # pointTrue.size().getInfo()
    print("know the first points ", pointTrue.first().getInfo())

if param['changeAcount']:
    gerenciador(0, param)

# sys.exit()
########################################################
#   porBacia -----  Image
#              |--  ImageCollection -> min() -> Image
#   porBioma -----  Image
#              |--  ImageCollection -> min() -> Image
#######################################################
subfolder= ''
model = "GTB"
isFilter = True
if isFilter and ('POS-CLASS' in param['assetFilters']  or 'toExport' in param['assetFilters']):
    subfolder = "_" + dictFilters[param['assetFilters'].split('/')[-1] ]
else:
    subfolder= ''

if param['isImgCol']:
    if isFilter:
        version = int(version)
        mapClass = (ee.ImageCollection(param['assetFilters'])
                        .filter(ee.Filter.eq('version', version))
        )
        if 'Temporal' in param['assetFilters']:
            mapClass = mapClass.filter(ee.Filter.eq('janela', 4))
            subfolder += 'J4'
            print("número de imagens com filtro ", mapClass.size().getInfo())
            # lstInf = mapClass.reduceColumns(ee.Reducer.toList(), ['id_bacia']).get('list').getInfo()
            # print(lstInf)
            # sys.exit()
        if 'Spatial' in param['assetFilters']:
            # mapClass = mapClass.filter(
            #                 ee.Filter.eq('filter', 'spatial_use'))
            subfolder += 'su'
            print(mapClass.size().getInfo())
            # sys.exit()
        if 'grass_Aflor' in param['assetFilters']:    
            mapClass = mapClass.filter(ee.Filter.eq('type_filter', 'grassland'))
            subfolder += 'Gr'

        # if 'Gap-fill' in param['assetFilters']:
        #     mapClass = mapClass.filter(ee.Filter.eq('version', version))

    else:
        print(" classe basica ")
        mapClass = ee.ImageCollection(param['assetCol']).filter(
                            ee.Filter.eq('version', version))# .select(lstBands)

    getid_bacia = mapClass.first().get('id_bacia').getInfo()
    print(f"we load id bacia {getid_bacia}")
    
    # sys.exit()
    if knowImgcolg:
        print(f"versions quantity = {mapClass.aggregate_histogram('version').getInfo()}")
    if getid_bacia:         
        nameBands = 'classification'
        prefixo = ""
        propModel = 'classifier'

        print(f"########## 🔊 FILTERED BY VERSAO {version} AND MODEL {model} 🔊 ###############") 
        sizeimgCol = mapClass.size().getInfo()
        print(f"===  🚨 número de mapas bacias na Image Collection {sizeimgCol} no modelo  {model} =====") 
        # sys.exit()               
        if sizeimgCol > 0:
            getPointsAccuraciaFromIC(mapClass, True, pointTrue, model, version, True, False,  subfolder)

    else:
        print(f"########## 🔊 FILTERED BY VERSAO {version} 🔊 ###############")              
        mapClassYY = mapClass.filter(ee.Filter.eq('version', version))
        print(" 🚨 número de mapas bacias ", mapClass.size().getInfo())

        immapClassYY = ee.Image().byte()
        for yy in range(1985, 2023):
            nmIm = 'CAATINGA-' + str(yy) + '-' + str(version)
            nameBands = 'classification_' + str(yy)
            imTmp = mapClassYY.filter(ee.Filter.eq('system:index', nmIm)).first().rename(nameBands)
            if yy == 1985:
                immapClassYY = imTmp.byte()
            else:
                immapClassYY = immapClassYY.addBands(imTmp.byte())
        
        ### imageCollection converted in image Maps
        ### call to function samples  #######
        getPointsAccuraciaFromIC (immapClassYY, False, pointTrue, '', '', True, False, subfolder)

else:
    print("########## 🔊 LOADING MAP RASTER ###############")
    mapClassRaster = ee.Image(param['assetCol']).byte()
    ### call to function samples  #######
    # imClass, isImgCBa, ptosAccCorreg, modelo, version, exportByBasin, exportarAsset,subbfolder
    getPointsAccuraciaFromIC (mapClassRaster, False, pointTrue, '', 'Col8', False, True, subfolder)

