#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import os
import copy
import sys
import pandas as pd
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
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


class ClassMosaic_indexs_Spectral(object):

    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 18, 18, 18, 18, 18, 18, 18,  4, 12, 18],
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        # 'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
        'assetMapbiomas100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
        'asset_coincidentes_samples': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/aggrements',
        'asset_collectionId': 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
        'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_ROIs_reference':  'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C', 
        'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_V4C',
        'lsClasse': [4, 3, 12, 15, 18, 21, 22, 33],
        'lsPtos': [300, 500, 300, 350, 150, 100, 150, 300],
        "anoIntInit": 1985,
        "anoIntFin": 2024,
    }

    featureBands = [
        'blue_median', 'blue_median_wet', 'blue_median_dry', 'blue_stdDev', 
        'green_median', 'green_median_dry', 'green_median_wet', 
        'green_median_texture', 'green_min', 'green_stdDev', 
        'red_median', 'red_median_dry', 'red_min', 'red_median_wet', 
        'red_stdDev', 'nir_median', 'nir_median_dry', 'nir_median_wet', 
        'nir_stdDev', 'red_edge_1_median', 'red_edge_1_median_dry', 
        'red_edge_1_median_wet', 'red_edge_1_stdDev', 'red_edge_2_median', 
        'red_edge_2_median_dry', 'red_edge_2_median_wet', 'red_edge_2_stdDev', 
        'red_edge_3_median', 'red_edge_3_median_dry', 'red_edge_3_median_wet', 
        'red_edge_3_stdDev', 'red_edge_4_median', 'red_edge_4_median_dry', 
        'red_edge_4_median_wet', 'red_edge_4_stdDev', 'swir1_median', 
        'swir1_median_dry', 'swir1_median_wet', 'swir1_stdDev', 'swir2_median', 
        'swir2_median_wet', 'swir2_median_dry', 'swir2_stdDev'
    ]
    features_extras = [
        'blue_stdDev','green_median_texture', 'green_min', 'green_stdDev',
        'red_min', 'red_stdDev','red_edge_1_median', 'red_edge_1_median_dry', 
        'red_edge_1_median_wet', 'red_edge_1_stdDev', 'red_edge_2_median', 
        'red_edge_2_median_dry', 'red_edge_2_median_wet', 'red_edge_2_stdDev', 
        'red_edge_3_median', 'red_edge_3_median_dry', 'red_edge_3_median_wet', 
        'red_edge_3_stdDev', 'red_edge_4_median', 'red_edge_4_median_dry', 
        'red_edge_4_median_wet', 'red_edge_4_stdDev','swir1_stdDev',  'swir2_stdDev'
    ]

    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self):
        self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        self.band_mosaic = band_year + band_wets + band_drys
        lstSat = ["l5","l7","l8"]
        self.imgMosaic = (
            ee.ImageCollection(self.options['asset_mosaic'])
                            .filter(ee.Filter.inList('biome', self.options['biomas']))
                            .filter(ee.Filter.inList('satellite', lstSat))
                            .select(self.band_mosaic)
        )                                              
        print("  ", self.imgMosaic.size().getInfo())
        print("see band Names the first ")
        # print(" ==== ", ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)

    # def process_re_escalar_img (self, imgA):
    #     imgMosaic = imgA.select('blue_median').gte(0).rename('constant');
    #     imgEscalada = imgA.divide(10000).toFloat();
    #     return imgMosaic.addBands(imgEscalada).select(self.featureBands).set('year', imgA.get('year'))

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


    #region Bloco de functions de calculos de Indices 
    # Ratio Vegetation Index
    def agregateBandsIndexRATIO(self, img):
    
        ratioImgY = img.expression("float(b('nir_median') / b('red_median'))")\
                                .rename(['ratio_median']).toFloat()

        ratioImgwet = img.expression("float(b('nir_median_wet') / b('red_median_wet'))")\
                                .rename(['ratio_median_wet']).toFloat()  

        ratioImgdry = img.expression("float(b('nir_median_dry') / b('red_median_dry'))")\
                                .rename(['ratio_median_dry']).toFloat()        

        return img.addBands(ratioImgY).addBands(ratioImgwet).addBands(ratioImgdry)

    # Ratio Vegetation Index
    def agregateBandsIndexRVI(self, img):
    
        rviImgY = img.expression("float(b('red_median') / b('nir_median'))")\
                                .rename(['rvi_median']).toFloat() 
        
        rviImgWet = img.expression("float(b('red_median_wet') / b('nir_median_wet'))")\
                                .rename(['rvi_median_wet']).toFloat() 

        rviImgDry = img.expression("float(b('red_median_dry') / b('nir_median_dry'))")\
                                .rename(['rvi_median']).toFloat()       

        return img.addBands(rviImgY).addBands(rviImgWet).addBands(rviImgDry)

    
    def agregateBandsIndexNDVI(self, img):
    
        ndviImgY = img.expression("float(b('nir_median') - b('red_median')) / (b('nir_median') + b('red_median'))")\
                                .rename(['ndvi_median']).toFloat()    

        ndviImgWet = img.expression("float(b('nir_median_wet') - b('red_median_wet')) / (b('nir_median_wet') + b('red_median_wet'))")\
                                .rename(['ndvi_median_wet']).toFloat()  

        ndviImgDry = img.expression("float(b('nir_median_dry') - b('red_median_dry')) / (b('nir_median_dry') + b('red_median_dry'))")\
                                .rename(['ndvi_median_dry']).toFloat()     

        return img.addBands(ndviImgY).addBands(ndviImgWet).addBands(ndviImgDry)

    
    def agregateBandsIndexNDBI(self, img):
        
        ndbiImgY = img.expression("float(b('swir1_median') - b('nir_median')) / (b('swir1_median') + b('nir_median'))")\
                                .rename(['ndbi_median']).toFloat()    

        ndbiImgWet = img.expression("float(b('swir1_median_wet') - b('nir_median_wet')) / (b('swir1_median_wet') + b('nir_median_wet'))")\
                                .rename(['ndbi_median_wet']).toFloat()  

        ndbiImgDry = img.expression("float(b('swir1_median_dry') - b('nir_median_dry')) / (b('swir1_median_dry') + b('nir_median_dry'))")\
                                .rename(['ndbi_median_dry']).toFloat()     

        return img.addBands(ndbiImgY).addBands(ndbiImgWet).addBands(ndbiImgDry)

    
    def agregateBandsIndexNDMI(self, img):
        
        ndmiImgY = img.expression("float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")\
                                .rename(['ndmi_median']).toFloat()    

        ndmiImgWet = img.expression("float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")\
                                .rename(['ndmi_median_wet']).toFloat()  

        ndmiImgDry = img.expression("float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")\
                                .rename(['ndmi_median_dry']).toFloat()     

        return img.addBands(ndmiImgY).addBands(ndmiImgWet).addBands(ndmiImgDry)

    

    def agregateBandsIndexNBR(self, img):
        
        nbrImgY = img.expression("float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")\
                                .rename(['nbr_median']).toFloat()    

        nbrImgWet = img.expression("float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")\
                                .rename(['nbr_median_wet']).toFloat()  

        nbrImgDry = img.expression("float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")\
                                .rename(['nbr_median_dry']).toFloat()     

        return img.addBands(nbrImgY).addBands(nbrImgWet).addBands(nbrImgDry)


    def agregateBandsIndexNDTI(self, img):
        
        ndtiImgY = img.expression("float(b('swir1_median') - b('swir2_median')) / (b('swir1_median') + b('swir2_median'))")\
                                .rename(['ndti_median']).toFloat()    

        ndtiImgWet = img.expression("float(b('swir1_median_wet') - b('swir2_median_wet')) / (b('swir1_median_wet') + b('swir2_median_wet'))")\
                                .rename(['ndti_median_wet']).toFloat()  

        ndtiImgDry = img.expression("float(b('swir1_median_dry') - b('swir2_median_dry')) / (b('swir1_median_dry') + b('swir2_median_dry'))")\
                                .rename(['ndti_median_dry']).toFloat()     

        return img.addBands(ndtiImgY).addBands(ndtiImgWet).addBands(ndtiImgDry)


    def  agregateBandsIndexNDWI(self, img):
    
        ndwiImgY = img.expression("float(b('nir_median') - b('swir2_median')) / (b('nir_median') + b('swir2_median'))")\
                                .rename(['ndwi_median']).toFloat()       

        ndwiImgWet = img.expression("float(b('nir_median_wet') - b('swir2_median_wet')) / (b('nir_median_wet') + b('swir2_median_wet'))")\
                                .rename(['ndwi_median_wet']).toFloat()   

        ndwiImgDry = img.expression("float(b('nir_median_dry') - b('swir2_median_dry')) / (b('nir_median_dry') + b('swir2_median_dry'))")\
                                .rename(['ndwi_median_dry']).toFloat()   

        return img.addBands(ndwiImgY).addBands(ndwiImgWet).addBands(ndwiImgDry)

    
    def AutomatedWaterExtractionIndex(self, img):    
        aweiY = img.expression(
                            "float(4 * (b('green_median') - b('swir2_median')) - (0.25 * b('nir_median') + 2.75 * b('swir1_median')))"
                        ).rename("awei_median").toFloat() 

        aweiWet = img.expression(
                            "float(4 * (b('green_median_wet') - b('swir2_median_wet')) - (0.25 * b('nir_median_wet') + 2.75 * b('swir1_median_wet')))"
                        ).rename("awei_median_wet").toFloat() 

        aweiDry = img.expression(
                            "float(4 * (b('green_median_dry') - b('swir2_median_dry')) - (0.25 * b('nir_median_dry') + 2.75 * b('swir1_median_dry')))"
                        ).rename("awei_median_dry").toFloat()          
        
        return img.addBands(aweiY).addBands(aweiWet).addBands(aweiDry)

    
    def IndiceIndicadorAgua(self, img):    
        iiaImgY = img.expression(
                            "float((b('green_median') - 4 *  b('nir_median')) / (b('green_median') + 4 *  b('nir_median')))"
                        ).rename("iia_median").toFloat()
        
        iiaImgWet = img.expression(
                            "float((b('green_median_wet') - 4 *  b('nir_median_wet')) / (b('green_median_wet') + 4 *  b('nir_median_wet')))"
                        ).rename("iia_median_wet").toFloat()

        iiaImgDry = img.expression(
                            "float((b('green_median_dry') - 4 *  b('nir_median_dry')) / (b('green_median_dry') + 4 *  b('nir_median_dry')))"
                        ).rename("iia_median_dry").toFloat()
        
        return img.addBands(iiaImgY).addBands(iiaImgWet).addBands(iiaImgDry)

    
    def agregateBandsIndexEVI(self, img):
            
        eviImgY = img.expression(
            "float(2.4 * (b('nir_median') - b('red_median')) / (1 + b('nir_median') + b('red_median')))")\
                .rename(['evi_median']).toFloat() 

        eviImgWet = img.expression(
            "float(2.4 * (b('nir_median_wet') - b('red_median_wet')) / (1 + b('nir_median_wet') + b('red_median_wet')))")\
                .rename(['evi_median_wet']).toFloat()   

        eviImgDry = img.expression(
            "float(2.4 * (b('nir_median_dry') - b('red_median_dry')) / (1 + b('nir_median_dry') + b('red_median_dry')))")\
                .rename(['evi_median_dry']).toFloat()   
        
        return img.addBands(eviImgY).addBands(eviImgWet).addBands(eviImgDry)


    def agregateBandsIndexGVMI(self, img):
        
        gvmiImgY = img.expression(
                        "float ((b('nir_median')  + 0.1) - (b('swir1_median') + 0.02)) / ((b('nir_median') + 0.1) + (b('swir1_median') + 0.02))" 
                    ).rename(['gvmi_median']).toFloat()   

        gvmiImgWet = img.expression(
                        "float ((b('nir_median_wet')  + 0.1) - (b('swir1_median_wet') + 0.02)) / ((b('nir_median_wet') + 0.1) + (b('swir1_median_wet') + 0.02))" 
                    ).rename(['gvmi_median_wet']).toFloat()

        gvmiImgDry = img.expression(
                        "float ((b('nir_median_dry')  + 0.1) - (b('swir1_median_dry') + 0.02)) / ((b('nir_median_dry') + 0.1) + (b('swir1_median_dry') + 0.02))" 
                    ).rename(['gvmi_median_dry']).toFloat()  
    
        return img.addBands(gvmiImgY).addBands(gvmiImgWet).addBands(gvmiImgDry)
    
    def agregateBandsIndexLAI(self, img):

        laiImgY = img.expression(
            "float(3.618 * (b('evi_median') - 0.118))")\
                .rename(['lai_median']).toFloat()

        laiImgWet = img.expression(
            "float(3.618 * (b('evi_median_wet') - 0.118))")\
                .rename(['lai_median_wet']).toFloat()

        laiImgDry = img.expression(
            "float(3.618 * (b('evi_median_dry') - 0.118))")\
                .rename(['lai_median_dry']).toFloat()
    
        return img.addBands(laiImgY).addBands(laiImgWet).addBands(laiImgDry)      

    def agregateBandsIndexGCVI(self, img):    
        gcviImgAY = img.expression(
            "float(b('nir_median')) / (b('green_median')) - 1")\
                .rename(['gcvi_median']).toFloat()   

        gcviImgAWet = img.expression(
            "float(b('nir_median_wet')) / (b('green_median_wet')) - 1")\
                .rename(['gcvi_median_wet']).toFloat() 
                
        gcviImgADry = img.expression(
            "float(b('nir_median_dry')) / (b('green_median_dry')) - 1")\
                .rename(['gcvi_median_dry']).toFloat()      
        
        return img.addBands(gcviImgAY).addBands(gcviImgAWet).addBands(gcviImgADry)

    # Global Environment Monitoring Index GEMI 
    def agregateBandsIndexGEMI(self, img):    
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgAY = img.expression(
            "float((2 * (b('nir_median') * b('nir_median') - b('red_median') * b('red_median')) + 1.5 * b('nir_median')" +
            " + 0.5 * b('red_median')) / (b('nir_median') + b('green_median') + 0.5) )")\
                .rename(['gemi_median']).toFloat()    

        gemiImgAWet = img.expression(
            "float((2 * (b('nir_median_wet') * b('nir_median_wet') - b('red_median_wet') * b('red_median_wet')) + 1.5 * b('nir_median_wet')" +
            " + 0.5 * b('red_median_wet')) / (b('nir_median_wet') + b('green_median_wet') + 0.5) )")\
                .rename(['gemi_median_wet']).toFloat() 

        gemiImgADry = img.expression(
            "float((2 * (b('nir_median_dry') * b('nir_median_dry') - b('red_median_dry') * b('red_median_dry')) + 1.5 * b('nir_median_dry')" +
            " + 0.5 * b('red_median_dry')) / (b('nir_median_dry') + b('green_median_dry') + 0.5) )")\
                .rename(['gemi_median_dry']).toFloat()     
        
        return img.addBands(gemiImgAY).addBands(gemiImgAWet).addBands(gemiImgADry)

    # Chlorophyll vegetation index CVI
    def agregateBandsIndexCVI(self, img):    
        cviImgAY = img.expression(
            "float(b('nir_median') * (b('green_median') / (b('blue_median') * b('blue_median'))))")\
                .rename(['cvi_median']).toFloat()  

        cviImgAWet = img.expression(
            "float(b('nir_median_wet') * (b('green_median_wet') / (b('blue_median_wet') * b('blue_median_wet'))))")\
                .rename(['cvi_median_wet']).toFloat()

        cviImgADry = img.expression(
            "float(b('nir_median_dry') * (b('green_median_dry') / (b('blue_median_dry') * b('blue_median_dry'))))")\
                .rename(['cvi_median_dry']).toFloat()      
        
        return img.addBands(cviImgAY).addBands(cviImgAWet).addBands(cviImgADry)

    # Green leaf index  GLI
    def agregateBandsIndexGLI(self,img):    
        gliImgY = img.expression(
            "float((2 * b('green_median') - b('red_median') - b('blue_median')) / (2 * b('green_median') + b('red_median') + b('blue_median')))")\
                .rename(['gli_median']).toFloat()    

        gliImgWet = img.expression(
            "float((2 * b('green_median_wet') - b('red_median_wet') - b('blue_median_wet')) / (2 * b('green_median_wet') + b('red_median_wet') + b('blue_median_wet')))")\
                .rename(['gli_median_wet']).toFloat()   

        gliImgDry = img.expression(
            "float((2 * b('green_median_dry') - b('red_median_dry') - b('blue_median_dry')) / (2 * b('green_median_dry') + b('red_median_dry') + b('blue_median_dry')))")\
                .rename(['gli_median_dry']).toFloat()       
        
        return img.addBands(gliImgY).addBands(gliImgWet).addBands(gliImgDry)

    # Shape Index  IF 
    def agregateBandsIndexShapeI(self, img):    
        shapeImgAY = img.expression(
            "float((2 * b('red_median') - b('green_median') - b('blue_median')) / (b('green_median') - b('blue_median')))")\
                .rename(['shape_median']).toFloat()  

        shapeImgAWet = img.expression(
            "float((2 * b('red_median_wet') - b('green_median_wet') - b('blue_median_wet')) / (b('green_median_wet') - b('blue_median_wet')))")\
                .rename(['shape_median_wet']).toFloat() 

        shapeImgADry = img.expression(
            "float((2 * b('red_median_dry') - b('green_median_dry') - b('blue_median_dry')) / (b('green_median_dry') - b('blue_median_dry')))")\
                .rename(['shape_median_dry']).toFloat()      
        
        return img.addBands(shapeImgAY).addBands(shapeImgAWet).addBands(shapeImgADry)

    # Aerosol Free Vegetation Index (2100 nm) 
    def agregateBandsIndexAFVI(self, img):    
        afviImgAY = img.expression(
            "float((b('nir_median') - 0.5 * b('swir2_median')) / (b('nir_median') + 0.5 * b('swir2_median')))")\
                .rename(['afvi_median']).toFloat()  

        afviImgAWet = img.expression(
            "float((b('nir_median_wet') - 0.5 * b('swir2_median_wet')) / (b('nir_median_wet') + 0.5 * b('swir2_median_wet')))")\
                .rename(['afvi_median_wet']).toFloat()

        afviImgADry = img.expression(
            "float((b('nir_median_dry') - 0.5 * b('swir2_median_dry')) / (b('nir_median_dry') + 0.5 * b('swir2_median_dry')))")\
                .rename(['afvi_median_dry']).toFloat()      
        
        return img.addBands(afviImgAY).addBands(afviImgAWet).addBands(afviImgADry)

    # Advanced Vegetation Index 
    def agregateBandsIndexAVI(self, img):    
        aviImgAY = img.expression(
            "float((b('nir_median')* (1.0 - b('red_median')) * (b('nir_median') - b('red_median'))) ** 1/3)")\
                .rename(['avi_median']).toFloat()   

        aviImgAWet = img.expression(
            "float((b('nir_median_wet')* (1.0 - b('red_median_wet')) * (b('nir_median_wet') - b('red_median_wet'))) ** 1/3)")\
                .rename(['avi_median_wet']).toFloat()

        aviImgADry = img.expression(
            "float((b('nir_median_dry')* (1.0 - b('red_median_dry')) * (b('nir_median_dry') - b('red_median_dry'))) ** 1/3)")\
                .rename(['avi_median_dry']).toFloat()     
        
        return img.addBands(aviImgAY).addBands(aviImgAWet).addBands(aviImgADry)

    #  NDDI Normalized Differenece Drought Index
    def agregateBandsIndexNDDI(self, img):
        nddiImg = img.expression(
            "float((b('ndvi_median') - b('ndwi_median')) / (b('ndvi_median') + b('ndwi_median')))"
        ).rename(['nddi_median']).toFloat() 
        
        nddiImgWet = img.expression(
            "float((b('ndvi_median_wet') - b('ndwi_median_wet')) / (b('ndvi_median_wet') + b('ndwi_median_wet')))"
        ).rename(['nddi_median_wet']).toFloat()  
        
        nddiImgDry = img.expression(
            "float((b('ndvi_median_dry') - b('ndwi_median_dry')) / (b('ndvi_median_dry') + b('ndwi_median_dry')))"
        ).rename(['nddi_median_dry']).toFloat()  

        return img.addBands(nddiImg).addBands(nddiImgWet).addBands(nddiImgDry)
    

    # Bare Soil Index 
    def agregateBandsIndexBSI(self,img):    
        bsiImgY = img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")\
                .rename(['bsi_median']).toFloat()  

        bsiImgWet = img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")\
                .rename(['bsi_median']).toFloat()

        bsiImgDry = img.expression(
            "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / " + 
                "((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")\
                .rename(['bsi_median']).toFloat()      
        
        return img.addBands(bsiImgY).addBands(bsiImgWet).addBands(bsiImgDry)

    # BRBA	Band Ratio for Built-up Area  
    def agregateBandsIndexBRBA(self,img):    
        brbaImgY = img.expression(
            "float(b('red_median') / b('swir1_median'))")\
                .rename(['brba_median']).toFloat()   

        brbaImgWet = img.expression(
            "float(b('red_median_wet') / b('swir1_median_wet'))")\
                .rename(['brba_median_wet']).toFloat()

        brbaImgDry = img.expression(
            "float(b('red_median_dry') / b('swir1_median_dry'))")\
                .rename(['brba_median_dry']).toFloat()     
        
        return img.addBands(brbaImgY).addBands(brbaImgWet).addBands(brbaImgDry)

    # DSWI5	Disease-Water Stress Index 5
    def agregateBandsIndexDSWI5(self,img):    
        dswi5ImgY = img.expression(
            "float((b('nir_median') + b('green_median')) / (b('swir1_median') + b('red_median')))")\
                .rename(['dswi5_median']).toFloat() 

        dswi5ImgWet = img.expression(
            "float((b('nir_median_wet') + b('green_median_wet')) / (b('swir1_median_wet') + b('red_median_wet')))")\
                .rename(['dswi5_median_wet']).toFloat() 

        dswi5ImgDry = img.expression(
            "float((b('nir_median_dry') + b('green_median_dry')) / (b('swir1_median_dry') + b('red_median_dry')))")\
                .rename(['dswi5_median_dry']).toFloat() 

        return img.addBands(dswi5ImgY).addBands(dswi5ImgWet).addBands(dswi5ImgDry)

    # LSWI	Land Surface Water Index
    def agregateBandsIndexLSWI(self,img):    
        lswiImgY = img.expression(
            "float((b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median')))")\
                .rename(['lswi_median']).toFloat()  

        lswiImgWet = img.expression(
            "float((b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet')))")\
                .rename(['lswi_median_wet']).toFloat()

        lswiImgDry = img.expression(
            "float((b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry')))")\
                .rename(['lswi_median_dry']).toFloat()      
        
        return img.addBands(lswiImgY).addBands(lswiImgWet).addBands(lswiImgDry)

    # MBI	Modified Bare Soil Index
    def agregateBandsIndexMBI(self,img):    
        mbiImgY = img.expression(
            "float(((b('swir1_median') - b('swir2_median') - b('nir_median')) /" + 
                " (b('swir1_median') + b('swir2_median') + b('nir_median'))) + 0.5)")\
                    .rename(['mbi_median']).toFloat() 

        mbiImgWet = img.expression(
            "float(((b('swir1_median_wet') - b('swir2_median_wet') - b('nir_median_wet')) /" + 
                " (b('swir1_median_wet') + b('swir2_median_wet') + b('nir_median_wet'))) + 0.5)")\
                    .rename(['mbi_median_wet']).toFloat() 

        mbiImgDry = img.expression(
            "float(((b('swir1_median_dry') - b('swir2_median_dry') - b('nir_median_dry')) /" + 
                " (b('swir1_median_dry') + b('swir2_median_dry') + b('nir_median_dry'))) + 0.5)")\
                    .rename(['mbi_median_dry']).toFloat()       
        
        return img.addBands(mbiImgY).addBands(mbiImgWet).addBands(mbiImgDry)

    # UI	Urban Index	urban
    def agregateBandsIndexUI(self,img):    
        uiImgY = img.expression(
            "float((b('swir2_median') - b('nir_median')) / (b('swir2_median') + b('nir_median')))")\
                .rename(['ui_median']).toFloat()  

        uiImgWet = img.expression(
            "float((b('swir2_median_wet') - b('nir_median_wet')) / (b('swir2_median_wet') + b('nir_median_wet')))")\
                .rename(['ui_median_wet']).toFloat() 

        uiImgDry = img.expression(
            "float((b('swir2_median_dry') - b('nir_median_dry')) / (b('swir2_median_dry') + b('nir_median_dry')))")\
                .rename(['ui_median_dry']).toFloat()       
        
        return img.addBands(uiImgY).addBands(uiImgWet).addBands(uiImgDry)

    # OSAVI	Optimized Soil-Adjusted Vegetation Index
    def agregateBandsIndexOSAVI(self,img):    
        osaviImgY = img.expression(
            "float(b('nir_median') - b('red_median')) / (0.16 + b('nir_median') + b('red_median'))")\
                .rename(['osavi_median']).toFloat() 

        osaviImgWet = img.expression(
            "float(b('nir_median_wet') - b('red_median_wet')) / (0.16 + b('nir_median_wet') + b('red_median_wet'))")\
                .rename(['osavi_median_wet']).toFloat() 

        osaviImgDry = img.expression(
            "float(b('nir_median_dry') - b('red_median_dry')) / (0.16 + b('nir_median_dry') + b('red_median_dry'))")\
                .rename(['osavi_median_dry']).toFloat()        
        
        return img.addBands(osaviImgY).addBands(osaviImgWet).addBands(osaviImgDry)

    # MSAVI	modifyed Soil-Adjusted Vegetation Index
    # [ 2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR-RED)) ]/2
    def agregateBandsIndexMSAVI(self,img):    
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
        
        return img.addBands(msaviImgY).addBands(msaviImgWet).addBands(msaviImgDry)

    # GSAVI	Optimized Soil-Adjusted Vegetation Index
    # (NIR - GREEN) /(0.5 + NIR + GREEN) * 1.5) 
    def agregateBandsIndexGSAVI(self,img):    
        gsaviImgY = img.expression(
            "float(b('nir_median') - b('green_median')) / ((0.5 + b('nir_median') + b('green_median')) * 1.5)")\
                .rename(['gsavi_median']).toFloat() 

        gsaviImgWet = img.expression(
            "float(b('nir_median_wet') - b('green_median_wet')) / ((0.5 + b('nir_median_wet') + b('green_median_wet')) * 1.5)")\
                .rename(['gsavi_median_wet']).toFloat() 

        gsaviImgDry = img.expression(
            "float(b('nir_median_dry') - b('green_median_dry')) / ((0.5 + b('nir_median_dry') + b('green_median_dry')) * 1.5)")\
                .rename(['gsavi_median_dry']).toFloat()        
        
        return img.addBands(gsaviImgY).addBands(gsaviImgWet).addBands(gsaviImgDry)

    # Normalized Difference Red/Green Redness Index  RI
    def agregateBandsIndexRI(self, img):        
        riImgY = img.expression(
            "float(b('nir_median') - b('green_median')) / (b('nir_median') + b('green_median'))")\
                .rename(['ri_median']).toFloat()   

        riImgWet = img.expression(
            "float(b('nir_median_wet') - b('green_median_wet')) / (b('nir_median_wet') + b('green_median_wet'))")\
                .rename(['ri_median_wet']).toFloat()

        riImgDry = img.expression(
            "float(b('nir_median_dry') - b('green_median_dry')) / (b('nir_median_dry') + b('green_median_dry'))")\
                .rename(['ri_median_dry']).toFloat()    
        
        return img.addBands(riImgY).addBands(riImgWet).addBands(riImgDry)    

    # Tasselled Cap - brightness 
    def agregateBandsIndexBrightness(self, img):    
        tasselledCapImgY = img.expression(
            "float(0.3037 * b('blue_median') + 0.2793 * b('green_median') + 0.4743 * b('red_median')  " + 
                "+ 0.5585 * b('nir_median') + 0.5082 * b('swir1_median') +  0.1863 * b('swir2_median'))")\
                    .rename(['brightness_median']).toFloat()

        tasselledCapImgWet = img.expression(
            "float(0.3037 * b('blue_median_wet') + 0.2793 * b('green_median_wet') + 0.4743 * b('red_median_wet')  " + 
                "+ 0.5585 * b('nir_median_wet') + 0.5082 * b('swir1_median_wet') +  0.1863 * b('swir2_median_wet'))")\
                    .rename(['brightness_median_wet']).toFloat()

        tasselledCapImgDry = img.expression(
            "float(0.3037 * b('blue_median_dry') + 0.2793 * b('green_median_dry') + 0.4743 * b('red_median_dry')  " + 
                "+ 0.5585 * b('nir_median_dry') + 0.5082 * b('swir1_median_dry') +  0.1863 * b('swir2_median_dry'))")\
                    .rename(['brightness_median_dry']).toFloat() 
        
        return img.addBands(tasselledCapImgY).addBands(tasselledCapImgWet).addBands(tasselledCapImgDry)
    
    # Tasselled Cap - wetness 
    def agregateBandsIndexwetness(self, img): 

        tasselledCapImgY = img.expression(
            "float(0.1509 * b('blue_median') + 0.1973 * b('green_median') + 0.3279 * b('red_median')  " + 
                "+ 0.3406 * b('nir_median') + 0.7112 * b('swir1_median') +  0.4572 * b('swir2_median'))")\
                    .rename(['wetness_median']).toFloat() 
        
        tasselledCapImgWet = img.expression(
            "float(0.1509 * b('blue_median_wet') + 0.1973 * b('green_median_wet') + 0.3279 * b('red_median_wet')  " + 
                "+ 0.3406 * b('nir_median_wet') + 0.7112 * b('swir1_median_wet') +  0.4572 * b('swir2_median_wet'))")\
                    .rename(['wetness_median_wet']).toFloat() 
        
        tasselledCapImgDry = img.expression(
            "float(0.1509 * b('blue_median_dry') + 0.1973 * b('green_median_dry') + 0.3279 * b('red_median_dry')  " + 
                "+ 0.3406 * b('nir_median_dry') + 0.7112 * b('swir1_median_dry') +  0.4572 * b('swir2_median_dry'))")\
                    .rename(['wetness_median_dry']).toFloat() 
        
        return img.addBands(tasselledCapImgY).addBands(tasselledCapImgWet).addBands(tasselledCapImgDry)
    
    # Moisture Stress Index (MSI)
    def agregateBandsIndexMSI(self, img):    
        msiImgY = img.expression(
            "float( b('nir_median') / b('swir1_median'))")\
                .rename(['msi_median']).toFloat() 
        
        msiImgWet = img.expression(
            "float( b('nir_median_wet') / b('swir1_median_wet'))")\
                .rename(['msi_median_wet']).toFloat() 

        msiImgDry = img.expression(
            "float( b('nir_median_dry') / b('swir1_median_dry'))")\
                .rename(['msi_median_dry']).toFloat() 
        
        return img.addBands(msiImgY).addBands(msiImgWet).addBands(msiImgDry)


    def agregateBandsIndexsPRI(self, img):        
        priImgY = img.expression(
                                "float((b('green_median') - b('blue_median')) / (b('green_median') + b('blue_median')))"
                            ).rename(['pri_median'])   
        spriImgY =   priImgY.expression(
                                "float((b('pri_median') + 1) / 2)").rename(['spri_median']).toFloat()  

        priImgWet = img.expression(
                                "float((b('green_median_wet') - b('blue_median_wet')) / (b('green_median_wet') + b('blue_median_wet')))"
                            ).rename(['pri_median_wet'])   
        spriImgWet =   priImgWet.expression(
                                "float((b('pri_median_wet') + 1) / 2)").rename(['spri_median_wet']).toFloat()

        priImgDry = img.expression(
                                "float((b('green_median') - b('blue_median')) / (b('green_median') + b('blue_median')))"
                            ).rename(['pri_median_dry'])   
        spriImgDry =   priImgDry.expression(
                                "float((b('pri_median_dry') + 1) / 2)").rename(['spri_median']).toFloat()
    
        return img.addBands(spriImgY).addBands(spriImgWet).addBands(spriImgDry)
    

    def agregateBandsIndexCO2Flux(self, img):        
        ndviImg = img.expression(
                            "float(b('nir_median') - b('swir2_median')) / (b('nir_median') + b('swir2_median'))"
                        ).rename(['ndvi_median']).toFloat() 
        ndviImgWet = img.expression(
                            "float(b('nir_median_wet') - b('swir2_median_wet')) / (b('nir_median_wet') + b('swir2_median_wet'))"
                        ).rename(['ndvi_median_wet']).toFloat() 
        ndviImgDry = img.expression(
                            "float(b('nir_median_dry') - b('swir2_median_dry')) / (b('nir_median_dry') + b('swir2_median_dry'))"
                        ).rename(['ndvi_median_dry']).toFloat() 
        priImg = img.expression(
                            "float((b('green_median') - b('blue_median')) / (b('green_median') + b('blue_median')))"
                        ).rename(['pri_median']).toFloat()   
        priImgWet = img.expression(
                            "float((b('green_median_wet') - b('blue_median_wet')) / (b('green_median_wet') + b('blue_median_wet')))"
                        ).rename(['pri_median_wet']).toFloat()  
        priImgDry = img.expression(
                            "float((b('green_median_dry') - b('blue_median_dry')) / (b('green_median_dry') + b('blue_median_dry')))"
                        ).rename(['pri_median_dry']).toFloat()  
        spriImg =   priImg.expression(
                                "float((b('pri_median') + 1) / 2)").rename(['spri_median']).toFloat()
        spriImgWet =   priImgWet.expression(
                                "float((b('pri_median_wet') + 1) / 2)").rename(['spri_median_wet']).toFloat()
        spriImgDry =   priImgDry.expression(
                                "float((b('pri_median_dry') + 1) / 2)").rename(['spri_median_dry']).toFloat()

        co2FluxImg = ndviImg.multiply(spriImg).rename(['co2flux_median'])   
        co2FluxImgWet = ndviImgWet.multiply(spriImgWet).rename(['co2flux_median_wet']) 
        co2FluxImgDry = ndviImgDry.multiply(spriImgDry).rename(['co2flux_median_dry']) 
        
        return img.addBands(co2FluxImg).addBands(co2FluxImgWet).addBands(co2FluxImgDry)


    def agregateBandsTexturasGLCM(self, img):        
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

        return  img.addBands(contrastnir).addBands(contrastred
                        ).addBands(contrastnirDry).addBands(contrastredDry)    

    
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
                                ).rename('ndfia' + sufixo)

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


    #endregion


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

        imageW = self.agregateBandsIndexEVI(imagem)
        imageW = self.agregateBandsIndexLAI(imageW)
        imageW = self.agregateBandsIndexNDVI(imageW)
        imageW = self.agregateBandsIndexRATIO(imageW)  #
        imageW = self.agregateBandsIndexRVI(imageW)    #    
        imageW = self.agregateBandsIndexNDWI(imageW)  #        
        imageW = self.AutomatedWaterExtractionIndex(imageW)  # awei     
        imageW = self.IndiceIndicadorAgua(imageW)    #      
        imageW = self.agregateBandsIndexGCVI(imageW)   #   
        imageW = self.agregateBandsIndexGEMI(imageW)
        imageW = self.agregateBandsIndexCVI(imageW) 
        imageW = self.agregateBandsIndexGLI(imageW) 
        imageW = self.agregateBandsIndexShapeI(imageW) 
        imageW = self.agregateBandsIndexAFVI(imageW) 
        imageW = self.agregateBandsIndexAVI(imageW) 
        imageW = self.agregateBandsIndexBSI(imageW) 
        imageW = self.agregateBandsIndexBRBA(imageW) 
        imageW = self.agregateBandsIndexDSWI5(imageW) 
        imageW = self.agregateBandsIndexLSWI(imageW) 
        imageW = self.agregateBandsIndexMBI(imageW) 
        imageW = self.agregateBandsIndexUI(imageW) 
        imageW = self.agregateBandsIndexRI(imageW) 
        imageW = self.agregateBandsIndexOSAVI(imageW)  #  
        imageW = self.agregateBandsIndexNDDI(imageW)   
        imageW = self.agregateBandsIndexNDMI(imageW) 
        imageW = self.agregateBandsIndexwetness(imageW)   #   
        imageW = self.agregateBandsIndexBrightness(imageW)  #  
        imageW = self.agregateBandsIndexGVMI(imageW)     
        imageW = self.agregateBandsTexturasGLCM(imageW)     #
        imageW = self.addSlopeAndHilshade(imageW)    #
        imageW = self.agregateBandsIndexNDBI(imageW)   #   
        imageW = self.agregateBandsIndexMSAVI(imageW)  #  
        imageW = self.agregateBandsIndexGSAVI(imageW)     
        imageW = self.agregateBandsIndexNBR(imageW)     #
        imageW = self.agregateBandsIndexNDTI(imageW) 
        imageW = self.agregateBandsIndexCO2Flux(imageW) 
        imageW = self.agregate_Bands_SMA_NDFIa(imageW)

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
    
    def make_mosaicofromIntervalo(self, colMosaic, year_courrent):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]

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

        return mosaico

    def iterate_bacias(self, _nbacia):        

        # loading geometry bacim
        baciabuffer = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                            .filter(ee.Filter.eq('nunivotto4', _nbacia)))
        print(f"know about the geometry 'nunivotto4' >>  {_nbacia
                        } loaded < {baciabuffer.size().getInfo()} > geometry" )    
        # baciabuffer = baciabuffer.geometry()
        maskBaciaBuffer = baciabuffer.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)

        for nyear in self.lst_year[:]:
            bandYear = 'classification_' + str(nyear)
            print(f" processing _nbacia => {_nbacia} <> {bandYear} ")

            rois_Samples = ee.FeatureCollection(os.path.join(self.options['asset_ROIs_reference'], f"{_nbacia}_{nyear}_cd"))   
            dict_classes = rois_Samples.aggregate_histogram('class').getInfo()         
            print("dictionario de classes ", dict_classes)

            # # testando coincidencia com a geometria 
            # otherROIs = rois_Samples.filterBounds(baciabuffer.geometry())
            # print(" supervise ", otherROIs.size().getInfo())

            imgColfiltered = self.imgMosaic.filter(ee.Filter.eq('year', nyear)) 
            imgColfiltered = imgColfiltered.mosaic().updateMask(maskBaciaBuffer) 

            # print("size images ", imgColfiltered.size().getInfo())
            # sys.exit()
            #
            # print("metadado bandas names ", imgColfiltered.bandNames().getInfo())
            print("----- calculado todos os old(102) now 123 indices ---------------------")
            img_recMosaicnewB = self.CalculateIndice(imgColfiltered)
            # print("metadados bandas Mosaico Calculado  >>> \n ", img_recMosaicnewB.bandNames().getInfo())
            # sys.exit()

            # print("numero de ptos controle ", roisAct.size().getInfo())
            # opcoes para o sorteio estratificadoBuffBacia
            featSamples = ee.FeatureCollection([])
            for nclass, NNsample in dict_classes.items():
                nclass = int(float(nclass))
                if NNsample > 10:
                    # sample(region, scale, projection, factor, numPixels, seed, dropNulls, tileScale, geometries)
                    ptosTemp = (
                        img_recMosaicnewB
                        .sample(
                            region=  rois_Samples.filter(ee.Filter.eq('class', nclass )),  
                            scale= 30,
                            dropNulls= True,
                            geometries= True
                        )
                    )
                    ptosTemp = ptosTemp.map(lambda feat: feat.set('class', nclass))
                    featSamples = featSamples.merge(ptosTemp)
            name_exp = f'{_nbacia}_{nyear}_cd'   
            self.save_ROIs_toAsset(ee.FeatureCollection(featSamples), name_exp)
            # print( "name export {name_exp} >> ", ee.FeatureCollection(ptosTemp).size().getInfo())
            # sys.exit() 
 
    # salva ftcol para um assetindexIni
    # lstKeysFolder = ['cROIsN2manualNN', 'cROIsN2clusterNN'] 
    def save_ROIs_toAsset(self, collection, name):
        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['asset_output'] + "/" + name
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("exportando ROIs da bacia $s ...!", name)


def ask_byGrid_saved(dict_asset):
    getlstFeat = ee.data.getList(dict_asset)
    lst_temporalAsset = []
    assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']
    for idAsset in getlstFeat[:]:         
        path_ = idAsset.get('id')        
        name_feat = path_.replace( assetbase + '/', '')
        print("reading <==> " + name_feat)
        idGrade = name_feat.split('_')[2]
        # name_exp = 'rois_grade_' + str(idGrade) + "_" + str(nyear)
        if int(idGrade) not in lst_temporalAsset:
            lst_temporalAsset.append(int(idGrade))
    
    return lst_temporalAsset

asset_grid = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga'
shp_grid = ee.FeatureCollection(asset_grid)

# lstIds = shp_grid.reduceColumns(ee.Reducer.toList(), ['indice']).get('list').getInfo()
# print("   ", lstIds)


reprocessar = False
if reprocessar:
    df = pd.read_csv('lista_gride_with_failsYearSaved.csv')
    lstIdCode = df['idGrid'].tolist()
    print(f"we reprocessing {len(lstIdCode)} gride that fails to samples \n", lstIdCode)

# sys.exit()
param = {
    'anoInicial': 2016,
    'anoFinal': 2022,
    'changeCount': False,
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta': {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',
        '25': 'solkan1201',
        # '60': 'solkanGeodatin',
        '30': 'superconta'
    },
}
def gerenciador(cont):    
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
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
        
        # for lin in tarefas:   
        #     print(str(lin))         
            # relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

askingbySizeFC = False
searchFeatSaved = False
cont = 30
if param['changeCount']:
    cont = gerenciador(cont)

nameBacias = [
    '7411','7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615',  
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
print(f"we have {len(nameBacias)} bacias")

objetoMosaic_exportROI = ClassMosaic_indexs_Spectral()
print("saida ==> ", objetoMosaic_exportROI.options['asset_output'])
# sys.exit()
if searchFeatSaved: 
    lstFeatAsset = ask_byGrid_saved({'id': objetoMosaic_exportROI.options['asset_output']})
    print("   lista de feat ", lstFeatAsset[:5] )
    print("  == size ", len(lstFeatAsset))
    askingbySizeFC = False
else:
    lstFeatAsset = []

# sys.exit()

inicP = 0 # 0, 100
endP = 1   # 100, 200, 300, 600
for cc, item in enumerate(nameBacias[inicP: endP]):
    print(f"# {cc + 1 + inicP} loading geometry grade {item}")   
    if item not in lstFeatAsset:
        objetoMosaic_exportROI.iterate_bacias(item)
        # cont = gerenciador(cont)
    # sys.exit()

