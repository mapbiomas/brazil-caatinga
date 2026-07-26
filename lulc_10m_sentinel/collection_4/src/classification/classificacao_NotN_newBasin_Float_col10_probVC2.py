#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import glob
import time
import json
import copy
import sys
import pandas as pd
from pathlib import Path
import arqParametros as arqParams 
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


#============================================================
#============== FUNCTIONS FO SPECTRAL INDEX =================


class ClassMosaic_indexs_Spectral(object):

    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'bioma': "CAATINGA",
        'lsBandasMap': [],
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
        'asset_embedding': "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL",
        'asset_mosaic_sentinelp2': 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',
        'asset_mosaic_sentinelp1': 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
        # Amostras que passaram pelo downsampling supervisionado (col11)
        'asset_ROIs_merge': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/ROIs/ROIs_by_BasinGroup_downS',
        'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/Classifier/Classify_layers',
        # 'asset_output': 'projects/nexgenmap/SAMPLES/Caatinga',
        # Spectral bands selected
        'lsClasse': [4, 3, 12, 15, 18, 22, 33],
        'lsPtos': [300, 500, 300, 350, 100, 150, 300],
        "anoIntInit": 2016,
        "anoIntFin": 2025,
        'janela': 3,
        'version': 5,
        'numero_bndFS': 45,
        # 'dict_classChangeBa': arqParams.dictClassRepre,
        # https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting
        'pmtGTB': {
            'numberOfTrees': 25, 
            'shrinkage': 0.1,         
            'samplingRate': 0.65, 
            'loss': "LeastSquares",#'Huber',#'LeastAbsoluteDeviation', 
            'seed': 0
        },
    }
    classes_old   = [ 3, 4, 5, 6, 11, 12, 15, 19, 20, 21, 23, 24, 25, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75]
    classes_desej = [ 3, 4, 0, 0,  0, 12, 15, 18, 18,  0, 25,  0, 25, 29,  0, 33, 12, 33, 18, 18, 18, 18, 18, 18, 18,  3,  4, 18,  0] # < ajuste

    lst_bandExt = [
        'blue_min','blue_stdDev','green_min','green_stdDev','green_median_texture', 
        'red_min', 'red_stdDev','nir_min','nir_stdDev', 'swir1_min', 'swir1_stdDev', 
        'swir2_min', 'swir2_stdDev'
    ]
    featureBands = [
        'blue_median', 'green_median', 'red_median',
        'nir_median', 'swir1_median', 'swir2_median',
    ]
    paramInt = {
        'min': {
            "2017": -0.2679,
            "2018": -0.2679,
            "2019": -0.2679,
            "2020": -0.2761,
            "2021": -0.2844,
            "2022": -0.2761,
            "2023": -0.2761,
            "2024": -0.2679,
        },
        'max': {
            "2017": 0.31,
            "2018": 0.2679,
            "2019": 0.3188,
            "2020": 0.2844,
            "2021": 0.2679,
            "2022": 0.2844,
            "2023": 0.2679,
            "2024": 0.2761
        },
    }

    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self):
        """
        Initializes the ClassMosaic_indexs_Spectral object.

        Args:
        testando (object): An object used for testing purposes.
        dictidGrBa (dict): A dictionary containing the id and group of basins.

        Returns:
        None
        """
     
        imgMapSaved = ee.ImageCollection(self.options['assetOut'])
        self.lstIDassetS = imgMapSaved.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
        print(f" ====== we have {len(self.lstIDassetS)} maps saved ====")   

        # print(" ==== ", ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        self.options['lsBandasMap'] = ['classification_' + str(kk) for kk in self.lst_year]

        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        self.band_mosaic = band_year + band_wets + band_drys

        # self.tesauroBasin = arqParams.tesauroBasin
        pathHiperpmtros = os.path.join(pathparent, 'dados', 'jsons', 'hiper_pmtr_tunning_col2_S2.json')
        b_file = open(pathHiperpmtros, 'r')
        self.dictHiperPmtTuning = json.load(b_file)
        print(f" we readed {len(self.dictHiperPmtTuning.keys())} basin with the parameter tuning in << self.dictHiperPmtTuning  >> ")

        pathFSJson = os.path.join(pathparent, 'dados', 'jsons', 'FS_col2S2_v3.json')
        print("==== path of Features Selections in json ==== \n >>> ", pathFSJson)
        json_file = open(pathFSJson, 'r')
        self.dictBand_FS = json.load(json_file)
        print(f" we readed {len(self.dictBand_FS.keys())} basin with the list Features Bands in << self.dictBand_FS  >> ")


    # add bands with slope and hilshade informations 
    def addSlopeAndHilshade(self, img):
        # A digital elevation model.
        # NASADEM: NASA NASADEM Digital Elevation 30m
        dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')

        # Calculate slope. Units are degrees, range is [0,90).
        slope = ee.Terrain.slope(dem).divide(500).toFloat()

        # Use the ee.Terrain.products function to calculate slope, aspect, and
        # hillshade simultaneously. The output bands are appended to the input image.
        # Hillshade is calculated based on illumination azimuth=270, elevation=45.
        terrain = ee.Terrain.products(dem)
        hillshade = terrain.select('hillshade').divide(500).toFloat()

        return img.addBands(slope.rename('slope')).addBands(hillshade.rename('hillshade'))


    # Ratio Vegetation Index # Global Environment Monitoring Index GEMI 
    def agregateBandswithSpectralIndex(self, img): # lista_bands
        # if 'ratio_median'
        ratioImgY = (img.expression(
            "float(b('nir_median') / b('red_median'))")
                                .rename(['ratio_median']).multiply(10000).toFloat()
        )

        ratioImgwet = (img.expression(
            "float(b('nir_median_wet') / b('red_median_wet'))")
                                .rename(['ratio_median_wet']).multiply(10000).toFloat()  
        )

        ratioImgdry = (img.expression(
            "float(b('nir_median_dry') / b('red_median_dry'))")
                                .rename(['ratio_median_dry']).multiply(10000).toFloat()        
        )

        rviImgY = (img.expression(
            "float(b('red_median') / b('nir_median'))")
                                .rename(['rvi_median']).add(1).multiply(10000).toFloat() 
        )

        rviImgWet = (img.expression(
            "float(b('red_median_wet') / b('nir_median_wet'))")
                                .rename(['rvi_median_wet']).add(1).multiply(10000).toFloat() 
        )

        rviImgDry = (img.expression(
            "float(b('red_median_dry') / b('nir_median_dry'))")
                                .rename(['rvi_median_dry']).add(1).multiply(10000).toFloat()  
        )

        ndviImgY = (img.expression(
            "float(b('nir_median') - b('red_median')) / (b('nir_median') + b('red_median'))")
                                .rename(['ndvi_median'])
                                .add(1).multiply(10000).toFloat()    
        )

        ndviImgWet = (img.expression(
                "float(b('nir_median_wet') - b('red_median_wet')) / (b('nir_median_wet') + b('red_median_wet'))").rename(['ndvi_median_wet'])
                            .add(1).multiply(10000).toFloat()
        )  

        ndviImgDry = (img.expression(
            "float(b('nir_median_dry') - b('red_median_dry')) / (b('nir_median_dry') + b('red_median_dry'))")
                                .rename(['ndvi_median_dry'])
                                .add(1).multiply(10000).toFloat()                           
        )

        ndbiImgY = (img.expression(
            "float(b('swir1_median') - b('nir_median')) / (b('swir1_median') + b('nir_median'))")
                                .rename(['ndbi_median'])
                                .add(1).multiply(10000).toFloat()   
        ) 

        ndbiImgWet = (img.expression(
            "float(b('swir1_median_wet') - b('nir_median_wet')) / (b('swir1_median_wet') + b('nir_median_wet'))")
                                .rename(['ndbi_median_wet'])
                                .add(1).multiply(10000).toFloat()  
        )

        ndbiImgDry = (img.expression(
            "float(b('swir1_median_dry') - b('nir_median_dry')) / (b('swir1_median_dry') + b('nir_median_dry'))")
                                .rename(['ndbi_median_dry'])
                                .add(1).multiply(10000).toFloat()
        )

        ndmiImgY = (img.expression(
                "float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")
                                .rename(['ndmi_median'])
                                .add(1).multiply(10000).toFloat()    
        )

        ndmiImgWet = (img.expression(
            "float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")
                                .rename(['ndmi_median_wet'])
                                .add(1).multiply(10000).toFloat()  
        )

        ndmiImgDry = (img.expression(
            "float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")
                                .rename(['ndmi_median_dry'])
                                .add(1).multiply(10000).toFloat()
        )

        nbrImgY = (img.expression(
            "float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")
                                .rename(['nbr_median'])
                                .add(1).multiply(10000).toFloat() 
        )   

        nbrImgWet = (img.expression(
            "float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")
                                .rename(['nbr_median_wet'])
                                .add(1).multiply(10000).toFloat()  
        )

        nbrImgDry = (img.expression(
            "float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")
                                .rename(['nbr_median_dry'])
                                .add(1).multiply(10000).toFloat() 
        )

        ndtiImgY = (img.expression(
            "float(b('swir1_median') - b('swir2_median')) / (b('swir1_median') + b('swir2_median'))")
                                .rename(['ndti_median'])
                                .add(1).multiply(10000).toFloat()   
        ) 

        ndtiImgWet = (img.expression(
            "float(b('swir1_median_wet') - b('swir2_median_wet')) / (b('swir1_median_wet') + b('swir2_median_wet'))")
                                .rename(['ndti_median_wet'])
                                .add(1).multiply(10000).toFloat()  
        )

        ndtiImgDry = (img.expression(
            "float(b('swir1_median_dry') - b('swir2_median_dry')) / (b('swir1_median_dry') + b('swir2_median_dry'))")
                                .rename(['ndti_median_dry'])
                                .add(1).multiply(10000).toFloat() 
        )

        ndwiImgY = (img.expression(
            "float(b('nir_median') - b('swir2_median')) / (b('nir_median') + b('swir2_median'))")
                                .rename(['ndwi_median'])
                                .add(1).multiply(10000).toFloat() 
        )      

        ndwiImgWet = (img.expression(
            "float(b('nir_median_wet') - b('swir2_median_wet')) / (b('nir_median_wet') + b('swir2_median_wet'))")
                                .rename(['ndwi_median_wet'])
                                .add(1).multiply(10000).toFloat()   
        )

        ndwiImgDry = (img.expression(
            "float(b('nir_median_dry') - b('swir2_median_dry')) / (b('nir_median_dry') + b('swir2_median_dry'))")
                                .rename(['ndwi_median_dry'])
                                .add(1).multiply(10000).toFloat()   
        )

        aweiY = (img.expression(
                            "float(4 * (b('green_median') - b('swir2_median')) - (0.25 * b('nir_median') + 2.75 * b('swir1_median')))"
                        ).rename("awei_median")
                        .add(1).multiply(10000).toFloat() 
        )

        aweiWet = (img.expression(
                            "float(4 * (b('green_median_wet') - b('swir2_median_wet')) - (0.25 * b('nir_median_wet') + 2.75 * b('swir1_median_wet')))"
                        ).rename("awei_median_wet")
                        .add(1).multiply(10000).toFloat() 
        )

        aweiDry = (img.expression(
                            "float(4 * (b('green_median_dry') - b('swir2_median_dry')) - (0.25 * b('nir_median_dry') + 2.75 * b('swir1_median_dry')))"
                        ).rename("awei_median_dry")
                        .add(1).multiply(10000).toFloat()  
        )

        iiaImgY = (img.expression(
                            "float((b('green_median') - 4 *  b('nir_median')) / (b('green_median') + 4 *  b('nir_median')))"
                        ).rename("iia_median")
                        .add(1).multiply(10000).toFloat()
        )
        
        iiaImgWet = (img.expression(
                            "float((b('green_median_wet') - 4 *  b('nir_median_wet')) / (b('green_median_wet') + 4 *  b('nir_median_wet')))"
                        ).rename("iia_median_wet")
                        .add(1).multiply(10000).toFloat()
        )

        iiaImgDry = (img.expression(
                            "float((b('green_median_dry') - 4 *  b('nir_median_dry')) / (b('green_median_dry') + 4 *  b('nir_median_dry')))"
                        ).rename("iia_median_dry")
                        .add(1).multiply(10000).toFloat()
        )

        eviImgY = (img.expression(
            "float(2.4 * (b('nir_median') - b('red_median')) / (1 + b('nir_median') + b('red_median')))")
                .rename(['evi_median'])
                .add(1).multiply(10000).toFloat() 
        )

        eviImgWet = (img.expression(
            "float(2.4 * (b('nir_median_wet') - b('red_median_wet')) / (1 + b('nir_median_wet') + b('red_median_wet')))")
                .rename(['evi_median_wet'])
                .add(1).multiply(10000).toFloat()   
        )

        eviImgDry = (img.expression(
            "float(2.4 * (b('nir_median_dry') - b('red_median_dry')) / (1 + b('nir_median_dry') + b('red_median_dry')))")
                .rename(['evi_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )

        gvmiImgY = (img.expression(
                        "float ((b('nir_median')  + 0.1) - (b('swir1_median') + 0.02)) / ((b('nir_median') + 0.1) + (b('swir1_median') + 0.02))" 
                    ).rename(['gvmi_median'])
                    .add(1).multiply(10000).toFloat() 
        )  

        gvmiImgWet = (img.expression(
                        "float ((b('nir_median_wet')  + 0.1) - (b('swir1_median_wet') + 0.02)) / ((b('nir_median_wet') + 0.1) + (b('swir1_median_wet') + 0.02))" 
                    ).rename(['gvmi_median_wet'])
                    .add(1).multiply(10000).toFloat()
        )

        gvmiImgDry = (img.expression(
                        "float ((b('nir_median_dry')  + 0.1) - (b('swir1_median_dry') + 0.02)) / ((b('nir_median_dry') + 0.1) + (b('swir1_median_dry') + 0.02))" 
                    ).rename(['gvmi_median_dry'])
                    .add(1).multiply(10000).toFloat() 
        )

        gcviImgAY = (img.expression(
            "float(b('nir_median')) / (b('green_median')) - 1")
                .rename(['gcvi_median'])
                .add(1).multiply(10000).toFloat()   
        )

        gcviImgAWet = (img.expression(
            "float(b('nir_median_wet')) / (b('green_median_wet')) - 1")
                .rename(['gcvi_median_wet'])
                .add(1).multiply(10000).toFloat() 
        )
                
        gcviImgADry = (img.expression(
            "float(b('nir_median_dry')) / (b('green_median_dry')) - 1")
                .rename(['gcvi_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )

        # Global Environment Monitoring Index GEMI
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgAY = (img.expression(
            "float((2 * (b('nir_median') * b('nir_median') - b('red_median') * b('red_median')) + 1.5 * b('nir_median')" +
            " + 0.5 * b('red_median')) / (b('nir_median') + b('green_median') + 0.5) )")
                .rename(['gemi_median'])
                .add(2).multiply(10000).toFloat()   
        ) 

        gemiImgAWet = (img.expression(
            "float((2 * (b('nir_median_wet') * b('nir_median_wet') - b('red_median_wet') * b('red_median_wet')) + 1.5 * b('nir_median_wet')" +
            " + 0.5 * b('red_median_wet')) / (b('nir_median_wet') + b('green_median_wet') + 0.5) )")
                .rename(['gemi_median_wet'])
                .add(2).multiply(10000).toFloat() 
        )

        gemiImgADry = (img.expression(
            "float((2 * (b('nir_median_dry') * b('nir_median_dry') - b('red_median_dry') * b('red_median_dry')) + 1.5 * b('nir_median_dry')" +
            " + 0.5 * b('red_median_dry')) / (b('nir_median_dry') + b('green_median_dry') + 0.5) )")
                .rename(['gemi_median_dry'])
                .add(2).multiply(10000).toFloat() 
        )
         # Chlorophyll vegetation index CVI
        cviImgAY = (img.expression(
            "float(b('nir_median') * (b('green_median') / (b('blue_median') * b('blue_median'))))")
                .rename(['cvi_median'])
                .add(1).multiply(10000).toFloat()  
        )

        cviImgAWet = (img.expression(
            "float(b('nir_median_wet') * (b('green_median_wet') / (b('blue_median_wet') * b('blue_median_wet'))))")
                .rename(['cvi_median_wet'])
                .add(1).multiply(10000).toFloat()
        )

        cviImgADry = (img.expression(
            "float(b('nir_median_dry') * (b('green_median_dry') / (b('blue_median_dry') * b('blue_median_dry'))))")
                .rename(['cvi_median_dry'])
                .add(1).multiply(10000).toFloat()  
        )
        # Green leaf index  GLI
        gliImgY = (img.expression(
            "float((2 * b('green_median') - b('red_median') - b('blue_median')) / (2 * b('green_median') + b('red_median') + b('blue_median')))")
                .rename(['gli_median'])
                .add(1).multiply(10000).toFloat()
        )    

        gliImgWet = (img.expression(
            "float((2 * b('green_median_wet') - b('red_median_wet') - b('blue_median_wet')) / (2 * b('green_median_wet') + b('red_median_wet') + b('blue_median_wet')))")
                .rename(['gli_median_wet'])
                .add(1).multiply(10000).toFloat()   
        )

        gliImgDry = (img.expression(
            "float((2 * b('green_median_dry') - b('red_median_dry') - b('blue_median_dry')) / (2 * b('green_median_dry') + b('red_median_dry') + b('blue_median_dry')))")
                .rename(['gli_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )
        # Shape Index  IF 
        shapeImgAY = (img.expression(
            "float((2 * b('red_median') - b('green_median') - b('blue_median')) / (b('green_median') - b('blue_median')))")
                .rename(['shape_median']).toFloat()  
        )

        shapeImgAWet = (img.expression(
            "float((2 * b('red_median_wet') - b('green_median_wet') - b('blue_median_wet')) / (b('green_median_wet') - b('blue_median_wet')))")
                .rename(['shape_median_wet']).toFloat() 
        )

        shapeImgADry = (img.expression(
            "float((2 * b('red_median_dry') - b('green_median_dry') - b('blue_median_dry')) / (b('green_median_dry') - b('blue_median_dry')))")
                .rename(['shape_median_dry']).toFloat()  
        )
        # Aerosol Free Vegetation Index (2100 nm)
        afviImgAY = (img.expression(
            "float((b('nir_median') - 0.5 * b('swir2_median')) / (b('nir_median') + 0.5 * b('swir2_median')))")
                .rename(['afvi_median'])
                .add(1).multiply(10000).toFloat()  
        )

        afviImgAWet = (img.expression(
            "float((b('nir_median_wet') - 0.5 * b('swir2_median_wet')) / (b('nir_median_wet') + 0.5 * b('swir2_median_wet')))")
                .rename(['afvi_median_wet'])
                .add(1).multiply(10000).toFloat()
        )

        afviImgADry = (img.expression(
            "float((b('nir_median_dry') - 0.5 * b('swir2_median_dry')) / (b('nir_median_dry') + 0.5 * b('swir2_median_dry')))")
                .rename(['afvi_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )
        # Advanced Vegetation Index
        aviImgAY = (img.expression(
            "float((b('nir_median')* (1.0 - b('red_median')) * (b('nir_median') - b('red_median'))) ** 1/3)")
                .rename(['avi_median']).divide(100).toFloat()   
        )

        aviImgAWet = (img.expression(
            "float((b('nir_median_wet')* (1.0 - b('red_median_wet')) * (b('nir_median_wet') - b('red_median_wet'))) ** 1/3)")
                .rename(['avi_median_wet']).divide(100).toFloat()
        )

        aviImgADry = (img.expression(
            "float((b('nir_median_dry')* (1.0 - b('red_median_dry')) * (b('nir_median_dry') - b('red_median_dry'))) ** 1/3)")
                .rename(['avi_median_dry']).divide(100).toFloat()     
        )
        #  NDDI Normalized Differenece Drought Index
        nddiImg = (ndviImgY.addBands(ndwiImgY).expression(
                "float((b('ndvi_median') - b('ndwi_median')) / (b('ndvi_median') + b('ndwi_median')))"
            ).rename(['nddi_median'])
            .add(1).multiply(10000).toFloat() )
        
        nddiImgWet = (ndviImgWet.addBands(ndwiImgWet).expression(
                "float((b('ndvi_median_wet') - b('ndwi_median_wet')) / (b('ndvi_median_wet') + b('ndwi_median_wet')))"
            ).rename(['nddi_median_wet'])
            .add(1).multiply(10000).toFloat() )
        
        nddiImgDry = (ndviImgDry.addBands(ndwiImgDry).expression(
                "float((b('ndvi_median_dry') - b('ndwi_median_dry')) / (b('ndvi_median_dry') + b('ndwi_median_dry')))"
            ).rename(['nddi_median_dry'])
            .add(1).multiply(10000).toFloat())
        
        # Bare Soil Index
        bsiImgY = (img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
                .rename(['bsi_median'])
                .add(1).multiply(10000).toFloat()  
        )

        bsiImgWet = (img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
                .rename(['bsi_median_wet'])
                .add(1).multiply(10000).toFloat()
        )

        bsiImgDry = (img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
                .rename(['bsi_median_dry'])
                .add(1).multiply(10000).toFloat()
        )
        
        # BRBA	Band Ratio for Built-up Area  
        brbaImgY = (img.expression(
            "float(b('red_median') / b('swir1_median'))")
                .rename(['brba_median'])
                .add(1).multiply(10000).toFloat()   
        )

        brbaImgWet = (img.expression(
            "float(b('red_median_wet') / b('swir1_median_wet'))")
                .rename(['brba_median_wet'])
                .add(1).multiply(10000).toFloat()
        )

        brbaImgDry = (img.expression(
            "float(b('red_median_dry') / b('swir1_median_dry'))")
                .rename(['brba_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )

        # DSWI5	Disease-Water Stress Index 5
        dswi5ImgY = (img.expression(
            "float((b('nir_median') + b('green_median')) / (b('swir1_median') + b('red_median')))")
                .rename(['dswi5_median'])
                .add(1).multiply(10000).toFloat() 
        )

        dswi5ImgWet = (img.expression(
            "float((b('nir_median_wet') + b('green_median_wet')) / (b('swir1_median_wet') + b('red_median_wet')))")
                .rename(['dswi5_median_wet'])
                .add(1).multiply(10000).toFloat() 
        )

        dswi5ImgDry = (img.expression(
            "float((b('nir_median_dry') + b('green_median_dry')) / (b('swir1_median_dry') + b('red_median_dry')))")
                .rename(['dswi5_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )

        # LSWI	Land Surface Water Index
        lswiImgY = (img.expression(
            "float((b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median')))")
                .rename(['lswi_median'])
                .add(1).multiply(10000).toFloat()
        )  

        lswiImgWet = (img.expression(
            "float((b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet')))")
                .rename(['lswi_median_wet'])
                .add(1).multiply(10000).toFloat()
        )

        lswiImgDry = (img.expression(
            "float((b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry')))")
                .rename(['lswi_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )
        
        # MBI	Modified Bare Soil Index
        mbiImgY = (img.expression(
            "float(((b('swir1_median') - b('swir2_median') - b('nir_median')) /" + 
                " (b('swir1_median') + b('swir2_median') + b('nir_median'))) + 0.5)")
                    .rename(['mbi_median'])
                    .add(1).multiply(10000).toFloat() 
        )

        mbiImgWet = (img.expression(
            "float(((b('swir1_median_wet') - b('swir2_median_wet') - b('nir_median_wet')) /" + 
                " (b('swir1_median_wet') + b('swir2_median_wet') + b('nir_median_wet'))) + 0.5)")
                    .rename(['mbi_median_wet'])
                    .add(1).multiply(10000).toFloat() 
        )

        mbiImgDry = (img.expression(
            "float(((b('swir1_median_dry') - b('swir2_median_dry') - b('nir_median_dry')) /" + 
                " (b('swir1_median_dry') + b('swir2_median_dry') + b('nir_median_dry'))) + 0.5)")
                    .rename(['mbi_median_dry'])
                    .add(1).multiply(10000).toFloat() 
        )

        # UI	Urban Index	urban
        uiImgY = (img.expression(
            "float((b('swir2_median') - b('nir_median')) / (b('swir2_median') + b('nir_median')))")
                .rename(['ui_median'])
                .add(1).multiply(10000).toFloat()  
        )

        uiImgWet = (img.expression(
            "float((b('swir2_median_wet') - b('nir_median_wet')) / (b('swir2_median_wet') + b('nir_median_wet')))")
                .rename(['ui_median_wet'])
                .add(1).multiply(10000).toFloat() 
        )

        uiImgDry = (img.expression(
            "float((b('swir2_median_dry') - b('nir_median_dry')) / (b('swir2_median_dry') + b('nir_median_dry')))")
                .rename(['ui_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )

        # OSAVI	Optimized Soil-Adjusted Vegetation Index
        osaviImgY = (img.expression(
            "float(b('nir_median') - b('red_median')) / (0.16 + b('nir_median') + b('red_median'))")
                .rename(['osavi_median'])
                .add(1).multiply(10000).toFloat() 
        )

        osaviImgWet = (img.expression(
            "float(b('nir_median_wet') - b('red_median_wet')) / (0.16 + b('nir_median_wet') + b('red_median_wet'))")
                .rename(['osavi_median_wet'])
                .add(1).multiply(10000).toFloat() 
        )

        osaviImgDry = (img.expression(
            "float(b('nir_median_dry') - b('red_median_dry')) / (0.16 + b('nir_median_dry') + b('red_median_dry'))")
                .rename(['osavi_median_dry'])
                .add(1).multiply(10000).toFloat()  
        )

        # MSAVI	modifyed Soil-Adjusted Vegetation Index
        # [ 2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR-RED)) ]/2
        msaviImgY = (img.expression(
            "float((2 * b('nir_median') + 1 - sqrt((2 * b('nir_median') + 1) * (2 * b('nir_median') + 1) - 8 * (b('nir_median') - b('red_median'))))/2)")
                .rename(['msavi_median']).toFloat() 
        )

        msaviImgWet = (img.expression(
            "float((2 * b('nir_median_wet') + 1 - sqrt((2 * b('nir_median_wet') + 1) * (2 * b('nir_median_wet') + 1) - 8 * (b('nir_median_wet') - b('red_median_wet'))))/2)")
                .rename(['msavi_median_wet']).toFloat() 
        )

        msaviImgDry = (img.expression(
            "float((2 * b('nir_median_dry') + 1 - sqrt((2 * b('nir_median_dry') + 1) * (2 * b('nir_median_dry') + 1) - 8 * (b('nir_median_dry') - b('red_median_dry'))))/2)")
                .rename(['msavi_median_dry']).toFloat()  
        )   

        # GSAVI	Optimized Soil-Adjusted Vegetation Index
        # (NIR - GREEN) /(0.5 + NIR + GREEN) * 1.5) 
        gsaviImgY = (img.expression(
            "float(b('nir_median') - b('green_median')) / ((0.5 + b('nir_median') + b('green_median')) * 1.5)")
                .rename(['gsavi_median']).toFloat() 
        )

        gsaviImgWet = (img.expression(
            "float(b('nir_median_wet') - b('green_median_wet')) / ((0.5 + b('nir_median_wet') + b('green_median_wet')) * 1.5)")
                .rename(['gsavi_median_wet']).toFloat() 
        )

        gsaviImgDry = (img.expression(
            "float(b('nir_median_dry') - b('green_median_dry')) / ((0.5 + b('nir_median_dry') + b('green_median_dry')) * 1.5)")
                .rename(['gsavi_median_dry']).toFloat()
        )
        
        # Normalized Difference Red/Green Redness Index  RI
        riImgY = (img.expression(
            "float(b('nir_median') - b('green_median')) / (b('nir_median') + b('green_median'))")
                .rename(['ri_median'])
                .add(1).multiply(10000).toFloat()   
        )

        riImgWet = (img.expression(
            "float(b('nir_median_wet') - b('green_median_wet')) / (b('nir_median_wet') + b('green_median_wet'))")
                .rename(['ri_median_wet'])
                .add(1).multiply(10000).toFloat()
        )

        riImgDry = (img.expression(
            "float(b('nir_median_dry') - b('green_median_dry')) / (b('nir_median_dry') + b('green_median_dry'))")
                .rename(['ri_median_dry'])
                .add(1).multiply(10000).toFloat() 
        )

        # Moisture Stress Index (MSI)
        msiImgY = (img.expression(
            "float( b('nir_median') / b('swir1_median'))")
                .rename(['msi_median'])
                .add(1).multiply(10000).toFloat() 
        )
        
        msiImgWet = (img.expression(
            "float( b('nir_median_wet') / b('swir1_median_wet'))")
                .rename(['msi_median_wet'])
                .add(1).multiply(10000).toFloat() 
        )

        msiImgDry = (img.expression(
            "float( b('nir_median_dry') / b('swir1_median_dry'))")
                .rename(['msi_median_dry'])
                .add(1).multiply(10000).toFloat()
        )

        priImgY = (img.expression(
                                "float((b('green_median') - b('blue_median')) / (b('green_median') + b('blue_median')))"
                            ).rename(['pri_median'])   
        )
        spriImgY =   (priImgY.expression(
                                "float((b('pri_median') + 1) / 2)").rename(['spri_median']).toFloat()  )

        priImgWet = (img.expression(
                                "float((b('green_median_wet') - b('blue_median_wet')) / (b('green_median_wet') + b('blue_median_wet')))"
                            ).rename(['pri_median_wet'])   
        )
        spriImgWet =   (priImgWet.expression(
                                "float((b('pri_median_wet') + 1) / 2)").rename(['spri_median_wet']).toFloat())

        priImgDry = (img.expression(
                                "float((b('green_median') - b('blue_median')) / (b('green_median') + b('blue_median')))"
                            ).rename(['pri_median_dry'])   
        )
        spriImgDry =   (priImgDry.expression(
                                "float((b('pri_median_dry') + 1) / 2)").rename(['spri_median_dry']).toFloat())

        # ndviImgY    ndviImgWet      ndviImgDry
        # co2FluxImg = ndviImgY.multiply(spriImgY).rename(['co2flux_median'])   
        # co2FluxImgWet = ndviImgWet.multiply(spriImgWet).rename(['co2flux_median_wet']) 
        # co2FluxImgDry = ndviImgDry.multiply(spriImgDry).rename(['co2flux_median_dry']) 

        # img = img.toInt()                
        textura2 = img.select('nir_median').multiply(10000).toUint16().glcmTexture(3)  
        contrastnir = textura2.select('nir_median_contrast').divide(10000).toFloat()
        textura2Dry = img.select('nir_median_dry').multiply(10000).toUint16().glcmTexture(3)  
        contrastnirDry = textura2Dry.select('nir_median_dry_contrast').divide(10000).toFloat()
        #
        textura2R = img.select('red_median').multiply(10000).toUint16().glcmTexture(3)  
        contrastred = textura2R.select('red_median_contrast').divide(10000).toFloat()
        textura2RDry = img.select('red_median_dry').multiply(10000).toUint16().glcmTexture(3)  
        contrastredDry = textura2RDry.select('red_median_dry_contrast').divide(10000).toFloat()
        
        return (
            img.addBands(ratioImgY).addBands(ratioImgwet).addBands(ratioImgdry)
                .addBands(rviImgY).addBands(rviImgWet).addBands(rviImgDry)
                .addBands(ndviImgY).addBands(ndviImgWet).addBands(ndviImgDry)
                .addBands(ndbiImgY).addBands(ndbiImgWet).addBands(ndbiImgDry)
                .addBands(ndmiImgY).addBands(ndmiImgWet).addBands(ndmiImgDry)
            #     .addBands(nbrImgY).addBands(nbrImgWet).addBands(nbrImgDry)
                .addBands(ndtiImgY).addBands(ndtiImgWet).addBands(ndtiImgDry)
                .addBands(ndwiImgY).addBands(ndwiImgWet).addBands(ndwiImgDry)
                .addBands(aweiY).addBands(aweiWet).addBands(aweiDry)
                .addBands(iiaImgY).addBands(iiaImgWet).addBands(iiaImgDry)
                .addBands(eviImgY).addBands(eviImgWet).addBands(eviImgDry)
                .addBands(gvmiImgY).addBands(gvmiImgWet).addBands(gvmiImgDry)
                .addBands(gcviImgAY).addBands(gcviImgAWet).addBands(gcviImgADry)
                .addBands(gemiImgAY).addBands(gemiImgAWet).addBands(gemiImgADry)
                .addBands(cviImgAY).addBands(cviImgAWet).addBands(cviImgADry)
                .addBands(gliImgY).addBands(gliImgWet).addBands(gliImgDry)
                .addBands(shapeImgAY).addBands(shapeImgAWet).addBands(shapeImgADry)
                .addBands(afviImgAY).addBands(afviImgAWet).addBands(afviImgADry)
                .addBands(aviImgAY).addBands(aviImgAWet).addBands(aviImgADry)
                .addBands(nddiImg).addBands(nddiImgWet).addBands(nddiImgDry)
                .addBands(bsiImgY).addBands(bsiImgWet).addBands(bsiImgDry)
                .addBands(brbaImgY).addBands(brbaImgWet).addBands(brbaImgDry)
                .addBands(dswi5ImgY).addBands(dswi5ImgWet).addBands(dswi5ImgDry)
                .addBands(lswiImgY).addBands(lswiImgWet).addBands(lswiImgDry)
                .addBands(mbiImgY).addBands(mbiImgWet).addBands(mbiImgDry)
                .addBands(uiImgY).addBands(uiImgWet).addBands(uiImgDry)
                .addBands(osaviImgY).addBands(osaviImgWet).addBands(osaviImgDry)
            #     # .addBands(msaviImgY).addBands(msaviImgWet).addBands(msaviImgDry)
            #     # .addBands(gsaviImgY).addBands(gsaviImgWet).addBands(gsaviImgDry)
                .addBands(riImgY).addBands(riImgWet).addBands(riImgDry)
            #     .addBands(msiImgY).addBands(msiImgWet).addBands(msiImgDry)
            #     .addBands(spriImgY).addBands(spriImgWet).addBands(spriImgDry)
                .addBands(contrastnir).addBands(contrastred)
                .addBands(contrastnirDry).addBands(contrastredDry) 
        )

    # def calculateBandsIndexEVI(self, img):
        
    #     eviImgY = img.expression(
    #         "float(2.4 * (b('nir') - b('red')) / (1 + b('nir') + b('red')))")\
    #             .rename(['evi']).toFloat() 

    #     return img.addBands(eviImgY)

    # def agregateBandsIndexLAI(self, img):
    #     laiImgY = img.expression(
    #         "float(3.618 * (b('evi_median') - 0.118))")\
    #             .rename(['lai_median']).toFloat()
    
    #     return img.addBands(laiImgY)    

    def GET_NDFIA(self, IMAGE, sufixo):
            
        lstBands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
        lstBandsSuf = [bnd + sufixo for bnd in lstBands]
        lstFractions = ['gv', 'shade', 'npv', 'soil', 'cloud']
        lstFractionsSuf = [frac + sufixo for frac in lstFractions]
        
        endmembers = [            
            [0.05, 0.09, 0.04, 0.61, 0.30, 0.10], #/*gv*/
            [0.14, 0.17, 0.22, 0.30, 0.55, 0.30], #/*npv*/
            [0.20, 0.30, 0.34, 0.58, 0.60, 0.58], #/*soil*/
            [0.0 , 0.0,  0.0 , 0.0 , 0.0 , 0.0 ], #/*Shade*/
            [0.90, 0.96, 0.80, 0.78, 0.72, 0.65]  #/*cloud*/
        ];

        fractions = (ee.Image(IMAGE).select(lstBandsSuf)
                                .unmix(endmembers= endmembers, sumToOne= True, nonNegative= True)
                                .float())
        fractions = fractions.rename(lstFractions)
        # // print(UNMIXED_IMAGE);
        # GVshade = GV /(1 - SHADE)
        # NDFIa = (GVshade - SOIL) / (GVshade + )
        NDFI_ADJUSTED = fractions.expression(
                                "float(((b('gv') / (1 - b('shade'))) - b('soil')) / ((b('gv') / (1 - b('shade'))) + b('npv') + b('soil')))"
                                ).rename('ndfia')

        NDFI_ADJUSTED = NDFI_ADJUSTED.toFloat()
        fractions = fractions.rename(lstFractionsSuf)
        RESULT_IMAGE = (fractions.toFloat()
                            .addBands(NDFI_ADJUSTED))

        return ee.Image(RESULT_IMAGE).toFloat()

    def agregate_Bands_SMA_NDFIa(self, img):
        
        indSMA_median =  self.GET_NDFIA(img, '_median')
        indSMA_med_wet =  self.GET_NDFIA(img, '_median_wet')
        indSMA_med_dry =  self.GET_NDFIA(img, '_median_dry')

        return img.addBands(indSMA_median).addBands(indSMA_med_wet).addBands(indSMA_med_dry)

    def agregateBandsContextoEstrutural(self, img):
        """
        Contexto estrutural espacial (kernel 7x7) sobre 7 índices-chave.
        Produz 14 bandas: {banda}_mean e {banda}_stdDev para cada entrada.
        Requer que ndfia, osavi_median, gcvi_median, avi_median,
        bsi_median, ui_median e awei_median já estejam no img.
        """
        kernel = ee.Kernel.square(7)
        bandas_textura = [
            'osavi_median', 'gcvi_median', 'avi_median',
            'ndfia', 'bsi_median', 'ui_median', 'awei_median'
        ]
        img_base = img.select(bandas_textura)
        redutor_combo = ee.Reducer.mean().combine(
            reducer2=ee.Reducer.stdDev(),
            sharedInputs=True
        )
        contexto_espacial = img_base.reduceNeighborhood(
            reducer=redutor_combo,
            kernel=kernel
        )
        return img.addBands(contexto_espacial)

    def CalculateIndice(self, imagem):
        imageW = self.agregateBandswithSpectralIndex(imagem)
        imageW = self.agregate_Bands_SMA_NDFIa(imageW)      # gera ndfia (exigido pelo contexto)
        imageW = self.addSlopeAndHilshade(imageW)
        imageW = self.agregateBandsContextoEstrutural(imageW)  # 14 bandas de contexto espacial
        return imageW     
       

    def get_bands_mosaicos (self):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        # retornando as 3 listas em 1 só
        return band_year + band_wets + band_drys

    def get_list_bands_FS(self, dict_tmp):
        numOtimo = 0
        lst_FS = []
        for jj, par in  enumerate(zip(dict_tmp['bandas'], dict_tmp['ranking'])):
            if par[1] == 1 or jj < self.options['numero_bndFS']:
                # print(f">> {jj} -- {par[0]} <> {par[1]}")
                lst_FS.append(par[0])
                if par[1] == 1:
                    numOtimo += 1

        return lst_FS, numOtimo

    def get_dict_hiperTuning(self, dictHP, yyear):
        hiperPM = None
        lst_year = list(dictHP.keys())
        lst_year.remove('2025')
        if str(yyear) in lst_year:     
            # print(dictHP[yyear])           
            hiperPM = dictHP[str(yyear)]
        
        elif int(yyear) < int(lst_year[0]):
            hiperPM = dictHP[lst_year[0]]

        else:
            hiperPM = dictHP[lst_year[-1]]
    
        return hiperPM

    def scaleToNegOneToOne(self, image, imgMin, imgMax):
        """
            Escalona linearmente uma imagem para o intervalo [-1, 1]
            usando a API Python do GEE.
        """
        # expression = '-1.0 + ( (img - imgMin) * 2.0 ) / (imgMax - imgMin)'
        # scaled_image = image.expression(expression, {
        #     'img': image,
        #     'imgMin': imgMin,
        #     'imgMax': imgMax
        # })
        scaled_image = image.subtract(ee.Image.constant(imgMin))
        scaled_image = scaled_image.divide(ee.Image.constant(imgMax).subtract(ee.Image.constant(imgMin)))
        scaled_image = scaled_image.add(1).multiply(10000)

        # Renomeia as bandas para os nomes originais e copia as propriedades
        return scaled_image.rename(image.bandNames()).copyProperties(image, image.propertyNames())

    
    def get_ROIs_from_neighbor(self, lst_bacias, asset_root, esp_bacia):

        featGeral = ee.FeatureCollection([])
        for jbasin in lst_bacias:
            nameFeatROIs = f"rois_fromGrade_{jbasin}"
            dir_asset_rois = os.path.join(asset_root, nameFeatROIs)
            feat_tmp = ee.FeatureCollection(dir_asset_rois)
            if jbasin != esp_bacia:
                feat_tmp = feat_tmp.randomColumn().filter(ee.Filter.lt("random", 0.3))
                
            featGeral = featGeral.merge(feat_tmp)

        return featGeral


    def convert_distribuition_ideal(self, fc_ROIs):

        lst_class_present = [3,4,12,15,20,24,25,29,33,41]
        lst_class_end = [3,4,12,15,18,25,25,29,33,18]
        big_ROIs = [3, 4, 15]
        dict_prop = {
            3: 900,
            4: 1200,
            15: 1000,
        }
        fc_ROIs = (fc_ROIs.filter(ee.Filter.inList('class', lst_class_present))
                            .remap(lst_class_present, lst_class_end, 'class')
        )
        fc_other =fc_ROIs.filter(ee.Filter.inList('class', big_ROIs).Not())
        for nclass in big_ROIs:
            fc_tmp = fc_ROIs.filter(ee.Filter.eq('class', nclass))
            size_fc = ee.Number(fc_tmp.size())
            porcent = ee.Number(dict_prop[nclass]).divide(size_fc)
            fc_tmp = fc_tmp.randomColumn("rc")
            fc_tmp = fc_tmp.filter(ee.Filter.lt('rc', porcent))
            # print(f"classe {nclass} >>> {fc_tmp.size().getInfo()}")

            fc_other = fc_other.merge(fc_tmp)

        return fc_other




    def apply_minority_boost(self, fc_train):
        """
        Duplica amostras de classes sub-representadas para compensar o viés do GTB.
        Operação puramente server-side (sem getInfo()).

        Estratégia de multiplicação por classe (ajustar conforme distribuição da bacia):
          - Classes raras (22=Afloramento, 29=Rocha): até 3x
          - Classes médias (25=Outras Não-Veg, 33=Água): 2x
          - Demais classes: passagem simples

        Para ativar, descomente a chamada em iterate_bacias.
        """
        CLASS_BOOST = {22: 3, 29: 3, 25: 2, 33: 2}
        minority = ee.List(list(CLASS_BOOST.keys()))
        fc_boosted = fc_train.filter(ee.Filter.inList('class', minority).Not())
        for cls, mult in CLASS_BOOST.items():
            fc_cls = fc_train.filter(ee.Filter.eq('class', cls))
            for _ in range(mult):
                fc_boosted = fc_boosted.merge(fc_cls)
        return fc_boosted

    def iterate_bacias(self, _nbacia, makeProb):

        # loading geometry bacim
        baciabuffer = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                            ee.Filter.eq('nunivotto4', _nbacia))
        print(f"know about the geometry 'nunivotto4' >>  {_nbacia} loaded < {baciabuffer.size().getInfo()} > geometry" )   
        baciabuffer = baciabuffer.map(lambda f: f.set('id_codigo', 1))
        bacia_raster =  baciabuffer.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        baciabuffer = baciabuffer.geometry()
        # sys.exit()
        
        # https://code.earthengine.google.com/48effe10e1fffbedf2076a53b472be0e?asset=projects%2Fgeo-data-s%2Fassets%2Ffotovoltaica%2Fversion_4%2Freg_00000000000000000017_2015_10_pred_g2c
        
        # # lista de classe por bacia 
        # lstClassesUn = self.options['dict_classChangeBa'][self.tesauroBasin[_nbacia]]
        # print(f" ==== lista de classes ness bacia na bacia < {_nbacia} >  ====")
        # print(f" ==== {lstClassesUn} ======" )
        print("---------------------------------------------------------------")
        pmtroClass = copy.deepcopy(self.options['pmtGTB'])

        # tesauroBasin = arqParams.tesauroBasin
        lsNamesBaciasViz = arqParams.basinVizinhasNew[_nbacia]
        lstSoViz =  [kk for kk in lsNamesBaciasViz if kk != _nbacia]
        print("lista de Bacias vizinhas", lstSoViz)

        ## get ROIs  self.options['asset_ROIs_merge']
        rois_vizinhos = self.get_ROIs_from_neighbor(lstSoViz, self.options['asset_ROIs_merge'], _nbacia)

        # sys.exit()
        # imglsClasxanos = ee.Image().byte()

        for nyear in self.lst_year[:]:
            bandActiva = 'classification_' + str(nyear)
            nomec_check = f"{_nbacia}_{nyear}_GTB_col2S2-v_{self.options['version']}"
            nomeDesc_check = 'BACIA_' + nomec_check
            if nomeDesc_check in self.lstIDassetS:
                print(f"  ↷ {nomec_check} já exportado — pulando ano {nyear}")
                continue
            print(f"  processando: {bandActiva}")

            dict_basinFS = self.dictBand_FS[_nbacia][str(nyear)]
            if nyear == 2025:       
                dict_basinFS = self.dictBand_FS[_nbacia]['2016']

            bandas_fromFS, otimas = self.get_list_bands_FS(dict_basinFS)
            if otimas > self.options['numero_bndFS']: 
                print(f"we load {len(bandas_fromFS)} features << OTIMAS >> from Features Selection process")
            else:
                print(f"we load {len(bandas_fromFS)} features from Features Selection process")
            print(' as primeiras 3 \n ==> ', bandas_fromFS[:3])
            
            nomec = f"{_nbacia}_{nyear}_GTB_col10-v_{self.options['version']}"

            print(f"**** filtered by year {nyear} >> bacia {_nbacia}")
            if nyear < 2024:
                img_recMosaic = (ee.ImageCollection(self.options['asset_mosaic_sentinelp1'])
                                    .filter(ee.Filter.inList('biome', self.options['biomas']))
                                    .filterBounds(baciabuffer) 
                                    .filter(ee.Filter.eq('year', nyear))    
                                    # .select(self.band_mosaic)                                
                        )       
                    
            else:
                img_recMosaic = (ee.ImageCollection(self.options['asset_mosaic_sentinelp2'])
                                    .filter(ee.Filter.inList('biome', self.options['biomas']))
                                    .filterBounds(baciabuffer) 
                                    .filter(ee.Filter.eq('year', nyear))
                                    # .select(self.band_mosaic)
                        )  
            
            # print(f" we loaded {img_recMosaic.size().getInfo()} images from mosaic Mapbiomas")
            img_recMosaic = img_recMosaic.median().updateMask(bacia_raster).toFloat()

            img_recMosaicnewB = self.CalculateIndice(img_recMosaic)
            # print(f" we have {len(img_recMosaicnewB.bandNames().getInfo())} bands into mosaic ")

            if nyear > 2016 and nyear < 2025:
                print(f"**** filtered by year {nyear} >> {_nbacia}")
                date_inic = ee.Date.fromYMD(nyear, 1, 1)
                img_recEmbedding = (ee.ImageCollection(self.options['asset_embedding'])
                                    .filterBounds(baciabuffer) 
                                    .filterDate(date_inic, date_inic.advance(1, 'year'))
                        )   
                img_recEmb = img_recEmbedding.mosaic().updateMask(bacia_raster).toFloat() 

                val_min = self.paramInt['min'][str(nyear)]
                val_max = self.paramInt['max'][str(nyear)]
                img_recEmbNew = self.scaleToNegOneToOne(img_recEmb, val_min, val_max)
                time.sleep(3)# esperar 8 segundos

                img_recMosaicnewB = img_recMosaicnewB.addBands(img_recEmbNew)

            # print(f" we have  {len(img_recMosaicnewB.bandNames().getInfo())} bands into mosaic ")  
            # print(img_recMosaicnewB.bandNames().getInfo())   
            # if nyear < 2025:
            ROIs_toTrain = rois_vizinhos.filter(ee.Filter.eq('year', nyear))
            # convert_distribuition_ideal removido: amostras já balanceadas pelo downsampling supervisionado
            # Para boosting adicional de classes raras, descomente: ROIs_toTrain = self.apply_minority_boost(ROIs_toTrain)
            # ROIs_toTrain = ROIs_toTrain.remap(self.classes_old, self.classes_desej, 'class')
            # ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.gt('class', 0))
            # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
            # print(ROIs_toTrain.first().propertyNames().getInfo())
            
            # print(self.dictHiperPmtTuning[_nbacia])
            dict_HpT = self.get_dict_hiperTuning(self.dictHiperPmtTuning[_nbacia], nyear)
            pmtroClass['shrinkage'] = dict_HpT['clf__learning_rate']
            pmtroClass['numberOfTrees'] = dict_HpT['clf__max_iter']
            pmtroClass['maxNodes'] = dict_HpT['clf__max_leaf_nodes']
            print("pmtros Classifier ==> ", pmtroClass)
            bnd_exc = [
                'rvi_median_dry', 'bsi_median_wet', 'bsi_median_dry', 
                'wetness_median_wet', 'wetness_median', 'wetness_median_dry',
                'brightness_median', 'brightness_median_dry', 'brightness_median_wet'
            ]
            for bnb_ext in bnd_exc:
                try:
                    bandas_fromFS.remove(bnb_ext)
                except:
                    pass
            # print(bandas_fromFS)
            # sys.exit()
            # ee.Classifier.smileGradientTreeBoost(numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed)
            # print("antes de classificar ", ROIs_toTrain.first().propertyNames().getInfo())

            classifierGTB = ee.Classifier.smileGradientTreeBoost(**pmtroClass).train(
                                                ROIs_toTrain, 'class', bandas_fromFS)              
            classifiedGTB = img_recMosaicnewB.classify(classifierGTB, bandActiva)        
            # print("classificando!!!! ")
            # sys.exit()
            # se for o primeiro ano cria o dicionario e seta a variavel como
            # o resultado da primeira imagem classificada
            print("addicionando classification bands = " , bandActiva)      
                 
            # if self.options['anoIntInit'] == nyear:
            #     print ('entrou em <<<< 2016 >>>, no modelo ')            
  
            #     imglsClasxanos = copy.deepcopy(classifiedGTB)                                        
                           
            #     mydict = {
            #         'id_bacia': _nbacia,
            #         'version': self.options['version'],
            #         'biome': self.options['bioma'],
            #         'classifier': 'GTB',
            #         'collection': '2.0',
            #         'sensor': 'Sentinel S2',
            #         'source': 'geodatin',  
            #         'year': nyear              
            #     }
            #     # imglsClasxanos = imglsClasxanos.set(mydict)
            #     classifiedGTB = classifiedGTB.set(mydict)
            #         ##### se nao, adiciona a imagem como uma banda a imagem que ja existia
            # else:
            #     # print("Adicionando o mapa do ano  ", nyear)
            #     # print(" ", classifiedGTB.bandNames().getInfo())     
            #     imglsClasxanos = imglsClasxanos.addBands(classifiedGTB)  


            mydict = {
                    'id_bacia': _nbacia,
                    'version': self.options['version'],
                    'biome': self.options['bioma'],
                    'classifier': 'GTB',
                    'collection': '2.0',
                    'sensor': 'Sentinel S2',
                    'source': 'geodatin',  
                    'year': nyear              
                }
            # imglsClasxanos = imglsClasxanos.set(mydict)
            classifiedGTB = classifiedGTB.set(mydict)

            nomec = f"{_nbacia}_{nyear}_GTB_col2S2-v_{self.options['version']}" 
            # classifiedGTB = classifiedGTB.select(self.options['lsBandasMap'])    
            classifiedGTB = classifiedGTB.set("system:footprint", baciabuffer.coordinates())
            # classifiedGTB = classifiedGTB.set("system:footprint", baciabuffer.coordinates())
            # exporta bacia   .coordinates()
            self.processoExportar(classifiedGTB, baciabuffer, nomec)


    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF, regionB, nameB):
        nomeDesc = 'BACIA_'+ str(nameB)
        idasset =  os.path.join(self.options['assetOut'] , nomeDesc)
        
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':ee.Geometry(regionB), #['coordinates'] .getInfo()
            'scale': 10, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"},
            # 'priority': 1000
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))


mosaico = 'mosaico_mapbiomas'
param = {    
    'bioma': "CAATINGA", #nome do bioma setado nos metadados
    'biomas': ["CAATINGA","CERRADO", "MATAATLANTICA"],
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga49div",
    'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/Classifier/Classify_layers',
    'bnd_L': ['blue','green','red','nir','swir1','swir2'],
    'version': 4,
    'lsBandasMap': [],
    'numeroTask': 6,
    'numeroLimit': 10,
    'conta' : {
        '0': 'caatinga01',   # 
        '1': 'caatinga02',
        '2': 'caatinga03',
        '3': 'caatinga04',
        '4': 'caatinga05',        
        '5': 'solkan1201',    
        '6': 'solkanGeodatin',
        '7': 'superconta'   
    },
    'dict_classChangeBa': arqParams.dictClassRepre
}
# print(param.keys())
# print("vai exportar em ", param['assetOut'])

#============================================================
#========================METODOS=============================
#============================================================

def gerenciador(cont):
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    print(numberofChange)
    
    if str(cont) in numberofChange:
        print(f"inicialize in account #{cont} <> {param['conta'][str(cont)]}")
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 
        
        # relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:   
            print(str(lin))         
            # relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

#exporta a FeatCollection Samples classificada para o asset
# salva ftcol para um assetindexIni
def save_ROIs_toAsset(collection, name):

    optExp = {
        'collection': collection,
        'description': name,
        'assetId': param['outAssetROIs'] + "/" + name
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando ROIs da bacia $s ...!", name)



def check_dir(file_name):
    if not os.path.exists(file_name):
        arq = open(file_name, 'w+')
        arq.close()

def getPathCSV (nfolder):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])
    # folder of CSVs ROIs
    roisPath = '/dados/' + nfolder
    mpath = pathparent + roisPath
    print("path of CSVs Rois is \n ==>",  mpath)
    return mpath

def clean_lstBandas(tmplstBNDs):
    lstFails = ['green_median_texture']
    lstbndsRed = []
    for bnd in tmplstBNDs:
        bnd = bnd.replace('_1','')
        bnd = bnd.replace('_2','')
        bnd = bnd.replace('_3','')
        if bnd not in lstbndsRed and 'min' not in bnd and bnd not in lstFails and 'stdDev' not in bnd:
            lstbndsRed.append(bnd)
    return lstbndsRed

dictPmtroArv = {
    '35': [
            '741', '746', '753', '766', '7741', '778', 
            '7616', '7617', '7618', '7619'
    ],
    '50': [
            '7422', '745', '752', '758', '7621', 
            '776', '777',  '7612', '7615'# 
    ],
    '65':  [
            '7421','744','7492','751',
            '754','755','756','757','759','7622','763','764',
            '765','767','771','772','773', '7742','775',
            '76111','76116','7614','7613'
    ]
}

tesauroBasin = arqParams.tesauroBasin
pathJson = getPathCSV("regJSON/")


print("==================================================")
# process_normalized_img
# imagens_mosaic = imagens_mosaico.map(lambda img: process_re_escalar_img(img))          
# ftcol_baciasbuffer = ee.FeatureCollection(param['asset_bacias_buffer'])
# print(imagens_mosaic.first().bandNames().getInfo())
#nome das bacias que fazem parte do bioma7619
# nameBacias = arqParams.listaNameBacias
# print("carregando {} bacias hidrograficas ".format(len(nameBbacias_prioritariasacias)))
# sys.exit()
#lista de anos
# listYears = [k for k in range(param['yearInicial'], param['yearFinal'] + 1)]
# print(f'lista de bandas anos entre {param['yearInicial']} e {param['yearFinal']}')
# param['lsBandasMap'] = ['classification_' + str(kk) for kk in listYears]
# print(param['lsBandasMap'])

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
# bandNames = ['awei_median_dry', 'blue_stdDev', 'brightness_median', 'cvi_median_dry',]
# a_file = open(pathJson + "filt_lst_features_selected_spIndC9.json", "r")
# dictFeatureImp = json.load(a_file)
# print("dict Features ",dictFeatureImp.keys())



## Revisando todos as Bacias que foram feitas 
registros_proc = "registros/lsBaciasClassifyfeitasv_1.txt"
pathFolder = os.getcwd()
path_MGRS = os.path.join(pathFolder, registros_proc)
baciasFeitas = []
check_dir(path_MGRS)

arqFeitos = open(path_MGRS, 'r')
for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

arqFeitos.close()
arqFeitos = open(path_MGRS, 'a+')

# mpath_bndImp = pathFolder + '/dados/regJSON/'
# filesJSON = glob.glob(pathJson + '*.json')
# print("  files json ", filesJSON)
# nameDictGradeBacia = ''
# sys.exit()

# lista de 49 bacias 
nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751', 
    '752', '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622'
]
# nameBacias = [
    # '7422', '7424', '7438', '7443', '745', '746','751','752','753', '7564', '7581',
    # '7617', '7618', '7619', '7622', '7625', '763','765', '766', '7671', '772',
    # '7721', '7741', '7754'
# ]

# '7617', '7564',  '763', '7622'
print(f"we have {len(nameBacias)} bacias")
# "761112",
modelo = "GTB"
knowMapSaved = False
procMosaicEE = True

listBacFalta = []
# lst_bacias_proc = [item for item in nameBacias if item in listBacFalta]
# bacias_prioritarias = [
#   '7411',  '746', '7541', '7544', '7591', '7592', '761111', '761112', 
#   '7612', '7613', '7614', 
#   '7615', '771', '7712', '772', '7721', '773', '7741', '7746', 
#   '7754', '7761', '7764'
# ]
# print(len(lst_bacias_proc))
cont = 7
# cont = gerenciador(cont)

asset_exportar = param['assetOut']
pos_inic = 0
pos_end = 50
# sys.exit()
for cc, _nbacia in enumerate(nameBacias[pos_inic: pos_end]):
    if knowMapSaved:
        try:
            nameMap = 'BACIA_' + _nbacia + '_' + 'GTB_col10-v' + str(param['version'])
            imgtmp = ee.Image(os.path.join(asset_exportar, nameMap))
            print(" 🚨 loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), " bandas 🚨")
        except:
            listBacFalta.append(_nbacia)
    else:        
        print("-------------------.kmkl---------------------------------------------")
        print(f"-------- {cc + pos_inic}/{len(nameBacias)}   classificando bacia nova {_nbacia} and seus properties da antinga {tesauroBasin[_nbacia]}-----------------")   
        print("---------------------------------------------------------------------") 
        process_classification = ClassMosaic_indexs_Spectral()
        process_classification.iterate_bacias(_nbacia,  False) 
        # arqFeitos.write(_nbacia + '\n')
        # cont = gerenciador(cont) 

    # sys.exit()
arqFeitos.close()


if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))