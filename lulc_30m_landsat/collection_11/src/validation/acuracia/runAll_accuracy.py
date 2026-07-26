#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runAll_accuracy.py
Exporta pontos de acurácia para TODAS as combinações sem argumentos:
  - filtros POS-CLASS (nc=7) × todas as versões disponíveis no GEE
  - classificação direta (nc=10) × todas as versões
  - coleções anteriores Map71/80/90/100 (nc=10)

Troca de conta GEE a cada TROCA_APOS tasks exportadas.
"""
import ee
import os
import sys
import collections
collections.Callable = collections.abc.Callable
from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

projAccount = get_current_account()
print(f"conta inicial >>> {projAccount} <<<")
try:
    ee.Initialize(project=projAccount)
    print('GEE inicializado com sucesso')
except Exception as e:
    print(f'Erro ao inicializar GEE: {e}')
    raise

# ─── Controle de contas ───────────────────────────────────────────────────────
CONTAS     = ['caatinga02', 'caatinga03','caatinga04', 'caatinga05']
TROCA_APOS = 6
task_total = [0]  # lista para mutabilidade em closure

def checar_troca_conta():
    n = task_total[0]
    if n >= 0 and n % TROCA_APOS == 0:
        nova = CONTAS[(n // TROCA_APOS) % len(CONTAS)]
        switch_user(nova)
        ee.Initialize(project=get_project_from_account(nova))
        print(f"  ↪ conta trocada → {nova}")

# ─── Combinações a processar ──────────────────────────────────────────────────
# (tipo, filtro, colecao, num_class)
COMBINATIONS = [
    ('filter', 'gap_fill',      None,     7),
    ('filter', 'temporalA',     None,     7),
    ('filter', 'frequency',     None,     7),
    ('filter', 'spatial_Sieve', None,     7),
    ('filter', 'temporal_CC',   None,     7),
    ('filter', 'estabilidade',  None,     7),
    ('filter', 'correcoes',     None,     7),
    ('class',  None,            None,     10),
    ('colecao',None,            'Map71',  10),
    ('colecao',None,            'Map80',  10),
    ('colecao',None,            'Map90',  10),
    ('colecao',None,            'Map100', 10),
]

# ─── Bacias e parâmetros fixos ────────────────────────────────────────────────
nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592',
    '761111', '761112', '7612', '7613', '7614', '7615',
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754',
    '7761', '7764', '7581', '7625', '7584', '751',
    '7616', '745', '7424', '7618', '7561', '755', '7617',
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752'
]

BACIAS_CORRECOES = {'761112', '7754', '7591', '771', '7741', '7746', '761111', '753'}

param = {
    'asset_bacias':       'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'assetBiomas':        'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'assetpointLapig23':  'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col5_points_w_edge_and_edited_v3',
    'asset_biomas_raster':'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'assetCol':           'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
    'asset_filters': {
        'gap_fill':      'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill',
        'temporalA':     'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',        
        'frequency':     'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency',
        'spatial_Sieve': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_sieve',
        'temporal_CC':   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalbyCC',
        'estabilidade':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/EstabilidadeCols',
        'correcoes':     'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/correcoes_pontuais',
    },
    'colecoes_ant': {
        'Map71':  'projects/mapbiomas-public/assets/brazil/lulc/collection7_1/mapbiomas_collection71_integration_v1',
        'Map80':  'projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1',
        'Map90':  'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'Map100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    },
    'anoInicial':   1985,
    'anoFinal':     2025,
    'lsProp':       ['BIOMA_250K', 'CARTA_2', 'DECLIVIDAD', 'PESO_AMOS', 'LON', 'LAT'],
    'scale':        30,
    'driverFolder': 'ptosAccCol11',
}

# ─── Remapeamento de classes ──────────────────────────────────────────────────
classMapB = [
     0,  3,  4,  5,  6,  9, 11, 12, 13, 15, 18, 19, 20, 21, 22,
    23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 37, 38, 39, 40, 41,
    42, 43, 44, 45, 46, 47, 48, 49, 50, 62, 75
]
classNew_10 = [
    27,  3,  4,  3,  3,  3, 12, 12, 12, 15, 19, 19, 19, 21, 25,
    25, 25, 25, 33, 29, 25, 33, 12, 33, 19, 33, 33, 19, 19, 19,
    36, 36, 36, 36, 36, 36, 36,  4, 12, 36, 25
]
classNew_7  = [
    27,  3,  4,  3,  3,  3, 12, 12, 12, 21, 21, 21, 21, 21, 25,
    25, 25, 25, 33, 25, 25, 33, 12, 33, 21, 33, 33, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21,  4, 12, 21, 25
]

dictRemap = {
    "FORMAÇÃO FLORESTAL": 3,      "FORMAÇÃO SAVÂNICA": 4,
    "MANGUE": 3,                   "RESTINGA HERBÁCEA": 4,
    "FLORESTA PLANTADA": 36,       "FLORESTA INUNDÁVEL": 3,
    "CAMPO ALAGADO E ÁREA PANTANOSA": 12,
    "APICUM": 12,                  "FORMAÇÃO CAMPESTRE": 12,
    "AFLORAMENTO ROCHOSO": 29,     "OUTRA FORMAÇÃO NÃO FLORESTAL": 12,
    "PASTAGEM": 15,                "CANA": 19,
    "LAVOURA TEMPORÁRIA": 19,      "LAVOURA PERENE": 36,
    "MINERAÇÃO": 25,               "PRAIA E DUNA": 25,
    "INFRAESTRUTURA URBANA": 25,   "VEGETAÇÃO URBANA": 25,
    "OUTRA ÁREA NÃO VEGETADA": 25,
    "RIO, LAGO E OCEANO": 33,      "AQUICULTURA": 33,
    "NÃO OBSERVADO": 27,
}

# ─── Funções auxiliares ───────────────────────────────────────────────────────
def change_value_class(feat):
    """Converte CLASS_YEAR de texto para código numérico; null → 27 (Não Observado)."""
    pts_remap = ee.Dictionary(dictRemap)
    feat_tmp  = feat.select(param['lsProp'])
    for year in range(param['anoInicial'], param['anoFinal'] + 1):
        nam = 'CLASS_' + str(year)
        raw = feat.get(nam)
        feat_tmp = feat_tmp.set(
            nam, ee.Algorithms.If(raw, pts_remap.get(ee.String(raw), 27), 27)
        )
    return feat_tmp


def processar_e_exportar(ptosAcc, imgMosaic, listBandas, classNew,
                          lsAllprop, subfolder, version):
    """Coleta pontos de acurácia por bacia e exporta uma tabela para o Drive."""
    ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
    all_fcs      = []
    total_pts    = 0

    for nbacia in nameBacias:
        baciaGeom = ftcol_bacias.filter(ee.Filter.eq('nunivotto4', nbacia)).geometry()
        ptosTemp  = ptosAcc.filterBounds(baciaGeom)
        n = ptosTemp.size().getInfo()
        if n == 0:
            continue
        total_pts += n

        maskBacia = (ee.FeatureCollection([ee.Feature(ee.Geometry(baciaGeom), {'v': 1})])
                     .reduceToImage(['v'], ee.Reducer.first()).gt(0))

        mapBacia = ee.Image().byte()
        for band in listBandas:
            mapBacia = mapBacia.addBands(
                imgMosaic.select(band)
                         .updateMask(maskBacia)
                         .remap(classMapB, classNew)
                         .rename(band)
            )
        mapBacia = mapBacia.select(listBandas)

        pts = (mapBacia.unmask(27)
               .sampleRegions(collection=ptosTemp, properties=lsAllprop,
                              scale=param['scale']))
        all_fcs.append(pts.map(lambda f: f.set('bacia', nbacia)))

    fc_out  = ee.FeatureCollection(all_fcs).flatten() if all_fcs else ee.FeatureCollection([])
    ver_str = str(version) if version is not None else 'na'
    nome    = f"acc_col11{subfolder}_vers_{ver_str}"

    ee.batch.Export.table.toDrive(
        collection=fc_out,
        description=nome,
        folder=param['driverFolder'],
    ).start()

    task_total[0] += 1
    checar_troca_conta()
    print(f"  ✓ {nome}  [{total_pts} pontos | task #{task_total[0]}]")


# ─── Carregar pontos de referência uma única vez (até 2025) ──────────────────
bioma250mil = (ee.FeatureCollection(param['assetBiomas'])
               .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry())

pointTrue = (ee.FeatureCollection(param['assetpointLapig23'])
             .filterBounds(bioma250mil)
             .map(change_value_class))

print(f"Pontos de referência carregados: {pointTrue.size().getInfo()}\n")

# task_total[0] += 1
checar_troca_conta()
# ─── Loop principal ───────────────────────────────────────────────────────────
for (tipo, filtro, colecao, num_class) in COMBINATIONS:
    tag = filtro or colecao or 'class'
    print(f"\n{'─'*55}")
    print(f"  tipo={tipo}  filtro/colecao={tag}  nc={num_class}")

    if tipo == 'filter':
        asset_path = param['asset_filters'][filtro]
    elif tipo == 'class':
        asset_path = param['assetCol']
    else:
        asset_path = param['colecoes_ant'][colecao]

    anoFinal = param['anoFinal']
    if tipo == 'colecao':
        anoFinal -= {'Map100': 1, 'Map90': 3, 'Map80': 4, 'Map71': 5}.get(colecao, 0)

    subfolder = (f"_{filtro}" if tipo == 'filter' else
                 '_class'    if tipo == 'class'   else
                 f"_{colecao}") + f"_nc{num_class}"

    classNew   = classNew_10 if num_class == 10 else classNew_7
    listBandas = ['classification_' + str(y) for y in range(param['anoInicial'], anoFinal + 1)]
    lsAllprop  = param['lsProp'] + ['CLASS_' + str(y) for y in range(param['anoInicial'], anoFinal + 1)]
    isImgCol   = (tipo in ('filter', 'class'))

    if isImgCol:
        try:
            hist     = ee.ImageCollection(asset_path).aggregate_histogram('version').getInfo()
            versions = sorted(int(float(v)) for v in hist.keys()) if hist else []
        except Exception as e:
            print(f"  ERRO ao ler histograma: {e}")
            continue
        if not versions:
            print("  sem versões disponíveis, pulando")
            continue
        imgsMaps = ee.ImageCollection(asset_path)
    else:
        versions = [None]

    for version in versions:
        print(f"  versão={version}")
        try:
            if isImgCol:
                mapFiltered = imgsMaps.filter(ee.Filter.eq('version', float(version)))
                size = mapFiltered.size().getInfo()
                if size == 0:
                    print(f"    → 0 imagens, pulando")
                    continue
                if filtro == 'correcoes':
                    ic_estab = (ee.ImageCollection(param['asset_filters']['estabilidade'])
                                .filter(ee.Filter.eq('version', version))
                                .filter(ee.Filter.inList('id_bacia',
                                    [b for b in nameBacias if b not in BACIAS_CORRECOES])))
                    mapFiltered = mapFiltered.merge(ic_estab)
                imgMosaic = mapFiltered.min()
            else:
                bioCaat   = ee.Image(param['asset_biomas_raster']).eq(5)
                imgMosaic = ee.Image(asset_path).byte().updateMask(bioCaat)

            processar_e_exportar(pointTrue, imgMosaic, listBandas, classNew,
                                  lsAllprop, subfolder, version)
        except Exception as e:
            print(f"    ERRO versão {version}: {e}")
            continue

print(f"\n{'='*55}")
print(f"CONCLUIDO — {task_total[0]} tasks submetidas")
