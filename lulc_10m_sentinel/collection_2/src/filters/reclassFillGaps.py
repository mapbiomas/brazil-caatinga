#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import ee
import gee
import copy
import sys
import json
from tqdm import tqdm
import time
import collections
import pandas as pd
pd.set_option("mode.copy_on_write", True)
from pathlib import Path
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount) # project='ee-cartassol'
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


class processo_gapfill(object):

    options = {
            # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVY',
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX',            
            'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
            'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
            'asset_region_img_buffer': 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',   # 98 imagens the buffer = 1
            'classMapB' : [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62],
            'classNew'  : [3, 4, 3, 3,12,12,21,21,21,21,21,25,25,25,25,33,29,25,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21],
            'classUniques': [3,4,12,21,25,33],
            'year_inic': 2016,
            'year_end': 2023
        }


    def __init__(self, nameBacia, conectarPixels, vers, modelo):
        self.id_bacias = nameBacia
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto4', nameBacia)).first().geometry()   
        print("geometria ", len(self.geom_bacia.getInfo()['coordinates']))
        # https://code.earthengine.google.com/939d48fabf463d0a682491c6f5929cfb
        self.raster_bacia = (
            ee.ImageCollection(self.options['asset_region_img_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', nameBacia))
                    .filter(ee.Filter.eq('isBuffer', 1)).first()
        )

        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['year_inic'], self.options['year_end'] + 1)]
        self.years = [yy for yy in range(self.options['year_end'], self.options['year_inic'] - 1,  -1)]
        # print("lista de years \n ", self.years)
        self.conectarPixels = conectarPixels
        self.version = vers
        self.model = modelo
        # BACIA_776_GTB_col9-v9
        self.name_imgClass = 'BACIA_' + nameBacia + '_'+ modelo + '_col9-v' + str(self.version)
        print("processing image ", self.name_imgClass)
        # self.name_imgClass = 'BACIA_corr_mista_' + nameBacia + '_V2'       
        self.imgMapC9 = ee.Image(self.options['assetMapbiomas90']).updateMask(self.raster_bacia)

        self.imgClass = (
            ee.ImageCollection(self.options['input_asset'])
                .filter(ee.Filter.eq('version', str(self.version)))
                    .filter(ee.Filter.eq('id_bacia', nameBacia)).first() 
        )
        
        print("todas as bandas \n === > ", self.imgClass.bandNames().getInfo())
        # sys.exit()
        # self.imgClass = self.imgClass.mask(self.imgClass.neq(0))  
        # o segundo processo de revisão começa na versão 3      
        
        
    def dictionary_bands(self, key, value):
        imgT = ee.Algorithms.If(
                        ee.Number(value).eq(2),
                        self.imgClass.select([key]).byte(),
                        ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
                    )
        return ee.Image(imgT)

    def applyGapFill(self):
        lst_band_conn = []
        new_rasterMap = None
        previousImage = None        
        ###########  CORREGINDO DE 2023 PARA 2016 ############################
        cc = 0
        for yyear in tqdm(self.years):
            bandActive = 'classification_' + str(yyear)
            print(f" # {cc}  processing >> {bandActive}")
            rasterCol9YY =  (self.imgMapC9.select(bandActive)
                                .remap(self.options['classMapB'], self.options['classNew']))
            rasterS2YY = (self.imgClass.select(bandActive)
                                .remap(self.options['classMapB'], self.options['classNew'])
                                .unmask(0))

            for nClass in self.options['classUniques']:
                rasterS2YY = rasterS2YY.where(rasterS2YY.eq(0).And(rasterCol9YY.eq(nClass)), ee.Image.constant(nClass))

            if cc == 0:
                new_rasterMap = copy.deepcopy(rasterS2YY.rename(bandActive))
            else:
                new_rasterMap = new_rasterMap.addBands(rasterS2YY.rename(bandActive))
            cc += 1
        imageFilledTnT0 = ee.Image.cat(new_rasterMap).select(self.lstbandNames)
        
        if self.conectarPixels:
            lst_band_conn = [bnd + '_conn' for bnd in self.lstbandNames]
            # / add connected pixels bands
            imageFilledTnCon = imageFilledTnT0.addBands(
                                        imageFilledTnT0.connectedPixelCount(10, True).rename(lst_band_conn))
            # exportin imagem conectada    
            return imageFilledTnCon
        else:
            # print("banda col 8", imageFilledTn.bandNames().getInfo())
            return imageFilledTnT0

    def processing_gapfill(self):
        # apply the gap fill
        imageFilled = self.applyGapFill()
        print("passou")
        # print(imageFilled.bandNames().getInfo())

        name_toexport = 'filterGF_BACIA_'+ str(self.id_bacias) + '_' +  self.model + "_V" + str(self.version)
        imageFilled = ee.Image(imageFilled).set(
                            'version', int(self.version), 
                            'biome', 'CAATINGA',
                            'source', 'geodatin',
                            'model', self.model,
                            'type_filter', 'gap_fill',
                            'collection', '2.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Sentinel',
                            'system:footprint' , self.geom_bacia
                        )
        
        self.processoExportar(imageFilled, name_toexport)

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  self.options['output_asset'] + "/" + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':self.geom_bacia.getInfo()['coordinates'],
            'scale': 10,             
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))


param = {    
    'bioma': "CAATINGA", #nome do bioma setado nos metadados  
    'numeroTask': 6,
    'numeroLimit': 49,
    'conta' : {
        '0': 'caatinga01',   # 
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '25': 'solkan1201',    
        '30': 'solkanGeodatin',
        # '28': 'diegoUEFS',
        '35': 'superconta'     
    }
}

#============================================================
#========================METODOS=============================
#============================================================
def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
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


listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]


models = "GTB"  # "RF", "GTB"
versionMap = 3
cont = 0
for idbacia in listaNameBacias[:]:
    print("-----------------------------------------")
    print("----- PROCESSING BACIA {} -------".format(idbacia))

    cont = gerenciador(cont)
    aplicando_gapfill = processo_gapfill(idbacia, False, versionMap, models) # added band connected is True
    aplicando_gapfill.processing_gapfill()