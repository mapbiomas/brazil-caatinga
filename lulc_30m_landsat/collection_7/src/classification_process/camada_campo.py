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
def limparImag(image, nameBnd):

    # get pixels with value 12 (grassland)
    img_mask_campo = image.eq(12).unmask(0).clip(bioma250mil)
    img_mask_campo = img_mask_campo.set('system:footprint', bioma250mil).unmask(0)
    img_mask_campo = img_mask_campo.focal_min(0.5, 'square' ).focal_max(0.5, 'square')   

    return img_mask_campo.rename(nameBnd)

param = {       
    'input_old': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV3_norm/RF_BACIA_757_RF-vnorm_col6_camp',    
    'outputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/',      
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",   
    'biome': 'CAATINGA', # configure como null se for tema transversal
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

# geomet = imageMap.geometry()
# formando a imagem solo "Caatinga_2018_classification_2018"
img_corr_class12_v4 = ee.Image(param['input_old'])
# ft_bacias = ee.FeatureCollection(param['asset_bacias']).filter( 
#                                         ee.Filter.eq('nunivotto3', '757'))

camada_campo = ee.Image().byte()
for ii, year in enumerate(range(1985, 2021)):
    
    banda_year = 'classification_' + str(year)     
    print("Banda activa: " + banda_year)

    imgYear = img_corr_class12_v4.select(banda_year)
    
    img_mask_campo = imgYear.eq(12).unmask(0).clip(bioma250mil)
    img_mask_campo = img_mask_campo.set('system:footprint', bioma250mil).unmask(0)
    img_mask_campo = img_mask_campo.focal_min(0.5, 'square' ).focal_max(0.5, 'square')   

    img_mask_campo = img_mask_campo.rename(banda_year)

    camada_campo = camada_campo.addBands(img_mask_campo)
    
camada_campo = camada_campo.set('type', 'biome').set('name', param['biome']) \
                    .set('version', param['version'])\
                    .set('source', param['source'])\
                    .set('system:footprint', bioma250mil)    


name = param['biome'] + '-camada_grassland-' + param['version']
# maps_caat_col6_v6
optExp = {   
    'image': camada_campo.byte(), 
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