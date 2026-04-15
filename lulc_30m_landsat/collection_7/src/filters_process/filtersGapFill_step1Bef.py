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
import json
import csv
import copy
import sys
import math
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


class processo_gapfill(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Col71/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_v1/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
            'classMapB' : [ 3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,41,42,43,44,45,46,47,48],
            'classNew'  : [ 3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21]
        }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()   

        self.lstbandNames = ['classification_' + str(yy) for yy in range(1985, 2022)]
        self.years = [yy for yy in range(1985, 2022)]
        self.name_imgClass = 'RF_BACIA_' + nameBacia + '_RF_col71'
        listImg = ee.List(self.lstbandNames).map(lambda bandsClass : ee.Image(
                                                self.options['input_asset'] + self.name_imgClass).select(
                                                            ee.String(bandsClass)).remap(self.options['classMapB'], 
                                                                                self.options['classNew']).rename(ee.String(bandsClass)))
        
        # self.imgClass = ee.Image(self.options['input_asset'] + self.name_imgClass)
        # print(listImg.getInfo())
        #########  RECLASSIFICANDO AS CLASSES 15 E 18 PARA 21 #################
        self.imgClass =ee.Image().byte()
        for item in range(len(self.lstbandNames)):
            self.imgClass = self.imgClass.addBands(ee.Image(ee.List(listImg).get(item)))
        self.imgClass = self.imgClass.select(self.lstbandNames)
        # print("todas as bandas ", self.imgClass.bandNames().getInfo())
        # sys.exit()
        self.imgClass = self.imgClass.mask(self.imgClass.neq(0))

        
        self.version = '1'
        
    def dictionary_bands(self, key, value):
        imgT = ee.Algorithms.If(
                        ee.Number(value).eq(2),
                        self.imgClass.select([key]).byte(),
                        ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
                    )
        return ee.Image(imgT)

    def applyGapFill(self, imagemask):

        previousImage = None        
        for cc, bndName in enumerate(self.lstbandNames):
            if cc > 0:
                currentImage = ee.Image(self.imgClass.select(bndName))
                previousImage = ee.Image(previousImage)
                currentImage = currentImage.unmask(
                            previousImage.select([0]))
                previousImage = currentImage.addBands(previousImage)
            else:
                previousImage = ee.Image(self.imgClass.select(bndName))

        imageFilledT0Tn = copy.deepcopy(ee.Image(previousImage))
        # print("image Filled on ", imageFilledT0Tn.bandNames().getInfo())

        # apply the gap fill form tn until t0
        bandNamesReversed = [bnd for bnd in reversed(self.lstbandNames)]
        previousImage = None
        for cc, bndName in enumerate(bandNamesReversed):
            if cc > 0:
                currentImage = imageFilledT0Tn.select(bndName)
                previousImage = ee.Image(previousImage)
                currentImage = currentImage.unmask(
                            previousImage.select(previousImage.bandNames().length().subtract(1)))
                
                previousImage = previousImage.addBands(currentImage)
            else:
                previousImage = ee.Image(imageFilledT0Tn.select(bndName))
                
        imageFilledTnT0 = copy.deepcopy(ee.Image(previousImage))

        return imageFilledTnT0.select(self.lstbandNames)

    def processing_gapfill(self):

        # generate a histogram dictionary of [bandNames, image.bandNames()]
        bandsOccurrence = ee.Dictionary(
            ee.List(self.lstbandNames).cat(self.imgClass.bandNames()).reduce(ee.Reducer.frequencyHistogram())
        )
        # print("bandas de ocorrencias ", bandsOccurrence.getInfo())

        # insert a masked band 
        bandsDictionary = bandsOccurrence.map(lambda pkey, pvalue: self.dictionary_bands(pkey, pvalue))
        # print("dictionary bandas e imagens ", bandsDictionary.keys().getInfo())

        # convert dictionary to image
        myimg = ee.Image().select()
        for bndName in self.lstbandNames:
            myimg = ee.Image(myimg).addBands(bandsDictionary.get(bndName))
        imageAllBands = copy.deepcopy(ee.Image(myimg))

        # apply the gap fill
        imageFilledtnt0 = self.applyGapFill(imageAllBands)
        print("passou")
        # print(imageFilledtnt0.bandNames().getInfo())

        name_toexport = 'filterGF_BACIA_'+ str(self.id_bacias) + "_V" + self.version
        imageFilledtnt0 = imageFilledtnt0.set(
                            'version', self.version, 
                            'biome', 'CAATINGA',
                            'type_filter', 'gap_fill',
                            'collection', '7.1',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.imgClass.get('system:footprint')
                        )
        imageFilledtnt0 = ee.Image.cat(imageFilledtnt0)
        self.processoExportar(imageFilledtnt0, name_toexport)

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  self.options['output_asset'] + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':self.geom_bacia.getInfo()['coordinates'],
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))



param = {
    'prefixo_out': 'maps_caat_col6_v5',
    'bioma': "CAATINGA", #nome do bioma setado nos metadados  
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta' : {
        '0': 'caatinga01',
        '6': 'caatinga02',
        '12': 'caatinga03',
        '17': 'caatinga04',
        '22': 'caatinga05',        
        '27': 'solkan1201',
        '32': 'rodrigo',
        '37': 'diegoGmail',    
    }
}

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
        cont = 0
    
    cont += 1    
    return cont


listaNameBacias = [
    # '741','7421','7422','744','745','746','7492','751','752','753',
    # '754','755','756','757','758','759','7621','7622','763','764',
    # '765','766','767',
    '771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7613','7614','7615','7616',
    '7617','7618','7619'
    # "76111","76116","7612","7613","7614",
]
cont = 0
for idbacia in listaNameBacias[:]:
    print("-----------------------------------------")
    print("----- PROCESSING BACIA {} -------".format(idbacia))

    cont = gerenciador(cont)
    aplicando_gapfill = processo_gapfill(idbacia)
    aplicando_gapfill.processing_gapfill()