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
    ee.Initialize(project=projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

param = {
    'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Spatials_sieve',
    'input_asset':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Gap-fill',
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'last_year':   2025,
    'first_year':  2016,
    'step':        1,
    'num_classes': 7,
    'versionOut':  7,
    'versionInp':  7,
    # ── Parâmetros do filtro sieve ──────────────────────────────────────────────
    'native_scale':      10,     # resolução Sentinel-2 (m)
    'max_filter_pixels': 25,     # manchas com cc ≤ este valor são substituídas (25 px × 100 m² = 0,25 ha)
    'kernel_size':       9,      # raio do kernel da moda (pixels)
    'max_cc_size':       500,    # cap do connectedPixelCount (deve ser >> max_filter_pixels)
    'use_bridge_detect': True,   # preserva pixels "ponte" em estruturas lineares finas
    'excessions_class':  [33, 29, 25],  # classes nunca substituídas pelo filtro
    'erode_radius':      2,      # raio da erosão morfológica; kernel (2*r+1)×(2*r+1)
    'thin_cc_threshold': 50,     # cc mínimo para preservar estrutura fina sem interior
    # classes tratadas como uma mesma feição para CC, erosão e bridge detect
    # {15,21}: Pastagem ↔ Mosaico Agropec.  |  {4,12}: Savana ↔ Campestre
    'class_merge_groups': [[15, 21], [4, 12]],
    # ── Gerenciamento de tasks ──────────────────────────────────────────────────
    
}

lst_bands_years = ['classification_' + str(yy) for yy in range(param['first_year'], param['last_year'] + 1)]


def mode_spatial_filter(img_band, band_name):
    """
    Filtro espacial sieve com preservação de estruturas finas (erosão morfológica)
    e mescla de grupos de classes para cálculo de conectividade.

    Manchas com cc <= max_filter_pixels são substituídas pela moda da vizinhança,
    exceto: pixels ponte em estruturas lineares, estruturas finas longas
    (cc > thin_cc_threshold sem interior compacto) e classes de exceção.
    """
    native_scale       = param['native_scale']
    max_filter_pixels  = param['max_filter_pixels']
    kernel_size        = param['kernel_size']
    max_cc_size        = param['max_cc_size']
    use_bridge_detect  = param['use_bridge_detect']
    excessions_class   = param['excessions_class']
    erode_radius       = param['erode_radius']
    thin_cc_threshold  = param['thin_cc_threshold']
    class_merge_groups = param['class_merge_groups']

    projection      = img_band.projection()
    img_for_connect = img_band.reproject(crs=projection, scale=native_scale)

    # ── Mescla de classes para conectividade ─────────────────────────────────
    # Classes em cada grupo são tratadas como uma mesma feição para CC, erosão e
    # bridge detect. Evita filtrar fragmentos que fazem parte de manchas maiores
    # de classes ecologicamente equivalentes.
    # A imagem de saída mantém as classes originais (usa img_for_connect).
    img_merged = img_for_connect
    for group in class_merge_groups:
        target = group[0]
        for cls in group[1:]:
            img_merged = img_merged.where(img_merged.eq(cls), target)

    # ── Conectividade calculada sobre img_merged ──────────────────────────────
    # max_cc_size >> max_filter_pixels: estruturas finas longas retornam CC real,
    # não truncado. Garante que um rio de 200px retorne cc=200, não cc=max_filter_pixels.
    connect_1 = img_merged.connectedPixelCount(max_cc_size, True)   # 8-conn
    connect_2 = img_merged.connectedPixelCount(max_cc_size, False)  # 4-conn

    # ── Detecção de pixels "ponte" ────────────────────────────────────────────
    # Um pixel é ponte se tem vizinhos da mesma classe (grupo mesclado) em ao
    # menos um par de direções opostas: H, V, diagonal ↗↙, diagonal ↖↘.
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
        img_merged.eq(nb_p10).And(img_merged.eq(nb_n10))           # horizontal
        .Or(img_merged.eq(nb_p01).And(img_merged.eq(nb_n01)))       # vertical
        .Or(img_merged.eq(nb_p11).And(img_merged.eq(nb_n11)))       # diagonal ↗↙
        .Or(img_merged.eq(nb_n1p1).And(img_merged.eq(nb_p1n1)))     # diagonal ↖↘
    )
    not_bridge = is_bridge.Not() if use_bridge_detect else ee.Image.constant(1)

    # ── Erosão morfológica: detectar interior compacto ────────────────────────
    # Um pixel "sobrevive" se todos os vizinhos no kernel têm o mesmo valor mesclado.
    # Feições com largura < 2*erode_radius+1 não têm pixel sobrevivente (são finas).
    lmin     = img_merged.focal_min(erode_radius, 'square', 'pixels')
    lmax     = img_merged.focal_max(erode_radius, 'square', 'pixels')
    survived = lmin.eq(img_merged).And(lmax.eq(img_merged))

    # Dilata o interior de volta para marcar toda a mancha como compacta
    compact_region = (survived
        .reproject(crs=projection, scale=native_scale)
        .focal_max(erode_radius, 'square', 'pixels')
        .gt(0))

    # Estruturas finas: cc > thin_cc_threshold E sem interior compacto
    # (rios, florestas ciliares, corredores lineares)
    is_thin    = connect_1.gt(thin_cc_threshold).And(compact_region.Not())
    thin_layer = img_for_connect.updateMask(is_thin)

    # ── Imagem de moda da vizinhança (classes originais, escala nativa) ───────
    mode_img = img_for_connect.focal_mode(kernel_size, 'square', 'pixels')

    # ── Aplicação do filtro ───────────────────────────────────────────────────
    # Substitui apenas manchas com cc <= max_filter_pixels que não são pontes.
    # Manchas maiores nunca são modificadas (connect_1.lte(max_filter_pixels) = False).
    mode_all = mode_img.updateMask(connect_1.lte(max_filter_pixels).And(not_bridge))

    # Classe 21: 4-conn (mais restrito); connect_2 reflete grupo {15,21} mesclado
    mode_21 = mode_img.updateMask(
        img_for_connect.eq(21).And(connect_2.lte(max_filter_pixels)).And(not_bridge)
    )

    # Exceções: classes nunca substituídas (água, afloramento, solo exposto)
    exceptions_layer = img_for_connect.remap(excessions_class, excessions_class)

    # Composição: original → moda geral → moda cl21 → restaura finas → exceções
    filtered = (img_for_connect
        .blend(mode_all)
        .blend(mode_21)
        .blend(thin_layer)
        .blend(exceptions_layer))

    return filtered.rename(band_name)


def apply_sieve_filter(name_bacia):
    geomBacia    = (ee.FeatureCollection(param['asset_bacias_buffer'])
                        .filter(ee.Filter.eq('nunivotto4', name_bacia)))
    geomBacia    = geomBacia.map(lambda f: f.set('id_codigo', 1))
    bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    geomBacia    = geomBacia.geometry()

    ic = (ee.ImageCollection(param['input_asset'])
                .filter(ee.Filter.eq('version',   param['versionInp']))
                .filter(ee.Filter.eq('id_bacias', name_bacia)))
    n = ic.size().getInfo()
    print(f"  imagens carregadas para bacia {name_bacia}: {n}")

    imgClass = ic.first().updateMask(bacia_raster)
    print('  system:index:', imgClass.get('system:index').getInfo())

    band_images = []
    for yband_name in lst_bands_years:
        img_band = imgClass.select(yband_name)
        filtered = mode_spatial_filter(img_band, yband_name)
        band_images.append(filtered)

    class_output = ee.Image.cat(band_images)

    nameExp = f"filterSieve_BACIA_{name_bacia}_GTB_V{param['versionOut']}"
    class_output = (class_output
                    .updateMask(bacia_raster)
                    .select(lst_bands_years)
                    .set(
                        'version',          param['versionOut'],
                        'biome',            'CAATINGA',
                        'collection',       '4.0',
                        'id_bacias',        name_bacia,
                        'sensor',           'Sentinel',
                        'source',           'geodatin',
                        'model',            'GTB',
                        'step',             param['step'],
                        'num_class',        param['num_classes'],
                        'system:footprint', geomBacia,
                    ))
    processoExportar(class_output, nameExp, geomBacia)


def processoExportar(mapaRF, nomeDesc, geom_bacia):
    idasset = f"{param['output_asset']}/{nomeDesc}"
    optExp  = {
        'image':            mapaRF,
        'description':      nomeDesc,
        'assetId':          idasset,
        'region':           geom_bacia,
        'scale':            10,
        'maxPixels':        1e13,
        'pyramidingPolicy': {'.default': 'mode'},
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start()
    print("salvando ... " + nomeDesc + "..!")
    for k, v in dict(task.status()).items():
        print(f"  {k} : {v}")


#============================================================
#======================= EXECUÇÃO ===========================
#============================================================
listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614',
    '7616', '745', '7424', '773', '7612', '7613', '752',
    '7618', '7561', '755', '7617', '7564', '761111', '761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757', '771', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '7544', '7438',
    '763', '7591', '7592', '746', '7712', '7622', '765'
]

def verficar_bacias_inTask():
    """Retorna True enquanto o input (Gap-fill) ainda não tem todas as bacias. False = todas prontas."""
    imgCol_temp = (ee.ImageCollection(param['input_asset'])
                        .filter(ee.Filter.eq('version', param['versionInp'])))
    num_img = imgCol_temp.size().getInfo()
    print(f"  input: {num_img}/{len(listaNameBacias)} bacias prontas")
    return num_img < len(listaNameBacias)


# listaNameBacias = ['7617', '7564', '761111'] # teste rápido
# listaNameBacias = ['7671', '757', '7438', '763', '7622']

# False → aguarda input completo, submete Sieve tasks
# True  → pula submissão, verifica output (tasks já enviadas anteriormente)
knowMapSaved = False
listBacFalta = []

if not knowMapSaved:
    # Fase 1: aguardar o input (Gap-fill) ter todas as bacias
    while verficar_bacias_inTask():
        print(" .... esperar mais 5 minutos ... ")
        time.sleep(300)

    # Fase 2: submeter tasks do Sieve
    for cc, idbacia in enumerate(listaNameBacias):
        print(f"----- PROCESSING BACIA {idbacia} -------")
        apply_sieve_filter(idbacia)
else:
    # Verificar output (Spatials_sieve)
    for cc, idbacia in enumerate(listaNameBacias):
        try:
            imgtmp = (ee.ImageCollection(param['output_asset'])
                            .filter(ee.Filter.eq('version',   param['versionOut']))
                            .filter(ee.Filter.eq('id_bacias', idbacia))
                            .first())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}",
                  len(imgtmp.bandNames().getInfo()), "bandas ✅")
        except Exception:
            listBacFalta.append(idbacia)

    print("lista de bacias que faltam\n", listBacFalta)
    print("total", len(listBacFalta))
