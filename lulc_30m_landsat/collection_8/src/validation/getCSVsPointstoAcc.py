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


param = {
    'lsBiomas': ['CAATINGA'],
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'assetBiomas' : 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    # 'assetpointLapig': 'projects/mapbiomas-workspace/VALIDACAO/MAPBIOMAS_100K_POINTS_utf8', 
    'assetpointLapig': 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col3_points_w_edge_and_edited_v2',   
    'assetCol': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/class_filtered/maps_caat_col6_v1B_1',
    'assetCol7': 'projects/mapbiomas-workspace/public/collection7/mapbiomas_collection70_integration_v2',
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,40,41,46,47,48,49,50],
    'classNew':  [3, 4, 3,36,12,12,15,18,19,19,21,22,22,24,22,33,29,22,33,32,33,36,19,19,19,36,36,36,50,50],
    'pts_remap' : {
        "Formação Florestal": 3,
        "Formação Savânica": 4,        
        "Mangue": 3,
        "Floresta Plantada": 3,
        "Formação Campestre": 12,
        "Outra Formação Natural Não Florestal": 12,
        "Pastagem Cultivada": 15,
        "Aquicultura": 18,
        "Cultura Perene": 36,
        "Cultura Semi-Perene": 19,
        "Cultura Anual": 36,
        "Mineração": 22,
        "Praia e Duna": 22,
        "Afloramento Rochoso": 29,
        "Infraestrutura Urbana": 24,
        "Outra Área Não Vegetada": 22,
        "Rio, Lago e Oceano": 33,
        "Não Observado": 27            
    },
    'inBacia': False,
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
        "Pastagem Cultivada": 15,
        "Aquicultura": 18,
        "Cultura Perene": 36,
        "Cultura Semi-Perene": 19,
        "Cultura Anual": 36,
        "Mineração": 22,
        "Praia e Duna": 22,
        "Afloramento Rochoso": 29,
        "Infraestrutura Urbana": 24,
        "Outra Área Não Vegetada": 22,
        "Rio, Lago e Oceano": 33,
        "Não Observado": 27       
    })    

    prop_select = [
        'BIOMA', 'CARTA','DECLIVIDAD','ESTADO','JOIN_ID','PESO_AMOS'
        ,'POINTEDITE','PROB_AMOS','REGIAO','TARGET_FID','UF']
    
    feat_tmp = feat.select(prop_select)

    for year in range(1985, 2023):
        nam_class = "CLASS_" + str(year)
        feat_tmp = feat_tmp.set(nam_class, pts_remap.get(feat.get(nam_class)))
    
    return feat_tmp

bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

#lista de anos
list_anos = [str(k) for k in range(param['anoInicial'],param['anoFinal'])]

#print('lista de anos', list_anos)
lsAllprop = param['lsProp'].copy()
for ano in list_anos:
    band = 'CLASS_' + str(ano)
    lsAllprop.append(band) 

point_ref = ee.FeatureCollection(param['assetpointLapig']).filter(
                    ee.Filter.inList('BIOMA',  param['lsBiomas']))

# pointTrue = point_ref.map(lambda feat: change_value_class(feat))
pointTrue = point_ref
print("Carregamos {} points ".format(9738))  # pointTrue.size().getInfo()
# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

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
    
if param['inBacia']:
    mapClass = ee.Image(ee.ImageCollection(param['assetCol']).min()).byte()

else:
    if param['isImgCol']:
        for yy in range(1985, 2021):
            nmIm = 'CAATINGA-' + str(yy) + '-2'
            imTmp = ee.Image(param['inputAsset'] + nmIm).rename("classification_" + str(yy))

            if yy == 1985:
                mapClass = imTmp.byte()
            else:
                mapClass = mapClass.addBands(imTmp.byte())

    else:
        print("open the maps ")
        mapClass = ee.Image(param['assetCol7']).byte()

pointAcc = ee.FeatureCollection([])
mapClasses = ee.List([])

if param['inBacia']:
    for _nbacia in nameBacias:
        
        nameImg = 'filterGF_BACIA_' + _nbacia + '_V1'
        # nameImg = 'RF_BACIA_' + _nbacia + '_RF-v2_pca_baciaC6'
        # nameImg = 'RF_BACIA_' + _nbacia  

        baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).geometry()
        g_bacia_biome = bioma250mil.intersection(baciaTemp)

        pointTrueTemp = pointTrue.filterBounds(g_bacia_biome)

        pointAccTemp = mapClass.sampleRegions(
            collection= pointTrueTemp, 
            properties= lsAllprop, 
            scale= 30,  
            tileScale = 2,
            geometries= False)

        pointAccTemp = pointAccTemp.map(lambda Feat: Feat.set('bacia', _nbacia))

        pointAcc = pointAcc.merge(pointAccTemp)
    
    param['lsProp'].append('bacia')
else:

    pointAcc = mapClass.sampleRegions(
            collection= pointTrue, 
            properties= lsAllprop, 
            scale= 30,  
            tileScale = 4,
            geometries= False)
    

## Revisando todos as Bacias que foram feitas 

# cont = 0
# cont = gerenciador(cont, param)


print(pointAcc.first().getInfo())

pointAll = ee.FeatureCollection([])

lsNameClass = [kk for kk in param['pts_remap'].keys()]
lsValClass = [kk for kk in param['pts_remap'].values()]

for ano in list_anos:    
    
    labelRef = 'CLASS_' + str(ano)
    print("label de referencia : " + labelRef)
    labelCla = 'classification_' + str(ano)
    print("label da classification : " + labelCla)

    newProp = param['lsProp'] + [labelRef, labelCla]
    print("lista de propeties", newProp)
    newPropCh = param['lsProp'] + ['reference', 'classification']

    FeatTemp = pointAcc.select(newProp)
    #print(FeatTemp.first().getInfo())
    FeatTemp = FeatTemp.remap(lsNameClass, lsValClass, labelRef)   

    FeatTemp = FeatTemp.select(newProp, newPropCh)

    FeatTemp = FeatTemp.map(lambda  Feat: Feat.set('year', str(ano)))
    #print(FeatTemp.first().getInfo())

    pointAll = pointAll.merge(FeatTemp)

extra = param['assetCol7'].split('/')

name = 'occTabela_Caatinga_' + extra[-1]

processoExportar(pointAll, name)               

