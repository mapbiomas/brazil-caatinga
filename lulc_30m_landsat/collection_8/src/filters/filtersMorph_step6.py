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


class processo_filterTemporal(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/morfologico/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Fq/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/SSpatial/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',            
            'last_year' : 2022,
            'first_year': 1985,
            'janela' : 3
        }
    # weights = [
    #         [1, 1, 1, 1, 1, 1, 1],
    #         [1, 1, 1, 1, 1, 1, 1],
    #         [1, 1, 1, 1, 1, 1, 1],
    #         [1, 1, 1, 1, 1, 1, 1],
    #         [1, 1, 1, 1, 1, 1, 1],
    #         [1, 1, 1, 1, 1, 1, 1],
    #         [1, 1, 1, 1, 1, 1, 1]
    #     ]
    
    pmtrosMax = {
            'kernelType': 'square', 
            'radius': 5,
            'iterations': 1
        }
    pmtrosMin = {  
                'kernelType': 'square', 
                'radius': 2,
                'iterations': 1
                }

    def __init__(self):
        # self.id_bacias = nameBacia
        self.versionInput = '6'
        self.versionOutput = '1'
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer'])#.filter(
                                                    # ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()              

        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]

        self.ordem_exec_class = [3,12]
        self.classOutput = 4
        # mykernel = ee.Kernel.fixed(weights= self.weights)       



    ################### CONJUNTO DE REGRAS PARA CONSTRUIR A LISTA DE BANDAS ##############    
    ######### https://code.earthengine.google.com/6a44ff0aa371319687e5f53911b8c7a4 #######
    ######## https://code.earthengine.google.com/69f20b4175a7c0c9267c1f5d73ab760c ########
    def mask_kernel_N (self, valor, imagem):
        imagem = ee.Image(imagem)
        maskClass = imagem.eq(valor)
        # capturando os pixels de sal e pimenta
        # apply filter morphological
        maskMorfolica = maskClass.focalMin(**self.pmtrosMin)
        maskMorfolica = maskMorfolica.focalMax(**self.pmtrosMax)
        maskMorfolica = maskMorfolica.multiply(maskClass)        

        maskChange = maskClass.subtract(maskMorfolica)
        img_out = imagem.where(maskChange.eq(1), self.classOutput)
        return img_out

    
    def applyMorphologicalFilter(self, id_bacias): 
              
        # clase = {
        #         '21': "agro",
        #         '4': 'Florest',
        #         '12': "campo",
        #         '3': 'savana',
        #         '22': 'area naoVeg',
        #         '29': 'aflora'
        #     }        

        name_imgClass = 'filterSP_BACIA_'+ id_bacias + '_V' + self.versionInput
        print("processing image ", name_imgClass)
        imgClass = ee.Image(self.options['input_asset'] + name_imgClass)  

        for id_class in self.ordem_exec_class:
            imgOutput = ee.Image().byte()
            print("processing class {} == bacia {} ".format(id_class, id_bacias))            
            for bndyear in self.lstbandNames:
                # print("  => ", lstyear)
                imgtmp = self.mask_kernel_N(id_class, imgClass.select(bndyear))
                # if bndyear == self.ordem_exec_class[-1]:
                #     maskInv = imgtmp.eq(0)
                #     # corregindo algum pixel 0
                #     imgtmp = imgtmp.add(maskInv.multiply(3))
                imgOutput = imgOutput.addBands(imgtmp.rename(bndyear))

            imgOutput = imgOutput.select(self.lstbandNames)
            imgClass = copy.deepcopy(imgOutput)
            # print("comprovando o número de bandas \n ====>", len(imgOutput.bandNames().getInfo()))

        geom = self.geom_bacia.filter(ee.Filter.eq('nunivotto3', id_bacias)).first().geometry()
        imageFilled = imgClass.set(
                            'version',  self.versionOutput, 
                            'biome', 'CAATINGA',
                            'type_filter', 'morfologico',
                            'collection', '8.0',
                            'id_bacia', id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , geom
                        )
        imageFilled = ee.Image.cat(imageFilled).clip(geom)        
        name_toexport = 'filterMO_BACIA_'+ str(id_bacias) + "_V" + self.versionOutput
        self.processoExportar(imageFilled, name_toexport, geom)    

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc, geom_bacia):
        
        idasset =  self.options['output_asset'] + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region': geom_bacia.getInfo()['coordinates'],
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
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',        
        '32': 'solkan1201',
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
    '777','778','76111','76116','7612','7614','7615','7616',
    '7617','7618','7619', '7613',
]
aplicando_TemporalFilter = processo_filterTemporal()

cont = 0
for idbacia in listaNameBacias[1:]:    
    cont = gerenciador(cont)
    print("----- PROCESSING BACIA {} -------".format(idbacia))
    
    aplicando_TemporalFilter.applyMorphologicalFilter(idbacia)