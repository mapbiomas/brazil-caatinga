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
import arqParametros as arqParam
import lstIdCodigoBacias as lstIdCodN5
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


class ClassMosaic_indexs_Spectral(object):

    feat_pts_true = ee.FeatureCollection([])
    # default options
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
        'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
        'inputAssetStats': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/stats_mosaics_ba/all_statisticsMosaicC9_',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas50': 'projects/mapbiomas-workspace/public/collection5/mapbiomas_collection50_integration_v1',
        'assetMapbiomas60': 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
        'assetMapbiomas71': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
        'assetMapbiomas80': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_fire': 'projects/ee-geomapeamentoipam/assets/MAPBIOMAS_FOGO/COLECAO_2/Colecao2_fogo_mask_v1',
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

    # featureBands = [
    #     'blue_median','blue_median_wet','blue_median_dry','blue_min','blue_stdDev', 
    #     'green_median','green_median_wet','green_median_dry','green_min','green_stdDev','green_median_texture', 
    #     'red_median','red_median_wet','red_median_dry','red_min', 'red_stdDev', 
    #     'nir_median','nir_median_wet','nir_median_dry','nir_min','nir_stdDev', 
    #     'swir1_median','swir1_median_wet','swir1_median_dry','swir1_min', 'swir1_stdDev', 
    #     'swir2_median', 'swir2_median_wet', 'swir2_median_dry','swir2_min', 'swir2_stdDev',
    #     'slope'
    # ]
    lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self, testando, dictidGrBa):
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
        self.dictidGrBasin = dictidGrBa

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
        
        bandMos = copy.deepcopy(arqParam.featureBands)
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
                                .rename(['ratio_median']).toFloat()

        ratioImgwet = img.expression(f"float(b('nir_median_wet{self.sufN}') / b('red_median_wet{self.sufN}'))")\
                                .rename(['ratio_median_wet']).toFloat()  

        ratioImgdry = img.expression(f"float(b('nir_median_dry{self.sufN}') / b('red_median_dry{self.sufN}'))")\
                                .rename(['ratio_median_dry']).toFloat()        

        return img.addBands(ratioImgY).addBands(ratioImgwet).addBands(ratioImgdry)

    # Ratio Vegetation Index
    def agregateBandsIndexRVI(self, img):
    
        rviImgY = img.expression(f"float(b('red_median{self.sufN}') / b('nir_median{self.sufN}'))")\
                                .rename(['rvi_median']).toFloat() 
        
        rviImgWet = img.expression(f"float(b('red_median_wet{self.sufN}') / b('nir_median_wet{self.sufN}'))")\
                                .rename(['rvi_median_wet']).toFloat() 

        rviImgDry = img.expression(f"float(b('red_median_dry{self.sufN}') / b('nir_median_dry{self.sufN}'))")\
                                .rename(['rvi_median']).toFloat()       

        return img.addBands(rviImgY).addBands(rviImgWet).addBands(rviImgDry)
    
    def agregateBandsIndexNDVI(self, img):
    
        ndviImgY = img.expression(f"float(b('nir_median{self.sufN}') - b('red_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('red_median{self.sufN}'))")\
                                .rename(['ndvi_median']).toFloat()    

        ndviImgWet = img.expression(f"float(b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('red_median_wet{self.sufN}'))")\
                                .rename(['ndvi_median_wet']).toFloat()  

        ndviImgDry = img.expression(f"float(b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('red_median_dry{self.sufN}'))")\
                                .rename(['ndvi_median_dry']).toFloat()     

        return img.addBands(ndviImgY).addBands(ndviImgWet).addBands(ndviImgDry)

    def agregateBandsIndexWater(self, img):
    
        ndwiImgY = img.expression(f"float(b('nir_median{self.sufN}') - b('swir2_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('swir2_median{self.sufN}'))")\
                                .rename(['ndwi_median']).toFloat()       

        ndwiImgWet = img.expression(f"float(b('nir_median_wet{self.sufN}') - b('swir2_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('swir2_median_wet{self.sufN}'))")\
                                .rename(['ndwi_median_wet']).toFloat()   

        ndwiImgDry = img.expression(f"float(b('nir_median_dry{self.sufN}') - b('swir2_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('swir2_median_dry{self.sufN}'))")\
                                .rename(['ndwi_median_dry']).toFloat()   

        return img.addBands(ndwiImgY).addBands(ndwiImgWet).addBands(ndwiImgDry)
    
    def AutomatedWaterExtractionIndex(self, img):    
        aweiY = img.expression(
                            f"float(4 * (b('green_median{self.sufN}') - b('swir2_median{self.sufN}')) - (0.25 * b('nir_median{self.sufN}') + 2.75 * b('swir1_median{self.sufN}')))"
                        ).rename("awei_median").toFloat() 

        aweiWet = img.expression(
                            f"float(4 * (b('green_median_wet{self.sufN}') - b('swir2_median_wet{self.sufN}')) - (0.25 * b('nir_median_wet{self.sufN}') + 2.75 * b('swir1_median_wet{self.sufN}')))"
                        ).rename("awei_median_wet").toFloat() 

        aweiDry = img.expression(
                            f"float(4 * (b('green_median_dry{self.sufN}') - b('swir2_median_dry{self.sufN}')) - (0.25 * b('nir_median_dry{self.sufN}') + 2.75 * b('swir1_median_dry{self.sufN}')))"
                        ).rename("awei_median_dry").toFloat()          
        
        return img.addBands(aweiY).addBands(aweiWet).addBands(aweiDry)
    
    def IndiceIndicadorAgua(self, img):    
        iiaImgY = img.expression(
                            f"float((b('green_median{self.sufN}') - 4 *  b('nir_median{self.sufN}')) / (b('green_median{self.sufN}') + 4 *  b('nir_median{self.sufN}')))"
                        ).rename("iia_median").toFloat()
        
        iiaImgWet = img.expression(
                            f"float((b('green_median_wet{self.sufN}') - 4 *  b('nir_median_wet{self.sufN}')) / (b('green_median_wet{self.sufN}') + 4 *  b('nir_median_wet{self.sufN}')))"
                        ).rename("iia_median_wet").toFloat()

        iiaImgDry = img.expression(
                            f"float((b('green_median_dry{self.sufN}') - 4 *  b('nir_median_dry{self.sufN}')) / (b('green_median_dry{self.sufN}') + 4 *  b('nir_median_dry{self.sufN}')))"
                        ).rename("iia_median_dry").toFloat()
        
        return img.addBands(iiaImgY).addBands(iiaImgWet).addBands(iiaImgDry)
    
    def agregateBandsIndexEVI(self, img):
            
        eviImgY = img.expression(
            f"float(2.4 * (b('nir_median{self.sufN}') - b('red_median{self.sufN}')) / (1 + b('nir_median{self.sufN}') + b('red_median{self.sufN}')))")\
                .rename(['evi_median'])     

        eviImgWet = img.expression(
            f"float(2.4 * (b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}')) / (1 + b('nir_median_wet{self.sufN}') + b('red_median_wet{self.sufN}')))")\
                .rename(['evi_median_wet'])   

        eviImgDry = img.expression(
            f"float(2.4 * (b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}')) / (1 + b('nir_median_dry{self.sufN}') + b('red_median_dry{self.sufN}')))")\
                .rename(['evi_median_dry'])   
        
        return img.addBands(eviImgY).addBands(eviImgWet).addBands(eviImgDry)

    def agregateBandsIndexGVMI(self, img):
        
        gvmiImgY = img.expression(
                        f"float ((b('nir_median{self.sufN}')  + 0.1) - (b('swir1_median{self.sufN}') + 0.02)) / ((b('nir_median{self.sufN}') + 0.1) + (b('swir1_median{self.sufN}') + 0.02))" 
                    ).rename(['gvmi_median']).toFloat()   

        gvmiImgWet = img.expression(
                        f"float ((b('nir_median_wet{self.sufN}')  + 0.1) - (b('swir1_median_wet{self.sufN}') + 0.02)) / ((b('nir_median_wet{self.sufN}') + 0.1) + (b('swir1_median_wet{self.sufN}') + 0.02))" 
                    ).rename(['gvmi_median_wet']).toFloat()

        gvmiImgDry = img.expression(
                        f"float ((b('nir_median_dry{self.sufN}')  + 0.1) - (b('swir1_median_dry{self.sufN}') + 0.02)) / ((b('nir_median_dry{self.sufN}') + 0.1) + (b('swir1_median_dry{self.sufN}') + 0.02))" 
                    ).rename(['gvmi_median_dry']).toFloat()  
    
        return img.addBands(gvmiImgY).addBands(gvmiImgWet).addBands(gvmiImgDry)
    
    def agregateBandsIndexLAI(self, img):
        laiImgY = img.expression(
            f"float(3.618 * (b('evi_median{self.sufN}') - 0.118))")\
                .rename(['lai_median']).toFloat()
    
        return img.addBands(laiImgY)    

    def agregateBandsIndexGCVI(self, img):    
        gcviImgAY = img.expression(
            f"float(b('nir_median{self.sufN}')) / (b('green_median{self.sufN}')) - 1")\
                .rename(['gcvi_median']).toFloat()   

        gcviImgAWet = img.expression(
            f"float(b('nir_median_wet{self.sufN}')) / (b('green_median_wet{self.sufN}')) - 1")\
                .rename(['gcvi_median_wet']).toFloat() 
                
        gcviImgADry = img.expression(
            f"float(b('nir_median_dry{self.sufN}')) / (b('green_median_dry{self.sufN}')) - 1")\
                .rename(['gcvi_median_dry']).toFloat()      
        
        return img.addBands(gcviImgAY).addBands(gcviImgAWet).addBands(gcviImgADry)

    # Global Environment Monitoring Index GEMI 
    def agregateBandsIndexGEMI(self, img):    
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgAY = img.expression(
            f"float((2 * (b('nir_median{self.sufN}') * b('nir_median{self.sufN}') - b('red_median{self.sufN}') * b('red_median{self.sufN}')) + 1.5 * b('nir_median{self.sufN}')" +
            f" + 0.5 * b('red_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('green_median{self.sufN}') + 0.5) )")\
                .rename(['gemi_median']).toFloat()    

        gemiImgAWet = img.expression(
            f"float((2 * (b('nir_median_wet{self.sufN}') * b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}') * b('red_median_wet{self.sufN}')) " +
            f" + 1.5 * b('nir_median_wet{self.sufN}') + 0.5 * b('red_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('green_median_wet{self.sufN}') + 0.5) )")\
                .rename(['gemi_median_wet']).toFloat() 

        gemiImgADry = img.expression(
            f"float((2 * (b('nir_median_dry{self.sufN}') * b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}') * b('red_median_dry{self.sufN}')) + 1.5 * b('nir_median_dry{self.sufN}')" +
            f" + 0.5 * b('red_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('green_median_dry{self.sufN}') + 0.5) )")\
                .rename(['gemi_median_dry']).toFloat()     
        
        return img.addBands(gemiImgAY).addBands(gemiImgAWet).addBands(gemiImgADry)

    # Chlorophyll vegetation index CVI
    def agregateBandsIndexCVI(self, img):    
        cviImgAY = img.expression(
            f"float(b('nir_median{self.sufN}') * (b('green_median{self.sufN}') / (b('blue_median{self.sufN}') * b('blue_median{self.sufN}'))))")\
                .rename(['cvi_median']).toFloat()  

        cviImgAWet = img.expression(
        f"float(b('nir_median_wet{self.sufN}') * (b('green_median_wet{self.sufN}') / (b('blue_median_wet{self.sufN}') * b('blue_median_wet{self.sufN}'))))")\
                .rename(['cvi_median_wet']).toFloat()

        cviImgADry = img.expression(
        f"float(b('nir_median_dry{self.sufN}') * (b('green_median_dry{self.sufN}') / (b('blue_median_dry{self.sufN}') * b('blue_median_dry{self.sufN}'))))")\
                .rename(['cvi_median_dry']).toFloat()      
        
        return img.addBands(cviImgAY).addBands(cviImgAWet).addBands(cviImgADry)

    # Green leaf index  GLI
    def agregateBandsIndexGLI(self,img):    
        gliImgY = img.expression(
        f"float((2 * b('green_median{self.sufN}') - b('red_median{self.sufN}') - b('blue_median{self.sufN}')) / (2 * b('green_median{self.sufN}') - b('red_median{self.sufN}') - b('blue_median{self.sufN}')))")\
                .rename(['gli_median']).toFloat()    

        gliImgWet = img.expression(
        f"float((2 * b('green_median_wet{self.sufN}') - b('red_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')) / (2 * b('green_median_wet{self.sufN}') - b('red_median_wet{self.sufN}') - b('blue_median_wet{self.sufN}')))")\
                .rename(['gli_median_wet']).toFloat()   

        gliImgDry = img.expression(
        f"float((2 * b('green_median_dry{self.sufN}') - b('red_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')) / (2 * b('green_median_dry{self.sufN}') - b('red_median_dry{self.sufN}') - b('blue_median_dry{self.sufN}')))")\
                .rename(['gli_median_dry']).toFloat()       
        
        return img.addBands(gliImgY).addBands(gliImgWet).addBands(gliImgDry)

    # Shape Index  IF 
    def agregateBandsIndexShapeI(self, img):    
        shapeImgAY = img.expression(
        f"float((2 * b('red_median{self.sufN}') - b('green_median{self.sufN}') - b('blue_median{self.sufN}')) / (b('green_median{self.sufN}') - b('blue_median{self.sufN}')))")\
                .rename(['shape_median']).toFloat()  

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
                .rename(['afvi_median']).toFloat()  

        afviImgAWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}') - 0.5 * b('swir2_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + 0.5 * b('swir2_median_wet{self.sufN}')))")\
                .rename(['afvi_median_wet']).toFloat()

        afviImgADry = img.expression(
        f"float((b('nir_median_dry{self.sufN}') - 0.5 * b('swir2_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + 0.5 * b('swir2_median_dry{self.sufN}')))")\
                .rename(['afvi_median_dry']).toFloat()      
        
        return img.addBands(afviImgAY).addBands(afviImgAWet).addBands(afviImgADry)

    # Advanced Vegetation Index 
    def agregateBandsIndexAVI(self, img):    
        aviImgAY = img.expression(
        f"float((b('nir_median{self.sufN}')* (1.0 - b('red_median{self.sufN}')) * (b('nir_median{self.sufN}') - b('red_median{self.sufN}'))) ** 1/3)")\
                .rename(['avi_median']).toFloat()   

        aviImgAWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}')* (1.0 - b('red_median_wet{self.sufN}')) * (b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}'))) ** 1/3)")\
                .rename(['avi_median_wet']).toFloat()

        aviImgADry = img.expression(
        f"float((b('nir_median_dry{self.sufN}')* (1.0 - b('red_median_dry{self.sufN}')) * (b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}'))) ** 1/3)")\
                .rename(['avi_median_dry']).toFloat()     
        
        return img.addBands(aviImgAY).addBands(aviImgAWet).addBands(aviImgADry)

    # Bare Soil Index 
    def agregateBandsIndexBSI(self,img):    
        bsiImgY = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('red_median{self.sufN}')) - (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))) / " + 
                f"((b('swir1_median{self.sufN}') + b('red_median{self.sufN}')) + (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))))")\
                .rename(['bsi_median']).toFloat()  

        bsiImgWet = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('red_median{self.sufN}')) - (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))) / " + 
                f"((b('swir1_median{self.sufN}') + b('red_median{self.sufN}')) + (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))))")\
                .rename(['bsi_median']).toFloat()

        bsiImgDry = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('red_median{self.sufN}')) - (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))) / " + 
                f"((b('swir1_median{self.sufN}') + b('red_median{self.sufN}')) + (b('nir_median{self.sufN}') + b('blue_median{self.sufN}'))))")\
                .rename(['bsi_median']).toFloat()      
        
        return img.addBands(bsiImgY).addBands(bsiImgWet).addBands(bsiImgDry)

    # BRBA	Band Ratio for Built-up Area  
    def agregateBandsIndexBRBA(self,img):    
        brbaImgY = img.expression(
        f"float(b('red_median{self.sufN}') / b('swir1_median{self.sufN}'))")\
                .rename(['brba_median']).toFloat()   

        brbaImgWet = img.expression(
        f"float(b('red_median_wet{self.sufN}') / b('swir1_median_wet{self.sufN}'))")\
                .rename(['brba_median_wet']).toFloat()

        brbaImgDry = img.expression(
        f"float(b('red_median_dry{self.sufN}') / b('swir1_median_dry{self.sufN}'))")\
                .rename(['brba_median_dry']).toFloat()     
        
        return img.addBands(brbaImgY).addBands(brbaImgWet).addBands(brbaImgDry)

    # DSWI5	Disease-Water Stress Index 5
    def agregateBandsIndexDSWI5(self,img):    
        dswi5ImgY = img.expression(
        f"float((b('nir_median{self.sufN}') + b('green_median{self.sufN}')) / (b('swir1_median{self.sufN}') + b('red_median{self.sufN}')))")\
                .rename(['dswi5_median']).toFloat() 

        dswi5ImgWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}') + b('green_median_wet{self.sufN}')) / (b('swir1_median_wet{self.sufN}') + b('red_median_wet{self.sufN}')))")\
                .rename(['dswi5_median_wet']).toFloat() 

        dswi5ImgDry = img.expression(
        f"float((b('nir_median_dry{self.sufN}') + b('green_median_dry{self.sufN}')) / (b('swir1_median_dry{self.sufN}') + b('red_median_dry{self.sufN}')))")\
                .rename(['dswi5_median_dry']).toFloat() 

        return img.addBands(dswi5ImgY).addBands(dswi5ImgWet).addBands(dswi5ImgDry)

    # LSWI	Land Surface Water Index
    def agregateBandsIndexLSWI(self,img):    
        lswiImgY = img.expression(
        f"float((b('nir_median{self.sufN}') - b('swir1_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('swir1_median{self.sufN}')))")\
                .rename(['lswi_median']).toFloat()  

        lswiImgWet = img.expression(
        f"float((b('nir_median_wet{self.sufN}') - b('swir1_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('swir1_median_wet{self.sufN}')))")\
                .rename(['lswi_median_wet']).toFloat()

        lswiImgDry = img.expression(
        f"float((b('nir_median_dry{self.sufN}') - b('swir1_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('swir1_median_dry{self.sufN}')))")\
                .rename(['lswi_median_dry']).toFloat()      
        
        return img.addBands(lswiImgY).addBands(lswiImgWet).addBands(lswiImgDry)

    # MBI	Modified Bare Soil Index
    def agregateBandsIndexMBI(self,img):    
        mbiImgY = img.expression(
        f"float(((b('swir1_median{self.sufN}') - b('swir2_median{self.sufN}') - b('nir_median{self.sufN}')) /" + 
                f" (b('swir1_median{self.sufN}') + b('swir2_median{self.sufN}') + b('nir_median{self.sufN}'))) + 0.5)")\
                    .rename(['mbi_median']).toFloat() 

        mbiImgWet = img.expression(
        f"float(((b('swir1_median_wet{self.sufN}') - b('swir2_median_wet{self.sufN}') - b('nir_median_wet{self.sufN}')) /" + 
                f" (b('swir1_median_wet{self.sufN}') + b('swir2_median_wet{self.sufN}') + b('nir_median_wet{self.sufN}'))) + 0.5)")\
                    .rename(['mbi_median_wet']).toFloat() 

        mbiImgDry = img.expression(
        f"float(((b('swir1_median_dry{self.sufN}') - b('swir2_median_dry{self.sufN}') - b('nir_median_dry{self.sufN}')) /" + 
                f" (b('swir1_median_dry{self.sufN}') + b('swir2_median_dry{self.sufN}') + b('nir_median_dry{self.sufN}'))) + 0.5)")\
                    .rename(['mbi_median_dry']).toFloat()       
        
        return img.addBands(mbiImgY).addBands(mbiImgWet).addBands(mbiImgDry)

    # UI	Urban Index	urban
    def agregateBandsIndexUI(self,img):    
        uiImgY = img.expression(
        f"float((b('swir2_median{self.sufN}') - b('nir_median{self.sufN}')) / (b('swir2_median{self.sufN}') + b('nir_median{self.sufN}')))")\
                .rename(['ui_median']).toFloat()  

        uiImgWet = img.expression(
        f"float((b('swir2_median_wet{self.sufN}') - b('nir_median_wet{self.sufN}')) / (b('swir2_median_wet{self.sufN}') + b('nir_median_wet{self.sufN}')))")\
                .rename(['ui_median_wet']).toFloat() 

        uiImgDry = img.expression(
        f"float((b('swir2_median_dry{self.sufN}') - b('nir_median_dry{self.sufN}')) / (b('swir2_median_dry{self.sufN}') + b('nir_median_dry{self.sufN}')))")\
                .rename(['ui_median_dry']).toFloat()       
        
        return img.addBands(uiImgY).addBands(uiImgWet).addBands(uiImgDry)

    # OSAVI	Optimized Soil-Adjusted Vegetation Index
    def agregateBandsIndexOSAVI(self,img):    
        osaviImgY = img.expression(
        f"float(b('nir_median{self.sufN}') - b('red_median{self.sufN}')) / (0.16 + b('nir_median{self.sufN}') + b('red_median{self.sufN}'))")\
                .rename(['osavi_median']).toFloat() 

        osaviImgWet = img.expression(
        f"float(b('nir_median_wet{self.sufN}') - b('red_median_wet{self.sufN}')) / (0.16 + b('nir_median_wet{self.sufN}') + b('red_median_wet{self.sufN}'))")\
                .rename(['osavi_median_wet']).toFloat() 

        osaviImgDry = img.expression(
        f"float(b('nir_median_dry{self.sufN}') - b('red_median_dry{self.sufN}')) / (0.16 + b('nir_median_dry{self.sufN}') + b('red_median_dry{self.sufN}'))")\
                .rename(['osavi_median_dry']).toFloat()        
        
        return img.addBands(osaviImgY).addBands(osaviImgWet).addBands(osaviImgDry)

    # Normalized Difference Red/Green Redness Index  RI
    def agregateBandsIndexRI(self, img):        
        riImgY = img.expression(
        f"float(b('nir_median{self.sufN}') - b('green_median{self.sufN}')) / (b('nir_median{self.sufN}') + b('green_median{self.sufN}'))")\
                .rename(['ri_median']).toFloat()   

        riImgWet = img.expression(
        f"float(b('nir_median_wet{self.sufN}') - b('green_median_wet{self.sufN}')) / (b('nir_median_wet{self.sufN}') + b('green_median_wet{self.sufN}'))")\
                .rename(['ri_median_wet']).toFloat()

        riImgDry = img.expression(
        f"float(b('nir_median_dry{self.sufN}') - b('green_median_dry{self.sufN}')) / (b('nir_median_dry{self.sufN}') + b('green_median_dry{self.sufN}'))")\
                .rename(['ri_median_dry']).toFloat()    
        
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
                .rename(['msi_median']).toFloat() 
        
        msiImgWet = img.expression(
        f"float( b('nir_median_wet{self.sufN}') / b('swir1_median_wet{self.sufN}'))")\
                .rename(['msi_median_wet']).toFloat() 

        msiImgDry = img.expression(
        f"float( b('nir_median_dry{self.sufN}') / b('swir1_median_dry{self.sufN}'))")\
                .rename(['msi_median_dry']).toFloat() 
        
        return img.addBands(msiImgY).addBands(msiImgWet).addBands(msiImgDry)


    def agregateBandsIndexGVMI(self, img):        
        gvmiImgY = img.expression(
                    f"float ((b('nir_median{self.sufN}')  + 0.1) - (b('swir1_median{self.sufN}') + 0.02)) " + 
                            f"/ ((b('nir_median{self.sufN}') + 0.1) + (b('swir1_median{self.sufN}') + 0.02))" 
                        ).rename(['gvmi_median']).toFloat()  

        gvmiImgWet = img.expression(
                    f"float ((b('nir_median_wet{self.sufN}')  + 0.1) - (b('swir1_median_wet{self.sufN}') + 0.02)) " + 
                            f"/ ((b('nir_median_wet{self.sufN}') + 0.1) + (b('swir1_median_wet{self.sufN}') + 0.02))" 
                        ).rename(['gvmi_median_wet']).toFloat()

        gvmiImgDry = img.expression(
                    f"float ((b('nir_median_dry{self.sufN}')  + 0.1) - (b('swir1_median_dry{self.sufN}') + 0.02)) " + 
                            f"/ ((b('nir_median_dry{self.sufN}') + 0.1) + (b('swir1_median_dry{self.sufN}') + 0.02))" 
                        ).rename(['gvmi_median_dry']).toFloat()   
    
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

    #endregion

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

    def CalculateIndice(self, imagem):

        band_feat = [
                "ratio","rvi","ndwi","awei","iia","evi",
                "gcvi","gemi","cvi","gli","shape","afvi",
                "avi","bsi","brba","dswi5","lswi","mbi","ui",
                "osavi","ri","brightness","wetness","gvmi",
                "nir_contrast","red_contrast"
            ]   

        # agregateBandsIndexMSI, agregateBandsIndexGVMI
        # agregateBandsIndexCO2Flux      faltam

        imageW = self.agregateBandsIndexEVI(imagem)
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
        imageW = self.agregateBandsIndexOSAVI(imageW)  #     
        imageW = self.agregateBandsIndexwetness(imageW)   #   
        imageW = self.agregateBandsIndexBrightness(imageW)  #       
        imageW = self.agregateBandsTexturasGLCM(imageW)     #

        return imageW#.select(band_feat)# .addBands(imageF)


    def calculate_indices_x_blocos(self, image):
        
        # band_year = [bnd + '_median' for bnd in self.option['bnd_L']]
        band_year = ['blue_medianN','green_medianN','red_medianN','nir_medianN','swir1_medianN','swir2_medianN']
        band_drys = [bnd + '_median_dry' for bnd in self.options['bnd_L']]    
        band_wets = [bnd + '_median_wet' for bnd in self.options['bnd_L']]
        band_std = [bnd + '_stdDev'for bnd in self.options['bnd_L']]
        band_features = [
                    "ratio","rvi","ndwi","awei","iia",
                    "gcvi","gemi","cvi","gli","shape","afvi",
                    "avi","bsi","brba","dswi5","lswi","mbi","ui",
                    "osavi","ri","brightness","wetness",
                    "nir_contrast","red_contrast"] # ,"ndfia"
        # band_features.extend(self.option['bnd_L'])        
        
        image_year = image.select(band_year)
        image_year = image_year.select(band_year, self.options['bnd_L'])
        # print("imagem bandas index ")    
        # print("  ", image_year.bandNames().getInfo())
        image_year = self.CalculateIndice(image_year)    
        # print("imagem bandas index ")    
        # print("  ", image_year.bandNames().getInfo())
        bnd_corregida = [bnd + '_median' for bnd in band_features]
        image_year = image_year.select(band_features, bnd_corregida)
        # print("imagem bandas final median \n ", image_year.bandNames().getInfo())

        image_drys = image.select(band_drys)
        image_drys = image_drys.select(band_drys, self.options['bnd_L'])
        image_drys = self.CalculateIndice(image_drys)
        bnd_corregida = [bnd + '_median_dry' for bnd in band_features]
        image_drys = image_drys.select(band_features, bnd_corregida)
        # print("imagem bandas final dry \n", image_drys.bandNames().getInfo())

        image_wets = image.select(band_wets)
        image_wets = image_wets.select(band_wets, self.options['bnd_L'])
        image_wets = self.CalculateIndice(image_wets)
        bnd_corregida = [bnd + '_median_wet' for bnd in band_features]
        image_wets = image_wets.select(band_features, bnd_corregida)
        # print("imagem bandas final wet \n ", image_wets.bandNames().getInfo())

        # image_std = image.select(band_std)
        # image_std = self.match_Images(image_std)
        # image_std = self.CalculateIndice(image_std)
        # bnd_corregida = ['stdDev_' + bnd for bnd in band_features]
        # image_std = image_std.select(band_features, bnd_corregida)        

        image_year =  image_year.addBands(image_drys).addBands(image_wets)#.addBands(image_std)
        return image_year

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


    # https://code.earthengine.google.com/6127586297423a622e139858312aa448   testando coincidencia com a primeira celda da grade 
    def iterate_GradesCaatinga(self, paridCodVBacN5):
        idCount = paridCodVBacN5[0]
        idCod = paridCodVBacN5[1]
        ic(f" # {idCount} =============  processing ID => {idCod}")
        nomeBacia = self.dictidGrBasin[str(idCod)]
        print(f"----- loading the basin {nomeBacia} from asset inputAssetStats--------------")
        self.featCStat = ee.FeatureCollection(self.options['inputAssetStats'] + nomeBacia)        
        gradeKM = ee.FeatureCollection(self.options['asset_shpGrade']).filter(
                                                ee.Filter.eq('id', idCod)).geometry()

        if self.testando:
            ic("show geometry() ", gradeKM.getInfo())

        imgColMosaic = ee.ImageCollection(self.options['asset_mosaic_mapbiomas']
                                                    ).filter(ee.Filter.inList('biome', self.options['biomas'])
                                                        ).filterBounds(gradeKM).select(arqParam.featureBands)        
        print(f" we loaded {imgColMosaic.size().getInfo()} images ")
        
        

        # @collection80: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection80 = ee.Image(self.options['assetMapbiomas80'])
        # print(collection80.bandNames().getInfo())
        
        # print(baciaN5.getInfo())
        imMasCoinc = None
        maksEstaveis = None
        areaColeta = None
        # sys.exit()
        featCol= ee.FeatureCollection([])
        for anoCount in self.lst_year[:]:                
            bandActiva = 'classification_' + str(anoCount)
            
            if anoCount < 2023:
                # Loaded camadas de pixeles estaveis
                m_assetPixEst = self.options['asset_estaveis'] + '/masks_estatic_pixels_' + str(anoCount)
                maksEstaveis = ee.Image(m_assetPixEst).rename('estatic')  
                # print("mascara maksEstaveis ", maksEstaveis.bandNames().getInfo())

                # mask de fogo com os ultimos 5 anos de fogo mapeado 
                # imMaskFire = self.get_mask_Fire_estatics_pixels(anoCount, False)
                imMaskFire = self.get_class_maskFire(anoCount,gradeKM)
                imMaskFire = ee.Image(imMaskFire)
                # print("mascara imMaskFire ", imMaskFire.bandNames().getInfo())
                # loaded banda da coleção 
                map_yearAct = collection80.select(bandActiva).rename(['class'])

                # 1 Concordante, 2 concordante recente, 3 discordante recente,
                # 4 discordante, 5 muito discordante
                if anoCount < 2022:
                    asset_PixCoinc = self.options['asset_Coincidencia'] + '/masks_pixels_incidentes_'+ str(anoCount)                     
                else:
                    asset_PixCoinc = self.options['asset_Coincidencia'] + '/masks_pixels_incidentes_2021'
                
                imMasCoinc = ee.Image(asset_PixCoinc).rename('coincident')
                # print("mascara coincidentes ", imMasCoinc.bandNames().getInfo())

                if anoCount > 1985:
                    imMaksAlert = self.get_class_maskAlerts(anoCount)

                elif anoCount >= 2020:
                    imMaksAlert = self.AlertasSAD  
                else:
                    imMaksAlert = ee.Image.constant(1).rename('mask_alerta')   
                
                # print("mascara imMaksAlert ", imMaksAlert.bandNames().getInfo())
                areaColeta = maksEstaveis.multiply(imMaskFire).multiply(imMaksAlert) \
                                .multiply(imMasCoinc.lt(3))
                areaColeta = areaColeta.eq(1) # mask of the area for colects
            
            map_yearAct = map_yearAct.addBands(
                                    ee.Image.constant(int(anoCount)).rename('year')).addBands(
                                        imMasCoinc)           
            # filtered year anoCount
            print(f"**** filtered by year {anoCount}")
            img_recMosaic = imgColMosaic.filter(ee.Filter.eq('year', anoCount))
            img_recMosaic = img_recMosaic.map(lambda img: self.process_normalized_img(img))
            
            if self.testando:
                print(" ⚠️  quantity of images ", img_recMosaic.size().getInfo()) 
                print(" list of bands selected ", arqParam.featureBands)
                print(" show the bands of the first image ", img_recMosaic.first().bandNames().getInfo()) 
                # print("metadato ", img_recMosaic.first().getInfo())
            
            img_recMosaic = img_recMosaic.median() 
            
            if self.testando:
                print("img_recMosaic   ", img_recMosaic.bandNames().getInfo())            
            img_recMosaicnewB = self.CalculateIndice(img_recMosaic)
            
            if self.testando:
                bndAdd = img_recMosaicnewB.bandNames().getInfo()                    
                print(f"know bands names {len(bndAdd)}")
                step = 5
                for cc in range(0, len(bndAdd), step):
                    print("  ", bndAdd[cc: cc + step])

            img_recMosaic = img_recMosaic.addBands(ee.Image(img_recMosaicnewB)).addBands(map_yearAct)
            img_recMosaic = img_recMosaic.updateMask(areaColeta)
            

            # sampleRegions()
            ptosTemp = img_recMosaic.sample(
                                region=  gradeKM,                              
                                scale= 30,   
                                numPixels= 10000,
                                dropNulls= True,
                                # tileScale= 2,                             
                                geometries= True
                            )
            ptosTemp = ptosTemp.filter(ee.Filter.notNull(arqParam.featureBands))
            # featCol = featCol.merge(ptosTemp)

            nomeBaciaEx = "gradeROIs_" + str(idCod) + "_" + str(anoCount) + "_wl" 
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

        # @collection80: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection80 = ee.Image(self.options['assetMapbiomas80'])
        if self.testando:
            print(collection80.bandNames().getInfo())
        
        imMasCoinc = None
        maksEstaveis = None
        areaColeta = None
        # sys.exit()
            
                    
        if anoCount > 2022:
            bandActiva = 'classification_2022'
            # Loaded camadas de pixeles estaveis
            m_assetPixEst = self.options['asset_estaveis'] + '/masks_estatic_pixels_' + str(2022)
            # mask de fogo com os ultimos 5 anos de fogo mapeado 
            # imMaskFire = self.get_mask_Fire_estatics_pixels(2022, False)
            imMaskFire = self.get_class_maskFire(anoCount,gradeKM)
            # loaded banda da coleção 
            map_yearAct = collection80.select('classification_2022').rename(['class'])                  
            
        else:
            bandActiva = 'classification_' + str(anoCount)
            # Loaded camadas de pixeles estaveis
            m_assetPixEst = self.options['asset_estaveis'] + '/masks_estatic_pixels_' + str(anoCount)                
            # mask de fogo com os ultimos 5 anos de fogo mapeado 
            # imMaskFire = self.get_mask_Fire_estatics_pixels(anoCount, False)
            imMaskFire = self.get_class_maskFire(anoCount, gradeKM)
            # loaded banda da coleção 
            map_yearAct = collection80.select(bandActiva).rename(['class'])
        
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


print("len arqParam ", len(arqParam.featuresreduce))

param = {
    'bioma': ["CAATINGA", 'CERRADO', 'MATAATLANTICA'],
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/',
    # 'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/PtosXBaciasBalanceados/',
    'asset_ROIs_manual': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv7N2manual'},
    'asset_ROIs_cluster': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster'},
    'asset_ROIs_automatic': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsGradeallBNDNormal'},
    'asset_shpGrade': 'projects/mapbiomas-arida/ALERTAS/auxiliar/basegrade30KMCaatinga',
    'showAssetFeat': False,
    'janela': 5,
    'escala': 30,
    'sampleSize': 0,
    'metodotortora': True,
    'tamROIsxClass': 4000,
    'minROIs': 1500,
    # "anoColeta": 2015,
    'anoInicial': 1985,
    'anoFinal': 2023,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 4,
    'conta': {
        # '0': 'caatinga01',
        # '1': 'caatinga02',
        '0': 'caatinga03',
        '1': 'caatinga04',
        '2': 'caatinga05',
        '3': 'solkan1201',
        # '6': 'solkanGeodatin',
        # '20': 'solkanGeodatin'
    },
}
def gerenciador(cont, param):

    numberofChange = [kk for kk in param['conta'].keys()]
    
    if str(cont) in numberofChange:

        gee.switch_user(param['conta'][str(cont)])
        gee.init()
        gee.tasks(n=param['numeroTask'], return_list=True)
        cont += 1

    elif cont > param['numeroLimit']:
        cont = 0

    else:
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
    listTarge = []
    lstOut = []    
    pathroot = None
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


# listaNameBacias = ['765','766','759','7619','7422']

changeCount = False
cont = 0
if changeCount:
    cont = gerenciador(cont, param)
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
    mpath_bndImp = pathparent + '/dados/regJSON/'
    print("path of CSVs Rois is \n ==>",  mpath_bndImp)
    return mpath_bndImp

pathBase = getPathCSV()
pathjsonBaGr = pathBase + "dict_convert_bacia_N2_toGrade.json"
with open(pathjsonBaGr, 'r') as fp:
    dictidGrBasin = json.loads(fp.read())
ic(" -- Loading dict_convert_bacia_N2_toGrade.json and convert to dict 💭 -- ")

setTeste = False
show_IdReg = False
colectSaved = True
getLstIds = False
# path('update/<int:pk>/', update, name= 'url_update'),
if getLstIds:
    gradeCaat = ee.FeatureCollection(param['asset_shpGrade']) 
    lstIds = gradeCaat.reduceColumns(ee.Reducer.toList(), ['id']).get('list').getInfo()
    nlksIDs = [kk for kk in lstIds]
    nlksIDs.sort()
else:
    nlksIDs = lstIdCodN5.lstIdsGradeCaat

numberGradeYearsAll = len(nlksIDs) * 37
print(f"lista de Ids com {len(nlksIDs)} grades no total {numberGradeYearsAll}")

# nlksIDs = [ ]

if colectSaved:
    lstAssetFolder = GetPolygonsfromFolder(param['asset_ROIs_automatic'])
    print(f"lista de Features ROIs Grades saved {len(lstAssetFolder)}   ")       
    newlstIdGrades = [kk.split("/")[-1] for kk in lstAssetFolder]
    print("show the first 5 : \n", newlstIdGrades[:5])
    # get the basin saved
    print(f"we have {len(newlstIdGrades)} asset to search in what year is missing some ROIs from of  {numberGradeYearsAll} possivel")
    sys.exit()
    lstGradeMissing =  getlistofRegionYeartoProcessing(newlstIdGrades, nlksIDs)
    print(f"we have {len(lstGradeMissing)} asset that are missing")
    lstProcpool = [(cc, kk) for cc, kk in enumerate(lstGradeMissing[:])]    

else:
    lstProcpool = [(cc, kk) for cc, kk in enumerate(nlksIDs[:])]

print("size of list to processe ", len(lstProcpool))
# sys.exit()
lstKeysFolder = 'asset_shpGrade'  # , , 'asset_ROIs_manual', 'asset_ROIs_cluster'
objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(setTeste, dictidGrBasin)
print("============= Get parts of the list ===============")
# lstProcpool = [(0, 1420)]
# print(lstProcpool[0])
# objetoMosaic_exportROI.iterate_bacias(lstProcpool[0])
if setTeste:
    if colectSaved:
        print("testando o primero dado ")
        objetoMosaic_exportROI.iterate_idAsset_missing(lstProcpool[0])
    else:
        objetoMosaic_exportROI.iterate_GradesCaatinga(lstProcpool[0])
else:
    print("Não fazer teste")
    step = 60
    for ll in range(0, len(lstProcpool[39070:]), step):
        lstProcpoolss = lstProcpool[ll: ll + step]
        if ll > -1:
            with ThreadPool() as pool:
                # issue one task for each call to the function
                print(f"enviando para processamento entre a posição {ll} e {ll + step}")
                if colectSaved:
                    for result in pool.map(objetoMosaic_exportROI.iterate_idAsset_missing, lstProcpoolss):
                        # handle the result
                        print(f'>got {result}')
                else:
                    for result in pool.map(objetoMosaic_exportROI.iterate_GradesCaatinga, lstProcpoolss):
                        # handle the result
                        print(f'>got {result}')

            # break
            cont = gerenciador(cont, param)

