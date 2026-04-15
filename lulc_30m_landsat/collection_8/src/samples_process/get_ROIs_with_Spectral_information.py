#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
import json
import csv
import sys
import arqParametros as arqParam
import collections
collections.Callable = collections.abc.Callable
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
        'biomes': ['CAATINGA','CERRADO','MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_baciasN2': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
        'asset_baciasN4': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4',
        'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv1N4',
        'inAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv2N4',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas5': 'projects/mapbiomas-workspace/public/collection5/mapbiomas_collection50_integration_v1',
        'assetMapbiomas6': 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
        'assetMapbiomas71': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_fire': 'projects/mapbiomas-workspace/FOGO_COL2/SUBPRODUTOS/mapbiomas-fire-collection2-annual-burned-v1',
        'asset_befFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_S1v18',
        'asset_filtered': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Tp',
        'asset_alerts': 'users/data_sets_solkan/Alertas/layersClassTP',
        'asset_input_mask' : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/masks/maks_layers',
        'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
        'lsClasse': [3, 4, 12, 15, 18, 21, 22, 33, 29],
        'lsPtos': [3000, 2000, 3000, 1500, 1500, 1000, 1500, 1000, 1000],
        "anoIntInit": 1985,
        "anoIntFin": 2022,
        'janela': 3
    }
    lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self):

        self.regionInterest = ee.FeatureCollection(self.options['asset_baciasN2'])#.geometry()
        self.imgMosaic = ee.ImageCollection(self.options['asset_mosaic_mapbiomas']
                                                    ).filter(ee.Filter.inList('biome', self.options['biomes'])
                                                        ).select(arqParam.featuresreduce)
                                                    
        # print("  ", self.imgMosaic.size().getInfo())
        print("see band Names the first ")
        # print(ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'])]
        # # @collection6 bruta: mapas de uso e cobertura Mapbiomas ==> para masquear as amostra fora de mascara
        # self.collection_bruta = ee.ImageCollection(self.options['assetMapbiomas71']).min()
        # self.img_mask = self.collection_bruta.unmask(100).eq(100).reduce(ee.Reducer.sum())
        # self.img_mask = self.img_mask.eq(0).selfMask()
        
        # @collection71: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection71 = ee.Image(self.options['assetMapbiomas71'])

        # # Remap todas as imagens mapbiomas
        lsBndMapBiomnas = []
        self.imgMapbiomas = ee.Image().toByte()

        for year in self.lst_year:
            band = 'classification_' + str(year)
            lsBndMapBiomnas.append(band)
            imgTemp = collection71.select(band).remap(
                self.options['classMapB'], self.options['classNew'])
            self.imgMapbiomas = self.imgMapbiomas.addBands(
                imgTemp.rename(band))

        self.imgMapbiomas = self.imgMapbiomas.select(lsBndMapBiomnas).clip(self.regionInterest.geometry())
        # self.imgMapbiomas = self.imgMapbiomas.updateMask(self.img_mask)

        self.baciasN2 = ee.FeatureCollection(self.options['asset_baciasN2'])
        # colectAnos = []
    # Ratio Vegetation Index
    def agregateBandsIndexRATIO(self, img):
    
        ratioImg = img.expression("float(b('nir') / b('red'))")\
                                .multiply(10000).rename(['ratio']).toUint16()      

        return img.addBands(ratioImg)

    # Ratio Vegetation Index
    def agregateBandsIndexRVI(self, img):
    
        rviImg = img.expression("float(b('red') / b('nir'))")\
                                .multiply(10000).rename(['rvi']).toUint16()       

        return img.addBands(rviImg)
    
    def agregateBandsIndexNDVI(self, img):
    
        ndviImg = img.expression("float(b('nir') - b('red')) / (b('nir') + b('red'))")\
                                .add(1).multiply(10000).rename(['ndvi']).toUint16()       

        return img.addBands(ndviImg)

    def agregateBandsIndexWater(self, img):
    
        ndwiImg = img.expression("float(b('nir') - b('swir2')) / (b('nir') + b('swir2'))")\
                                .add(1).multiply(10000).rename(['ndwi']).toUint16()       

        return img.addBands(ndwiImg)
    
    
    def AutomatedWaterExtractionIndex(self, img):    
        awei = img.expression(
                            "float(4 * (b('green') - b('swir2')) - (0.25 * b('nir') + 2.75 * b('swir1')))"
                        ).add(1).multiply(10000).rename("awei").toUint16()          
        
        return img.addBands(awei)
    
    def IndiceIndicadorAgua(self, img):    
        iiaImg = img.expression(
                            "float((b('green') - 4 *  b('nir')) / (b('green') + 4 *  b('nir')))"
                        ).add(1).multiply(10000).rename("iia").toUint16()
        
        return img.addBands(iiaImg)
    
    def agregateBandsIndexLAI(self, img):
        laiImg = img.expression(
            "float(3.618 * (b('evi') - 0.118))")\
                .add(3).multiply(10000).rename(['lai']).toUint16()
    
        return img.addBands(laiImg)    

    def agregateBandsIndexGCVI(self, img):    
        gcviImgA = img.expression(
            "float(b('nir')) / (b('green')) - 1")\
                .add(1).multiply(10000).rename(['gcvi']).toUint16()        
        
        return img.addBands(gcviImgA)

    # Global Environment Monitoring Index GEMI 
    def agregateBandsIndexGEMI(self, img):    
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgA = img.expression(
            "float((2 * (b('nir') * b('nir') - b('red') * b('red')) + 1.5 * b('nir') + 0.5 * b('red')) / (b('nir') + b('green') + 0.5) )")\
                .add(3).multiply(10000).rename(['gemi']).toUint16()        
        
        return img.addBands(gemiImgA)

    # Chlorophyll vegetation index CVI
    def agregateBandsIndexCVI(self, img):    
        cviImgA = img.expression(
            "float(b('nir') * (b('green') / (b('blue') * b('blue'))))")\
                .multiply(10000).rename(['cvi']).toUint16()        
        
        return img.addBands(cviImgA)

    # Green leaf index  GLI
    def agregateBandsIndexGLI(self,img):    
        gliImg = img.expression(
            "float((2 * b('green') - b('red') - b('blue')) / (2 * b('green') - b('red') - b('blue')))")\
                .add(1).multiply(10000).rename(['gli']).toUint16()        
        
        return img.addBands(gliImg)

    # Shape Index  IF 
    def agregateBandsIndexShapeI(self, img):    
        shapeImgA = img.expression(
            "float((2 * b('red') - b('green') - b('blue')) / (b('green') - b('blue')))")\
                .add(1).multiply(10000).rename(['shape']).toUint16()       
        
        return img.addBands(shapeImgA)

    # Aerosol Free Vegetation Index (2100 nm) 
    def agregateBandsIndexAFVI(self, img):    
        afviImgA = img.expression(
            "float((b('nir') - 0.5 * b('swir2')) / (b('nir') + 0.5 * b('swir2')))")\
                .add(1).multiply(10000).rename(['afvi']).toUint16()        
        
        return img.addBands(afviImgA)

    # Advanced Vegetation Index 
    def agregateBandsIndexAVI(self, img):    
        aviImgA = img.expression(
            "float((b('nir')* (1.0 - b('red')) * (b('nir') - b('red'))) ** 1/3)")\
                .add(1).multiply(10000).rename(['avi']).toUint16()        
        
        return img.addBands(aviImgA)

    # Bare Soil Index 
    def agregateBandsIndexBSI(self,img):    
        bsiImg = img.expression(
            "float(((b('swir1') - b('red')) - (b('nir') + b('blue'))) / ((b('swir1') + b('red')) + (b('nir') + b('blue'))))")\
                .add(1).multiply(10000).rename(['bsi']).toUint16()        
        
        return img.addBands(bsiImg)

    # BRBA	Band Ratio for Built-up Area  
    def agregateBandsIndexBRBA(self,img):    
        brbaImg = img.expression(
            "float(b('red') / b('swir1'))")\
                .multiply(10000).rename(['brba']).toUint16()        
        
        return img.addBands(brbaImg)

    # DSWI5	Disease-Water Stress Index 5
    def agregateBandsIndexDSWI5(self,img):    
        dswi5Img = img.expression(
            "float((b('nir') + b('green')) / (b('swir1') + b('red')))")\
                .multiply(10000).rename(['dswi5']).toUint16()        
        
        return img.addBands(dswi5Img)

    # LSWI	Land Surface Water Index
    def agregateBandsIndexLSWI(self,img):    
        lswiImg = img.expression(
            "float((b('nir') - b('swir1')) / (b('nir') + b('swir1')))")\
                .add(1).multiply(10000).rename(['lswi']).toUint16()        
        
        return img.addBands(lswiImg)

    # MBI	Modified Bare Soil Index
    def agregateBandsIndexMBI(self,img):    
        mbiImg = img.expression(
            "float(((b('swir1') - b('swir2') - b('nir')) / (b('swir1') + b('swir2') + b('nir'))) + 0.5)")\
                .add(1).multiply(10000).rename(['mbi']).toUint16()       
        
        return img.addBands(mbiImg)

    # UI	Urban Index	urban
    def agregateBandsIndexUI(self,img):    
        uiImg = img.expression(
            "float((b('swir2') - b('nir')) / (b('swir2') + b('nir')))")\
                .add(1).multiply(10000).rename(['ui']).toUint16()        
        
        return img.addBands(uiImg)

    # OSAVI	Optimized Soil-Adjusted Vegetation Index
    def agregateBandsIndexOSAVI(self,img):    
        osaviImg = img.expression(
            "float(b('nir') - b('red')) / (0.16 + b('nir') + b('red'))")\
                .add(1).multiply(10000).rename(['osavi']).toUint16()        
        
        return img.addBands(osaviImg)

    # Normalized Difference Red/Green Redness Index  RI
    def agregateBandsIndexRI(self, img):        
        riImg = img.expression(
            "float(b('nir') - b('green')) / (b('nir') + b('green'))")\
                .add(1).multiply(10000).rename(['ri']).toUint16()       
        
        return img.addBands(riImg)    

    # Tasselled Cap - brightness 
    def agregateBandsIndexBrightness(self, img):    
        tasselledCapImg = img.expression(
            "float(0.3037 * b('blue') + 0.2793 * b('green') + 0.4743 * b('red')  + 0.5585 * b('nir') + 0.5082 * b('swir1') +  0.1863 * b('swir2'))")\
                .add(1).multiply(10000).rename(['brightness']).toUint16() 
        
        return img.addBands(tasselledCapImg)
    
    # Tasselled Cap - wetness 
    def agregateBandsIndexwetness(self, img):    
        tasselledCapImg = img.expression(
            "float(0.1509 * b('blue') + 0.1973 * b('green') + 0.3279 * b('red')  + 0.3406 * b('nir') + 0.7112 * b('swir1') +  0.4572 * b('swir2'))")\
                .add(1).multiply(10000).rename(['wetness']).toUint16() 
        
        return img.addBands(tasselledCapImg)
    
    # Moisture Stress Index (MSI)
    def agregateBandsIndexMSI(self, img):    
        msiImg = img.expression(
            "float( b('nir') / b('swir1'))")\
                .add(1).multiply(10000).rename(['msi']).toUint16() 
        
        return img.addBands(msiImg)

    def agregateBandsIndexGVMI(self, img):        
        gvmiImg = img.expression(
                        "float ((b('nir')  + 0.1) - (b('swir1') + 0.02)) / ((b('nir') + 0.1) + (b('swir1') + 0.02))" 
                    ).add(3).multiply(10000).rename(['gvmi']).toUint16()     
    
        return img.addBands(gvmiImg) 
    
    def agregateBandsIndexsPRI(self, img):        
        priImg = img.expression(
                                "float((b('green') - b('blue')) / (b('green') + b('blue')))"
                            ).rename(['pri'])   
        spriImg =   priImg.expression(
                                "float((b('pri') + 1) / 2)").add(1).multiply(10000).rename(['spri'])  
    
        return img.addBands(spriImg)
    

    def agregateBandsIndexCO2Flux(self, img):        
        ndviImg = img.expression("float(b('nir') - b('swir2')) / (b('nir') + b('swir2'))").rename(['ndvi']) 
        
        priImg = img.expression(
                                "float((b('green') - b('blue')) / (b('green') + b('blue')))"
                            ).rename(['pri'])   
        spriImg =   priImg.expression(
                                "float((b('pri') + 1) / 2)").rename(['spri'])

        co2FluxImg = ndviImg.multiply(spriImg).rename(['co2flux'])   
        
        return img.addBands(co2FluxImg)


    def agregateBandsTexturasGLCM(self, img):        
        img = img.toInt()                
        textura2 = img.select('nir').glcmTexture(3)  
        contrastnir = textura2.select('nir_contrast').toUint16()
        #
        textura2 = img.select('red').glcmTexture(3)  
        contrastred = textura2.select('red_contrast').toUint16()
        return  img.addBands(contrastnir).addBands(contrastred)

    def agregateBandsgetFractions(self, fractions):         
        # 'bnd_fraction': ['gv_median','npv_median','soil_median'],
        ndfia = fractions.expression(
            "float(b('gv') - b('soil')) / float( b('gv') + 2 * b('npv') + b('soil'))")        
        ndfia = ndfia.add(1).rename('ndfia')
        
        return ndfia

    # https://code.earthengine.google.com/d5a965bbb6b572306fb81baff4bd401b
    def get_class_maskAlerts(self, yyear):
        #  get from ImageCollection 
        maskAlertyyear = ee.ImageCollection(self.options['asset_alerts']).filter(ee.Filter.eq('yearDep', yyear)
                                ).reduce(ee.Reducer.max()).eq(0).rename('mask_alerta')

        return maskAlertyyear        

    def get_class_maskFire(self, yyear):
        maskFireyyear = ee.Image(self.options['asset_fire']).select("burned_area_" + str(yyear)
                                    ).unmask(0).eq(0).rename('mask_fire')

        return maskFireyyear

    def CalculateIndice(self, imagem):

        band_feat = [
                "ratio","rvi","ndwi","awei","iia",
                "gcvi","gemi","cvi","gli","shape","afvi",
                "avi","bsi","brba","dswi5","lswi","mbi","ui",
                "osavi","ri","brightness","wetness",
                "nir_contrast","red_contrast"
            ]
        
        # imagem em Int16 com valores inteiros ate 10000        
        # imageF = self.agregateBandsgetFractions(imagem)        
        # print(imageF.bandNames().getInfo())
        imageW = imagem.divide(10000)
   
        imageW = self.agregateBandsIndexRATIO(imageW)  #
        imageW = self.agregateBandsIndexRVI(imageW)    #    
        imageW = self.agregateBandsIndexWater(imageW)  #      
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

        return imagem.addBands(imageW).select(band_feat)# .addBands(imageF)


    def calculate_indices_x_blocos(self, image):

        
        # band_year = [bnd + '_median' for bnd in self.option['bnd_L']]
        band_year = ['blue_median','green_median','red_median','nir_median','swir1_median','swir2_median']
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
    
    def iterate_bacias(self, nomeBacia):

        # colecao responsavel por executar o controle de execucao, caso optem 
        # por executar o codigo em terminais paralelos,
        # ou seja, em mais de um terminal simultaneamente..
        # caso deseje executar num unico terminal, deixar colecao vazia.        
        # colecaoPontos = ee.FeatureCollection([])
        # lsNoPtos = []
        
        oneBacia = self.baciasN2.filter(
            ee.Filter.eq('nunivotto3', nomeBacia)).geometry()            

        for anoCount in range(self.options['anoIntInit'], self.options["anoIntFin"] + 1):

            if ((nomeBacia == '759') and (anoCount == 2010)) or (
                (nomeBacia == '765') and (anoCount == 1997)) or (
                (nomeBacia == '766') and (anoCount == 2007)) or (
                (nomeBacia == '7619') and (anoCount == 1999)) or (
                (nomeBacia == '7619') and (anoCount == 2016)) or (
                (nomeBacia == '7422') and (anoCount == 2004)):

                bandActiva = 'classification_' + str(anoCount)
                if anoCount < self.options["anoIntFin"]:
                    # print("banda activa: " + bandActiva)  
                    m_assetPixE = self.options['asset_input_mask'] + '/masks_estatic_pixels_'+ str(anoCount)
                    maksEstaveis = ee.Image(m_assetPixE).rename('estatic')  

                    map_yearAct = self.imgMapbiomas.select(bandActiva).rename(['class'])
                    imMaskFire = self.get_class_maskFire(anoCount)
                    imMaskFire = imMaskFire.multiply(maksEstaveis)

                    if anoCount >= 2020:
                        imMaksAlert = self.get_class_maskAlerts(anoCount)
                        imMaskFire = imMaskFire.multiply(imMaksAlert)
                    else:
                        m_asset = self.options['asset_input_mask'] + '/masks_pixels_incidentes_'+ str(anoCount)
                        imMaskInc = ee.Image(m_asset).rename('incident')   
                    # adding pixels that coincidem em col5, 6, 7 or coincident in col 6 and col7
                    imMaskFire = imMaskFire.multiply(imMaskInc.lte(2))
                    map_yearAct = map_yearAct.addBands(
                                            ee.Image.constant(int(anoCount)).rename('year'))

                    map_yearAct = map_yearAct.clip(oneBacia.bounds()) 


                img_recMosaic = self.imgMosaic.filterBounds(oneBacia).filter(
                                            ee.Filter.eq('year', anoCount)).median().toUint16()   

                img_recMosaicnewB = self.calculate_indices_x_blocos(img_recMosaic)
                bndAdd = img_recMosaicnewB.bandNames().getInfo()
                # print(f"know bands names {len(bndAdd)}")
                # print("  ", bndAdd)

                img_recMosaic = img_recMosaic.addBands(ee.Image(img_recMosaicnewB))

                # print("numero de ptos controle ", roisAct.size().getInfo())
                # opcoes para o sorteio estratificadoBuffBacia
                ptosTemp = img_recMosaic.updateMask(imMaskFire).addBands(
                                map_yearAct).stratifiedSample(
                                    numPoints= 1200,
                                    classBand= 'class',
                                    region= oneBacia,
                                    scale= 30,
                                    # classValues= self.options['lsClasse'],
                                    # classPoints= self.options['lsPtos'],
                                    tileScale= 8,
                                    geometries= True
                                )
                # insere informacoes em cada ft
                ptosTemp = ptosTemp.filter(ee.Filter.notNull(['class']))
                # merge com colecoes anteriores
                # colecaoPontos = colecaoPontos.merge(ptosTemp)            
                # sys.exit()
                name_exp = str(nomeBacia) + "_" + str(anoCount) +"_c1"  
                self.save_ROIs_toAsset(ee.FeatureCollection(ptosTemp), name_exp)        

    
    # salva ftcol para um assetindexIni
    def save_ROIs_toAsset(self, collection, name):

        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['outAssetROIs'] + "/" + name
        }

        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("exportando ROIs da bacia $s ...!", name)


print("len arqParam ", len(arqParam.featuresreduce))

param = {
    'bioma': ["CAATINGA", 'CERRADO', 'MATAATLANTICA'],
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    # 'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/PtosXBaciasBalanceados/',
    'janela': 5,
    'escala': 30,
    'sampleSize': 0,
    'metodotortora': True,
    'tamROIsxClass': 4000,
    'minROIs': 1500,
    # "anoColeta": 2015,
    'anoInicial': 1985,
    'anoFinal': 2022,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta': {
        '0': 'caatinga01',
        '6': 'caatinga02',
        '12': 'caatinga03',
        '18': 'caatinga04',
        '24': 'caatinga05',
        '30': 'solkan1201',
        '36': 'diegoGmail',
        # '20': 'rodrigo'
    },
}
def gerenciador(cont, param):

    numberofChange = [kk for kk in param['conta'].keys()]

    if str(cont) in numberofChange:

        gee.switch_user(param['conta'][str(cont)])
        gee.init()
        gee.tasks(n=param['numeroTask'], return_list=True)

    elif cont > param['numeroLimit']:
        cont = 0

    cont += 1
    return cont

# listaNameBacias = [
#     '741','7421','7422','744','745','746','7492','751','752','753',
#     '754','755','756','757','758','759','7621','7622','763','764',
#     '765','766','767','771','772','773', '7741','7742','775','776',
#     '777','778','76111','76116','7612','7614','7615','7616','7617',
#     '7618','7619', '7613'
# ]
listaNameBacias = ['765','766','759','7619','7422']
cont = gerenciador(0, param)
# revisao da coleção 8 
# https://code.earthengine.google.com/5e8af5ef94684a5769e853ad675fc368

for cc, item_bacia in enumerate(listaNameBacias[:]):
    print(f"# {cc + 1} loading geometry bacia {item_bacia}")     
    objetoMosaic_exportROI = ClassMosaic_indexs_Spectral()
    # geobacia, colAnos, nomeBacia, dict_nameBN4
    objetoMosaic_exportROI.iterate_bacias(item_bacia)
    cont = gerenciador(cont, param)

    # sys.exit()