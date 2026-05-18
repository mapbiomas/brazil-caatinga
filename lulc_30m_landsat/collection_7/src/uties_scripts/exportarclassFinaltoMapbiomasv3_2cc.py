#!/usr/bin/env python2
# -*- coding: utf-8 -*-

##########################################################
## CRIPT DE EXPORTAÇÃO DO RESULTADO FINAL PARA O ASSET  ##
## DE mAPBIOMAS                                         ##
## Produzido por Geodatin - Dados e Geoinformação       ##
##  DISTRIBUIDO COM GPLv2                               ##
#########################################################

import ee 
import gee
import json
import csv
import sys
import lista_poligons

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

bioma250mil = ee.FeatureCollection('users/CartasSol/shapes/nCaatingaBff3000').geometry()

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


#https://code.earthengine.google.com/36953f8f5dcec8b827c69a3394c5258a
def limparImag(image, nameBnd, iCorr_class12_v4, img_sust):

    geom_erro = ee.Geometry.MultiPolygon(lista_poligons.new_list_pol_erro) 
    # # get pixels with value 12 (grassland)
    # img_mask_campo = iCorr_class12_v4.eq(12).unmask(0).clip(bioma250mil)
    # img_mask_campo = img_mask_campo.set('system:footprint', bioma250mil).unmask(0)
    # img_mask_campo = img_mask_campo.focal_min(0.5, 'square' ).focal_max(0.5, 'square')

    # criando as imagem mascara para  vegetação
    feat_err1 = ee.Feature(bioma250mil.difference(geom_erro), {'value': 1})
    feat_err0 = ee.Feature(geom_erro, {'value': 0})
    img_mask_err = ee.FeatureCollection([feat_err0, feat_err1])
    # all biome with value 1 except geometry with erro 
    img_mask_err = img_mask_err.reduceToImage(['value'], ee.Reducer.first())

    # tem tudos os pixels que não serão modificados
    # mask_geral  = img_mask_err.subtract(img_mask_campo)    
    # removindo tudos os pixels que serão reclassificados do mapa inicial
    geomMap1 = image.updateMask(img_mask_err).unmask(0) 

    # creating as mask of all pixel are changing
    mask_veg_erro = ee.Image(1).subtract(img_mask_err)#.clip(bioma250mil)
    
    # img_changed_camp = img_mask_campo.multiply(12)
    img_changed_veg_erro = img_sust.updateMask(mask_veg_erro).unmask(0)    
    
    imgFinal = geomMap1.add(img_changed_veg_erro) # .add(img_changed_camp)
    imgFinal = imgFinal.clip(bioma250mil)

    return imgFinal.rename(nameBnd)

param = {
    # 'inputAsset': "projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV6_final/",    
    'input_old': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV3_norm/RF_BACIA_757_RF-vnorm_col6_camp',
    'input_solo': 'users/diegocosta/doctorate/Bare_Soils_Caatinga',
    'outputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV6_final/',   
    'assetIm': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV0/CAATINGA-VERSION_FINAL-3',
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    # 'outputAsset': 'projects/mapbiomas-workspace/COLECAO5/classificacao',
    'biome': 'CAATINGA', #configure como null se for tema transversal
    'version': '2',
    'collection': 6.0,
    'source': 'geodatin',
    'theme': None, 
    'numeroTask': 0,
    'numeroLimit': 37,
    'conta' : {
        '0': 'caatinga01',
        '12': 'caatinga02',
        '24': 'caatinga03'        
    },
}
pRDilate = {
    'radius': 2,
    'kernelType': 'square',
    'iterations': 1
}
pRErode = {
    'radius': 3,
    'kernelType': 'square',
    'iterations': 1
}

imageMap_main = ee.Image()

for year in range(1985, 2021):
    
    nome_bnd = "CAATINGA-" + str(year) + '-1'
    img_tmp = ee.Image(param['outputAsset'] + nome_bnd)
    banda_year = 'classification_' + str(year)
    
    if year == 1985:
        imageMap_main = img_tmp.rename(banda_year)
    else:
        imageMap_main = imageMap_main.addBands(img_tmp.rename(banda_year))

# geomet = imageMap.geometry()
# formando a imagem solo "Caatinga_2018_classification_2018"
img_corr_class12_v4 = ee.Image(param['input_old'])
# ft_bacias = ee.FeatureCollection(param['asset_bacias']).filter( 
#                                         ee.Filter.eq('nunivotto3', '757'))


for ii, year in enumerate(range(1985, 2021)):
    gerenciador(ii, param)
    banda_year = 'classification_' + str(year) 
    bandaAct = 'CAATINGA-' + str(year) +  '-1'
    print("Banda activa: " + bandaAct)

    imgYear = ee.Image(param['assetIm']).select(banda_year)
    mapa_year = limparImag(
                        imgYear, 
                        banda_year, 
                        img_corr_class12_v4.select(banda_year), 
                        imageMap_main.select(banda_year)
                        )    

    mapa_year = mapa_year.set('type', 'biome')\
                    .set('year', year)\
                    .set('name', param['biome'])\
                    .set('version', param['version'])\
                    .set('source', param['source'])\
                    .set('system:footprint', bioma250mil)    

    
    name = param['biome'] + '-' + str(year) + '-' + param['version']
    # maps_caat_col6_v6
    optExp = {   
        'image': mapa_year.byte(), 
        'description': name, 
        'assetId':param['outputAsset'] + name, 
        'region': bioma250mil.getInfo()['coordinates'],
        'scale': 30, 
        'maxPixels': 1e13,
        "pyramidingPolicy": {".default": "mode"}
    }

    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... banda  " + name + "..!")