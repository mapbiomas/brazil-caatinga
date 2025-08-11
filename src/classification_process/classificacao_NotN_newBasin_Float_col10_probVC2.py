#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import glob
import json
import csv
import copy
import sys
import math
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
# sys.setrecursionlimit(1000000000)

#============================================================
#============== FUNCTIONS FO SPECTRAL INDEX =================


class ClassMosaic_indexs_Spectral(object):

    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'bioma': "CAATINGA",
        'version': 4,
        'lsBandasMap': [],
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
        'asset_collectionId': 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
        'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        # 'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C',
        # 'asset_joinsGrBaMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_V4C',
        'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C',
        'asset_joinsGrBaMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_DS_v4corrCC',
        'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2',
        'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX',
        # 'asset_output': 'projects/nexgenmap/SAMPLES/Caatinga',
        # Spectral bands selected
        'lsClasse': [4, 3, 12, 15, 18, 21, 22, 33],
        'lsPtos': [300, 500, 300, 350, 150, 100, 150, 300],
        "anoIntInit": 1985,
        "anoIntFin": 2025,
        'dict_classChangeBa': arqParams.dictClassRepre,
        # https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting
        'pmtGTB': {
            'numberOfTrees': 25, 
            'shrinkage': 0.1,         
            'samplingRate': 0.65, 
            'loss': "LeastSquares",#'Huber',#'LeastAbsoluteDeviation', 
            'seed': 0
        },
    }


    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self):

        # self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])
        # band_year = [nband + '_median' for nband in self.options['bnd_L']]
        # band_drys = [bnd + '_dry' for bnd in band_year]    
        # band_wets = [bnd + '_wet' for bnd in band_year]
        # self.band_mosaic = band_year + band_wets + band_drys
        # lstSat = ["l5","l7","l8"]
        # self.imgMosaic = (
        #     ee.ImageCollection(self.options['asset_mosaic'])
        #                     .filter(ee.Filter.inList('biome', self.options['biomas']))
        #                     .filter(ee.Filter.inList('satellite', lstSat))
        #                     .select(self.band_mosaic)
        # )      
        imgMapSaved = ee.ImageCollection(self.options['assetOut'])
        self.lstIDassetS = imgMapSaved.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
        print(f" ====== we have {len(self.lstIDassetS)} maps saved ====")   

        # for kk in range(0, len(self.lstIDassetS) + 1, 5):
        #     print(self.lstIDassetS[kk : kk + 5])

        # print("  ", self.imgMosaic.size().getInfo())
        # print("see band Names the first ")
        # self.imgMosaic = simgMosaic#.map(lambda img: self.process_re_escalar_img(img))                                      
        # print("  ", self.imgMosaic.size().getInfo())
        # print("see band Names the first ")
        # print(" ==== ", ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        self.options['lsBandasMap'] = ['classification_' + str(kk) for kk in self.lst_year]

        # self.tesauroBasin = arqParams.tesauroBasin
        pathHiperpmtros = os.path.join(pathparent, 'dados', 'dictBetterModelpmtCol10v1.json')
        b_file = open(pathHiperpmtros, 'r')
        self.dictHiperPmtTuning = json.load(b_file)
        self.pathFSJson = getPathCSV("FS_col10_json/")
        print("==== path of CSVs of Features Selections ==== \n >>> ", self.pathFSJson)
        self.lstBandMB = self.get_bands_mosaicos()
        print("bandas mapbiomas ", self.lstBandMB)



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
        ratioImgY = (img.expression("float(b('nir_median') / b('red_median'))")
                                .rename(['ratio_median']).toFloat()
        )

        ratioImgwet = (img.expression("float(b('nir_median_wet') / b('red_median_wet'))")
                                .rename(['ratio_median_wet']).toFloat()  
        )

        ratioImgdry = (img.expression("float(b('nir_median_dry') / b('red_median_dry'))")
                                .rename(['ratio_median_dry']).toFloat()        
        )

        rviImgY = (img.expression("float(b('red_median') / b('nir_median'))")
                                .rename(['rvi_median']).toFloat() 
        )

        rviImgWet = (img.expression("float(b('red_median_wet') / b('nir_median_wet'))")
                                .rename(['rvi_median_wet']).toFloat() 
        )

        rviImgDry = (img.expression("float(b('red_median_dry') / b('nir_median_dry'))")
                                .rename(['rvi_median_dry']).toFloat()  
        )

        ndviImgY = (img.expression("float(b('nir_median') - b('red_median')) / (b('nir_median') + b('red_median'))")
                                .rename(['ndvi_median']).toFloat()    
        )

        ndviImgWet = (img.expression("float(b('nir_median_wet') - b('red_median_wet')) / (b('nir_median_wet') + b('red_median_wet'))").rename(['ndvi_median_wet']).toFloat()
        )  

        ndviImgDry = (img.expression("float(b('nir_median_dry') - b('red_median_dry')) / (b('nir_median_dry') + b('red_median_dry'))")
                                .rename(['ndvi_median_dry']).toFloat()                           
        )

        ndbiImgY = (img.expression("float(b('swir1_median') - b('nir_median')) / (b('swir1_median') + b('nir_median'))")
                                .rename(['ndbi_median']).toFloat()   
        ) 

        ndbiImgWet = (img.expression("float(b('swir1_median_wet') - b('nir_median_wet')) / (b('swir1_median_wet') + b('nir_median_wet'))")
                                .rename(['ndbi_median_wet']).toFloat()  
        )

        ndbiImgDry = (img.expression("float(b('swir1_median_dry') - b('nir_median_dry')) / (b('swir1_median_dry') + b('nir_median_dry'))")
                                .rename(['ndbi_median_dry']).toFloat()
        )

        ndmiImgY = (img.expression("float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")
                                .rename(['ndmi_median']).toFloat()    
        )

        ndmiImgWet = (img.expression("float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")
                                .rename(['ndmi_median_wet']).toFloat()  
        )

        ndmiImgDry = (img.expression("float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")
                                .rename(['ndmi_median_dry']).toFloat()
        )

        nbrImgY = (img.expression("float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")
                                .rename(['nbr_median']).toFloat() 
        )   

        nbrImgWet = (img.expression("float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")
                                .rename(['nbr_median_wet']).toFloat()  
        )

        nbrImgDry = (img.expression("float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")
                                .rename(['nbr_median_dry']).toFloat() 
        )

        ndtiImgY = (img.expression("float(b('swir1_median') - b('swir2_median')) / (b('swir1_median') + b('swir2_median'))")
                                .rename(['ndti_median']).toFloat()   
        ) 

        ndtiImgWet = (img.expression("float(b('swir1_median_wet') - b('swir2_median_wet')) / (b('swir1_median_wet') + b('swir2_median_wet'))")
                                .rename(['ndti_median_wet']).toFloat()  
        )

        ndtiImgDry = (img.expression("float(b('swir1_median_dry') - b('swir2_median_dry')) / (b('swir1_median_dry') + b('swir2_median_dry'))")
                                .rename(['ndti_median_dry']).toFloat() 
        )

        ndwiImgY = (img.expression("float(b('nir_median') - b('swir2_median')) / (b('nir_median') + b('swir2_median'))")
                                .rename(['ndwi_median']).toFloat() 
        )      

        ndwiImgWet = (img.expression("float(b('nir_median_wet') - b('swir2_median_wet')) / (b('nir_median_wet') + b('swir2_median_wet'))")
                                .rename(['ndwi_median_wet']).toFloat()   
        )

        ndwiImgDry = (img.expression("float(b('nir_median_dry') - b('swir2_median_dry')) / (b('nir_median_dry') + b('swir2_median_dry'))")
                                .rename(['ndwi_median_dry']).toFloat()   
        )

        aweiY = (img.expression(
                            "float(4 * (b('green_median') - b('swir2_median')) - (0.25 * b('nir_median') + 2.75 * b('swir1_median')))"
                        ).rename("awei_median").toFloat() 
        )

        aweiWet = (img.expression(
                            "float(4 * (b('green_median_wet') - b('swir2_median_wet')) - (0.25 * b('nir_median_wet') + 2.75 * b('swir1_median_wet')))"
                        ).rename("awei_median_wet").toFloat() 
        )

        aweiDry = (img.expression(
                            "float(4 * (b('green_median_dry') - b('swir2_median_dry')) - (0.25 * b('nir_median_dry') + 2.75 * b('swir1_median_dry')))"
                        ).rename("awei_median_dry").toFloat()  
        )

        iiaImgY = (img.expression(
                            "float((b('green_median') - 4 *  b('nir_median')) / (b('green_median') + 4 *  b('nir_median')))"
                        ).rename("iia_median").toFloat()
        )
        
        iiaImgWet = (img.expression(
                            "float((b('green_median_wet') - 4 *  b('nir_median_wet')) / (b('green_median_wet') + 4 *  b('nir_median_wet')))"
                        ).rename("iia_median_wet").toFloat()
        )

        iiaImgDry = (img.expression(
                            "float((b('green_median_dry') - 4 *  b('nir_median_dry')) / (b('green_median_dry') + 4 *  b('nir_median_dry')))"
                        ).rename("iia_median_dry").toFloat()
        )

        eviImgY = (img.expression(
            "float(2.4 * (b('nir_median') - b('red_median')) / (1 + b('nir_median') + b('red_median')))")
                .rename(['evi_median']).toFloat() 
        )

        eviImgWet = (img.expression(
            "float(2.4 * (b('nir_median_wet') - b('red_median_wet')) / (1 + b('nir_median_wet') + b('red_median_wet')))")
                .rename(['evi_median_wet']).toFloat()   
        )

        eviImgDry = (img.expression(
            "float(2.4 * (b('nir_median_dry') - b('red_median_dry')) / (1 + b('nir_median_dry') + b('red_median_dry')))")
                .rename(['evi_median_dry']).toFloat() 
        )

        gvmiImgY = (img.expression(
                        "float ((b('nir_median')  + 0.1) - (b('swir1_median') + 0.02)) / ((b('nir_median') + 0.1) + (b('swir1_median') + 0.02))" 
                    ).rename(['gvmi_median']).toFloat() 
        )  

        gvmiImgWet = (img.expression(
                        "float ((b('nir_median_wet')  + 0.1) - (b('swir1_median_wet') + 0.02)) / ((b('nir_median_wet') + 0.1) + (b('swir1_median_wet') + 0.02))" 
                    ).rename(['gvmi_median_wet']).toFloat()
        )

        gvmiImgDry = (img.expression(
                        "float ((b('nir_median_dry')  + 0.1) - (b('swir1_median_dry') + 0.02)) / ((b('nir_median_dry') + 0.1) + (b('swir1_median_dry') + 0.02))" 
                    ).rename(['gvmi_median_dry']).toFloat() 
        )

        gcviImgAY = (img.expression(
            "float(b('nir_median')) / (b('green_median')) - 1")
                .rename(['gcvi_median']).toFloat()   
        )

        gcviImgAWet = (img.expression(
            "float(b('nir_median_wet')) / (b('green_median_wet')) - 1")
                .rename(['gcvi_median_wet']).toFloat() 
        )
                
        gcviImgADry = (img.expression(
            "float(b('nir_median_dry')) / (b('green_median_dry')) - 1")
                .rename(['gcvi_median_dry']).toFloat() 
        )

        # Global Environment Monitoring Index GEMI
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgAY = (img.expression(
            "float((2 * (b('nir_median') * b('nir_median') - b('red_median') * b('red_median')) + 1.5 * b('nir_median')" +
            " + 0.5 * b('red_median')) / (b('nir_median') + b('green_median') + 0.5) )")
                .rename(['gemi_median']).toFloat()   
        ) 

        gemiImgAWet = (img.expression(
            "float((2 * (b('nir_median_wet') * b('nir_median_wet') - b('red_median_wet') * b('red_median_wet')) + 1.5 * b('nir_median_wet')" +
            " + 0.5 * b('red_median_wet')) / (b('nir_median_wet') + b('green_median_wet') + 0.5) )")
                .rename(['gemi_median_wet']).toFloat() 
        )

        gemiImgADry = (img.expression(
            "float((2 * (b('nir_median_dry') * b('nir_median_dry') - b('red_median_dry') * b('red_median_dry')) + 1.5 * b('nir_median_dry')" +
            " + 0.5 * b('red_median_dry')) / (b('nir_median_dry') + b('green_median_dry') + 0.5) )")
                .rename(['gemi_median_dry']).toFloat() 
        )
         # Chlorophyll vegetation index CVI
        cviImgAY = (img.expression(
            "float(b('nir_median') * (b('green_median') / (b('blue_median') * b('blue_median'))))")
                .rename(['cvi_median']).toFloat()  
        )

        cviImgAWet = (img.expression(
            "float(b('nir_median_wet') * (b('green_median_wet') / (b('blue_median_wet') * b('blue_median_wet'))))")
                .rename(['cvi_median_wet']).toFloat()
        )

        cviImgADry = (img.expression(
            "float(b('nir_median_dry') * (b('green_median_dry') / (b('blue_median_dry') * b('blue_median_dry'))))")
                .rename(['cvi_median_dry']).toFloat()  
        )
        # Green leaf index  GLI
        gliImgY = (img.expression(
            "float((2 * b('green_median') - b('red_median') - b('blue_median')) / (2 * b('green_median') + b('red_median') + b('blue_median')))")
                .rename(['gli_median']).toFloat()
        )    

        gliImgWet = (img.expression(
            "float((2 * b('green_median_wet') - b('red_median_wet') - b('blue_median_wet')) / (2 * b('green_median_wet') + b('red_median_wet') + b('blue_median_wet')))")
                .rename(['gli_median_wet']).toFloat()   
        )

        gliImgDry = (img.expression(
            "float((2 * b('green_median_dry') - b('red_median_dry') - b('blue_median_dry')) / (2 * b('green_median_dry') + b('red_median_dry') + b('blue_median_dry')))")
                .rename(['gli_median_dry']).toFloat() 
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
                .rename(['afvi_median']).toFloat()  
        )

        afviImgAWet = (img.expression(
            "float((b('nir_median_wet') - 0.5 * b('swir2_median_wet')) / (b('nir_median_wet') + 0.5 * b('swir2_median_wet')))")
                .rename(['afvi_median_wet']).toFloat()
        )

        afviImgADry = (img.expression(
            "float((b('nir_median_dry') - 0.5 * b('swir2_median_dry')) / (b('nir_median_dry') + 0.5 * b('swir2_median_dry')))")
                .rename(['afvi_median_dry']).toFloat() 
        )
        # Advanced Vegetation Index
        aviImgAY = (img.expression(
            "float((b('nir_median')* (1.0 - b('red_median')) * (b('nir_median') - b('red_median'))) ** 1/3)")
                .rename(['avi_median']).toFloat()   
        )

        aviImgAWet = (img.expression(
            "float((b('nir_median_wet')* (1.0 - b('red_median_wet')) * (b('nir_median_wet') - b('red_median_wet'))) ** 1/3)")
                .rename(['avi_median_wet']).toFloat()
        )

        aviImgADry = (img.expression(
            "float((b('nir_median_dry')* (1.0 - b('red_median_dry')) * (b('nir_median_dry') - b('red_median_dry'))) ** 1/3)")
                .rename(['avi_median_dry']).toFloat()     
        )
        #  NDDI Normalized Differenece Drought Index
        nddiImg = (ndviImgY.addBands(ndwiImgY).expression(
            "float((b('ndvi_median') - b('ndwi_median')) / (b('ndvi_median') + b('ndwi_median')))"
        ).rename(['nddi_median']).toFloat() )
        
        nddiImgWet = (ndviImgWet.addBands(ndwiImgWet).expression(
            "float((b('ndvi_median_wet') - b('ndwi_median_wet')) / (b('ndvi_median_wet') + b('ndwi_median_wet')))"
        ).rename(['nddi_median_wet']).toFloat() )
        
        nddiImgDry = (ndviImgDry.addBands(ndwiImgDry).expression(
            "float((b('ndvi_median_dry') - b('ndwi_median_dry')) / (b('ndvi_median_dry') + b('ndwi_median_dry')))"
        ).rename(['nddi_median_dry']).toFloat())
        # Bare Soil Index
        bsiImgY = (img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
                .rename(['bsi_median']).toFloat()  
        )

        bsiImgWet = (img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
                .rename(['bsi_median_wet']).toFloat()
        )

        bsiImgDry = (img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
                .rename(['bsi_median_dry']).toFloat()
        )
        # BRBA	Band Ratio for Built-up Area  
        brbaImgY = (img.expression(
            "float(b('red_median') / b('swir1_median'))")
                .rename(['brba_median']).toFloat()   
        )

        brbaImgWet = (img.expression(
            "float(b('red_median_wet') / b('swir1_median_wet'))")
                .rename(['brba_median_wet']).toFloat()
        )

        brbaImgDry = (img.expression(
            "float(b('red_median_dry') / b('swir1_median_dry'))")
                .rename(['brba_median_dry']).toFloat() 
        )
        # DSWI5	Disease-Water Stress Index 5
        dswi5ImgY = (img.expression(
            "float((b('nir_median') + b('green_median')) / (b('swir1_median') + b('red_median')))")
                .rename(['dswi5_median']).toFloat() 
        )

        dswi5ImgWet = (img.expression(
            "float((b('nir_median_wet') + b('green_median_wet')) / (b('swir1_median_wet') + b('red_median_wet')))")
                .rename(['dswi5_median_wet']).toFloat() 
        )

        dswi5ImgDry = (img.expression(
            "float((b('nir_median_dry') + b('green_median_dry')) / (b('swir1_median_dry') + b('red_median_dry')))")
                .rename(['dswi5_median_dry']).toFloat() 
        )
        # LSWI	Land Surface Water Index
        lswiImgY = (img.expression(
            "float((b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median')))")
                .rename(['lswi_median']).toFloat()
        )  

        lswiImgWet = (img.expression(
            "float((b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet')))")
                .rename(['lswi_median_wet']).toFloat()
        )

        lswiImgDry = (img.expression(
            "float((b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry')))")
                .rename(['lswi_median_dry']).toFloat() 
        )
        # MBI	Modified Bare Soil Index
        mbiImgY = (img.expression(
            "float(((b('swir1_median') - b('swir2_median') - b('nir_median')) /" + 
                " (b('swir1_median') + b('swir2_median') + b('nir_median'))) + 0.5)")
                    .rename(['mbi_median']).toFloat() 
        )

        mbiImgWet = (img.expression(
            "float(((b('swir1_median_wet') - b('swir2_median_wet') - b('nir_median_wet')) /" + 
                " (b('swir1_median_wet') + b('swir2_median_wet') + b('nir_median_wet'))) + 0.5)")
                    .rename(['mbi_median_wet']).toFloat() 
        )

        mbiImgDry = (img.expression(
            "float(((b('swir1_median_dry') - b('swir2_median_dry') - b('nir_median_dry')) /" + 
                " (b('swir1_median_dry') + b('swir2_median_dry') + b('nir_median_dry'))) + 0.5)")
                    .rename(['mbi_median_dry']).toFloat() 
        )
        # UI	Urban Index	urban
        uiImgY = (img.expression(
            "float((b('swir2_median') - b('nir_median')) / (b('swir2_median') + b('nir_median')))")
                .rename(['ui_median']).toFloat()  
        )

        uiImgWet = (img.expression(
            "float((b('swir2_median_wet') - b('nir_median_wet')) / (b('swir2_median_wet') + b('nir_median_wet')))")
                .rename(['ui_median_wet']).toFloat() 
        )

        uiImgDry = (img.expression(
            "float((b('swir2_median_dry') - b('nir_median_dry')) / (b('swir2_median_dry') + b('nir_median_dry')))")
                .rename(['ui_median_dry']).toFloat() 
        )
        # OSAVI	Optimized Soil-Adjusted Vegetation Index
        osaviImgY = (img.expression(
            "float(b('nir_median') - b('red_median')) / (0.16 + b('nir_median') + b('red_median'))")
                .rename(['osavi_median']).toFloat() 
        )

        osaviImgWet = (img.expression(
            "float(b('nir_median_wet') - b('red_median_wet')) / (0.16 + b('nir_median_wet') + b('red_median_wet'))")
                .rename(['osavi_median_wet']).toFloat() 
        )

        osaviImgDry = (img.expression(
            "float(b('nir_median_dry') - b('red_median_dry')) / (0.16 + b('nir_median_dry') + b('red_median_dry'))")
                .rename(['osavi_median_dry']).toFloat()  
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
                .rename(['ri_median']).toFloat()   
        )

        riImgWet = (img.expression(
            "float(b('nir_median_wet') - b('green_median_wet')) / (b('nir_median_wet') + b('green_median_wet'))")
                .rename(['ri_median_wet']).toFloat()
        )

        riImgDry = (img.expression(
            "float(b('nir_median_dry') - b('green_median_dry')) / (b('nir_median_dry') + b('green_median_dry'))")
                .rename(['ri_median_dry']).toFloat() 
        )
        # Tasselled Cap - brightness 
        tasselledCapbImgY = (img.expression(
            "float(0.3037 * b('blue_median') + 0.2793 * b('green_median') + 0.4743 * b('red_median')  " + 
                "+ 0.5585 * b('nir_median') + 0.5082 * b('swir1_median') +  0.1863 * b('swir2_median'))")
                    .rename(['brightness_median']).toFloat()
        )

        tasselledCapbImgWet = (img.expression(
            "float(0.3037 * b('blue_median_wet') + 0.2793 * b('green_median_wet') + 0.4743 * b('red_median_wet')  " + 
                "+ 0.5585 * b('nir_median_wet') + 0.5082 * b('swir1_median_wet') +  0.1863 * b('swir2_median_wet'))")
                    .rename(['brightness_median_wet']).toFloat()
        )

        tasselledCapbImgDry = (img.expression(
            "float(0.3037 * b('blue_median_dry') + 0.2793 * b('green_median_dry') + 0.4743 * b('red_median_dry')  " + 
                "+ 0.5585 * b('nir_median_dry') + 0.5082 * b('swir1_median_dry') +  0.1863 * b('swir2_median_dry'))")
                    .rename(['brightness_median_dry']).toFloat()
        ) 

        # Tasselled Cap - wetness 
        tasselledCapwImgY = (img.expression(
            "float(0.1509 * b('blue_median') + 0.1973 * b('green_median') + 0.3279 * b('red_median')  " + 
                "+ 0.3406 * b('nir_median') + 0.7112 * b('swir1_median') +  0.4572 * b('swir2_median'))")
                    .rename(['wetness_median']).toFloat() 
        )
        
        tasselledCapwImgWet = (img.expression(
            "float(0.1509 * b('blue_median_wet') + 0.1973 * b('green_median_wet') + 0.3279 * b('red_median_wet')  " + 
                "+ 0.3406 * b('nir_median_wet') + 0.7112 * b('swir1_median_wet') +  0.4572 * b('swir2_median_wet'))")
                    .rename(['wetness_median_wet']).toFloat() 
        )
        
        tasselledCapwImgDry = (img.expression(
            "float(0.1509 * b('blue_median_dry') + 0.1973 * b('green_median_dry') + 0.3279 * b('red_median_dry')  " + 
                "+ 0.3406 * b('nir_median_dry') + 0.7112 * b('swir1_median_dry') +  0.4572 * b('swir2_median_dry'))")
                    .rename(['wetness_median_dry']).toFloat() 
        )
        # Moisture Stress Index (MSI)
        msiImgY = (img.expression(
            "float( b('nir_median') / b('swir1_median'))")
                .rename(['msi_median']).toFloat() 
        )
        
        msiImgWet = (img.expression(
            "float( b('nir_median_wet') / b('swir1_median_wet'))")
                .rename(['msi_median_wet']).toFloat() 
        )

        msiImgDry = (img.expression(
            "float( b('nir_median_dry') / b('swir1_median_dry'))")
                .rename(['msi_median_dry']).toFloat()
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
        co2FluxImg = ndviImgY.multiply(spriImgY).rename(['co2flux_median'])   
        co2FluxImgWet = ndviImgWet.multiply(spriImgWet).rename(['co2flux_median_wet']) 
        co2FluxImgDry = ndviImgDry.multiply(spriImgDry).rename(['co2flux_median_dry']) 

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
                .addBands(nbrImgY).addBands(nbrImgWet).addBands(nbrImgDry)
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
                .addBands(msaviImgY).addBands(msaviImgWet).addBands(msaviImgDry)
                .addBands(gsaviImgY).addBands(gsaviImgWet).addBands(gsaviImgDry)
                .addBands(riImgY).addBands(riImgWet).addBands(riImgDry)
                .addBands(tasselledCapbImgY).addBands(tasselledCapbImgWet).addBands(tasselledCapbImgDry)
                .addBands(tasselledCapwImgY).addBands(tasselledCapwImgWet).addBands(tasselledCapwImgDry)
                .addBands(msiImgY).addBands(msiImgWet).addBands(msiImgDry)
                .addBands(spriImgY).addBands(spriImgWet).addBands(spriImgDry)
                .addBands(co2FluxImg).addBands(co2FluxImgWet).addBands(co2FluxImgDry)
                .addBands(contrastnir).addBands(contrastred).addBands(contrastnirDry).addBands(contrastredDry) 
        )

    def calculateBandsIndexEVI(self, img):
        
        eviImgY = img.expression(
            "float(2.4 * (b('nir') - b('red')) / (1 + b('nir') + b('red')))")\
                .rename(['evi']).toFloat() 

        return img.addBands(eviImgY)

    def agregateBandsIndexLAI(self, img):
        laiImgY = img.expression(
            "float(3.618 * (b('evi_median') - 0.118))")\
                .rename(['lai_median']).toFloat()
    
        return img.addBands(laiImgY)    

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

    def CalculateIndice(self, imagem):
        # band_feat = [
        #         "ratio","rvi","ndwi","awei","iia","evi",
        #         "gcvi","gemi","cvi","gli","shape","afvi",
        #         "avi","bsi","brba","dswi5","lswi","mbi","ui",
        #         "osavi","ri","brightness","wetness","gvmi",
        #         "nir_contrast","red_contrast", 'nddi',"ndvi",
        #         "ndmi","msavi", "gsavi","ndbi","nbr","ndti", 
        #         'co2flux'
        #     ]        
        imageW = self.agregateBandswithSpectralIndex(imagem)
        imageW = self.agregate_Bands_SMA_NDFIa(imageW)
        imageW = self.addSlopeAndHilshade(imageW)

        return imageW  

    def make_mosaicofromReducer(self, colMosaic):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        # self.bandMosaic = band_year + band_wets + band_drys
        # print("bandas principais \n ==> ", self.bandMosaic)
        # bandsDry =None
        percentilelowDry = 5
        percentileDry = 35
        percentileWet = 65

        # get dry season collection
        evilowDry = (
            colMosaic.select(['evi'])
                    .reduce(ee.Reducer.percentile([percentilelowDry]))
        )
        eviDry = (
            colMosaic.select(['evi'])
                    .reduce(ee.Reducer.percentile([percentileDry]))
        )        

        collectionDry = (
            colMosaic.map(lambda img: img.mask(img.select(['evi']).gte(evilowDry))
                                        .mask(img.select(['evi']).lte(eviDry)))
        )

        # get wet season collection
        eviWet = (
            colMosaic.select(['evi'])        
                    .reduce(ee.Reducer.percentile([percentileWet]))
        )
        collectionWet = (
            colMosaic.map(lambda img: img.mask(img.select(['evi']).gte(eviWet)))                                        
        )

        # Reduce collection to median mosaic
        mosaic = (
            colMosaic.select(self.options['bnd_L'])
                .reduce(ee.Reducer.median()).rename(band_year)
        )

        # get dry median mosaic
        mosaicDry = (
            collectionDry.select(self.options['bnd_L'])
                .reduce(ee.Reducer.median()).rename(band_drys)
        )

        # get wet median mosaic
        mosaicWet = (
            collectionWet.select(self.options['bnd_L'])
                .reduce(ee.Reducer.median()).rename(band_wets)
        )

        # get stdDev mosaic
        mosaicStdDev = (
            colMosaic.select(self.options['bnd_L'])
                        .reduce(ee.Reducer.stdDev())
        )

        mosaic = (mosaic.addBands(mosaicDry)
                        .addBands(mosaicWet)
                        .addBands(mosaicStdDev)
        )

        return mosaic
    
    def make_mosaicofromIntervalo(self, colMosaic, year_courrent, semetral=False):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]            
        band_wets = [bnd + '_wet' for bnd in band_year]
        band_drys = [bnd + '_dry' for bnd in band_year]
        dictPer = {
            'year': {
                'start': str(str(year_courrent)) + '-01-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'year',
                'bnds': band_year
            },
            'dry': {
                'start': str(year_courrent) + '-08-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'dry',
                'bnds': band_drys
            },
            'wet': {
                'start': str(year_courrent) + '-01-01',
                'end': str(year_courrent) + '-07-31',
                'surf': 'wet',
                'bnds': band_wets
            }
        }       
        mosaico = None
        if semetral:
            lstPeriodo = ['year', 'wet']
        else:
            lstPeriodo = ['year', 'dry', 'wet']
        for periodo in lstPeriodo:
            dateStart =  dictPer[periodo]['start']
            dateEnd = dictPer[periodo]['end']
            bands_period = dictPer[periodo]['bnds']
            # get dry median mosaic
            mosaictmp = (
                colMosaic.select(self.options['bnd_L'])
                    .filter(ee.Filter.date(dateStart, dateEnd))
                    .max()
                    .rename(bands_period)
            )
            if periodo == 'year':
                mosaico = copy.deepcopy(mosaictmp)
            else:
                mosaico = mosaico.addBands(mosaictmp)

        if semetral:
            bands_period = dictPer[ 'dry']['bnds']
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(bands_period)
            mosaico = mosaico.addBands(imgUnos)

        return mosaico

    def make_mosaicofromIntervalo_y25(self, colMosaic, year_courrent, semetral=False):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]            
        band_wets = [bnd + '_wet' for bnd in band_year]
        band_drys = [bnd + '_dry' for bnd in band_year]
        dictPer = {
            'year': {
                'start': str(str(year_courrent)) + '-01-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'year',
                'bnds': band_year
            },
            'dry': {
                'start': str(year_courrent) + '-08-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'dry',
                'bnds': band_drys
            },
            'wet': {
                'start': str(year_courrent) + '-01-01',
                'end': str(year_courrent) + '-07-31',
                'surf': 'wet',
                'bnds': band_wets
            }
        }        
        periodo = 'wet'
        dateStart =  dictPer[periodo]['start']
        dateEnd = dictPer[periodo]['end']
        bands_period = dictPer[periodo]['bnds']
        # print("--> ", bands_period )
        # get dry median mosaic
        mosaico = (
            colMosaic.select(self.options['bnd_L'])
                .filter(ee.Filter.date(dateStart, dateEnd))
                .max()
                .rename(bands_period)
        )
        print(mosaico.bandNames().getInfo())
        # mosaico = mosaictmp

        if semetral:
            bands_period = dictPer['dry']['bnds']
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(bands_period)
            mosaico = mosaico.addBands(imgUnos)
            bands_period = dictPer['year']['bnds']
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(bands_period)
            mosaico = mosaico.addBands(imgUnos)

        return mosaico

    def get_bands_mosaicos (self):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        # retornando as 3 listas em 1 só
        return band_year + band_wets + band_drys

    def down_samples_ROIs(self, rois_train):
        # dictROIs = ee.FeatureCollection(rois_train).aggregate_histogram('class').getInfo()
        # print(dictROIs)
        # dictQtLimit = {
        #     '3': 800,
        #     '4': 2000,
        #     '12': 600,
        #     '15': 950,
        #     '18': 800,
        #     '21': 900,
        #     '22': 800,
        #     '29': 400,
        #     '33': 200
        # }
        dictQtLimit = {
            '3': 600,
            '4': 1800,
            '12': 300,
            '15': 1050,
            '18': 100,
            '21': 750,
            '22': 400,
            '29': 200,
            '33': 100
        }
        lstFeats = ee.FeatureCollection([])
        def make_random_select(featCC, limiar):
            #float(dictQtLimit[cclass]/sizeFC) limiar
            featCC = featCC.randomColumn()
            featCC = featCC.filter(ee.Filter.lt('random', ee.Number(limiar).toFloat()))  
            return featCC
        for cclass in [3, 4, 12, 22, 33]:  # dictROIs.keys()
            # print(" filtering class >> ", cclass)
            feattmp = rois_train.filter(ee.Filter.eq('class', int(cclass)))
            sizeFC = feattmp.size()#.getInfo()
            # print("cclass " , cclass, " ", sizeFC.getInfo())
            feattmp = ee.Algorithms.If(
                        ee.Algorithms.IsEqual(ee.Number(sizeFC).gt(ee.Number(dictQtLimit[str(cclass)])),1), 
                        make_random_select(feattmp, ee.Number(dictQtLimit[str(cclass)]).divide(ee.Number(sizeFC))), 
                        feattmp)
            lstFeats = lstFeats.merge(feattmp)
        return ee.FeatureCollection(lstFeats)
    
    def get_ROIs_from_neighbor(self, lst_bacias, asset_root, yyear):

        featGeral = ee.FeatureCollection([])
        for jbasin in lst_bacias:
            nameFeatROIs =  f"{jbasin}_{yyear}_cd"  
            dir_asset_rois = os.path.join(asset_root, nameFeatROIs)
            feat_tmp = ee.FeatureCollection(dir_asset_rois)
            feat_tmp = feat_tmp.map(lambda f: f.set('class', ee.Number.parse(f.get('class')).toFloat().toInt8()))
            featGeral = featGeral.merge(feat_tmp)
        return featGeral

    def iterate_bacias(self, _nbacia, myModel, makeProb, process_mosaic_EE):        

        # loading geometry bacim
        baciabuffer = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                            ee.Filter.eq('nunivotto4', _nbacia))
        print(f"know about the geometry 'nunivotto4' >>  {_nbacia} loaded < {baciabuffer.size().getInfo()} > geometry" )   
        baciabuffer = baciabuffer.map(lambda f: f.set('id_codigo', 1))
        bacia_raster =  baciabuffer.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        baciabuffer = baciabuffer.geometry()
        # sys.exit()
        
        # https://code.earthengine.google.com/48effe10e1fffbedf2076a53b472be0e?asset=projects%2Fgeo-data-s%2Fassets%2Ffotovoltaica%2Fversion_4%2Freg_00000000000000000017_2015_10_pred_g2c
        lstSat = ["l5","l7","l8"]
        imagens_mosaicoEE = (
            ee.ImageCollection(self.options['asset_collectionId'])
                    .select(self.options['bnd_L'])
        )
        imagens_mosaico = (ee.ImageCollection(self.options['asset_mosaic'])
                                .filter(ee.Filter.inList('biome', self.options['biomas']))
                                .filter(ee.Filter.inList('satellite', lstSat))
                                .select(self.lstBandMB)
                    )

        # # lista de classe por bacia 
        # lstClassesUn = self.options['dict_classChangeBa'][self.tesauroBasin[_nbacia]]
        # print(f" ==== lista de classes ness bacia na bacia < {_nbacia} >  ====")
        # print(f" ==== {lstClassesUn} ======" )
        print("---------------------------------------------------------------")
        pmtroClass = copy.deepcopy(self.options['pmtGTB'])

        path_ptrosFS = os.path.join(self.pathFSJson, f"feat_sel_{_nbacia}.json")
        print("load features json ", path_ptrosFS)
        # Open the JSON file for reading
        with open(path_ptrosFS, 'r') as file:
            # Load the JSON data
            bandas_fromFS = json.load(file)

        print(f"lista de Bacias Anos no dict de FS  {len(bandas_fromFS.keys())} years  " )
        print(' as primeiras 3 \n ==> ', list(bandas_fromFS.keys())[:3])
        # tesauroBasin = arqParams.tesauroBasin
        lsNamesBaciasViz = arqParams.basinVizinhasNew[_nbacia]
        lstSoViz =  [kk for kk in lsNamesBaciasViz if kk != _nbacia]
        print("lista de Bacias vizinhas", lstSoViz)

        # sys.exit()
        # imglsClasxanos = ee.Image().byte()

        for nyear in self.lst_year[-1:]:
            bandActiva = 'classification_' + str(nyear)       
            print( "banda activa: " + bandActiva)   

            nomec = f"{_nbacia}_{nyear}_GTB_col10-v_{self.options['version']}"
            if 'BACIA_' + nomec not in self.lstIDassetS:                

                #cria o classificador com as especificacoes definidas acima 
                limitlsb = 35
                # print( bandas_fromFS[f"{_nbacia}_{nyear}"])            
                # lstbandas_import = bandas_fromFS[f"{_nbacia}_{nyear}"]['features']
                if nyear < 2025:
                    lstbandas_import = bandas_fromFS[f"{_nbacia}_{nyear}"]['features']
                else:
                    lstbandas_import = bandas_fromFS[f"{_nbacia}_{2024}"]['features']
                # obandas_imports = [bnd for bnd in lstbandas_import if  not in bnd]
                # obandas_imports = obandas_imports[:limitlsb]
                outrasBandas = ['stdDev', 'solpe']
                bandas_imports = []
                for bnd_index in lstbandas_import:
                    adding = True                   
                    for nbnd in  outrasBandas:
                        if nbnd in bnd_index:
                            adding = False
                    if '_1' in bnd_index or '_2' in bnd_index:
                        adding = False
                    if '_dry' in bnd_index:
                        adding = False
                    #     band_cruz = bnd_index.replace('_dry', '_wet')
                    #     if band_cruz not in bandas_imports:
                    #         adding = True                    
                    if adding:
                        if '_wet' not in bnd_index:
                            if bnd_index + '_wet' not in bandas_imports:
                                bandas_imports.append(bnd_index + '_wet')
                        else:
                            bandas_imports.append(bnd_index)
                bandas_imports = bandas_imports[:limitlsb]
                print(f" numero de bandas selecionadas {len(bandas_imports)} ") 
                # print(bandas_imports)
                
                # sys.exit()
                # nameFeatROIs = 'rois_grade_' + _nbacia
                if nyear < 2025:
                    nameFeatROIs =  f"{_nbacia}_{nyear}_cd"  
                else:
                    nameFeatROIs =  f"{_nbacia}_{2024}_cd"
                dicAttention = {
                    '7622': {0: [1985], 1: 1986},
                    '751': {0: [1994,1995,1996], 1: 1997},
                    '746_1': {0: [1985,1986,1987], 1: 1988},
                    '746_2': {0: [1991,1992,1993,1995,1996], 1: 1994},
                    '746_3': {0: [2002,2003], 1: 2004},
                    '7443': {0: [1986,1987], 1: 1988},
                    '7422': {0: [2006,2007], 1: 2008},
                }
                lstKeys = list(dicAttention.keys()) 
                if int(nyear) > 2020:
                    nameFeatROIs = f"{_nbacia}_{2020}_cd"                
                elif _nbacia in lstKeys:
                    if nyear in dicAttention[_nbacia][0]:
                        nameFeatROIs =  f"{_nbacia}_{dicAttention[_nbacia][1]}_cd"
                elif _nbacia == '746':
                    if nyear in  dicAttention['746_1'][0]:
                        nameFeatROIs =  f"{_nbacia}_{dicAttention['746_1'][1]}_cd"
                    elif nyear in  dicAttention['746_2'][0]:
                        nameFeatROIs =  f"{_nbacia}_{dicAttention['746_2'][1]}_cd"                
                    elif nyear in  dicAttention['746_3'][0]:
                        nameFeatROIs =  f"{_nbacia}_{dicAttention['746_3'][1]}_cd"

                print("loading Rois with name =>>>>>> ", nameFeatROIs)

                asset_rois = self.options['asset_joinsGrBa']
                if not process_mosaic_EE:
                    asset_rois = self.options['asset_joinsGrBaMB']
                
                try:
                    dir_asset_rois = os.path.join(asset_rois, nameFeatROIs)
                    print(f"load samples from idAsset >> {dir_asset_rois}")
                    ROIs_toTrain = ee.FeatureCollection(dir_asset_rois) 
                    # print(ROIs_toTrain.size().getInfo())
                    # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
                    bandExtra = [nband + '_median_wet' for nband in self.options['bnd_L']]  
                    ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.neq('class', 21.0))
                    ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.notNull(bandExtra))                
                    ROIs_toTrain = ROIs_toTrain.map(lambda f: f.set('class', ee.Number.parse(f.get('class')).toFloat().toInt8()))
                    # ROIs_toTrain = ROIs_toTrain.select(bandas_imports)
                    print(ROIs_toTrain.size().getInfo())
                    # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
                    # otherROIsneighbor = self.get_ROIs_from_neighbor(lstSoViz, asset_rois, nyear)
                    ROIs_toTrain =  self.down_samples_ROIs(ROIs_toTrain)  #.merge(otherROIsneighbor)
                    print(" saindo do processo downsamples ")                    
                    # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
                    # lstBandasROIS = ROIs_toTrain.first().propertyNames().getInfo()
                    # print(lstBandasROIS)
                    # print(len(bandas_imports))
                    # tmpBandasImp = [col for col in bandas_imports if col in lstBandasROIS]
                    # print(" >> ", len(bandas_imports))
                    print(" fez down samples nos ROIs  ")
                    # sys.exit()
                    # cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia 
                    date_inic = ee.Date.fromYMD(int(nyear),1,1)      
                    date_end = ee.Date.fromYMD(int(nyear),12,31)   
                    if nyear < 2025: 
                        if process_mosaic_EE:
                            # de mosaico EE y para mosaico Mapbiomas (X)
                            lstCoef = [0.8425, 0.8957, 0.9097, 0.3188, 0.969, 0.9578]
                            bandsCoef = ee.Image.constant(lstCoef + lstCoef + lstCoef)
                            lstIntercept = [106.7546, 115.1553, 239.0688, 1496.4408, 392.3453, 366.57]
                            bandsIntercept = ee.Image.constant(lstIntercept + lstIntercept + lstIntercept)

                            colmosaicMapbiomas = (imagens_mosaico.filter(ee.Filter.eq('year', nyear))
                                            .median().updateMask(bacia_raster))
                            imagens_mosaicoEEv = colmosaicMapbiomas.multiply(bandsCoef).add(bandsIntercept) 
                            imagens_mosaicoEEv = imagens_mosaicoEEv.divide(10000)#.rename(param.bnd_L)
                            # print(f" we have {imagens_mosaicoEEv.bandNames().getInfo()} images ")
                        
                            #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia    
                            mosaicColGoogle = imagens_mosaicoEE.filter(ee.Filter.date(date_inic, date_end))        
                            mosaicoBuilded = self.make_mosaicofromIntervalo(mosaicColGoogle, nyear) 
                            mosaicoBuilded = mosaicoBuilded.updateMask(bacia_raster)
                            print(f" we have {mosaicoBuilded.bandNames().getInfo()} images do mosaico mensal do google ")
                            maskGaps = mosaicoBuilded.unmask(-9999).eq(-9999).updateMask(bacia_raster)
                            ## preenchendo o gap do mosaico do EE pelo mosaico dao mapbiomas
                            mosaicoBuilded = mosaicoBuilded.unmask(-9999).where(maskGaps, imagens_mosaicoEEv)
                            maskGaps = mosaicoBuilded.neq(-9999)
                            mosaicoBuilded = mosaicoBuilded.updateMask(maskGaps).updateMask(bacia_raster)
                            # print(f" we have {mosaicoBuilded.bandNames().getInfo()} images ")
                        else:                
                            ######  de mosaico Mapbiomas para mosaico EE (X)    #####
                            lstCoef = [6499.0873, 8320.9741, 7243.8252, 5944.0973, 7494.4502, 7075.1618]
                            bandsCoef = ee.Image.constant(lstCoef + lstCoef + lstCoef)
                            lstIntercept = [64.0821, 55.127, 36.7782, 1417.7931, 325.8045, 141.9352]
                            bandsIntercept = ee.Image.constant(lstIntercept + lstIntercept + lstIntercept)             

                            #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia    
                            mosaicColGoogle = imagens_mosaicoEE.filter(ee.Filter.date(date_inic, date_end))        
                            mosaicoGoogle = self.make_mosaicofromIntervalo(mosaicColGoogle, nyear) 
                            mosaicoGoogle = mosaicoGoogle.updateMask(bacia_raster)
                            imagens_mosaicoEEv = mosaicoGoogle.multiply(bandsCoef).add(bandsIntercept)
                            
                            colmosaicMapbiomas = (imagens_mosaico.filter(ee.Filter.eq('year', nyear))
                                                        .median().updateMask(bacia_raster))
                            maskGaps = mosaicoBuilded.unmask(-9999).eq(-9999).updateMask(bacia_raster)
                            # ## preenchendo o gap do mosaico do EE pelo mosaico dao mapbiomas
                            # ## preenchendo o gap do mosaico do EE pelo mosaico dao mapbiomas
                            mosaicoBuilded = mosaicoBuilded.unmask(-9999).where(maskGaps, imagens_mosaicoEEv)
                            maskGaps = mosaicoBuilded.neq(-9999)
                            mosaicoBuilded = mosaicoBuilded.updateMask(maskGaps).updateMask(bacia_raster)
                            # print(f" we have {mosaicoBuilded.bandNames().getInfo()} images ")
                    else:
                        mosaicColGoogle = imagens_mosaicoEE.filter(ee.Filter.date(date_inic, date_end))        
                        # print(mosaicColGoogle.size().getInfo())
                        mosaicoBuilded = self.make_mosaicofromIntervalo_y25(mosaicColGoogle, nyear,  True) 
                        # print(f" we have {mosaicoBuilded.bandNames().getInfo()} images ")
                    # print("----- calculado todos os 102 indices ---------------------")
                    mosaicProcess = self.CalculateIndice(mosaicoBuilded.updateMask(bacia_raster))
                    # print(f" we have {mosaicProcess.bandNames().getInfo()} images ")
                    print("calculou todas as bandas necesarias ")
                    # sys.exit()
                    gradeExpMemo = [
                        '7625', '7616', '7613', '7618', '7617', '761112', '7741', 
                        '7615', '7721', '7619', '7443', '763', '746'
                    ]
                    if _nbacia in gradeExpMemo:
                        pmtroClass['numberOfTrees'] = 18
                        pmtroClass['shrinkage'] = 0.1    # 
                    else:            
                        pmtroClass['shrinkage'] = self.dictHiperPmtTuning[_nbacia]['learning_rate']
                        lstBacias_prob = [ '7541', '7544', '7592', '7612', '7615',  '7712', '7721', '7741', '7746']
                        if _nbacia in lstBacias_prob:
                            numberTrees = 18
                            if self.dictHiperPmtTuning[_nbacia]["n_estimators"] < numberTrees:
                                pmtroClass['numberOfTrees'] = self.dictHiperPmtTuning[_nbacia]["n_estimators"] - 3
                            else:
                                pmtroClass['numberOfTrees'] = numberTrees       

                    print("pmtros Classifier ==> ", pmtroClass)
                    
                    # ee.Classifier.smileGradientTreeBoost(numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed)
                    # print("antes de classificar ", ROIs_toTrain.first().propertyNames().getInfo())
                    lstNN = []
                    for col in bandas_imports:
                        if col not in bandas_imports:
                            lstNN.append(col)
                    classifierGTB = ee.Classifier.smileGradientTreeBoost(**pmtroClass).train(
                                                        ROIs_toTrain, 'class', lstNN)              
                    classifiedGTB = mosaicProcess.classify(classifierGTB, bandActiva)        
                    # print("classificando!!!! ")
                    # sys.exit()
                    # se for o primeiro ano cria o dicionario e seta a variavel como
                    # o resultado da primeira imagem classificada
                    print("addicionando classification bands = " , bandActiva)            
                    # if self.options['anoIntInit'] == nyear:
                        # print ('entrou em 1985, no modelo ', myModel)            
                        # print("===> ", myModel)    
                        # imglsClasxanos = copy.deepcopy(classifiedGTB)                                        
                    # nomec = f"{_nbacia}_{nyear}_GTB_col10-v_{self.options['version']}"            
                    mydict = {
                        'id_bacia': _nbacia,
                        'version': self.options['version'],
                        'biome': self.options['bioma'],
                        'classifier': 'GTB',
                        'collection': '10.0',
                        'sensor': 'Landsat',
                        'source': 'geodatin',  
                        'year': nyear              
                    }
                        # imglsClasxanos = imglsClasxanos.set(mydict)
                    classifiedGTB = classifiedGTB.set(mydict)
                        ##### se nao, adiciona a imagem como uma banda a imagem que ja existia
                    # else:
                    #     # print("Adicionando o mapa do ano  ", nyear)
                    #     # print(" ", classifiedGTB.bandNames().getInfo())     
                    #     imglsClasxanos = imglsClasxanos.addBands(classifiedGTB)  


                    # imglsClasxanos = imglsClasxanos.select(self.options['lsBandasMap'])    
                    # imglsClasxanos = imglsClasxanos.set("system:footprint", baciabuffer.coordinates())
                    classifiedGTB = classifiedGTB.set("system:footprint", baciabuffer.coordinates())
                    # exporta bacia   .coordinates()
                    self.processoExportar(classifiedGTB, baciabuffer, nomec, process_mosaic_EE)
                     
                except:
                    print("-----------FALTANDO AS AMOSTRAS ----------------")
                sys.exit()
        else:
            print(f' bacia >>> {nomec}  <<<  foi FEITA ')            

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF, regionB, nameB, proc_mosaicEE):
        nomeDesc = 'BACIA_'+ str(nameB)
        idasset =  os.path.join(self.options['assetOut'] , nomeDesc)
        if not proc_mosaicEE:
            idasset = os.path.join(self.options['assetOutMB'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':ee.Geometry(regionB), #['coordinates'] .getInfo()
            'scale': 30, 
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
    'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX',
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

# listBacFalta = []
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
if procMosaicEE:
    asset_exportar = param['assetOut']
else:
    asset_exportar = param['assetOutMB']

# sys.exit()
for _nbacia in nameBacias[:]:
    if knowMapSaved:
        try:
            nameMap = 'BACIA_' + _nbacia + '_' + 'GTB_col10-v' + str(param['version'])
            imgtmp = ee.Image(os.path.join(asset_exportar, nameMap))
            print(" 🚨 loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), " bandas 🚨")
        except:
            listBacFalta.append(_nbacia)
    else:        
        print("-------------------.kmkl---------------------------------------------")
        print(f"--------    classificando bacia nova {_nbacia} and seus properties da antinga {tesauroBasin[_nbacia]}-----------------")   
        print("---------------------------------------------------------------------") 
        process_classification = ClassMosaic_indexs_Spectral()
        process_classification.iterate_bacias(_nbacia, modelo, False, procMosaicEE) 
        arqFeitos.write(_nbacia + '\n')
        # cont = gerenciador(cont) 

    # sys.exit()
arqFeitos.close()


if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))