#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
# https://code.earthengine.google.com/0c432999045898bb6e40c1fb7238d32f
'''

import ee
import os 
import gee
import json
import csv
import copy
import time
import sys
import math
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount) # project='ee-cartassol'
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


class processo_filterTemporal(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Temporal/',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Temporal',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/merge/',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/grass_Aflor',
            'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
            'asset_region_img_buffer': 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',   # 98 imagens the buffer = 1
            'last_year' : 2023,
            'first_year': 2016,
            'janela' : 5,
            'step': 1
        }

    def __init__(self):
        # self.id_bacias = nameBacia
        self.versoutput = 1
        self.versionInput = 1
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer'])
        self.raster_bacia = (
            ee.ImageCollection(self.options['asset_region_img_buffer'])
                    # .filter(ee.Filter.eq('nunivotto4', nameBacia))
                    .filter(ee.Filter.eq('isBuffer', 1))#.first()
        )

        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]  # ,  - 1, -1
        # self.years = [kk for kk in years.sort(reverse= False)]
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['last_year'], self.options['first_year'] - 1, -1)]
        print("lista de anos ", self.years)
        self.lstBandFinal =  ['classification_' + str(yy) for yy in self.years]
        print("lista de anos ", self.lstBandFinal)
        # self.ordem_exec_first = [4,21,4,3,12] #
        # self.ordem_exec_last = [12]  # 29
        self.ordem_exec_middle = [4] # ,33, 22,      21,4,3,12

        self.colectAnos = [self.mapeiaAnos(
                                ano, self.options['janela'], self.years) for ano in self.years]

        # self.colectAnos = [self.mapeiaAnos(
        #                         ano, self.options['janela'], self.years) for ano in self.years]
        # dictYY = {}
        # for cc, lstYY in enumerate(colectAnos):
        #     # print(cc, " <==>  ", lstYY)
        #     dictYY[str(cc)] = lstYY
        # self.colectAnos = []
        # for cc in range(len(self.years)-1, -1, -1):
        #     print(cc, " <> ",dictYY[str(cc)])
        #     self.colectAnos.append(dictYY[str(cc)])

        # sys.exit()
    ################### CONJUNTO DE REGRAS PARA CONSTRUIR A LISTA DE BANDAS ##############
    def regra_primeira(self, jan, delt, lstYears):
        return lstYears[1 : delt + 1] + [lstYears[0]] + lstYears[delt + 1 : jan]
    def regra_primeiraJ4(self, jan, delt, lstYears):
        return [lstYears[1]] + [lstYears[0]] + lstYears[delt : jan]
    def regra_ultima(self, jan, delt, lstYears):
        print(lstYears[-1 * jan : ])
        return lstYears[-1 * jan : -1 *(delt + 1)] + [lstYears[-1]] + lstYears[-1 * (delt + 1) : -1]    
    def regra_segundo_stepJ5(self, jan, delt, lstYears):
        return [lstYears[0]] + [lstYears[1]] + lstYears[delt : jan]
    def regra_antespenultimo_stepJ5(self, jan, delt, lstYears):
        return [lstYears[-5], lstYears[-3]] + [lstYears[-4]] + lstYears[-2:]
    def regra_penultimo_stepJ5(self, jan, delt, lstYears):
        return [lstYears[-5], lstYears[-2]] + lstYears[-4: -2] + [lstYears[-1]]
    def regra_ultimo_stepJ5(self, jan, delt, lstYears):
        return [lstYears[-5], lstYears[-1]] + lstYears[-4: -1]    
    def regra_penultimo_stepJ4(self, jan, delt, lstYears):
        return [lstYears[-1 * jan]] + [lstYears[-2]] + [lstYears[-3]]  + [lstYears[-1]] 
    # retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1Nan999, o metodo retornaria
    # ['classification_1997', 'classification_1998', 'classification_1999', 'classification_2000', 'classification_2001']
    # desse jeito pode-se extrair as bandas referentes as janelas

    def mapeiaAnos(self, ano, janela, anos):
        lsBandAnos = ['classification_'+str(item) for item in anos]
        # print("ultimo ano ", anos[-1])
        indice = anos.index(ano)
        delta = int(janela / 2)
        resto = int(janela % 2)
        ######### LIST OF BANDS FOR WINDOWS 3 #######################
        if janela == 3:
            if ano == self.options['first_year']:
                return self.regra_primeira(janela, delta, lsBandAnos)
            elif ano == anos[-1]: # igual a ultimo ano 
                return self.regra_ultima(janela, delta, lsBandAnos)
            else:
                return lsBandAnos[indice - delta: indice + delta + resto]
        ######### LIST OF BANDS FOR WINDOWS 4 #######################
        elif janela == 4:
            if ano == self.options['first_year']:
                return self.regra_primeiraJ4(janela, delta, lsBandAnos)
            elif ano == anos[1]:
                return lsBandAnos[:janela]
            elif ano == anos[-2]:
                return self.regra_penultimo_stepJ4(janela, delta, lsBandAnos)
            elif ano == anos[-1]:
                return self.regra_ultima(janela, delta, lsBandAnos)
            else:
                return lsBandAnos[indice - 1: indice + delta + 1]
        ######### LIST OF BANDS FOR WINDOWS 3 #######################
        elif janela == 5:
            if ano == self.options['first_year']:
                return self.regra_primeiraJ4(janela, delta, lsBandAnos)
            elif ano == anos[1]:
                return self.regra_segundo_stepJ5(janela, delta, lsBandAnos)
            elif ano == anos[-3]:
                return self.regra_antespenultimo_stepJ5(janela, delta, lsBandAnos)
            elif ano == anos[-2]:
                return self.regra_penultimo_stepJ5(janela, delta, lsBandAnos)
            elif ano == anos[-1]:
                return self.regra_ultimo_stepJ5(janela, delta, lsBandAnos)  
            else:                  
                return lsBandAnos[indice - 1: indice + 2 * delta]    
           
    def mask_3_years (self, valor, imagem):
        #### https://code.earthengine.google.com/1f9dd3ab081d243fa9d7962e06348579
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).eq(valor)).unmask(0)    
        muda_img = imagem.select([1]).mask(mmask.eq(1)).where(mmask.eq(1), valor)
        return imagem.select([1]).blend(muda_img)

    def mask_4_years (self, valor, imagem):
        imagem = ee.Image(imagem)  
        # print("    === > ", imagem.bandNames().getInfo())      
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).neq(valor)).And(
                            imagem.select([3]).eq(valor))
        
        muda_img = imagem.select([1]).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        muda_img_post = imagem.select([2]).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        # print("  <> ", imagem.select([2]).bandNames().getInfo())
        img_out = imagem.select([1]).blend(muda_img).addBands(imagem.select([2]).blend(muda_img_post))
        return img_out

    def mask_5_years (self, valor, imagem):
        # print("imagem bandas ", imagem.bandNames().getInfo())
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
                    imagem.select([1]).neq(valor)).And(
                        imagem.select([2]).neq(valor)).And(
                            imagem.select([3]).neq(valor)).And(
                                imagem.select([4]).eq(valor))
        
        
        muda_img = imagem.select([1]).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        muda_img_post = imagem.select([2]).mask(mmask.eq(1)).where(mmask.eq(1), valor) 
        muda_img_pospos = imagem.select([3]).mask(mmask.eq(1)).where(mmask.eq(1), valor)

        img_out = imagem.select([1]).blend(muda_img).addBands(
                        imagem.select([2]).blend(muda_img_post)).addBands(
                            imagem.select([3]).blend(muda_img_pospos))
        # print("imagem bandas Out ", img_out.bandNames().getInfo())
        return img_out

    def applyTemporalFilter(self, id_bacias, nmodel): 

        baseRasterBacia = self.raster_bacia.filter(ee.Filter.eq('nunivotto4', id_bacias)).first()

        if "Temporal" in self.options['input_asset']:
            name_imgClass = 'filterTP_BACIA_'+ str(id_bacias) + f"_GTB_J{self.options['janela'] - 1}_V" + str(self.versoutput) 
            imgClass = (ee.ImageCollection(self.options['input_asset'])
                                .filter(ee.Filter.eq('id_bacia', id_bacias))
                                .filter(ee.Filter.eq('version',  self.versionInput))
                                .filter(ee.Filter.eq('janela', self.options['janela'] - 1)).first() 
            )
        else:            
            imgClass = (ee.ImageCollection(self.options['input_asset'])
                                .filter(ee.Filter.eq('id_bacia', id_bacias))
                                .filter(ee.Filter.eq('version',  self.versionInput)).first()
                                        )    #.filter(  # self.options['step']
                                                # ee.Filter.eq('filter', 'spatial_use')).first()
        # name_imgClass = 'filterFQ_BACIA_'+ str(id_bacias) + "_V" + str(self.versionTP)

        
        # print(imgClass.size().getInfo())
        print("loading ", imgClass.get('system:index').getInfo()) #.bandNames()
        # self.colectAnos = self.colectAnos[1:]
        
        # print(" --------- lista de bandas -------------\n", self.colectAnos)
        if self.options['janela'] == 3:
            for id_class in self.ordem_exec_middle[:]:
                imgOutput = ee.Image().byte()
                rasterbefore = ee.Image().byte()
                print("processing class {} == janela {} ".format(id_class, self.options['janela'] )) 

                for cc, lstyear in enumerate(self.colectAnos):
                    print(f" {self.options['janela']} => ", lstyear)
                    if cc == 0:                        
                        # print(f" #{cc} show bands ", imgClass.select(lstyear).bandNames().getInfo())                     
                        imgtmp = self.mask_3_years(id_class, imgClass.select(lstyear))
                    elif cc == len(self.colectAnos) - 1:  # ultimo year
                        print(" show bands ", lstyear[1])
                        imgtmp = imgClass.select(lstyear[1])
                    else:                        
                        rasterbefore = imgtmp 
                        imgComposta = rasterbefore.addBands(imgClass.select(lstyear[1:]))
                        # print(f"#{cc} show bands ", imgComposta.bandNames().getInfo())
                        imgtmp = self.mask_3_years(id_class, imgComposta)
                    
                    imgOutput = imgOutput.addBands(imgtmp)
                    # time.sleep(3)
                # sys.exit()
                imgOutput = imgClass.select(self.lstBandFinal[:-1]).addBands(imgOutput.select(['classification_2023']))
                imgClass = imgOutput
                # print("comprovando o número de bandas \n ====>", len(imgOutput.bandNames().getInfo()))
                # sys.exit()
            # for id_class in self.ordem_exec_last:
            #     print("processing last 3 years class = ", id_class)
            #     for lstyear in self.colectAnos:
            #         # print("  => ", lstyear)
            #         if cc == 0:
            #             rasterbefore = imgClass.select(lstyear[0])
            #             # print(f" #{cc} show bands ", imgClass.select(lstyear).bandNames().getInfo())                     
            #             imgtmp = self.mask_3_years(id_class, imgClass.select(lstyear))
            #         elif cc == len(self.colectAnos) - 1:
            #             rasterbefore = imgtmp
            #             # print(" show bands ", rasterbefore.addBands(imgClass.select(lstyear[1])).addBands(imgOutput.select(lstyear[2])).bandNames().getInfo())
            #             imgtmp = self.mask_3_years(id_class, rasterbefore.addBands(imgClass.select(lstyear[1])).addBands(imgOutput.select(lstyear[-1])))
            #         else:                        
            #             rasterbefore = imgtmp   
            #             # print(f"#{cc} show bands ", imgClass.select(lstyear[:2]).addBands(rasterbefore).bandNames().getInfo())
            #             imgtmp = self.mask_3_years(id_class, imgClass.select(lstyear[:2]).addBands(rasterbefore))
            #         imgOutput = imgOutput.addBands(imgtmp)

            #     imgOutput = imgOutput.select(self.lstbandNames)
            #     imgClass = imgOutput
            #     print("comprovando o número de bandas \n ====>", len(imgOutput.bandNames().getInfo()))


        elif self.options['janela'] == 4:
            imageTranscicao = None
            self.colectAnos = [self.mapeiaAnos(
                                    ano, self.options['janela'], self.years) for ano in self.years]   
            for id_class in self.ordem_exec_middle[:]:
                imgOutput = ee.Image().byte()
                print("processing class {} == janela {} ".format(id_class, self.options['janela']))            
                for cc, lstyear in enumerate(self.colectAnos):
                    print(f" {self.options['janela']} => ", lstyear)
                    if cc == 0:
                        # print(f" #{cc} => ", imgClass.select(lstyear).bandNames().getInfo()) 
                        # imgtmp = self.mask_4_years(id_class, imgClass.select(lstyear))
                        imgstmp = imgClass.select(lstyear[1])
                        imageTranscicao = imgstmp
                        # print("transcição ", imageTranscicao.bandNames().getInfo())

                        imgOutput = imgOutput.addBands(imgstmp)
                        
                            
                    elif cc == 1: 
                        imgComposta =  imgClass.select(lstyear)                    
                        # print(f" #{cc} =>  {imgComposta.bandNames().getInfo()}  cc")
                        imgstmp = self.mask_4_years(id_class, imgComposta)
                        imageTranscicao = imgstmp.select([1])
                        # print("par de imagens ", imgstmp.bandNames().getInfo())
                        # print("transcição ", imageTranscicao.bandNames().getInfo())
                        imgOutput = imgOutput.addBands(imgstmp.select([0]))

                    elif cc < len(self.colectAnos) - 2:                        
                        # if cc == 3:
                        imgComposta = imgOutput.select(lstyear[0]).addBands(imageTranscicao).addBands(imgClass.select(lstyear[2:]))
                        # else:
                        #     imgComposta = imgClass.select(lstyear[0]).addBands(imageTranscicao).addBands(imgOutput.select(lstyear[2:]))
                        # print("   ", lstyear)                   
                        # print(f" #{cc} =>  {imgComposta.bandNames().getInfo()}  cc")
                        imgstmp = self.mask_4_years(id_class,imgComposta )
                        imageTranscicao = imgstmp.select([1])
                        # print("transcição ", imageTranscicao.bandNames().getInfo())
                        imgOutput = imgOutput.addBands(imgstmp.select([0]))
                    
                    elif cc == len(self.colectAnos) - 2:
                        # print("transcição ", imageTranscicao.bandNames().getInfo())
                        imgOutput = imgOutput.addBands(imageTranscicao)                        
                    
                    else:                        
                        imgstmp = imgClass.select(lstyear[1])                    
                        imgOutput = imgOutput.addBands(imgstmp)
                
                # print("image banda addicionada ", imgOutput.bandNames().getInfo())
                imgOutput = imgOutput.select(self.lstbandNames)
                imgClass = imgOutput
                # print("comprovando o número de bandas \n ====>", len(imgOutput.bandNames().getInfo()))
                # if id_class ==  self.ordem_exec_middle[0]:
                # print(imgOutput.bandNames().getInfo())

            # time.sleep(5)
        
        elif self.options['janela'] == 5:
            imageT1 = None
            imageT2 = None
            self.colectAnos = [self.mapeiaAnos(
                                    ano, self.options['janela'], self.years) for ano in self.years]   

            for id_class in self.ordem_exec_middle:
                imgOutput = ee.Image().byte()
                print("processing class {} == janela {} ".format(id_class, self.options['janela']))            
                for cc, lstyear in enumerate(self.colectAnos):
                    # print("  => ", lstyear)
                    if cc == 0:
                        # print(f" #{cc} => ", imgClass.select(lstyear).bandNames().getInfo()) 
                        imgstmp = imgClass.select(lstyear[1])
                        imageT1 = imgstmp.select(lstyear[1])
                        # print("    ", imgstmp.bandNames().getInfo())
                        imgOutput = imgOutput.addBands(imgstmp)

                    elif cc < len(self.colectAnos) - 3:  
                        if cc == 1:   
                            # print(" Com cc = 1")
                            imgComposta =  imgClass.select(lstyear)                            
                        else:
                            imgComposta = imgOutput.select(lstyear[0]).addBands(imageT1).addBands(imageT2).addBands(imgClass.select(lstyear[3:]))                
                        
                        # print(f" #{cc} =>  {imgComposta.bandNames().getInfo()}  cc")
                        imgstmpM = self.mask_5_years(id_class, imgComposta)
                        imageT1 = imgstmpM.select([1])
                        imageT2 = imgstmpM.select([2])
                        imgOutput = imgOutput.addBands(imgstmpM.select([0]))
                        # if cc < 3:
                        #     print(f" {imgstmpM.select([0]).bandNames().getInfo()} | {imageT1.bandNames().getInfo()} | {imageT2.bandNames().getInfo()} ")
                    elif cc == len(self.colectAnos) - 3:
                        # print("transcição ", imageTranscicao.bandNames().getInfo())
                        imgOutput = imgOutput.addBands(imageT1) 
                    elif cc == len(self.colectAnos) - 2:
                        # print("transcição ", imageTranscicao.bandNames().getInfo())
                        imgOutput = imgOutput.addBands(imageT2)       
                    else:                    
                        imgstmp = imgClass.select(lstyear[1])                    
                        imgOutput = imgOutput.addBands(imgstmp)
                    
                # print("image banda addicionada ", imgOutput.bandNames().getInfo())
                imgOutput = imgOutput.select(self.lstbandNames)
                imgClass = imgOutput
                # print("comprovando o número de bandas \n ====>", len(imgOutput.bandNames().getInfo()))
                # if id_class ==  self.ordem_exec_middle[0]:
                #     print(imgOutput.bandNames().getInfo())
        
                # syy.exit()
        # lst_band_conn = [bnd + '_conn' for bnd in self.lstbandNames]
        # # / add connected pixels bands
        # imageFilledConnected = imgClass.addBands(
        #                             imgClass.connectedPixelCount(10, True).rename(lst_band_conn))
        geom = self.geom_bacia.filter(ee.Filter.eq('nunivotto4', id_bacias)).first().geometry()
        print(imgClass.bandNames().getInfo())
        imageFilledConnected = imgClass.set(
                            'version',  self.versoutput, 
                            'biome', 'CAATINGA',
                            'type_filter', 'temporal',
                            'source', 'geodatin',
                            'model', nmodel,
                            'collection', '2.0',
                            'id_bacia', id_bacias,
                            'janela', self.options['janela'],
                            'sensor', 'Sentinel', 
                            'system:footprint' , geom
                        )
        imageFilledConnected = ee.Image.cat(imageFilledConnected).updateMask(baseRasterBacia)
        
        name_toexport = 'filterTP_BACIA_'+ str(id_bacias) + f"_{nmodel}_J{self.options['janela']}_V" + str(self.versoutput)
        self.processoExportar(imageFilledConnected, name_toexport, geom)    
        # sys.exit()

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc, geom_bacia):
        
        idasset =  self.options['output_asset'] + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region': geom_bacia.getInfo()['coordinates'],
            'scale': 10, 
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
    'numeroLimit': 50,
    'conta' : {
        '0': 'caatinga01',
        '3': 'caatinga02',
        '6': 'caatinga03',
        '9': 'caatinga04',
        '12': 'caatinga05',        
        '15': 'solkan1201',    
        '18': 'solkanGeodatin',
        # '16': 'diegoUEFS' ,
        '21': 'superconta'      
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
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!')        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont


listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766',  '753', '764', '7619',    
    '7541', '7721', '772',  '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746', '7746',
    # '7591', '7592', '7622','757'
]


lstBacias = []
#'7421', '746', '764', '765', '772', '7741', '777',


aplicando_TemporalFilter = processo_filterTemporal()
# sys.exit()
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3/'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Temporal/'

version = 1
janela = 3
cont = 21
modelo = "GTB"
listBacFalta = []
knowMapSaved = False
for cc, idbacia in enumerate(listaNameBacias[-2:]):   
    if knowMapSaved:
        try:
            if 'Spatial' in input_asset:
                nameMap = 'filterSPU_BACIA_' + idbacia + f"_{modelo}_V" + str(version)
            else:
                nameMap = 'filterTP_BACIA_'+ idbacia + f"_GTB_J{janela}_V" + str(version)
            print(input_asset + nameMap)
            imgtmp = ee.Image(input_asset + nameMap)
            print(f" {cc} loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), "bandas ")
            if cc == 0:
                print('show bands \n ', imgtmp.bandNames().getInfo())
        except:
            listBacFalta.append(idbacia)
    else: 
        if idbacia not in lstBacias:
            cont = gerenciador(cont)
            print("----- PROCESSING BACIA {} -------".format(idbacia))        
            aplicando_TemporalFilter.applyTemporalFilter(idbacia, modelo)


if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))