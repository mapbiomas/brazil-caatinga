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
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Frequency/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Temporal/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Frequency/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',            
            'last_year' : 2022,
            'first_year': 1985,
            'yearLimitA': 1987,
            'yearLimitB': 2000,
            'yearRefe1': 1987,
            'yearRefe2': 1999,
            'yearRefe3': 1989
        }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.versionTP = '9'
        self.versionFR = '7'
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()   
        # filterSP_BACIA_778_V1     
        # self.name_imgClass = 'filterSP_BACIA_' + nameBacia + "_V" + self.versionSP
        self.name_imgClass = 'filterTP_BACIA_' + nameBacia + "_V" + self.versionTP
        # self.name_imgClass = 'filterFQ_BACIA_' + nameBacia + "_V" + self.versionTP

        self.imgClass = ee.Image(self.options['input_asset'] + self.name_imgClass)        
        # print('bandas Year ', self.imgClass.bandNames().getInfo());
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        
        self.bandsNamesSel = ['classification_' + str(yy) for yy in range(self.options['first_year'], 
                                                    self.options['last_year'] + 1) if yy <= self.options['yearLimitB'] and yy >= self.options['yearLimitA']]

        self.lstBaciaSel = [
                '7421','7422','7621','7742','7741','764',
                '765','741','744','745','746','751','752',
                '753','754','755','763','772','7614']
    
    # https://code.earthengine.google.com/a64f20d97fa5581d2f8f9801251acd4d
    def applySpatialFrequency(self):

        ##### ////////Calculando frequencias /////////////#####
        #######################################################
        #############  General rule in Years ##################
        mapaReturn = ee.Image().byte()
        mapMosaicMaxC = ee.Image.constant(0);
        mapCampMax = ee.Image.constant(0);
        mapReference = ee.Image.constant(1);
        mapYYmax = ee.Image.constant(0);

        for YYband in self.bandsNamesSel:
            imgMapCamp_tmp = self.imgClass.select(YYband).eq(12)
            imgMapMos_tmp = self.imgClass.select(YYband).eq(21)
            mapReference = mapReference.multiply(imgMapCamp_tmp)
            mapMosaicMaxC = mapMosaicMaxC.add(imgMapMos_tmp)
            mapCampMax = mapCampMax.add(imgMapCamp_tmp)

        mapReference = ee.Image(mapReference).gt(0);  # intersection of all maps 
        mapMosaicMaxC = mapMosaicMaxC.gt(3); # repetido mais de 3 vezes
        mapReference = mapCampMax.gt(2)
        mapCampMax = mapCampMax.gt(0)
        mapMosaicMaxC = mapMosaicMaxC.add(mapCampMax).gt(0)

        # # selecionar mapas de referencias 
        # if self.id_bacias in self.lstBaciaSel:
        #     print(f"bacia {self.id_bacias} está dentro da lista de selecionadas ")
        #     bandRef1 = 'classification_' + str(self.options['yearRefe1'])
        #     bandRef2 = 'classification_' + str(self.options['yearRefe2'])
        #     bandRef3 = 'classification_' + str(self.options['yearRefe3'])
        #     print("banda de referencia ", bandRef1, " <=> ", bandRef2)
        #     mapReference = ee.Image(self.imgClass.select(bandRef1).eq(12)).add(
        #                         self.imgClass.select(bandRef2).eq(12)).add(
        #                             self.imgClass.select(bandRef3).eq(12)).gt(0)
        
        # print("aplicando filters ")
        for bandasYY in self.lstbandNames:
            # print("     ", bandasYY ," ",self.imgClass.select(bandasYY).bandNames().getInfo())
            if bandasYY in self.bandsNamesSel[:-1]:
                # aplicando o filtro para todos 
                print(" aplicando filtro -> ", bandasYY)
                maskCampoYear = self.imgClass.select(bandasYY).eq(12)
                maskDifCampo = mapReference.subtract(maskCampoYear)

                maskPushFlo = maskDifCampo.eq(1)
                maskPushFlo = maskPushFlo.multiply(mapMosaicMaxC)
                map_tmp = self.imgClass.select(bandasYY).where(maskPushFlo, 12)

                maskRemovFlo = maskDifCampo.eq(-1)
                maskRemovFlo = maskRemovFlo.multiply(mapMosaicMaxC)
                map_tmp = map_tmp.where(maskRemovFlo, 21)
                print(" add Band ", bandasYY)
                mapaReturn = mapaReturn.addBands(map_tmp.rename([bandasYY]))   

            else:
                mapaReturn = mapaReturn.addBands(self.imgClass.select(bandasYY))

            
        mapaReturn = mapaReturn.select(self.lstbandNames).clip(self.geom_bacia)
        mapaReturn = mapaReturn.set(
                            'version',  self.versionFR, 
                            'biome', 'CAATINGA',
                            'type_filter', 'frequence',
                            'collection', '8.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.imgClass.get('system:footprint')
                        )
        img_output = ee.Image.cat(mapaReturn)
        name_toexport = 'filterFQ_BACIA_'+ str(self.id_bacias) + "_V" + self.versionFR
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
        '0': 'caatinga03',
        '7': 'caatinga02',
        '14': 'caatinga01',
        '21': 'caatinga04',
        '28': 'caatinga05',        
        '32': 'solkan1201',
        # '32': 'rodrigo',
        '37': 'diegoGmail',    
    }
}

#============================================================
#========================METODOS=============================
#============================================================

def gerenciador(cont):

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
    '777','778','76111','76116','7612','7613', '7614','7615','7616',
    '7617','7618','7619'
]
# listaNameBacias = ['756','777','778']
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial/'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Frequency/'
cont = 10
knowMapSaved = False
listBacFalta = []
for idbacia in listaNameBacias[21:]:
    if knowMapSaved:
        try:
            # projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill/filterGF_BACIA_741_V2
            nameMap = 'filterFQ_BACIA_' + idbacia + "_V2"
            imgtmp = ee.Image(input_asset + nameMap)
            print("loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), "bandas ")
        except:
            listBacFalta.append(idbacia)
    else:
        print(" ")
        print("--------- PROCESSING BACIA {} ---------".format(idbacia))
        print("-------------------------------------------")
        cont = gerenciador(cont)
        aplicando_FrequenceFilter = processo_filterFrequence(idbacia)
        aplicando_FrequenceFilter.applySpatialFrequency()

if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))