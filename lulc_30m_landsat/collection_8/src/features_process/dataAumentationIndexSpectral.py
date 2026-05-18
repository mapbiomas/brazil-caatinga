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
        'bnd_L': ['blue','green','red','nir','swir1','swir2','gv','npv','soil'],
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
        'asset_output_mask' : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/masks/maks_layers',
        'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
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
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
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
                                .rename(['ratio'])      

        return img.addBands(ratioImg)

    # Ratio Vegetation Index
    def agregateBandsIndexRVI(self, img):
    
        rviImg = img.expression("float(b('red') / b('nir'))")\
                                .rename(['rvi'])       

        return img.addBands(rviImg)
    
    def agregateBandsIndexNDVI(self, img):
    
        ndviImg = img.expression("float(b('nir') - b('red')) / (b('nir') + b('red'))")\
                                .rename(['ndvi'])       

        return img.addBands(ndviImg)

    def agregateBandsIndexWater(self, img):
    
        ndwiImg = img.expression("float(b('nir') - b('swir2')) / (b('nir') + b('swir2'))")\
                                .rename(['ndwi'])       

        return img.addBands(ndwiImg)
    
    
    def AutomatedWaterExtractionIndex(self, img):    
        awei = img.expression(
                            "float(4 * (b('green') - b('swir2')) - (0.25 * b('nir') + 2.75 * b('swir1')))"
                        ).rename("awei")          
        
        return img.addBands(awei)
    
    def IndiceIndicadorAgua(self, img):    
        iiaImg = img.expression(
                            "float((b('green') - 4 *  b('nir')) / (b('green') + 4 *  b('nir')))"
                        ).rename("iia")
        
        return img.addBands(iiaImg)
    
    def agregateBandsIndexLAI(self, img):
        laiImg = img.expression(
            "float(3.618 * (b('evi') - 0.118))")\
                .rename(['lai'])     
    
        return img.addBands(laiImg)    

    def agregateBandsIndexGCVI(self, img):    
        gcviImgA = img.expression(
            "float(b('nir')) / (b('green')) - 1")\
                .rename(['gcvi'])        
        
        return img.addBands(gcviImgA)

    # Global Environment Monitoring Index GEMI 
    def agregateBandsIndexGEMI(self, img):    
        # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
        gemiImgA = img.expression(
            "float((2 * (b('nir') * b('nir') - b('red') * b('red')) + 1.5 * b('nir') + 0.5 * b('red')) / (b('nir') + b('green') + 0.5) )")\
                .rename(['gemi'])        
        
        return img.addBands(gemiImgA)

    # Chlorophyll vegetation index CVI
    def agregateBandsIndexCVI(self, img):    
        cviImgA = img.expression(
            "float(b('nir') * (b('green') / (b('blue') * b('blue'))))").multiply(100)\
                .rename(['cvi'])        
        
        return img.addBands(cviImgA)

    # Green leaf index  GLI
    def agregateBandsIndexGLI(self,img):    
        gliImg = img.expression(
            "float((2 * b('green') - b('red') - b('blue')) / (2 * b('green') - b('red') - b('blue')))")\
                .rename(['gli'])        
        
        return img.addBands(gliImg)

    # Shape Index  IF 
    def agregateBandsIndexShapeI(self, img):    
        shapeImgA = img.expression(
            "float((2 * b('red') - b('green') - b('blue')) / (b('green') - b('blue')))").multiply(100)\
                .rename(['shape'])        
        
        return img.addBands(shapeImgA)

    # Aerosol Free Vegetation Index (2100 nm) 
    def agregateBandsIndexAFVI(self, img):    
        afviImgA = img.expression(
            "float((b('nir') - 0.5 * b('swir2')) / (b('nir') + 0.5 * b('swir2')))")\
                .rename(['afvi'])        
        
        return img.addBands(afviImgA)

    # Advanced Vegetation Index 
    def agregateBandsIndexAVI(self, img):    
        aviImgA = img.expression(
            "float((b('nir')* (1.0 - b('red')) * (b('nir') - b('red'))) ** 1/3)")\
                .rename(['avi'])        
        
        return img.addBands(aviImgA)

    # Bare Soil Index 
    def agregateBandsIndexBSI(self,img):    
        bsiImg = img.expression(
            "float(((b('swir1') - b('red')) - (b('nir') + b('blue'))) / ((b('swir1') + b('red')) + (b('nir') + b('blue'))))")\
                .rename(['bsi'])        
        
        return img.addBands(bsiImg)

    # BRBA	Band Ratio for Built-up Area  
    def agregateBandsIndexBRBA(self,img):    
        brbaImg = img.expression(
            "float(b('red') / b('swir1'))")\
                .rename(['brba'])        
        
        return img.addBands(brbaImg)

    # DSWI5	Disease-Water Stress Index 5
    def agregateBandsIndexDSWI5(self,img):    
        dswi5Img = img.expression(
            "float((b('nir') + b('green')) / (b('swir1') + b('red')))")\
                .rename(['dswi5'])        
        
        return img.addBands(dswi5Img)

    # LSWI	Land Surface Water Index
    def agregateBandsIndexLSWI(self,img):    
        lswiImg = img.expression(
            "float((b('nir') - b('swir1')) / (b('nir') + b('swir1')))")\
                .rename(['lswi'])        
        
        return img.addBands(lswiImg)

    # MBI	Modified Bare Soil Index
    def agregateBandsIndexMBI(self,img):    
        mbiImg = img.expression(
            "float(((b('swir1') - b('swir2') - b('nir')) / (b('swir1') + b('swir2') + b('nir'))) + 0.5)")\
                .rename(['mbi'])        
        
        return img.addBands(mbiImg)

    # UI	Urban Index	urban
    def agregateBandsIndexUI(self,img):    
        uiImg = img.expression(
            "float((b('swir2') - b('nir')) / (b('swir2') + b('nir')))")\
                .rename(['ui'])        
        
        return img.addBands(uiImg)

    # OSAVI	Optimized Soil-Adjusted Vegetation Index
    def agregateBandsIndexOSAVI(self,img):    
        osaviImg = img.expression(
            "float(b('nir') - b('red')) / (0.16 + b('nir') + b('red'))")\
                .rename(['osavi'])        
        
        return img.addBands(osaviImg)

    # Normalized Difference Red/Green Redness Index  RI
    def agregateBandsIndexRI(self, img):        
        riImg = img.expression(
            "float(b('nir') - b('green')) / (b('nir') + b('green'))")\
                .rename(['ri'])       
        
        return img.addBands(riImg)    

    # Tasselled Cap - brightness 
    def agregateBandsIndexBrightness(self, img):    
        tasselledCapImg = img.expression(
            "float(0.3037 * b('blue') + 0.2793 * b('green') + 0.4743 * b('red')  + 0.5585 * b('nir') + 0.5082 * b('swir1') +  0.1863 * b('swir2'))")\
                .rename(['brightness']) 
        
        return img.addBands(tasselledCapImg)
    
    # Tasselled Cap - wetness 
    def agregateBandsIndexwetness(self, img):    
        tasselledCapImg = img.expression(
            "float(0.1509 * b('blue') + 0.1973 * b('green') + 0.3279 * b('red')  + 0.3406 * b('nir') + 0.7112 * b('swir1') +  0.4572 * b('swir2'))")\
                .rename(['wetness']) 
        
        return img.addBands(tasselledCapImg)
    
    # Moisture Stress Index (MSI)
    def agregateBandsIndexMSI(self, img):    
        msiImg = img.expression(
            "float( b('nir') / b('swir1'))")\
                .rename(['msi']) 
        
        return img.addBands(msiImg)

    def agregateBandsIndexGVMI(self, img):        
        gvmiImg = img.expression(
                        "float ((b('nir')  + 0.1) - (b('swir1') + 0.02)) / ((b('nir') + 0.1) + (b('swir1') + 0.02))" 
                    ).rename(['gvmi'])     
    
        return img.addBands(gvmiImg) 
    
    def agregateBandsIndexsPRI(self, img):        
        priImg = img.expression(
                                "float((b('green') - b('blue')) / (b('green') + b('blue')))"
                            ).rename(['pri'])   
        spriImg =   priImg.expression(
                                "float((b('pri') + 1) / 2)").rename(['spri'])  
    
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
        contrastnir = textura2.select('nir_contrast')#.rename('contrast') 
        #
        textura2 = img.select('red').glcmTexture(3)  
        contrastred = textura2.select('red_contrast')
        return  img.addBands(contrastnir).addBands(contrastred)

    def agregateBandsgetFractions(self, fractions):         
        # 'bnd_fraction': ['gv_median','npv_median','soil_median'],
        ndfia = fractions.expression(
            "float(b('gv') - b('soil')) / float( b('gv') + 2 * b('npv') + b('soil'))")        
        ndfia = ndfia.add(1).rename('ndfia')
        
        return ndfia

    def CalculateIndice(self, imagem):

        band_feat = [
                "ratio","rvi","ndwi","awei","iia",
                "gcvi","gemi","cvi","gli","shape","afvi",
                "avi","bsi","brba","dswi5","lswi","mbi","ui",
                "osavi","ri","brightness","wetness",
                "nir_contrast","red_contrast"
            ]
        
        # imagem em Int16 com valores inteiros ate 10000        
        imageF = self.agregateBandsgetFractions(imagem)        
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

        return imagem.addBands(imageW.select(band_feat)).addBands(imageF)


    def calculate_indices_x_blocos(self, image):

        
        # band_year = [bnd + '_median' for bnd in self.option['bnd_L']]
        band_year = ['blue_median','green_median','red_median','nir_median','swir1_median','swir2_median', 'gv_median','npv_median','soil_median']
        band_drys = [bnd + '_median_dry' for bnd in self.options['bnd_L']]    
        band_wets = [bnd + '_median_wet' for bnd in self.options['bnd_L']]
        band_std = [bnd + '_stdDev'for bnd in self.options['bnd_L']]
        band_features = [
                    "ratio","rvi","ndwi","awei","iia",
                    "gcvi","gemi","cvi","gli","shape","afvi",
                    "avi","bsi","brba","dswi5","lswi","mbi","ui",
                    "osavi","ri","brightness","wetness",
                    "nir_contrast","red_contrast","ndfia"]
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
        # print("imagem bandas final ", image_year.bandNames().getInfo())

        image_drys = image.select(band_drys)
        image_drys = image_drys.select(band_drys, self.options['bnd_L'])
        image_drys = self.CalculateIndice(image_drys)
        bnd_corregida = [bnd + '_median_dry' for bnd in band_features]
        image_drys = image_drys.select(band_features, bnd_corregida)
        # print("imagem bandas final ", image_drys.bandNames().getInfo())

        image_wets = image.select(band_wets)
        image_wets = image_wets.select(band_wets, self.options['bnd_L'])
        image_wets = self.CalculateIndice(image_wets)
        bnd_corregida = [bnd + '_median_wet' for bnd in band_features]
        image_wets = image_wets.select(band_features, bnd_corregida)

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
        colecaoPontos = ee.FeatureCollection([])
        # lsNoPtos = []
        
        oneBacia = self.baciasN2.filter(
            ee.Filter.eq('nunivotto3', nomeBacia)).geometry()            


        for anoCount in range(self.options['anoIntInit'], self.options["anoIntFin"] + 1):

            if ((nomeBacia == '765') and (anoCount == 1997)) or (
                (nomeBacia == '759') and (anoCount == 2019)) or (
                (nomeBacia == '7422') and (anoCount == 2004)):

                bandActiva = 'classification_' + str(anoCount)
                # print("banda activa: " + bandActiva)  
                if anoCount == self.options["anoIntFin"]:
                    asset_roisAct = self.options['inAssetROIs'] + "/" + nomeBacia + "_" + nomeBacia + "_" + str(anoCount) + "_c1"
                else:
                    asset_roisAct = self.options['inAssetROIs'] + "/" + nomeBacia + "_" + nomeBacia + "_" + str(anoCount + 1) + "_c1"
                # loading rois with classe
                roisAct = ee.FeatureCollection(asset_roisAct)

                if anoCount >= 2020:
                    imMaskInc = ee.Image.constant(1).rename('incident')
                else:
                    m_asset = self.options['asset_output_mask'] + '/masks_pixels_incidentes_'+ str(anoCount)
                    imMaskInc = ee.Image(m_asset).rename('incident')   


                # map_yearAct = map_yearAct.addBands(imMaskInc) 


                img_recMosaic = self.imgMosaic.filterBounds(oneBacia).filter(
                                            ee.Filter.eq('year', anoCount)).median()   

                img_recMosaic = self.calculate_indices_x_blocos(img_recMosaic)
                print("numero de ptos controle ", roisAct.size().getInfo())
                # opcoes para o sorteio estratificadoBuffBacia
                ptosTemp = img_recMosaic.addBands(imMaskInc).sampleRegions(
                    collection= roisAct,
                    properties= ['class'],
                    scale= 30,
                    tileScale= 8,
                    geometries= True
                )
                # insere informacoes em cada ft
                ptosTemp = ptosTemp.filter(ee.Filter.notNull(['class']))
                # merge com colecoes anteriores
                colecaoPontos = colecaoPontos.merge(ptosTemp)
                
                # sys.exit()
                name_exp = str(nomeBacia) + "_" + str(nomeBacia) + "_" + str(anoCount) +"_c1"  
                self.save_ROIs_toAsset(colecaoPontos, name_exp)        

    
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
    'lsClasse': [3, 4, 12, 15, 18, 21, 22, 33, 29],
    'lsPtos': [3000, 2000, 3000, 1500, 1500, 1000, 1500, 1000, 1000],
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
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',
        # '0': 'solkan1201',
        # '5': 'diegoGmail',
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

listaNameBacias = ['765','759','7422']
cont = gerenciador(0, param)
# revisao da coleção 8 
# https://code.earthengine.google.com/5e8af5ef94684a5769e853ad675fc368

for cc, item_bacia in enumerate(listaNameBacias[:]):
    print(f"# {cc + 1} loading geometry bacia {item_bacia}")     
    objetoMosaic_exportROI = ClassMosaic_indexs_Spectral()
    # geobacia, colAnos, nomeBacia, dict_nameBN4
    objetoMosaic_exportROI.iterate_bacias(item_bacia)
    cont = gerenciador(cont, param)

    