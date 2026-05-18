#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import gee
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
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
# sys.setrecursionlimit(1000000000)

#============================================================
#============== FUNCTIONS FO SPECTRAL INDEX =================
#region All functions index spectral 
# Ratio Vegetation Index
def agregateBandsIndexRATIO(img):

    ratioImg = img.expression("float(b('nir') / b('red'))")\
                            .rename(['ratio']).toUint16()      

    return img.addBands(ratioImg)

# Ratio Vegetation Index
def agregateBandsIndexRVI(img):

    rviImg = img.expression("float(b('red') / b('nir'))")\
                            .rename(['rvi']).toUint16()       

    return img.addBands(rviImg)

def agregateBandsIndexNDVI(img):

    ndviImg = img.expression("float(b('nir') - b('red')) / (b('nir') + b('red'))")\
                            .rename(['ndvi']).toUint16()       

    return img.addBands(ndviImg)

def agregateBandsIndexWater(img):

    ndwiImg = img.expression("float(b('nir') - b('swir2')) / (b('nir') + b('swir2'))")\
                            .rename(['ndwi']).toUint16()       

    return img.addBands(ndwiImg)


def AutomatedWaterExtractionIndex(img):    
    awei = img.expression(
                        "float(4 * (b('green') - b('swir2')) - (0.25 * b('nir') + 2.75 * b('swir1')))"
                    ).rename("awei").toFloat()          
    
    return img.addBands(awei)

def IndiceIndicadorAgua(img):    
    iiaImg = img.expression(
                        "float((b('green') - 4 *  b('nir')) / (b('green') + 4 *  b('nir')))"
                    ).rename("iia").toFloat()
    
    return img.addBands(iiaImg)

def agregateBandsIndexLAI(img):
    laiImg = img.expression(
        "float(3.618 * (b('evi') - 0.118))")\
            .rename(['lai']).toFloat()

    return img.addBands(laiImg)    

def agregateBandsIndexGCVI(img):    
    gcviImgA = img.expression(
        "float(b('nir')) / (b('green')) - 1")\
            .rename(['gcvi']).toFloat()        
    
    return img.addBands(gcviImgA)

# Global Environment Monitoring Index GEMI 
def agregateBandsIndexGEMI(img):    
    # "( 2 * ( NIR ^2 - RED ^2) + 1.5 * NIR + 0.5 * RED ) / ( NIR + RED + 0.5 )"
    gemiImgA = img.expression(
        "float((2 * (b('nir') * b('nir') - b('red') * b('red')) + 1.5 * b('nir') + 0.5 * b('red')) / (b('nir') + b('green') + 0.5) )")\
            .rename(['gemi']).toFloat()        
    
    return img.addBands(gemiImgA)

# Chlorophyll vegetation index CVI
def agregateBandsIndexCVI(img):    
    cviImgA = img.expression(
        "float(b('nir') * (b('green') / (b('blue') * b('blue'))))")\
            .rename(['cvi']).toFloat()        
    
    return img.addBands(cviImgA)

# Green leaf index  GLI
def agregateBandsIndexGLI(img):    
    gliImg = img.expression(
        "float((2 * b('green') - b('red') - b('blue')) / (2 * b('green') - b('red') - b('blue')))")\
            .rename(['gli']).toFloat()        
    
    return img.addBands(gliImg)

# Shape Index  IF 
def agregateBandsIndexShapeI(img):    
    shapeImgA = img.expression(
        "float((2 * b('red') - b('green') - b('blue')) / (b('green') - b('blue')))")\
            .rename(['shape']).toFloat()       
    
    return img.addBands(shapeImgA)

# Aerosol Free Vegetation Index (2100 nm) 
def agregateBandsIndexAFVI(img):    
    afviImgA = img.expression(
        "float((b('nir') - 0.5 * b('swir2')) / (b('nir') + 0.5 * b('swir2')))")\
            .rename(['afvi']).toFloat()        
    
    return img.addBands(afviImgA)

# Advanced Vegetation Index 
def agregateBandsIndexAVI(img):    
    aviImgA = img.expression(
        "float((b('nir')* (1.0 - b('red')) * (b('nir') - b('red'))) ** 1/3)")\
            .rename(['avi']).toFloat()        
    
    return img.addBands(aviImgA)

# Bare Soil Index 
def agregateBandsIndexBSI(img):    
    bsiImg = img.expression(
        "float(((b('swir1') - b('red')) - (b('nir') + b('blue'))) / ((b('swir1') + b('red')) + (b('nir') + b('blue'))))")\
            .rename(['bsi']).toFloat()        
    
    return img.addBands(bsiImg)

# BRBA	Band Ratio for Built-up Area  
def agregateBandsIndexBRBA(img):    
    brbaImg = img.expression(
        "float(b('red') / b('swir1'))")\
            .rename(['brba']).toFloat()        
    
    return img.addBands(brbaImg)

# DSWI5	Disease-Water Stress Index 5
def agregateBandsIndexDSWI5(img):    
    dswi5Img = img.expression(
        "float((b('nir') + b('green')) / (b('swir1') + b('red')))")\
            .rename(['dswi5']).toFloat()        
    
    return img.addBands(dswi5Img)

# LSWI	Land Surface Water Index
def agregateBandsIndexLSWI(img):    
    lswiImg = img.expression(
        "float((b('nir') - b('swir1')) / (b('nir') + b('swir1')))")\
            .rename(['lswi']).toFloat()        
    
    return img.addBands(lswiImg)

# MBI	Modified Bare Soil Index
def agregateBandsIndexMBI(img):    
    mbiImg = img.expression(
        "float(((b('swir1') - b('swir2') - b('nir')) / (b('swir1') + b('swir2') + b('nir'))) + 0.5)")\
            .rename(['mbi']).toFloat()       
    
    return img.addBands(mbiImg)

# UI	Urban Index	urban
def agregateBandsIndexUI(img):    
    uiImg = img.expression(
        "float((b('swir2') - b('nir')) / (b('swir2') + b('nir')))")\
            .rename(['ui']).toFloat()        
    
    return img.addBands(uiImg)

# OSAVI	Optimized Soil-Adjusted Vegetation Index
def agregateBandsIndexOSAVI(img):    
    osaviImg = img.expression(
        "float(b('nir') - b('red')) / (0.16 + b('nir') + b('red'))")\
            .rename(['osavi']).toFloat()        
    
    return img.addBands(osaviImg)

# Normalized Difference Red/Green Redness Index  RI
def agregateBandsIndexRI(img):        
    riImg = img.expression(
        "float(b('nir') - b('green')) / (b('nir') + b('green'))")\
            .rename(['ri']).toFloat()       
    
    return img.addBands(riImg)    

# Tasselled Cap - brightness 
def agregateBandsIndexBrightness(img):    
    tasselledCapImg = img.expression(
        "float(0.3037 * b('blue') + 0.2793 * b('green') + 0.4743 * b('red')  + 0.5585 * b('nir') + 0.5082 * b('swir1') +  0.1863 * b('swir2'))")\
            .rename(['brightness']).toFloat() 
    
    return img.addBands(tasselledCapImg)

# Tasselled Cap - wetness 
def agregateBandsIndexwetness(img):    
    tasselledCapImg = img.expression(
        "float(0.1509 * b('blue') + 0.1973 * b('green') + 0.3279 * b('red')  + 0.3406 * b('nir') + 0.7112 * b('swir1') +  0.4572 * b('swir2'))")\
            .rename(['wetness']).toFloat() 
    
    return img.addBands(tasselledCapImg)

# Moisture Stress Index (MSI)
def agregateBandsIndexMSI(img):    
    msiImg = img.expression(
        "float( b('nir') / b('swir1'))")\
            .rename(['msi']).toFloat() 
    
    return img.addBands(msiImg)

def agregateBandsIndexGVMI(img):        
    gvmiImg = img.expression(
                    "float ((b('nir')  + 0.1) - (b('swir1') + 0.02)) / ((b('nir') + 0.1) + (b('swir1') + 0.02))" 
                ).rename(['gvmi']).toFloat()     

    return img.addBands(gvmiImg) 

def agregateBandsIndexsPRI(img):        
    priImg = img.expression(
                            "float((b('green') - b('blue')) / (b('green') + b('blue')))"
                        ).rename(['pri'])   
    spriImg =   priImg.expression(
                            "float((b('pri') + 1) / 2)"
                        ).rename(['spri']).toFloat() 

    return img.addBands(spriImg)


def agregateBandsIndexCO2Flux(img):        
    ndviImg = img.expression("float(b('nir') - b('swir2')) / (b('nir') + b('swir2'))").rename(['ndvi']) 
    
    priImg = img.expression(
                            "float((b('green') - b('blue')) / (b('green') + b('blue')))"
                        ).rename(['pri'])   
    spriImg =   priImg.expression(
                            "float((b('pri') + 1) / 2)").rename(['spri'])

    co2FluxImg = ndviImg.multiply(spriImg).rename(['co2flux']).toFloat()   
    
    return img.addBands(co2FluxImg)


def agregateBandsTexturasGLCM(img):        
    img = img.toInt()                
    textura2 = img.select('nir').glcmTexture(3)  
    contrastnir = textura2.select('nir_contrast').toFloat()
    #
    textura2 = img.select('red').glcmTexture(3)  
    contrastred = textura2.select('red_contrast').toFloat()
    return  img.addBands(contrastnir).addBands(contrastred)

#endregion


lst_bandExt = [
        'blue_min','blue_stdDev','green_min','green_stdDev','green_median_texture', 
        'red_min', 'red_stdDev','nir_min','nir_stdDev', 'swir1_min', 'swir1_stdDev', 
        'swir2_min', 'swir2_stdDev'
    ]

def process_re_escalar_img (imgA):
    imgNormal = imgA.select(['slope'], ['slopeA']).divide(1500).toFloat()
    bandMos = copy.deepcopy(arqParams.featureBands)
    bandMos.remove('slope')
    imgEscalada = imgA.select(bandMos).divide(10000);

    return imgA.select(['slope']).addBands(imgEscalada.toFloat()).addBands(imgNormal)
    #return imgEscalada.toFloat().addBands(imgNormal)

def CalculateIndice(imagem):

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
    # imageW = copy.deepcopy(imagem).divide(10000)

    imageW = agregateBandsIndexRATIO(imagem)  #
    imageW = agregateBandsIndexRVI(imageW)    #    
    imageW = agregateBandsIndexWater(imageW)  #      
    imageW = AutomatedWaterExtractionIndex(imageW)  #      
    imageW = IndiceIndicadorAgua(imageW)    #      
    imageW = agregateBandsIndexGCVI(imageW)   #   
    imageW = agregateBandsIndexGEMI(imageW)
    imageW = agregateBandsIndexCVI(imageW) 
    imageW = agregateBandsIndexGLI(imageW) 
    imageW = agregateBandsIndexShapeI(imageW) 
    imageW = agregateBandsIndexAFVI(imageW) 
    imageW = agregateBandsIndexAVI(imageW) 
    imageW = agregateBandsIndexBSI(imageW) 
    imageW = agregateBandsIndexBRBA(imageW) 
    imageW = agregateBandsIndexDSWI5(imageW) 
    imageW = agregateBandsIndexLSWI(imageW) 
    imageW = agregateBandsIndexMBI(imageW) 
    imageW = agregateBandsIndexUI(imageW) 
    imageW = agregateBandsIndexRI(imageW) 
    imageW = agregateBandsIndexOSAVI(imageW)  #     
    imageW = agregateBandsIndexwetness(imageW)   #   
    imageW = agregateBandsIndexBrightness(imageW)  #       
    imageW = agregateBandsTexturasGLCM(imageW)     #

    return imagem.addBands(imageW).select(band_feat)

def calculate_indices_x_blocos(image):

    bnd_L = ['blue','green','red','nir','swir1','swir2']        
    # band_year = [bnd + '_median' for bnd in self.option['bnd_L']]
    band_year = [
            'blue_median','green_median','red_median',
            'nir_median','swir1_median','swir2_median'
        ]
    band_drys = [bnd + '_median_dry' for bnd in bnd_L]    
    band_wets = [bnd + '_median_wet' for bnd in bnd_L]
    band_std = [bnd + '_stdDev'for bnd in bnd_L]
    band_features = [
                "ratio","rvi","ndwi","awei","iia",
                "gcvi","gemi","cvi","gli","shape","afvi",
                "avi","bsi","brba","dswi5","lswi","mbi","ui",
                "osavi","ri","brightness","wetness",
                "nir_contrast","red_contrast"] # ,"ndfia"
    # band_features.extend(self.option['bnd_L'])        
    
    image_year = image.select(band_year)
    image_year = image_year.select(band_year, bnd_L)
    # print("imagem bandas index ")    
    # print("  ", image_year.bandNames().getInfo())
    image_year = CalculateIndice(image_year)    
    # print("imagem bandas index ")    
    # print("  ", image_year.bandNames().getInfo())
    bnd_corregida = [bnd + '_median' for bnd in band_features]
    image_year = image_year.select(band_features, bnd_corregida)
    # print("imagem bandas final median \n ", image_year.bandNames().getInfo())

    image_drys = image.select(band_drys)
    image_drys = image_drys.select(band_drys, bnd_L)
    image_drys = CalculateIndice(image_drys)
    bnd_corregida = [bnd + '_median_dry' for bnd in band_features]
    image_drys = image_drys.select(band_features, bnd_corregida)
    # print("imagem bandas final dry \n", image_drys.bandNames().getInfo())

    image_wets = image.select(band_wets)
    image_wets = image_wets.select(band_wets, bnd_L)
    image_wets = CalculateIndice(image_wets)
    bnd_corregida = [bnd + '_median_wet' for bnd in band_features]
    image_wets = image_wets.select(band_features, bnd_corregida)
    # print("imagem bandas final wet \n ", image_wets.bandNames().getInfo())   

    image_year =  image_year.addBands(image_drys).addBands(image_wets) 
    return image_year

#endregion
#============================================================



param = {    
    'bioma': "CAATINGA", #nome do bioma setado nos metadados
    'biomas': ["CAATINGA","CERRADO", "MATAATLANTICA"],
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVY/',
    'assetROIs': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2clusterNN'},
    'assetROIsExt': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2manualNN'}, 
    'assetROIgrade': {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisGradesgrouped'},   
    'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisredDJoinsbyBaciaNN',
    'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisJoinedBaGrNN', 
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21],
    'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    'version': 31,
    'anoInicial': 1985,
    'anoFinal': 2023,
    'sufix': "_01",    
    'lsBandasMap': [],
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta' : {
        '0': 'caatinga01',   # 
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '25': 'solkan1201',    
        '30': 'solkanGeodatin',
        '35': 'diegoUEFS',
        # '32': 'superconta'     
    },
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
    'dict_classChangeBa': arqParams.dictClassRepre

}
# print(param.keys())
print("vai exportar em ", param['assetOut'])
# print(param['conta'].keys())
bandNames = [
    "swir1_stdDev_1","nir_stdDev_1","green_stdDev_1","ratio_median_dry","gli_median_wet","dswi5_median_dry",
    "ri_median","osavi_median","swir2_min","shape_median","mbi_median_dry","wetness_median_dry","green_median_texture_1",
    "iia_median_wet","slopeA_1","brba_median_dry","nir_median","lswi_median_wet","red_min","rvi_median","green_min",
    "gcvi_median_dry","shape_median_dry","cvi_median_dry","blue_median_dry","mbi_median","nir_median_dry_contrast",
    "swir2_median_wet","ui_median_wet","red_median_wet","avi_median","nir_stdDev","swir1_stdDev","red_median_dry",
    "gemi_median","osavi_median_dry","blue_median_dry_1","swir2_median_dry_1","brba_median","ratio_median",
    "gli_median_dry","blue_min_1","wetness_median","green_median_wet","blue_median_wet_1","brightness_median_wet",
    "blue_min","blue_median","red_median_contrast","swir1_min_1","evi_median","blue_stdDev_1","lswi_median_dry",
    "blue_median_wet","cvi_median","red_stdDev_1","shape_median_wet","red_median_dry_1","swir2_median_wet_1",
    "dswi5_median_wet","red_median_wet_1","afvi_median","ndwi_median","avi_median_wet","gli_median","evi_median_wet",
    "nir_median_dry","gvmi_median","cvi_median_wet","swir2_min_1","iia_median","ndwi_median_dry","green_min_1",
    "ri_median_dry","osavi_median_wet","green_median_dry","ui_median_dry","red_stdDev","nir_median_wet_1",
    "swir1_median_dry_1","red_median_1","nir_median_dry_1","swir1_median_wet","blue_stdDev","bsi_median",
    "swir1_median","swir2_median","gvmi_median_dry","red_median","gemi_median_wet","lswi_median",
    "brightness_median_dry","awei_median_wet","nir_min","afvi_median_wet","nir_median_wet","evi_median_dry",
    "swir2_median_1","ndwi_median_wet","ratio_median_wet","swir2_stdDev","gcvi_median","ui_median","rvi_median_wet",
    "green_median_wet_1","ri_median_wet","nir_min_1","rvi_median_1","swir1_median_dry","blue_median_1","green_median_1",
    "avi_median_dry","gvmi_median_wet","wetness_median_wet","swir1_median_1","dswi5_median","swir2_stdDev_1",
    "awei_median","red_min_1","mbi_median_wet","brba_median_wet","green_stdDev","green_median_texture","swir1_min",
    "awei_median_dry","swir1_median_wet_1","gemi_median_dry","nir_median_1","red_median_dry_contrast","bsi_median_1",
    "bsi_median_2","nir_median_contrast","green_median_dry_1","afvi_median_dry","gcvi_median_wet","iia_median_dry",
    "brightness_median","green_median","swir2_median_dry"
]

bandasComuns = [
    'slope', 'blue_median', 'blue_median_wet', 'blue_median_dry', 'blue_min', 'blue_stdDev', 'green_median', 
    'green_median_wet', 'green_median_dry', 'green_min', 'green_stdDev', 'green_median_texture', 'red_median', 
    'red_median_wet', 'red_median_dry', 'red_min', 'red_stdDev', 'nir_median', 'nir_median_wet', 'nir_median_dry', 
    'nir_min', 'nir_stdDev', 'swir1_median', 'swir1_median_wet', 'swir1_median_dry', 'swir1_min', 'swir1_stdDev', 
    'swir2_median', 'swir2_median_wet', 'swir2_median_dry', 'swir2_min', 'swir2_stdDev', 'slopeA', 'ratio_median', 
    'rvi_median', 'ndwi_median', 'awei_median', 'iia_median', 'gcvi_median', 'gemi_median', 'cvi_median', 'gli_median', 
    'shape_median', 'afvi_median', 'avi_median', 'bsi_median', 'brba_median', 'dswi5_median', 'lswi_median', 'mbi_median', 
    'ui_median', 'osavi_median', 'ri_median', 'brightness_median', 'wetness_median', 'nir_contrast_median', 
    'red_contrast_median', 'ratio_median_dry', 'rvi_median_dry', 'ndwi_median_dry', 'awei_median_dry', 'iia_median_dry', 
    'gcvi_median_dry', 'gemi_median_dry', 'cvi_median_dry', 'gli_median_dry', 'shape_median_dry', 'afvi_median_dry', 
    'avi_median_dry', 'bsi_median_dry', 'brba_median_dry', 'dswi5_median_dry', 'lswi_median_dry', 'mbi_median_dry', 
    'ui_median_dry', 'osavi_median_dry', 'ri_median_dry', 'brightness_median_dry', 'wetness_median_dry', 
    'nir_contrast_median_dry', 'red_contrast_median_dry', 'ratio_median_wet', 'rvi_median_wet', 
    'ndwi_median_wet', 'awei_median_wet', 'iia_median_wet', 'gcvi_median_wet', 'gemi_median_wet', 
    'cvi_median_wet', 'gli_median_wet', 'shape_median_wet', 'afvi_median_wet', 'avi_median_wet', 
    'bsi_median_wet', 'brba_median_wet', 'dswi5_median_wet', 'lswi_median_wet', 'mbi_median_wet', 
    'ui_median_wet', 'osavi_median_wet', 'ri_median_wet', 'brightness_median_wet', 'wetness_median_wet', 
    'nir_contrast_median_wet', 'red_contrast_median_wet'
]
bandasComunsCorr = [
    'slope', 'blue_median_1', 'blue_median_wet_1', 'blue_median_dry_1', 'blue_min_1', 'blue_stdDev_1', 'green_median_1', 
    'green_median_wet_1', 'green_median_dry_1', 'green_min_1', 'green_stdDev_1', 'green_median_texture_1', 'red_median_1', 
    'red_median_wet_1', 'red_median_dry_1', 'red_min_1', 'red_stdDev_1', 'nir_median_1', 'nir_median_wet_1', 'nir_median_dry_1', 
    'nir_min_1', 'nir_stdDev_1', 'swir1_median_1', 'swir1_median_wet_1', 'swir1_median_dry_1', 'swir1_min_1', 'swir1_stdDev_1', 
    'swir2_median_1', 'swir2_median_wet_1', 'swir2_median_dry_1', 'swir2_min_1', 'swir2_stdDev_1', 'slopeA_1', 'ratio_median', 
    'rvi_median', 'ndwi_median', 'awei_median', 'iia_median', 'gcvi_median', 'gemi_median', 'cvi_median', 'gli_median', 
    'shape_median', 'afvi_median', 'avi_median', 'bsi_median', 'brba_median', 'dswi5_median', 'lswi_median', 'mbi_median', 
    'ui_median', 'osavi_median', 'ri_median', 'brightness_median', 'wetness_median', 'nir_contrast_median', 
    'red_contrast_median', 'ratio_median_dry', 'rvi_median_dry', 'ndwi_median_dry', 'awei_median_dry', 'iia_median_dry', 
    'gcvi_median_dry', 'gemi_median_dry', 'cvi_median_dry', 'gli_median_dry', 'shape_median_dry', 'afvi_median_dry', 
    'avi_median_dry', 'bsi_median_dry', 'brba_median_dry', 'dswi5_median_dry', 'lswi_median_dry', 'mbi_median_dry', 
    'ui_median_dry', 'osavi_median_dry', 'ri_median_dry', 'brightness_median_dry', 'wetness_median_dry', 
    'nir_contrast_median_dry', 'red_contrast_median_dry', 'ratio_median_wet', 'rvi_median_wet', 
    'ndwi_median_wet', 'awei_median_wet', 'iia_median_wet', 'gcvi_median_wet', 'gemi_median_wet', 
    'cvi_median_wet', 'gli_median_wet', 'shape_median_wet', 'afvi_median_wet', 'avi_median_wet', 
    'bsi_median_wet', 'brba_median_wet', 'dswi5_median_wet', 'lswi_median_wet', 'mbi_median_wet', 
    'ui_median_wet', 'osavi_median_wet', 'ri_median_wet', 'brightness_median_wet', 'wetness_median_wet', 
    'nir_contrast_median_wet', 'red_contrast_median_wet'
]
#============================================================
#========================METODOS=============================
#============================================================

def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
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
#exporta a imagem classificada para o asset
def processoExportar(mapaRF, regionB, nameB):
    nomeDesc = 'BACIA_'+ str(nameB)
    idasset =  param['assetOut'] + nomeDesc
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId':idasset, 
        'region':regionB.getInfo(), #['coordinates']
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

def process_reduce_ROIsXclass(featColROIs, featColROIsbase ,lstclassVal, dfProp, mbacia):
    # 12': 1304, '15': 1247, '18': 1280, '22': 1635, '3': 1928, '33': 1361, '4': 1378
    dictQtLimit = {
        3: 600,
        4: 2500,
        12: 600,
        15: 1200,
        18: 900,
        21: 1200,
        22: 1000,
        33: 400
    }
    nFeatColROIs = ee.FeatureCollection([])
    lstBac21 = ["76111","76116","7742","757","758","759","771","772","773","775","776","777"]
    # lstBac3 = ['766', '776', '764', '765', '7621', '744']
    lstLitoral = ['758','761','756','755','754', '76111']

    for ccclass in lstclassVal:
        # print("classse ", ccclass)
        if ccclass in [15, 18]:
            myClass = 21
        else:
            myClass = int(ccclass)
        try:
            valpropCC = dfProp[dfProp['classe'] == myClass]['area_prob'].values[0]
            if ccclass == 21 and str(mbacia) not in ['771', '7613', '7617', '7615']:
                valpropCC += 0.1
            if str(mbacia) in ['771', '7613', '7617', '7615'] and ccclass == 4:
                valpropCC += 0.15

            if str(mbacia) in ['776', '757', '758'] and ccclass == 3:   # 7622
                valpropCC += 0.1

            if ccclass == 3:
                if valpropCC < 0.05:
                    valpropCC = 0.15
            if str(mbacia) in lstBac21:
                if ccclass == 21:
                    valpropCC += 0.25
            
        except:
            valpropCC = 0.01
        
        if str(mbacia) in ['7614','7421', '744'] and ccclass == 4:
            valpropCC = 0.3
            dictQtLimit[ccclass] = 1500
        if str(mbacia) in ['753', '752'] and ccclass == 4:
            valpropCC = 0.2
            dictQtLimit[ccclass] = 800
        if str(mbacia) in lstLitoral and ccclass == 4:
            valpropCC = 0.1
            dictQtLimit[ccclass] = 900
            if str(mbacia) in ['76111']:
                valpropCC = 0.1
                dictQtLimit[ccclass] = 650


        # print(" valpropCC ", valpropCC)
        tmpROIs = featColROIs.filter(ee.Filter.eq('class', int(ccclass))).randomColumn('random')
        threhold = ee.Number(dictQtLimit[ccclass]).multiply(valpropCC).divide(tmpROIs.size())
        tmpROIs = tmpROIs.filter(ee.Filter.lte('random', threhold))
        
        tmpROIff = featColROIsbase.filter(ee.Filter.eq('class', int(ccclass))).randomColumn('random')
        threhold2 = ee.Number(dictQtLimit[ccclass]).divide(tmpROIff.size())
        tmpROIff = tmpROIff.filter(ee.Filter.lte('random', threhold2))
        # if ccclass  == 4:
        #     print("size class 4 ", tmpROIs.size().getInfo())
        #     print("size class 4 ", tmpROIff.size().getInfo(), "  ", valpropCC)

        if str(mbacia) in ['771', '7613', '7617', '7615'] and ccclass == 12:
            tmpROIs = tmpROIs.limit(200)
            tmpROIff = tmpROIff.limit(200)
        if str(mbacia) in ['757', '758'] and ccclass == 12:
            tmpROIs = tmpROIs.limit(350)
            tmpROIff = tmpROIff.limit(350)
        if ccclass == 22:
            tmpROIs = tmpROIs.limit(100)
            tmpROIff = tmpROIff.limit(100)
        if ccclass == 4 and str(mbacia) in lstBac21:
            tmpROIs = tmpROIs.limit(1000)
            tmpROIff = tmpROIff.limit(1000)

        nFeatColROIs = nFeatColROIs.merge(tmpROIs).merge(tmpROIff)
    
    return nFeatColROIs

def GetPolygonsfromFolder(nBacias, lstClasesBacias, yyear):    
    # print("lista de classe ", lstClasesBacias)
    getlistPtos = ee.data.getList(param['assetROIs'])
    getlistPtosExt = ee.data.getList(param['assetROIsExt'])
    ColectionPtos = ee.FeatureCollection([])
    dictQtLimit = {
        3: 800,
        4: 5500,
        12: 1600,
        15: 1200,
        18: 800,
        21: 1500,
        22: 1200,
        33: 400
    }
    for idAsset in getlistPtos:         
        path_ = idAsset.get('id')
        lsFile =  path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')
        # print("cole", str(newName[0]))
        if str(newName[0]) in nBacias and str(newName[1]) == str(yyear):
            # print(f"reading year {yyear} from basin {name}")
            FeatTemp = ee.FeatureCollection(path_)
             # print(FeatTemp.size().getInfo())
            ColectionPtos = ColectionPtos.merge(FeatTemp) # .select(bandasComunsCorr)
    nFeatColROIs = ee.FeatureCollection([])
    for ccclass in lstClasesBacias:
        tmpROIs = ColectionPtos.filter(ee.Filter.eq('class', int(ccclass))).randomColumn('random')
        threhold = ee.Number(dictQtLimit[ccclass]).divide(tmpROIs.size())
        tmpROIs = tmpROIs.filter(ee.Filter.lte('random', threhold))
        nFeatColROIs = nFeatColROIs.merge(tmpROIs)

    return  ee.FeatureCollection(nFeatColROIs)


def FiltrandoROIsXimportancia(nROIs, baciasAll, nbacia):

    limitCaat = ee.FeatureCollection('users/CartasSol/shapes/nCaatingaBff3000')
    # selecionando todas as bacias vizinhas 
    baciasB = baciasAll.filter(ee.Filter.eq('nunivotto3', nbacia))
    # limitando pelo bioma novo com buffer
    baciasB = baciasB.geometry().buffer(2000).intersection(limitCaat.geometry())
    # filtrando todo o Rois pela área construida 
    redROIs = nROIs.filterBounds(baciasB)
    mhistogram = redROIs.aggregate_histogram('class').getInfo()
    ROIsEnd = ee.FeatureCollection([])
    
    roisT = ee.FeatureCollection([])
    for kk, vv in mhistogram.items():
        print("class {}: == {}".format(kk, vv))
        
        roisT = redROIs.filter(ee.Filter.eq('class', int(kk)))
        roisT =roisT.randomColumn()
        
        if int(kk) == 4:
            roisT = roisT.filter(ee.Filter.gte('random',0.5))
            # print(roisT.size().getInfo())

        elif int(kk) != 21:
            roisT = roisT.filter(ee.Filter.lte('random',0.9))
            # print(roisT.size().getInfo())

        ROIsEnd = ROIsEnd.merge(roisT)
        # roisT = None
    
    return ROIsEnd

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

lstSat = ["l5","l7","l8"];
pathJson = getPathCSV("regJSON/")
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
imagens_mosaico = ee.ImageCollection(param['asset_mosaic']).filter(
                            ee.Filter.inList('biome', param['biomas'])).filter(
                                ee.Filter.inList('satellite', lstSat)).filterBounds(
                                    ftcol_bacias.geometry()).select(
                                            arqParams.featuresreduce)
# process_normalized_img
imagens_mosaic = imagens_mosaico.map(lambda img: process_re_escalar_img(img))          
# ftcol_baciasbuffer = ee.FeatureCollection(param['asset_bacias_buffer'])
# print(imagens_mosaic.first().bandNames().getInfo())
#nome das bacias que fazem parte do bioma7619
nameBacias = arqParams.listaNameBacias
print("carregando {} bacias hidrograficas ".format(len(nameBacias)))
# sys.exit()
#lista de anos
list_anos = [k for k in range(param['anoInicial'], param['anoFinal'] + 1)]
print('lista de bandas anos entre 1985 e 2023')
param['lsBandasMap'] = ['classification_' + str(kk) for kk in list_anos]
print(param['lsBandasMap'])

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
bandNames = ['awei_median_dry', 'blue_stdDev', 'brightness_median', 'cvi_median_dry',]
a_file = open(pathJson + "filt_lst_features_selected_spIndC9.json", "r")
dictFeatureImp = json.load(a_file)
# print("dict Features ",dictFeatureImp.keys())
b_file = open(pathJson +  "regBacia_Year_hiperPmtrosTuningfromROIs2Y.json", 'r')
dictHiperPmtTuning = json.load(b_file)

def iterandoXBacias( _nbacia, myModel, makeProb):
    exportatROIS = False
    classifiedRF = None;
    # selectBacia = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).first()
    # https://code.earthengine.google.com/2f8ea5070d3f081a52afbcfb7a7f9d25 

    dfareasCC = pd.read_csv('areaXclasse_CAATINGA_Col71_red.csv')
    print("df areas CC ", dfareasCC.columns)
    dfareasCC = dfareasCC[dfareasCC['Bacia'] == _nbacia]
    print(" dfareasCC shape table ", dfareasCC.shape)
    
    baciabuffer = ee.FeatureCollection(param['asset_bacias_buffer']).filter(
                            ee.Filter.eq('nunivotto3', _nbacia)).first().geometry()
    
    lsNamesBaciasViz = arqParams.dictBaciasViz[_nbacia]
    print("lista de Bacias vizinhas", lsNamesBaciasViz)
    lstSoViz = [kk for kk in lsNamesBaciasViz if kk != _nbacia]
    print("lista de bacias ", lstSoViz)
    # lista de classe por bacia 
    lstClassesUn = param['dict_classChangeBa'][_nbacia]
    # sys.exit()
    imglsClasxanos = ee.Image().byte()
    imglsClasxanos_prob = ee.Image().byte()
    mydict = None
    pmtroClass = copy.deepcopy(param['pmtGTB'])
    # print("area ", baciabuffer.area(0.1).getInfo())
    bandas_imports = []
    for cc, ano in enumerate(list_anos[:]):        
        #se o ano for 2018 utilizamos os dados de 2017 para fazer a classificacao
        bandActiva = 'classification_' + str(ano)        
        print( "banda activa: " + bandActiva) 

        if ano < 2022:
            dfareasccYY = dfareasCC[dfareasCC['year'] == ano][['area', 'classe']]
            total = dfareasccYY['area'].sum()
            dfareasccYY['area_prob'] = dfareasccYY['area'] / total
            # print(" ", dfareasccYY.head(9))

        if ano < 2023:
            keyDictFeat = _nbacia + "_" + str(ano) 
            bandas_lst = dictFeatureImp[keyDictFeat][:]
            # print(lsNamesBacias)
            if (_nbacia in ['778']) or (_nbacia == '764' and ano == 1995):
                print(" entrou a coletar")
                ROIs_toTrain = GetPolygonsfromFolder(lsNamesBaciasViz, lstClassesUn, ano) 
                
            else:
                nameFeatROIs = 'joined_ROIs_' + _nbacia + "_" + str(ano) + '_wl'
                print("loading Rois JOINS = ", nameFeatROIs)
                ROIs_toTrain = ee.FeatureCollection(param['asset_joinsGrBa'] + '/' + nameFeatROIs)       
                ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.inList('class', lstClassesUn))                 
                ROIs_toTrainViz = GetPolygonsfromFolder(lstSoViz, lstClassesUn, ano)
                ROIs_toTrain = process_reduce_ROIsXclass(ROIs_toTrain, ROIs_toTrainViz, lstClassesUn, dfareasccYY, _nbacia)
                ROIs_toTrain = ROIs_toTrain.map(lambda feat: feat.set('class', ee.Number(feat.get('class')).toInt8()))

        # sys.exit()
        # excluindo a classe 12
        if '745' == _nbacia:
            ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.neq('class', 12))
        # bandas_ROIs = [kk for kk in ROIs_toTrain.first().propertyNames().getInfo()]  
        # print()    
        # ROIs_toTrain  = ROIs_toTrain.filter(ee.Filter.notNull(bandasComuns))
        if exportatROIS:
            save_ROIs_toAsset(ROIs_toTrain, nameFeatROIs)

        else:
        
            if param['anoInicial'] == ano : #or ano == 2021      
                # print("lista de bandas loaded \n ", bandas_lst)      
                # pega os dados de treinamento utilizando a geometria da bacia com buffer           
                print(" Distribuição dos pontos na bacia << {} >>".format(_nbacia))
                # print(ROIs_toTrain.first().getInfo())
                # print(" ")
                print("===  {}  ===".format(ROIs_toTrain.aggregate_histogram('class').getInfo()))            
                # ===  {'12': 1304, '15': 1247, '18': 1280, '22': 1635, '3': 1928, '33': 1361, '4': 1378}  ===
            pass
            #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia    
            colmosaicMapbiomas = imagens_mosaic.filter(ee.Filter.eq('year', ano)
                                        ).filterBounds(baciabuffer).median()

            mosaicMapbiomas = calculate_indices_x_blocos(colmosaicMapbiomas)
            mosaicMapbiomas = colmosaicMapbiomas.addBands(mosaicMapbiomas)
            mosaicMapbiomas = mosaicMapbiomas.select(bandasComuns, bandasComunsCorr)
            # print(mosaicMapbiomas.size().getInfo())
            ################################################################
            # listBandsMosaic = mosaicMapbiomas.bandNames().getInfo()
            # print("bandas do mosaico ", listBandsMosaic)
            # sys.exit()
            # print('NUMERO DE BANDAS MOSAICO ',len(listBandsMosaic) )
            # # if param['anoInicial'] == ano:
            # #     print("bandas ativas ", listBandsMosaic)
            # # for bband in lsAllprop:
            # #     if bband not in listBandsMosaic:
            # #         print("Alerta com essa banda = ", bband)
            # print('bandas importantes ', len(bandas_lst))
            #bandas_filtered = [kk for kk in bandas_lst if kk in listBandsMosaic]  # 
            #bandas_imports = [kk for kk in bandas_filtered if kk in bandas_ROIs]  # 
            bandas_imports = []
            for bandInt in bandas_lst:
                for bndCom in bandasComuns:
                    if bandInt == bndCom:
                        # if param['anoInicial'] == ano :
                            # print("band " + bandInt)
                        bandas_imports.append(bandInt)

            # bandas_imports.remove('class')
            # print("bandas cruzadas <<  ",len(bandas_imports) , " >> ")
            if param['anoInicial'] == ano:
                print("bandas ativas ", bandas_imports)
            # sys.exit()
            # print("        ", ROIs_toTrain.first().propertyNames().getInfo())


            ###############################################################
            # print(ROIs_toTrain.size().getInfo())
            # ROIs_toTrain_filted = ROIs_toTrain.filter(ee.Filter.notNull(bandas_imports))
            # print(ROIs_toTrain_filted.size().getInfo())
            # lsAllprop = ROIs_toTrain_filted.first().propertyNames().getInfo()
            # print('PROPERTIES FEAT = ', lsAllprop)
            #cria o classificador com as especificacoes definidas acima 
            if myModel == "RF":
                classifierRF = ee.Classifier.smileRandomForest(**param['pmtRF']).train(
                                                    ROIs_toTrain, 'class', bandas_imports)            
                classifiedRF = mosaicMapbiomas.classify(classifierRF, bandActiva)
                if makeProb:
                    classifiedRFBprob = mosaicMapbiomas.classify(classifierRF.setOutputMode('MULTIPROBABILITY'))
                    classifiedRFBprob = classifiedRFBprob.arrayReduce(reducer= ee.Reducer.max(), axes= [0])
                    classifiedRFBprob = classifiedRFBprob.multiply(100).byte().rename('prob_'+ str(ano))
                
                    
            # print("parameter loading ", dictHiperPmtTuning[_nbacia])
            # # 'numberOfTrees': 50, 
            # # 'shrinkage': 0.1,    # 
            # pmtroClass['shrinkage'] = dictHiperPmtTuning[_nbacia]['2021'][0]
            # pmtroClass['numberOfTrees'] = dictHiperPmtTuning[_nbacia]['2021'][1]
            # # print("pmtros Classifier ==> ", pmtroClass)
            # # reajusta os parametros 
            # if pmtroClass['numberOfTrees'] > 35 and _nbacia in dictPmtroArv['35']:
            #     pmtroClass['numberOfTrees'] = 35
            # elif pmtroClass['numberOfTrees'] > 50 and _nbacia in dictPmtroArv['50']:
            #     pmtroClass['numberOfTrees'] = 50
            
            # print("===="*10)
            # print("pmtros Classifier Ajustado ==> ", pmtroClass)
            elif myModel == "GTB":
                # ee.Classifier.smileGradientTreeBoost(numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed)
                classifierGTB = ee.Classifier.smileGradientTreeBoost(**pmtroClass).train(
                                                    ROIs_toTrain, 'class', bandas_imports)              
                classifiedGTB = mosaicMapbiomas.classify(classifierGTB, bandActiva)
                if makeProb:
                    classifiedGTBprob = mosaicMapbiomas.classify(classifierGTB.setOutputMode('MULTIPROBABILITY'))
                    classifiedGTBprob = classifiedGTBprob.arrayReduce(reducer= ee.Reducer.max(), axes= [0])
                    classifiedGTBprob = classifiedGTBprob.multiply(100).byte().rename('prob_'+ str(ano))
                
            else:
                # ee.Classifier.libsvm(decisionProcedure, svmType, kernelType, shrinking, degree, gamma, coef0, cost, nu, terminationEpsilon, lossEpsilon, oneClass)
                classifierSVM = ee.Classifier.libsvm(**param['pmtSVM'])\
                                            .train(ROIs_toTrain, 'class', bandas_imports)
                classifiedSVM = mosaicMapbiomas.classify(classifierSVM, bandActiva)
                if makeProb:
                    classifiedSVMBprob = mosaicMapbiomas.classify(classifierSVM.setOutputMode('MULTIPROBABILITY'))
                    classifiedSVMBprob = classifiedSVMBprob.arrayReduce(reducer= ee.Reducer.max(), axes= [0])
                    classifiedSVMBprob = classifiedSVMBprob.multiply(100).byte().rename('prob_'+ str(ano))
                                
                # print("classificando!!!! ")

            # threeClassification  = classifiedRF.addBands(classifiedGTB).addBands(classifiedSVM)
            # threeClassification = threeClassification.reduce(ee.Reducer.mode(1))
            # threeClassification = threeClassification.rename(bandActiva)

            #se for o primeiro ano cria o dicionario e seta a variavel como
            #o resultado da primeira imagem classificada
            print("addicionando classification bands = " , bandActiva)            
            if param['anoInicial'] == ano:
                print ('entrou em 1985, no modelo ', myModel)
                if myModel == "GTB":
                    print("===> ", myModel)    
                    imglsClasxanos = copy.deepcopy(classifiedGTB)            
                    if makeProb:
                        imglsClasxanos_prob = copy.deepcopy(classifiedGTBprob)                        
                    nomec = _nbacia + '_' + 'GTB_col9-v' + str(param['version'])
                elif myModel == "RF":
                    print("===> ", myModel)                
                    imglsClasxanos = copy.deepcopy(classifiedRF)
                    if makeProb:
                        imglsClasxanos_prob = copy.deepcopy(classifiedRFBprob)                        
                    nomec = _nbacia + '_' + 'RF_col9-v' + str(param['version'])      
                else:   
                    imglsClasxanos = copy.deepcopy(classifiedSVM)              
                    if makeProb:
                        imglsClasxanos_prob = copy.deepcopy(classifiedSVMBprob)                        
                    nomec = _nbacia + '_' + 'SVM_col9-v' + str(param['version'])
                
                mydict = {
                    'id_bacia': _nbacia,
                    'version': param['version'],
                    'biome': param['bioma'],
                    'classifier': myModel,
                    'collection': '9.0',
                    'sensor': 'Landsat',
                    'source': 'geodatin',                
                }
                imglsClasxanos = imglsClasxanos.set(mydict)
            #se nao, adiciona a imagem como uma banda a imagem que ja existia
            else:
                # print("Adicionando o mapa do ano  ", ano)
                # print(" ", classifiedGTB.bandNames().getInfo())
                if myModel == "GTB":      
                    imglsClasxanos = imglsClasxanos.addBands(classifiedGTB)          
                    if makeProb:
                        imglsClasxanos_prob = imglsClasxanos_prob.addBands(classifiedGTBprob)                      
                        
                elif myModel == "RF":
                    imglsClasxanos = imglsClasxanos.addBands(classifiedRF) 
                    if makeProb:
                        imglsClasxanos_prob = imglsClasxanos_prob.addBands(classifiedRFBprob)
                         
                else:   
                    imglsClasxanos = imglsClasxanos.addBands(classifiedSVM)             
                    if makeProb:
                        imglsClasxanos_prob = imglsClasxanos_prob.addBands(classifiedSVMBprob)                        
                #           
        
    # i+=1
    # print(param['lsBandasMap'])   
    if not exportatROIS: 
        # seta as propriedades na imagem classificada    
        # print("show names bands of imglsClasxanos ", imglsClasxanos.bandNames().getInfo() )        
        imglsClasxanos = imglsClasxanos.select(param['lsBandasMap'])    
        imglsClasxanos = imglsClasxanos.clip(baciabuffer).set("system:footprint", baciabuffer.coordinates())
        # exporta bacia
        processoExportar(imglsClasxanos, baciabuffer.coordinates(), nomec) 
        if makeProb:
            imglsClasxanos_prob = imglsClasxanos_prob.clip(baciabuffer).set("system:footprint", baciabuffer.coordinates())
            processoExportar(imglsClasxanos_prob, baciabuffer.coordinates(), nomec + '_prob')

                
        
    # sys.exit()


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

# 100 arvores
nameBacias = [
    '745','741', '7422','746','7492','751','752','753',
    '757', '759','7621','7622','763','764','765', '766',
    '767','771','772', '773', '7741','776','7742','775',
    '777','778','744','754','755','756','758', '76111',
    '76116','7612', '7614','7421','7615','7616','7617',
    '7618','7619', '7613'
]

modelo = "GTB"# "GTB"# "RF"
knowMapSaved = False
listBacFalta = []
cont = 0
cont = gerenciador(cont)
for _nbacia in nameBacias[:]:
    if knowMapSaved:
        try:
            nameMap = 'BACIA_' + _nbacia + '_' + 'GTB_col9-v' + str(param['version'])
            imgtmp = ee.Image(param['assetOut'] + nameMap)
            print(" 🚨 loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), " bandas 🚨")
        except:
            listBacFalta.append(_nbacia)
    else:        
        print("-------------------.kmkl-------------------------------------")
        print("--------    classificando bacia " + _nbacia + "-----------------")   
        print("--------------------------------------------------------") 
        iterandoXBacias(_nbacia, modelo, True) 
        arqFeitos.write(_nbacia + '\n')
        cont = gerenciador(cont) 
arqFeitos.close()


if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))