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
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV2/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/TemporalV2',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',            
            'last_year' : 2023,
            'first_year': 1985
        }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.versionTP = 16
        self.versionFR = 16
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()   
        # filterSP_BACIA_778_V1     
        # self.name_imgClass = 'filterSP_BACIA_' + nameBacia + "_V" + self.versionSP
        self.name_imgClass = 'filterGF_BACIA_' + nameBacia + "_GTB_V" + str(self.versionTP)
        self.imgClass = ee.ImageCollection(self.options['input_asset']).filter(
                                ee.Filter.eq('id_bacia', nameBacia)).filter(
                                    ee.Filter.inList('version', [self.versionTP])).filter(
                                        ee.Filter.eq('janela', 3)).first()       

        print(" show metadata raster ", self.imgClass.get('system:index').getInfo());
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]

        self.maskNatural = self.imgClass.eq(3).Or(self.imgClass.eq(4)).Or(self.imgClass.eq(12))

    def getwindowsfeed(self, lstyear, pos, janela):
        if len(lstyear) - pos < 5:
            return lstyear[ - janela: ]
        elif pos < 2:
            return lstyear[0: janela]
        else:
            return lstyear[pos - 2: pos + 3]
    
    def getwindows(self, lstyear, pos, janela):
        if len(lstyear) - pos < 5:
            return lstyear[ - janela: ]
        else:
            return lstyear[pos: pos + janela]
        

    def applyStabilityNaturalUse(self):          
        ############## get frequency   #######################
        colNatForward = ee.Image().byte()
        for cc, yyearband in enumerate(self.lstbandNames):
            lstWindowsforward = self.getwindows(self.lstbandNames, cc, 5); # janela = 5
            # print(cc, " ", lstWindowsforward)
            rasterWindwsNat = self.maskNatural.select(lstWindowsforward).reduce(ee.Reducer.sum())
            colNatForward = colNatForward.addBands(rasterWindwsNat.rename(yyearband))
        
        colNatForward = colNatForward.select(self.lstbandNames)

        #####################################################
        ###### corregindo a serie de janelas naturais  ######
        ###### escada subindo de descendo das janelas  ###### 
        ###### com 5 ou mais natural                   ######
        colNatForwardCor = ee.Image().byte()
        for cc, yyearband in enumerate(self.lstbandNames):
            lstWindowsforward = self.getwindows(self.lstbandNames, cc, 5)
            rasterWindwsNat = colNatForward.select(lstWindowsforward);
            if cc > 2:
                mmasQ1 = rasterWindwsNat.select([0]).eq(1).And(
                          rasterWindwsNat.select([1]).eq(2)).And(
                            rasterWindwsNat.select([2]).eq(3)).And(
                                rasterWindwsNat.select([3]).eq(4)).And(
                                    rasterWindwsNat.select([4]).eq(5));

                mmasQ2 = rasterWindwsNat.select([0]).eq(2).And(
                            rasterWindwsNat.select([1]).eq(3)).And(
                                rasterWindwsNat.select([2]).eq(4)).And(
                                    rasterWindwsNat.select([3]).eq(5)).And(
                                        rasterWindwsNat.select([4]).eq(5))

                mmasQ3 = rasterWindwsNat.select([0]).eq(2).And(
                            rasterWindwsNat.select([1]).eq(3)).And(
                                rasterWindwsNat.select([2]).eq(4)).And(
                                    rasterWindwsNat.select([3]).eq(5)).And(
                                        rasterWindwsNat.select([4]).eq(4))
                                        
                mmasQ4 = rasterWindwsNat.select([0]).eq(5).And(
                            rasterWindwsNat.select([1]).eq(5)).And(
                                rasterWindwsNat.select([2]).eq(4)).And(
                                    rasterWindwsNat.select([3]).eq(3)).And(
                                        rasterWindwsNat.select([4]).eq(2))
                                        
                mmasQ5 = rasterWindwsNat.select([0]).eq(5).And(
                            rasterWindwsNat.select([1]).eq(4)).And(
                                rasterWindwsNat.select([2]).eq(3)).And(
                                    rasterWindwsNat.select([3]).eq(2)).And(
                                        rasterWindwsNat.select([4]).eq(1))
                                        
                mmasQ6 = rasterWindwsNat.select([0]).eq(4).And(
                            rasterWindwsNat.select([1]).eq(3)).And(
                                rasterWindwsNat.select([2]).eq(2)).And(
                                    rasterWindwsNat.select([3]).eq(1)).And(
                                        rasterWindwsNat.select([4]).eq(0))

                colNatForwardGG = colNatForward.select(yyearband).where(mmasQ1.eq(1), ee.Image.constant(0))
                colNatForwardGG = colNatForwardGG.where(mmasQ2.eq(1), ee.Image.constant(0))
                colNatForwardGG = colNatForwardGG.where(mmasQ3.eq(1), ee.Image.constant(0))
                colNatForwardGG = colNatForwardGG.where(mmasQ4.eq(1), ee.Image.constant(5))
                colNatForwardGG = colNatForwardGG.where(mmasQ5.eq(1), ee.Image.constant(5))
                colNatForwardGG = colNatForwardGG.where(mmasQ6.eq(1), ee.Image.constant(5))
                colNatForwardCor = colNatForwardCor.addBands(colNatForwardGG.rename(yyearband))
            else:
                colNatForwardCor = colNatForwardCor.addBands(colNatForward.select(yyearband))
        
        colNatForwardCor = colNatForwardCor.select(self.lstbandNames)
        rasterFinal = ee.Image().byte()
        areaAnalises = self.imgClass.eq(4).Or(self.imgClass.eq(21))
        ###########  /////Mapa base////// ############
        for cc, yyearband in enumerate(self.lstbandNames):
            imageYY = self.imgClass.select(yyearband)
            imageYY = imageYY.where(
                                areaAnalises.select(yyearband).eq(1).And(
                                            colNatForwardCor.select(yyearband).lte(2)), 21
                            ).where(
                                areaAnalises.select(yyearband).eq(1).And(
                                            colNatForwardCor.select(yyearband).gte(3)), 4
                            );
            rasterFinal = rasterFinal.addBands(imageYY.rename(yyearband))

        rasterFinal = rasterFinal.select(self.lstbandNames)        

        rasterFinal = rasterFinal.clip(self.geom_bacia).set(
                            'version',  int(self.versionFR), 
                            'biome', 'CAATINGA',
                            'type_filter', 'frequence_natUso',
                            'collection', '9.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.geom_bacia
                        )

        rasterFinal = ee.Image.cat(rasterFinal)
        name_toexport = 'filterFQnu_BACIA_'+ str(self.id_bacias) + "_V" + str(self.versionFR)
        self.processoExportar(rasterFinal, name_toexport)  

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
        # '0': 'caatinga01',
        # '2': 'caatinga02',
        '0': 'caatinga03',
        '9': 'caatinga04',
        '18': 'caatinga05',        
        '27': 'solkan1201',    
        '35': 'solkanGeodatin'
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
    '744','741','7422','745','746','7492','751','752','753',
    '755','759','7621','7622','763','764','765','766','767', 
    '771', '772','773','7741','776','7742','775', '777','778',
    '76111','76116','7612','7613','7615','7616', '7617','7618', 
    '7619', '754','756','757','758', '7614', '7421',
]
# listaNameBacias = [
#    
# ]
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial/'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/FrequencyV2/'
cont = 0
knowMapSaved = False
listBacFalta = []
for idbacia in listaNameBacias[1:]:
    if knowMapSaved:
        try:
            # projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill/filterGF_BACIA_741_V2
            nameMap = 'filterFQ_BACIA_' + idbacia + "_V3"
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
        aplicando_FrequenceFilter.applyStabilityNaturalUse()

if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))