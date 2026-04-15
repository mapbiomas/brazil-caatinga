#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import json
import csv
import sys
import arqParametros as arqParam
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

path_asset = "projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/"
param = {
    'lsBiomas': ['CAATINGA'],
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'assetBiomas' : 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'assetpointLapig': 'projects/mapbiomas-workspace/VALIDACAO/MAPBIOMAS_100K_POINTS_utf8',    
    'limit_bacias': "users/CartasSol/shapes/bacias_limit",
    'assetCol': path_asset + 'class_filtered_Tp',
    # 'assetCol6': path_asset + "class_filtered/maps_caat_col6_v2_4",
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21],
    'inBacia': True,
    'pts_remap' : {
        "Formação Florestal": 3,
        "Formação Savânica": 4,        
        "Mangue": 3,
        "Floresta Plantada": 3,
        "Formação Campestre": 12,
        "Outra Formação Natural Não Florestal":12,
        "Pastagem Cultivada": 21,
        "Aquicultura": 21,
        "Cultura Perene": 21,
        "Cultura Semi-Perene": 21,
        "Cultura Anual": 21,
        "Mineração": 22,
        "Praia e Duna": 22,
        "Afloramento Rochoso": 29,
        "Infraestrutura Urbana": 22,
        "Outra Área Não Vegetada": 22,
        "Rio, Lago e Oceano": 33,
        "Não Observado": 27       
    },
    'anoInicial': 1985,
    'anoFinal': 2019,  # 2019
    'numeroTask': 6,
    'numeroLimit': 2,
    'conta' : {
        '0': 'caatinga05'              
    },
    'lsProp': ['ESTADO','LON','LAT','PESO_AMOS','PROB_AMOS','REGIAO','TARGET_FID','UF'],
    "amostrarImg": False,
    'isImgCol': False
}

def change_value_class(feat):

    pts_remap = ee.Dictionary({
        "Formação Florestal": 3,
        "Formação Savânica": 4,        
        "Mangue": 3,
        "Floresta Plantada": 3,
        "Formação Campestre": 12,
        "Outra Formação Natural Não Florestal": 12,
        "Pastagem Cultivada": 21,
        "Aquicultura": 21,
        "Cultura Perene": 21,
        "Cultura Semi-Perene": 21,
        "Cultura Anual": 21,
        "Mineração": 22,
        "Praia e Duna": 22,
        "Afloramento Rochoso": 29,
        "Infraestrutura Urbana": 22,
        "Outra Área Não Vegetada": 22,
        "Rio, Lago e Oceano": 33,
        "Não Observado": 27       
    }) 

    prop_select = [
        'BIOMA', 'CARTA','DECLIVIDAD','ESTADO','JOIN_ID','PESO_AMOS'
        ,'POINTEDITE','PROB_AMOS','REGIAO','TARGET_FID','UF', 'LON', 'LAT']
    
    feat_tmp = feat.select(prop_select)

    for year in range(1985, 2019):
        nam_class = "CLASS_" + str(year)
        set_class = "CLASS_" + str(year)
        valor_class = ee.String(feat.get(nam_class))
        feat_tmp = feat_tmp.set(set_class, pts_remap.get(valor_class))
    
    return feat_tmp

bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

#lista de anos
list_anos = [str(k) for k in range(param['anoInicial'],param['anoFinal'])]

print('lista de anos', list_anos)
lsAllprop = param['lsProp'].copy()
for ano in list_anos:
    band = 'CLASS_' + str(ano)
    lsAllprop.append(band) 

ptsTrue = ee.FeatureCollection(param['assetpointLapig']).filterBounds(bioma250mil)

pointTrue = ptsTrue.map(lambda feat: change_value_class(feat))
print("Carregamos {} points ".format(9738))  # pointTrue.size().getInfo()
print(pointTrue.first().getInfo())
# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
limite_bacias = ee.FeatureCollection(param['limit_bacias']).geometry()

#nome das bacias que fazem parte do bioma
nameBacias = [
      '741','7421','7422','744','745','746','7492','751','752',
      '753', '754','755','756','757','758','759','7621','7622','763',
      '764','765','766','767','771','772','773', '7741','7742','775',
      '776','777','778','76111','76116','7612','7613','7614','7615',
      '7616','7617','7618','7619'
]
# '7491',

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
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, nameT):  
    
    optExp = {
          'collection': ROIsFeat, 
          'description': nameT, 
          'folder':"ptosCol6"          
        }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")
    # print(task.status())
    

pointAcc = ee.FeatureCollection([])
mapClasses = ee.List([])

if param['inBacia']:    
    print("##########  CARREGOU A VERSAO 4 ###############")
    mapClass = ee.ImageCollection(param['assetCol']).filter(
                        ee.Filter.eq('version', '5'))
else:
    if param['isImgCol']:
        for yy in range(1985, 2021):
            nmIm = 'CAATINGA-' + str(yy) + '-2'
            imTmp = ee.Image(param['assetCol'] + nmIm).rename("classification_" + str(yy))

            if yy == 1985:
                mapClass = imTmp.byte()
            else:
                mapClass = mapClass.addBands(imTmp.byte())

    else:
        mapClass = ee.Image(param['assetCol']).byte()

pointAll = ee.FeatureCollection([])
lsNameClass = [kk for kk in param['pts_remap'].keys()]
lsValClass = [kk for kk in param['pts_remap'].values()]
# 


for _nbacia in nameBacias:
    
    nameImg = 'filterTp_BACIA_' + _nbacia + '_V1'
    # nameImg = 'RF_BACIA_' + _nbacia + '_RF-vnorm_col6'
    # nameImg = 'RF_BACIA_' + _nbacia  
    print("processando img == " + nameImg + " em bacia *** " + _nbacia)
    baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).geometry()    
    g_bacia_biome = bioma250mil.intersection(baciaTemp)
    
    # print("cortou a imagem em {} metros quadrados ".format(g_bacia_biome.area(0.1).getInfo()))
    # mapClassTemp = mapClass.clip(g_bacia_biome).byte()   
    pointTrueTemp = pointTrue.filterBounds(g_bacia_biome)
    if param['inBacia']:
        mapClassBacia = ee.Image(mapClass.filter(ee.Filter.eq('id_bacia', _nbacia)).first())
        pointAccTemp = mapClassBacia.sampleRegions(
            collection= pointTrueTemp, 
            properties= lsAllprop, 
            scale= 30, 
            tileScale= 2, 
            geometries= False)

    else:
        pointAccTemp = mapClass.sampleRegions(
            collection= pointTrueTemp, 
            properties= lsAllprop, 
            scale= 30, 
            tileScale= 2, 
            geometries= False)

    pointAccTemp = pointAccTemp.map(lambda Feat: Feat.set('bacia', _nbacia))

    pointAcc = pointAcc.merge(pointAccTemp)
    
    # print(pointAccTemp.first().getInfo())    

param['lsProp'].append('bacia')
newPropCh = param['lsProp'] + ['reference', 'classification']
for cc, ano in enumerate(list_anos):    
    
    labelRef = 'CLASS_' + str(ano)
    print("label de referencia : " + labelRef)
    labelCla = 'classification_' + str(ano)
    print("label da classification : " + labelCla)
    
    
    newProp = param['lsProp'] + [labelRef, labelCla]
    print("lista de propeties", newProp) 
    print("nova ls propeties", newPropCh)       

    FeatTemp = pointAcc.select(newProp)
    # print(FeatTemp.first().getInfo())
    FeatTemp = FeatTemp.filter(ee.Filter.notNull([labelCla]))
    
    # tam = FeatTemp.size().getInfo() 

    # if tam > 0:
    # FeatTemp = FeatTemp.remap(lsNameClass, lsValClass, labelRef)   
    FeatTemp = FeatTemp.select(newProp, newPropCh)

    FeatTemp = FeatTemp.map(lambda  Feat: Feat.set('year', str(ano)))
    print(FeatTemp.first().getInfo())

    pointAll = pointAll.merge(FeatTemp)

extra = param['assetCol'].split('/')
name = 'occTab_corr_Caatinga_' + extra[-1] +"_V5"
processoExportar(pointAll, name)

## Revisando todos as Bacias que foram feitas 

# cont = 0
# cont = gerenciador(cont, param)

               

