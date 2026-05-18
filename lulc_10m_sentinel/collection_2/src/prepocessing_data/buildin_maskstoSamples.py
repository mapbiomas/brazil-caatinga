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
import json
import time
from icecream import ic 
from tqdm import tqdm
from pathlib import Path
import sys
# import arqParametros as arqParam
# import lstIdCodigoBacias as lstIdCodN5
import collections
collections.Callable = collections.abc.Callable
from multiprocessing.pool import ThreadPool
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


class ClassMask_toSample(object):

    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'bioma': 'CAATINGA',
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_baciasN2': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
        'asset_baciasN4': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4',
        'asset_cruzN245': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga_BdivN245',
        'asset_shpN5': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_nivel_5_clipReg_Caat',
        'asset_shpGrade': 'projects/mapbiomas-arida/ALERTAS/auxiliar/basegrade30KMCaatinga',
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
        'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
        'inputAssetStats': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/stats_mosaics_ba/all_statisticsMosaicC9_',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas71': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
        'assetMapbiomas80': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_fire': 'projects/mapbiomas-public/assets/brazil/fire/collection3/mapbiomas_fire_collection3_annual_burned_v1',
        'asset_befFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_S1v18',
        'asset_filtered': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Tp',
        'asset_alerts': 'users/data_sets_solkan/Alertas/layersClassTP',
        'asset_alerts_SAD': 'users/data_sets_solkan/Alertas/layersImgClassTP_2024_02',
        'asset_alerts_Desf': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_deforestation_secondary_vegetation_v2',
        'asset_input_mask' : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/masks/maks_layers',
        'asset_baseROIs_col9': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
        'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
        'asset_ROIs_manual': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv7N2manual'},
        'asset_ROIs_cluster': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster'}, 
        'asset_ROIs_automatic': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsGradeallBNDNormal'},  #  , coletaROIsv1N245, cROIsGradeallBNDNorm
        'asset_Coincidencia': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_coinciden',
        'asset_estaveis': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_estaveis',
        'asset_fire_mask': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5',
        'lsClasse': [3, 4, 12, 15, 18, 21, 22, 33, 29],
        'lsPtos': [3000, 2000, 3000, 1500, 1500, 1000, 1500, 1000, 1000],
        "anoIntInit": 1985,
        "anoIntFin": 2023,
        'janela': 3,
        'nfolder': 'cROIsN5allBND'
    }
    lst_bandExt = [
        'blue_min','blue_stdDev','green_min','green_stdDev','green_median_texture', 
        'red_min', 'red_stdDev','nir_min','nir_stdDev', 'swir1_min', 'swir1_stdDev', 
        'swir2_min', 'swir2_stdDev'
    ]

    def __init__(self):
        """
        Initializes the ClassMosaic_indexs_Spectral object.

        Args:
        testando (object): An object used for testing purposes.
        dictidGrBa (dict): A dictionary containing the id and group of basins.

        Returns:
        None
        """
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]                   
        self.sufN = ''
        # self.nbacia = mbacia
        self.baciabuffer = ee.FeatureCollection(self.options['asset_bacias_buffer'])
        # self.regionInterest = ee.FeatureCollection(self.options[')


    # https://code.earthengine.google.com/d5a965bbb6b572306fb81baff4bd401b
    def get_class_maskAlerts(self, yyear):
        #  get from ImageCollection 
        janela = 5
        intervalo_bnd_years = ['classification_' + str(kk) for kk in self.lst_year[1:] if kk <= yyear and kk > yyear - janela]
        maskAlertyyear = ee.Image(self.options['asset_alerts_Desf']).select(intervalo_bnd_years)\
                                    .divide(100).toUint16().eq(4).reduce(ee.Reducer.sum())
        return maskAlertyyear.eq(0).rename('mask_alerta')   

    #https://code.earthengine.google.com/b0ff1ef3aef14267704786be27d202a4
    def get_class_maskFire(self, yyear, gradeReg):
        maskFireyyear = ee.ImageCollection(self.options['asset_fire']).filter(
                                ee.Filter.inList('biome', ['CAATINGA', 'CERRADO', 'MATA_ATLANTICA'])).filter(
                                    ee.Filter.eq('year', int(yyear))).filterBounds(ee.Geometry(gradeReg)
                                        ).mosaic().unmask(0).eq(0).rename('mask_fire')                         

        return maskFireyyear

    
    def get_mask_Fire_estatics_pixels(self, _nbacia, exportFire):
        janela = 5   
        baciaselect = self.baciabuffer.filter(
                            ee.Filter.eq('nunivotto3', _nbacia)).first().geometry()
        # print("bacia ", baciaselect.getInfo())
        imgColFire = ee.Image(self.options['asset_fire']).clip(baciaselect)                            

        lstBands = []
        rasterFire = ee.Image.constant(0).clip(baciaselect);
        for nyear in self.lst_year:
            intervalo_years = ["burned_area_" + str(kk) for kk in self.lst_year if kk <= nyear and kk > nyear - janela]
            # print(intervalo_years)
            imgTemp = imgColFire.select(intervalo_years).reduce(ee.Reducer.sum()).unmask(0).gt(0)
            # print("image Fire imgTemp ", imgTemp.size().getInfo())

            #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
            lstBands.append('mask5wfire_'+ str(nyear))
            imgTemp = imgTemp.rename('mask5wfire_'+ str(nyear))
            rasterFire = rasterFire.addBands(imgTemp)

        rasterFire = rasterFire.select(lstBands).set('type', 'fire', 'bacia', _nbacia)
        name_exportimg = 'masks_fire_wind5_' + _nbacia
        if exportFire:
            asset_export = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5'
            self.processoExportarImage(imgTemp,  baciaselect, name_exportimg, asset_export)
        else:
            return imgTemp



    
    def save_ROIs_toAsset(self, collection, name, pos):
              
        nfolder = 'cROIsGradeallBNDNormal'  #'cROIsN5allBND'
        # AMOSTRAS/col9/CAATINGA/ROIs/cROIsGradeallBNDNorm       
        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['outAssetROIs'] + nfolder + "/" + name
        }

        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("#", pos, " ==> exportando ROIs da bacia $s ...!", name)


    #exporta a imagem classificada para o asset
    def processoExportarImage(self, mapaRaster, regionB, nameRasterExp, asset_base):

        idasset =  asset_base + "/" + nameRasterExp
        optExp = {
            'image': mapaRaster, 
            'description': nameRasterExp, 
            'assetId': idasset, 
            'region':regionB.getInfo()['coordinates'], #
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nameRasterExp + "..!")
        # print(task.status())
        

def gerenciador(cont, param):
    
    numberofChange = [kk for kk in param['conta'].keys()]    
    if str(cont) in numberofChange:

        gee.switch_user(param['conta'][str(cont)])
        gee.init()
        gee.tasks(n=param['numeroTask'], return_list=True)
        cont += 1

    elif cont > param['numeroLimit']:
        return 0
    
    cont += 1    
    return cont

param = {
    'anoInicial': 1985,
    'anoFinal': 2023,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta': {
        '0': 'caatinga01',
        '6': 'caatinga02',
        '12': 'caatinga03',
        '18': 'caatinga04',
        '24': 'caatinga05',
        '30': 'solkan1201',
        '36': 'solkanGeodatin',
        # '20': 'solkanGeodatin'
    },
}

cont = 0
# cont = gerenciador(cont, param)
nameBacias = [
    '745','741', '7422','746','7492','751','752','753',
    '757', '759','7621','7622','763','764','765', '766',
    '767','771','772', '773', '7741','776','7742','775',
    '777','778','744','754','755','756','758', '76111',
    '76116','7612', '7614','7421','7615','7616','7617',
    '7618','7619', '7613'
]
myClassMask_toSample = ClassMask_toSample()
for _nbacia in nameBacias[1:]:
    print("-------------------.kmkl-------------------------------------")
    print("--------    processing bacia " + _nbacia + "-----------------")   
    print("--------------------------------------------------------")
    
    myClassMask_toSample.get_mask_Fire_estatics_pixels(_nbacia, True)
    cont = gerenciador(cont, param)