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


class processo_filter_florests(object):

    options = {
            # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/ilumination/',
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/toExport/',
            'inputAssetC9': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',            
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill',
            'asset_regions_ilumination': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/regions_iluminations_problems',
            'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
            'asset_region_img_buffer': 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',   # 98 imagens the buffer = 1
            'classMapB' : [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62],
            'classNew'  : [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21],
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

        self.rasterMap = ee.Image(self.options['inputAssetC9']).updateMask(self.raster_bacia);

        self.model = modelo
        self.classFlorest = 3
        self.classSavana = 4

        self.imgClass = (ee.ImageCollection(self.options['input_asset'])
                            .filter(ee.Filter.eq('id_bacia', nameBacia)) 
                                .filter(ee.Filter.eq('version', int(nversion))).first()
                            )
        print(" img Class ",self.imgClass.bandNames().getInfo())
        # print("processing image ", self.name_imgClass)        
        # print("todas as bandas \n === > ", self.imgClass.bandNames().getInfo()) 
        
        
    def dictionary_bands(self, key, value):
        imgT = ee.Algorithms.If(
                        ee.Number(value).eq(2),
                        self.imgClass.select([key]).byte(),
                        ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
                    )
        return ee.Image(imgT)

    def applyFilter(self):

        lstImgMap = None
        previousImage = None        
        ###########  CORREGINDO DE 2023 PARA 1985 ############################
        imgRasterbase = ee.Image().byte()
        cc = 0
        for yyear in tqdm(self.years):
            bandActive = 'classification_' + str(yyear)
            print(f" # {cc}  processing >> {bandActive}")
            currentImage = self.imgClass.select(bandActive)
            masktoChange = self.rasterMap.select(bandActive).eq(int(self.classFlorest))
            rasterTemp = currentImage.where(masktoChange.eq(1), ee.Image.constant(int(self.classFlorest)))   
            if cc == 0:
                imgRasterbase = copy.deepcopy(rasterTemp)
            else:
                imgRasterbase = imgRasterbase.addBands(rasterTemp)       

            cc += 1       

        imgRasterbase = ee.Image.cat(imgRasterbase).select(self.lstbandNames)

        # print("show bandas from raster filtered ", imgRasterbase.bandNames().getInfo())
        return imgRasterbase

    def processing_layers_florest(self):
        # apply the gap fill
        lstBaciastoProcess = ["7411","7422","7424","7438","7443","745","746","751","753","7541","755","757"]
        if self.id_bacias in lstBaciastoProcess:
            imageFilled = self.applyFilter()
            print("passou")
        else:
            print(" ----- filtro não aplicado -----")
            imageFilled = self.imgClass

        name_toexport = 'filterCO_BACIA_'+ str(self.id_bacias) + '_' +  self.model + "_V" + str(self.nversion)
        imageFilled = ee.Image(imageFilled).updateMask(self.raster_bacia).toByte().set(
                            'version', int(self.nversion), 
                            'biome', 'CAATINGA',
                            'source', 'geodatin',
                            'model', self.model,
                            'type_filter', 'correcao',
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
    '7764', '757',  '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
listaNameB = []
# addFlorest = False
models = "GTB"  # "RF", "GTB"
versionMap= 4
cont = 23
for idbacia in listaNameBacias[:]:    
    if idbacia not in listaNameB:
        print("-----------------------------------------")
        print("----- PROCESSING BACIA {} -------".format(idbacia))
        
        aplicando_gapfill = processo_filter_florests(idbacia, models, versionMap) # added band connected is True
        aplicando_gapfill.processing_layers_florest()
        cont = gerenciador(cont)