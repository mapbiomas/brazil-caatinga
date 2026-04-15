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
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
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
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
        'asset_mosaic_sentinel': 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample', 
        # 'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2',
        'asset_output': 'projects/nexgenmap/SAMPLES/Caatinga',
        'lsClasse': [4, 3, 12, 15, 18, 21, 25, 33],
        'lsPtos': [3000, 5000, 3000, 3500, 1500, 1000, 1500, 3000],
        "anoIntInit": 2016,
        "anoIntFin": 2023,
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

        self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])#.geometry()
        self.year_activo =  2016
        name_dict = 'dict_stat_nyearRegCorr.json'
        self.dict_Statgeral = {}

        # Using json.load()
        with open(name_dict) as dictJson:
            self.dict_Statgeral = json.load(dictJson)

        # print("dict statistics ", self.dict_Statgeral )
        # sys.exit()
        # self.nlstAssetsROIs = nlstAssetsROIs                                
        # print("  ", self.imgMosaic.size().getInfo())
        print("see band Names the first ")
        # print(" ==== ", ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        # print("all images ", self.imgMosaic.size().getInfo())
        # print("show metadata from first images ", self.imgMosaic.first().getInfo())
        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        
        # @collection90: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection90 = ee.Image(self.options['assetMapbiomas90'])

        # # Remap todas as imagens mapbiomas
        lsBndMapBiomnas = []
        self.imgMapbiomas = ee.Image().toByte()

        for year in self.lst_year:
            band = 'classification_' + str(year)
            lsBndMapBiomnas.append(band)
            imgTemp = collection90.select(band).remap(
                self.options['classMapB'], self.options['classNew'])
            self.imgMapbiomas = self.imgMapbiomas.addBands(
                imgTemp.rename(band))

        self.imgMapbiomas = self.imgMapbiomas.select(lsBndMapBiomnas)#.clip(self.regionInterest.geometry())

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
        
        return imgMosaic.addBands(imgEscalada).select(self.featureBands).set('year', imgA.get('year'))


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

   
    def iterate_bacias(self, idGrade, askSize):        

        # loading geometry bacim
    
        oneGrade = ee.FeatureCollection(self.options['asset_grad']).filter(
                                        ee.Filter.eq('indice', int(idGrade)))
        print("show size regions ", oneGrade.size().getInfo())                                
        oneGrade = oneGrade.geometry()  
        # sys.exit()
        

        
        layerSamplesMask = ee.ImageCollection(self.options['asset_mask_toSamples']
                                ).filterBounds(oneGrade)#
        numLayers = 1
        try:
            numLayers =  layerSamplesMask.size().getInfo()
            if numLayers > 0:
                layerSamplesMask = layerSamplesMask.mosaic()
            else:
                layerSamplesMask = ee.Image.constant(1).clip(oneGrade) 
                numLayers = 0
        except:
            layerSamplesMask = ee.Image.constant(1).clip(oneGrade) 
            numLayers = 0      
        
        for nyear in self.lst_year[:]:
            bandYear = 'classification_' + str(nyear)
            self.year_activo  = str(nyear)
            print(f" processing grid_year => {idGrade} <> {bandYear} ")             

            simgMosaic = ee.ImageCollection(self.options['asset_mosaic_sentinel']
                                                    ).filter(ee.Filter.inList('biome', self.options['biomas'])
                                                        ).filter(ee.Filter.eq('year', int(nyear))
                                                                ).filterBounds(oneGrade)#.select(arqParam.featureBands)
            # print(simgMosaic.first().getInfo())

            imgMosaic = simgMosaic.map(lambda img: self.process_re_escalar_img(img))

            img_recMosaic = imgMosaic.median() 
            # print("size ", img_recMosaic.size().getInfo())  
            # print("metadado ", img_recMosaic.select(self.bandSentinel).bandNames().getInfo())
            img_recMosaicnewB = self.CalculateIndice(img_recMosaic.select(self.bandSentinel))
            # bndAdd = img_recMosaicnewB.bandNames().getInfo()            
            # print(f"know bands names Index {len(bndAdd)}")
            # print("  ", bndAdd)

            img_recMosaic = img_recMosaic.select(self.features_extras).addBands(
                                        ee.Image(img_recMosaicnewB))
            # bndAdd = img_recMosaic.bandNames().getInfo()            
            # print(f"know bands names {len(bndAdd)}")
            # print("  ", bndAdd)
            print("----- calculado todos os indices ---------------------")
            # sys.exit()
            if numLayers > 0:
                maskYear = layerSamplesMask.select("mask_sample_" + str(nyear))
                print("imagem mask layer => ", maskYear.bandNames().getInfo())
            else:
                maskYear = layerSamplesMask

            shpAllFeat = ee.FeatureCollection([])                    
            for cc, nclass in enumerate(self.options['lsClasse'][:]):
                # print(f"processing class {nclass}")

                layerCC = self.imgMapbiomas.select(bandYear).eq(int(nclass)).multiply(int(nclass)).rename('class')
                layerCC = layerCC.updateMask(maskYear)
                # print("numero de ptos controle ", roisAct.size().getInfo())
                # opcoes para o sorteio estratificadoBuffBacia
                # sample(region, scale, projection, factor, numPixels, seed, dropNulls, tileScale, geometries)
                ptosTemp = img_recMosaic.addBands(layerCC).updateMask(
                                layerCC.gt(0)).sample(
                                    region=  oneGrade,                                                                
                                    scale= 10,   
                                    numPixels= self.options['lsPtos'][cc],
                                    dropNulls= True,
                                    geometries= True
                                )
                # insere informacoes em cada ft
                ptosTemp = ptosTemp.map(lambda feat : feat.set('year', nyear, 'GRID_ID', idGrade) )
                shpAllFeat = shpAllFeat.merge(ptosTemp)
                # sys.exit()
            print(f"======  coleted rois from class {self.options['lsClasse']}  =======")
        name_exp = 'rois_grade_' + str(idGrade) + "_" + str(nyear)# + "_cc_" + str(nclass)
        if askSize:
            sizeROIscol = ee.FeatureCollection(shpAllFeat).size().getInfo()
            if sizeROIscol > 1:
                self.save_ROIs_toAsset(ee.FeatureCollection(shpAllFeat), name_exp) 
            else:
                print(" we can´t to export roi ")

        else:
            self.save_ROIs_toAsset(ee.FeatureCollection(shpAllFeat), name_exp)
                
    
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

lstIdCode = [
    3990, 3991, 3992, 3993, 3994, 3995, 3996, 3997, 3998, 3999, 4000, 4096, 
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

param = {
    'anoInicial': 2016,
    'anoFinal': 2022,
    'changeCount': False,
    'numeroTask': 6,
    'numeroLimit': 30,
    'conta': {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',
        '25': 'solkan1201',
        # '30': 'diegoGmail',
        # '35': 'solkanGeodatin',
        # '40': 'superconta'
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

askingbySizeFC = True
searchFeatSaved = True
cont = 0
if param['changeCount']:
    cont = gerenciador(cont, param)


objetoMosaic_exportROI = ClassMosaic_indexs_Spectral()
print("saida ==> ", objetoMosaic_exportROI.options['asset_output'])
if searchFeatSaved: 
    lstFeatAsset = ask_byGrid_saved({'id': objetoMosaic_exportROI.options['asset_output']})
    print("   lista de feat ", lstFeatAsset[:5] )
    print("  == size ", len(lstFeatAsset))
    askingbySizeFC = True
else:
    lstFeatAsset = []

# sys.exit()
for cc, item in enumerate(lstIdCode[:1]):
    print(f"# {cc + 1} loading geometry grade {item}")   
    if item not in lstFeatAsset:
        objetoMosaic_exportROI.iterate_bacias(item, askingbySizeFC)
        cont = gerenciador(cont, param)
    # sys.exit()

