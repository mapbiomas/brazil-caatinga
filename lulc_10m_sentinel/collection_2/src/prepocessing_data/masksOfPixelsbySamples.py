#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
# import json
# import csv
import sys
# import arqParametros as arqParam
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


class ClassMosaic_indexs_Spectral(object):

    feat_pts_true = ee.FeatureCollection([])
    # default options
    options = {
        "bandas": ['B2', 'B3', 'B4', 'B8', 'B9', 'B11', 'B12', 'MSK_CLDPRB'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 4, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_baciasN2': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
        'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsv1N245',
        'assetMapbiomas71': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
        'assetMapbiomas80': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        # 'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_fire': 'projects/mapbiomas-public/assets/brazil/fire/collection3/mapbiomas_fire_collection3_annual_burned_v1',
        'asset_befFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_S1v18',
        'asset_filtered': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Tp',
        'asset_alerts_SAD': 'users/data_sets_solkan/Alertas/layersImgClassTP_2024_02',
        'asset_alerts_Desf': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_deforestation_secondary_vegetation_v2',
        'asset_transitions_maps': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_transitions_v1',
        'asset_Coincidencia': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_coinciden',
        'asset_estaveis': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_estaveis_v2',
        'asset_fire_mask': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5',
        'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',     
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample',   
        "anoIntInit": 1985,
        "anoIntFin": 2023,
        'janela': 3
    }
    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self, lst_year):

        self.regionInterest = ee.FeatureCollection(self.options['assetrecorteCaatCerrMA'])
        self.imgMosaic = ee.ImageCollection(self.options['asset_mosaic_mapbiomas']
                                                    ).filterBounds(self.regionInterest)
        self.lst_year = lst_year
        # # @collection6 bruta: mapas de uso e cobertura Mapbiomas ==> para masquear as amostra fora de mascara
        # self.collection_bruta = ee.ImageCollection(self.options['assetMapbiomas71']).min()
        # self.img_mask = self.collection_bruta.unmask(100).eq(100).reduce(ee.Reducer.sum())
        # self.img_mask = self.img_mask.eq(0).selfMask()
        self.baciabuffer = ee.FeatureCollection(self.options['asset_bacias_buffer'])
        # @collection9: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection90 = ee.Image(self.options['assetMapbiomas90'])
        # mask of areas where don´t haven´t desforestations
        self.AlertasSAD = ee.Image(self.options['asset_alerts_SAD']).unmask(0).eq(0)

        # Remap todas as imagens mapbiomas
        lsBndMapBiomnas = []
        # self.imgMapbiomas = ee.Image().toByte()

        # for year in lst_year:
        #     band = 'classification_' + str(year)
        #     lsBndMapBiomnas.append(band)

        #     imgTemp = collection90.select(band).remap(
        #         self.options['classMapB'], self.options['classNew'])
        #     self.imgMapbiomas = self.imgMapbiomas.addBands(
        #         imgTemp.rename(band))

        # self.imgMapbiomas = self.imgMapbiomas.select(lsBndMapBiomnas)#.clip(self.regionInterest.geometry())
        self.imgMapbiomas = collection90
        # self.imgMapbiomas = self.imgMapbiomas.updateMask(self.img_mask)

        self.baciasN2 = ee.FeatureCollection(self.options['asset_baciasN2'])
    

    #retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1999, o metodo retornaria
    #['classification_1997', 'classification_1998', 'classification_1999', 'classification_2000', 'classification_2001']
    #desse jeito pode-se extrair as bandas referentes as janelas
    def mapeiaWindows_5_year(self, ano, janela, anos):

        lsBandAnos = ['classification_'+str(item) for item in anos]
        
        primeiroAno = anos[0]
        ultimoAno = anos[-1]
        indice = anos.index(ano)
        
        if ano == primeiroAno:
            return lsBandAnos[0:janela]
        
        elif ano == anos[1]:
            return lsBandAnos[0:janela]
        
        elif ano == anos[-2]:
            return lsBandAnos[-janela:]
        
        elif ano == ultimoAno:
            return lsBandAnos[-janela:]
        
        else:
            return lsBandAnos[indice - 2: indice + 3]
    
    def mapeiaWindows_3_year(self, ano, janela, anos):

        lsBandAnos = ['classification_'+str(item) for item in anos]
        
        primeiroAno = anos[0]
        ultimoAno = anos[-1]
        indice = anos.index(ano)
        
        if ano == primeiroAno:
            return lsBandAnos[0:janela] 

        elif ano == ultimoAno:
            return lsBandAnos[-janela:]
        
        else:
            return lsBandAnos[indice - 1: indice + 2]

    #  ver aqui apresentação 
    # https://docs.google.com/presentation/d/1sYceKjmR9FXa8kvuGbMQgmqbONtA9yBz/edit#slide=id.p14
    def get_coincidecia_mapCol_last3(self, _nbacia): 
        shp_recort = ee.FeatureCollection(self.options['assetrecorteCaatCerrMA']).geometry()
        # mask_pixels_incident = ee.Image().byte()
            
             
        print("path =", self.options["assetMapbiomas90"])        

        baciaselect = self.baciabuffer.filter(
                            ee.Filter.eq('nunivotto4', _nbacia)).first().geometry() 

        mapLULCcol71 = ee.Image(self.options["assetMapbiomas71"]).clip(baciaselect)
        mapLULCcol80 = ee.Image(self.options["assetMapbiomas80"]).clip(baciaselect)
        mapLULCcol90 = ee.Image(self.options["assetMapbiomas90"]).clip(baciaselect)
        lstBands = []
        rasterMaps = ee.Image.constant(0).clip(baciaselect);

        for yyear in self.lst_year[:-2]: # até 2021
            print("mapsLULC doing .. ", yyear )  
            bnd_activa = "classification_" + str(yyear)
            bnd_class = 'classes_'+ str(yyear)
            # join all map layer years join 
            mapLULCcol71YY = mapLULCcol71.select(bnd_activa).remap(
                                self.options["classMapB"], self.options["classNew"])            
            mapLULCcol71YY = mapLULCcol71YY.select(['remapped'], [bnd_activa])
            
            mapLULCcol80YY = mapLULCcol80.select(bnd_activa).remap(
                                self.options["classMapB"], self.options["classNew"]
                                    ).select(['remapped'], [bnd_activa])
            
            mapLULCcol90YY = mapLULCcol90.select(bnd_activa).remap(
                                self.options["classMapB"], self.options["classNew"]
                                            ).select(['remapped'], [bnd_activa])

            print("year {} mapLULCcol71 band {}".format(yyear, mapLULCcol90YY.bandNames().getInfo()))
            print("year {} mapLULCcol80 band {}".format(yyear, mapLULCcol90YY.bandNames().getInfo()))
            print("year {} mapLULCcol90 band {}".format(yyear, mapLULCcol90YY.bandNames().getInfo()))
            # sys.exit()
            mapSum = mapLULCcol71YY.addBands(mapLULCcol80YY).addBands(mapLULCcol90YY)            

            incidentes = mapSum.reduce(ee.Reducer.countRuns()).subtract(1).rename('incidentes');
            states = mapSum.reduce(ee.Reducer.countDistinctNonNull()).rename('states')
            moda = mapSum.reduce(ee.Reducer.mode())

            clas2 = incidentes.eq(1).And(mapSum.select(0).subtract(moda).eq(0)).selfMask()
            clas3 = incidentes.eq(1).And(mapSum.select(0).subtract(moda).eq(0)).selfMask()
            clas4 = incidentes.eq(2).And(states.eq(2)).selfMask()
            clas5 = incidentes.eq(2).And(states.eq(3)).selfMask()

            outIncid = incidentes.eq(0).blend(clas2.multiply(2)).blend(
                    clas3.multiply(3)).blend(clas4.multiply(4)).blend(
                        clas5.multiply(5)).rename(bnd_class).toByte()
                    # .addBands(
                    #     incidentes).addBands(states).addBands(
                    #         moda).addBands(mapSum).toByte()
            lstBands.append('coincidencia_' + str(yyear))
            rasterMaps = rasterMaps.addBands(outIncid.rename('coincidencia_' + str(yyear)))
        
        # mask_pixels_incident = mask_pixels_incident.addBands(outIncid)            
        rasterMaps = rasterMaps.select(lstBands).set('type', 'incident', 'bacia', _nbacia)
        name_exportimg = 'masks_pixels_incidentes_' + str(_nbacia)
        self.processoExportarImage(rasterMaps,  name_exportimg, baciaselect, 'coincidencia')
            # sys.exit()

    # https://code.earthengine.google.com/d5a965bbb6b572306fb81baff4bd401b
    def get_class_maskAlerts(self, yyear):
        #  get from ImageCollection 
        janela = 5
        intervalo_bnd_years = ['classification_' + str(kk) for kk in self.lst_year[1:] if kk <= yyear and kk > yyear - janela]
        maskAlertyyear = ee.Image(self.options['asset_alerts_Desf']).select(intervalo_bnd_years)\
                                    .divide(100).toUint16().eq(4).reduce(ee.Reducer.sum())
        return maskAlertyyear.eq(0).rename('mask_alerta')        

    def get_class_maskFire(self, yyear):
        nameFireMask = 'masks_fire_wind5_' + str(yyear)
        maskFireyyear = ee.Image(self.options['asset_fire_mask'] + "/" + nameFireMask)\
                                    .unmask(0).eq(0).rename('mask_fire')
        return maskFireyyear

    def get_class_estatics_pixels(self, _nbacia):        

        baciaselect = self.baciabuffer.filter(
                            ee.Filter.eq('nunivotto4', _nbacia)).first().geometry() 

        rasterMapBac = self.imgMapbiomas.clip(baciaselect)
        lstBands = []
        rasterMaps = ee.Image.constant(0).clip(baciaselect);
        for yyear in self.lst_year:
            if self.options['janela'] > 3:
                intervalo_years = self.mapeiaWindows_5_year(yyear, self.options['janela'], self.lst_year)            
            else:
                # print("processing janela ", self.options['janela'])
                intervalo_years = self.mapeiaWindows_3_year(yyear, self.options['janela'], self.lst_year)
            print("intervalo ", intervalo_years)
            imgTemp = rasterMapBac.select(intervalo_years)

            #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
            pixelsVariante =  imgTemp.reduce(ee.Reducer.countDistinct())
            lstBands.append('mask_estavel_'+ str(yyear))
            maksEstaveis = pixelsVariante.eq(1).rename('mask_estavel_'+ str(yyear))
            rasterMaps = rasterMaps.addBands(maksEstaveis.selfMask())
        # sys.exit()
        rasterMaps = rasterMaps.select(lstBands).set('type', 'estavel', 'bacia', _nbacia)
        name_exportimg = 'masks_estatic_pixels_v2_' + str(_nbacia)
        self.processoExportarImage(rasterMaps,  name_exportimg, baciaselect, 'estavel')

    def get_mask_Fire_estatics_pixels(self, _nbacia, exportFire):
        janela = 5
        baciaselect = self.baciabuffer.filter(
                            ee.Filter.eq('nunivotto4', _nbacia)).first().geometry() 
        print("lst coordenadas ", len(baciaselect.getInfo()['coordinates']))
        imgColFire = ee.Image(self.options['asset_fire']).clip(baciaselect)                            
        lstBands = []
        rasterFire = ee.Image.constant(0).clip(baciaselect);
        for nyear in self.lst_year:
            intervalo_years = ["burned_area_" + str(kk) for kk in self.lst_year if kk <= nyear and kk > nyear - janela]
            # print(intervalo_years)
            imgTemp = imgColFire.select(intervalo_years).reduce(ee.Reducer.sum()).unmask(0).gt(0)
            # print("image Fire imgTemp ", imgTemp.size().getInfo())

            #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
            lstBands.append('mask5wfire_'+ str(nyear))
            imgTemp = imgTemp.rename('mask5wfire_'+ str(nyear))
            rasterFire = rasterFire.addBands(imgTemp)

        rasterFire = rasterFire.select(lstBands).set('type', 'fire', 'bacia', _nbacia)
        name_exportimg = 'masks_fire_wind5_' + _nbacia

        self.processoExportarImage(rasterFire, name_exportimg, baciaselect, 'fire')


    def export_masks_pixels_changeded_with_filters(self, idname_bacia):

        bacia_tmp = ee.Feature(self.baciasN2.filter(ee.Filter.eq('nunivotto3', idname_bacia)).first())
        # print("show geometry ", bacia_tmp.getInfo())
        bacia_tmp = bacia_tmp.geometry()
        mapsfromRFcc = ee.Image(ee.ImageCollection(self.options['asset_befFilters']).filter(
                                                            ee.Filter.eq('id_bacia', idname_bacia)
                                                                ).first())
        print("Map from RF loaded ", mapsfromRFcc.bandNames().getInfo())

        mapsfromfiltered = ee.Image(ee.ImageCollection(self.options['asset_filtered']).filter(
                                                                ee.Filter.eq('version', '5')).filter(
                                                                    ee.Filter.eq('id_bacia', idname_bacia)
                                                                        ).first())
        print("Map from filterered temporal, gap fill, etc .. ", mapsfromfiltered.bandNames().getInfo())
        lst_bnd_name = []
        mask_pixels_without_change = ee.Image().byte()
        for yyear in range(1985, 2022):
            bnd_select = 'classification_' + str(yyear)
            lst_bnd_name.append(bnd_select)
            tmp_bnd_year = mapsfromfiltered.select(bnd_select).subtract(
                                    mapsfromRFcc.select(bnd_select).rename(bnd_select)                                                          )
            
            mask_pixels_without_change = mask_pixels_without_change.addBands(tmp_bnd_year)
        # sys.exit()
        name_exportimg = 'masks_changes_pixels'

        self.processoExportarImage(mask_pixels_without_change.select(lst_bnd_name),  name_exportimg, bacia_tmp, '')

    def iterate_bacias(self, nomeBacia):

        # colecao responsavel por executar o controle de execucao, caso optem 
        # por executar o codigo em terminais paralelos,
        # ou seja, em mais de um terminal simultaneamente..
        # caso deseje executar num unico terminal, deixar colecao vazia.        
        colecaoPontos = ee.FeatureCollection([])
        # lsNoPtos = []
        
        baciaselect = self.baciabuffer.filter(
                            ee.Filter.eq('nunivotto4', _nbacia)).first().geometry()   

        maksEstaveis = ee.ImageCollection(self.options['asset_estaveis']).filter(
                                                ee.Filter.eq('bacia', nomeBacia))  
        maksEstaveis = maksEstaveis.first()
        # print(maksEstaveis.bandNames().getInfo(), "\n")

        imMasCoinc = ee.ImageCollection(self.options['asset_Coincidencia']).filter(
                                                ee.Filter.eq('bacia', nomeBacia))  
        imMasCoinc = imMasCoinc.first()
        # print(f" imMasCoinc {imMasCoinc.bandNames().getInfo()} \n")
        systemIndexFire = 'masks_fire_wind5_' + str(nomeBacia)
        rasterMaskFire = ee.ImageCollection(self.options['asset_fire_mask']).filter(
                                                ee.Filter.eq('system:index', systemIndexFire))  
        # print(f" rasterMaskFire {rasterMaskFire.size().getInfo()} \n")
        rasterMaskFire = rasterMaskFire.first()
        # print(f" rasterMaskFire {rasterMaskFire.bandNames().getInfo()} \n")

        # sys.exit()         
        lstBands = []
        rasterSample = ee.Image.constant(0).clip(baciaselect);
        for anoCount in range(self.options['anoIntInit'], self.options["anoIntFin"] + 1): #

            bandActiva = 'classification_' + str(anoCount)
            print("banda activa: " + bandActiva)  
            # pixels estaveis em uma janela de 3 anos 
            if anoCount < 2023:
                maksEstaveisYY = maksEstaveis.select('mask_estavel_' + str(anoCount)).eq(1)                
                # mask de fogo com os ultimos 5 anos de fogo mapeado 
                imMaskFireYY = rasterMaskFire.select("mask5wfire_" + str(anoCount)).eq(0)
            else:
                maksEstaveisYY = maksEstaveis.select('mask_estavel_2022').eq(1) 
                imMaskFireYY = rasterMaskFire.select("mask5wfire_2022").eq(0)
            
            # 1 Concordante, 2 concordante recente, 3 discordante recente,
            # 4 discordante, 5 muito discordante
            if anoCount < 2022:
                imMasCoincYY = imMasCoinc.select('coincidencia_' + str(anoCount)).lt(3)
            else:
                imMasCoincYY = imMasCoinc.select('coincidencia_2021').lt(3)                
            

            # map_yearAct = self.imgMapbiomas.select(bandActiva).rename(['class']).clip(baciaselect)
            # imMasCoincYY = imMasCoincYY.rename('coincidencia_' + str(anoCount))
            areaColeta = maksEstaveisYY.multiply(imMaskFireYY).multiply(imMasCoincYY)
            areaColeta = areaColeta.eq(1).rename("mask_sample_" + str(anoCount)) # mask of the area for colects     mask_stable_
            
            # map_yearAct = map_yearAct.updateMask(areaColeta).rename(bandActiva)
            
            rasterSample = rasterSample.addBands(areaColeta)#.addBands(imMasCoincYY)
            # lstBands.append('coincidencia_' + str(anoCount))   
            lstBands.append('mask_sample_' + str(anoCount))                 

            # print("numero de ptos controle ", feat_control_yy.size().getInfo())
            # opcoes para o sorteio estratificadoBuffBacia
            # ptosTemp = map_yearAct.stratifiedSample(
            #     numPoints= 15000,
            #     classBand= 'class',
            #     region= oneBacia,
            #     scale= 30,
            #     dropNulls= True,
            #     # classValues= param['lsClasse'],
            #     # classPoints= param['lsPtos'],
            #     # tileScale= 8,
            #     geometries= True
            # )
            # insere informacoes em cada ft
            # ptosTemp = ptosTemp.filter(ee.Filter.notNull(['class']))
            # merge com colecoes anteriores
            # só se juntar por anop
            # colecaoPontos = colecaoPontos.merge(ptosTemp)
            # name_exp = str(nomeBacia) + "_" + str(anoCount) +"_cv1"  
            # self.save_ROIs_toAsset(ptosTemp, name_exp) 
            
            # sys.exit()
        
        rasterSample = rasterSample.select(lstBands).set('bacia', nomeBacia, 'layer', 'masktoSample')
                   
        name_exportimg = 'masks_pixels_toSample_' + str(nomeBacia)
        self.processoExportarImage(rasterSample,  name_exportimg, baciaselect, 'masktoSample')

    # salva ftcol para um assetindexIni
    def save_ROIs_toAsset(self, collection, name):
        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['outAssetROIs'] + "/" + name
        }

        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()

        print(f"⚡️⚡ exportando ROIs da bacia << {name} >> ...! ⚡️⚡")

    #exporta a imagem classificada para o asset
    def processoExportarImage(self, mapaRF,  nomeDesc, gGeomeB, layername):

        if layername == 'estavel':
            idasset =  self.options['asset_estaveis'] + "/" + nomeDesc
        elif layername == 'coincidencia':
            idasset =  self.options['asset_Coincidencia'] + "/" + nomeDesc
        elif layername == 'fire':
            idasset = self.options['asset_fire_mask'] + "/" + nomeDesc
        elif layername == 'masktoSample':
            idasset = self.options['asset_mask_toSamples'] + "/" + nomeDesc
        lstCoord = []
        if len(gGeomeB.getInfo()['coordinates']) > 1:
            if '7721' in nomeDesc:
                lstCoord = gGeomeB.getInfo()['coordinates'][2]
            elif len(gGeomeB.getInfo()['coordinates'][1][0]) > len(gGeomeB.getInfo()['coordinates'][0][0]):
                print("=======> ", nomeDesc)
                lstCoord = gGeomeB.getInfo()['coordinates'][1]
            else:
                lstCoord = gGeomeB.getInfo()['coordinates'][0]
        else:
            lstCoord = gGeomeB.getInfo()['coordinates']
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region': lstCoord,
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("⚡️⚡️ salvando ... " + nomeDesc + "..! ⚡️⚡")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))


param = {
    'bioma': ["CAATINGA", 'CERRADO', 'MATAATLANTICA'],
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga_49_regions',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    # 'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/PtosXBaciasBalanceados/',
    'janela': 5,
    'escala': 30,
    'sampleSize': 0,
    'metodotortora': True,
    'lsClasse': [3, 4, 12, 15, 18, 21, 22, 33, 29],
    'lsPtos': [3000, 2000, 3000, 1500, 1500, 1000, 1500, 1000, 1000],
    'tamROIsxClass': 4000,
    'minROIs': 1500,
    # "anoColeta": 2015,
    'anoInicial': 1985,
    'anoFinal': 2023,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 42,
    'conta': {
        '0': 'caatinga01',
        '7': 'superconta',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',
        '35': 'solkan1201',
        # '5': 'diegoGmail',
        # '20': 'rodrigo'
    },
}

# limite_bioma = ee.Geometry.Polygon(arqParam.lsPtos_limite_bioma)

biomas = ee.FeatureCollection(param['asset_IBGE']).filter(
    ee.Filter.inList('CD_LEGENDA',  param['bioma']))

# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
list_anos = [k for k in range(param['anoInicial'], param['anoFinal'] + 1)]

print('Analisando desde o ano {} hasta o {} '.format(
    list_anos[0], list_anos[-1]))

# carregando a lista de nomes das bacias
# lsBacias = arqParam.listaNameBacias


#=====================================#
# gerenciador de contas para controlar#
# processos task no gee               #
#=====================================#


def gerenciador(cont, param):

    numberofChange = [kk for kk in param['conta'].keys()]

    if str(cont) in numberofChange:

        gee.switch_user(param['conta'][str(cont)])
        gee.init()
        gee.tasks(n=param['numeroTask'], return_list=True)

    elif cont > param['numeroLimit']:
        cont = 0

    cont += 1
    return cont

cont = 0
# cont = gerenciador(0, param)
export_areas_changed = False
export_pixels_coincid = False
export_pixels_staveis = False
export_wind5_fire = False

# activeMask = False
# revisao da coleção 8 
# https://code.earthengine.google.com/5e8af5ef94684a5769e853ad675fc368

listaNameBacias = [
    # '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    # '752', '7616', '745', '7424', '773', '7612', '7613', 
    # '7618', '7561', '755', '7617', '7564', 
    '761111', 
    # '761112', 
    # '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    # '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    # '7541', 
    '7721', 
    # '772', '7619', '7443', '765', '7544', '7438', 
    # '763', '7591', '7592', '7622', '746'
]
print("⚡️⚡️=== lista de nomes de bacias carregadas === ⚡️⚡️")
# print("=== {} ===".format(listaNameBacias))
objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(list_anos)

for _nbacia in listaNameBacias[:]:
    print("⚡️⚡️ -------------------.kmkl-----------------------------------⚡️⚡️")
    print("⚡️⚡️ --------------    processing bacia " + _nbacia + "------------------ ⚡️⚡️")   
    print("---------------------------------------------------------------------")
    # dict_lstBacias = arqParam.dictlstBacias
    if not export_areas_changed and not export_pixels_coincid and not export_pixels_staveis and not export_wind5_fire:
        # geobacia, colAnos, nomeBacia, dict_nameBN4
        objetoMosaic_exportROI.iterate_bacias(_nbacia)

    elif export_pixels_coincid:
        objetoMosaic_exportROI.get_coincidecia_mapCol_last3(_nbacia)
        # cont = gerenciador(cont, param) 
        
    elif export_pixels_staveis:
        objetoMosaic_exportROI.get_class_estatics_pixels(_nbacia)
        # cont = gerenciador(cont, param)
    
    elif export_wind5_fire:
        objetoMosaic_exportROI.get_mask_Fire_estatics_pixels(_nbacia, True)

    # del objetoMosaic_exportROI
    # sys.exit()

    cont = gerenciador(cont, param)