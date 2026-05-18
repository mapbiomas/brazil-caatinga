#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import os
import json
import copy
import sys
import time
from tqdm import tqdm
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

    feat_pts_true = ee.FeatureCollection([])
    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'bioma': 'CAATINGA',
        'biomas': ['CAATINGA', 'CERRADO', 'MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_baciasN2': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
        'asset_baciasN4': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4',
        'asset_cruzN245': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga_BdivN245',
        'asset_shpN5': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_nivel_5_clipReg_Caat',
        'asset_shpGrade': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
        'inputAssetStats': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/stats_mosaics_ba/all_statisticsMosaicC9_',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas80': 'projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'assetMapbiomas100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
        'asset_embedding': "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL",
        'asset_mosaic_sentinelp2': 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',
        'asset_mosaic_sentinelp1': 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
        'asset_fire': 'projects/ee-geomapeamentoipam/assets/MAPBIOMAS_FOGO/COLECAO_2/Colecao2_fogo_mask_v1',
        'asset_befFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_S1v18',
        'asset_filtered': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Tp',
        'asset_alerts': 'users/data_sets_solkan/Alertas/layersClassTP',
        'asset_alerts_SAD': 'users/data_sets_solkan/Alertas/layersImgClassTP_2024_02',
        'asset_alerts_Desf': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_deforestation_secondary_vegetation_v2',
        'asset_input_mask' : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/masks/maks_layers',
        'asset_baseROIs_col9': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
        'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
        'asset_ROIs_manual': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv7N2manual'},
        'asset_ROIs_cluster': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster'}, 
        'asset_ROIs_automatic': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsGradeallBNDNormal'},  #  , coletaROIsv1N245, cROIsGradeallBNDNorm
        'asset_mask_Coincidencia': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_coinciden',
        'asset_mask_estaveis': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_estaveis_v2',
        'asset_mask_fire': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5',
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample', 
        'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2',
        'asset_output_grade': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_byGrades_emb', 
        # Spectral bands selected
        'lsClasse': [4, 3, 12, 15, 18, 21, 22, 33],
        'lsPtos': [300, 500, 300, 350, 150, 100, 150, 300],
        "anoIntInit": 2016,
        "anoIntFin": 2025,
        'janela': 3,
        'nfolder': 'cROIsN5allBND'
    }
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
    def __init__(self, testando):
        """
        Initializes the ClassMosaic_indexs_Spectral object.

        Args:
        testando (object): An object used for testing purposes.
        dictidGrBa (dict): A dictionary containing the id and group of basins.

        Returns:
        None
        """
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        self.testando =  testando                     
        self.sufN = ''
        self.featCStat = None
        self.dictidGrBasin = {}

        self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        self.band_mosaic = band_year + band_wets + band_drys

        print("see band Names the first ")


    def process_normalized_img (self, imgA):         
        """
        Process the normalized image.

        Args:
        imgA (ee.Image): The input image.

        Returns:
        ee.Image: The processed normalized image.
        """
        year = ee.Number(imgA.get('year'))
        featSt = self.featCStat.filter(ee.Filter.eq('year', year)).first()
        
        imgNormal = imgA.select(['slope'], ['slopeA']).divide(1500).toFloat()
        
        bandMos = copy.deepcopy(self.lst_bandExt)
        bandMos.remove('slope')
        
        for bnd in bandMos:
            if bnd not in self.lst_bandExt:
                bndMed = bnd + '_mean'
                bndStd = bnd + '_stdDev'
            else:
                partes = bnd.split('_')
                nbnd = partes[0] + '_median'
                bndMed = nbnd + '_mean'
                bndStd = nbnd + '_stdDev'

            band_tmp = imgA.select(bnd)
            # Normalizing the image 
            # calcZ = (arrX - xmean) / xstd
            calcZ = band_tmp.subtract(ee.Image.constant(featSt.get(bndMed))).divide(
                        ee.Image.constant(featSt.get(bndStd)))
            # expBandAft =  np.exp(-1 * calcZ)
            expBandAft = calcZ.multiply(ee.Image.constant(-1)).exp()
            # return 1 / (1 + expBandAft)
            bndend = expBandAft.add(ee.Image.constant(1)).pow(ee.Image.constant(-1))
            imgNormal = imgNormal.addBands(bndend.rename(bnd + self.sufN))

        return imgA.select(['slope']).addBands(imgNormal.toFloat())#.select(bandMos + ['slopeA'])

    #region Bloco de functions de calculos de Indices 

    # Ratio Vegetation Index
    def agregateBandsIndexRATIO(self, img):
        """
        Aggregates bands for Ratio Vegetation Index (RATIO) calculation.

        Args:
        img (ee.Image): The input image.

        Returns:
        ee.Image: The image with added bands for RATIO index calculation.
        """
        
        ratioImgY = img.expression(f"float(b('nir_median{self.sufN}') / b('red_median{self.sufN}'))")\
                                .rename(['ratio_median']).multiply(10000).toFloat()

        ratioImgwet = img.expression(f"float(b('nir_median_wet{self.sufN}') / b('red_median_wet{self.sufN}'))")\
                                .rename(['ratio_median_wet']).multiply(10000).toFloat()  

        ratioImgdry = img.expression(f"float(b('nir_median_dry{self.sufN}') / b('red_median_dry{self.sufN}'))")\
                                .rename(['ratio_median_dry']).multiply(10000).toFloat()        

        return img.addBands(ratioImgY).addBands(ratioImgwet).addBands(ratioImgdry)

    # Ratio Vegetation Index
    def agregateBandsIndexRVI(self, img):
    
        rviImgY = img.expression(f"float(b('red_median{self.sufN}') / b('nir_median{self.sufN}'))")\
                                .rename(['rvi_median']).multiply(10000).toFloat() 
        
        rviImgWet = img.expression(f"float(b('red_median_wet{self.sufN}') / b('nir_median_wet{self.sufN}'))")\
                                .rename(['rvi_median_wet']).multiply(10000).toFloat() 

        rviImgDry = img.expression(f"float(b('red_median_dry{self.sufN}') / b('nir_median_dry{self.sufN}'))")\
                                .rename(['rvi_median_dry']).multiply(10000).toFloat()       

        return img.addBands(rviImgY).addBands(rviImgWet).addBands(rviImgDry) 

    def agregateBandsIndexNDVI(self, img):
    
        ndviImgY = img.expression(f"float(b('nir_median{self.sufN}') - b('red_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('red_median{self.sufN}'))")\
                                .rename(['ndvi_median']).add(1).multiply(10000).toFloat()    

        ndviImgWet = img.expression(f"float(b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('red_median_wet{self.sufN}'))")\
                                .rename(['ndvi_median_wet']).add(1).multiply(10000).toFloat()  

        ndviImgDry = img.expression(f"float(b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('red_median_dry{self.sufN}'))")\
                                .rename(['ndvi_median_dry']).add(1).multiply(10000).toFloat()     

        return img.addBands(ndviImgY).addBands(ndviImgWet).addBands(ndviImgDry)

    def agregateBandsIndexWater(self, img):
    
        ndwiImgY = img.expression(f"float(b('nir_median{self.sufN}') - b('swir2_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('swir2_median{self.sufN}'))")\
                                .rename(['ndwi_median']).add(1).multiply(10000).toFloat()       

        ndwiImgWet = img.expression(f"float(b('nir_median_wet{self.sufN}') - b('swir2_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('swir2_median_wet{self.sufN}'))")\
                                .rename(['ndwi_median_wet']).add(1).multiply(10000).toFloat()   

        ndwiImgDry = img.expression(f"float(b('nir_median_dry{self.sufN}') - b('swir2_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('swir2_median_dry{self.sufN}'))")\
                                .rename(['ndwi_median_dry']).add(1).multiply(10000).toFloat()   

        return img.addBands(ndwiImgY).addBands(ndwiImgWet).addBands(ndwiImgDry)
    
    def AutomatedWaterExtractionIndex(self, img):    
        aweiY = img.expression(
                            f"float(4 * (b('green_median{self.sufN}') - b('swir2_median{self.sufN}')) - (0.25 * b('nir_median{self.sufN}') + 2.75 * b('swir1_median{self.sufN}')))"
                        ).rename("awei_median").add(1).multiply(10000).toFloat() 

        aweiWet = img.expression(
                            f"float(4 * (b('green_median_wet{self.sufN}') - b('swir2_median_wet{self.sufN}')) - (0.25 * b('nir_median_wet{self.sufN}') + 2.75 * b('swir1_median_wet{self.sufN}')))"
                        ).rename("awei_median_wet").add(1).multiply(10000).toFloat() 

        aweiDry = img.expression(
                            f"float(4 * (b('green_median_dry{self.sufN}') - b('swir2_median_dry{self.sufN}')) - (0.25 * b('nir_median_dry{self.sufN}') + 2.75 * b('swir1_median_dry{self.sufN}')))"
                        ).rename("awei_median_dry").add(1).multiply(10000).toFloat()          
        
        return img.addBands(aweiY).addBands(aweiWet).addBands(aweiDry)
    
    def IndiceIndicadorAgua(self, img):    
        iiaImgY = img.expression(
                            f"float((b('green_median{self.sufN}') - 4 *  b('nir_median{self.sufN}')) / (b('green_median{self.sufN}') + 4 *  b('nir_median{self.sufN}')))"
                        ).add(1).multiply(10000).rename("iia_median").toFloat()
        
        iiaImgWet = img.expression(
                            f"float((b('green_median_wet{self.sufN}') - 4 *  b('nir_median_wet{self.sufN}')) / (b('green_median_wet{self.sufN}') + 4 *  b('nir_median_wet{self.sufN}')))"
                        ).add(1).multiply(10000).rename("iia_median_wet").toFloat()

        iiaImgDry = img.expression(
                            f"float((b('green_median_dry{self.sufN}') - 4 *  b('nir_median_dry{self.sufN}')) / (b('green_median_dry{self.sufN}') + 4 *  b('nir_median_dry{self.sufN}')))"
                        ).add(1).multiply(10000).rename("iia_median_dry").toFloat()
        
        return img.addBands(iiaImgY).addBands(iiaImgWet).addBands(iiaImgDry)
    
    def agregateBandsIndexEVI(self, img):
            
        eviImgY = img.expression(
            f"float(2.4 * (b('nir_median{self.sufN}') - b('red_median{self.sufN}')) / (1 + b('nir_median{self.sufN}') + b('red_median{self.sufN}')))")\
                .add(1).multiply(10000).rename(['evi_median'])     
                # corregir depois para somar 10 e multiplicar 1000

        eviImgWet = img.expression(
            f"float(2.4 * (b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}')) / (1 + b('nir_median_wet{self.sufN}') + b('red_median_wet{self.sufN}')))")\
                .add(1).multiply(10000).rename(['evi_median_wet'])   

        eviImgDry = img.expression(
            f"float(2.4 * (b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}')) / (1 + b('nir_median_dry{self.sufN}') + b('red_median_dry{self.sufN}')))")\
                .add(1).multiply(10000).rename(['evi_median_dry'])   
        
        return img.addBands(eviImgY).addBands(eviImgWet).addBands(eviImgDry)
    
    def agregateBandsIndexLAI(self, img):
        laiImgY = img.expression(
            f"float(3.618 * (b('evi_median{self.sufN}') - 0.118))")\
                .rename(['lai_median']).toFloat()
    
        return img.addBands(laiImgY)    

    def agregateBandsIndexGCVI(self, img):    
        gcviImgAY = img.expression(
            f"float(b('nir_median{self.sufN}')) / (b('green_median{self.sufN}')) - 1")\
                .rename(['gcvi_median']).add(1).multiply(10000).toFloat()   

        gcviImgAWet = img.expression(
            f"float(b('nir_median_wet{self.sufN}')) / (b('green_median_wet{self.sufN}')) - 1")\
                .rename(['gcvi_median_wet']).add(1).multiply(10000).toFloat() 
                
        gcviImgADry = img.expression(
            f"float(b('nir_median_dry{self.sufN}')) / (b('green_median_dry{self.sufN}')) - 1")\
                .rename(['gcvi_median_dry']).add(1).multiply(10000).toFloat()      
        
        return img.addBands(gcviImgAY).addBands(gcviImgAWet).addBands(gcviImgADry)

    # Global Environment Monitoring Index GEMI 
    def agregateBandsIndexGEMI(self, img):    
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgAY = img.expression(
            f"float((2 * (b('nir_median{self.sufN}') * b('nir_median{self.sufN}') - b('red_median{self.sufN}') * b('red_median{self.sufN}')) + 1.5 * b('nir_median{self.sufN}')" +
            f" + 0.5 * b('red_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('green_median{self.sufN}') + 0.5) )")\
                .rename(['gemi_median']).add(2).multiply(10000).toFloat()    

        gemiImgAWet = img.expression(
            f"float((2 * (b('nir_median_wet{self.sufN}') * b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}') * b('red_median_wet{self.sufN}')) " +
            f" + 1.5 * b('nir_median_wet{self.sufN}') + 0.5 * b('red_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('green_median_wet{self.sufN}') + 0.5) )")\
                .rename(['gemi_median_wet']).add(2).multiply(10000).toFloat() 

        gemiImgADry = img.expression(
            f"float((2 * (b('nir_median_dry{self.sufN}') * b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}') * b('red_median_dry{self.sufN}')) + 1.5 * b('nir_median_dry{self.sufN}')" +
            f" + 0.5 * b('red_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('green_median_dry{self.sufN}') + 0.5) )")\
                .rename(['gemi_median_dry']).add(2).multiply(10000).toFloat()     
        
        return img.addBands(gemiImgAY).addBands(gemiImgAWet).addBands(gemiImgADry)

    # Chlorophyll vegetation index CVI
    def agregateBandsIndexCVI(self, img):    
        cviImgAY = img.expression(
            f"float(b('nir_median{self.sufN}') * (b('green_median{self.sufN}') / (b('blue_median{self.sufN}') * b('blue_median{self.sufN}'))))")\
                .add(1).multiply(10000).rename(['cvi_median']).toFloat()  

        cviImgAWet = img.expression(
        f"float(b('nir_median_wet{self.sufN}') * (b('green_median_wet{self.sufN}') / (b('blue_median_wet{self.sufN}') * b('blue_median_wet{self.sufN}'))))")\
                .add(1).multiply(10000).rename(['cvi_median_wet']).toFloat()

        cviImgADry = img.expression(
        f"float(b('nir_median_dry{self.sufN}') * (b('green_median_dry{self.sufN}') / (b('blue_median_dry{self.sufN}') * b('blue_median_dry{self.sufN}'))))")\
                .add(1).multiply(10000).rename(['cvi_median_dry']).toFloat()      
        
        return img.addBands(cviImgAY).addBands(cviImgAWet).addBands(cviImgADry)

    # Green leaf index  GLI
    def agregateBandsIndexGLI(self,img):    
        gliImgY = img.expression(
        f"float((2 * b('green_median{self.sufN}') - b('red_median{self.sufN}') - b('blue_median{self.sufN}')) / (2 * b('green_median{self.sufN}') - b('red_median{self.sufN}') - b('blue_median{self.sufN}')))")\
                .add(1).multiply(10000).rename(['gli_median']).toFloat()    

        gliImgWet = img.expression(
        f"float((2 * b('green_median_wet{self.sufN}') - b('red_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')) / (2 * b('green_median_wet{self.sufN}') - b('red_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')))")\
                .add(1).multiply(10000).rename(['gli_median_wet']).toFloat()   

        gliImgDry = img.expression(
        f"float((2 * b('green_median_dry{self.sufN}') - b('red_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')) / (2 * b('green_median_dry{self.sufN}') - b('red_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')))")\
                .add(1).multiply(10000).rename(['gli_median_dry']).toFloat()       
        
        return img.addBands(gliImgY).addBands(gliImgWet).addBands(gliImgDry)

    # Shape Index  IF # deve corregir 
    def agregateBandsIndexShapeI(self, img):    
        shapeImgAY = img.expression(
        f"float((2 * b('red_median{self.sufN}') - b('green_median{self.sufN}') - b('blue_median{self.sufN}')) / (b('green_median{self.sufN}') - b('blue_median{self.sufN}')))")\
                .rename(['shape_median']).toFloat()  # deve corregir 

        shapeImgAWet = img.expression(
        f"float((2 * b('red_median_wet{self.sufN}') - b('green_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')) / (b('green_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')))")\
                .rename(['shape_median_wet']).toFloat() 

        shapeImgADry = img.expression(
        f"float((2 * b('red_median_dry{self.sufN}') - b('green_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')) / (b('green_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')))")\
                .rename(['shape_median_dry']).toFloat()      
        
        return img.addBands(shapeImgAY).addBands(shapeImgAWet).addBands(shapeImgADry)

    # Aerosol Free Vegetation Index (2100 nm) 
    def agregateBandsIndexAFVI(self, img):    
        afviImgAY = img.expression(
        f"float((b('nir_median{self.sufN}') - 0.5 * b('swir2_median{self.sufN}')) / (b('nir_median{self.sufN}') + 0.5 * b('swir2_median{self.sufN}')))")\
                .add(1).multiply(10000).rename(['afvi_median']).toFloat()  

        afviImgAWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}') - 0.5 * b('swir2_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + 0.5 * b('swir2_median_wet{self.sufN}')))")\
                .add(1).multiply(10000).rename(['afvi_median_wet']).toFloat()

        afviImgADry = img.expression(
        f"float((b('nir_median_dry{self.sufN}') - 0.5 * b('swir2_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + 0.5 * b('swir2_median_dry{self.sufN}')))")\
                .add(1).multiply(10000).rename(['afvi_median_dry']).toFloat()      
        
        return img.addBands(afviImgAY).addBands(afviImgAWet).addBands(afviImgADry)

    # Advanced Vegetation Index 
    def agregateBandsIndexAVI(self, img):    
        aviImgAY = (img.expression(
                f"float((b('nir_median')* (1.0 - b('red_median')) * (b('nir_median') - b('red_median'))) ** 1/3)")
                .divide(100).rename(['avi_median']).toFloat()   )

        aviImgAWet = (img.expression(
                f"float((b('nir_median_wet')* (1.0 - b('red_median_wet')) * (b('nir_median_wet') - b('red_median_wet'))) ** 1/3)")
                .divide(100).rename(['avi_median_wet']).toFloat())

        aviImgADry = (img.expression(
                f"float((b('nir_median_dry')* (1.0 - b('red_median_dry')) * (b('nir_median_dry') - b('red_median_dry'))) ** 1/3)")
                .divide(100).rename(['avi_median_dry']).toFloat()     )
        
        return img.addBands(aviImgAY).addBands(aviImgAWet).addBands(aviImgADry)

        

    # #  NDDI Normalized Differenece Drought Index    
    def agregateBandsIndexNDDI(self, img):
        nddiImg = img.expression(
            "float((b('ndvi_median') - b('ndwi_median')) / (b('ndvi_median') + b('ndwi_median')))"
        ).add(1).multiply(10000).rename(['nddi_median']) 
        
        nddiImgWet = img.expression(
            "float((b('ndvi_median_wet') - b('ndwi_median_wet')) / (b('ndvi_median_wet') + b('ndwi_median_wet')))"
        ).add(1).multiply(10000).rename(['nddi_median_wet'])  
        
        nddiImgDry = img.expression(
            "float((b('ndvi_median_dry') - b('ndwi_median_dry')) / (b('ndvi_median_dry') + b('ndwi_median_dry')))"
        ).add(1).multiply(10000).rename(['nddi_median_dry'])  

        return img.addBands(nddiImg).addBands(nddiImgWet).addBands(nddiImgDry)

    # Bare Soil Index 
    def agregateBandsIndexBSI(self,img):    
        bsiImgY = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('red_median{self.sufN}')) - (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))) / " + 
                f"((b('swir1_median{self.sufN}') + b('red_median{self.sufN}')) + (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))))")\
                .add(1).multiply(10000).rename(['bsi_median']).toFloat()  

        bsiImgWet = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('red_median{self.sufN}')) - (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))) / " + 
                f"((b('swir1_median{self.sufN}') + b('red_median{self.sufN}')) + (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))))")\
                .add(1).multiply(10000).rename(['bsi_median_wet']).toFloat()

        bsiImgDry = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('red_median{self.sufN}')) - (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))) / " + 
                f"((b('swir1_median{self.sufN}') + b('red_median{self.sufN}')) + (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))))")\
                .add(1).multiply(10000).rename(['bsi_median_dry']).toFloat()      
        
        return img.addBands(bsiImgY).addBands(bsiImgWet).addBands(bsiImgDry)

    # BRBA	Band Ratio for Built-up Area  
    def agregateBandsIndexBRBA(self,img):    
        brbaImgY = img.expression(
        f"float(b('red_median{self.sufN}') / b('swir1_median{self.sufN}'))")\
                .add(1).multiply(10000).rename(['brba_median']).toFloat()   

        brbaImgWet = img.expression(
        f"float(b('red_median_wet{self.sufN}') / b('swir1_median_wet{self.sufN}'))")\
                .add(1).multiply(10000).rename(['brba_median_wet']).toFloat()

        brbaImgDry = img.expression(
        f"float(b('red_median_dry{self.sufN}') / b('swir1_median_dry{self.sufN}'))")\
                .add(1).multiply(10000).rename(['brba_median_dry']).toFloat()     
        
        return img.addBands(brbaImgY).addBands(brbaImgWet).addBands(brbaImgDry)

    # DSWI5	Disease-Water Stress Index 5
    def agregateBandsIndexDSWI5(self,img):    
        dswi5ImgY = img.expression(
        f"float((b('nir_median{self.sufN}') + b('green_median{self.sufN}')) / (b('swir1_median{self.sufN}') + b('red_median{self.sufN}')))")\
                .add(1).multiply(10000).rename(['dswi5_median']).toFloat() 

        dswi5ImgWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}') + b('green_median_wet{self.sufN}')) / (b('swir1_median_wet{self.sufN}') + b('red_median_wet{self.sufN}')))")\
                .add(1).multiply(10000).rename(['dswi5_median_wet']).toFloat() 

        dswi5ImgDry = img.expression(
        f"float((b('nir_median_dry{self.sufN}') + b('green_median_dry{self.sufN}')) / (b('swir1_median_dry{self.sufN}') + b('red_median_dry{self.sufN}')))")\
                .add(1).multiply(10000).rename(['dswi5_median_dry']).toFloat() 

        return img.addBands(dswi5ImgY).addBands(dswi5ImgWet).addBands(dswi5ImgDry)

    # LSWI	Land Surface Water Index
    def agregateBandsIndexLSWI(self,img):    
        lswiImgY = img.expression(
        f"float((b('nir_median{self.sufN}') - b('swir1_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('swir1_median{self.sufN}')))")\
                .add(1).multiply(10000).rename(['lswi_median']).toFloat()  

        lswiImgWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}') - b('swir1_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('swir1_median_wet{self.sufN}')))")\
                .add(1).multiply(10000).rename(['lswi_median_wet']).toFloat()

        lswiImgDry = img.expression(
        f"float((b('nir_median_dry{self.sufN}') - b('swir1_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('swir1_median_dry{self.sufN}')))")\
                .add(1).multiply(10000).rename(['lswi_median_dry']).toFloat()      
        
        return img.addBands(lswiImgY).addBands(lswiImgWet).addBands(lswiImgDry)

    # MBI	Modified Bare Soil Index
    def agregateBandsIndexMBI(self,img):    
        mbiImgY = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('swir2_median{self.sufN}') - b('nir_median{self.sufN}')) /" + 
                f" (b('swir1_median{self.sufN}') + b('swir2_median{self.sufN}') + b('nir_median{self.sufN}'))) + 0.5)")\
                    .add(1).multiply(10000).rename(['mbi_median']).toFloat() 

        mbiImgWet = img.expression(
        f"float(((b('swir1_median_wet{self.sufN}') - b('swir2_median_wet{self.sufN}') - b('nir_median_wet{self.sufN}')) /" + 
                f" (b('swir1_median_wet{self.sufN}') + b('swir2_median_wet{self.sufN}') + b('nir_median_wet{self.sufN}'))) + 0.5)")\
                    .add(1).multiply(10000).rename(['mbi_median_wet']).toFloat() 

        mbiImgDry = img.expression(
        f"float(((b('swir1_median_dry{self.sufN}') - b('swir2_median_dry{self.sufN}') - b('nir_median_dry{self.sufN}')) /" + 
                f" (b('swir1_median_dry{self.sufN}') + b('swir2_median_dry{self.sufN}') + b('nir_median_dry{self.sufN}'))) + 0.5)")\
                    .add(1).multiply(10000).rename(['mbi_median_dry']).toFloat()       
        
        return img.addBands(mbiImgY).addBands(mbiImgWet).addBands(mbiImgDry)

    # UI	Urban Index	urban
    def agregateBandsIndexUI(self,img):    
        uiImgY = img.expression(
        f"float((b('swir2_median{self.sufN}') - b('nir_median{self.sufN}')) / (b('swir2_median{self.sufN}') + b('nir_median{self.sufN}')))")\
                .add(1).multiply(10000).rename(['ui_median']).toFloat()  

        uiImgWet = img.expression(
        f"float((b('swir2_median_wet{self.sufN}') - b('nir_median_wet{self.sufN}')) / (b('swir2_median_wet{self.sufN}') + b('nir_median_wet{self.sufN}')))")\
                .add(1).multiply(10000).rename(['ui_median_wet']).toFloat() 

        uiImgDry = img.expression(
        f"float((b('swir2_median_dry{self.sufN}') - b('nir_median_dry{self.sufN}')) / (b('swir2_median_dry{self.sufN}') + b('nir_median_dry{self.sufN}')))")\
                .add(1).multiply(10000).rename(['ui_median_dry']).toFloat()       
        
        return img.addBands(uiImgY).addBands(uiImgWet).addBands(uiImgDry)

    # OSAVI	Optimized Soil-Adjusted Vegetation Index
    def agregateBandsIndexOSAVI(self,img):    
        osaviImgY = img.expression(
        f"float(b('nir_median{self.sufN}') - b('red_median{self.sufN}')) / (0.16 + b('nir_median{self.sufN}') + b('red_median{self.sufN}'))")\
                .add(1).multiply(10000).rename(['osavi_median']).toFloat() 

        osaviImgWet = img.expression(
        f"float(b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}')) / (0.16 + b('nir_median_wet{self.sufN}') + b('red_median_wet{self.sufN}'))")\
                .add(1).multiply(10000).rename(['osavi_median_wet']).toFloat() 

        osaviImgDry = img.expression(
        f"float(b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}')) / (0.16 + b('nir_median_dry{self.sufN}') + b('red_median_dry{self.sufN}'))")\
                .add(1).multiply(10000).rename(['osavi_median_dry']).toFloat()        
        
        return img.addBands(osaviImgY).addBands(osaviImgWet).addBands(osaviImgDry)

    # Normalized Difference Red/Green Redness Index  RI
    def agregateBandsIndexRI(self, img):        
        riImgY = img.expression(
        f"float(b('nir_median{self.sufN}') - b('green_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('green_median{self.sufN}'))")\
                .add(1).multiply(10000).rename(['ri_median']).toFloat()   

        riImgWet = img.expression(
        f"float(b('nir_median_wet{self.sufN}') - b('green_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('green_median_wet{self.sufN}'))")\
                .add(1).multiply(10000).rename(['ri_median_wet']).toFloat()

        riImgDry = img.expression(
        f"float(b('nir_median_dry{self.sufN}') - b('green_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('green_median_dry{self.sufN}'))")\
                .add(1).multiply(10000).rename(['ri_median_dry']).toFloat()    
        
        return img.addBands(riImgY).addBands(riImgWet).addBands(riImgDry)    

    # Tasselled Cap - brightness 
    def agregateBandsIndexBrightness(self, img):    
        tasselledCapImgY = img.expression(
        f"float(0.3037 * b('blue_median{self.sufN}') + 0.2793 * b('green_median{self.sufN}') + 0.4743 * b('red_median{self.sufN}')  " + 
                f"+ 0.5585 * b('nir_median{self.sufN}') + 0.5082 * b('swir1_median{self.sufN}') +  0.1863 * b('swir2_median{self.sufN}'))")\
                    .rename(['brightness_median']).toFloat()

        tasselledCapImgWet = img.expression(
        f"float(0.3037 * b('blue_median_wet{self.sufN}') + 0.2793 * b('green_median_wet{self.sufN}') + 0.4743 * b('red_median_wet{self.sufN}')  " + 
                f"+ 0.5585 * b('nir_median_wet{self.sufN}') + 0.5082 * b('swir1_median_wet{self.sufN}') +  0.1863 * b('swir2_median_wet{self.sufN}'))")\
                    .rename(['brightness_median_wet']).toFloat()

        tasselledCapImgDry = img.expression(
        f"float(0.3037 * b('blue_median_dry{self.sufN}') + 0.2793 * b('green_median_dry{self.sufN}') + 0.4743 * b('red_median_dry{self.sufN}')  " + 
                f"+ 0.5585 * b('nir_median_dry{self.sufN}') + 0.5082 * b('swir1_median_dry{self.sufN}') +  0.1863 * b('swir2_median_dry{self.sufN}'))")\
                    .rename(['brightness_median_dry']).toFloat() 
        
        return img.addBands(tasselledCapImgY).addBands(tasselledCapImgWet).addBands(tasselledCapImgDry)
    
    # Tasselled Cap - wetness 
    def agregateBandsIndexwetness(self, img): 

        tasselledCapImgY = img.expression(
        f"float(0.1509 * b('blue_median{self.sufN}') + 0.1973 * b('green_median{self.sufN}') + 0.3279 * b('red_median{self.sufN}')  " + 
                f"+ 0.3406 * b('nir_median{self.sufN}') + 0.7112 * b('swir1_median{self.sufN}') +  0.4572 * b('swir2_median{self.sufN}'))")\
                    .rename(['wetness_median']).toFloat() 
        
        tasselledCapImgWet = img.expression(
        f"float(0.1509 * b('blue_median_wet{self.sufN}') + 0.1973 * b('green_median_wet{self.sufN}') + 0.3279 * b('red_median_wet{self.sufN}')  " + 
                f"+ 0.3406 * b('nir_median_wet{self.sufN}') + 0.7112 * b('swir1_median_wet{self.sufN}') +  0.4572 * b('swir2_median_wet{self.sufN}'))")\
                    .rename(['wetness_median_wet']).toFloat() 
        
        tasselledCapImgDry = img.expression(
        f"float(0.1509 * b('blue_median_dry{self.sufN}') + 0.1973 * b('green_median_dry{self.sufN}') + 0.3279 * b('red_median_dry{self.sufN}')  " + 
                f"+ 0.3406 * b('nir_median_dry{self.sufN}') + 0.7112 * b('swir1_median_dry{self.sufN}') +  0.4572 * b('swir2_median_dry{self.sufN}'))")\
                    .rename(['wetness_median_dry']).toFloat() 
        
        return img.addBands(tasselledCapImgY).addBands(tasselledCapImgWet).addBands(tasselledCapImgDry)
    
    # Moisture Stress Index (MSI)
    def agregateBandsIndexMSI(self, img):    
        msiImgY = img.expression(
        f"float( b('nir_median{self.sufN}') / b('swir1_median{self.sufN}'))")\
                .add(1).multiply(10000).rename(['msi_median']).toFloat() 
        
        msiImgWet = img.expression(
        f"float( b('nir_median_wet{self.sufN}') / b('swir1_median_wet{self.sufN}'))")\
                .add(1).multiply(10000).rename(['msi_median_wet']).toFloat() 

        msiImgDry = img.expression(
        f"float( b('nir_median_dry{self.sufN}') / b('swir1_median_dry{self.sufN}'))")\
                .add(1).multiply(10000).rename(['msi_median_dry']).toFloat() 
        
        return img.addBands(msiImgY).addBands(msiImgWet).addBands(msiImgDry)


    def agregateBandsIndexGVMI(self, img):        
        gvmiImgY = img.expression(
                    f"float ((b('nir_median{self.sufN}')  + 0.1) - (b('swir1_median{self.sufN}') + 0.02)) " + 
                            f"/ ((b('nir_median{self.sufN}') + 0.1) + (b('swir1_median{self.sufN}') + 0.02))" 
                        ).add(1).multiply(10000).rename(['gvmi_median']).toFloat()  

        gvmiImgWet = img.expression(
                    f"float ((b('nir_median_wet{self.sufN}')  + 0.1) - (b('swir1_median_wet{self.sufN}') + 0.02)) " + 
                            f"/ ((b('nir_median_wet{self.sufN}') + 0.1) + (b('swir1_median_wet{self.sufN}') + 0.02))" 
                        ).add(1).multiply(10000).rename(['gvmi_median_wet']).toFloat()

        gvmiImgDry = img.expression(
                    f"float ((b('nir_median_dry{self.sufN}')  + 0.1) - (b('swir1_median_dry{self.sufN}') + 0.02)) " + 
                            f"/ ((b('nir_median_dry{self.sufN}') + 0.1) + (b('swir1_median_dry{self.sufN}') + 0.02))" 
                        ).add(1).multiply(10000).rename(['gvmi_median_dry']).toFloat()   
    
        return img.addBands(gvmiImgY).addBands(gvmiImgWet).addBands(gvmiImgDry) 
    
    
    def agregateBandsIndexsPRI(self, img):        
        priImgY = img.expression(
                            f"float((b('green_median{self.sufN}') - b('blue_median{self.sufN}')) / (b('green_median{self.sufN}') + b('blue_median{self.sufN}')))"
                            ).rename(['pri_median'])   
        spriImgY =   priImgY.expression(
                            f"float((b('pri_median{self.sufN}') + 1) / 2)").rename(['spri_median']).toFloat()  

        priImgWet = img.expression(
                            f"float((b('green_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')) / (b('green_median_wet{self.sufN}') + b('blue_median_wet{self.sufN}')))"
                            ).rename(['pri_median_wet'])   
        spriImgWet =   priImgWet.expression(
                            f"float((b('pri_median_wet{self.sufN}') + 1) / 2)").rename(['spri_median_wet']).toFloat()

        priImgDry = img.expression(
                            f"float((b('green_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')) / (b('green_median_dry{self.sufN}') + b('blue_median_dry{self.sufN}')))"
                            ).rename(['pri_median_dry'])   
        spriImgDry =   priImgDry.expression(
                            f"float((b('pri_median{self.sufN}') + 1) / 2)").rename(['spri_median_dry']).toFloat()
    
        return img.addBands(spriImgY).addBands(spriImgWet).addBands(spriImgDry)
    

    def agregateBandsIndexCO2Flux(self, img):        
        ndviImg = img.expression(
                f"float(b('nir_median{self.sufN}') - b('swir2_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('swir2_median{self.sufN}'))"
            ).rename(['ndvi']) 
        
        priImg = img.expression(
                            f"float((b('green_median{self.sufN}') - b('blue_median{self.sufN}')) / (b('green_median{self.sufN}') + b('blue_median{self.sufN}')))"
                            ).rename(['pri_median'])   
        spriImg =   priImg.expression(
                            f"float((b('pri_median{self.sufN}') + 1) / 2)").rename(['spri_median'])

        co2FluxImg = ndviImg.multiply(spriImg).rename(['co2flux_median'])   
        
        return img.addBands(co2FluxImg)


    def agregateBandsTexturasGLCM(self, img):        
        img = img.toInt()                
        textura2 = img.select(f'nir_median{self.sufN}').glcmTexture(3)  
        contrastnir = textura2.select(f'nir_median{self.sufN}_contrast').toUint16()
        textura2Dry = img.select(f'nir_median_dry{self.sufN}').glcmTexture(3)  
        contrastnirDry = textura2Dry.select(f'nir_median_dry{self.sufN}_contrast').toUint16()
        #
        textura2R = img.select(f'red_median{self.sufN}').glcmTexture(3)  
        contrastred = textura2R.select(f'red_median{self.sufN}_contrast').toFloat()
        textura2RDry = img.select(f'red_median_dry{self.sufN}').glcmTexture(3)  
        contrastredDry = textura2RDry.select(f'red_median_dry{self.sufN}_contrast').toFloat()

        return  img.addBands(contrastnir).addBands(contrastred
                        ).addBands(contrastnirDry).addBands(contrastredDry)

    
    def agregateBandsIndexNDMI(self, img):
        
        ndmiImgY = img.expression("float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")\
                                .add(1).multiply(10000).rename(['ndmi_median']).toFloat()    

        ndmiImgWet = img.expression("float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")\
                                .add(1).multiply(10000).rename(['ndmi_median_wet']).toFloat()  

        ndmiImgDry = img.expression("float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")\
                                .add(1).multiply(10000).rename(['ndmi_median_dry']).toFloat()     

        return img.addBands(ndmiImgY).addBands(ndmiImgWet).addBands(ndmiImgDry)


    def agregateBandsIndexNDTI(self, img):
        
        ndtiImgY = img.expression("float(b('swir1_median') - b('swir2_median')) / (b('swir1_median') + b('swir2_median'))")\
                                .add(1).multiply(10000).rename(['ndti_median']).toFloat()    

        ndtiImgWet = img.expression("float(b('swir1_median_wet') - b('swir2_median_wet')) / (b('swir1_median_wet') + b('swir2_median_wet'))")\
                                .add(1).multiply(10000).rename(['ndti_median_wet']).toFloat()  

        ndtiImgDry = img.expression("float(b('swir1_median_dry') - b('swir2_median_dry')) / (b('swir1_median_dry') + b('swir2_median_dry'))")\
                                .add(1).multiply(10000).rename(['ndti_median_dry']).toFloat()     

        return img.addBands(ndtiImgY).addBands(ndtiImgWet).addBands(ndtiImgDry)


    def agregateBandsIndexNBR(self, img):
        
        nbrImgY = img.expression("float(b('nir_median') - b('swir1_median')) / (b('nir_median') + b('swir1_median'))")\
                                .add(1).multiply(10000).rename(['nbr_median']).toFloat()    

        nbrImgWet = img.expression("float(b('nir_median_wet') - b('swir1_median_wet')) / (b('nir_median_wet') + b('swir1_median_wet'))")\
                                .add(1).multiply(10000).rename(['nbr_median_wet']).toFloat()  

        nbrImgDry = img.expression("float(b('nir_median_dry') - b('swir1_median_dry')) / (b('nir_median_dry') + b('swir1_median_dry'))")\
                                .add(1).multiply(10000).rename(['nbr_median_dry']).toFloat()     

        return img.addBands(nbrImgY).addBands(nbrImgWet).addBands(nbrImgDry)

    #
    def agregateBandsIndexNDBI(self, img):
        
        ndbiImgY = img.expression("float(b('swir1_median') - b('nir_median')) / (b('swir1_median') + b('nir_median'))")\
                                .add(1).multiply(10000).rename(['ndbi_median']).toFloat()    

        ndbiImgWet = img.expression("float(b('swir1_median_wet') - b('nir_median_wet')) / (b('swir1_median_wet') + b('nir_median_wet'))")\
                                .add(1).multiply(10000).rename(['ndbi_median_wet']).toFloat()  

        ndbiImgDry = img.expression("float(b('swir1_median_dry') - b('nir_median_dry')) / (b('swir1_median_dry') + b('nir_median_dry'))")\
                                .add(1).multiply(10000).rename(['ndbi_median_dry']).toFloat()     

        return img.addBands(ndbiImgY).addBands(ndbiImgWet).addBands(ndbiImgDry)

    #
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
        ]

        fractions = (ee.Image(IMAGE).select(lstBandsSuf)
                                .unmix(endmembers= endmembers)
                                .float())
        fractions = fractions.rename(lstFractions)
        # // print(UNMIXED_IMAGE);
        # GVshade = GV /(1 - SHADE)
        # NDFIa = (GVshade - SOIL) / (GVshade + )
        NDFI_ADJUSTED = fractions.expression(
                                "float(((b('gv') / (1 - b('shade'))) - b('soil')) / ((b('gv') / (1 - b('shade'))) + b('npv') + b('soil')))"
                                ).rename('ndfia')

        NDFI_ADJUSTED = NDFI_ADJUSTED.add(1).multiply(10000).toFloat()
        fractions = fractions.rename(lstFractionsSuf).add(1).multiply(10000)
        RESULT_IMAGE = (fractions.toFloat()
                            .addBands(NDFI_ADJUSTED))

        return ee.Image(RESULT_IMAGE).toFloat()


    def agregate_Bands_SMA_NDFIa(self, img):
        
        indSMA_median =  self.GET_NDFIA(img, '_median')
        indSMA_med_wet =  self.GET_NDFIA(img, '_median_wet')
        indSMA_med_dry =  self.GET_NDFIA(img, '_median_dry')

        return img.addBands(indSMA_median).addBands(indSMA_med_wet).addBands(indSMA_med_dry)

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


    #endregion


    def CalculateIndice(self, imagem):

        # band_feat = [
        #         "ratio","rvi","ndwi","awei","iia","evi","ndvi",
        #         "gcvi","gemi","cvi","gli","shape","afvi",
        #         "avi","bsi","brba","dswi5","lswi","mbi","ui",
        #         "osavi","ri","brightness","wetness","gvmi",
        #         "nir_contrast","red_contrast", "nddi"
        #     ]   

        # agregateBandsIndexMSI, agregateBandsIndexGVMI
        # agregateBandsIndexCO2Flux      faltam

        imageW = self.agregateBandsIndexEVI(imagem)
        imageW = self.agregateBandsIndexNDVI(imageW)
        imageW = self.agregateBandsIndexRATIO(imageW)  #
        imageW = self.agregateBandsIndexRVI(imageW)    #    
        imageW = self.agregateBandsIndexWater(imageW)  #   
        imageW = self.agregateBandsIndexGVMI(imageW)
        imageW = self.AutomatedWaterExtractionIndex(imageW)  #      
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
        imageW = self.agregateBandsIndexOSAVI(imageW)  # msavi e gsavi     
        imageW = self.agregateBandsIndexNDDI(imageW)
        imageW = self.agregateBandsIndexNDMI(imageW) 
        imageW = self.agregateBandsIndexNDBI(imageW)   #
        imageW = self.agregateBandsIndexNDTI(imageW)  
        imageW = self.agregateBandsIndexwetness(imageW)   #   
        imageW = self.agregateBandsIndexBrightness(imageW)  #       
        imageW = self.agregateBandsTexturasGLCM(imageW)     #
        imageW = self.addSlopeAndHilshade(imageW)
        imageW = self.agregate_Bands_SMA_NDFIa(imageW)

        # nbrImgY, msiImgY, spriImgY
        # imageW = self.addSlopeAndHilshade(imageW)

        return imageW #.select(band_feat)# .addBands(imageF)



    def get_mask_Fire_estatics_pixels(self, yyear, exportFire):
        janela = 5        
        imgColFire = ee.ImageCollection( self.options['asset_fire']).filter(
                            ee.Filter.eq('biome', 'CAATINGA'))                            
        # print("image Fire imgColFire ", imgColFire.size().getInfo())
        intervalo_years = [kk for kk in self.lst_year if kk <= yyear and kk > yyear - janela]
        # print(intervalo_years)
        # sys.exit()
        imgTemp = imgColFire.filter(ee.Filter.inList('year', intervalo_years)
                                        ).sum().unmask(0).gt(0)
        # print("image Fire imgTemp ", imgTemp.size().getInfo())

        #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
        imgTemp = imgTemp.rename('fire_'+ str(yyear)).set('type', 'fire', 'year', yyear)

        name_exportimg = 'masks_fire_wind5_' + str(yyear)
        if exportFire:
            self.processoExportarImage(imgTemp,  name_exportimg, self.regionInterest.geometry(), 'fire')
        else:
            return imgTemp

    # ====================================================///
    #          NOVA FUNÇÃO DE ESCALONAMENTO
    # ====================================================///
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

    # https://code.earthengine.google.com/6127586297423a622e139858312aa448   testando coincidencia com a primeira celda da grade 
    def iterate_GradesCaatinga(self, paridCod, lista_ids_gradeYY):
        idCount =  paridCod[0]
        idCod = paridCod[1]
        print(f" # {idCount} =============  processing ID => {idCod}")
        print("years did >> ", lista_ids_gradeYY)
              
        gradeKM = ee.FeatureCollection(self.options['asset_shpGrade']).filter(
                                                ee.Filter.eq('indice', idCod))
        maskgradeKM = gradeKM.reduceToImage(['indice'], ee.Reducer.first()).gt(0)
        gradeKM = gradeKM.geometry()
        
        

        # @collection90: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        lstBandMap = [
            'classification_2016', 'classification_2017', 'classification_2018', 'classification_2019', 
            'classification_2020', 'classification_2021', 'classification_2022', 'classification_2023',
            'classification_2024'
        ]
        collection100 = ee.Image(self.options['assetMapbiomas100']).select(lstBandMap)
        # print(collection100.bandNames().getInfo())
        
        # print(baciaN5.getInfo())
        # imMasCoinc = None
        maksEstaveis = None
        areaColeta = None
        # sys.exit()
        # https://code.earthengine.google.com/ae392a6079570e39c7d480745f3baf5f
        # Loaded camadas de pixeles estaveis  mask_pixels_toSample
        # 'asset_mask_Coincidencia'  // "coincidencia_2020"
        # 'asset_mask_estaveis'      // "mask_estavel_2022"
        # 'asset_mask_fire'          // "mask5wfire_2022"
        # 'asset_mask_toSamples'     // "mask_sample_2022"

        maksEstaveis = ee.ImageCollection(self.options['asset_mask_estaveis']).mosaic().unmask(0) 
        # print("mascara maksEstaveis ", maksEstaveis.bandNames().getInfo())

        # mask de fogo com os ultimos 5 anos de fogo mapeado 
        imMaskFire = ee.ImageCollection(self.options['asset_mask_fire']).mosaic().unmask(0)
        # print("mascara imMaskFire ", imMaskFire.bandNames().getInfo())
        # 1 Concordante, 2 concordante recente, 3 discordante recente,
        # 4 discordante, 5 muito discordante  até 2021
        # imMasCoinc = ee.ImageCollection(self.options['asset_mask_Coincidencia']).mosaic().unmask(0)
        # "classification_2024"
        # carregando os valores de supressão 
        imMaksAlert = (ee.Image(self.options['asset_alerts_Desf']).eq(4)
                                .Or(ee.Image(self.options['asset_alerts_Desf']).eq(6)))

        # imMaskSample = ee.ImageCollection(self.options['asset_mask_toSamples']).mosaic().unmask(0)

        maksEstaveisYY = None
        imMaskFireYY = None
        # imMasCoincYY = None
        imMaksAlertYY = None
        # imMaskSampleYY = None
        # featCol= ee.FeatureCollection([])
        for anoCount in self.lst_year[:]:      
            nomeBaciaEx = "gradeROIs_" + str(idCod) + "_" + str(anoCount) 
            if nomeBaciaEx in lista_ids_gradeYY:          
                bandActiva = 'classification_' + str(anoCount)           

                if anoCount < 2025:
                    # loaded banda da coleção 
                    map_yearAct = collection100.select(bandActiva).rename(['class'])
                    imMaksAlertYY = imMaksAlert.select(bandActiva).eq(0)
                
                if anoCount < 2022:
                    maksEstaveisYY = maksEstaveis.select(f"mask_estavel_{anoCount}").eq(1)
                    imMaskFireYY = imMaskFire.select(f"mask5wfire_{anoCount}").eq(0)
                    # imMasCoincYY = imMasCoinc.select(f"coincidencia_{anoCount}").lt(3) # removidos da segunda coleta
                    # imMaskSampleYY = imMaskSample.select(f"mask_sample_{anoCount}").eq(1) # removidos da segunda coleta

                

                # print("mascara imMaksAlert ", imMaksAlert.bandNames().getInfo())
                areaColeta = (maksEstaveisYY.multiply(imMaskFireYY)
                                            .multiply(imMaksAlertYY) 
                                            # .multiply(imMasCoincYY)  # removidos da segunda coleta
                                            # .multiply(imMaskSampleYY) # removidos da segunda coleta
                                    )
                areaColeta = areaColeta.eq(1) # mask of the area for colects
                
                map_yearAct = (map_yearAct.addBands(
                                        ee.Image.constant(int(anoCount))
                                        .rename('year'))
                                        .updateMask(maskgradeKM)
                            )           
                # filtered year anoCount
                print(f"**** filtered by year {anoCount} >> {nomeBaciaEx}")
                if anoCount < 2024:
                    img_recMosaic = (ee.ImageCollection(self.options['asset_mosaic_sentinelp1'])
                                        .filter(ee.Filter.inList('biome', self.options['biomas']))
                                        .filterBounds(gradeKM) 
                                        .filter(ee.Filter.eq('year', anoCount))
                                        #.select(arqParam.featureBands) 
                            )       
                        
                else:
                    img_recMosaic = (ee.ImageCollection(self.options['asset_mosaic_sentinelp2'])
                                        .filter(ee.Filter.inList('biome', self.options['biomas']))
                                        .filterBounds(gradeKM) 
                                        .filter(ee.Filter.eq('year', anoCount))
                                        #.select(arqParam.featureBands) 
                            )       
                
                print(f" we loaded {img_recMosaic.size().getInfo()} images ")
                
                if self.testando:
                    print(" ⚠️  quantity of images ", img_recMosaic.size().getInfo()) 
                    # print(" list of bands selected ", arqParam.featureBands)
                    # print(" show the bands of the first image ", img_recMosaic.first().bandNames().getInfo()) 
                    # print("metadato ", img_recMosaic.first().getInfo())
                    
                
                img_recMosaic = img_recMosaic.median().updateMask(maskgradeKM).toFloat() 

                if self.testando:
                    print("img_recMosaic   ", img_recMosaic.bandNames().getInfo())       
                
                # sys.exit()

                img_recMosaicnewB = self.CalculateIndice(img_recMosaic)
                
                if self.testando:
                    bndAdd = img_recMosaicnewB.bandNames().getInfo()                    
                    print(f"know bands names {len(bndAdd)}")
                    step = 5
                    for cc in range(0, len(bndAdd), step):
                        print("  ", bndAdd[cc: cc + step])

                
                if anoCount > 2016 and anoCount < 2025:
                    print(f"**** filtered by year {anoCount} >> {nomeBaciaEx}")
                    date_inic = ee.Date.fromYMD(anoCount, 1, 1)
                    img_recEmbedding = (ee.ImageCollection(self.options['asset_embedding'])
                                        .filterBounds(gradeKM) 
                                        .filterDate(date_inic, date_inic.advance(1, 'year'))
                            )   
                    img_recEmb = img_recEmbedding.mosaic().updateMask(maskgradeKM).toFloat() 

                    val_min = self.paramInt['min'][str(anoCount)]
                    val_max = self.paramInt['max'][str(anoCount)]
                    img_recEmbNew = self.scaleToNegOneToOne(img_recEmb, val_min, val_max)
                    time.sleep(3)# esperar 8 segundos

                    img_recMosaicnewB = img_recMosaicnewB.addBands(img_recEmbNew)

                img_recMosaicnewB = (img_recMosaicnewB.toUint16()                                        
                                        # .addBands(ee.Image(img_recMosaicnewB))
                                        .addBands(map_yearAct)
                                )
                img_recMosaicnewB = img_recMosaicnewB.toUint16().updateMask(areaColeta)


                

                # sampleRegions()
                ptosTemp = img_recMosaicnewB.sample(
                                    region=  gradeKM,                              
                                    scale= 10,   
                                    numPixels= 300,
                                    dropNulls= True,
                                    # tileScale= 2,                             
                                    geometries= True
                                )
                ptosTemp = ptosTemp.filter(ee.Filter.notNull(self.featureBands))
                # featCol = featCol.merge(ptosTemp)
                
                self.save_ROIs_toAsset(ee.FeatureCollection(ptosTemp), nomeBaciaEx, idCount)        


    def iterate_idAsset_missing(self, paridAssetVBacN5):

        idCount = paridAssetVBacN5[0]
        partes = paridAssetVBacN5[1].split("_")
        print(partes)
        idCodGrad = partes[1]
        anoCount = int(partes[2])
        print(f"=============  processing {idCount} => {idCodGrad}")
        nomeBacia = self.dictidGrBasin[str(idCodGrad)]

        self.featCStat = ee.FeatureCollection(self.options['inputAssetStats'] + nomeBacia)
        gradeKM = ee.FeatureCollection(self.options['asset_shpGrade']).filter(
                                                ee.Filter.eq('id', int(idCodGrad))).geometry()        
        # print("número de grades KM ", gradeKM.size().getInfo())
        # gradeKM = gradeKM.geometry()        
        imgMosaic = ee.ImageCollection(self.options['asset_mosaic_mapbiomas']
                                                    ).filter(ee.Filter.inList('biome', self.options['biomas'])
                                                        ).filterBounds(gradeKM).select(arqParam.featureBands)        

        # imgMosaic = simgMosaic.map(lambda img: self.process_re_escalar_img(img))
        # print(imgMosaic.first().bandNames().getInfo())

        # @collection90: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection90 = ee.Image(self.options['assetMapbiomas90'])
        if self.testando:
            print(collection90.bandNames().getInfo())
        
        imMasCoinc = None
        maksEstaveis = None
        areaColeta = None
        # sys.exit()           
                    

        bandActiva = 'classification_' + str(anoCount)
        # Loaded camadas de pixeles estaveis
        m_assetPixEst = self.options['asset_estaveis'] + '/masks_estatic_pixels_' + str(anoCount)                
        # mask de fogo com os ultimos 5 anos de fogo mapeado 
        # imMaskFire = self.get_mask_Fire_estatics_pixels(anoCount, False)
        imMaskFire = self.get_class_maskFire(anoCount, gradeKM)
        # loaded banda da coleção 
        map_yearAct = collection90.select(bandActiva).rename(['class'])
        
        if self.testando:
            dictInformation = map_yearAct.getInfo()
            print("\n ============== banda selecionada map_yearAct: =======" )
            for kkey, vval in dictInformation.items():
                print(f" {kkey}   ==> {vval}")
        
        maksEstaveis = ee.Image(m_assetPixEst).rename('estatic')
        if self.testando:
            dictInformation = maksEstaveis.getInfo()
            print("\n============== mascara maksEstaveis ==============")
            for kkey, vval in dictInformation.items():
                print(f" {kkey}   ==> {vval}")

        imMaskFire = ee.Image(imMaskFire)
        if self.testando:
            print("\n****************** mascara imMaskFire ********************")
            dictInformation = imMaskFire.getInfo()
            for kkey, vval in dictInformation.items():
                print(f" {kkey}   ==> {vval}")

        # 1 Concordante, 2 concordante recente, 3 discordante recente,
        # 4 discordante, 5 muito discordante
        if anoCount < 2022:
            asset_PixCoinc = self.options['asset_Coincidencia'] + '/masks_pixels_incidentes_'+ str(anoCount)                     
        else:
            asset_PixCoinc = self.options['asset_Coincidencia'] + '/masks_pixels_incidentes_2021'
            
        imMasCoinc = ee.Image(asset_PixCoinc).rename('coincident')
        if self.testando:
            print("\n============== mascara coincidentes =============")
            dictInformation = imMasCoinc.getInfo()
            for kkey, vval in dictInformation.items():
                print(f" {kkey}   ==> {vval}")

        if anoCount > 1985:
            imMaksAlert = self.get_class_maskAlerts(anoCount)

        elif anoCount >= 2020:
            imMaksAlert = self.AlertasSAD  
        else:
            imMaksAlert = ee.Image.constant(1).rename('mask_alerta')

        if self.testando:
            print(">>>>>>>>>>>>>>> mascara imMaksAlert <<<<<<<<<<<<<<<<<<<")
            dictInformation = imMaksAlert.getInfo()
            for kkey, vval in dictInformation.items():
                print(f" {kkey}   ==> {vval}")

        # areaColeta = imMaskFire.multiply(imMaksAlert)#  #\
        areaColeta = maksEstaveis.multiply(imMasCoinc.lt(4)).multiply(imMaksAlert).multiply(imMaskFire)
        areaColeta = areaColeta.eq(1) # mask of the area for colects
        
        
        map_yearAct = map_yearAct.addBands(
                                ee.Image.constant(int(anoCount)).rename('year')).addBands(
                                    imMasCoinc)           

        img_recMosaic = imgMosaic.filter(ee.Filter.eq('year', anoCount))
        numImgMosaic = img_recMosaic.size().getInfo()
        if self.testando:
            print(" \n Quantas imagens nos temos cobrindo a grade ", numImgMosaic)  
        
        if numImgMosaic > 1:
            img_recMosaicG = img_recMosaic.median().clip(gradeKM) 
        else:
            img_recMosaicG = img_recMosaic.first().clip(gradeKM) 
        # print("metadato ", img_recMosaic.first().bandNames().getInfo())
        img_recMosaicGNorm = self.process_normalized_img(img_recMosaicG)       
        if self.testando:
            print("\n ------------ bands of img_recMosaic  ====== ")
            dictInformation = img_recMosaicGNorm.bandNames().getInfo()
            print(f" Bandas   ==> {dictInformation}")
        img_recMosaicnewB = self.CalculateIndice(img_recMosaicGNorm)
        time.sleep(8)# esperar 8 segundos
        if self.testando:
            bndAdd = img_recMosaicnewB.bandNames().getInfo()
            print(f"know bands names {len(bndAdd)}")
            print("  ", bndAdd)

        img_recMosaicG = img_recMosaicG.addBands(ee.Image(img_recMosaicnewB)).addBands(map_yearAct)
        img_recMosaicG = img_recMosaicG.updateMask(areaColeta)
        nomeBaciaEx = "gradeROIs_" + str(idCodGrad) +  '_' + str(anoCount) + "_wl" 

        # sampleRegions()
        ptosTemp = img_recMosaicG.sample(
                            region=  gradeKM,                              
                            scale= 30,   
                            numPixels= 3000,
                            dropNulls= True,
                            # tileScale= 2,                             
                            geometries= True
                        )

        self.save_ROIs_toAsset(ee.FeatureCollection(ptosTemp), nomeBaciaEx, idCount)        
                
    
    # salva ftcol para um assetindexIni
    # lstKeysFolder = ['cROIsN2manualNN', 'cROIsN2clusterNN'] 
    def save_ROIs_toAsset(self, collection, name, pos):
     
        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['asset_output_grade'] + "/" + name
        }

        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("#", pos, " ==> exportando ROIs da grade $s ...!", name)


# print("len arqParam ", len(arqParam.featuresreduce))

param = {
    # 'bioma': ["CAATINGA", 'CERRADO', 'MATAATLANTICA'],
    # 'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    # 'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    # 'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
    # # 'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/PtosXBaciasBalanceados/',
    # 'asset_ROIs_manual': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv7N2manual'},
    # 'asset_ROIs_cluster': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster'},
    # 'asset_ROIs_automatic': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsGradeallBNDNormal'},
    # 'showAssetFeat': False,
    # 'janela': 5,
    # 'escala': 30,
    # 'sampleSize': 0,
    # 'metodotortora': True,
    # 'tamROIsxClass': 4000,
    # 'minROIs': 1500,
    # # "anoColeta": 2015,
    # 'anoInicial': 1985,
    # 'anoFinal': 2023,
    # 'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 4,
    'conta': {
        # '0': 'caatinga01',
        # '1': 'caatinga02',
        '0': 'caatinga03',
        '1': 'caatinga04',
        '2': 'caatinga05',
        '3': 'superconta',
        # '6': 'solkanGeodatin',
        # '20': 'solkanGeodatin'
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

def GetPolygonsfromFolder(dictAsset):    
    getlistPtos = ee.data.getList(dictAsset)
    ColectionPtos = []
    # print("bacias vizinhas ", nBacias)
    for idAsset in tqdm(getlistPtos):         
        path_ = idAsset.get('id')        
        ColectionPtos.append(path_) 
        name = path_.split("/")[-1]
        if param['showAssetFeat']:
            print("Reading ", name)
        
    return ColectionPtos

def ask_byGrid_saved(dict_asset):
    getlstFeat = ee.data.getList(dict_asset)
    lst_temporalAsset = []
    # assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']
    for idAsset in getlstFeat[:]:         
        path_ = idAsset.get('id')        
        name_feat = path_.split('/')[-1]
        # print("reading <==> " + name_feat)
        # idGrade = name_feat.split('_')[2]
        # name_exp = 'rois_grade_' + str(idGrade) + "_" + str(nyear)
        # if int(idGrade) not in lst_temporalAsset:
        #     print("adding ")
        lst_temporalAsset.append(name_feat)
    
    return lst_temporalAsset

def getlistofRegionYeartoProcessing(lstAssetSaved, lstCodGrade):
    """
    This function generates a list of ROI names that are missing in the saved assets.

    Parameters:
    lstAssetSaved (list): A list of existing ROI asset names.
    lstCodGrade (list): A list of all possivel grade IDs. # 1352

    Returns:
    lstOut (list): A list of ROI names that are missing in the saved assets.
    """
    
    dicttmp = {}
    for nkey in lstAssetSaved:        
        partes = nkey.split("_")
        lstkeys = dicttmp.keys()        
        print("===> ", nkey)
        if partes[1] not in lstkeys:
            # agregando o ano para a lista 
            dicttmp[partes[1]] = [int(partes[2])]
        else:
            dicttmp[partes[1]] += [partes[2]]

    idGradeKeys = [kk for kk in dicttmp.keys()]
    print(f"we have {len(idGradeKeys)} keys basin ")
    # listTarge = []
    lstOut = []    
    # pathroot = None
    print("************* looping all list of  basin ***********" )
    
    for idGrade in tqdm(lstCodGrade):  
        if str(idGrade) in idGradeKeys:
            lstyears = dicttmp[str(idGrade)]
            for year in range(param['anoInicial'], param['anoFinal'] + 1):
                # 74113_1986_wl
                nameAssetW = "gradeROIs_" + str(idGrade) + "_" + str(year) + "_wl"            
                if year not in lstyears:                
                    lstOut.append(nameAssetW)    
        else:
            # if gradeId not in gradelistsaved () then adding gradeId with your years 
            for year in range(param['anoInicial'], param['anoFinal'] + 1):
                nameAssetW = "gradeROIs_" + str(idGrade) + "_" + str(year) + "_wl"            
                lstOut.append(nameAssetW)

    
    print("we show the 30 finaly ", lstAssetSaved[-30:])
    return lstOut 

def getListGradesROIsSaved (nList, show_survive):
    lstB = []
    dictBacin = {}
    for namef in nList:
        nameB = namef.split("/")[-1].split("_")[0]
        if nameB not in lstB:
            lstB.append(nameB)
            dictBacin[nameB] = 1
        else:
            dictBacin[nameB] += 1
    # building list to survive        
    newlstBkeys = []
    for cc, nameB in enumerate(lstB):
        if show_survive:
            print("# ", cc, "  ", nameB, "  ", dictBacin[nameB])
        if int(dictBacin[nameB]) < 39:
            # adding in the new list             
            newlstBkeys.append(nameB)
        else:
            print(f" {nameB} removed")

    if show_survive:
        for cc, nameB in enumerate(newlstBkeys):
            print("# ", cc, "  ", nameB, "  ", dictBacin[nameB])
    
    return newlstBkeys


lstIdCode = [
    3991, 3992, 3993, 3994, 3995, 3996, 3997, 3998, 3999, 4000, 4096, 
    4097, 4098, 4099, 4100, 4101, 4102, 4103, 4104, 4105, 4106, 4107, 4108, 
    4109, 4110, 4111, 4112, 4113, 4114, 4115, 4116, 4117, 4118, 4119, 4120, 
    4121, 4122, 4123, 4414, 4415, 4416, 4417, 4418, 4419, 4420, 4421, 4422, 
    4423, 4424, 4425, 4426, 4427, 4428, 4429, 4430, 4431, 4432, 4433, 4434,
    4435, 4436, 4437, 4438, 4439, 4440, 4202, 4203, 4204, 4205, 4206, 4207, 
    4208, 4209, 4210, 4211, 4212, 4213, 4214, 4215, 4216, 4217, 4218, 4219, 
    4220, 4221, 4222, 4223, 4224, 4225, 4226, 4227, 4228, 4001, 4002, 4003, 
    4004, 4005, 4006, 4007, 4008, 4009, 4010, 4011, 4012, 4013, 4014, 4015, 
    4016, 4308, 4309, 4310, 4311, 4312, 4313, 4314, 4315, 4316, 4317, 4318, 
    4319, 4320, 4321, 4322, 4323, 4324, 4325, 4326, 4327, 4328, 4329, 4330, 
    4331, 4332, 4333, 4334, 4626, 4627, 4628, 4629, 4630, 4631, 4632, 4633, 
    4634, 4635, 4636, 4637, 4638, 4639, 4640, 4641, 4642, 4643, 4644, 4645, 
    4646, 4647, 4648, 4649, 4650, 4651, 4942, 4943, 4944, 4945, 4946, 4947, 
    4948, 4949, 4950, 4951, 4952, 4953, 4954, 4955, 4956, 4957, 4958, 4959, 
    4960, 4961, 4962, 4731, 4732, 4733, 4734, 4735, 4736, 4737, 4738, 4739, 
    4740, 4741, 4742, 4743, 4744, 4745, 4746, 4747, 4748, 4749, 4750, 4751, 
    4752, 4753, 4754, 4755, 4756, 4520, 4521, 4522, 4523, 4524, 4525, 4526, 
    4527, 4528, 4529, 4530, 4531, 4532, 4533, 4534, 4535, 4536, 4537, 4538, 
    4539, 4540, 4541, 4542, 4543, 4544, 4545, 4546, 4837, 4838, 4839, 4840, 
    4841, 4842, 4843, 4844, 4845, 4846, 4847, 4848, 4849, 4850, 4851, 4852, 
    4853, 4854, 4855, 4856, 4857, 5376, 5377, 5378, 5379, 5380, 5381, 5382, 
    5383, 5384, 5385, 5154, 5155, 5156, 5157, 5158, 5159, 5160, 5161, 5162, 
    5163, 5164, 5165, 5166, 5167, 5168, 5169, 5170, 5171, 5172, 5173, 5174, 
    5175, 5471, 5472, 5473, 5474, 5475, 5476, 5477, 5478, 5479, 5480, 5481, 
    5482, 5483, 5484, 5485, 5486, 5487, 5488, 5489, 5490, 5261, 5262, 5263, 
    5264, 5265, 5266, 5267, 5268, 5269, 5270, 5271, 5272, 5273, 5274, 5275, 
    5276, 5277, 5278, 5279, 5280, 5048, 5049, 5050, 5051, 5052, 5053, 5054, 
    5055, 5056, 5057, 5058, 5059, 5060, 5061, 5062, 5063, 5064, 5065, 5066, 
    5067, 5366, 5367, 5368, 5369, 5370, 5371, 5372, 5373, 5374, 5375, 5901, 
    5902, 5903, 5904, 5905, 5906, 5907, 5908, 5683, 5684, 5686, 5687, 5688, 
    5689, 5690, 5691, 5692, 5693, 5694, 5695, 5696, 5697, 5698, 5699, 5700, 
    5792, 5793, 5794, 5795, 5796, 5797, 5798, 5799, 5800, 5801, 5802, 5803, 
    5804, 5805, 5576, 5577, 5578, 5579, 5580, 5581, 5582, 5583, 5584, 5585, 
    5586, 5587, 5588, 5589, 5590, 5591, 5592, 5593, 5594, 5595, 6217, 6218, 
    6219, 6220, 6221, 6222, 6006, 6007, 6008, 6009, 6010, 6011, 6012, 6013, 
    6323, 6324, 6325, 6326, 6327, 6112, 6113, 6114, 6115, 6116, 6117, 6118, 
    2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2425, 2426, 2427, 2428, 
    2429, 2430, 2431, 2432, 2433, 2434, 2220, 2223, 2224, 2840, 2841, 2842, 
    2843, 2844, 2845, 2846, 2847, 2848, 2849, 2850, 2851, 2852, 2853, 2854, 
    2855, 2856, 2633, 2634, 2635, 2636, 2637, 2638, 2639, 2640, 2641, 2642, 
    2643, 2644, 2645, 2646, 2941, 2942, 2943, 2944, 2945, 2946, 2947, 2948, 
    2949, 2950, 2951, 2952, 2953, 2954, 2955, 2956, 2957, 2958, 2959, 2960, 
    2737, 2738, 2739, 2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 
    2749, 2750, 2751, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 
    2538, 2539, 2540, 3360, 3361, 3362, 3363, 3364, 3365, 3366, 3367, 3368, 
    3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377, 3378, 3379, 3380, 
    3381, 3382, 3383, 3150, 3151, 3152, 3153, 3154, 3155, 3156, 3157, 3158, 
    3159, 3160, 3161, 3162, 3163, 3164, 3165, 3166, 3167, 3168, 3169, 3170, 
    3171, 3465, 3466, 3467, 3468, 3469, 3470, 3471, 3472, 3473, 3474, 3475, 
    3476, 3477, 3478, 3479, 3480, 3481, 3482, 3483, 3484, 3485, 3486, 3487, 
    3488, 3489, 3255, 3256, 3257, 3258, 3259, 3260, 3261, 3262, 3263, 3264, 
    3265, 3266, 3267, 3268, 3269, 3270, 3271, 3272, 3273, 3274, 3275, 3276, 
    3277, 3278, 3046, 3047, 3048, 3049, 3050, 3051, 3052, 3053, 3054, 3055, 
    3056, 3057, 3058, 3059, 3060, 3061, 3062, 3063, 3064, 3584, 3585, 3586, 
    3587, 3588, 3589, 3590, 3591, 3592, 3593, 3594, 3885, 3886, 3887, 3888, 
    3889, 3890, 3891, 3892, 3893, 3894, 3895, 3896, 3897, 3898, 3899, 3900, 
    3901, 3902, 3903, 3904, 3905, 3906, 3907, 3908, 3909, 3910, 3911, 3675, 
    3676, 3677, 3678, 3679, 3680, 3681, 3682, 3683, 3684, 3685, 3686, 3687, 
    3688, 3689, 3690, 3691, 3692, 3693, 3694, 3695, 3696, 3697, 3698, 3699, 
    3700, 3780, 3781, 3782, 3783, 3784, 3785, 3786, 3787, 3788, 3789, 3790, 
    3791, 3792, 3793, 3794, 3795, 3796, 3797, 3798, 3799, 3800, 3801, 3802, 
    3803, 3804, 3805, 3570, 3571, 3572, 3573, 3574, 3575, 3576, 3577, 3578, 
    3579, 3580, 3581, 3582, 3583
]

asset_grid = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga'
shp_grid = ee.FeatureCollection(asset_grid)
print("shps de gride ", shp_grid.size().getInfo())
# sys.exit()

changeCount = False
cont = 3
if changeCount:
    cont = gerenciador(cont)
# revisao da coleção 8 
# https://code.earthengine.google.com/5e8af5ef94684a5769e853ad675fc368
# revisão da grade cosntruida 
# https://code.earthengine.google.com/62b0572fcdcb8abbdc2b240eeeda85af


def getPathCSV():
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])
    print("path parents ", pathparent)
    # folder results of CSVs ROIs
    mpath_bndImp = pathparent + '/dados/jsons/'
    print("path of CSVs Rois is \n ==>",  mpath_bndImp)
    return mpath_bndImp


# def get_list_itens(numItem):
    
#     return 

# pathBase = getPathCSV()
# pathjsonBaGr = pathBase + "dict_convert_bacia_N2_toGrade.json"
# with open(pathjsonBaGr, 'r') as fp:
#     try:
#         dictidGrBasin = json.loads(fp.read())
#     except:
#         print("json vacio")
# print(" -- Loading dict_convert_bacia_N2_toGrade.json and convert to dict 💭 -- ")

setTeste = False
show_IdReg = False
colectSaved = True
getLstIds = False
searchFeatSaved = True
reprocessar = False
if reprocessar:
    df = pd.read_csv('lista_gride_with_failsYearSaved.csv')
    lstIdCode = df['idGrid'].tolist()
    print(f"we reprocessing {len(lstIdCode)} gride that fails to samples \n", lstIdCode)



# nlksIDs = [ ]

# if colectSaved:
#     lstAssetFolder = GetPolygonsfromFolder(param['asset_ROIs_automatic'])
#     print(f"lista de Features ROIs Grades saved {len(lstAssetFolder)}   ")       
#     newlstIdGrades = [kk.split("/")[-1] for kk in lstAssetFolder]
#     print("show the first 5 : \n", newlstIdGrades[:5])
#     # get the basin saved
#     print(f"we have {len(newlstIdGrades)} asset to search in what year is missing some ROIs from of  {numberGradeYearsAll} possivel")
#     sys.exit()
#     lstGradeMissing =  getlistofRegionYeartoProcessing(newlstIdGrades, nlksIDs)
#     print(f"we have {len(lstGradeMissing)} asset that are missing")
#     lstProcpool = [(cc, kk) for cc, kk in enumerate(lstGradeMissing[:])]    

# else:
#     lstProcpool = [(cc, kk) for cc, kk in enumerate(nlksIDs[:])]

# print("size of list to processe ", len(lstProcpool))
# sys.exit()
lstKeysFolder = 'asset_shpGrade'  # , , 'asset_ROIs_manual', 'asset_ROIs_cluster'
objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(False)
print("saida ==> ", objetoMosaic_exportROI.options['asset_output_grade'])
print("============= Get parts of the list ===============")

askingbySizeFC = False
if searchFeatSaved: 
    lstFeatAsset = ask_byGrid_saved({'id': objetoMosaic_exportROI.options['asset_output_grade']})
    print("   lista de feat ", lstFeatAsset[:5] )
    print(f" ====== size das grade_year feitas {len(lstFeatAsset)} / {len(lstIdCode) * 10} faltando <> {len(lstIdCode) * 10 - len(lstFeatAsset)} ========= ")
    askingbySizeFC = False
else:
    lstFeatAsset = []
print("size of grade geral >> ", len(lstIdCode))
# sys.exit()


inicP = 380 # 0, 158
endP = 761   # 300, 200, 300, 600
for cc, item in enumerate(lstIdCode[inicP: endP]):
    print(f"# {cc + 1 + inicP} loading geometry grade {item}")   
    lst_item_yy = [f"gradeROIs_{item}_{myear}" for myear in range(2016, 2026) if f"gradeROIs_{item}_{myear}" not in lstFeatAsset]
    print(f'para a gride {item} >> we process >> {len(lst_item_yy)}')
    if len(lst_item_yy) > 0:
        objetoMosaic_exportROI.iterate_GradesCaatinga([inicP + cc, item], lst_item_yy)
        # cont = gerenciador(cont)
    # sys.exit()


