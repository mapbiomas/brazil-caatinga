#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import copy
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
# sys.exit()
try:
    ee.Initialize(project= projAccount) #
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

#nome das bacias que fazem parte do bioma
nameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '765',
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '7622', '746','7712', '752',  
] 
# nameBacias = [
#     '763','7618'
# ]
classMapB = [ 0, 3, 4, 5, 6, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =  [27, 3, 4, 3, 3, 3,12,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21]
param = {
    # 'inputAsset': path + 'class_filtered_Tp',   
    # 'assetCol': "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger" ,
    # 'assetCol': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_int',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_all',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/transition',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/TemporalA',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/TemporalN',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalN',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalA',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_int',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Frequency',
    # 'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_all',
    'assetFilters': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Merger',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    # 'asset_Map' : "projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1",
    # 'asset_Map': 'projects/mapbiomas-public/assets/brazil/lulc/collection7_1/mapbiomas_collection71_integration_v1',
    'asset_Map' : "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    # 'asset_Map' : "projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2",
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_bacias': 'projects/ee-solkancengine17/assets/shape/bacias_shp_caatinga_div_49_regions',
    "asset_biomas_raster" : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'collection': '2S2',
    'geral':  True,
    'isImgCol': True,  
    'remapRaster': True,
    'inBacia': True,
    'version': 5,
    'janela': 5,
    'sufixo': '_Cv', 
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 10,
    'year_inic': 2016,
    'year_end': 2025,
    'driverFolder': 'AREA-EXPORT-COL2S2', 
    'lsClasses': [3,4,12,15,18,21,22,33],
    'changeAcount': False,
    'numeroTask': 0,
    'numeroLimit': 37,
    'conta' : {
        # '0': 'caatinga04',
        '0': 'solkanGeodatin'
    }
}

# arq_area =  arqParamet.area_bacia_inCaat
relatorios = open("relatorioTaskXContas.txt", 'a+')
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
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:            
            relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
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
    # featC = ee.FeatureCollection([ee.Feature(geometry, {'class', 1})])
    # raster_mask = featC.reduceToImage(['class'], ee.Reducer.first())
    pixelArea = pixelArea.addBands(image.rename('classe'))#.updateMask(raster_mask)        
    # print(pixelArea.bandNames().getInfo())                        
    reducer = ee.Reducer.sum().group(1, 'classe')
    optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': param['scale'],
        'bestEffort': True,
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)
    # print(areas.getInfo())
    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

# pixelArea, imgMapa, bioma250mil

def iterandoXanoImCruda(imgMapp, limite):
    
    geomRecBacia = ee.FeatureCollection([ee.Feature(ee.Geometry(limite), {'id_codigo': 1})])
    maskRecBacia = geomRecBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0) 
    imgMapp = imgMapp.updateMask(maskRecBacia)
    imgAreaRef = ee.Image.pixelArea().divide(10000).updateMask(maskRecBacia)

    areaGeral = ee.FeatureCollection([])    
    yearEnd = param['year_end']
    if not param['isImgCol']:
        if 'collection90_' in param['asset_Map']:
            yearEnd -= 1
        if 'collection80_' in param['asset_Map']:
            yearEnd -= 2
        elif 'collection71_' in param['asset_Map']:
            yearEnd -= 3

    if param['remapRaster']:
        print(" 🚨 📢 we are to remap the raste 🚨 ")

    for year in range(param['year_inic'], yearEnd + 1):  # 
        bandAct = "classification_" + str(year) 
        if param['remapRaster']:
            # print(" processing banda activa  >>>> ", bandAct)
            mapToCalc = imgMapp.select(bandAct).remap(classMapB , classNew)
            # print(mapToCalc.bandNames().getInfo())
            areaTemp = calculateArea (mapToCalc.rename('classe'), imgAreaRef, limite)
            # print(areaTemp.getInfo())
        else:            
            areaTemp = calculateArea (imgMapp.select(bandAct), imgAreaRef, limite)        
            return calculateArea (imgMapp.select(bandAct), imgAreaRef, limite)        
        # sys.exit()
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year ))
        areaGeral = areaGeral.merge(areaTemp)      
    # sys.exit()
    return areaGeral

        
#exporta a imagem classificada para o asset
def processoExportar(areaFeat, nameT, ipos):      
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': param["driverFolder"],
        #   'priority': 700        
        }    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print(f"🔉 {ipos} salvando ...📲   {nameT} ... ")      

#testes do dado
# https://code.earthengine.google.com/8e5ba331665f0a395a226c410a04704d
# https://code.earthengine.google.com/306a03ce0c9cb39c4db33265ac0d3ead
# get raster with area km2st.write("tenemos um analises aqui Area")
lstBands = ['classification_' + str(yy) for yy in range(2016, 2026)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()
knowImgcolg = False
isFilter = True
if isFilter and ('POS-CLASS' in param['assetFilters'] or 'toExport' in param['assetFilters']):
    subfolder = "_" + param['assetFilters'].split('/')[-1] + "_min"
    print(" subfolder >> ", subfolder)
else:
    subfolder= ''
# lstVers = [5, 6, 7, 8, 9] # versions classification 
# lstVers = [5, 9] # versions Filters 


account = 0
if param['changeAcount']:
    account = gerenciador(0)

numebacias = len(nameBacias) # save o número de bacias 
if param['isImgCol']:
    print("-------- processing isImgCol -----")
    if isFilter:
        imgsMaps = (ee.ImageCollection(param['assetFilters'])
                        .filter(ee.Filter.eq('version', param['version']))
        )
        print('imgsMaps ', imgsMaps.aggregate_histogram('version').getInfo())

        if 'Temporal' in param['assetFilters']:
            imgsMaps = imgsMaps.filter(ee.Filter.eq('janela', param['janela']))
            subfolder += f"J{param['janela']}"
            print(f"apply filter Temporal com janela {param['janela']}, depois >> ", imgsMaps.size().getInfo())
            # sys.exit()
            # idList = imgsMaps.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
            # for ids in idList:
            #     print("    ", ids)
        if 'Spatialu' in param['assetFilters']:
            # imgsMaps = imgsMaps.filter(ee.Filter.eq('filter', 'spatial_use'))
            subfolder += 'su'
            print(imgsMaps.size().getInfo())
            # print()
            # sys.exit()
        # if 'Frequency' in param['assetFilters']:
        #     # neq ==>  'nat'   e  eq ===>  natUso
        #     # imgsMaps = imgsMaps.filter(ee.Filter.eq('type_filter', 'frequence_natUso'))
        #     imgsMaps = imgsMaps.filter(ee.Filter.eq('step', 1))
        #     # print(imgsMaps.size().getInfo())
        #     # print(imgsMaps.aggregate_histogram('version').getInfo())
        #     subfolder += 'St1'
        # sys.exit()
    else:
        imgsMaps = (ee.ImageCollection(param['assetCol'])
                        .filter(ee.Filter.eq('version', param['version']))
        )
        # .select(lstBands)
    print(f">>> we load {imgsMaps.size().getInfo()} in the image collection")
    getid_bacia = imgsMaps.first().get('id_bacias').getInfo()
    if not getid_bacia:
        getid_bacia = imgsMaps.first().get('id_bacias').getInfo()
    print(f"we load bacia {getid_bacia} as test")
    # print(imgsMaps.first().bandNames().getInfo())
    # sys.exit()
    if knowImgcolg:
        print(f"versions quantity = {imgsMaps.aggregate_histogram('version').getInfo()}")
    if getid_bacia:
        nameBands = 'classification'
        prefixo = ""
        propModel = 'classifier'       
        # if isFilter:
        #     propModel = 'model'            
        mapClassMod = imgsMaps.filter(ee.Filter.eq('version', param['version']))                           
        # print(mapClassMod.first().getInfo())
        print("show size ImCol ", mapClassMod.size().getInfo())
        # sys.exit()
        print(f"########## 🔊 FILTERED BY VERSION {param['version']}  🔊 ###############") 
        sizeimgCol = mapClassMod.size().getInfo()
        print(" 🚨 número de mapas bacias ", sizeimgCol) 
        nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] +  subfolder + "_vers_" + str(param['version'])
        print("iremos a exportar com ", nameCSV)
        # sys.exit()               
        if sizeimgCol > 0: 
            area_mapsGeral = ee.FeatureCollection([])               
            for cc, nbacia in enumerate(nameBacias): # nameBacias
                print(f"# {cc + 1}/{numebacias} +++++++++++++++ bacia {nbacia} ++++++++++")
                ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                                    ee.Filter.eq('nunivotto4', nbacia)).geometry()
                limitInt = bioma250mil.intersection(ftcol_bacias) 

                # mapClassBacia = mapClassMod.filter(ee.Filter.eq('id_bacias', nbacia)).first()  
                mapClassBacia = mapClassMod.min()
                # print("     ", mapClassBacia.bandNames().getInfo())       
                # print("area da bacia = ", round(ftcol_bacias.area().getInfo() / 10000, 2))
                # print(" area intersectada = ", round(limitInt.area().getInfo() / 10000, 2))

                # sys.exit()           
                areaM = iterandoXanoImCruda(mapClassBacia, limitInt) 
                areaM = ee.FeatureCollection(areaM).map(lambda feat: feat.set('id_bacia', nbacia))
                area_mapsGeral = area_mapsGeral.merge(areaM)
            # nameCSVBa = nameCSV + "_" + nbacia 
            processoExportar(area_mapsGeral, nameCSV, cc + 1)
    else:
        print(f"########## 🔊 FILTERED BY VERSAO {param['version']} 🔊 ###############")              
        mapClassYY = imgsMaps.filter(ee.Filter.eq('version', param['version']))
        print(" 🚨 número de mapas bacias ", imgsMaps.size().getInfo())
        immapClassYY = ee.Image().byte()
        for yy in range(1985, 2025):
            nmIm = 'CAATINGA-' + str(yy) + '-' + str(param['version'])
            nameBands = 'classification_' + str(yy)
            imTmp = mapClassYY.filter(ee.Filter.eq('system:index', nmIm)).first().rename(nameBands)
            if yy == 1985:
                immapClassYY = imTmp.byte()
            else:
                immapClassYY = immapClassYY.addBands(imTmp.byte())
        
        nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_" +"_vers_" + str(param['version'])

        for cc, nbacia in enumerate(nameBacias):
            ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                                ee.Filter.eq('nunivotto4', nbacia)).geometry()
            limitInt = bioma250mil.intersection(ftcol_bacias)
            areaM = iterandoXanoImCruda(immapClassYY, limitInt,  f'{cc}/{numebacias}') 
            nameCSVBa = nameCSV + "_" + nbacia 
            processoExportar(areaM, nameCSVBa, cc)
    
else:
    print("########## 🔊 LOADING MAP RASTER FROM IMAGE OBJECT ###############")
    assetPathRead = param['asset_Map'] 
    print(f" ------ {assetPathRead} ---- ")
    nameImg = assetPathRead.split('/')[-1].replace('mapbiomas_collection', '')
    bioCaat = ee.Image(param['asset_biomas_raster']).eq(5)
    # reading the image raster maps collections 9.0, 8.0 or 7.1
    mapClassRaster = ee.Image(assetPathRead).byte().updateMask(bioCaat)
    print("know the bands names from mapClassRaster ", mapClassRaster.bandNames().getInfo())
    ### call to function samples  #######
    nameCSV = 'areaXclasse_' + param['biome'][:4] + "_Col" + nameImg

    # sys.exit()
    area_mapsGeral = ee.FeatureCollection([])
    
    for cc, nbacia in enumerate(nameBacias):
        print( f" #{cc + 1}/{numebacias} +++++++++++++++++++++++++++ BACIA {nbacia} ++++++++++++++++++++++++++++++++++++")
        ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                            ee.Filter.eq('nunivotto4', nbacia)).geometry()
        limitInt = bioma250mil.intersection(ftcol_bacias)
        areaM = iterandoXanoImCruda(mapClassRaster, limitInt) 
        areaM = ee.FeatureCollection(areaM).map(lambda feat: feat.set('id_bacia', nbacia))
        area_mapsGeral = area_mapsGeral.merge(areaM)
    
    # nameCSVBa = nameCSV + "_" + nbacia
    if param['remapRaster']:
        nameCSV += "_remap"
    print(f" #{cc}  we processing ==> {nameCSV}   -- ") 
    processoExportar(area_mapsGeral, nameCSV, cc)



    


