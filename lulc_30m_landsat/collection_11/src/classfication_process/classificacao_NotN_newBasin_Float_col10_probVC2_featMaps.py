#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import glob
import json
import csv
import copy
import sys
import math
import pandas as pd
from pathlib import Path
import arqParametros_class as arqParams 
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
# sys.setrecursionlimit(1000000000)

#============================================================
#============== FUNCTIONS FO SPECTRAL INDEX =================


class ClassMosaic_indexs_Spectral(object):

    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'bioma': "CAATINGA",
        'version': 1,
        'lsBandasMap': [],
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'asset_collectionId': 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
        'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/rois_resample_featmaps',
        # 'asset_joinsGrBaMB': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/rois_resample_featmaps',
        'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2',
        'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX',
        # 'asset_output': 'projects/nexgenmap/SAMPLES/Caatinga',
        # Spectral bands selected
        'lsClasse': [4, 3, 12, 15, 18, 21, 22, 33],
        'lsPtos': [300, 500, 300, 350, 150, 100, 150, 300],
        "anoIntInit": 1985,
        "anoIntFin": 2025,
        'dict_classChangeBa': arqParams.dictClassRepre,
        # https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting
        'pmtGTB': {
            'numberOfTrees': 25, 
            'shrinkage': 0.1,         
            'samplingRate': 0.65, 
            'loss': "LeastSquares",#'Huber',#'LeastAbsoluteDeviation', 
            'seed': 0
        },
    }

    all_bands = [
        'afvi_median_wet', 'avi_median', 'avi_median_wet', 'awei_median', 'awei_median_dry', 
        'awei_median_wet', 'blue_median_wet', 'brba_median_wet', 'awei_median_mean', 
        'brightness_median', 'brightness_median_dry', 'brightness_median_wet',
        'co2flux_median_wet', 'dswi5_median_wet', 'evi_median_wet', 'gcvi_median_wet', 
        'gndvi_median_wet', 'green_median', 'green_median_dry', 'green_median_wet', 'gvmi_median_wet', 
        'iia_median_wet', 'lai_median_wet', 'mbi_median_dry', 'ndbi_median_wet', 'nddi_median_wet', 
        'ndfia_median_wet', 'ndti_median', 'ndti_median_dry', 'ndti_median_wet', 'ndvi_median_wet', 
        'ndwi_median_wet', 'nir_median_dry', 'nir_median_wet', 'npv_median', 'npv_median_dry', 
        'npv_median_wet', 'osavi_median_wet', 'ratio_median_wet', 'red_median', 'red_median_dry', 
        'red_median_wet', 'rvi_median_wet', 'shade_median_dry', 'shade_median_wet', 'soil_median', 
        'soil_median_dry', 'soil_median_wet', 'swir1_median', 'swir1_median_dry', 'swir1_median_wet',
        'swir2_median', 'swir2_median_dry', 'swir2_median_wet', 'ui_median_wet', 'wetness_median', 
        'wetness_median_dry', 'wetness_median_wet'
    ]
    all_bands = [f'b{ii}' for ii in  range(1, 33) ]

    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self):
     
        imgMapSaved = ee.ImageCollection(self.options['assetOut'])
        self.lstIDassetS = imgMapSaved.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
        print(f" ====== we have {len(self.lstIDassetS)} maps saved ====")   

        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        self.options['lsBandasMap'] = ['classification_' + str(kk) for kk in self.lst_year]

        # self.tesauroBasin = arqParams.tesauroBasin
        pathHiperpmtros = os.path.join(pathparent, 'dados', 'dictBetterModelpmtCol10v1.json')
        b_file = open(pathHiperpmtros, 'r')
        self.dictHiperPmtTuning = json.load(b_file)
        self.pathFSJson = getPathCSV("FS_col11_json/")
        print("==== path of CSVs of Features Selections ==== \n >>> ", self.pathFSJson)
        self.lstBandMB = self.get_bands_mosaicos()
        print("bandas mapbiomas ", self.lstBandMB)



    # add bands with slope and hilshade informations 
    def addSlopeAndHilshade(self, img):
        # A digital elevation model.
        # NASADEM: NASA NASADEM Digital Elevation 30m
        dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')

        # Calculate slope. Units are degrees, range is [0,90).
        slope = ee.Terrain.slope(dem).divide(500).toFloat()

        # Use the ee.Terrain.products function to calculate slope, aspect, and
        # hillshade simultaneously. The output bands are appended to the input image.
        # Hillshade is calculated based on illumination azimuth=270, elevation=45.
        terrain = ee.Terrain.products(dem)
        hillshade = terrain.select('hillshade').divide(500).toFloat()

        return img.addBands(slope.rename('slope')).addBands(hillshade.rename('hillshade'))

    def GET_NDFIA(self, IMAGE, sufixo):
        lstBands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
        lstBandsSuf = [bnd + sufixo for bnd in lstBands]
        lstFractions = ['gv', 'shade', 'npv', 'soil', 'cloud']
        lstFractionsSuf = [frac + sufixo for frac in lstFractions]
        
        endmembers = [            
            [0.05, 0.09, 0.04, 0.61, 0.30, 0.10], # gv
            [0.14, 0.17, 0.22, 0.30, 0.55, 0.30], # npv
            [0.20, 0.30, 0.34, 0.58, 0.60, 0.58], # soil
            [0.0 , 0.0,  0.0 , 0.0 , 0.0 , 0.0 ], # Shade
            [0.90, 0.96, 0.80, 0.78, 0.72, 0.65]  # cloud
        ];

        fractions = (ee.Image(IMAGE).select(lstBandsSuf)
                                .unmix(endmembers=endmembers, sumToOne=True, nonNegative=True)
                                .float())
        fractions = fractions.rename(lstFractions)

        NDFI_ADJUSTED = fractions.expression(
                                "float(((b('gv') / (1 - b('shade'))) - b('soil')) / ((b('gv') / (1 - b('shade'))) + b('npv') + b('soil')))"
                                ).rename('ndfia' + sufixo)

        NDFI_ADJUSTED = NDFI_ADJUSTED.toFloat()
        fractions = fractions.rename(lstFractionsSuf)
        RESULT_IMAGE = fractions.toFloat().addBands(NDFI_ADJUSTED)

        return ee.Image(RESULT_IMAGE).toFloat()


    def agregate_Bands_SMA_NDFIa(self, img):
        indSMA_median =  self.GET_NDFIA(img, '_median')
        indSMA_med_wet =  self.GET_NDFIA(img, '_median_wet')
        indSMA_med_dry =  self.GET_NDFIA(img, '_median_dry')
        return img.addBands(indSMA_median).addBands(indSMA_med_wet).addBands(indSMA_med_dry)

    def agregateBandsContextoEstrutural(self, img):        
        kernel = ee.Kernel.square(7)
        bandas_textura = [
            'osavi_median', 'gcvi_median', 'avi_median', 
            'ndfia_median', 'bsi_median', 'ui_median', 
            'awei_median'
        ]
        
        img_base = img.select(bandas_textura)
        redutor_combo = ee.Reducer.mean().combine(
            reducer2=ee.Reducer.stdDev(),
            sharedInputs=True
        )
        contexto_espacial = img_base.reduceNeighborhood(
            reducer=redutor_combo,
            kernel=kernel
        )
        return img.addBands(contexto_espacial)



    # Ratio Vegetation Index # Global Environment Monitoring Index GEMI 
    def agregateBandswithSpectralIndex(self, img): # lista_bands
        sufixos = ['_median', '_median_wet', '_median_dry']

        # Puxa o dicionário gigante do seu arquivo de configuração!
        formulas_base = arqParams.FORMULAS_INDICES_ESPECTRAIS

        novas_bandas_base = []        
        for s in sufixos:
            print("sufixos ==> ", s)
            for nome_indice, expressao in formulas_base.items():
                expr_formatada = expressao.format(s=s)
                nome_banda = f"{nome_indice}{s}"
                banda_calc = img.expression(f"float({expr_formatada})").rename(nome_banda)
                novas_bandas_base.append(banda_calc)
                # print(f" === {nome_banda} addicionados ===")

        img_com_base = ee.Image.cat([img] + novas_bandas_base)
        
        bandas_dependentes = []
        for s in sufixos:
            lai = img_com_base.expression(f"float(3.618 * (b('evi{s}') - 0.118))").rename(f"lai{s}")
            nddi = img_com_base.expression(f"float((b('ndvi{s}') - b('ndwi{s}')) / (b('ndvi{s}') + b('ndwi{s}')))").rename(f"nddi{s}")
            spri = img_com_base.expression(f"float((b('pri{s}') + 1) / 2)").rename(f"spri{s}")
            bandas_dependentes.extend([lai, nddi, spri])

        img_quase_pronta = ee.Image.cat([img_com_base] + bandas_dependentes)

        bandas_co2 = []
        for s in sufixos:
            co2 = img_quase_pronta.expression(f"float(b('ndvi{s}') * b('spri{s}'))").rename(f"co2flux{s}")
            bandas_co2.append(co2)

        imagem_final = ee.Image.cat([img_quase_pronta] + bandas_co2)
        
        imagem_final = self.addSlopeAndHilshade(imagem_final)
        imagem_final = self.agregate_Bands_SMA_NDFIa(imagem_final)
        imagem_final = self.agregateBandsContextoEstrutural(imagem_final)
        # print("bandas mosaico ", img_com_base.bandNames().getInfo())
        print("-----ADICIONOU TODOS OS INDICES ESPTRAIS AO PASSAR POR AQUI -----------")
        return imagem_final

    
    def make_mosaicofromIntervalo(self, colMosaic, year_courrent, semetral=False):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]            
        band_wets = [bnd + '_wet' for bnd in band_year]
        band_drys = [bnd + '_dry' for bnd in band_year]
        dictPer = {
            'year': {
                'start': str(str(year_courrent)) + '-01-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'year',
                'bnds': band_year
            },
            'dry': {
                'start': str(year_courrent) + '-08-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'dry',
                'bnds': band_drys
            },
            'wet': {
                'start': str(year_courrent) + '-01-01',
                'end': str(year_courrent) + '-07-31',
                'surf': 'wet',
                'bnds': band_wets
            }
        }       
        mosaico = None
        if semetral:
            lstPeriodo = ['year', 'wet']
        else:
            lstPeriodo = ['year', 'dry', 'wet']
        for periodo in lstPeriodo:
            dateStart =  dictPer[periodo]['start']
            dateEnd = dictPer[periodo]['end']
            bands_period = dictPer[periodo]['bnds']
            # get dry median mosaic
            mosaictmp = (
                colMosaic.select(self.options['bnd_L'])
                    .filter(ee.Filter.date(dateStart, dateEnd))
                    .max()
                    .rename(bands_period)
            )
            if periodo == 'year':
                mosaico = copy.deepcopy(mosaictmp)
            else:
                mosaico = mosaico.addBands(mosaictmp)

        if semetral:
            bands_period = dictPer[ 'dry']['bnds']
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(bands_period)
            mosaico = mosaico.addBands(imgUnos)

        return mosaico

    def make_mosaicofromIntervalo_y25(self, colMosaic, year_courrent, semetral=False):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]            
        band_wets = [bnd + '_wet' for bnd in band_year]
        band_drys = [bnd + '_dry' for bnd in band_year]
        dictPer = {
            'year': {
                'start': str(str(year_courrent)) + '-01-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'year',
                'bnds': band_year
            },
            'dry': {
                'start': str(year_courrent) + '-08-01',
                'end': str(year_courrent) + '-12-31',
                'surf': 'dry',
                'bnds': band_drys
            },
            'wet': {
                'start': str(year_courrent) + '-01-01',
                'end': str(year_courrent) + '-07-31',
                'surf': 'wet',
                'bnds': band_wets
            }
        }        
        periodo = 'wet'
        dateStart =  dictPer[periodo]['start']
        dateEnd = dictPer[periodo]['end']
        bands_period = dictPer[periodo]['bnds']
        mosaico = (
            colMosaic.select(self.options['bnd_L'])
                .filter(ee.Filter.date(dateStart, dateEnd))
                .max()
                .rename(bands_period)
        )

        if semetral:
            bands_period = dictPer['dry']['bnds']
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(bands_period)
            mosaico = mosaico.addBands(imgUnos)
            bands_period = dictPer['year']['bnds']
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(bands_period)
            mosaico = mosaico.addBands(imgUnos)

        return mosaico

    def get_bands_mosaicos (self):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        return band_year + band_wets + band_drys

    def down_samples_ROIs(self, rois_train):
        dictQtLimit = {
            '3': 600, '4': 1800, '12': 300, '15': 1050,
            '18': 100, '21': 750, '22': 400, '29': 200, '33': 100
        }
        lstFeats = ee.FeatureCollection([])
        def make_random_select(featCC, limiar):
            featCC = featCC.randomColumn()
            featCC = featCC.filter(ee.Filter.lt('random', ee.Number(limiar).toFloat()))  
            return featCC
            
        for cclass in [3, 4, 12, 22, 33]: 
            feattmp = rois_train.filter(ee.Filter.eq('class', int(cclass)))
            sizeFC = feattmp.size()
            feattmp = ee.Algorithms.If(
                        ee.Algorithms.IsEqual(ee.Number(sizeFC).gt(ee.Number(dictQtLimit[str(cclass)])),1), 
                        make_random_select(feattmp, ee.Number(dictQtLimit[str(cclass)]).divide(ee.Number(sizeFC))), 
                        feattmp)
            lstFeats = lstFeats.merge(feattmp)
        return ee.FeatureCollection(lstFeats)
    
    def get_ROIs_from_neighbor(self, lst_bacias, asset_root, yyear):
        featGeral = ee.FeatureCollection([])
        for jbasin in lst_bacias:
            nameFeatROIs =  f"{jbasin}_{yyear}_cd"  
            dir_asset_rois = os.path.join(asset_root, nameFeatROIs)
            feat_tmp = ee.FeatureCollection(dir_asset_rois)
            feat_tmp = feat_tmp.map(lambda f: f.set('class', ee.Number.parse(f.get('class')).toFloat().toInt8()))
            featGeral = featGeral.merge(feat_tmp)
        return featGeral

    def iterate_bacias(self, _nbacia, myModel, makeProb, process_mosaic_EE):        

        # loading geometry bacim
        baciabuffer = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                            ee.Filter.eq('nunivotto4', _nbacia))
        print(f"know about the geometry 'nunivotto4' >>  {_nbacia} loaded < {baciabuffer.size().getInfo()} > geometry" )   
        baciabuffer = baciabuffer.map(lambda f: f.set('id_codigo', 1))
        bacia_raster =  baciabuffer.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        baciabuffer = baciabuffer.geometry()
        # sys.exit()
        
        # https://code.earthengine.google.com/48effe10e1fffbedf2076a53b472be0e?asset=projects%2Fgeo-data-s%2Fassets%2Ffotovoltaica%2Fversion_4%2Freg_00000000000000000017_2015_10_pred_g2c
        lstSat = ["l5","l7","l8"]
        imagens_mosaicoEE = (
            ee.ImageCollection(self.options['asset_collectionId'])
                    .select(self.options['bnd_L'])
        )
        imagens_mosaico = (ee.ImageCollection(self.options['asset_mosaic'])
                                .filter(ee.Filter.inList('biome', self.options['biomas']))
                                .filter(ee.Filter.inList('satellite', lstSat))
                                .select(self.lstBandMB)
                    )

        featMaps = (ee.ImageCollection('projects/solvedltda/assets/MB11_FM/1990')
                      .filterBounds(baciabuffer)
                      .mosaic())
        lst_feat_select = 
        # # lista de classe por bacia 
        # lstClassesUn = self.options['dict_classChangeBa'][self.tesauroBasin[_nbacia]]
        # print(f" ==== lista de classes ness bacia na bacia < {_nbacia} >  ====")
        # print(f" ==== {lstClassesUn} ======" )
        print("---------------------------------------------------------------")
        pmtroClass = copy.deepcopy(self.options['pmtGTB'])

        path_ptrosFS = os.path.join(self.pathFSJson, f"feat_sel_{_nbacia}.json")
        print("load features json ", path_ptrosFS)
        # Open the JSON file for reading
        with open(path_ptrosFS, 'r') as file:
            # Load the JSON data
            bandas_fromFS = json.load(file)

        print(f"lista de Bacias Anos no dict de FS  {len(bandas_fromFS.keys())} years  " )
        print(' as primeiras 3 \n ==> ', list(bandas_fromFS.keys())[:3])
        # tesauroBasin = arqParams.tesauroBasin
        lsNamesBaciasViz = arqParams.basinVizinhasNew[_nbacia]
        lstSoViz =  [kk for kk in lsNamesBaciasViz if kk != _nbacia]
        print("lista de Bacias vizinhas", lstSoViz)

        # sys.exit()
        # imglsClasxanos = ee.Image().byte()

        for nyear in [1990]:  # self.lst_year[-1:]
            bandActiva = 'classification_' + str(nyear)       
            print( "banda activa: " + bandActiva)   

            nomec = f"{_nbacia}_{nyear}_GTB_col10_BND_fm-v_{self.options['version']}"
            if 'BACIA_' + nomec not in self.lstIDassetS:                

                #cria o classificador com as especificacoes definidas acima 
                limitlsb = 35
                # print( bandas_fromFS[f"{_nbacia}_{nyear}"])            
                # lstbandas_import = bandas_fromFS[f"{_nbacia}_{nyear}"]['features']
                if nyear < 2025:
                    lstbandas_import = bandas_fromFS[f"{_nbacia}_{nyear}"]['features']
                else:
                    lstbandas_import = bandas_fromFS[f"{_nbacia}_{2024}"]['features']
                # obandas_imports = [bnd for bnd in lstbandas_import if  not in bnd]
                # obandas_imports = obandas_imports[:limitlsb]
                # outrasBandas = ['stdDev', 'solpe']
                
                bandas_imports = lstbandas_import[:limitlsb]  + ['slope']
                print(f" numero de bandas selecionadas {len(bandas_imports)} ") 
                # print(bandas_imports)
                
                # sys.exit()
                # nameFeatROIs = samples_7424_1990
                if nyear < 2026:
                    nameFeatROIs =  f"samples_{_nbacia}_{nyear}"  
                else:
                    nameFeatROIs =  f"samples_{_nbacia}_{2024}"                

                print("loading Rois with name =>>>>>> ", nameFeatROIs)

                asset_rois = self.options['asset_joinsGrBa']
                
                try:
                    dir_asset_rois = os.path.join(asset_rois, nameFeatROIs)
                    print(f"load samples from idAsset >> {dir_asset_rois}")
                    ROIs_toTrain = ee.FeatureCollection(dir_asset_rois) 
                    # print(ROIs_toTrain.size().getInfo())
                    # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
                    bandExtra = [nband + '_median_wet' for nband in self.options['bnd_L']]  
                    # ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.neq('class', 21.0))
                    ROIs_toTrain = ROIs_toTrain.filter(ee.Filter.notNull(bandExtra))                
                    ROIs_toTrain = ROIs_toTrain.map(lambda f: f.set('class', ee.Number.parse(f.get('class')).toFloat().toInt8()))
                    print(ROIs_toTrain.size().getInfo())
                    # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
                    # otherROIsneighbor = self.get_ROIs_from_neighbor(lstSoViz, asset_rois, nyear)
                    ROIs_toTrain =  self.down_samples_ROIs(ROIs_toTrain)  #.merge(otherROIsneighbor)
                    print(" saindo do processo downsamples ")                    
                    # print(ROIs_toTrain.aggregate_histogram('class').getInfo())
                    # lstBandasROIS = ROIs_toTrain.first().propertyNames().getInfo()
                    # print(lstBandasROIS)
                    # print(len(bandas_imports))
                    # tmpBandasImp = [col for col in bandas_imports if col in lstBandasROIS]
                    # print(" >> ", len(bandas_imports))
                    print(" fez down samples nos ROIs  ")
                    # sys.exit()
                    # cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia 
                    date_inic = ee.Date.fromYMD(int(nyear),1,1)      
                    date_end = ee.Date.fromYMD(int(nyear),12,31)   
                    if nyear < 2026: 
                        lstCoef = [0.8425, 0.8957, 0.9097, 0.3188, 0.969, 0.9578]
                        bandsCoef = ee.Image.constant(lstCoef + lstCoef + lstCoef)
                        lstIntercept = [106.7546, 115.1553, 239.0688, 1496.4408, 392.3453, 366.57]
                        bandsIntercept = ee.Image.constant(lstIntercept + lstIntercept + lstIntercept)

                        colmosaicMapbiomas = (imagens_mosaico.filter(ee.Filter.eq('year', nyear))
                                        .median().updateMask(bacia_raster))
                        imagens_mosaicoEEv = colmosaicMapbiomas.multiply(bandsCoef).add(bandsIntercept) 
                        imagens_mosaicoEEv = imagens_mosaicoEEv.divide(10000)
                    
                        mosaicColGoogle = imagens_mosaicoEE.filter(ee.Filter.date(date_inic, date_end))        
                        mosaicoBuilded = self.make_mosaicofromIntervalo(mosaicColGoogle, nyear) 
                        mosaicoBuilded = mosaicoBuilded.updateMask(bacia_raster)
                        maskGaps = mosaicoBuilded.unmask(-9999).eq(-9999).updateMask(bacia_raster)
                        mosaicoBuilded = mosaicoBuilded.unmask(-9999).where(maskGaps, imagens_mosaicoEEv)
                        maskGaps = mosaicoBuilded.neq(-9999)
                        mosaicoBuilded = mosaicoBuilded.updateMask(maskGaps).updateMask(bacia_raster)
                    else:
                        mosaicColGoogle = imagens_mosaicoEE.filter(ee.Filter.date(date_inic, date_end))        
                        # print(mosaicColGoogle.size().getInfo())
                        mosaicoBuilded = self.make_mosaicofromIntervalo_y25(mosaicColGoogle, nyear,  True) 
                    
                    # print(f" we have {mosaicoBuilded.bandNames().getInfo()} images ")
                    
                    print("----- calculado todos os 102 indices ---------------------")
                    mosaicProcess = self.agregateBandswithSpectralIndex(mosaicoBuilded.updateMask(bacia_raster))
                    mosaicProcess = ee.Image(mosaicProcess)
                    print("-----------------------------------------")
                    # print(f" we have {mosaicProcess.bandNames().getInfo()} images ")
                    mosaicProcess = mosaicProcess.addBands(featMaps)
                    print("calculou todas as bandas necesarias ")
                    
                    # sys.exit()
                    gradeExpMemo = [
                        '7625', '7616', '7613', '7618', '7617', '761112', '7741', 
                        '7615', '7721', '7619', '7443', '763', '746'
                    ]
                    if _nbacia in gradeExpMemo:
                        pmtroClass['numberOfTrees'] = 18
                        pmtroClass['shrinkage'] = 0.1    # 
                    else:            
                        pmtroClass['shrinkage'] = self.dictHiperPmtTuning[_nbacia]['learning_rate']
                        lstBacias_prob = [ '7541', '7544', '7592', '7612', '7615',  '7712', '7721', '7741', '7746']
                        if _nbacia in lstBacias_prob:
                            numberTrees = 18
                            if self.dictHiperPmtTuning[_nbacia]["n_estimators"] < numberTrees:
                                pmtroClass['numberOfTrees'] = self.dictHiperPmtTuning[_nbacia]["n_estimators"] - 3
                            else:
                                pmtroClass['numberOfTrees'] = numberTrees       

                    print("pmtros Classifier ==> ", pmtroClass)
                    
                    # ee.Classifier.smileGradientTreeBoost(numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed)
                    # print("antes de classificar ", ROIs_toTrain.first().propertyNames().getInfo())
                    # lstNN = []
                    # for col in bandas_imports:
                    #     if col not in bandas_imports:
                    #         lstNN.append(col)
                    classifierGTB = ee.Classifier.smileGradientTreeBoost(**pmtroClass).train(
                                                        ROIs_toTrain, 'class', self.all_bands)              
                    classifiedGTB = mosaicProcess.classify(classifierGTB, bandActiva)        
                    # print("classificando!!!! ")
                    # sys.exit()
                    # se for o primeiro ano cria o dicionario e seta a variavel como
                    # o resultado da primeira imagem classificada
                    print("addicionando classification bands = " , bandActiva)            
                    # if self.options['anoIntInit'] == nyear:
                        # print ('entrou em 1985, no modelo ', myModel)            
                        # print("===> ", myModel)    
                        # imglsClasxanos = copy.deepcopy(classifiedGTB)                                        
                    # nomec = f"{_nbacia}_{nyear}_GTB_col10-v_{self.options['version']}"            
                    mydict = {
                        'id_bacia': _nbacia,
                        'version': self.options['version'],
                        'biome': self.options['bioma'],
                        'classifier': 'GTB',
                        'collection': '10.0',
                        'sensor': 'Landsat',
                        'source': 'geodatin',  
                        'year': nyear, 
                        'bands': 'fm'             
                    }
                        # imglsClasxanos = imglsClasxanos.set(mydict)
                    classifiedGTB = classifiedGTB.set(mydict)
                        ##### se nao, adiciona a imagem como uma banda a imagem que ja existia
                    # else:
                    #     # print("Adicionando o mapa do ano  ", nyear)
                    #     # print(" ", classifiedGTB.bandNames().getInfo())     
                    #     imglsClasxanos = imglsClasxanos.addBands(classifiedGTB)  


                    # imglsClasxanos = imglsClasxanos.select(self.options['lsBandasMap'])    
                    # imglsClasxanos = imglsClasxanos.set("system:footprint", baciabuffer.coordinates())
                    classifiedGTB = classifiedGTB.set("system:footprint", baciabuffer.coordinates())
                    # exporta bacia   .coordinates()
                    self.processoExportar(classifiedGTB, baciabuffer, nomec, process_mosaic_EE)
                     
                except:
                    print("-----------FALTANDO AS AMOSTRAS ----------------")
                # sys.exit()
        else:
            print(f' bacia >>> {nomec}  <<<  foi FEITA ')            

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF, regionB, nameB, proc_mosaicEE):
        nomeDesc = 'BACIA_'+ str(nameB)
        idasset =  os.path.join(self.options['assetOut'] , nomeDesc)
        if not proc_mosaicEE:
            idasset = os.path.join(self.options['assetOutMB'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':ee.Geometry(regionB), #['coordinates'] .getInfo()
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"},
            # 'priority': 1000
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))


mosaico = 'mosaico_mapbiomas'
param = {    
    'bioma': "CAATINGA", #nome do bioma setado nos metadados
    'biomas': ["CAATINGA","CERRADO", "MATAATLANTICA"],
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga49div",
    'asset_bacias_buffer' : 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1',
    'bnd_L': ['blue','green','red','nir','swir1','swir2'],
    'version': 1,
    'lsBandasMap': [],
    'numeroTask': 6,
    'numeroLimit': 10,
    'conta' : {
        '0': 'caatinga01',   # 
        '1': 'caatinga02',
        '2': 'caatinga03',
        '3': 'caatinga04',
        '4': 'caatinga05',        
        '5': 'solkan1201',    
        '6': 'solkanGeodatin',
        '7': 'superconta'   
    },
    'dict_classChangeBa': arqParams.dictClassRepre
}
# print(param.keys())
# print("vai exportar em ", param['assetOut'])

#============================================================
#========================METODOS=============================
#============================================================

def gerenciador(cont):
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    print(numberofChange)
    
    if str(cont) in numberofChange:
        print(f"inicialize in account #{cont} <> {param['conta'][str(cont)]}")
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 
        
        # relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:   
            print(str(lin))         
            # relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

#exporta a FeatCollection Samples classificada para o asset
# salva ftcol para um assetindexIni
def save_ROIs_toAsset(collection, name):

    optExp = {
        'collection': collection,
        'description': name,
        'assetId': param['outAssetROIs'] + "/" + name
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando ROIs da bacia $s ...!", name)



def check_dir(file_name):
    if not os.path.exists(file_name):
        arq = open(file_name, 'w+')
        arq.close()

def getPathCSV (nfolder):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])
    # folder of CSVs ROIs
    roisPath = '/dados/' + nfolder
    mpath = pathparent + roisPath
    print("path of CSVs Rois is \n ==>",  mpath)
    return mpath

def clean_lstBandas(tmplstBNDs):
    lstFails = ['green_median_texture']
    lstbndsRed = []
    for bnd in tmplstBNDs:
        bnd = bnd.replace('_1','')
        bnd = bnd.replace('_2','')
        bnd = bnd.replace('_3','')
        if bnd not in lstbndsRed and 'min' not in bnd and bnd not in lstFails and 'stdDev' not in bnd:
            lstbndsRed.append(bnd)
    return lstbndsRed

dictPmtroArv = {
    '35': [
            '741', '746', '753', '766', '7741', '778', 
            '7616', '7617', '7618', '7619'
    ],
    '50': [
            '7422', '745', '752', '758', '7621', 
            '776', '777',  '7612', '7615'# 
    ],
    '65':  [
            '7421','744','7492','751',
            '754','755','756','757','759','7622','763','764',
            '765','767','771','772','773', '7742','775',
            '76111','76116','7614','7613'
    ]
}

tesauroBasin = arqParams.tesauroBasin
pathJson = getPathCSV("regJSON/")


print("==================================================")
# process_normalized_img
# imagens_mosaic = imagens_mosaico.map(lambda img: process_re_escalar_img(img))          
# ftcol_baciasbuffer = ee.FeatureCollection(param['asset_bacias_buffer'])
# print(imagens_mosaic.first().bandNames().getInfo())
#nome das bacias que fazem parte do bioma7619
# nameBacias = arqParams.listaNameBacias
# print("carregando {} bacias hidrograficas ".format(len(nameBbacias_prioritariasacias)))
# sys.exit()
#lista de anos
# listYears = [k for k in range(param['yearInicial'], param['yearFinal'] + 1)]
# print(f'lista de bandas anos entre {param['yearInicial']} e {param['yearFinal']}')
# param['lsBandasMap'] = ['classification_' + str(kk) for kk in listYears]
# print(param['lsBandasMap'])

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
# bandNames = ['awei_median_dry', 'blue_stdDev', 'brightness_median', 'cvi_median_dry',]
# a_file = open(pathJson + "filt_lst_features_selected_spIndC9.json", "r")
# dictFeatureImp = json.load(a_file)
# print("dict Features ",dictFeatureImp.keys())



## Revisando todos as Bacias que foram feitas 
registros_proc = "registros/lsBaciasClassifyfeitasv_1.txt"
pathFolder = os.getcwd()
path_MGRS = os.path.join(pathFolder, registros_proc)
baciasFeitas = []
check_dir(path_MGRS)

arqFeitos = open(path_MGRS, 'r')
for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

arqFeitos.close()
arqFeitos = open(path_MGRS, 'a+')

# mpath_bndImp = pathFolder + '/dados/regJSON/'
# filesJSON = glob.glob(pathJson + '*.json')
# print("  files json ", filesJSON)
# nameDictGradeBacia = ''
# sys.exit()

# lista de 49 bacias 
nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751', 
    '752', '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622'
]
# nameBacias = [
    # '7422', '7424', '7438', '7443', '745', '746','751','752','753', '7564', '7581',
    # '7617', '7618', '7619', '7622', '7625', '763','765', '766', '7671', '772',
    # '7721', '7741', '7754'
# ]

# '7617', '7564',  '763', '7622'
print(f"we have {len(nameBacias)} bacias")
# "761112",
modelo = "GTB"
knowMapSaved = False
procMosaicEE = True

listBacFalta = []
# lst_bacias_proc = [item for item in nameBacias if item in listBacFalta]
# bacias_prioritarias = [
#   '7411',  '746', '7541', '7544', '7591', '7592', '761111', '761112', 
#   '7612', '7613', '7614', 
#   '7615', '771', '7712', '772', '7721', '773', '7741', '7746', 
#   '7754', '7761', '7764'
# ]
# print(len(lst_bacias_proc))
cont = 7
# cont = gerenciador(cont)

asset_exportar = param['assetOut']


# sys.exit()
for _nbacia in nameBacias[:]:
    if knowMapSaved:
        try:
            nameMap = 'BACIA_' + _nbacia + '_' + 'GTB_col10-v' + str(param['version'])
            imgtmp = ee.Image(os.path.join(asset_exportar, nameMap))
            print(" 🚨 loading ", nameMap, " ", len(imgtmp.bandNames().getInfo()), " bandas 🚨")
        except:
            listBacFalta.append(_nbacia)
    else:        
        print("-------------------.kmkl---------------------------------------------")
        print(f"--------    classificando bacia nova {_nbacia} and seus properties da antinga {tesauroBasin[_nbacia]}-----------------")   
        print("---------------------------------------------------------------------") 
        process_classification = ClassMosaic_indexs_Spectral()
        process_classification.iterate_bacias(_nbacia, modelo, False, procMosaicEE) 
        arqFeitos.write(_nbacia + '\n')
        # cont = gerenciador(cont) 

    # sys.exit()
arqFeitos.close()


# if knowMapSaved:
#     print("lista de bacias que faltam \n ",listBacFalta)
#     print("total ", len(listBacFalta))