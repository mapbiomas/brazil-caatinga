#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import os
import copy
import sys
import pandas as pd
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
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


class ClassMosaic_indexs_Spectral(object):

    # default options
    options = {
        'bnd_L': ['blue','green','red','nir','swir1','swir2'],
        'bnd_fraction': ['gv','npv','soil'],
        'biomas': ['CERRADO','CAATINGA','MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 19, 19, 19, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 25],
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        # 'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
        'assetMapbiomas100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
        'asset_collectionId': 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
        # 'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample', 
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/aggrements',
        # 'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2',
        'asset_output_grade': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_byGradesIndv2', 
        # 'asset_output_grade': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesIndV3', 
        # 'asset_output': 'projects/nexgenmap/SAMPLES/Caatinga',
        # Spectral bands selected
        'lsClasse': [  4,   3,  12,  15,  19,  21,  25,  29, 33,   36],
        'lsPtos':   [300, 500, 300, 350, 150, 100, 150, 100, 200, 150],
        "anoIntInit": 1985,
        "anoIntFin": 2025,
    }

    featureBands = [
        'blue_median', 'blue_median_wet', 'blue_median_dry', 'blue_stdDev', 
        'green_median', 'green_median_dry', 'green_median_wet', 
        'green_median_texture', 'green_min', 'green_stdDev', 
        'red_median', 'red_median_dry', 'red_min', 'red_median_wet', 
        'red_stdDev', 'nir_median', 'nir_median_dry', 'nir_median_wet', 
        'nir_stdDev', 'red_edge_1_median', 'red_edge_1_median_dry', 
        'red_edge_1_median_wet', 'red_edge_1_stdDev', 'red_edge_2_median', 
        'red_edge_2_median_dry', 'red_edge_2_median_wet', 'red_edge_2_stdDev', 
        'red_edge_3_median', 'red_edge_3_median_dry', 'red_edge_3_median_wet', 
        'red_edge_3_stdDev', 'red_edge_4_median', 'red_edge_4_median_dry', 
        'red_edge_4_median_wet', 'red_edge_4_stdDev', 'swir1_median', 
        'swir1_median_dry', 'swir1_median_wet', 'swir1_stdDev', 'swir2_median', 
        'swir2_median_wet', 'swir2_median_dry', 'swir2_stdDev'
    ]
    features_extras = [
        'blue_stdDev','green_median_texture', 'green_min', 'green_stdDev',
        'red_min', 'red_stdDev','red_edge_1_median', 'red_edge_1_median_dry', 
        'red_edge_1_median_wet', 'red_edge_1_stdDev', 'red_edge_2_median', 
        'red_edge_2_median_dry', 'red_edge_2_median_wet', 'red_edge_2_stdDev', 
        'red_edge_3_median', 'red_edge_3_median_dry', 'red_edge_3_median_wet', 
        'red_edge_3_stdDev', 'red_edge_4_median', 'red_edge_4_median_dry', 
        'red_edge_4_median_wet', 'red_edge_4_stdDev','swir1_stdDev',  'swir2_stdDev'
    ]

    allbands = [
        'soil_median_dry', 'shade_median_dry', 'ratio_median_dry', 'gli_median_wet', 'pri_median_dry', 'dswi5_median_dry', 'osavi_median', 'npv_median_wet', 'gcvi_median_mean', 'shade_median', 'shape_median', 'soil_median', 'ndfia_median_dry', 'mbi_median_dry', 'bsi_median_stdDev', 'nbr_median', 'wetness_median_dry', 'ndfia_median_mean', 'ndfia_median', 'iia_median_wet', 'brba_median_dry', 'cloud_median', 'nir_median', 'lswi_median_wet', 'ndvi_median', 'slope', 'rvi_median', 'gcvi_median_dry', 'shape_median_dry', 'cvi_median_dry', 'blue_median_dry', 'mbi_median', 'nddi_median', 'avi_median_mean', 'ndfia_median_stdDev', 'gcvi_median_stdDev', 'swir2_median_wet', 'ui_median_wet', 'red_median_wet', 'avi_median', 'co2flux_median_wet', 'shade_median_wet', 'red_median_dry', 'gemi_median', 'osavi_median_dry', 'awei_median_mean', 'brba_median', 'cloud_median_wet', 'bsi_median_mean', 'nbr_median_dry', 'ratio_median', 'gli_median_dry', 'wetness_median', 'green_median_wet', 'brightness_median_wet', 'ndmi_median_dry', 'blue_median', 'msi_median_dry', 'evi_median', 'lswi_median_dry', 'ndti_median_dry', 'ui_median_stdDev', 'blue_median_wet', 'lai_median', 'lai_median_wet', 'cvi_median', 'spri_median_wet', 'shape_median_wet', 'dswi5_median_wet', 'afvi_median', 'ndwi_median', 'avi_median_wet', 'gli_median', 'evi_median_wet', 'nir_median_dry', 'gvmi_median', 'cvi_median_wet', 'ndvi_median_dry', 'ui_median_mean', 'iia_median', 'ndwi_median_dry', 'co2flux_median', 'system:index', 'msi_median_wet', 'osavi_median_wet', 'green_median_dry', 'pri_median', 'ui_median_dry', 'ndbi_median_wet', 'nbr_median_wet', 'nddi_median_wet', 'osavi_median_mean', 'swir1_median_wet', 'bsi_median', 'hillshade', 'swir1_median', 'swir2_median', 'gvmi_median_dry', 'rvi_median_dry', 'ndti_median', 'red_median', 'gemi_median_wet', 'lswi_median', 'brightness_median_dry', 'awei_median_wet', 'gndvi_median_wet', 'gv_median_dry', 'osavi_median_stdDev', 'ndti_median_wet', 'ndvi_median_wet', 'afvi_median_wet', 'spri_median', 'avi_median_stdDev', 'ndmi_median', 'nir_median_wet', 'evi_median_dry', 'bsi_median_dry', 'ndbi_median', 'ndwi_median_wet', 'ratio_median_wet', 'soil_median_wet', 'gcvi_median', 'ui_median', 'rvi_median_wet', 'nddi_median_dry', 'msi_median', 'npv_median', 'swir1_median_dry', 'pri_median_wet', 'ndbi_median_dry', 'avi_median_dry', 'gvmi_median_wet', 'wetness_median_wet', 'dswi5_median', 'spri_median_dry', 'awei_median', 'gndvi_median', 'lai_median_dry', 'gv_median', 'ndfia_median_wet', 'mbi_median_wet', 'gndvi_median_dry', 'brba_median_wet', 'gv_median_wet', 'ndmi_median_wet', 'npv_median_dry', 'awei_median_dry', 'gemi_median_dry', 'bsi_median_wet', 'cloud_median_dry', 'afvi_median_dry', 'gcvi_median_wet', 'iia_median_dry', 'brightness_median', 'awei_median_stdDev', 'green_median', 'co2flux_median_dry', 'swir2_median_dry'
    ]

    # lst_properties = arqParam.allFeatures
    # MOSAIC WITH BANDA 2022 
    # https://code.earthengine.google.com/c3a096750d14a6aa5cc060053580b019
    def __init__(self):

        self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])
        self.imgMosaic = (
            ee.ImageCollection(self.options['asset_collectionId'])
                            .filterBounds(self.regionInterest.geometry().bounds())
                            .select(self.options['bnd_L'])
        )
        # print(simgMosaic.first().getInfo())
        # self.imgMosaic = simgMosaic#.map(lambda img: self.process_re_escalar_img(img))
                                      
        print("  ", self.imgMosaic.size().getInfo())
        print("see band Names the first ")
        # print(" ==== ", ee.Image(self.imgMosaic.first()).bandNames().getInfo())
        print("==================================================")
        # sys.exit()
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        
        # @collection90: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
        self.imgMapbiomas = ee.Image(self.options['assetMapbiomas100'])

    # def process_re_escalar_img (self, imgA):
    #     imgMosaic = imgA.select('blue_median').gte(0).rename('constant');
    #     imgEscalada = imgA.divide(10000).toFloat();
    #     return imgMosaic.addBands(imgEscalada).select(self.featureBands).set('year', imgA.get('year'))

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
            [0.05, 0.09, 0.04, 0.61, 0.30, 0.10], #/*gv*/
            [0.14, 0.17, 0.22, 0.30, 0.55, 0.30], #/*npv*/
            [0.20, 0.30, 0.34, 0.58, 0.60, 0.58], #/*soil*/
            [0.0 , 0.0,  0.0 , 0.0 , 0.0 , 0.0 ], #/*Shade*/
            [0.90, 0.96, 0.80, 0.78, 0.72, 0.65]  #/*cloud*/
        ];

        fractions = (ee.Image(IMAGE).select(lstBandsSuf)
                                .unmix(endmembers= endmembers, sumToOne= True, nonNegative= True)
                                .float())
        fractions = fractions.rename(lstFractions)
        # // print(UNMIXED_IMAGE);
        # GVshade = GV /(1 - SHADE)
        # NDFIa = (GVshade - SOIL) / (GVshade + )
        NDFI_ADJUSTED = fractions.expression(
                                "float(((b('gv') / (1 - b('shade'))) - b('soil')) / ((b('gv') / (1 - b('shade'))) + b('npv') + b('soil')))"
                                ).rename('ndfia' + sufixo)

        NDFI_ADJUSTED = NDFI_ADJUSTED.toFloat()
        fractions = fractions.rename(lstFractionsSuf)
        RESULT_IMAGE = (fractions.toFloat()
                            .addBands(NDFI_ADJUSTED))

        return ee.Image(RESULT_IMAGE).toFloat()

    def agregate_Bands_SMA_NDFIa(self, img):
        
        indSMA_median =  self.GET_NDFIA(img, '_median')
        indSMA_med_wet =  self.GET_NDFIA(img, '_median_wet')
        indSMA_med_dry =  self.GET_NDFIA(img, '_median_dry')

        return img.addBands(indSMA_median).addBands(indSMA_med_wet).addBands(indSMA_med_dry)


    #endregion


 

    def agregateBandsContextoEstrutural(self, img):        
        """
        Calcula métricas de vizinhança (Média e Desvio Padrão) para ensinar ao modelo 
        o contexto espacial da paisagem (ex: separar savana esparsa de campestre).
        """
        # Kernel quadrado de raio 7 (Janela de 15x15 pixels = ~450x450m no Landsat)
        # Escala ideal para capturar aglomerados de árvores e fragmentação na Caatinga
        kernel = ee.Kernel.square(7)
        
        # Selecionamos apenas as versões anuais (_median) dos índices
        bandas_textura = [
            # Vegetação (Diferenciação de densidade de biomassa e dossel)
            'osavi_median', 
            'gcvi_median', 
            'avi_median', 
            
            # Solo Exposto / Degradação / Urbano (Captura o fundo/background da savana)
            'ndfia_median', 
            'bsi_median', 
            'ui_median', 
            
            # Água e Sombras (Ajuda a isolar corpos hídricos e áreas úmidas)
            'awei_median'
        ]
        
        # Filtra a imagem apenas com as bandas selecionadas para otimizar o cálculo
        img_base = img.select(bandas_textura)
        
        # Cria um redutor duplo: Calcula a Média e o Desvio Padrão simultaneamente
        # - Média: entende a "densidade" da região (ex: quantidade geral de verde ao redor)
        # - Desvio Padrão: entende a "heterogeneidade" (ex: árvores isoladas vs. pasto liso)
        redutor_combo = ee.Reducer.mean().combine(
            reducer2=ee.Reducer.stdDev(),
            sharedInputs=True
        )
        
        # Aplica o redutor na vizinhança usando álgebra de mapas nativa (rápido e vetorizado)
        contexto_espacial = img_base.reduceNeighborhood(
            reducer=redutor_combo,
            kernel=kernel
        )

        # O Earth Engine nomeará as bandas de saída automaticamente adicionando os sufixos.
        # Você terá 14 novas bandas no total. Exemplo: 
        # 'msavi_median_mean', 'msavi_median_stdDev', 'ndfia_mean', 'ndfia_stdDev', etc.
        
        return img.addBands(contexto_espacial)

    def CalculateIndice_otimizado(self, img):
        # 1. Sufixos para automatizar o cálculo das 3 estações (Anual, Wet, Dry)
        sufixos = ['_median', '_median_wet', '_median_dry']

        # 2. Dicionário Mestre de Expressões Base
        # O marcador {s} será substituído automaticamente pelo sufixo da estação
        formulas_base = {
            # Simple Ratio / Ratio Vegetation Index (Jordan, 1969 / Pearson & Miller, 1972)
            'ratio': "b('nir{s}') / b('red{s}')",
            
            # Inverse Ratio Vegetation Index (Richardson & Wiegand, 1977)
            'rvi': "b('red{s}') / b('nir{s}')",
            
            # Normalized Difference Vegetation Index (Rouse et al., 1974)
            'ndvi': "(b('nir{s}') - b('red{s}')) / (b('nir{s}') + b('red{s}'))",
            
            # Normalized Difference Built-up Index (Zha et al., 2003)
            'ndbi': "(b('swir1{s}') - b('nir{s}')) / (b('swir1{s}') + b('nir{s}'))",
            
            # Normalized Difference Moisture Index (Wilson & Sader, 2002)
            # Na literatura também é equivalente ao NDWI baseado no SWIR (Gao, 1996)
            'ndmi': "(b('nir{s}') - b('swir1{s}')) / (b('nir{s}') + b('swir1{s}'))",
            
            # Normalized Difference Water Index - Variação usando SWIR2 
            # (Adaptado de McFeeters, 1996 e Gao, 1996. Muitas vezes chamado de NBR2)
            'ndwi': "(b('nir{s}') - b('swir2{s}')) / (b('nir{s}') + b('swir2{s}'))",
            
            # Automated Water Extraction Index - Variante sem sombra / no shadow (Feyisa et al., 2014)
            'awei': "4 * (b('green{s}') - b('swir2{s}')) - (0.25 * b('nir{s}') + 2.75 * b('swir1{s}'))",
            
            # Índice Indicador de Água (Índice customizado, comum em adaptações empíricas regionais)
            'iia': "(b('green{s}') - 4 * b('nir{s}')) / (b('green{s}') + 4 * b('nir{s}'))",
            
            # Enhanced Vegetation Index de 2 Bandas (EVI2 adaptado - Jiang et al., 2008)
            'evi': "2.4 * (b('nir{s}') - b('red{s}')) / (1 + b('nir{s}') + b('red{s}'))",
            
            # Green Chlorophyll Vegetation Index (Gitelson et al., 1998)
            'gcvi': "(b('nir{s}') / b('green{s}')) - 1",
            
            # Global Environment Monitoring Index (Pinty & Verstraete, 1992)
            'gemi': "(2 * (b('nir{s}') * b('nir{s}') - b('red{s}') * b('red{s}')) + 1.5 * b('nir{s}') + 0.5 * b('red{s}')) / (b('nir{s}') + b('green{s}') + 0.5)",
            
            # Chlorophyll Vegetation Index (Vincini et al., 2008)
            'cvi': "b('nir{s}') * (b('green{s}') / (b('blue{s}') * b('blue{s}')))",
            
            # Green Leaf Index (Louhaichi et al., 2001)
            'gli': "(2 * b('green{s}') - b('red{s}') - b('blue{s}')) / (2 * b('green{s}') + b('red{s}') + b('blue{s}'))",
            
            # Shape Index / Índice de Forma (Derivado de espaços de cor visíveis)
            'shape': "(2 * b('red{s}') - b('green{s}') - b('blue{s}')) / (b('green{s}') - b('blue{s}'))",
            
            # Aerosol Free Vegetation Index (Karnieli et al., 2001)
            'afvi': "(b('nir{s}') - 0.5 * b('swir2{s}')) / (b('nir{s}') + 0.5 * b('swir2{s}'))",
            
            # Advanced Vegetation Index (Rikimaru et al., 2002)
            'avi': "(b('nir{s}') * (1.0 - b('red{s}')) * (b('nir{s}') - b('red{s}'))) ** 0.3333", 
            
            # Bare Soil Index (Rikimaru et al., 2002)
            'bsi': "((b('swir1{s}') - b('red{s}')) - (b('nir{s}') + b('blue{s}'))) / ((b('swir1{s}') + b('red{s}')) + (b('nir{s}') + b('blue{s}')))",
            
            # Band Ratio for Built-up Area (Waqar et al., 2012)
            'brba': "b('red{s}') / b('swir1{s}')",
            
            # Disease-Water Stress Index 5 (Apan et al., 2004)
            'dswi5': "(b('nir{s}') + b('green{s}')) / (b('swir1{s}') + b('red{s}'))",
            
            # Land Surface Water Index (Xiao et al., 2004)
            'lswi': "(b('nir{s}') - b('swir1{s}')) / (b('nir{s}') + b('swir1{s}'))",
            
            # Modified Bare Soil Index (Nguyen et al., 2021)
            'mbi': "((b('swir1{s}') - b('swir2{s}') - b('nir{s}')) / (b('swir1{s}') + b('swir2{s}') + b('nir{s}'))) + 0.5",
            
            # Urban Index (Kawamura et al., 1996)
            'ui': "(b('swir2{s}') - b('nir{s}')) / (b('swir2{s}') + b('nir{s}'))",
            
            # Optimized Soil-Adjusted Vegetation Index (Rondeaux et al., 1996)
            'osavi': "(b('nir{s}') - b('red{s}')) / (0.16 + b('nir{s}') + b('red{s}'))",
            
            # Green Normalized Difference Vegetation Index (Gitelson et al., 1996)
            # Nota: Embora no script esteja nomeado como 'ri' (Redness Index), a fórmula usando NIR e Green corresponde ao GNDVI.
            'gndvi': "(b('nir{s}') - b('green{s}')) / (b('nir{s}') + b('green{s}'))",
            
            # Tasseled Cap Brightness - Coeficientes OLI Landsat 8 (Baig et al., 2014)
            'brightness': "0.3037 * b('blue{s}') + 0.2793 * b('green{s}') + 0.4743 * b('red{s}') + 0.5585 * b('nir{s}') + 0.5082 * b('swir1{s}') + 0.1863 * b('swir2{s}')",
            
            # Tasseled Cap Wetness - Coeficientes OLI Landsat 8 (Baig et al., 2014)
            'wetness': "0.1509 * b('blue{s}') + 0.1973 * b('green{s}') + 0.3279 * b('red{s}') + 0.3406 * b('nir{s}') + 0.7112 * b('swir1{s}') + 0.4572 * b('swir2{s}')",
            
            # Moisture Stress Index (Rock et al., 1990)
            'msi': "b('nir{s}') / b('swir1{s}')",
            
            # Global Vegetation Moisture Index (Ceccato et al., 2002)
            'gvmi': "((b('nir{s}') + 0.1) - (b('swir1{s}') + 0.02)) / ((b('nir{s}') + 0.1) + (b('swir1{s}') + 0.02))",
            
            # Pseudo-Photochemical Reflectance Index (Adaptado de Gamon et al., 1992 para satélites de banda larga)
            'pri': "(b('green{s}') - b('blue{s}')) / (b('green{s}') + b('blue{s}'))",
            
            # Normalized Burn Ratio (Key & Benson, 1999)
            'nbr': "(b('nir{s}') - b('swir1{s}')) / (b('nir{s}') + b('swir1{s}'))",
            
            # Normalized Difference Tillage Index (van Deventer et al., 1997)
            'ndti': "(b('swir1{s}') - b('swir2{s}')) / (b('swir1{s}') + b('swir2{s}'))"
        }

        novas_bandas_base = []

        # 3. Executa o loop achatando o processamento
        for s in sufixos:
            for nome_indice, expressao in formulas_base.items():
                expr_formatada = expressao.format(s=s)
                nome_banda = f"{nome_indice}{s}"
                
                # Gera a banda isolada e joga na lista (sem fazer addBands na imagem inteira ainda)
                banda_calc = img.expression(f"float({expr_formatada})").rename(nome_banda)
                novas_bandas_base.append(banda_calc)

        # Junta a imagem original com as novas bandas de uma vez só (Flattening)
        img_com_base = ee.Image.cat([img] + novas_bandas_base)

        # 4. Índices Dependentes (que usam índices calculados acima)
        bandas_dependentes = []
        for s in sufixos:
            # LAI depende de EVI
            lai = img_com_base.expression(f"float(3.618 * (b('evi{s}') - 0.118))").rename(f"lai{s}")
            # NDDI depende de NDVI e NDWI
            nddi = img_com_base.expression(f"float((b('ndvi{s}') - b('ndwi{s}')) / (b('ndvi{s}') + b('ndwi{s}')))").rename(f"nddi{s}")
            # SPRI depende de PRI
            spri = img_com_base.expression(f"float((b('pri{s}') + 1) / 2)").rename(f"spri{s}")
            bandas_dependentes.extend([lai, nddi, spri])

        img_quase_pronta = ee.Image.cat([img_com_base] + bandas_dependentes)

        # Fluxo de CO2 depende de SPRI (que acabou de ser gerado)
        bandas_co2 = []
        for s in sufixos:
            co2 = img_quase_pronta.expression(f"float(b('ndvi{s}') * b('spri{s}'))").rename(f"co2flux{s}")
            bandas_co2.append(co2)

        # 5. Concatena tudo e aplica as funções complexas finais
        imagem_final = ee.Image.cat([img_quase_pronta] + bandas_co2)

        # Adiciona Textura, Relevo e NDFIa (mantidos como métodos separados devido à complexidade)
        # imagem_final = self.agregateBandsTexturasGLCM(imagem_final)
        imagem_final = self.addSlopeAndHilshade(imagem_final)
        imagem_final = self.agregate_Bands_SMA_NDFIa(imagem_final)
        imagem_final = self.agregateBandsContextoEstrutural(imagem_final)

        return imagem_final

    def make_mosaicofromReducer(self, colMosaic):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]
        # self.bandMosaic = band_year + band_wets + band_drys
        # print("bandas principais \n ==> ", self.bandMosaic)
        # bandsDry =None
        percentilelowDry = 5
        percentileDry = 35
        percentileWet = 65

        # get dry season collection
        evilowDry = (
            colMosaic.select(['evi'])
                    .reduce(ee.Reducer.percentile([percentilelowDry]))
        )
        eviDry = (
            colMosaic.select(['evi'])
                    .reduce(ee.Reducer.percentile([percentileDry]))
        )        

        collectionDry = (
            colMosaic.map(lambda img: img.mask(img.select(['evi']).gte(evilowDry))
                                        .mask(img.select(['evi']).lte(eviDry)))
        )

        # get wet season collection
        eviWet = (
            colMosaic.select(['evi'])        
                    .reduce(ee.Reducer.percentile([percentileWet]))
        )
        collectionWet = (
            colMosaic.map(lambda img: img.mask(img.select(['evi']).gte(eviWet)))                                        
        )

        # Reduce collection to median mosaic
        mosaic = (
            colMosaic.select(self.options['bnd_L'])
                .reduce(ee.Reducer.median()).rename(band_year)
        )

        # get dry median mosaic
        mosaicDry = (
            collectionDry.select(self.options['bnd_L'])
                .reduce(ee.Reducer.median()).rename(band_drys)
        )

        # get wet median mosaic
        mosaicWet = (
            collectionWet.select(self.options['bnd_L'])
                .reduce(ee.Reducer.median()).rename(band_wets)
        )

        # get stdDev mosaic
        mosaicStdDev = (
            colMosaic.select(self.options['bnd_L'])
                        .reduce(ee.Reducer.stdDev())
        )

        mosaic = (mosaic.addBands(mosaicDry)
                        .addBands(mosaicWet)
                        .addBands(mosaicStdDev)
        )

        return mosaic
    
    def make_mosaicofromIntervalo(self, colMosaic, year_courrent):
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]    
        band_wets = [bnd + '_wet' for bnd in band_year]

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

        return mosaico

    def iterate_by_grid(self, idGrade, askSize):        

        # loading geometry bacim    
        oneGrade = (ee.FeatureCollection(self.options['asset_grad'])
                            .filter(ee.Filter.eq('indice', int(idGrade)))
                            .geometry()
                    )
        # print("show size regions ", oneGrade.size().getInfo())                                
        # oneGrade = oneGrade.geometry()  
        # print("show area regions ", oneGrade.area().getInfo()) 
        # sys.exit()
        
        layerSamplesMask = (ee.ImageCollection(self.options['asset_mask_toSamples'])
                                .filterBounds(oneGrade)
                                # .mosaic().clip(oneGrade)
        )
        numLayers = 1
        try:
            numLayers =  layerSamplesMask.size().getInfo()
            if numLayers > 0:
                layerSamplesMask = layerSamplesMask.mosaic()
            else:
                layerSamplesMask = ee.Image.constant(1).clip(oneGrade) 
                numLayers = 0
        except:
            layerSamplesMask = ee.Image.constant(1).clip(oneGrade) 
            numLayers = 0    

        # shpAllFeat = ee.FeatureCollection([]) 
        # Usar uma lista Python para acumular as FeatureCollections anuais
        # Evita a criação de uma árvore profunda de .merge()
        list_of_fc_years = []

        # Junta todas as bandas que realmente importam em uma lista Python
        # Se você precisar de mais bandas (como as texturas novas), garanta que estão nessas listas no __init__
        todas_bandas_alvo = self.featureBands + self.features_extras

        for nyear in self.lst_year[:]:
            bandYear = 'classification_' + str(nyear)
            print(f" processing grid_year => {idGrade} <> {bandYear} ")     
            date_inic =  str(nyear) + '-01-01'      
            date_end = str(nyear) + '-12-31'

            imgColfiltered = (
                self.imgMosaic.filter(ee.Filter.date(date_inic, date_end))
                        .filterBounds(oneGrade)
            )

            # img_recMosaico = img_recMosaic.map(lambda img: self.calculateBandsIndexEVI(img))
            # mosaicoBuilded = self.make_mosaicofromReducer(imgColfiltered)
            mosaicoBuilded = self.make_mosaicofromIntervalo(imgColfiltered, nyear) 
            # print("metadado bandas names ", mosaicoBuilded.bandNames().getInfo())

            print("----- calculado todos os old(102) now 123 indices ---------------------")
            img_recMosaicnewB = self.CalculateIndice_otimizado(mosaicoBuilded)
            bndAdd = img_recMosaicnewB.bandNames().getInfo()            
            print(f"know bands names Index {len(bndAdd)}")
            print("  ", bndAdd)
            
            # sys.exit()
            nameBandYear = bandYear
            if nyear == 2025:
                nameBandYear = 'classification_2024'
            if numLayers > 0:    
                if nyear > 2023:
                    maskYear = layerSamplesMask.select("layer_samples_2023").eq(1)#.clip(oneGrade)                    
                else:
                    maskYear = layerSamplesMask.select("layer_samples_" + str(nyear)).eq(1)#.clip(oneGrade)
                # print("imagem mask layer => ", maskYear.bandNames().getInfo())
            else:
                maskYear = layerSamplesMask

            # shpAllFeat = ee.FeatureCollection([]) 

            layerCC = (
                self.imgMapbiomas.select(nameBandYear)
                    .remap(self.options['classMapB'], self.options['classNew'])
                    .rename('class')   # .clip(oneGrade)          
            )             
            # print("numero de ptos controle ", roisAct.size().getInfo())
            # opcoes para o sorteio estratificadoBuffBacia
            # sample(region, scale, projection, factor, numPixels, seed, dropNulls, tileScale, geometries)
            ptosTemp = (
                img_recMosaicnewB.addBands(layerCC)
                .select(self.allbands) # Filtra a imagem brutalmente!
                .addBands(ee.Image.constant(nyear).rename('year'))
                .addBands(ee.Image.constant(idGrade).rename('GRID_ID'))
                .updateMask(maskYear)
                .sample(
                    region=  oneGrade,  
                    scale= 30,   
                    numPixels= 3000,
                    dropNulls= True,
                    geometries= True,
                    tileScale= 16
                )
            )
            # lstBandsNNull = ['blue_median', 'blue_median_wet', 'blue_median_dry']
            # ptosTemp = ptosTemp.filter(ee.Filter.notNull(lstBandsNNull))
            # print("numero de ptos controle ", ptosTemp.size().getInfo())
            # insere informacoes em cada ft
            # ptosTemp = ptosTemp.map(lambda feat : feat.set('year', nyear, 'GRID_ID', idGrade) )
            # shpAllFeat = shpAllFeat.merge(ptosTemp)
            list_of_fc_years.append(ptosTemp)
                # sys.exit()
            # print(f"======  coleted rois from class {self.options['lsClasse']}  =======")
            # sys.exit()
        name_exp = 'rois_grade_' + str(idGrade) #  + "_" + str(nyear)# + "_cc_" + str(nclass)    
        # name_exp = 'rois_grade_' + str(idGrade)
        # if askSize:
        #     sizeROIscol = ee.FeatureCollection(shpAllFeat).size().getInfo()
        #     if sizeROIscol > 1:
        #         self.save_ROIs_toAsset(ee.FeatureCollection(shpAllFeat), name_exp) 
        #     else:
        #         print(" we can´t to export roi ")

        # else:
        #     self.save_ROIs_toAsset(ee.FeatureCollection(shpAllFeat), name_exp)
        # Achatando a lista em uma única FeatureCollection otimizada
        if list_of_fc_years:
            shpAllFeat = ee.FeatureCollection(list_of_fc_years).flatten()
            
            # Removemos a verificação assíncrona (askSize e .getInfo()).
            # Apenas envia para a task e deixa o servidor gerenciar limites.
            self.save_ROIs_toAsset(shpAllFeat, name_exp)
        else:
            print("Nenhuma amostra processada para esta bacia.")
                
    
    # salva ftcol para um assetindexIni
    # lstKeysFolder = ['cROIsN2manualNN', 'cROIsN2clusterNN'] 
    def save_ROIs_toAsset(self, collection, name):
        optExp = {
            'collection': collection,
            'description': name,
            'assetId': self.options['asset_output_grade'] + "/" + name
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("exportando ROIs da bacia $s ...!", name)




def ask_byGrid_saved(dict_asset):
    getlstFeat = ee.data.getList(dict_asset)
    lst_temporalAsset = []
    assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']
    for idAsset in getlstFeat[:]:         
        path_ = idAsset.get('id')        
        name_feat = path_.replace( assetbase + '/', '')
        print("reading <==> " + name_feat)
        idGrade = name_feat.split('_')[2]
        # name_exp = 'rois_grade_' + str(idGrade) + "_" + str(nyear)
        if int(idGrade) not in lst_temporalAsset:
            lst_temporalAsset.append(int(idGrade))
    
    return lst_temporalAsset

asset_grid = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga'
shp_grid = ee.FeatureCollection(asset_grid)

# lstIds = shp_grid.reduceColumns(ee.Reducer.toList(), ['indice']).get('list').getInfo()
# print("   ", lstIds)

lstIdCode = [
    3990, 3991, 3992, 3993, 3994, 3995, 3996, 3997, 3998, 3999, 4000, 4096, 
    4097, 4098, 4099, 4100, 4101, 4102, 4103, 4104, 4105, 4106, 4107, 4108, 
    4109, 4110, 4111, 4112, 4113, 4114, 4115, 4116, 4117, 4118, 4119, 4120, 
    4121, 4122, 4123, 4414, 4415, 4416, 4417, 4418, 4419, 4420, 4421, 4422, 
    4423, 4424, 4425, 4426, 4427, 4428, 4429, 4430, 4431, 4432, 4433, 4434,
    4435, 4436, 4437, 4438, 4439, 4440, 4202, 4203, 4204, 4205, 4206, 4207, 
    4208, 4209, 4210, 4211, 4212, 4213, 4214, 4215, 4216, 4217, 4218, 4219, 
    4220, 4221, 4222, 4223, 4224, 4225, 4226, 4227, 4228, 4001, 4002, 4003, 
    4004, 4005, 4006, 4007, 4008, 4009, 4010, 4011, 4012, 4013, 4014, 4015, 
    4016, 4308, 4309, 4310, 4311, 4312, 4313, 4314, 4315, 4316, 4317, 4318, 
    4319, 4320, 4321, 4322, 4323, 4324, 4325, 4326, 4327, 4328, 4329, 4330, 
    4331, 4332, 4333, 4334, 4626, 4627, 4628, 4629, 4630, 4631, 4632, 4633, 
    4634, 4635, 4636, 4637, 4638, 4639, 4640, 4641, 4642, 4643, 4644, 4645, 
    4646, 4647, 4648, 4649, 4650, 4651, 4942, 4943, 4944, 4945, 4946, 4947, 
    4948, 4949, 4950, 4951, 4952, 4953, 4954, 4955, 4956, 4957, 4958, 4959, 
    4960, 4961, 4962, 4731, 4732, 4733, 4734, 4735, 4736, 4737, 4738, 4739, 
    4740, 4741, 4742, 4743, 4744, 4745, 4746, 4747, 4748, 4749, 4750, 4751, 
    4752, 4753, 4754, 4755, 4756, 4520, 4521, 4522, 4523, 4524, 4525, 4526, 
    4527, 4528, 4529, 4530, 4531, 4532, 4533, 4534, 4535, 4536, 4537, 4538, 
    4539, 4540, 4541, 4542, 4543, 4544, 4545, 4546, 4837, 4838, 4839, 4840, 
    4841, 4842, 4843, 4844, 4845, 4846, 4847, 4848, 4849, 4850, 4851, 4852, 
    4853, 4854, 4855, 4856, 4857, 5376, 5377, 5378, 5379, 5380, 5381, 5382, 
    5383, 5384, 5385, 5154, 5155, 5156, 5157, 5158, 5159, 5160, 5161, 5162, 
    5163, 5164, 5165, 5166, 5167, 5168, 5169, 5170, 5171, 5172, 5173, 5174, 
    5175, 5471, 5472, 5473, 5474, 5475, 5476, 5477, 5478, 5479, 5480, 5481, 
    5482, 5483, 5484, 5485, 5486, 5487, 5488, 5489, 5490, 5261, 5262, 5263, 
    5264, 5265, 5266, 5267, 5268, 5269, 5270, 5271, 5272, 5273, 5274, 5275, 
    5276, 5277, 5278, 5279, 5280, 5048, 5049, 5050, 5051, 5052, 5053, 5054, 
    5055, 5056, 5057, 5058, 5059, 5060, 5061, 5062, 5063, 5064, 5065, 5066, 
    5067, 5366, 5367, 5368, 5369, 5370, 5371, 5372, 5373, 5374, 5375, 5901, 
    5902, 5903, 5904, 5905, 5906, 5907, 5908, 5683, 5684, 5686, 5687, 5688, 
    5689, 5690, 5691, 5692, 5693, 5694, 5695, 5696, 5697, 5698, 5699, 5700, 
    5792, 5793, 5794, 5795, 5796, 5797, 5798, 5799, 5800, 5801, 5802, 5803, 
    5804, 5805, 5576, 5577, 5578, 5579, 5580, 5581, 5582, 5583, 5584, 5585, 
    5586, 5587, 5588, 5589, 5590, 5591, 5592, 5593, 5594, 5595, 6217, 6218, 
    6219, 6220, 6221, 6222, 6006, 6007, 6008, 6009, 6010, 6011, 6012, 6013, 
    6323, 6324, 6325, 6326, 6327, 6112, 6113, 6114, 6115, 6116, 6117, 6118, 
    2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2425, 2426, 2427, 2428, 
    2429, 2430, 2431, 2432, 2433, 2434, 2220, 2223, 2224, 2840, 2841, 2842, 
    2843, 2844, 2845, 2846, 2847, 2848, 2849, 2850, 2851, 2852, 2853, 2854, 
    2855, 2856, 2633, 2634, 2635, 2636, 2637, 2638, 2639, 2640, 2641, 2642, 
    2643, 2644, 2645, 2646, 2941, 2942, 2943, 2944, 2945, 2946, 2947, 2948, 
    2949, 2950, 2951, 2952, 2953, 2954, 2955, 2956, 2957, 2958, 2959, 2960, 
    2737, 2738, 2739, 2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 
    2749, 2750, 2751, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 
    2538, 2539, 2540, 3360, 3361, 3362, 3363, 3364, 3365, 3366, 3367, 3368, 
    3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377, 3378, 3379, 3380, 
    3381, 3382, 3383, 3150, 3151, 3152, 3153, 3154, 3155, 3156, 3157, 3158, 
    3159, 3160, 3161, 3162, 3163, 3164, 3165, 3166, 3167, 3168, 3169, 3170, 
    3171, 3465, 3466, 3467, 3468, 3469, 3470, 3471, 3472, 3473, 3474, 3475, 
    3476, 3477, 3478, 3479, 3480, 3481, 3482, 3483, 3484, 3485, 3486, 3487, 
    3488, 3489, 3255, 3256, 3257, 3258, 3259, 3260, 3261, 3262, 3263, 3264, 
    3265, 3266, 3267, 3268, 3269, 3270, 3271, 3272, 3273, 3274, 3275, 3276, 
    3277, 3278, 3046, 3047, 3048, 3049, 3050, 3051, 3052, 3053, 3054, 3055, 
    3056, 3057, 3058, 3059, 3060, 3061, 3062, 3063, 3064, 3584, 3585, 3586, 
    3587, 3588, 3589, 3590, 3591, 3592, 3593, 3594, 3885, 3886, 3887, 3888, 
    3889, 3890, 3891, 3892, 3893, 3894, 3895, 3896, 3897, 3898, 3899, 3900, 
    3901, 3902, 3903, 3904, 3905, 3906, 3907, 3908, 3909, 3910, 3911, 3675, 
    3676, 3677, 3678, 3679, 3680, 3681, 3682, 3683, 3684, 3685, 3686, 3687, 
    3688, 3689, 3690, 3691, 3692, 3693, 3694, 3695, 3696, 3697, 3698, 3699, 
    3700, 3780, 3781, 3782, 3783, 3784, 3785, 3786, 3787, 3788, 3789, 3790, 
    3791, 3792, 3793, 3794, 3795, 3796, 3797, 3798, 3799, 3800, 3801, 3802, 
    3803, 3804, 3805, 3570, 3571, 3572, 3573, 3574, 3575, 3576, 3577, 3578, 
    3579, 3580, 3581, 3582, 3583
]


# lstIdCode = [
#     3992, 4098, 4203, 4546, 3887, 3675
# ]



reprocessar = False
if reprocessar:
    df = pd.read_csv('lista_gride_with_failsYearSaved.csv')
    lstIdCode = df['idGrid'].tolist()
    print(f"we reprocessing {len(lstIdCode)} gride that fails to samples \n", lstIdCode)

# sys.exit()
param = {
    'anoInicial': 1985,
    'anoFinal': 2024,
    'changeCount': True,
    'numeroTask': 6,
    'numeroLimit': 110,
    'conta': {
        '0': 'caatinga01',
        '10': 'caatinga02',
        '20': 'caatinga03',
        '30': 'caatinga04',
        '40': 'caatinga05',
        '50': 'solkan1201',
        # '120': 'diegoGmail',
        '60': 'solkanGeodatin',
        '70': 'superconta'
    },
}
def gerenciador(cont):    
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
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
        
        # for lin in tarefas:   
        #     print(str(lin))         
            # relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

askingbySizeFC = False
searchFeatSaved = True
cont = 70
if param['changeCount']:
    cont = gerenciador(cont)


objetoMosaic_exportROI = ClassMosaic_indexs_Spectral()
print("saida ==> ", objetoMosaic_exportROI.options['asset_output_grade'])
# sys.exit()
if searchFeatSaved: 
    lstFeatAsset = ask_byGrid_saved({'id': objetoMosaic_exportROI.options['asset_output_grade']})
    print("   lista de feat ", lstFeatAsset[:5] )
    print("  == size ", len(lstFeatAsset))
    askingbySizeFC = False
else:
    lstFeatAsset = []
print("size of grade geral >> ", len(lstIdCode))
# sys.exit()
inicP = 0 # 0, 100
endP = 100   # 100, 200, 300, 600
for cc, item in enumerate(lstIdCode[inicP:endP]):
    print(f"# {cc + 1 + inicP} loading geometry grade {item}")   
    if item not in lstFeatAsset:
        objetoMosaic_exportROI.iterate_by_grid(item, askingbySizeFC)
        # cont = gerenciador(cont)
    # sys.exit()

