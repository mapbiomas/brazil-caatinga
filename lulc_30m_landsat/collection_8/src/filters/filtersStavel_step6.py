#!/usr/bin/env python3
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


class processo_filterSpatial(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/merge/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Temporal/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
            'classMapB': [ 3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,41,42,43,44,45,46,47,48,49,50,62],
            'classNat' : [ 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'classAnt' : [ 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.versionSP = '6'
        # self.versionGF = '3'
        self.versionTP = '5'
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()  

        # projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill/filterGF_BACIA_741_V1   
        # self.name_imgClass = 'filterSP_BACIA_' + nameBacia + "_V" + self.versionGF
        self.name_imgClass = 'filterTP_BACIA_' + nameBacia + "_V" + self.versionTP
        self.imgClass = ee.Image(self.options['input_asset'] + self.name_imgClass)        
        print("carregada a imagem ", self.name_imgClass, " \n ", self.imgClass.bandNames().getInfo())
        self.lstbandNames = ['classification_' + str(yy) for yy in range(1985, 2023)]
        self.years = [yy for yy in range(1985, 2023)]
        # sys.exit()
    

    def applySpatialFilter(self):

        naturalClassMap = ee.Image().byte()    
        for cc, name_bnd in enumerate(self.lstbandNames):
            print(" banda Natural ", name_bnd)
            naturalClassMap = naturalClassMap.addBands(self.imgClass.select(name_bnd).remap(
                                    self.options['classMapB'], self.options['classNat']).rename(name_bnd))
        
        naturalClassMap = naturalClassMap.select(self.lstbandNames)

        # imagem multibands eq(1) condição para todas as bandas 
        # disminuir 34 se quizer contemplar mais areas naturais !!!
        imgMaskNatural = naturalClassMap.eq(1).reduce(ee.Reducer.sum()).gte(30)

        # // **************************************************************
        # // creando as mascaras onde foi todos os anos a mesma classe   **
        # // **************************************************************
        imgMask4 = self.imgClass.eq(4).reduce(ee.Reducer.sum()).gte(36)
        imgMask3 = self.imgClass.eq(3).reduce(ee.Reducer.sum()).gte(37)
        imgMask12 = self.imgClass.eq(12).reduce(ee.Reducer.sum()).gte(30)
        # imgMask29 = self.imgClass.eq(29).reduce(ee.Reducer.sum()).gt(5)
        # // **************************************************************
        # // separando da mascara de classes naturais os pixels estaveis **
        # // em todos os anos                                            **
        # // **************************************************************
        imgMaskNatural = imgMaskNatural.subtract(imgMask3).gt(0)
        imgMaskNatural = imgMaskNatural.subtract(imgMask4).gt(0)
        imgMaskNatural = imgMaskNatural.subtract(imgMask12).gt(0)
        # // **************************************************************************
        # // mascarando as classes naturais com  pixels não estaveis  em  *************
        # // todos os anos sendo eles Naturais, e visualizando 4 anos para comprovar **
        # // **************************************************************************
        mapClassNatural = self.imgClass.updateMask(imgMaskNatural)
        maskClassModa = mapClassNatural.reduce(ee.Reducer.mode());
        # // ***********************************************************
        # // modificando o valor 100 da moda                          **
        # // ***********************************************************
        maskClassModa = maskClassModa.remap([0,3,4,12,100], [0,3,4,12,3])
        maskClassModa = maskClassModa.updateMask(maskClassModa.gt(0))
        maskClassModa = maskClassModa.unmask(0, False)
        # // pegar todos os pixels do mapa que não serão modificados 
        maskNotNat = maskClassModa.eq(0);
        Mapfinal = self.imgClass.updateMask(maskNotNat);
        # /colocar em zero todos os pixels a serem modificadosfilter para
        Mapfinal = Mapfinal.unmask(0, False);

        # // Crea um mapa novo juntando tudo 
        newMapclass = ee.Image().byte()
        for cc, name_bnd in enumerate(self.lstbandNames):
            print(" class band ", name_bnd)
            newMapclass = newMapclass.addBands(
                Mapfinal.select(name_bnd).add(maskClassModa).rename(name_bnd))
        newMapclass = newMapclass.select(self.lstbandNames)

        newMapclass = newMapclass.set(
                            'version', self.versionSP, 
                            'biome', 'CAATINGA',
                            'type_filter', 'spatial',
                            'collection', '8.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.imgClass.get('system:footprint')
                        )
        newMapclass = ee.Image.cat(newMapclass)
        name_toexport = 'filterSP_BACIA_'+ str(self.id_bacias) + "_V" + self.versionSP
        self.processoExportar(newMapclass, name_toexport)    

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  self.options['output_asset'] + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId': idasset, 
            'region': self.geom_bacia.getInfo()['coordinates'],
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
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta' : {
        '0': 'caatinga01',
        '6': 'caatinga02',
        '13': 'caatinga03',
        '20': 'caatinga04',
        '27': 'caatinga05',        
        '32': 'solkan1201',
        # '32': 'rodrigo',
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
        '741','7421','7422','744','745','746','7492','751','752','753',
        '754','755','756','757','758','759','7621','7622','763','764',
        '765','766','767','771','772','773', '7741','7742','775','776',
        '777','778','76111','76116','7612','7613','7614','7615','7616',
        '7617','7618','7619'
]
# listaNameBacias = [
#     '76116','751','7612','7613', '7614',
#     '752', '753', '746','7422', '754','756','757'
# ]
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill/'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Temporal/'

knowMapSaved = False
listBacFalta = []
cont = 0
for idbacia in listaNameBacias[:]:
    if knowMapSaved:
        try:
            # projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill/filterGF_BACIA_741_V2
            nameMap = 'filterGF_BACIA_' + idbacia + "_V4"
            imgtmp = ee.Image(input_asset + nameMap)
            print("loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), "bandas ")
        except:
            listBacFalta.append(idbacia)
    else:
        print("-----------------------------------------")
        print("----- PROCESSING BACIA {} -------".format(idbacia))
        cont = gerenciador(cont)
        aplicando_SpatialFilter = processo_filterSpatial(idbacia)
        aplicando_SpatialFilter.applySpatialFilter()

if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))