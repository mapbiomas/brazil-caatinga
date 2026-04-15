#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import gee
import json
import csv
import copy
import sys
import math
import copy
from tqdm import tqdm 
import collections
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


class processo_filter_clean_Water(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/clean_water/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/toExport',        
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/grass_Aflor',
            'asset_raster_GrassAflor': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/layer_afloramento_campo_cluster',
            'inputAssetC9': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
            'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
            'asset_region_img_buffer': 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',   # 98 imagens the buffer = 1
            'year_inic': 2016,
            'year_end': 2023,
            'version_int': 1,
            'version_out': 1
        }


    def __init__(self, nameBacia,  modelo, nversion):
        self.nversion = nversion
        self.id_bacias = nameBacia
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto4', nameBacia)).first().geometry()
        print("geometria ", len(self.geom_bacia.getInfo()['coordinates']))

        self.raster_bacia = (
            ee.ImageCollection(self.options['asset_region_img_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', nameBacia))
                    .filter(ee.Filter.eq('isBuffer', 1)).first()
        )

        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['year_inic'], self.options['year_end'] + 1)]
        self.years = [yy for yy in range(self.options['year_end'], self.options['year_inic'] - 1,  -1)]
        # print("lista de years \n ", self.years)
        # self.maskGrassAfl = ee.Image(self.options['asset_raster_GrassAflor']).unmask(0)
        self.rasterMap = ee.Image(self.options['inputAssetC9']).updateMask(self.raster_bacia);
        self.model = modelo

        self.imgClass = (ee.ImageCollection(self.options['input_asset'])
                            .filter(ee.Filter.eq('id_bacia', nameBacia)) 
                                .filter(ee.Filter.eq('version', int(nversion)))
                            )

        self.imgClass = self.imgClass.first()   

        print(" img Class ",self.imgClass.bandNames().getInfo())
        print(" img Class ",self.imgClass.get('system:index').getInfo())
        # print("processing image ", self.name_imgClass)        
        # print("todas as bandas \n === > ", self.imgClass.bandNames().getInfo()) 
        

    def applyFilter(self):
        water = 33
        lstImgMap = None
        previousImage = None        
        ###########  CORREGINDO DE 2023 PARA 1985 ############################

        imgRasterbase = ee.Image().byte()
        cc = 0
        for yyear in tqdm(self.years):
            bandActive = 'classification_' + str(yyear)
            print(f" # {cc}  processing >> {bandActive}")
            rasterMapYY = self.rasterMap.select(bandActive)
            currentImage = self.imgClass.select(bandActive)
            masktoChange = rasterMapYY.eq(water).focalMax(9).gt(0)
            maskWaterS2 = currentImage.eq(33).subtract(masktoChange).gt(0)
            rasterTemp = currentImage.where(maskWaterS2.eq(1), rasterMapYY)   # sustituir Water by florest 
            if cc == 0:
                imgRasterbase = copy.deepcopy(rasterTemp)
            else:
                imgRasterbase = imgRasterbase.addBands(rasterTemp)       

            cc += 1  
        imgRasterbase = ee.Image.cat(imgRasterbase).select(self.lstbandNames)

        # print("show bandas from raster filtered ", imgRasterbase.bandNames().getInfo())
        return imgRasterbase    

    def processing_class_corrections(self):
        # apply the water clean
        
        imageFilled = self.applyFilter()

        print(" ----- filtro  aplicado -----")
        name_toexport = 'filterCW_BACIA_'+ str(self.id_bacias) + '_' +  self.model + "_V" + str(self.nversion)
        imageFilled = ee.Image(imageFilled).toByte().updateMask(self.raster_bacia).set(
                            'version', int(self.nversion), 
                            'biome', 'CAATINGA',
                            'source', 'geodatin',
                            'model', self.model,
                            'type_filter', 'clean_water',
                            'collection', '2.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Sentinel',
                            'system:footprint' , self.imgClass.get('system:footprint')
                        )
        
        self.processoExportar(imageFilled, name_toexport)

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):    

        idasset =  self.options['output_asset'] + nomeDesc
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
    'numeroLimit': 42,
    'conta' : {
        '0': 'caatinga01',   # 
        '3': 'caatinga02',
        '9': 'caatinga03',
        '12': 'caatinga04',
        '15': 'caatinga05',        
        '18': 'solkan1201',    
        '21': 'solkanGeodatin',
        # '21': 'diegoUEFS',
        '24': 'superconta'     
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
listaNameB = []
# addFlorest = False
models = "GTB"  # "RF", "GTB"
versionMap= 4
cont = 25
for idbacia in listaNameBacias[:]:    
    if idbacia not in listaNameB:
        print("-----------------------------------------")
        print("----- PROCESSING BACIA {} -------".format(idbacia))
        
        aplicando_cleanWater = processo_filter_clean_Water(idbacia, models, versionMap) # added band connected is True
        aplicando_cleanWater.processing_class_corrections()
        cont = gerenciador(cont)