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


class processo_filterFrequence(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Fq/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Sp/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',            
            'last_year' : 2021,
            'first_year': 1985
        }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.version = '4'
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()        
        self.name_imgClass = 'filterSp_BACIA_' + nameBacia + "_V" + self.version
        self.imgClass = ee.Image(self.options['input_asset'] + self.name_imgClass)        

        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        
    

    def applySpatialFrequency(self):

        ##### ////////Calculando frequencias /////////////#####
        #######################################################
        #############  General rule in Years ##################
        exp = '100*((b(0) + b(1) + b(2) + b(3) + b(4) + b(5) + b(6) + b(7) + b(8) + b(9) + b(10) + b(11) + b(12)'
        exp += '+ b(13) + b(14) + b(15) + b(16) + b(17) + b(18) + b(19) + b(20) + b(21) + b(22) + b(23) + b(24)'
        exp += '+ b(25) + b(26) + b(27) + b(28) + b(29) + b(30) + b(31) + b(32) + b(33) + b(34) + b(35) + b(36))/37)'
    
        ############## get frequency   #######################
        florest_frequence = self.imgClass.eq(3).expression(exp)
        savana_frequence = self.imgClass.eq(4).expression(exp)
        grassland__frequence = self.imgClass.eq(12).expression(exp)    
        
        frequency_natural = florest_frequence.add(savana_frequence).add(grassland__frequence)
        # //////Máscara de vegetacao nativa e agua (freq >95%)
        vegetationMask = ee.Image(0).where(frequency_natural.gt(95), 1)
        
    
        ###########  /////Mapa base////// ############
        vegetation_map = ee.Image(0).where(vegetationMask.eq(1).And(florest_frequence.gt(50).And(
                            self.imgClass.select('classification_' + str(self.options['last_year'])).neq(3))), 3).where(
                                    vegetationMask.eq(1).And(grassland__frequence.gt(50)), 12).where(
                                        vegetationMask.eq(1).And(savana_frequence.gt(80)), 4)

        vegetation_map = vegetation_map.updateMask(vegetation_map.neq(0))
        img_output = self.imgClass.where(vegetation_map, vegetation_map)       

        img_output = img_output.set(
                            'version',  self.version, 
                            'biome', 'CAATINGA',
                            'type_filter', 'frequence',
                            'collection', '7.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.imgClass.get('system:footprint')
                        )
        img_output = ee.Image.cat(img_output)
        name_toexport = 'filterFq_BACIA_'+ str(self.id_bacias) + "_V" + self.version
        self.processoExportar(img_output, name_toexport)    

    ##### exporta a imagem classificada para o asset  ###
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  self.options['output_asset'] + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
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
        '2': 'caatinga02',
        '4': 'caatinga03',
        '7': 'caatinga04',
        '22': 'caatinga05',        
        '27': 'solkan1201',
        '32': 'rodrigo',
        # '37': 'diegoGmail',    
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
    # '765','766','767','771','772','773', '7741','7742','775','776',
    # '777','778','76111','76116','7612','7613', '7614','7615','7616',
    # '7617','7618','7619'
    '76111','76116','7612','7613', '7614'
]
cont = 0
for idbacia in listaNameBacias[:]:
    print(" ")
    print("--------- PROCESSING BACIA {} ---------".format(idbacia))
    print("-------------------------------------------")
    cont = gerenciador(cont)
    aplicando_FrequenceFilter = processo_filterFrequence(idbacia)
    aplicando_FrequenceFilter.applySpatialFrequency()