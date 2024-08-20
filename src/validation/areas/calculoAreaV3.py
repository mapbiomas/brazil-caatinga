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

#nome das bacias que fazem parte do bioma
nameBacias = [
    '741', '7421','7422','744','745','746','751','752','7492',
    '753', '754','755','756','757','759','7621','7622','763', 
    '764','765','766','771','772', '7741','7742','775', '773',
    '776','76111','76116','7612','7613','7615','777','758',
    '778','7616','7617','7618', '7619', '767', '758', '773','7614',
] 
# nameBacias = [
#     '763','7618'
# ]
classMapB = [ 0, 3, 4, 5, 6, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =  [27, 3, 4, 3, 3, 3,12,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21]
param = {
    # 'inputAsset': path + 'class_filtered_Tp',   
    'assetCol': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVX" ,
    'assetColprob': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVY" ,
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV3',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel',
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/TemporalV3',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV3',
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    # 'asset_Map' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    # 'asset_Map': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'collection': '9.0',
    'geral':  True,
    'isImgCol': True,  
    'remapRaster': True,
    'inBacia': True,
    'version': 31,
    'sufixo': '_Cv', 
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'year_inic': 1985,
    'year_end': 2023,
    'driverFolder': 'AREA-EXPORT-COL9', 
    'lsClasses': [3,4,12,15,18,21,22,33],
    'changeAcount': True,
    'numeroTask': 0,
    'numeroLimit': 37,
    'conta' : {
        # '0': 'caatinga04',
        '0': 'solkanGeodatin'
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
        'bestEffort': True,
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)

    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

# pixelArea, imgMapa, bioma250mil

def iterandoXanoImCruda(imgAreaRef, imgMapp, limite):
    imgMapp = imgMapp.clip(limite)
    imgAreaRef = imgAreaRef.clip(limite)
    areaGeral = ee.FeatureCollection([])    
    yearEnd = param['year_end']
    if not param['isImgCol']:
        if 'collection80_' in param['asset_Map']:
            yearEnd -= 1
        elif 'collection71_' in param['asset_Map']:
            yearEnd -= 2
    if param['remapRaster']:
        print(" 🚨 📢 we are to remap the raste 🚨 ")

    for year in range(param['year_inic'], yearEnd + 1):  # 
        bandAct = "classification_" + str(year) 
        if param['remapRaster']:
            mapToCalc = imgMapp.select(bandAct).remap(classMapB , classNew)
            areaTemp = calculateArea (mapToCalc, imgAreaRef, limite)
        else:
            areaTemp = calculateArea (imgMapp.select(bandAct), imgAreaRef, limite)        
            return calculateArea (imgMapp.select(bandAct), imgAreaRef, limite)        
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year))
        areaGeral = areaGeral.merge(areaTemp)      
    
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
lstBands = ['classification_' + str(yy) for yy in range(1985, 2024)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()
knowImgcolg = False
isFilter = True
if isFilter and ('POS-CLASS' in param['assetFilters'] or 'toExport' in param['assetFilters']):
    subfolder = "_" + param['assetFilters'].split('/')[-1] 
else:
    subfolder= ''
# lstVers = [5, 6, 7, 8, 9] # versions classification 
# lstVers = [5, 9] # versions Filters 

version = param['version']
if param['changeAcount']:
    gerenciador(0, param)
pixelArea = ee.Image.pixelArea().divide(10000)
if param['isImgCol']:
    if isFilter:
        imgsMaps = ee.ImageCollection(param['assetFilters'])
        # print('imgsMaps ', imgsMaps.aggregate_histogram('version').getInfo())
        if 'Temporal' in param['assetFilters']:
            # imgsMaps = imgsMaps.filter(ee.Filter.eq('janela', 5))
            subfolder += 'J3'
            print(imgsMaps.size().getInfo())
            # idList = imgsMaps.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
            # for ids in idList:
            #     print("    ", ids)
        if 'Spatial' in param['assetFilters']:
            # imgsMaps = imgsMaps.filter(ee.Filter.eq('filter', 'spatial_use'))
            subfolder += 'su'
            print(imgsMaps.size().getInfo())
            # print()
            # sys.exit()
        if 'Frequency' in param['assetFilters']:
            # neq ==>  'nat'   e  eq ===>  natUso
            # imgsMaps = imgsMaps.filter(ee.Filter.eq('type_filter', 'frequence_natUso'))
            imgsMaps = imgsMaps.filter(ee.Filter.eq('step', 1))
            # print(imgsMaps.size().getInfo())
            # print(imgsMaps.aggregate_histogram('version').getInfo())
            subfolder += 'St1'
        # sys.exit()

    else:
        if int(version) > 6:  # 
            imgsMaps = ee.ImageCollection(param['assetColprob'])# .select(lstBands)
        else:
            imgsMaps = ee.ImageCollection(param['assetCol'])# .select(lstBands)
    
    getid_bacia = imgsMaps.first().get('id_bacia').getInfo()
    print(f"we load bacia {getid_bacia}")
    if knowImgcolg:
        print(f"versions quantity = {imgsMaps.aggregate_histogram('version').getInfo()}")
    if getid_bacia:
        nameBands = 'classification'
        prefixo = ""
        propModel = 'classifier'
        for model in ['GTB']:   # 'GTB', 'RF, 'RF'
            if isFilter:
                propModel = 'model'            
            mapClassMod = imgsMaps.filter(
                            ee.Filter.eq('version', version))#.filter(
                                # ee.Filter.eq(propModel, model))
            # print(mapClassMod.first().getInfo())
            print("show size ImCol ", mapClassMod.size().getInfo())
            # sys.exit()
            print(f"########## 🔊 FILTERED BY VERSION {version} AND MODEL {model} 🔊 ###############") 
            sizeimgCol = mapClassMod.size().getInfo()
            print(" 🚨 número de mapas bacias ", sizeimgCol) 
            nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_" + model +  subfolder + "_vers_" + str(version)
            # sys.exit()               
            if sizeimgCol > 0:                
                for cc, nbacia in enumerate(nameBacias): # nameBacias
                    ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                                        ee.Filter.eq('nunivotto3', nbacia)).geometry()
                    limitInt = bioma250mil.intersection(ftcol_bacias)
                    mapClassBacia = mapClassMod.filter(ee.Filter.eq('id_bacia', nbacia)).first()
                    areaM = iterandoXanoImCruda(pixelArea, mapClassBacia, limitInt) 
                    nameCSVBa = nameCSV + "_" + nbacia 
                    processoExportar(areaM, nameCSVBa, cc)
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
        
        nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_" + model + "_vers_" + str(version)

        for cc, nbacia in enumerate(nameBacias):
            ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                                ee.Filter.eq('nunivotto3', nbacia)).geometry()
            limitInt = bioma250mil.intersection(ftcol_bacias)
            areaM = iterandoXanoImCruda(pixelArea, immapClassYY, limitInt) 
            nameCSVBa = nameCSV + "_" + nbacia 
            processoExportar(areaM, nameCSVBa, cc)
    
else:
    print("########## 🔊 LOADING MAP RASTER FROM IMAGE OBJECT ###############")
    assetPathRead = param['asset_Map'] 
    print(f" ------ {assetPathRead} ---- ")
    nameImg = assetPathRead.split('/')[-1].replace('mapbiomas_collection', '')
    # reading the image raster maps collections 8.0 or 7.1
    mapClassRaster = ee.Image(assetPathRead).byte()
    print("know the bands names from mapClassRaster ", mapClassRaster.bandNames().getInfo())
    ### call to function samples  #######
    nameCSV = 'areaXclasse_' + param['biome'][:4] + "_Col" + nameImg

    # sys.exit()
    for cc, nbacia in enumerate(nameBacias):
        ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                            ee.Filter.eq('nunivotto3', nbacia)).geometry()
        limitInt = bioma250mil.intersection(ftcol_bacias)
        areaM = iterandoXanoImCruda(pixelArea, mapClassRaster, limitInt) 
        nameCSVBa = nameCSV + "_" + nbacia
        if param['remapRaster']:
            nameCSVBa += "_remap"
        print(f" #{cc}  we processing ==> {nameCSVBa}   -- ") 
        processoExportar(areaM, nameCSVBa, cc)



    


