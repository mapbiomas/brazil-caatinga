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
import time
import glob
import pandas as pd
import collections
import copy
collections.Callable = collections.abc.Callable

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

keyAssetr = 'integracao'
# keyAssetr = ''

param = {
    # 'inputAsset': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',   
    'inputAsset' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    'assetCol': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVX" ,
    'assetColprob': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVP" ,
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fill',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Spatial',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Temporal',
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Frequency',
    # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    'asset_Map' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    # 'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/aggrements',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Validation/aggrements',
    'classMapB': [3, 4, 5, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45],
    'classNew':  [3, 4, 3, 3,12,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21],
    'geral':  True,
    'isImgCol': True,  
    'inBacia': True,
    'collection': '9.0',
    'version': 13,
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-AGGREMENT-EXPORT', 
    'lsClasses': [3,4,12,21,22,33,29],
    'changeAcount': False,
    'numeroTask': 2,
    'numeroLimit': 420,
    'conta' : {
        '0': 'caatinga01',
        '70': 'caatinga02',
        '140': 'caatinga03',
        '210': 'caatinga04',
        '280': 'caatinga05',        
        '350': 'solkan1201',
        # '420': 'solkanGeodatin'
    }
}

# arq_area =  arqParamet.area_bacia_inCaat
def processoExportarMaps(mapaRF, regionB, nameExp):
    idasset =  param['assetOut'] + "/" + nameExp
    print(" Id Asset to export  >> ", idasset)
    # sys.exit()
    task = ee.batch.Export.image.toAsset(
                                    image= mapaRF, 
                                    description= nameExp, 
                                    assetId= idasset, 
                                    pyramidingPolicy ={".default": "mode"},
                                    region= regionB, #.getInfo()['coordinates']
                                    scale= 30, 
                                    maxPixels= 1e13,
                                    
                                )
    task.start() 
    print("salvando ... " + nameExp + "..!")


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
        'aggrement', item.get('aggrement'),"area", item.get('sum'))
        
    return feature

#########################################################################
####     Calculate area crossing a cover map (deforestation, mapbiomas)
####     and a region map (states, biomes, municipalites)
####      @param image 
####      @param geometry
#########################################################################
# https://code.earthengine.google.com/5a7c4eaa2e44f77e79f286e030e94695
def calculateArea (image, pixelArea, geometry):
    pixelArea = pixelArea.addBands(ee.Image(image).rename('aggrement')).clip(geometry)#.addBands(
                                # ee.Image.constant(yyear).rename('year'))
    reducer = ee.Reducer.sum().group(1, 'aggrement')
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


def sendingAggrementXanotoAsset(imgAreaRef, imgMappCC, nameAggremClass, namBacia, nameImgToexp, myModel, myProcess):
    limite = ee.FeatureCollection(param['asset_bacias']).filter(
                                        ee.Filter.eq('nunivotto3', namBacia)).geometry()
    valClass = int(nameAggremClass.split("_")[-1])
    print(f"name to aggrement class {nameAggremClass}   ==> {valClass}")
    imgMappC8 = ee.Image(param['inputAsset']).clip(limite) 
    imgAreaRef = imgAreaRef.clip(limite)
    mapConcord = None
    exportNameLayer = False
    layerFailsYY = []
    for year in range(1985, 2023):
        imgMapC8YY = imgMappC8.select('classification_' + str(year)).remap(param['classMapB'], param['classNew'])   
        imgMapCCyy = imgMappCC.select('classification_' + str(year)).remap(param['classMapB'], param['classNew'])
        concordante = ee.Image().constant(0).where(
                        imgMapC8YY.eq(valClass).And(imgMapCCyy.eq(valClass)), 1).where(
                            imgMapC8YY.neq(valClass).And(imgMapCCyy.eq(valClass)), 2).where(
                                imgMapC8YY.eq(valClass).And(imgMapCCyy.neq(valClass)), 3)
        concordante = concordante.updateMask(concordante.neq(0)).rename('aggrement_' + str(year))              
        # print(f"processing concordancia {year} ==> {concordante.bandNames().getInfo()}")
        maptemp = ee.Algorithms.If(
                            ee.Algorithms.IsEqual(ee.Number(ee.List(concordante.bandNames().length())).gt(0), 1), 
                            concordante.toByte().selfMask(), 
                            imgMapC8YY.eq(valClass).toByte().selfMask().rename('aggrement_' + str(year))
                        )
        if year == 1985:
            print("  adding year 1985  ")
            mapConcord = copy.deepcopy(ee.Image(maptemp))
        else:
            mapConcord = mapConcord.addBands(maptemp) 

    mapConcord = ee.Image(mapConcord).set(
                        'biome', param['biome'],
                        'id_bacia', namBacia,
                        'version', param['version'],            
                        'classifier', myModel,
                        'process', myProcess,
                        'collection', '9.0',
                        'sensor', 'Landsat',
                        'source', 'geodatin',   
                        'class', valClass
                    )  
    # print(mapConcord.getInfo())
    # print(limite.getInfo()['coordinates'])
    # print("asset = ", param['assetOut'] + "/" + nameImgToexp)
    # print("name ", nameImgToexp)
    try:
        processoExportarMaps(mapConcord, limite, nameImgToexp) # .getInfo()['coordinates']
    except:
        print("classe {nameAggremClass} don´t exits in the region {namBacia}")
        exportNameLayer = True
        return exportNameLayer, nameImgToexp

    return exportNameLayer, nameImgToexp

def iterandoXanoImCrudaCSV(imgAreaRef, imgMappCC, limite, nameAggremClass, namBacia, nomeCSVtable):
    valClass = int(nameAggremClass.split("_")[-1])
    print(f"name to aggrement class {nameAggremClass}   ==> {valClass}")
    imgMappC8 = ee.Image(param['inputAsset']).clip(limite) 
    imgAreaRef = imgAreaRef.clip(limite)
    lstYear = []
    lstArea = []
    lstClasse = []
    for year in range(1985, 2023):
        imgMapC8YY = imgMappC8.select('classification_' + str(year)).remap(param['classMapB'], param['classNew'])   
        imgMapCCyy = imgMappCC.select('classification_' + str(year)).remap(param['classMapB'], param['classNew'])

        concordante = ee.Image(0).clip(limite).where(
                        imgMapC8YY.eq(valClass).And(imgMapCCyy.eq(valClass)), 1).where(
                            imgMapC8YY.neq(valClass).And(imgMapCCyy.eq(valClass)), 2).where(
                                imgMapC8YY.eq(valClass).And(imgMapCCyy.neq(valClass)), 3)
        concordante = concordante.updateMask(concordante.neq(0)).rename('concordancia_' + str(year))              

        areatemp = calculateArea (concordante, imgAreaRef, limite) 
        print(f"Year {year} area temporal  ",) 
        dictArea = areatemp.getInfo()
        dictArea = dictArea['features']
        for dictfeat in dictArea:
            areatmp = dictfeat['properties']['area']
            classeC = dictfeat['properties']['classeConc']
            lstYear.append(year)
            lstArea.append(areatmp)
            lstClasse.append(classeC) 

    dictAreas = {
        'year': lstYear,
        'area': lstArea,
        'classeCoinc': lstClasse,
        'bacia': [namBacia] * len(lstYear),
        'classe': [valClass] * len(lstYear)
    }
    dfArea = pd.DataFrame.from_dict(dictAreas)

    dfArea.to_csv('tableCoincd/' + nomeCSVtable + '.csv', index= False)


def iterandoXanoImCruda(imgAreaRef, nameMappAgg, limite, valClass, namBacia):

    imgAreaRef = imgAreaRef.clip(limite)
    concordante = ee.ImageCollection(param['assetOut']).filter(
                            ee.Filter.eq('system:index', nameMappAgg)).first() 
    # print("show number bands ", concordante.bandNames().getInfo())
    areaGeral = ee.FeatureCollection([])

    for year in range(1985, 2023):
        bandAct = 'aggrement_' + str(year)         
        areatemp = calculateArea (concordante.select(bandAct), imgAreaRef, limite)        
        # print(f"processing year {year} e area {areatemp.getInfo()}")     
        areaTemp = areatemp.map( lambda feat: feat.set('year', int(year), 'bacia', namBacia, 'classe', valClass))  # 
        areaGeral = areaGeral.merge(areaTemp)

    return ee.FeatureCollection(areaGeral) 

        
#exporta a imagem classificada para o asset
def processoExportarSHP(areaFeat, nameT, ciposc):      
    optExp = {
          'collection': ee.FeatureCollection(areaFeat), 
          'description': nameT, 
          'folder': param["driverFolder"]        
        }    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print(f" # {ciposc} salvando ... " + nameT + "..!")      

#testes do dado
# https://code.earthengine.google.com/8e5ba331665f0a395a226c410a04704d
# https://code.earthengine.google.com/306a03ce0c9cb39c4db33265ac0d3ead
# get raster with area km2
lstBands = ['classification_' + str(yy) for yy in range(1985, 2023)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

# gerenciador(0, param)
pixelArea = ee.Image.pixelArea().divide(10000)
exportSta = True
verificarSalvos = True
# lista de imagens de correção com Sentinel Data 

lstnameImgCorre = [
    "Agreement_Class_12",
    # "Agreement_Class_15",
    "Agreement_Class_21",
    "Agreement_Class_22",
    # "Agreement_Class_25",
    "Agreement_Class_3",
    "Agreement_Class_33",
    "Agreement_Class_4"
]
dictCorre = {
    "Agreement_Class_12": 'AgrC_12',
    "Agreement_Class_15": 'AgrC_15',
    "Agreement_Class_21": 'AgrC_21',
    "Agreement_Class_22": 'AgrC_22',
    "Agreement_Class_25": 'AgrC_25',
    "Agreement_Class_3": 'AgrC_3',
    "Agreement_Class_33": 'AgrC_33',
    "Agreement_Class_4": 'AgrC_4'
}


lstCSVssaved = [];
if verificarSalvos:
    lst_path = glob.glob('areasAggrem/*.csv')
    for cc, npath in enumerate(lst_path):
        print(cc, " path file => ", npath)
        npath = npath.replace('areasAggrem/', '')
        npath = npath.replace('.csv', '')
        lstCSVssaved.append(npath)

#sys.exit()

# 100 arvores
nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759', '7621','7622','763','764',
    '765','766','767', '771','773', '7741','7742','775','776','777',
    '778','76111', '76116','7612','7614','7615','7616','7617','7618',
    '7619', '7613','772'
]
listBacFalta = []
cont = 350
lstBands = ['classification_' + str(yy) for yy in range(1985, 2024)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()
knowImgcolg = False
saveCSVs = False
savetoAsset = True
isFilter = True
if isFilter and ('POS-CLASS' in param['assetFilters'] or 'toExport' in param['assetFilters']):
    subfolder = "_" + param['assetFilters'].split('/')[-1] 
else:
    subfolder= '_class'
# lstVers = [5, 6, 7, 8, 9] # versions classification 
# lstVers = [5, 9]          # versions Filters 
dictClassAggrFails = []

version = param['version']
if param['changeAcount']:
    gerenciador(0, param)
pixelArea = ee.Image.pixelArea().divide(10000)
if param['isImgCol']:
    if isFilter:
        imgsMaps = ee.ImageCollection(param['assetFilters'])
    else:
        if int(version) > 6:  # 
            print(f" 🚨 Loading 🔊 >> {param['assetColprob']} <<  🚨")
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
        for model in ['GTB','RF']:   # 
            if isFilter and model != 'RF':
                mapClassMod = imgsMaps.filter(
                                ee.Filter.eq('version', version))
            else:
                mapClassMod = imgsMaps.filter(
                                ee.Filter.eq('version', version)).filter(
                                    ee.Filter.eq('classifier', model))

            print(f"########## 🔊 FILTERED BY VERSION {version} AND MODEL {model} 🔊 ###############") 
            sizeimgCol = mapClassMod.size().getInfo()
            print(" 🚨 número de mapas bacias ", sizeimgCol) 
            nameCSV = 'areaXclasse_CAAT_Col90_' + model +  subfolder + "_vers_" + str(version)
            # sys.exit()               
            if sizeimgCol > 0:                
                for cc, nbacia in enumerate(nameBacias): # nameBacias
                    ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                                        ee.Filter.eq('nunivotto3', nbacia)).geometry()
                    limitInt = bioma250mil.intersection(ftcol_bacias)
                    mapClassBacia = mapClassMod.filter(ee.Filter.eq('id_bacia', nbacia)).first()
                    # print(mapClassBacia.getInfo())
                    for nameImgCorre in lstnameImgCorre:                                    
                        print("sending name image to correction => ", nameImgCorre)                        
                         
                        if saveCSVs:
                            nameCSVBa = nameCSV + "_"+ dictCorre[nameImgCorre] + "_" +  nbacia
                            iterandoXanoImCruda(pixelArea, mapClassBacia, limitInt, nameImgCorre, nbacia, nameCSVBa) 
                        elif savetoAsset:
                            nameAssetBa =  'Col90_' + model +  subfolder + "_vers" + str(version) +  "_" + dictCorre[nameImgCorre] + "_" +  nbacia
                            # sim limites 
                            savedErro, nomeMapExp = sendingAggrementXanotoAsset(pixelArea, mapClassBacia, nameImgCorre, nbacia, nameAssetBa, model, subfolder)
                            if savedErro:
                                dictClassAggrFails.append(nomeMapExp)                
    
                            cont = gerenciador(cont, param)
                        else:
                            # Col90_GTB_toExport_vers10_AgrC_21_7618
                            nClass = nameImgCorre.replace('Agreement_Class_', '')
                            nameAggreImg = f'Col90_{model}{subfolder}_vers{version}_AgrC_{nClass}_{nbacia}'
                            print(" we process = ", nameAggreImg)
                            areaM = iterandoXanoImCruda(pixelArea, nameAggreImg, limitInt, nClass, nbacia) 
                            # print("  ddddd ", ee.FeatureCollection(areaM).first().getInfo())
                            # print(f"show the feature Area << {nameAggreImg} >> ")
                            # print(ee.FeatureCollection(areaM).getInfo())
                            processoExportarSHP(areaM, nameAggreImg, cc)
                            cont = gerenciador(cont, param)
                            # sys.exit()
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
            # areaM = 
            iterandoXanoImCruda(pixelArea, immapClassYY, limitInt, "", nbacia, "") 
            nameCSVBa = nameCSV + "_" + nbacia 
            # processoExportar(areaM, nameCSVBa, cc)
    
else:
    print("########## 🔊 LOADING MAP RASTER FROM IMAGE OBJECT ###############")
    assetPathRead = param['asset_Map'] 
    print(f" ------ {assetPathRead} ---- ")
    nameImg = assetPathRead.split('/')[-1].replace('mapbiomas_collection', '')
    mapClassRaster = ee.Image(assetPathRead).byte()
    ### call to function samples  #######
    nameCSV = 'areaXclasse_' + param['biome'] + "_Col" + nameImg

    for cc, nbacia in enumerate(nameBacias):
        ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                            ee.Filter.eq('nunivotto3', nbacia)).geometry()
        limitInt = bioma250mil.intersection(ftcol_bacias)
        for nameImgCorre in lstnameImgCorre:                                    
            print("sending name image to correction => ", nameImgCorre)                        
            # areaM = 
            iterandoXanoImCruda(pixelArea, mapClassRaster, limitInt, nameImgCorre, nbacia, "") 
            nameCSVBa = nameCSV + "_" + nbacia
            print(f" #{cc}  we processing ==> {nameCSVBa}   -- ") 
            # processoExportar(areaM, nameCSVBa, cc)
    



dictClassAggrFails = {
    'classAggrErrors': dictClassAggrFails
}
dfAggr = pd.DataFrame.from_dict(dictClassAggrFails)
dfAggr.to_csv(f'listaClassAggrementLayersFails_{subfolder}_vers{version}.csv', index= False)