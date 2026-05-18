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
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Tp/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Fq/',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',            
            'last_year' : 2021,
            'first_year': 1985
        }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.version = '1'
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                    ee.Filter.eq('nunivotto3', nameBacia)).first().geometry()        
        self.name_imgClass = 'filterFq_BACIA_'+ str(self.id_bacias) + "_V" + self.version
        self.imgClass = ee.Image(self.options['input_asset'] + self.name_imgClass)        

        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]

        self.ordem_exec_first = [12,4,21,3,22]
        self.ordem_exec_last = [21]
        self.ordem_exec_middle = [12,4,21,3,22]
        
    def mask_3_years (self, valor, ano, imagem, bnd_current, bnd_before, bnd_after):
        imagem = ee.Image(imagem)
        # bnd_before = ee.String('classification_').cat(ee.Number(ano).subtract(1))
        # bnd_current = ee.String('classification_').cat(ee.Number(ano))
        # bnd_after = ee.String('classification_').cat(ee.Number(ano).add(1))

        mmask = imagem.select(bnd_before).eq(valor).multiply(
                    imagem.select(bnd_current).neq(valor)).multiply(
                        imagem.select(bnd_after).eq(valor)).unmask(0)
    
        # muda_img = imagem.select(bnd_current).mask(mmask.eq(1)).where(mmask.eq(1), valor)  
        # img_out = imagem.select(bnd_current).blend(muda_img)
        
        # inversa da mascara, seleciona  pixels fora do alvo 
        invers_mask = mmask.eq(0)
        img_out = imagem.select(bnd_current).updateMask(invers_mask).unmask(0).add(mmask.eq(1).multiply(valor))        
        return img_out.rename(bnd_current)

    def mask_4_years (self, valor, ano, imagem):
        imagem = ee.Image(imagem)
        bnd_before = ee.String('classification_').cat(ee.Number(ano).subtract(1))
        bnd_current = ee.String('classification_').cat(ee.Number(ano))
        bnd_after = ee.String('classification_').cat(ee.Number(ano).add(1))
        bnd_afterpos = ee.String('classification_').cat(ee.Number(ano).add(2))

        mmask = imagem.select(bnd_before).eq(valor).And(
                    imagem.select(bnd_current).neq(valor)).And(
                        imagem.select(bnd_after).neq(valor)).And(
                            imagem.select(bnd_afterpos).eq(valor))
        
        muda_img = imagem.select(bnd_current).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        muda_img_post = imagem.select(bnd_after).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        img_out = imagem.select(bnd_current).blend(muda_img).blend(muda_img_post)
        return img_out

    def mask_5_years (self, valor, ano, imagem):
        imagem = ee.Image(imagem)
        bnd_before = ee.String('classification_').cat(ee.Number(ano).subtract(1))
        bnd_current = ee.String('classification_').cat(ee.Number(ano))
        bnd_after = ee.String('classification_').cat(ee.Number(ano).add(1))
        bnd_afterpos = ee.String('classification_').cat(ee.Number(ano).add(2))
        bnd_afterpospos = ee.String('classification_').cat(ee.Number(ano).add(3))

        mmask = imagem.select(bnd_before).eq(valor).And(
                    imagem.select(bnd_current).neq(valor)).And(
                        imagem.select(bnd_after).neq(valor)).And(
                            imagem.select(bnd_afterpos).neq(valor)).And(
                                imagem.select(bnd_afterpospos).eq(valor))
        
        
        muda_img = imagem.select(bnd_current).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        muda_img_post = imagem.select(bnd_after).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        muda_img_pospos = imagem.select(bnd_afterpos).mask(mmask.eq(1)).where(mmask.eq(1), valor)

        img_out = imagem.select(bnd_current).blend(muda_img).blend(muda_img_post).blend(muda_img_pospos)
        return img_out

    def mask3first (self, valor, imagem):
        bnd_current = 'classification_' + str(self.options['first_year'])
        bnd_pos = 'classification_' + str(self.options['first_year'] + 1)
        bnd_pospos = 'classification_' + str(self.options['first_year'] + 2)
        lstBands =copy.deepcopy(self.lstbandNames)
    
        mmask = imagem.select(bnd_current).neq(valor).And(
                    imagem.select(bnd_pos).eq(valor)).And(
                        imagem.select(bnd_pospos).eq (valor))
        
        muda_img = imagem.select(bnd_current).mask(mmask.eq(1)).where(mmask.eq(1), valor)
        img_out = imagem.select(bnd_current).blend(muda_img)
        lstBands.remove(bnd_current)
        
        img_out = img_out.addBands(imagem.select(lstBands))    
        return img_out
    
    def mask3last (self, valor, imagem):
        bnd_prebefore = 'classification_' + str(self.options['last_year'] - 2)
        bnd_before = 'classification_' + str(self.options['last_year'] - 1)
        bnd_current = 'classification_' + str(self.options['last_year'])
        lstBands = copy.deepcopy(self.lstbandNames)

        mmask = imagem.select(bnd_prebefore).eq (valor).And(
                        imagem.select().eq(valor)).And(
                            imagem.select(bnd_current).neq(valor))
        
        muda_img = imagem.select(bnd_current).mask(mmask.eq(1)).where(mmask.eq(1), valor)
        img_out = imagem.select(bnd_current).blend(muda_img)
        
        lstBands.remove(bnd_current)
        # // print("seleciona listaBandas", imagem.select(lsBands))
        img_out = imagem.select(lstBands).addBands(img_out)
        return img_out

    def window_years(self, imagem, valor, janela):
        bnd_current = 'classification_' + str(self.options['first_year'])
        
        print(self.years[1: len(self.years) - janela + 2])

        lst_Iteraryear = self.years[1: len(self.years) - janela + 2]
        
        band_mask = None
        if janela == 3:
            print("executando janela de 3 ")
            lstband_mask = ee.List(lst_Iteraryear).map(lambda yyear : self.mask_3_years(valor, yyear, imagem))
        elif janela == 4:
            lstband_mask = ee.List(lst_Iteraryear).map(lambda yyear : self.mask_4_years(valor, yyear, imagem))      
        elif janela == 5:
            lstband_mask = ee.List(lst_Iteraryear).map(lambda yyear : self.mask_5_years(valor, yyear, imagem))
        
        print("lista de bandas processadas ", lstband_mask)
        imgg_out = imagem.select(bnd_current)
        for yyear in lst_Iteraryear:
            band_class = 'classification_' + str(yyear)
            imgg_out = imgg_out.addBands(band_mask.select(band_class)) 
        
        print("image out ", imgg_out.bandNames().getInfo())

        bnd_prebefore = 'classification_' + str(self.options['last_year'] - 2)
        bnd_before = 'classification_' + str(self.options['last_year'] - 1)
        bnd_current = 'classification_' + str(self.options['last_year'])
        
        if janela == 3:
            imgg_out = imgg_out.addBands(imagem.select(bnd_current))            
        elif janela == 4:
            imgg_out = imgg_out.addBands(imagem.select(bnd_before))
            imgg_out = imgg_out.addBands(imagem.select(bnd_current))
        elif janela == 5:
            imgg_out = imgg_out.addBands(imagem.select(bnd_prebefore))
            imgg_out = imgg_out.addBands(imagem.select(bnd_before))
            imgg_out = imgg_out.addBands(imagem.select(bnd_current)) 

        return imgg_out

    def applyTemporalFilter(self):
        filtered = ee.Image(self.imgClass)
        clase = {
                '21': "agro",
                '4': 'Florest',
                '12': "campo",
                '3': 'savana',
                '22': 'area naoVeg',
                '29': 'aflora'
            }

        for id_class in self.ordem_exec_first:
            print("processing first 3 years class = ", id_class)
            filtered = self.mask3first(id_class, filtered)

        for id_class in self.ordem_exec_last:
            print("processing last 3 years class = ", id_class)
            filtered = self.mask3last(id_class, filtered)

        for id_class in self.ordem_exec_middle:
            print("processing years intermedio class = ", id_class)
            filtered = self.window_years(filtered, id_class, 3)

        lst_band_conn = [bnd + '_conn' for bnd in lstbandNames]
        # / add connected pixels bands
        imageFilledConnected = filtered.addBands(
                                    filtered.connectedPixelCount(100, True).rename(self.lstbandNames))

        imageFilledConnected = imageFilledConnected.set(
                            'version',  self.version, 
                            'biome', 'CAATINGA',
                            'type_filter', 'temporal',
                            'collection', '7.0',
                            'id_bacia', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.imgClass.get('system:footprint')
                        )
        imageFilledConnected = ee.Image.cat(imageFilledConnected)
        name_toexport = 'filterTp_BACIA_'+ str(self.id_bacias)
        self.processoExportar(imageFilledConnected, name_toexport)    

    #exporta a imagem classificada para o asset
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
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616',
    '7617','7618','7619', '7613',
]
cont = 0
for idbacia in listaNameBacias[:]:    
    cont = gerenciador(cont)
    print("----- PROCESSING BACIA {} -------".format(idbacia))
    aplicando_TemporalFilter = processo_filterTemporal(idbacia)
    aplicando_TemporalFilter.applyTemporalFilter()