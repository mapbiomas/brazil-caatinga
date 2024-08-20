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
import glob
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

keyAssetr = 'integracao'
# keyAssetr = ''

param = {
    # 'inputAsset': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',   
    # 'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/toExp',
    # 'inputAsset': 'projects/mapbiomas-workspace/TRANSVERSAIS/GTAGUA/CONSOLIDADO/new_pilot',
    'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/aggrements',
    'geral':  True,
    'isImgCol': True,  
    'inBacia': True,
    'version': '',
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-AGGREMENT-EXPORT', 
    'lsClasses': [3,4,12,21,22,33,29],
    'numeroTask': 0,
    'numeroLimit': 16500,
    'conta' : {
        '0': 'caatinga03',
        '10000': 'caatinga04',
        '18000': 'caatinga05'
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
# https://code.earthengine.google.com/5a7c4eaa2e44f77e79f286e030e94695
def calculateArea (image, pixelArea, geometry):

    pixelArea = pixelArea.addBands(image.rename('classe')).clip(geometry)#.addBands(
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

def iterandoXanoImCruda(imgAreaRef, namBacia, limite, nameImage):

    print("nameImage   ==> ", nameImage)
    try:
        imgMapp = ee.ImageCollection(param['inputAsset']).filter(
                                ee.Filter.eq('system:index', nameImage)).first().clip(limite) 
        year = nameImage[:4]

        imgAreaRef = imgAreaRef.clip(limite)
        areaGeral = ee.FeatureCollection([])         
        areaGeral = calculateArea (imgMapp, imgAreaRef, limite)        
        areaGeral = areaGeral.map( lambda feat: feat.set('year', int(year), 'bacia', namBacia))
        
        return areaGeral, True
    except:
        print("FAIL by don't exist")
        return ee.FeatureCollection([]), False

        
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
    "Agreement_Class_15",
    "Agreement_Class_21",
    #"Agreement_Class_22",
    "Agreement_Class_25",
    "Agreement_Class_3",
    #"Agreement_Class_33",
    "Agreement_Class_4"
]

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
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767', '771','773', '7741','7742','775','776','777',
    '778','76111', '76116','7612','7614','7615','7616','7617','7618',
    '7619', '7613','772'
]
listBacFalta = []
cont = 4500
for _nbacia in nameBacias[:]:
    print("-------------------.kmkl-------------------------------------")
    print("--------    classificando bacia " + _nbacia + "-----------------")   
    print("--------------------------------------------------------") 
    nameCSV = 'areaXclasse_' + _nbacia 
    baciabuffer = ee.FeatureCollection(param['asset_bacias']).filter(
                            ee.Filter.eq('nunivotto3', _nbacia)).first().geometry()

    geomCurt = bioma250mil.intersection(baciabuffer)                        
    #try:
    if exportSta:
        for year in range(1985, 2023):
            for nameImgCorre in lstnameImgCorre:            
                nameImgCorre = str(year) + nameImgCorre
                print("sending name image to correction => ", nameImgCorre)
                nameCSV = 'areaXclasse_' + _nbacia + "_" + nameImgCorre
                if nameCSV not in lstCSVssaved:
                    areaM, exportArea = iterandoXanoImCruda(pixelArea, _nbacia, geomCurt, nameImgCorre)   
                    if exportArea: 
                        try:                  
                            print("passso ", areaM.first().getInfo())
                            processoExportar(areaM, nameCSV)
                        except:
                            print("estava vacio ")
                    #sys.exit()
                cont = gerenciador(cont, param)
    else:
        areaM = iterandoXanoImCruda(pixelArea, _nbacia, geomCurt, '')  
        processoExportar(areaM, nameCSV)
    #except:
    #    print("=== BACIA {} WAS FAILED ====")



    


