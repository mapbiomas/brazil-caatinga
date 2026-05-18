#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
import json
import csv
import sys
import arqParametros as arqParam
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
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18,  4,  4, 21],
        'asset_baciasN2': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
        'asset_baciasN4': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4',
        'outAssetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv2N4',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas5': 'projects/mapbiomas-workspace/public/collection5/mapbiomas_collection50_integration_v1',
        'assetMapbiomas6': 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
        'assetMapbiomas71': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_fire': 'projects/mapbiomas-workspace/FOGO_COL2/SUBPRODUTOS/mapbiomas-fire-collection2-annual-burned-v1',
        'asset_befFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classification_Col71_S1v18',
        'asset_filtered': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Tp',
        'asset_alerts': 'users/data_sets_solkan/Alertas/layersClassTP',
        'asset_output_mask' : 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/masks/maks_layers',
        'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
        "anoIntInit": 1985,
        "anoIntFin": 2022,
        'janela': 3
    }
    lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self, lst_year, masksactives):

        self.regionInterest = ee.FeatureCollection(self.options['assetrecorteCaatCerrMA'])
        self.imgMosaic = ee.ImageCollection(self.options['asset_mosaic_mapbiomas']
                                                    ).filterBounds(self.regionInterest)
        self.lst_year = lst_year
        # # @collection6 bruta: mapas de uso e cobertura Mapbiomas ==> para masquear as amostra fora de mascara
        # self.collection_bruta = ee.ImageCollection(self.options['assetMapbiomas71']).min()
        # self.img_mask = self.collection_bruta.unmask(100).eq(100).reduce(ee.Reducer.sum())
        # self.img_mask = self.img_mask.eq(0).selfMask()

        # @collection71: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        collection71 = ee.Image(self.options['assetMapbiomas71'])

        # Remap todas as imagens mapbiomas
        lsBndMapBiomnas = []
        self.imgMapbiomas = ee.Image().toByte()

        for year in lst_year:
            band = 'classification_' + str(year)
            lsBndMapBiomnas.append(band)

            imgTemp = collection71.select(band).remap(
                self.options['classMapB'], self.options['classNew'])
            self.imgMapbiomas = self.imgMapbiomas.addBands(
                imgTemp.rename(band))

        self.imgMapbiomas = self.imgMapbiomas.select(lsBndMapBiomnas).clip(self.regionInterest.geometry())
        # self.imgMapbiomas = self.imgMapbiomas.updateMask(self.img_mask)

        self.baciasN2 = ee.FeatureCollection(self.options['asset_baciasN2'])
        colectAnos = []
    

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
    def get_coincidecia_mapCol_last3(self, yyear): 
        shp_recort = ee.FeatureCollection(self.options['assetrecorteCaatCerrMA']).geometry()
        # mask_pixels_incident = ee.Image().byte()

            
        print("mapsLULC doing .. ", yyear )       
        print("path =", self.options["assetMapbiomas5"])
        bnd_activa = "classification_" + str(yyear)
        bnd_class = 'classes_'+ str(yyear)
        # join all map layer years join 
        mapLULCcol5 = ee.Image(self.options["assetMapbiomas5"]).select(bnd_activa).remap(
                            self.options["classMapB"], self.options["classNew"])            
        mapLULCcol5 = mapLULCcol5.select(['remapped'], [bnd_activa])
        mapLULCcol6 = ee.Image(self.options["assetMapbiomas6"]).select(bnd_activa).remap(
                            self.options["classMapB"], self.options["classNew"]).select(['remapped'], [bnd_activa])
        mapLULCcol71 = ee.Image(self.options["assetMapbiomas71"]).select(bnd_activa).remap(
                            self.options["classMapB"], self.options["classNew"]).select(['remapped'], [bnd_activa])

        print("year {} mapLULCcol5 band {}".format(yyear, mapLULCcol5.bandNames().getInfo()))
        print("year {} mapLULCcol6 band {}".format(yyear, mapLULCcol6.bandNames().getInfo()))
        print("year {} mapLULCcol71 band {}".format(yyear, mapLULCcol71.bandNames().getInfo()))

        mapSum = mapLULCcol5.addBands(mapLULCcol6).addBands(mapLULCcol71)

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
        # mask_pixels_incident = mask_pixels_incident.addBands(outIncid)            
        outIncid = outIncid.set('type', 'incident')
        name_exportimg = 'masks_pixels_incidentes_' + str(yyear)
        self.processoExportarImage(outIncid,  name_exportimg, shp_recort)
            # sys.exit()

    # https://code.earthengine.google.com/d5a965bbb6b572306fb81baff4bd401b
    def get_class_maskAlerts(self, yyear):
        #  get from ImageCollection 
        maskAlertyyear = ee.ImageCollection(self.options['asset_alerts']).filter(ee.Filter.eq('yearDep', yyear)
                                ).reduce(ee.Reducer.max()).eq(0).rename('mask_alerta')

        return maskAlertyyear        

    def get_class_maskFire(self, yyear):
        maskFireyyear = ee.Image(self.options['asset_fire']).select("burned_area_" + str(yyear)
                                    ).unmask(0).eq(0).rename('mask_fire')

        return maskFireyyear

    def get_class_estatics_pixels(self, yyear):

        if self.options['janela'] > 3:
            intervalo_years = self.mapeiaWindows_5_year(yyear, self.options['janela'], self.lst_year)
            
        else:
            intervalo_years = self.mapeiaWindows_3_year(yyear, self.options['janela'], self.lst_year)

        imgTemp = self.imgMapbiomas.select(intervalo_years)

        #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
        pixelsVariante =  imgTemp.reduce(ee.Reducer.countDistinct())
        maksEstaveis = pixelsVariante.eq(1).rename('mask_estavel_'+ str(yyear))
        maksEstaveis = maksEstaveis.set('type', 'estavel')
        name_exportimg = 'masks_estatic_pixels_' + str(yyear)
        self.processoExportarImage(maksEstaveis,  name_exportimg, self.regionInterest.geometry())

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
        self.processoExportarImage(mask_pixels_without_change.select(lst_bnd_name),  name_exportimg, bacia_tmp)

    def iterate_bacias(self, nomeBacia):

        # colecao responsavel por executar o controle de execucao, caso optem 
        # por executar o codigo em terminais paralelos,
        # ou seja, em mais de um terminal simultaneamente..
        # caso deseje executar num unico terminal, deixar colecao vazia.        
        colecaoPontos = ee.FeatureCollection([])
        # lsNoPtos = []
        
        oneBacia = self.baciasN2.filter(
            ee.Filter.eq('nunivotto3', nomeBacia)).geometry()            

        for anoCount in range(self.options['anoIntInit'], self.options["anoIntFin"]):

            bandActiva = 'classification_' + str(anoCount)
            # print("banda activa: " + bandActiva)  
            m_assetPixE = self.options['asset_output_mask'] + '/masks_estatic_pixels_'+ str(anoCount)
            maksEstaveis = ee.Image(m_assetPixE).rename('estatic')  

            map_yearAct = self.imgMapbiomas.select(bandActiva).rename(['class'])

            imMaskFire = self.get_class_maskFire(anoCount)
            imMaskFire = imMaskFire.multiply(maksEstaveis)
              

            if anoCount >= 2020:
                imMaksAlert = self.get_class_maskAlerts(anoCount)
                imMaskFire = imMaskFire.multiply(imMaksAlert)
                
            else:
                m_asset = self.options['asset_output_mask'] + '/masks_pixels_incidentes_'+ str(anoCount)
                imMaskInc = ee.Image(m_asset).rename('incident')     
                


            map_yearAct = map_yearAct.updateMask(imMaskFire).addBands(
                                    ee.Image.constant(int(anoCount)).rename('year')).addBands(
                                        imMaskInc) 
            map_yearAct = map_yearAct.clip(oneBacia.bounds())                        

            # print("numero de ptos controle ", feat_control_yy.size().getInfo())
            # opcoes para o sorteio estratificadoBuffBacia
            ptosTemp = map_yearAct.stratifiedSample(
                numPoints= 15000,
                classBand= 'class',
                region= oneBacia,
                scale= 30,
                # classValues= param['lsClasse'],
                # classPoints= param['lsPtos'],
                tileScale= 8,
                geometries= True
            )
            # insere informacoes em cada ft
            ptosTemp = ptosTemp.filter(ee.Filter.notNull(['class']))
            # merge com colecoes anteriores
            colecaoPontos = colecaoPontos.merge(ptosTemp)
            
            # sys.exit()
            name_exp = str(nomeBacia) + "_" + str(nomeBacia) + "_" + str(anoCount) +"_c1"  
            self.save_ROIs_toAsset(colecaoPontos, name_exp)        

    
    # salva ftcol para um assetindexIni
    def save_ROIs_toAsset(self, collection, name):

        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['outAssetROIs'] + "/" + name
        }

        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()

        print("exportando ROIs da bacia $s ...!", name)



    #exporta a imagem classificada para o asset
    def processoExportarImage(self, mapaRF,  nomeDesc, gGeomeB):
        
        idasset =  self.options['asset_output_mask'] + "/" + nomeDesc
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region': gGeomeB.getInfo()['coordinates'],
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
    'bioma': ["CAATINGA", 'CERRADO', 'MATAATLANTICA'],
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
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
    'anoFinal': 2022,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta': {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',
        # '0': 'solkan1201',
        # '5': 'diegoGmail',
        # '20': 'rodrigo'
    },
}

limite_bioma = ee.Geometry.Polygon(arqParam.lsPtos_limite_bioma)

biomas = ee.FeatureCollection(param['asset_IBGE']).filter(
    ee.Filter.inList('CD_LEGENDA',  param['bioma']))

# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
list_anos = [k for k in range(param['anoInicial'], param['anoFinal'])]

print('Analisando desde o ano {} hasta o {} '.format(
    list_anos[0], list_anos[-1]))


# carregando a lista de nomes das bacias
lsBacias = arqParam.listaNameBacias
print("=== lista de nomes de bacias carregadas ===")
print("=== {} ===".format(lsBacias))

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

cont = gerenciador(0, param)
export_areas_changed = False
export_pixels_incident = False
export_pixels_staveis = False
activeMask = False

dict_lstBacias = arqParam.dictlstBacias
if export_areas_changed == False and export_pixels_incident == False and export_pixels_staveis == False:
    activeMask = True

objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(list_anos, activeMask)

if export_pixels_incident:
    for iyear in range(1985, 2020): 
        objetoMosaic_exportROI.get_coincidecia_mapCol_last3(iyear)
        cont = gerenciador(cont, param)
 
if export_pixels_staveis:
    for iyear in range(1985, 2022):
        objetoMosaic_exportROI.get_class_estatics_pixels(iyear)
        cont = gerenciador(cont, param)

del objetoMosaic_exportROI

listaNameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613',
]

# revisao da coleção 8 
# https://code.earthengine.google.com/5e8af5ef94684a5769e853ad675fc368

for item_bacia in lsBacias[:]:
    print(f"loading geometry bacia {item_bacia}")     
    objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(list_anos, activeMask)
    # geobacia, colAnos, nomeBacia, dict_nameBN4
    objetoMosaic_exportROI.iterate_bacias(item_bacia)
    cont = gerenciador(cont, param)

    # sys.exit()