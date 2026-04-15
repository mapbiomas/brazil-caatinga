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


class Classify_Mosaic_process(object):

    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
        'asset_mosaic_sentinel': 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample', 
        'asset_region_images': 'projects/ee-solkancengine17/assets/caat_49_regions_bacias',
        'asset_region_img_buffer': 'projects/ee-solkancengine17/assets/bacias_buf_raster_Caatinga49',
        # 'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX',
        'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVY',
        'asset_rois': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2',
        'asset_rois_red': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2red',
        'path_csvs_areas':  '/home/superuser/Dados/mapbiomas/dev_collection_sentinel/src/dados/areaBacia',
        'path_csvs_featSelect': '/home/superuser/Dados/mapbiomas/dev_collection_sentinel/src/dados/featuresSet',
        'lsClasse': [4, 3, 12, 15, 18, 21, 25, 33],
        'lsPtos': [3000, 5000, 3000, 3500, 1500, 1000, 1500, 3000],
        "anoInicial": 2016,
        "anoIntFin": 2023,
        'version': '2',
        'bioma': 'Caatinga',
        'pmtRF': {
            'numberOfTrees': 165, 
            'variablesPerSplit': 15,
            'minLeafPopulation': 40,
            'bagFraction': 0.8,
            'seed': 0
        },
        # https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting
        'pmtGTB': {
            'numberOfTrees': 25, 
            'shrinkage': 0.1,         
            'samplingRate': 0.8, 
            'loss': "LeastSquares",#'Huber',#'LeastAbsoluteDeviation', 
            'seed': 0
        },
        'pmtSVM' : {
            'decisionProcedure' : 'Margin', 
            'kernelType' : 'RBF', 
            'shrinking' : True, 
            'gamma' : 0.001
        },
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
    lstFeaturesSel = []

    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self, saveROIsBalance):

        self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])#.geometry()
        self.year_activo =  2016
        name_dict = 'dict_stat_nyearRegComp.json'
        self.dict_Statgeral = {}

        # Using json.load()
        with open(name_dict) as dictJson:
            self.dict_Statgeral = json.load(dictJson)

        raster_bacias = ee.ImageCollection(self.options['asset_region_img_buffer']).mosaic().gt(0);
        # self.nlstAssetsROIs = nlstAssetsROIs                                
        # print("  ", self.imgMosaic.size().getInfo())
        print("see band Names the first ")
        # print(" ==== ", ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        # print("all images ", self.imgMosaic.size().getInfo())
        # print("show metadata from first images ", self.imgMosaic.first().getInfo())
        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoInicial'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        self.options['lsBandasMap'] = ['classification_' + str(kk) for kk in range(self.options['anoInicial'], self.options['anoIntFin'] + 1)]
        # @collection90: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection90 = ee.Image(self.options['assetMapbiomas90'])

        # # Remap todas as imagens mapbiomas        
        band_year = ['blue_median','green_median','red_median','nir_median','swir1_median','swir2_median']
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        self.bandSentinel = band_year + band_wets + band_drys
        print("bandas principais \n ==> ", self.bandSentinel)


    def process_re_escalar_img (self, imgA):
        imgMosaic = imgA.select('blue_median').gte(0).rename('constant');
        dictStatYY = self.dict_Statgeral[self.year_activo]
        for cc, bnd in enumerate(self.featureBands):
            bndMed = bnd + '_mean';
            bndStd = bnd + '_stdDev'
            imgBand = imgA.select(bnd)
            # calcZ = (arrX - xmean) / xstd;
            calcZ = imgBand.subtract(ee.Image.constant(dictStatYY[bndMed])
                                        ).divide(ee.Image.constant(dictStatYY[bndStd]));
            
            #  expBandAft =  np.exp(-1 * calcZ)
            expBandAft = calcZ.multiply(ee.Image.constant(-1)).exp();

            #   return 1 / (1 + expBandAft)
            bndend = expBandAft.add(ee.Image.constant(1)).pow(ee.Image.constant(-1));                            

            if cc == 0:
                imgNormal = bndend.rename(bnd)
            else:
                imgNormal = imgNormal.addBands(bndend.rename(bnd))
        imgNormal = imgNormal.select(self.featureBands).toFloat();
        
        return imgMosaic.addBands(imgNormal).select(self.featureBands).set('year', imgA.get('year'))


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
    
        return img.addBands(laiImgY)    

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


    def agregateBandsIndexGVMI(self, img):        
        gvmiImgY = img.expression(
                        "float ((b('nir_median')  + 0.1) - (b('swir1_median') + 0.02)) " + 
                            "/ ((b('nir_median') + 0.1) + (b('swir1_median') + 0.02))" 
                        ).rename(['gvmi_median']).toFloat()  

        gvmiImgWet = img.expression(
                        "float ((b('nir_median_wet')  + 0.1) - (b('swir1_median_wet') + 0.02)) " + 
                            "/ ((b('nir_median_wet') + 0.1) + (b('swir1_median_wet') + 0.02))" 
                        ).rename(['gvmi_median_wet']).toFloat()

        gvmiImgDry = img.expression(
                        "float ((b('nir_median_dry')  + 0.1) - (b('swir1_median_dry') + 0.02)) " + 
                            "/ ((b('nir_median_dry') + 0.1) + (b('swir1_median_dry') + 0.02))" 
                        ).rename(['gvmi_median_dry']).toFloat()   
    
        return img.addBands(gvmiImgY).addBands(gvmiImgWet).addBands(gvmiImgDry) 


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
                            ).rename(['pri_median'])   
        spriImgDry =   priImgDry.expression(
                                "float((b('pri_median') + 1) / 2)").rename(['spri_median']).toFloat()
    
        return img.addBands(spriImgY).addBands(spriImgWet).addBands(spriImgDry)
    

    def agregateBandsIndexCO2Flux(self, img):        
        ndviImg = img.expression(
                            "float(b('nir_median') - b('swir2_median')) / (b('nir_median') + b('swir2_median'))"
                        ).rename(['ndvi']).toFloat() 
        
        priImg = img.expression(
                            "float((b('green_median') - b('blue_median')) / (b('green_median') + b('blue_median')))"
                        ).rename(['pri_median']).toFloat()   
        spriImg =   priImg.expression(
                                "float((b('pri_median') + 1) / 2)").rename(['spri_median']).toFloat()

        co2FluxImg = ndviImg.multiply(spriImg).rename(['co2flux_median'])   
        
        return img.addBands(co2FluxImg)


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

    
    #endregion


    def CalculateIndice(self, imagem):

        band_feat = [
                "ratio","rvi","ndwi","awei","iia","evi",
                "gcvi","gemi","cvi","gli","shape","afvi",
                "avi","bsi","brba","dswi5","lswi","mbi","ui",
                "osavi","ri","brightness","wetness","gvmi",
                "nir_contrast","red_contrast", 'nddi',"ndvi"
            ]        

        imageW = self.agregateBandsIndexEVI(imagem)
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
        imageW = self.agregateBandsIndexwetness(imageW)   #   
        imageW = self.agregateBandsIndexBrightness(imageW)  #  
        imageW = self.agregateBandsIndexGVMI(imageW)     
        imageW = self.agregateBandsTexturasGLCM(imageW)     #

        return imageW  #.select(band_feat)# .addBands(imageF)

    def balancear_samples(self, featROIs, myear, mbasin):

        numMaxRois = 10000
        # reducing the class of most quantities
        firstCC = 0
        roisDictCC = featROIs.aggregate_histogram('class').getInfo()
        lstValues = list(roisDictCC.values())
        lstValues.sort()
        print("lstValues => ", lstValues)
        lista_classes = list(roisDictCC.keys())
        valueSeg = lstValues[-2]
        for CC in lista_classes:
            if valueSeg < roisDictCC[str(CC)]:
                firstCC = int(CC)
        print(f"-- A classe com maior número de amostras é == << {firstCC} >> ---")
        print(f" --- quantidade do segundo com mais amostras == {valueSeg} ==")
        # https://code.earthengine.google.com/b5c169b1c748fa767b3c09412d6458fd
        featCCM = featROIs.filter(ee.Filter.eq('class', firstCC)).randomColumn('random')
        totalCCM = featCCM.size().getInfo()
        # print("totalCCM = ", totalCCM)
        featCCM = featCCM.filter(ee.Filter.lt('random', float(valueSeg/totalCCM)))
        featROIsRest = featROIs.filter(ee.Filter.neq('class', firstCC))
        featROIsRest = featROIsRest.merge(featCCM)
        # print(featROIsRest.aggregate_histogram('class').getInfo())

        # Load table  class areas distribuition
        nameCSV = f"/areaXclasse_CAAT_Col90_integration_v1_{mbasin}_remap.csv"
        tableAreas = pd.read_csv(self.options['path_csvs_areas'] + nameCSV)
        tableAreasYY = tableAreas[tableAreas['year'] == myear]
        area_total = tableAreasYY['area'].sum()
        tableAreasYY['percent'] =  tableAreasYY['area'].apply(lambda x: round(x/area_total, 2)) 
        # tableAreasYY['percent'] = tableAreasYY['percent'].round(2)
        # print(tableAreasYY.head(3))
        tableAreasYY['classe'] = tableAreasYY['classe'].astype(int)

        dictQuantPercent = {}
        for CC in lista_classes:
            CCc = CC
            if CC in ['15', '18']:
                CCc = '21' 
            # print(f' classe {CCc} tabela  ', tableAreasYY[tableAreasYY['classe'] == int(CCc)]['percent'])
            percentual = tableAreasYY[tableAreasYY['classe'] == int(CCc)]['percent'].iloc[0]
            if percentual == 0.0:
                percentual = 0.1
            percentQ = numMaxRois * percentual
            # print(f" classe {CC} >>  {percentual} de 30000 =>> {int(percentQ)}")
            dictQuantPercent[str(CC)] = int(percentQ)
        
        # balancing samples
        roiEnd = ee.FeatureCollection([])
        for CC in lista_classes:            
            featbyCC = featROIsRest.filter(ee.Filter.eq('class', int(CC))).randomColumn('random')
            totalCCM = featbyCC.size().getInfo()
            # print(f" classe {CC} : total filtrada {totalCCM}")
            ## Cuanto representa a quantidade X do total referente a porcentagem dos 30000
            percentRandom = float(dictQuantPercent[str(CC)] / int(totalCCM))
            # print(f" quantidade Classe {dictQuantPercent[str(CC)]}  percent in random = {percentRandom} ")
            featbyCC = featbyCC.filter(ee.Filter.lt('random', percentRandom))
            # print("juntando ", featbyCC.size().getInfo())
            roiEnd = roiEnd.merge(featbyCC)

        return roiEnd

    def read_list_FeatureSelection(self, idGrade, myear):
        nameCSVs = f"/featuresSelectS2_{idGrade}_{myear}.csv"  
        file_path = Path(self.options['path_csvs_featSelect'] + nameCSVs)

        # Check if the file exists
        if file_path.exists():       
            tableAreas = pd.read_csv(self.options['path_csvs_featSelect'] + nameCSVs)
            print("update Feature Selections ")
            if len(tableAreas['features'].tolist()) > 0:
                self.lstFeaturesSel = tableAreas['features'].tolist()
            else:
                nameCSVs = f"/featuresSelectS2_753_2023.csv" 
                tableAreas = pd.read_csv(self.options['path_csvs_featSelect'] + nameCSVs)
                self.lstFeaturesSel = tableAreas['features'].tolist()
        else:
            nameCSVs = f"/featuresSelectS2_753_2023.csv"  
            tableAreas = pd.read_csv(self.options['path_csvs_featSelect'] + nameCSVs)
            print("select Features Selections DEFAULT CSV")
            self.lstFeaturesSel = tableAreas['features'].tolist()
            
    def read_parameter_classify(self, idBasin):
        pathModelJson = "dictBetterModelpmtSet.json"  
        dictModelsS = {}
        with open(pathModelJson, 'r') as fh:
            dictModelsS = json.load(fh)
        # print("loaded dictModel => ", dictModelsS)

        lstKeysBasin = list(dictModelsS.keys())
        if idBasin in lstKeysBasin:
            self.options['pmtGTB']['numberOfTrees'] = dictModelsS[idBasin]['n_estimators']
            self.options['pmtGTB']['shrinkage'] =  dictModelsS[idBasin]['learning_rate']

        print(f"parametros do classificador activo basin {idBasin} \n ===> ", self.options['pmtGTB'])

    def iterate_bacias(self, idBacia, myModel, makeProb):        
        byYear = True
        # loading geometry bacim
        geoBasin = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                        ee.Filter.eq('nunivotto4', idBacia))
        print("show size regions ", geoBasin.size().getInfo())                                
        geoBasin = geoBasin.geometry()

        imgeoBasin = ee.ImageCollection(self.options['asset_region_img_buffer']).filter(
                                        ee.Filter.eq('nunivotto4', idBacia))  
        imgeoBasin = imgeoBasin.first().gt(0)
        # print("image base lodaded ", imgeoBasin.size().getInfo())

        # sys.exit()
        name_rois = '/rois_grade_' + idBacia
        # shpROIs = 

        # load parametros do classificador
        self.read_parameter_classify(idBacia)

        imglsClasxanos = ee.Image().byte()
        imglsClasxanos_prob = ee.Image().byte()
        
        for nyear in self.lst_year[:]:
            bandActiva = 'classification_' + str(nyear)
            print(f" processing grid_year => {idBacia} <> {bandActiva} ")  

            try:
                nomeROIssave = name_rois + '_red_' + str(nyear)
                roiYY_train = ee.FeatureCollection(self.options['asset_rois_red'] + nomeROIssave)
                roisDictCC = roiYY_train.aggregate_histogram('class').getInfo()
                print("distribuition class balanceada ", roisDictCC)

            except:
                self.saveROIsB = True
                roiYY = ee.FeatureCollection(self.options['asset_rois'] + name_rois).filter(
                            ee.Filter.eq('year', int(nyear)))
                roisDictCC = roiYY.aggregate_histogram('class').getInfo()
                textprint = f" ===== distribuition inicial das classes year {nyear} === \n =======> "
                # print(textprint, roisDictCC)

                roiYY_train = self.balancear_samples(roiYY, nyear, idBacia)
                roisDictCC = roiYY_train.aggregate_histogram('class').getInfo()
                print("distribuition class balanceada ", roisDictCC)
            
            if self.saveROIsB:            
                nomeROIssave = name_rois[1:] + '_red_' + str(nyear)
                self.save_ROIs_toAsset(roiYY_train, nomeROIssave) 
                continue
                
            simgMosaic = ee.ImageCollection(self.options['asset_mosaic_sentinel']
                                                    ).filter(ee.Filter.inList('biome', self.options['biomas'])
                                                        ).filter(ee.Filter.eq('year', int(nyear))
                                                                ).filterBounds(geoBasin)#.select(arqParam.featureBands)
            # print(simgMosaic.first().getInfo())
            imgMosaic = simgMosaic.map(lambda img: self.process_re_escalar_img(img))
            time.sleep(1)
            img_recMosaic = imgMosaic.median() 
        
            # print("size ", img_recMosaic.size().getInfo())  
            # print("metadado ", img_recMosaic.select(self.bandSentinel).bandNames().getInfo())
            img_recMosaicnewB = self.CalculateIndice(img_recMosaic.select(self.bandSentinel))
            time.sleep(1)
            # bndAdd = img_recMosaicnewB.bandNames().getInfo()            
            # print(f"know bands names Index {len(bndAdd)}")
            # print("  ", bndAdd)

            img_recMosaic = img_recMosaic.select(self.features_extras).addBands(
                                        ee.Image(img_recMosaicnewB))
            bndAdd = img_recMosaic.bandNames().getInfo()            
            print(f"know bands names {len(bndAdd)}")
            print("  ", bndAdd)
            
            
            # loaded new list of Feature Selections 
            self.read_list_FeatureSelection(idBacia, int(nyear))
            print(f"=== bandas {len(self.lstFeaturesSel)} para treinamento ", self.lstFeaturesSel[:3])
            print("show parameters ", self.options['pmtGTB'])

            # sys.exit()
            if myModel == "RF":
                classifierRF = ee.Classifier.smileRandomForest(**self.options['pmtRF']).train(
                                                    roiYY_train, 'class', self.lstFeaturesSel)            
                classifiedRF = img_recMosaic.classify(classifierRF, bandActiva)
                if makeProb:
                    classifiedRFBprob = img_recMosaic.classify(classifierRF.setOutputMode('MULTIPROBABILITY'))
                    classifiedRFBprob = classifiedRFBprob.arrayReduce(reducer= ee.Reducer.max(), axes= [0])
                    classifiedRFBprob = classifiedRFBprob.multiply(100).byte().rename('prob_'+ str(nyear))
                
            elif myModel == "GTB":
                # ee.Classifier.smileGradientTreeBoost(numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed)
                classifierGTB = ee.Classifier.smileGradientTreeBoost(**self.options['pmtGTB']).train(
                                                    roiYY_train, 'class', self.lstFeaturesSel)              
                classifiedGTB = img_recMosaic.classify(classifierGTB, bandActiva)
                # sys.exit()
                if makeProb:
                    classifiedGTBprob = img_recMosaic.classify(classifierGTB.setOutputMode('MULTIPROBABILITY'))
                    classifiedGTBprob = classifiedGTBprob.arrayReduce(reducer= ee.Reducer.max(), axes= [0])
                    classifiedGTBprob = classifiedGTBprob.multiply(100).byte().rename('prob_'+ str(nyear))
            
            else:
                # ee.Classifier.libsvm(decisionProcedure, svmType, kernelType, shrinking, degree, gamma, coef0, cost, nu, terminationEpsilon, lossEpsilon, oneClass)
                classifierSVM = ee.Classifier.libsvm(**self.options['pmtSVM'])\
                                            .train(roiYY_train, 'class', self.lstFeaturesSel)
                classifiedSVM = img_recMosaic.classify(classifierSVM, bandActiva)
                if makeProb:
                    classifiedSVMBprob = img_recMosaic.classify(classifierSVM.setOutputMode('MULTIPROBABILITY'))
                    classifiedSVMBprob = classifiedSVMBprob.arrayReduce(reducer= ee.Reducer.max(), axes= [0])
                    classifiedSVMBprob = classifiedSVMBprob.multiply(100).byte().rename('prob_'+ str(nyear))
                                
                # print("classificando!!!! ")

            #se for o primeiro ano cria o dicionario e seta a variavel como
            #o resultado da primeira imagem classificada
            print("addicionando classification bands = " , bandActiva)   
            nomec = 'bacia_' + idBacia + '_' + 'GTB_col9-S2_v' + str(self.options['version'])         
            # if self.options['anoInicial'] == nyear:
            #     print ('entrou em 2016, no modelo ', myModel)
            #     if myModel == "GTB":
            #         print("===> ", myModel)    
            #         imglsClasxanos = copy.deepcopy(classifiedGTB)            
            #         if makeProb:
            #             imglsClasxanos_prob = copy.deepcopy(classifiedGTBprob)                        
            #         nomec = 'bacia_' + idBacia + '_' + 'GTB_col9-S2_v' + str(self.options['version'])
            #     elif myModel == "RF":
            #         print("===> ", myModel)                
            #         imglsClasxanos = copy.deepcopy(classifiedRF)
            #         if makeProb:
            #             imglsClasxanos_prob = copy.deepcopy(classifiedRFBprob)                        
            #         nomec = 'bacia_' + idBacia + '_' + 'RF_col9-v' + str(self.options['version'])      
            #     else:   
            #         imglsClasxanos = copy.deepcopy(classifiedSVM)              
            #         if makeProb:
            #             imglsClasxanos_prob = copy.deepcopy(classifiedSVMBprob)                        
            #         nomec = 'bacia_' + idBacia + '_' + 'SVM_col9-v' + str(self.options['version'])
                
                # mydict = {
                #     'id_bacia': idBacia,
                #     'version': self.options['version'],
                #     'biome': self.options['bioma'],
                #     'classifier': myModel,
                #     'collection': '9.0',
                #     'sensor': 'Sentinel',
                #     'source': 'geodatin',                
                # }
                # imglsClasxanos = imglsClasxanos.set(mydict)
                # if byYear:
                #     processoExportar(imglsClasxanos.select(bandActiva), geoBasin.coordinates(), nomec + "_" +  '_prob')



            #se nao, adiciona a imagem como uma banda a imagem que ja existia
            # else:
            #     # print("Adicionando o mapa do ano  ", ano)
            #     # print(" ", classifiedGTB.bandNames().getInfo())
            #     if myModel == "GTB":      
            #         imglsClasxanos = imglsClasxanos.addBands(classifiedGTB)          
            #         if makeProb:
            #             imglsClasxanos_prob = imglsClasxanos_prob.addBands(classifiedGTBprob)                      
                        
            #     elif myModel == "RF":
            #         imglsClasxanos = imglsClasxanos.addBands(classifiedRF) 
            #         if makeProb:
            #             imglsClasxanos_prob = imglsClasxanos_prob.addBands(classifiedRFBprob)
                        
            #     else:   
            #         imglsClasxanos = imglsClasxanos.addBands(classifiedSVM)             
            #         if makeProb:
            #             imglsClasxanos_prob = imglsClasxanos_prob.addBands(classifiedSVMBprob)   

            imglsClasxanos = copy.deepcopy(classifiedGTB)
            mydict = {
                    'id_bacia': idBacia,
                    'version': self.options['version'],
                    'biome': self.options['bioma'],
                    'classifier': myModel,
                    'collection': '9.0',
                    'sensor': 'Sentinel',
                    'source': 'geodatin',  
                    'year':  nyear             
            }
            imglsClasxanos = imglsClasxanos.set(mydict)
            self.processoExportar(imglsClasxanos.select(bandActiva), geoBasin.coordinates(), nomec + "_" +  str(nyear) + '_prob')                     
                   
        # i+=1
        # print(param['lsBandasMap'])  
        
        # if not self.saveROIsB:
        #     # seta as propriedades na imagem classificada    
        #     # print("show names bands of imglsClasxanos ", imglsClasxanos.bandNames().getInfo() )        
        #     imglsClasxanos = imglsClasxanos.select(self.options['lsBandasMap'])    
        #     imglsClasxanos = imglsClasxanos.updateMask(imgeoBasin).set("system:footprint", geoBasin.coordinates())
        #     # exporta bacia
        #     self.processoExportar(imglsClasxanos, geoBasin.coordinates(), nomec) 
        #     if makeProb:
        #         imglsClasxanos_prob = imglsClasxanos_prob.updateMask(imgeoBasin).set("system:footprint", geoBasin.coordinates())
        #         processoExportar(imglsClasxanos_prob, geoBasin.coordinates(), nomec + '_prob')

                
    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF, regionB, nomeDesc):

        idasset =  self.options['asset_output'] + '/' + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':regionB.getInfo(), #['coordinates']
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

    # salva ftcol para um assetindexIni
    # lstKeysFolder = ['cROIsN2manualNN', 'cROIsN2clusterNN'] 
    def save_ROIs_toAsset(self, collection, name):
        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['asset_rois_red'] + "/" + name
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("exportando ROIs da bacia $s ...!", name)



listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
param = {
    'asset_input': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX',
    'anoInicial': 2016,
    'anoFinal': 2022,
    'changeCount': False,
    'numeroTask': 6,
    'numeroLimit': 60,
    'conta': {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',
        '25': 'solkan1201',
        '30': 'diegoGmail',
        '35': 'solkanGeodatin',
        '40': 'superconta'
    },
}

def gerenciador(cont, param):
    numberofChange = [kk for kk in param['conta'].keys()]
    if str(cont) in numberofChange:
        gee.switch_user(param['conta'][str(cont)])
        # gee.init()        
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!')
        gee.tasks(n=param['numeroTask'], return_list=True)
    elif cont > param['numeroLimit']:
        return 0
    cont += 1
    return cont


cont = 0
if param['changeCount']:
    cont = gerenciador(cont, param)
versionBuilding = '2'
rastersmap = ee.ImageCollection(param['asset_input']).filter(ee.Filter.eq('version', versionBuilding))
lstidCodeSaved = rastersmap.reduceColumns(ee.Reducer.toList(), ['id_bacia']).get('list').getInfo()
print("lista das bacias feitas \n ===> ", lstidCodeSaved)
print(f" ## {len(lstidCodeSaved)} feitas ")
# sys.exit()
if len(lstidCodeSaved) > 0:
    lstNameBacias = [ kk for kk in listaNameBacias if kk not in lstidCodeSaved]
else:
    lstNameBacias = listaNameBacias

modeloApply = "GTB"  # 'RF'
exportProbLayer = False
saveROIsBalance = False
objetoclassifyMosaic = Classify_Mosaic_process(saveROIsBalance)
print("saida ==> ", objetoclassifyMosaic.options['asset_output'])

for cc, nbacia in enumerate(lstNameBacias[:]):    
    print(f" processing bacia {nbacia}")
    objetoclassifyMosaic.iterate_bacias(nbacia, modeloApply, exportProbLayer)
    cont = gerenciador(cont, param)