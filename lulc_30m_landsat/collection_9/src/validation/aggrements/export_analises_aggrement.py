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



def gerenciador(cont, paramet):
    #0, 18, 36, 54]
    #===========================================#
    # gerenciador de contas para controlar      # 
    # processos task no gee                     #
    #===========================================#
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


"""
//   var ano = 2021
//   AZUL somente na col 8
//   VERMELHO somente col7.1
//   CINZA mapeado nos 2 
//   listar anos para poerformar a análise
//   years = [2021];
"""
#//exporta a imagem classificada para o asset
def processoExportarImage (imageMap, nameB, idAssetF, regionB):
    idasset =  idAssetF + "/" + nameB
    print("saving ")
    optExp = {
            'image': imageMap, 
            'description': nameB, 
            'assetId': idasset, 
            'region': regionB.getInfo()['coordinates'], #//['coordinates']
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando mapa ... " + nameB + "..!");


params = {
    'asset_Col6' : 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
    'asset_Col7' : 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
    'asset_Col8' : 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
    'asset_biomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas-2019-raster',
    'asset_sphBiomas': "projects/mapbiomas-workspace/AUXILIAR/biomas-2019",
    'assetOutput': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/aggrements',
    'numeroTask': 2,
    'numeroLimit': 10,
    'conta' : {
        # '0': 'caatinga01',
        '2': 'caatinga02',
        '4': 'caatinga03',
        '6': 'caatinga04',
        '8': 'caatinga05'
    },
}
bioma =  'Caatinga'; 
biomes = ee.Image(params['asset_biomas']).eq(5).selfMask();
limitBioma = ee.FeatureCollection(params['asset_sphBiomas']).filter(ee.Filter.eq("Bioma", bioma));

class_col71 = ee.Image(params['asset_Col7']).updateMask(biomes);
class_col80 = ee.Image(params['asset_Col8']).updateMask(biomes);
#Map.addLayer(ee.Image.constant(1), {min: 0, max: 1}, 'base');
    
cont = 2      
#// listar classes para performar a análise 
lst_classes = [3,4,12,29,15,18,21,22,25,33];
for year_j in range(2002, 2010):
    # // para cada classe 
    # // para cada ano
    year_j = str(year_j)
    col8_j = class_col80.select('classification_'+ year_j);
    col71_j = class_col71.select('classification_'+year_j);
    for class_i in lst_classes:
        images = ee.Image(0);
        #// selecionar a classificação do ano j        
        #// calcular concordância
        conc = ee.Image(0).where(col8_j.eq(class_i).And(col71_j.eq(class_i)), 1).where(   #// [1]: Concordância
                            col8_j.eq(class_i).And(col71_j.neq(class_i)), 2).where(  #// [2]: Apenas col8
                            col8_j.neq(class_i).And(col71_j.eq(class_i)), 3)  #// [3]: Apenas Col7.1
                            #//.updateMask(biomes.eq(4));
        
        conc = conc.updateMask(conc.neq(0)).rename('territory_' + year_j);
        
        #// build sinthetic image to compute areas
        synt = ee.Image(0).where(conc.eq(1), col8_j).where(
                            conc.eq(2), col71_j).where(
                            conc.eq(3), col8_j).updateMask(conc).rename(
                                ['classification_' + year_j]);
        #// build database
        images = images.addBands(conc).addBands(synt);
        nameLayer = year_j + 'Agreement_Class_' + str(class_i);
        processoExportarImage(images.select(['territory_' + year_j]), nameLayer, params['assetOutput'], limitBioma.geometry());
    
    cont = gerenciador(cont, params)