#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import time
import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
class processo_filterTemporal(object):

    options = {
            # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
            'output_asset': "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalNat",
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_int',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',  
            'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
            'classNew':  [3, 4, 3, 4, 3, 11, 12, 12, 15, 19, 19, 19, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 25],
            # 'classNew':[3, 4, 3, 3, 12, 12, 21, 21, 21, 21, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21,  4, 12, 21, 25], 
            'classNat':  [1, 1, 1, 1, 1,  1,  1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  0,  0],    
            'last_year' : 2025,
            'first_year': 1985,
            'janela_input' : 4,
            'janela_output' : 5,
            'num_classes': 7,  # 7, 10
            'step': 1
        }

    def __init__(self, name_bacia):
        self.id_bacias = name_bacia
        self.versoutput = 1
        self.versionInput = 1
        self.geom_bacia = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', name_bacia))
        )
        geomBacia = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)            
        self.geom_bacia = self.geom_bacia.geometry()            

        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]  
        
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]

        self.lstbandsInv = ['classification_' + str(yy) for yy in range(self.options['last_year'], self.options['first_year'] - 1, - 1)]
        self.yearsInv = [kk for kk in range(self.options['last_year'], self.options['first_year'] - 1, - 1)]
        print("lista de anos ", self.yearsInv)
        # self.lstBandFinal =  ['classification_' + str(yy) for yy in self.years]
        # print("lista de anos ", self.lstbandsInv)

        self.imgClass = (
                    ee.ImageCollection(self.options['input_asset'])
                        .filter(ee.Filter.eq('version', self.versionInput))
                        # só o Gap-fill tem id_bacia o resto tem id_bacias
                        .filter(ee.Filter.eq('id_bacias', name_bacia ))  
                        .filter(ee.Filter.eq('num_class', self.options['num_classes'] ))
                        # .first()
                )
        print(" list of bands  loaded \n  ", self.imgClass.size().getInfo())        
        # print(self.imgClass.aggregate_histogram('version').getInfo())
        if 'Temporal' in self.options['input_asset']:
            self.imgClass = self.imgClass.filter(ee.Filter.eq('janela', self.options['janela_input']))

        # print(self.imgClass.aggregate_histogram('janela').getInfo())
        self.imgClass = self.imgClass.first()

        # Ajusta o intervalo de anos para coincidir com as bandas reais da imagem de entrada.
        # O passo anterior (janela=3) pode não exportar o primeiro ano (e.g. 1985),
        # então reconstruímos as listas de anos/bandas com base no que está disponível.
        actualBands = self.imgClass.bandNames().getInfo()
        actualYears = sorted([int(b.split('_')[1]) for b in actualBands])
        if actualYears[0] > self.options['first_year']:
            print(f"WARNING: Input missing years {self.options['first_year']}..{actualYears[0]-1}. "
                  f"Adjusting first_year to {actualYears[0]}")
            self.years     = actualYears
            self.lstbandNames = ['classification_' + str(yy) for yy in actualYears]
            self.lstbandsInv  = list(reversed(self.lstbandNames))
            self.yearsInv     = list(reversed(actualYears))
        print(" list of bands  loaded \n  ", actualBands)

        self.imgReclass = ee.Image().byte()
        for yband in self.lstbandNames:
            img_tmp = self.imgClass.select(yband)
            # print(img_tmp.bandNames().getInfo())
            img_tmp = img_tmp.remap(self.options['classMapB'], self.options['classNat'])
            self.imgReclass = self.imgReclass.addBands(img_tmp.rename(yband))
        
        self.imgReclass = self.imgReclass.select(self.lstbandNames)
        self.colectAnos = [self.mapeiaAnos(ano, self.options['janela_output'], self.yearsInv) for ano in self.yearsInv]
        # print(self.colectAnos)
        # sys.exit()
    ################### CONJUNTO DE REGRAS PARA CONSTRUIR A LISTA DE BANDAS ##############
    def regra_primeiraJ3(self, jan, delt, lstYears):
        return lstYears[1 : delt + 1] + [lstYears[0]] + lstYears[delt + 1 : jan]
    
    def regra_primeiraJ4(self, jan, delt, lstYears):
        return [lstYears[delt]] + lstYears[0: delt] + [lstYears[jan - 1]]
    
    def regra_primeiraJ5(self, jan, delt, lstYears):
        return [lstYears[delt + 1]] + lstYears[0: delt + 1] +  [lstYears[jan - 1]]
    
    def regra_ultima(self, jan, delt, lstYears):
        # print(lstYears[-1 * jan : ])
        return [lstYears[-3] , lstYears[-1], lstYears[-2]]    
    
    def regra_segundo_stepJ5(self, jan, delt, lstYears):
        return [lstYears[0]] + [lstYears[1]] + lstYears[delt : jan]
    
    def regra_antespenultimo_stepJ5(self, jan, delt, lstYears):
        print([lstYears[-5], lstYears[-3]] + [lstYears[-4]] + lstYears[-2:])
        return [lstYears[-5], lstYears[-3], lstYears[-2], lstYears[-1], lstYears[-4]]
    
    def regra_penultimo_stepJ5(self, jan, delt, lstYears):
         return [lstYears[-5], lstYears[-2], lstYears[-1], lstYears[-3], lstYears[-4]] 
    
    def regra_ultimo_stepJ5(self, jan, delt, lstYears):
        return [lstYears[-5], lstYears[-1], lstYears[-2], lstYears[-3], lstYears[-4]]    
    
    def regra_penultimo_stepJ4(self, jan, delt, lstYears):
        return [lstYears[-1 * jan] , lstYears[-2], lstYears[-1], lstYears[-3]] 

    def regra_ultimaJ4(self, jan, delt, lstYears):
        # print(lstYears[-1 * jan : ])
        return [lstYears[-4] , lstYears[-1], lstYears[-2] , lstYears[-3]]    

    def regra_primeiraJ6(self, janela, delta, lstYears):
        """Retorna a primeira janela no formato [ano4, ano0, ano1, ano2, ano3, ano5]."""
        if len(lstYears) < 6:
            return lstYears  # Fallback se não houver anos suficientes
        return [lstYears[4], lstYears[0], lstYears[1], lstYears[2], lstYears[3], lstYears[5]]

    def regra_ultimaJ6(self, jan, delt, lstYears):
        # print(lstYears[-1 * jan : ])
        return [lstYears[-5], lstYears[-4], lstYears[-3],  lstYears[-2], lstYears[-1], lstYears[-6]]

    # retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1 Nan 999, o metodo retornaria
    # desse jeito pode-se extrair as bandas referentes as janelas

    def mapeiaAnos(self, ano, janela, anos):
        lsBandAnos = ['classification_' + str(item) for item in anos]
        # print("ultimo ano ", anos[-1])
        # print(ano, " ultimo ano ", anos[-1])
        indice = anos.index(ano)
        delta = int(janela / 2)
        resto = int(janela % 2)
        ######### LIST OF BANDS FOR WINDOWS 3 #######################
        if janela == 3:
            if ano == anos[0]: # primeiro ano (2025) — janela para trás usando 2024 e 2023
                return self.regra_primeiraJ3(janela, delta, lsBandAnos)
            elif ano == anos[-1]: # igual a ultimo ano
                print("ultimo ano ", anos[-1])
                return self.regra_ultima(janela, delta, lsBandAnos)
            else:
                return lsBandAnos[indice - delta: indice + delta + resto]
        ######### LIST OF BANDS FOR WINDOWS 4 #######################
        elif janela == 4:
            if ano == anos[-2]:
                return self.regra_penultimo_stepJ4(janela, delta, lsBandAnos)
            elif ano == anos[-1]:
                return self.regra_ultimaJ4(janela, delta, lsBandAnos)
            else:
                return lsBandAnos[indice - 1: indice + delta + 1]
        ######### LIST OF BANDS FOR WINDOWS 5 #######################
        elif janela == 5:
            if ano == anos[-3]:
                return self.regra_antespenultimo_stepJ5(janela, delta, lsBandAnos)
            elif ano == anos[-2]:
                return self.regra_penultimo_stepJ5(janela, delta, lsBandAnos)
            elif ano == anos[-1]:
                return self.regra_ultimo_stepJ5(janela, delta, lsBandAnos)  
            else:                  
                return lsBandAnos[indice - 1: indice + 2 * delta]    
        ######### LIST OF BANDS FOR WINDOWS 6 #######################
        elif janela == 6:
            if ano < anos[-janela + 1]:
                # return self.regra_primeiraJ6(janela, delta, lsBandAnos)
                return self.regra_ultimaJ6(janela, delta, lsBandAnos)
            # elif ano == anos[-2]:
            #     # return self.regra_primeiraJ6(janela, delta, lsBandAnos)
            #     return self.regra_ultimaJ6(janela, delta, lsBandAnos)
            else:                  
                return lsBandAnos[indice - 1: indice + 2 * delta - 1] 
           
    def mask_3_years (self, valor, imagem):
        #### https://code.earthengine.google.com/1f9dd3ab081d243fa9d7962e06348579
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).eq(valor)).unmask(0)    
        # muda_img = imagem.select([1]).where(mmask.eq(1), valor)
        # imagem a retornar será a mesma imagem da mascara 
        return mmask.eq(1)

    def mask_4_years (self, valor, imagem):
        imagem = ee.Image(imagem)  
        # print("    === > ", imagem.bandNames().getInfo())      
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).neq(valor)).And(
                            imagem.select([3]).eq(valor))

        return mmask.eq(1)

    def mask_5_years (self, valor, imagem):
        # print("imagem bandas ", imagem.bandNames().getInfo())
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).neq(valor)).And(
                            imagem.select([3]).neq(valor)).And(
                                imagem.select([4]).eq(valor))

        return mmask.eq(1)
    
    def mask_6_years (self, valor, imagem):
        # print("imagem bandas ", imagem.bandNames().getInfo())
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).neq(valor)).And(
                            imagem.select([3]).neq(valor)).And(
                                imagem.select([4]).neq(valor)).And(
                                    imagem.select([5]).eq(valor))

        return mmask.eq(1)

    def reclass_natural_Antropic(self, raster_maps, listYYbnd):
        mapstemporal = ee.Image().byte()
        lstRemap = []
        for mm, bnd_year in enumerate(listYYbnd):
            tmp_raster = raster_maps.select(bnd_year).remap(self.options['classMapB'], self.options['classNat'])
            mapstemporal = mapstemporal.addBands(tmp_raster)
            if mm == 0:
                lstRemap.append('remapped')
            else:
                lstRemap.append(f'remapped_{mm}')
        
        return mapstemporal.select(lstRemap).rename(listYYbnd)
    
    def applyTemporalFilter(self, showinterv):         

        imgOutput = ee.Image().byte()
        id_class = 1
        delta = self.options['janela_output'] // 2
        # print(" --------- lista de bandas -------------\n", self.colectAnos)
        if self.options['janela_output'] == 3:
            # as classes naturais estão agrupadas e convertidas a valor 1               
            
            rasterbefore = ee.Image().byte()
            print("processing class value << {} >> === with === janela {} ".format(id_class, self.options['janela_input'])) 

            for cc, lstyear in enumerate(self.colectAnos):     
                print(f"> {cc} intervalos <==> ", lstyear)            
                # if showinterv:
                #     print(f"> {cc} intervalos <==> ", lstyear)                 
                if cc > 0 : # and cc < len(self.colectAnos) - delta 
                    print(f"> {cc} intervalos <==> ", lstyear) 
                    band_C1 = lstyear[1]
                    if cc == 1:                
                        imgtmp_mask = self.mask_3_years(id_class, self.imgReclass.select(lstyear))
                        # imgtmp_mask = imgtmp_mask.selfMask()
                        # print("banda da mascara ", imgtmp_mask.bandNames().getInfo())
                    else:                     
                        imgComposta = rasterbefore.addBands(self.imgReclass.select(lstyear[1:]))
                        # print(f"#{cc} show bands ", imgComposta.bandNames().getInfo())
                        imgtmp_mask = self.mask_3_years(id_class, imgComposta)
                        imgtmp_mask = imgtmp_mask.selfMask()
                    
                    # print('addicionando a banda before modificada no imgReclass ', band_C1)
                    # addicionando os pixels que cumpriram a condição na janela de 3
                    rasterbefore = self.imgReclass.select(band_C1).where(imgtmp_mask.eq(1), id_class)
                    # reemplazar pixels mudados no mapa inicial 
                    # print(" >>>>>>>> ", band_C1)
                    map_change_year = (self.imgClass.select(band_C1)
                                                .blend(imgtmp_mask.selfMask().multiply(
                                                            self.imgClass.select(lstyear[2])))
                                                .rename(band_C1))
                    imgOutput = imgOutput.addBands(map_change_year)
                    # print("saida intermedia ", imgOutput.bandNames().getInfo())
                    # if cc == 38: 
                    #     map_change_year = (self.imgClass.select(self.lstbandNames[0])
                    #                             .blend(imgtmp_mask.selfMask().multiply(
                    #                                         imgOutput.select(lstyear[1])))
                    #                             .rename(self.lstbandNames[0]))
                    #     imgOutput = imgOutput.addBands(map_change_year)
                else:
                    if cc == 0:
                        print(f"> {cc} intervalos <==> ", lstyear)
                        band_C1 = lstyear[1]  # classification_2025
                        imgtmp_mask = self.mask_3_years(id_class, self.imgReclass.select(lstyear))
                        rasterbefore = self.imgReclass.select(band_C1).where(imgtmp_mask.eq(1), id_class)
                        map_change_year = (self.imgClass.select(band_C1)
                                                    .blend(imgtmp_mask.selfMask().multiply(
                                                                self.imgClass.select(lstyear[2])))
                                                    .rename(band_C1))
                        imgOutput = imgOutput.addBands(map_change_year)

            # sys.exit()

        elif self.options['janela_output'] == 4:
            # imageTranscicao = None
            self.colectAnos = [self.mapeiaAnos(ano, self.options['janela_output'], self.yearsInv) for ano in self.yearsInv]   
            # id_class = 1   # classe de floresta 
            # imgOutput = ee.Image().byte()
            maps_bacias_c = self.imgClass
            print(f"processing class {id_class} == janela {self.options['janela_output']} and delta {delta}")   
            rasterC1 = None
            rasterC2 = None  
            imgstmp_masks = None     
            limit_iterations = len(self.colectAnos[: - delta])  
            for cc, lstyear in enumerate(self.colectAnos[:]): #  - delta + 1               
                # band_C1 = lstyear[1]
                # band_C2 = lstyear[2]
                # rasterReclass = self.reclass_natural_Antropic(maps_bacias_c, lstyear)

                # if showinterv:
                #     print(f"> #{cc} intervalos <==> {lstyear}")  # 
                
                if cc > 0:  #  and cc < len(self.colectAnos) - delta - 1
                    print(f"> {cc} intervalos <==> ", lstyear) 
                    band_C1 = lstyear[1]
                    band_C2 = lstyear[2]
                    rasterReclass = self.reclass_natural_Antropic(maps_bacias_c, lstyear)
                    if cc == 1:                   
                        imgstmp_masks = self.mask_4_years(id_class, rasterReclass)
                        ### imgstmp_masks é uma unica imagem que mascara os pixels que comprem a condição 
                        ### da janela número 4 
                    else:  
                        # imagem composta pelas duas anteriores imagens centrais mais o resto das duas no intervalo
                        imgComposta = rasterC1.addBands(rasterC2).addBands(rasterReclass.select(lstyear[2:]))  
                        # print(f" #{cc} =>  {imgComposta.bandNames().getInfo()}  cc")
                        # extraindo as duas mascaras construidas no mask 4 years
                        imgstmp_masks = self.mask_4_years(id_class, imgComposta)     
                        # sys.exit()          
                    
                    # mudando os pixels dos mapas centrais reclassificados segundo a regra
                    rasterC1 = rasterReclass.select(band_C1).where(imgstmp_masks.eq(1), id_class)
                    rasterC2 = rasterReclass.select(band_C2).where(imgstmp_masks.eq(1), id_class)

                    # reemplazar pixels mudados no mapa inicial no primeiro mapado intervalo
                    # onde a mascara seja 1  coloca o valor do pixel da imagem final da janela
                    map_change_yeart0 = (maps_bacias_c.select(band_C1)
                                        .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                        .rename(band_C1))
                    # print("process t0 ", maps_bacias_c.select([lstyear[-1]]).bandNames().getInfo())
                    map_change_yeart1 = (maps_bacias_c.select(band_C2)
                                            .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                            .rename(band_C2))

                    imgOutput = imgOutput.addBands(map_change_yeart0)
                    """
                        atualizando  a matrix dos mapas
                    """
                    # last_cc: último cc em que ainda há bandas futuras para incluir no update
                    last_cc = len(self.lstbandsInv) - 1 - delta
                    if cc < last_cc:
                        # print(self.lstbandsInv[:cc])
                        maps_bacias_c = (maps_bacias_c.select(self.lstbandsInv[: cc])
                                                    .addBands(map_change_yeart0)
                                                    .addBands(map_change_yeart1)
                                                    .addBands(maps_bacias_c.select(self.lstbandsInv[cc + delta :]))
                                            )
                    elif cc == last_cc:
                        # print(f"{last_cc}   >>>>>>>> ", self.lstbandsInv[:cc])
                        # print(map_change_yeart0.bandNames().getInfo())
                        # print(map_change_yeart1.bandNames().getInfo())
                        maps_bacias_c = (maps_bacias_c.select(self.lstbandsInv[: cc])
                                                    .addBands(map_change_yeart0)
                                                    .addBands(map_change_yeart1)
                                                    .addBands(maps_bacias_c.select(self.lstbandsInv[cc + delta :]))
                                            )

                else:
                    if cc == 0:
                        print(f"> {cc} intervalos <==> ", lstyear, "  ", self.lstbandNames[-1]) 
                        imgOutput = imgOutput.addBands(self.imgClass.select(self.lstbandNames[-1]))
                #     else:
                #         imgOutput = imgOutput.addBands(self.imgClass.select(self.lstbandNames[0]))
            # print("primeira banda ", imgOutput.bandNames().getInfo())      
            
            # print("salindo ")
            # print("image banda addicionada ", imgOutput.bandNames().getInfo())

            # sys.exit()
            # imgOutput = imgOutput.select(self.lstbandNames)

        elif self.options['janela_output'] == 5:
            self.colectAnos = [self.mapeiaAnos(ano, self.options['janela_output'], self.yearsInv) for ano in self.yearsInv]   
            rasterC1 = None
            rasterC2 = None  
            rasterC3 = None
            imgstmp_masks = None
            
            limit_iterations = len(self.colectAnos[: - delta - 1])
            maps_bacias_c = self.imgClass
            # id_class = 3   # classe de floresta 
            # imgOutput = ee.Image().byte()
            print(f"processing class {id_class} == janela {self.options['janela_output']} and delta {delta}")            
            for cc, lstyear in enumerate(self.colectAnos[: ]): # - delta - 1
                # print("  => ", lstyear)
                # band_C1 = lstyear[1]
                # band_C2 = lstyear[2]
                # band_C3 = lstyear[3]
                # rasterReclass = self.reclass_natural_Antropic(maps_bacias_c, lstyear)

               
                if cc > 0  and  cc < 38:  # < len(self.colectAnos) - 3
                    print(f"> {cc} intervalos <==> ", lstyear) 
                    band_C1 = lstyear[1]
                    band_C2 = lstyear[2]
                    band_C3 = lstyear[3]
                    rasterReclass = self.reclass_natural_Antropic(maps_bacias_c, lstyear)
                    if cc == 1:
                        imgstmp_masks = self.mask_5_years(id_class, rasterReclass)

                    elif cc < len(self.colectAnos) - 3:  
                        # print(f"> {band_C1}  intervalos <==> ", lstyear)
                        imgComposta = (rasterC1.addBands(rasterC2)
                                                .addBands(rasterC3)
                                                .addBands(rasterReclass.select(lstyear[3:]))
                                        )
                        imgstmp_masks = self.mask_5_years(id_class, imgComposta)

                    # mudando os pixels dos mapas centrais reclassificados segundo a regra
                    rasterC1 = rasterReclass.select(band_C1).where(imgstmp_masks.eq(1), id_class)
                    rasterC2 = rasterReclass.select(band_C2).where(imgstmp_masks.eq(1), id_class)
                    rasterC3 = rasterReclass.select(band_C3).where(imgstmp_masks.eq(1), id_class)

                    # reemplazar pixels mudados no mapa inicial no primeiro mapado intervalo 
                    map_change_yeart0 = (maps_bacias_c.select(band_C1)
                                        .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                        .rename(band_C1))

                    # print("process t0 ", maps_bacias_c.select([lstyear[-1]]).bandNames().getInfo())
                    map_change_yeart1 = (maps_bacias_c.select(band_C2)
                                            .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                            .rename(band_C2))

                    map_change_yeart2 = (maps_bacias_c.select(band_C3)
                                            .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                            .rename(band_C3))
                    
                    imgOutput = imgOutput.addBands(map_change_yeart0)

                    """
                        atualizando  a matrix dos mapas 
                    """
                    if cc < 37:
                       # print(self.lstbandsInv[:cc])
                        maps_bacias_c = (maps_bacias_c.select(self.lstbandsInv[: cc])
                                                    .addBands(map_change_yeart0)
                                                    .addBands(map_change_yeart1)
                                                    .addBands(map_change_yeart2)
                                                    .addBands(maps_bacias_c.select(self.lstbandsInv[cc + delta :]))                                          
                                            )   
                    else:
                        imgOutput = imgOutput.addBands(map_change_yeart1)
                        imgOutput = imgOutput.addBands(map_change_yeart2)       

                else:
                    if cc == 0:
                        print(f"> {cc} intervalos <==> ", lstyear, "  ", self.lstbandNames[-1]) 
                        imgOutput = imgOutput.addBands(self.imgClass.select(self.lstbandNames[-1]))
                

                
            # print("salindo ")
            imgOutput = imgOutput.addBands(self.imgClass.select(self.lstbandNames[0]))
            print("image banda addicionada ", imgOutput.bandNames().getInfo())
            # imgOutput =  imgOutput.select(self.lstbandNames)
            # sys.exit()

        elif self.options['janela_output'] == 6:

            self.colectAnos = [self.mapeiaAnos(ano, self.options['janela_output'], self.yearsInv) for ano in self.yearsInv]   
            rasterC1 = None
            rasterC2 = None  
            rasterC3 = None
            rasterC4 = None
            imgstmp_masks = None
            
            # limit_iterations = len(self.colectAnos[: - delta - 1])
            maps_bacias_c = self.imgClass
            # id_class = 3   # classe de floresta 
            # imgOutput = ee.Image().byte()
            print("processing class {} == janela_output {} ".format(id_class, self.options['janela_output']))            
            for cc, lstyear in enumerate(self.colectAnos[:]):  #  - delta - 1
                # print("  => ", lstyear)

                if cc > 0  and cc < 37:
                    print(f"> {cc} intervalos <==> ", lstyear) 
                    band_C1 = lstyear[1]
                    band_C2 = lstyear[2]
                    band_C3 = lstyear[3]
                    band_C4 = lstyear[4]
                    rasterReclass = self.reclass_natural_Antropic(maps_bacias_c, lstyear)

                    if cc == 1:
                        imgstmp_masks = self.mask_6_years(id_class, rasterReclass)

                    elif cc < len(self.colectAnos) - 3:  
                        # print(f"> {band_C1}  intervalos <==> ", lstyear)
                        imgComposta = (rasterC1.addBands(rasterC2)
                                                .addBands(rasterC3)
                                                .addBands(rasterC4)
                                                .addBands(self.imgReclass.select(lstyear[4:]))
                                        )
                        imgstmp_masks = self.mask_6_years(id_class, imgComposta)

                    # mudando os pixels dos mapas centrais reclassificados segundo a regra
                    rasterC1 = self.imgReclass.select(band_C1).blend(imgstmp_masks.selfMask())
                    rasterC2 = self.imgReclass.select(band_C2).blend(imgstmp_masks.selfMask())
                    rasterC3 = self.imgReclass.select(band_C3).blend(imgstmp_masks.selfMask())
                    rasterC4 = self.imgReclass.select(band_C4).blend(imgstmp_masks.selfMask())

                    # reemplazar pixels mudados no mapa inicial no primeiro mapado intervalo 
                    map_change_yeart0 = (maps_bacias_c.select(band_C1)
                                        .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                        .rename(band_C1))

                    # print("process t0 ", maps_bacias_c.select([lstyear[-1]]).bandNames().getInfo())
                    map_change_yeart1 = (maps_bacias_c.select(band_C2)
                                            .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                            .rename(band_C2))

                    map_change_yeart2 = (maps_bacias_c.select(band_C3)
                                            .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                            .rename(band_C3))

                    map_change_yeart3 = (maps_bacias_c.select(band_C4)
                                            .blend(maps_bacias_c.select([lstyear[-1]]).updateMask(imgstmp_masks))
                                            .rename(band_C4))
                    
                    imgOutput = imgOutput.addBands(map_change_yeart0)

                    """
                        atualizando  a matrix dos mapas 
                    """
                    if cc < 36:
                       # print(self.lstbandsInv[:cc])
                        maps_bacias_c = (maps_bacias_c.select(self.lstbandsInv[: cc])
                                                    .addBands(map_change_yeart0)
                                                    .addBands(map_change_yeart1)
                                                    .addBands(map_change_yeart2)
                                                    .addBands(map_change_yeart3)
                                                    .addBands(maps_bacias_c.select(self.lstbandsInv[cc + delta + 1 :]))                                          
                                            )   
                        # if cc < 3:
                        #     print(" ver ", maps_bacias_c.bandNames().getInfo())

                    else:
                        imgOutput = imgOutput.addBands(map_change_yeart1)
                        imgOutput = imgOutput.addBands(map_change_yeart2)       
                        imgOutput = imgOutput.addBands(map_change_yeart3) 
                else:
                    if cc == 0:
                        print(f"> {cc} intervalos <==> ", lstyear, "  ", self.lstbandNames[-1]) 
                        imgOutput = imgOutput.addBands(self.imgClass.select(self.lstbandNames[-1]))
                
                

                
            # print("salindo ")
            # print("image banda addicionada ", imgOutput.bandNames().getInfo())
            # imgOutput = imgOutput.select(self.lstbandNames)
            # sys.exit()
        
        # print(imgClass.bandNames().getInfo())
        imClass = ee.Image().byte()
        for bndYY in self.lstbandNames:
            imClass = imClass.addBands(imgOutput.select(bndYY))
        
        imClass = imClass.select(self.lstbandNames[:])

        imClass = (imClass.updateMask(self.bacia_raster)
                        .set(
                            'version',  self.versoutput, 
                            'id_bacias', self.id_bacias,
                            'biome', 'CAATINGA',
                            'type_filter', 'temporal',
                            'collection', '10.0',                            
                            'janela', self.options['janela_output'],
                            'sensor', 'Landsat',
                            'num_class',  self.options['num_classes'],
                            'system:footprint' , self.geom_bacia
                        ))
        
        name_toexport = f"filterTP_BACIA_{self.id_bacias}_GTB_J{self.options['janela_output']}_V{self.versoutput}_{self.options['num_classes']}cc"
        self.processoExportar(imClass, name_toexport, self.geom_bacia)    
        # sys.exit()

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc, geom_bacia):
        
        idasset =  os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId': idasset, 
            'region': geom_bacia, #.getInfo()['coordinates'],
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
    'numeroLimit': 20,
    'conta' : {
        '0': 'caatinga01',
        '4': 'caatinga02',
        '6': 'caatinga03',
        '8': 'caatinga04',
        '10': 'caatinga05',        
        '12': 'solkan1201',    
        '14': 'solkanGeodatin',
        '16': 'superconta'      
    }
}
relatorios = open("relatorioTaskXContas.txt", 'a+')
#============================================================
#========================METODOS=============================
#============================================================
def gerenciador(cont):    
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)
    
    if str(cont) in numberofChange:
        
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 

        # tasks(n= param['numeroTask'], return_list= True) 
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:            
            relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont


listaNameBacias = [
    '765', '7544', '7541','746', '7591', '7592',  '7411', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751',     
    '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752',
]
# listaNameBacias = [ "7613","7746","7754","7741","773","761112","7591","7581","757"]
# listaNameBacias = [ "7613","7746","7741","7591","7581","757"] #
# listaNameBacias = ["7591"]
# listaNameBacias = ['7411', '7422', '751', '752', '753', '7541' ]
# listaNameBacias = ['7411'] 
print("ver quantidad ", len(listaNameBacias))
# sys.exit()

lstBacias = []
changeAcount = False
lstqFalta =  []
cont = 16
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_int'
if changeAcount:
    cont = gerenciador(cont)
version = 1
janela = 3
num_classes = 7
modelo = 'GTB'
listBacFalta = []
knowMapSaved = False
show_interval = True
for cc, idbacia in enumerate(listaNameBacias[:]):   
    if knowMapSaved:
        try:
            nameMap = f"filterTP_BACIA_{idbacia}_GTB_J{janela}_V{version}_{num_classes}cc"
            # # nameMap = 'filterSP_BACIA_'+ str(idbacia) + "_V" + str(version)
            # print(nameMap)
            imgtmp = ee.Image(os.path.join(input_asset, nameMap))
            # imgtmp = (ee.ImageCollection(input_asset)
            #                 # .filter(ee.Filter.eq('version', version))
            #                 .filter(ee.Filter.eq('id_bacia', idbacia ))
            #                 .first()
            #     )
            # print("know how many images exist ", imgtmp.size().getInfo())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}", len(imgtmp.bandNames().getInfo()), "bandas ✅ ")
        except:
            listBacFalta.append(idbacia)
    else: 
        if idbacia not in lstBacias:
            # cont = gerenciador(cont)            
            print("----- PROCESSING BACIA {} -------".format(idbacia)) 
            aplicando_TemporalFilter = processo_filterTemporal(idbacia)            
            aplicando_TemporalFilter.applyTemporalFilter(show_interval)
            if cc == 0:
                show_interval = False
        # sys.exit()