#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
SCRIPT DE CLASSIFICAÇÃO — fluxo funcional (sem classes)
Mosaico 3 períodos + índices espectrais → GTB → export
'''

import ee
import os
import sys
from pathlib import Path
import arqParametros_class as arqParams

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account  # noqa: E402
from gee_tools import *  # noqa: E402, F403

projAccount = get_current_account()
print(f"projeto >>> {projAccount}")
ee.Initialize(project=projAccount)

# ============================================================
# PARÂMETROS
# ============================================================
NBACIA  = '765'
NYEAR   = 1986
VERSION = 1

ASSET_BACIAS  = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions'
ASSET_COLECAO = 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY'
ASSET_ROIS    = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCred'
ASSET_OUT     = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1'

BND_L = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']

PMT_GTB = {
    'numberOfTrees': 35,
    'shrinkage': 0.1,
    'samplingRate': 0.65,
    'loss': 'LeastSquares',
    'seed': 0,
}

LST_FEAT_SELECT = [
    # --- BLOCO A (19 índices) ---
    'green_median_dry', 'green_median_wet',
    'red_median_dry', 'red_median_wet', 'swir1_median_wet', 
    'swir2_median_wet', 'swir2_median', 'swir2_median_dry',
    'ndti_median_dry', 'ndti_median_wet', 'ndti_median',    
    'brba_median_dry', 'brba_median_wet', 
    'gli_median_dry', 'mbi_median_dry',   'shape_median_dry',
    'ndvi_median', 'ndvi_median_dry', 'ndvi_median_wet',
    'ndwi_median_dry',  'ndwi_median', 'ndwi_median_wet',
    'gcvi_median', #'avi_median',
    'bsi_median','ui_median', 
    # 'evi_median_wet',   'evi_median', 'evi_median_dry',
    # 'pri_median_dry',   'pri_median', 'pri_median_wet',
    'awei_median', 'awei_median_wet',  'awei_median_dry',        
    
    # --- BLOCO B (20 índices) — comentado para teste ---
    # 'brightness_median', 'wetness_median',
    # 'wetness_median_wet', 'brightness_median_dry',

]

# ============================================================
# GEOMETRIA DA BACIA
# ============================================================
print(f"\n--- carregando bacia {NBACIA} ---")
bacias_fc   = ee.FeatureCollection(ASSET_BACIAS).filter(ee.Filter.eq('nunivotto4', NBACIA))
bacias_fc = bacias_fc.map(lambda f: f.set('id_codigo', 1))
bacia_raster =  bacias_fc.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
baciabuffer = bacias_fc.geometry()
print(f"bacia carregada: {bacias_fc.size().getInfo()} feature(s)")

# ============================================================
# MOSAICO (3 PERÍODOS)
# col é um único objeto Python — deduplicado na serialização GEE
# ============================================================
print(f"\n--- construindo mosaico {NYEAR} ---")

col = (ee.ImageCollection(ASSET_COLECAO)
         .filterBounds(baciabuffer)
         .filter(ee.Filter.date(f'{NYEAR}-01-01', f'{NYEAR}-12-31'))
         .select(BND_L))

bnd_median = [b + '_median'     for b in BND_L]
bnd_wet    = [b + '_median_wet' for b in BND_L]
bnd_dry    = [b + '_median_dry' for b in BND_L]

mosaic_year = col.max().rename(bnd_median)
mosaic_wet  = col.filter(ee.Filter.date(f'{NYEAR}-01-01', f'{NYEAR}-07-31')).max().rename(bnd_wet)
mosaic_dry  = col.filter(ee.Filter.date(f'{NYEAR}-08-01', f'{NYEAR}-12-31')).max().rename(bnd_dry)

# mosaic é o único nó raiz — todas as expressões de índice partem daqui
mosaic = ee.Image.cat([mosaic_year, mosaic_wet, mosaic_dry]).updateMask(bacia_raster)

# ============================================================
# ÍNDICES ESPECTRAIS
# Cada índice referencia `mosaic` diretamente (sem intermediários)
# ee.Image.cat no final — grafo plano, sem profundidade
# ============================================================
print("\n--- calculando índices espectrais ---")

sufixos        = ['_median', '_median_wet', '_median_dry']
formulas_base  = arqParams.FORMULAS_INDICES_ESPECTRAIS
indices = []

for s in sufixos:
    for nome_indice, expressao in formulas_base.items():
        nome_banda = f"{nome_indice}{s}"
        if nome_banda in LST_FEAT_SELECT:
            expr = expressao.format(s=s)
            indices.append(mosaic.expression(f"float({expr})").rename(nome_banda))

# spri e slope desativados para isolar complexidade

# combina tudo num único cat — grafo plano
mosaic_full = ee.Image.cat([mosaic] + indices)

print(f"índices calculados: {len(indices)}")

# ============================================================
# SELECIONA APENAS AS BANDAS DO CLASSIFICADOR
# ============================================================
bandas_classif = [b for b in LST_FEAT_SELECT if b in LST_FEAT_SELECT]
mosaic_classif = mosaic_full.select(bandas_classif)
print(f"bandas para classificação ({len(bandas_classif)}): {bandas_classif}")

# ============================================================
# AMOSTRAS
# ============================================================
print(f"\n--- carregando amostras ---")
ano_amostra = NYEAR if NYEAR <= 2024 else 2024
rois_path   = os.path.join(ASSET_ROIS, f"rois_fromBasin_{NBACIA}_{ano_amostra}")
print(f"asset ROIs: {rois_path}")
ROIs = ee.FeatureCollection(rois_path)
print(f"amostras: {ROIs.size().getInfo()}")

# ============================================================
# CLASSIFICADOR GTB
# ============================================================
print(f"\n--- treinando GTB com {len(bandas_classif)} bandas ---")
classifier = (ee.Classifier.smileGradientTreeBoost(**PMT_GTB)
                .train(ROIs, 'class', bandas_classif))
print("classificador treinado")

# ============================================================
# CLASSIFICAÇÃO
# ============================================================
band_result = f'classification_{NYEAR}'
classified  = mosaic_classif.classify(classifier, band_result)
classified  = classified.set({
    'id_bacia':   NBACIA,
    'version':    VERSION,
    'biome':      'CAATINGA',
    'classifier': 'GTB',
    'collection': '11.0',
    'sensor':     'Landsat',
    'year':       NYEAR,
})
classified = classified.set('system:footprint', baciabuffer.coordinates())

# ============================================================
# EXPORT
# ============================================================
nome_desc = f"BACIA_{NBACIA}_{NYEAR}_GTB_col11_BND_fm-v_{VERSION}"
asset_id  = os.path.join(ASSET_OUT, nome_desc)

task = ee.batch.Export.image.toAsset(
    image=classified,
    description=nome_desc,
    assetId=asset_id,
    region=baciabuffer,
    scale=30,
    maxPixels=1e13,
    pyramidingPolicy={'.default': 'mode'},
)
task.start()
print(f"\n--- task enviada: {nome_desc} ---")
for k, v in dict(task.status()).items():
    print(f"  {k}: {v}")
