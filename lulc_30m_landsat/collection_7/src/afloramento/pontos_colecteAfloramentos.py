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
                      36, 39, 40, 41, 46, 47, 48, 49],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18, 4],
        'asset_baciasN4': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4',
        'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsAflor/',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas': 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_input_NotAflor': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsAflor/points_Not_Afloramento_class',
        'asset_input_aflor': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsAflor/points_Afloramento_class',
        "anoIntInit": 1985,
        "anoIntFin": 2021,
    }
    lst_properties = arqParam.allFeatures
    def __init__(self, lst_year):

        self.imgMosaic = ee.ImageCollection(self.options['asset_mosaic_mapbiomas']).filter(
            ee.Filter.eq('biome', 'CAATINGA'))

        # @collection6 bruta: mapas de uso e cobertura Mapbiomas ==> para masquear as amostra fora de mascara
        self.collection_bruta = ee.ImageCollection(
            self.options['assetMapbiomasGF']).min()
        self.img_mask = self.collection_bruta.unmask(
            100).eq(100).reduce(ee.Reducer.sum())
        self.img_mask = self.img_mask.eq(0).selfMask()

        # @collection6: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        self.collection6 = ee.Image(self.options['assetMapbiomas'])

        # Remap todas as imagens mapbiomas
        lsBndMapBiomnas = []
        self.imgMapbiomas = ee.Image().toByte()

        for year in lst_year:

            band = 'classification_' + str(year)
            lsBndMapBiomnas.append(band)

            imgTemp = self.collection6.select(band).remap(
                self.options['classMapB'], self.options['classNew'])
            self.imgMapbiomas = self.imgMapbiomas.addBands(
                imgTemp.rename(band))

        self.imgMapbiomas = self.imgMapbiomas.select(lsBndMapBiomnas)
        self.imgMapbiomas = self.imgMapbiomas.updateMask(self.img_mask)

        self.baciasN4 = ee.FeatureCollection(self.options['asset_baciasN4'])

        self.feat_pts_aflor = ee.FeatureCollection(self.options['asset_input_aflor'])
        print("numero de pontos Afloresta", self.feat_pts_aflor.size().getInfo())
        feat_pts_Notafloram = ee.FeatureCollection(self.options['asset_input_NotAflor'])
        feat_pts_Notaflor = feat_pts_Notafloram.map(lambda feat: feat.set('class', 150))
        print("numero de pontos Not Floresta", feat_pts_Notaflor.size().getInfo())

        self.feat_pts_aflor = self.feat_pts_aflor.merge(feat_pts_Notaflor)
        # print(self.feat_pts_true.first().getInfo())               
    

    def iterate_bacias(self, geobacia, nomeBacia, dict_nameBN4):

        # colecao responsavel por executar o controle de execucao, caso optem por executar o codigo em terminais paralelos,
        # ou seja, em mais de um terminal simultaneamente..
        # caso deseje executar num unico terminal, deixar colecao vazia.        
        colecaoPontos = ee.FeatureCollection([])
        ptosRegions_ref = ee.FeatureCollection(self.feat_pts_aflor).filterBounds(geobacia)
        # print("numero de pontos ", ptosRegions_ref.size().getInfo())        

        for idBN4 in dict_nameBN4[nomeBacia]:
            name_export = nomeBacia + "_" + str(idBN4) + '_1'

            try:
                featColfeita = ee.FeatureCollection(
                    self.options['outAsset'] + name_export)
                print("Numero de Feat ROIs coletados : ",
                      featColfeita.size().getInfo())

            except:

                oneBacia = self.baciasN4.filter(
                                        ee.Filter.eq('fid', idBN4)).geometry()
                # print("número de Bacias menores achadas ", oneBacia.size().getInfo())
                
                ptosRegions_refRed = ptosRegions_ref.filterBounds(oneBacia)
                anoCount = self.options['anoIntInit']

                for anoCount in range(1985, 2022):

                    bandActiva = 'classification_' + str(anoCount)
                    print("banda activa: " + bandActiva)            
                    layer_ref = 'CLASS_' + str(anoCount)                    

                    img_recMosaic = self.imgMosaic.filterBounds(oneBacia).filter(
                                                ee.Filter.eq('year', anoCount)).median()                    

                    img_recMosaic = img_recMosaic.addBands(
                                            ee.Image.constant(int(anoCount)).rename('year'))
                    # print("numero de ptos controle ", feat_control_yy.size().getInfo())
                    # opcoes para o sorteio estratificadoBuffBacia
                    ptosTemp = img_recMosaic.sampleRegions(
                        collection= ptosRegions_refRed,
                        properties= ['class'],
                        scale=30,
                        tileScale=16,
                        geometries=True
                    )
                    # insere informacoes em cada ft
                    ptosTemp = ptosTemp.filter(ee.Filter.notNull(self.lst_properties[: 10]))

                    # merge com colecoes anteriores
                    colecaoPontos = colecaoPontos.merge(ptosTemp)
                    anoCount += 1
                # sys.exit()
                name_exp = str(nomeBacia) + "_" + str(idBN4) + "_cAfl"  
                self.saveToAsset(colecaoPontos, name_exp)

    # salva ftcol para um assetindexIni
    def saveToAsset(self, collection, name):

        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['outAsset'] + name
        }

        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()

        print("exportando ROIs da bacia $s ...!", name)


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
    'anoFinal': 2019,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta': {
        # '0': 'caatinga01',
        # '7': 'caatinga02',
        # '14': 'caatinga03',
        # '21': 'caatinga04',
        # '28': 'caatinga05',
        '0': 'solkan1201',
        # '5': 'diegoGmail',
        '20': 'rodrigo'
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


dict_lstBacias = arqParam.dictlstBacias
objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(list_anos)

listaNameBacias = [
    # '741','7421','7422','744','745','746','7492','751','752','753',
    # '754','755','756','757','758','759','7621','7622','763','764',
    # '765','766','767','771','772','773', '7741','7742','775','776',
    # '777','778','76111','76116','7612','7614','7615','7616',
    # '7617','7618','7619', '7613',

    '7421','7422','744','746','755'
]

cont = gerenciador(0, param)
for item in lsBacias[:]:
    print("fazendo bacia " + item)
    baciaTemp = ftcol_bacias.filter( ee.Filter.eq('nunivotto3', item)).first()
    # geobacia, colAnos, nomeBacia, dict_nameBN4
    objetoMosaic_exportROI.iterate_bacias(baciaTemp.geometry(), item, dict_lstBacias)

    print("salvando ROIs bacia: << {} >>".format(item))
    # cont = gerenciador(cont, param)


