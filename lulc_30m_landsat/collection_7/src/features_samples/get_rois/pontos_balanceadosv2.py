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

    # default options
    options = {
        "bandas": ['B2', 'B3', 'B4', 'B8', 'B9', 'B11', 'B12', 'MSK_CLDPRB'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33,
                      36, 39, 40, 41, 46, 47, 48, 49],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 18, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33,
                      18, 18, 18, 18, 18, 18, 18, 4],
        'asset_baciasN4': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4',
        'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv7/',
        'assetMapbiomasGF': 'projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV5',
        'assetMapbiomas': 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
        'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
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

        terrain = ee.Image("JAXA/ALOS/AW3D30_V1_1").select("AVE")
        self.slope = ee.Terrain.slope(terrain)

        self.baciasN4 = ee.FeatureCollection(self.options['asset_baciasN4'])

    # variavel que define o metodo de amostragem. o metodo 2 balanceia por area e por representatividade estatistica

    def iterate_bacias(self, geobacia, colAnos, nomeBacia, dict_nameBN4):

        # colecao responsavel por executar o controle de execucao, caso optem por executar o codigo em terminais paralelos,
        # ou seja, em mais de um terminal simultaneamente..
        # caso deseje executar num unico terminal, deixar colecao vazia.

        # baciasFeitas = ['$nome_bacia1', '$nome_bacia2', 'e assim por diante..']
        colecaoPontos = ee.FeatureCollection([])
        # imgBacia = collection1.clip(BuffBacia)

        # lsNoPtos = []
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

                anoCount = self.options['anoIntInit']
                for intervalo in colAnos:

                    bandActiva = 'classification_' + str(anoCount)
                    print("banda activa: " + bandActiva)

                    img_recMosaic = self.imgMosaic.filterBounds(oneBacia).filter(
                        ee.Filter.eq('year', anoCount)).median()

                    # print(intervalo)
                    if anoCount < 2021:
                        print("seleção anual ")
                        classes_brutas = self.collection_bruta.select(
                            bandActiva)
                        imgTemp = self.imgMapbiomas.select(intervalo)
                        # imgTemp = imgTemp.set("system:footprint", oneBacia)

                        # @reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
                        reducida = imgTemp.reduce(ee.Reducer.countDistinct())
                        mask_temporal = reducida.eq(1)

                        # @imgTemp: sera o mapa de uso e cobertura Mapbiomas ao que sera masked com as classes
                        # estaveis na janela de 5 anos
                        imgTemp = imgTemp.select(bandActiva)
                        imgTemp = imgTemp.mask(mask_temporal).rename(['class'])

                        # print("imgTemp ", imgTemp.bandNames().getInfo())
                        imgTemp = imgTemp.addBands(classes_brutas.rename('label'))
                    else:
                        print(imgTemp.bandNames().getInfo())

                    
                    imgTempAmp = imgTemp.addBands(
                        img_recMosaic).addBands(
                            ee.Image.constant(int(anoCount)).rename('year'))  # .addBands(self.slope)
                    
                    if anoCount == 2021:
                        print("bandas do 2021" , imgTemp.bandNames().getInfo())
                    # opcoes para o sorteio estratificadoBuffBacia
                    ptosTemp = imgTempAmp.sample(
                        region=oneBacia,
                        scale=30,
                        numPixels=1500,
                        dropNulls=True,
                        tileScale=16,
                        geometries=True
                    )
                    # insere informacoes em cada ft
                    ptosTemp = ptosTemp.filter(ee.Filter.notNull(self.lst_properties[: 10]))

                    # merge com colecoes anteriores
                    colecaoPontos = colecaoPontos.merge(ptosTemp)
                    anoCount += 1

                name_exp = str(nomeBacia) + "_" + str(idBN4) + param['sufix']
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
    'anoFinal': 2021,
    "anoIntInit": 1985,
    "anoIntFin": 2020,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 35,
    'conta': {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',
        '25': 'solkan1201',
        # '5': 'diegoGmail',
        '30': 'rodrigo',
        # '34': 'Rafael'
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
square = ee.Kernel.square(**{'radius': 3})
# print(imgMapbiomas.bandNames().getInfo())
collection6 = None

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


# calcula a proporsão que significa os pontos da classe do total de ROIS
def calcProporsion(valor, total):

    proporsion = ee.Number(valor).divide(total)

    valorN_Amost = proporsion.multiply(param['sampleSize'])

    valorMaxn = valorN_Amost.max(param['minROIs'])

    return valorMaxn.int()


def calcProporsionTortora(valor, total):

    proporsion = ee.Number(valor).divide(total)

    valorN_Amost = ee.Number(7.568).multiply(proporsion).multiply(
        ee.Number(1.0).subtract(proporsion)).divide(0.000625)

    valorMaxn = valorN_Amost.max(param['minROIs'])

    return valorMaxn.int()

# metodo retorna amostras de tamanhos diferentes, por classe, de acordo com a quantidade
# presente na bacia


def criar_amostras_por_classe(imgClassAnalises, limite):
    # classes = []
    # numero de minimo de samples para classes pouco presentes
    # nSamplesMin = 1000
    # numero maximo de samples - para o metodo balanceado por area

    paramtRedReg = {
        'reducer': ee.Reducer.frequencyHistogram(),
        'geometry': imgClassAnalises.geometry(),
        'scale': param['escala'],
        'tileScale': 8,
        'maxPixels': 1e13
    }

    histogramClasses = imgClassAnalises.reduceRegion(**paramtRedReg)
    histogramClasses = histogramClasses.values().get(0).getInfo()
    print(histogramClasses)

    total = sum(histogramClasses.values())
    classes = histogramClasses.keys()

    ###############################################################################
    #   calcula a quantidade de amostras que representarao bem cada classe,    ####
    #   de acorco com a porcentagem de presenca dessa classe na bacia e a      ####
    #   representatividade estatistica                                         ####
    #   n = z2*(p*(1-p))/E2 ===> z = 1.96 ====> E = 0.025 ==> no = 1/E2        ####
    #   n = (B*N*(1-N))/E2  indice de tortora (1978) e congalton (1957)        ####
    ###############################################################################

    lsROIsNum = []
    for cc in classes:

        proporsion = histogramClasses[cc]/total
        # Valor representativo de uma quantidade

        if param['metodotortora'] == False:
            valorN_Amost = proporsion * param['sampleSize']
            valorMax = max(valorN_Amost, param['minROIs'])

        else:
            valorN_Amost = (7.568 * proporsion *
                            (1.0 - proporsion)) / (0.000625)
            valorMax = max(valorN_Amost, param['minROIs'])

        lsROIsNum.append(int(valorMax))

    print('### Levando todos os valores mínimos ao máximo fixado ###')
    # get o valor do maximo
    valorMaximo = max(lsROIsNum)
    for ii in range(len(lsROIsNum)):

        vv = lsROIsNum[ii]
        if vv != param['minROIs']:
            lsROIsNum[ii] = valorMaximo

    return lsROIsNum, classes


# retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1Nan999, o metodo retornaria
# ['classification_1997', 'classification_1998', 'classification_1999', 'classification_2000', 'classification_2001']
# desse jeito pode-se extrair as bandas referentes as janelas
def mapeiaAnos(ano, janela, anos):

    lsBandAnos = ['classification_'+str(item) for item in anos]

    # primeiroAno = anos[0]
    # ultimoAno = anos[-1]

    primeiroAno = param['anoInicial']
    ultimoAno = param['anoFinal'] - 1
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
        return lsBandAnos[indice-2: indice+3]


# Revisando todos as Bacias que foram feitas
arqFeitos = open("registros/lsBaciasROIsfeitasBalanceadas.txt", 'r')
baciasFeitas = []
for ii in arqFeitos.readlines():
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

arqFeitos = open("registros/lsBaciasROIsfeitasBalanceadas.txt", 'a+')

# creando a lista de bandas em janelas de 5 anos

colectAnos = map(lambda ano: mapeiaAnos(
    ano, param['janela'], list_anos), list_anos)
newColectAnos = [k for k in colectAnos]
indexIni = list_anos.index(param['anoIntInit'])
indexFin = list_anos.index(param['anoIntFin'])
 
for cc, ii in enumerate(newColectAnos[indexIni: indexFin + 1]):
    print(cc + 1985, " : ",ii)
listfinalInt = ii
print("2021 : ", listfinalInt)
print("index inicial da lista de anos: ", list_anos.index(param['anoIntInit']))
print("index final da lista de anos: ", list_anos.index(param['anoIntFin']))

# print("colecao de anos ", newColectAnos[-1:])
#
#
newColectAnos.append(listfinalInt)

objetoMosaic_exportROI = ClassMosaic_indexs_Spectral(list_anos)

# print("objeto Bacias ", objetoMosaic_exportROI.baciasN4.size().getInfo())
# print("imagem mosaic ", objetoMosaic_exportROI.imgMosaic.first().bandNames().getInfo())

colectAnos = None
cont = 10
cont = gerenciador(cont, param)
# lsBacias = arqParam.listaNameBacias
dict_lstBacias = arqParam.dictlstBacias

# lsBacias = ['7619','7617','7616','7615','7614','7613','7612','76116',
#             '76111','778','777','776','775','7742','7741','773','772',
#             '771','767','766','765','764']
lsBacias = ['772']
for item in lsBacias[:]:

    if item not in baciasFeitas:

        print("fazendo bacia " + item)

        baciaTemp = ftcol_bacias.filter(
            ee.Filter.eq('nunivotto3', item)).first()
        # geobacia, colAnos, nomeBacia, dict_nameBN4
        objetoMosaic_exportROI.iterate_bacias(baciaTemp.geometry(
        ),  newColectAnos[indexIni: indexFin + 2], item,  dict_lstBacias)

        print("salvando ROIs bacia: << {} >>".format(item))

        arqFeitos.write(item + '\n')

        cont = gerenciador(cont, param)

arqFeitos.close()
