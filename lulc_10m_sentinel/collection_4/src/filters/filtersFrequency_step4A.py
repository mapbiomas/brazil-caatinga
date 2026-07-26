#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os
import sys
import time
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

def mode_spatial_filter(img_band, band_name, sieve_param):
    """
    Filtro espacial sieve com preservação de estruturas finas (erosão morfológica)
    e mescla de grupos de classes para cálculo de conectividade.

    Manchas com cc <= max_filter_pixels são substituídas pela moda da vizinhança,
    exceto: pixels ponte em estruturas lineares, estruturas finas longas
    (cc > thin_cc_threshold sem interior compacto) e classes de exceção.
    """
    native_scale       = sieve_param['native_scale']
    max_filter_pixels  = sieve_param['max_filter_pixels']
    kernel_size        = sieve_param['kernel_size']
    max_cc_size        = sieve_param['max_cc_size']
    use_bridge_detect  = sieve_param['use_bridge_detect']
    excessions_class   = sieve_param['excessions_class']
    erode_radius       = sieve_param['erode_radius']
    thin_cc_threshold  = sieve_param['thin_cc_threshold']
    class_merge_groups = sieve_param['class_merge_groups']

    projection      = img_band.projection()
    img_for_connect = img_band.reproject(crs=projection, scale=native_scale)

    img_merged = img_for_connect
    for group in class_merge_groups:
        target = group[0]
        for cls in group[1:]:
            img_merged = img_merged.where(img_merged.eq(cls), target)

    connect_1 = img_merged.connectedPixelCount(max_cc_size, True)
    connect_2 = img_merged.connectedPixelCount(max_cc_size, False)

    nbands  = img_merged.neighborhoodToBands(ee.Kernel.square(1))
    bn      = ee.String(img_merged.bandNames().get(0))
    nb_p10  = nbands.select(bn.cat('_1_0'))
    nb_n10  = nbands.select(bn.cat('_-1_0'))
    nb_p01  = nbands.select(bn.cat('_0_1'))
    nb_n01  = nbands.select(bn.cat('_0_-1'))
    nb_p11  = nbands.select(bn.cat('_1_1'))
    nb_n11  = nbands.select(bn.cat('_-1_-1'))
    nb_n1p1 = nbands.select(bn.cat('_-1_1'))
    nb_p1n1 = nbands.select(bn.cat('_1_-1'))

    is_bridge = (
        img_merged.eq(nb_p10).And(img_merged.eq(nb_n10))
        .Or(img_merged.eq(nb_p01).And(img_merged.eq(nb_n01)))
        .Or(img_merged.eq(nb_p11).And(img_merged.eq(nb_n11)))
        .Or(img_merged.eq(nb_n1p1).And(img_merged.eq(nb_p1n1)))
    )
    not_bridge = is_bridge.Not() if use_bridge_detect else ee.Image.constant(1)

    lmin     = img_merged.focal_min(erode_radius, 'square', 'pixels')
    lmax     = img_merged.focal_max(erode_radius, 'square', 'pixels')
    survived = lmin.eq(img_merged).And(lmax.eq(img_merged))

    compact_region = (survived
        .reproject(crs=projection, scale=native_scale)
        .focal_max(erode_radius, 'square', 'pixels')
        .gt(0))

    is_thin    = connect_1.gt(thin_cc_threshold).And(compact_region.Not())
    thin_layer = img_for_connect.updateMask(is_thin)

    mode_img = img_for_connect.focal_mode(kernel_size, 'square', 'pixels')

    mode_all = mode_img.updateMask(connect_1.lte(max_filter_pixels).And(not_bridge))

    mode_21 = mode_img.updateMask(
        img_for_connect.eq(21).And(connect_2.lte(max_filter_pixels)).And(not_bridge)
    )

    exceptions_layer = img_for_connect.remap(excessions_class, excessions_class)

    filtered = (img_for_connect
        .blend(mode_all)
        .blend(mode_21)
        .blend(thin_layer)
        .blend(exceptions_layer))

    return filtered.rename(band_name)


class processo_filterFrequence(object):

    sieve_options = {
        'native_scale'      : 10,     # resolução Sentinel-2 (m)
        'max_filter_pixels' : 5,
        'kernel_size'       : 3,
        'max_cc_size'       : 100,
        'use_bridge_detect' : True,
        'excessions_class'  : [33, 29],          # água e afloramento nunca substituídos
        'erode_radius'      : 1,
        'thin_cc_threshold' : 10,
        'class_merge_groups': [
            [3, 4, 5, 9, 12, 13],               # vegetação natural (conectividade conjunta)
            [15, 18, 19, 20, 21, 39, 40, 41],   # pastagem e agricultura
        ],
    }

    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Frequency',
        'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Temporal_Nat_Ant',
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'classMapB':     [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
        'classNew':      [3, 4, 3, 3, 12, 12, 15, 19, 19, 19, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 25],
        # 'classNew':    [3, 4, 3, 3, 12, 12, 21, 21, 21, 21, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21,  4, 12, 21, 25],
        'classNat':      [1, 1, 1, 1,  1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  1,  1,  0,  0],  
        'janela_input': 5,
        'num_classes': 7,  # 7, 10   
        'last_year' : 2025,
        'first_year': 2016
    }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.versoutput = 7
        self.versionInput = 7

        self.step = 1
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                   ee.Filter.eq('nunivotto4', nameBacia))  
        geomBacia = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)            
        self.geom_bacia = self.geom_bacia.geometry()     
        
        # self.imgClass = ee.Image(self.options['input_asset'] + "/" + self.name_imgClass)   

        self.imgClass =(ee.ImageCollection(self.options['input_asset'])
                                    .filter(ee.Filter.eq('version', self.versionInput))
                                    .filter(ee.Filter.eq('num_class', self.options['num_classes']))
                                    # só o Gap-fill tem id_bacia o resto tem id_bacias
                                    .filter(ee.Filter.eq('id_bacias', nameBacia))                                      
                                    # .first()
                        )        
        # print(" total of  image class ", self.imgClass.size().getInfo())
        if  self.options['janela_input'] > 0:
            self.imgClass = self.imgClass.filter(ee.Filter.eq('janela',  self.options['janela_input']))
        self.imgClass = self.imgClass.first()
        # print("numero de bandas ", self.imgClass.bandNames().getInfo())
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]

        # Filtro espacial sieve aplicado banda a banda antes do filtro de frequência
        self.imgClassFiltered = ee.Image.cat([
            mode_spatial_filter(self.imgClass.select(b), b, self.sieve_options)
            for b in self.lstbandNames
        ])

        self.imgReclass = ee.Image.cat([
            self.imgClassFiltered.select(b).remap(self.options['classMapB'], self.options['classNew']).rename(b)
            for b in self.lstbandNames
        ])

        ##### ////////Calculando frequencias sobre imagem filtrada espacialmente /////////////#####
        n = len(self.lstbandNames)
        self.florest_frequence   = self.imgClassFiltered.eq(3).reduce(ee.Reducer.sum()).multiply(100.0 / n)
        self.savana_frequence    = self.imgClassFiltered.eq(4).reduce(ee.Reducer.sum()).multiply(100.0 / n)
        self.grassland_frequence = self.imgClassFiltered.eq(12).reduce(ee.Reducer.sum()).multiply(100.0 / n)
        # máscara Natural: pixels naturais em 100% dos anos (classNat como 0/1)
        imgNatural = ee.Image.cat([
            self.imgClassFiltered.select(b).remap(self.options['classMapB'], self.options['classNat']).rename(b)
            for b in self.lstbandNames
        ])
        natural = imgNatural.reduce(ee.Reducer.sum()).multiply(100.0 / n)
        self.mask_natural = natural.eq(100)

        ## contruindo a regra de mudança para as classes naturais ####
        ### esta camada será de uma única banda com os pixels em 3, 4 ou 12 para as
        ### correspondentes classes e o resto em 0 
        ###########  /////Mapa base////// ############
        # atualizando os pixels que serão convertidos a formação campestre
        self.vegetation_map = ee.Image(0).where(self.mask_natural.eq(1).And(self.grassland_frequence.gt(70)), 12)
        # addicionando todos os pixels que serão convertidos em formação florestal 
        self.vegetation_map = self.vegetation_map.where(self.mask_natural.eq(1).And(self.florest_frequence.gt(70)), 3)
        # addicionando todos os pixels que serão convertidos em formação savanica 
        self.vegetation_map = self.vegetation_map.where(self.mask_natural.eq(1).And(self.savana_frequence.gte(80)), 4)
        self.vegetation_map = self.vegetation_map.updateMask(self.vegetation_map.gt(0))

        # Afloramento rochoso (29): classe estática — força 29 onde freq >= 75% da série
        self.afloramento_frequence = self.imgClassFiltered.eq(29).reduce(ee.Reducer.sum()).multiply(100.0 / n)
        self.afloramento_map = ee.Image(29).updateMask(self.afloramento_frequence.gte(75))

    def applyStabilityNaturalClass_byYear(self):
        rasterFinal = ee.Image.cat([
            self.imgClassFiltered.select(b).blend(self.vegetation_map).blend(self.afloramento_map)
            for b in self.lstbandNames
        ])
        rasterFinal = (rasterFinal.select(self.lstbandNames)
                        .updateMask(self.bacia_raster)
                        .set(
                            'version',  int(self.versoutput), 
                            'biome', 'CAATINGA',
                            'type_filter', 'frequence',
                            'from', 'Temporal_Nat_Ant',
                            'collection', '4.0',
                            'model', "GTB",                            
                            'id_bacias', self.id_bacias,
                            'sensor', 'Sentinel',
                            'num_class', self.options['num_classes'],
                            'system:footprint' , self.geom_bacia
                        )
                    )

        name_toexport = f"filterFQ_BACIA_{self.id_bacias}_GTB_V{self.versoutput}_{self.options['num_classes']}cc"
        self.processoExportar(rasterFinal, name_toexport)    

    ##### exporta a imagem classificada para o asset  ###
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region': self.geom_bacia, # .getInfo()['coordinates']
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


#============================================================
#========================METODOS=============================
#============================================================

listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765', 
    '752', 
]

# listaNameBacias = [
#     '76111', '756', '757', '758', '754', '7614', '7421'
# ]


def verficar_bacias_inTask():
    """Retorna True enquanto o input (Temporal_Nat_Ant) ainda não tem todas as bacias."""
    versionInp = 7
    imgCol_temp = (ee.ImageCollection(processo_filterFrequence.options['input_asset'])
                        .filter(ee.Filter.eq('version',   versionInp))
                )
    if processo_filterFrequence.options['janela_input'] > 0:
        imgCol_temp = imgCol_temp.filter(ee.Filter.eq('janela', processo_filterFrequence.options['janela_input']))
    num_img = imgCol_temp.size().getInfo()
    print(f"  input: {num_img}/{len(listaNameBacias)} bacias prontas")
    return num_img < len(listaNameBacias)


# listaNameBacias = ['76111', '756', '757', '758', '754', '7614', '7421']

# False → aguarda input completo, submete Frequency tasks
# True  → pula submissão, verifica output (tasks já enviadas anteriormente)
knowMapSaved = False
listBacFalta = []

if not knowMapSaved:
    # Fase 1: aguardar o input (Temporal_Nat_Ant) ter todas as bacias
    while verficar_bacias_inTask():
        print(" .... esperar mais 5 minutos ... ")
        time.sleep(300)

    # Fase 2: submeter tasks do Frequency
    for cc, idbacia in enumerate(listaNameBacias):
        if idbacia not in listBacFalta:
            print(f"\n--------- 📢 #{cc} PROCESSING BACIA {idbacia} ---------")
            print("----------------------------------------------")
            aplicando_FrequenceFilter = processo_filterFrequence(idbacia)
            aplicando_FrequenceFilter.applyStabilityNaturalClass_byYear()
else:
    # Verificar output (Frequency)
    output_asset = processo_filterFrequence.options['output_asset']
    version = 5
    for cc, idbacia in enumerate(listaNameBacias):
        try:
            imgtmp = (ee.ImageCollection(output_asset)
                            .filter(ee.Filter.eq('version',   version))
                            .filter(ee.Filter.eq('id_bacias', idbacia))
                            .filter(ee.Filter.eq('num_class', processo_filterFrequence.options['num_classes'])))
            print(f" {cc} 📢 ", imgtmp.first().get("system:index").getInfo(), " < > ",
                  len(imgtmp.first().bandNames().getInfo()))
        except Exception:
            listBacFalta.append(idbacia)

    print("lista de bacias que faltam \n ", listBacFalta)
    print("total ", len(listBacFalta))