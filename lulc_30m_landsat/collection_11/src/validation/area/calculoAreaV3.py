#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
SCRIPT DE CÁLCULO DE ÁREA POR BACIA — calculoAreaV3.py
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2

Estatísticas por: bacia (region), ano (year), versão (version), coleção.

Argumentos:
    --tipo       Obrigatório. Tipo de entrada:
                   filter  = filtro POS-CLASS (use --filtro para especificar qual)
                   class   = classificação direta (assetCol)
                   colecao = coleção anterior MapBiomas (use --colecao para especificar qual)
    --filtro     gap_fill | temporalN | temporalA | spatial_int | frequency | spatial_all
                 | spatial_Sieve | temporal_CC | estabilidade | correcoes | class_final
                 (obrigatório quando --tipo=filter)
    --colecao    Map71 | Map80 | Map90 | Map100
                 (obrigatório quando --tipo=colecao)
    --version    Versão da classificação/filtro  (default: 10)
    --num_class  Número de classes para estatísticas: 7 ou 10  (default: 10)
Exemplos:
    python calculoAreaV3.py --tipo filter  --filtro spatial_all  --version 10 --num_class 10
    python calculoAreaV3.py --tipo filter  --filtro temporalA    --version 10 --num_class 7
    python calculoAreaV3.py --tipo filter  --filtro temporal_CC  --version 5  --num_class 7
    python calculoAreaV3.py --tipo filter  --filtro frequency    --version 3  --num_class 10
    python calculoAreaV3.py --tipo class   --version 10 --num_class 10
    python calculoAreaV3.py --tipo colecao --colecao Map100 --num_class 7
'''

import ee
import os
import sys
import argparse
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[1])
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

# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description='Cálculo de área por bacia, ano, versão e coleção — MapBiomas Caatinga',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=(
        'Exemplos:\n'
        '  %(prog)s --tipo filter  --filtro spatial_all  --version 10 --num_class 10\n'
        '  %(prog)s --tipo filter  --filtro temporalA    --version 10 --num_class 7\n'
        '  %(prog)s --tipo filter  --filtro temporal_CC  --version 5  --num_class 7\n'
        '  %(prog)s --tipo filter  --filtro frequency    --version 3  --num_class 10\n'
        '  %(prog)s --tipo class   --version 10 --num_class 10\n'
        '  %(prog)s --tipo colecao --colecao Map100 --num_class 7\n'
    )
)
parser.add_argument(
    '--tipo', required=True,
    choices=['filter', 'class', 'colecao'],
    help=('"filter" = filtro POS-CLASS  |  '
          '"class" = classificação direta (assetCol)  |  '
          '"colecao" = coleção anterior (Map71/Map80/Map90/Map100)')
)
parser.add_argument(
    '--filtro',
    choices=[
        'gap_fill', 'spatial_Sieve', 'temporalA', 'frequency', 'temporal_CC', 'estabilidade', 'correcoes', 'class_final'
    ],
    help='Filtro POS-CLASS específico (obrigatório com --tipo filter).'
)
parser.add_argument(
    '--colecao',
    choices=['Map71', 'Map80', 'Map90', 'Map100'],
    help='Coleção anterior (obrigatório com --tipo colecao)'
)
parser.add_argument(
    '--version', type=int, default=10,
    help='Versão da classificação/filtro (default: 10)'
)
parser.add_argument(
    '--num_class', type=int, choices=[7, 10], default=10,
    help='Número de classes para as estatísticas: 7 ou 10 (default: 10)'
)
# parser.add_argument(
#     '--janela', type=int, choices=[3, 4, 5],
#     help='Janela temporal — obrigatório para --filtro temporalN ou temporalA'
# )
args = parser.parse_args()

# Validações cruzadas
if args.tipo == 'filter' and not args.filtro:
    parser.error('--filtro é obrigatório quando --tipo=filter')
if args.tipo == 'colecao' and not args.colecao:
    parser.error('--colecao é obrigatório quando --tipo=colecao')
# if args.filtro in ('temporalN', 'temporalA') and not args.janela:
#     parser.error('--janela é obrigatório para filtros temporalN e temporalA')

print(f"\n{'='*60}")
print(f"  tipo      : {args.tipo}")
print(f"  filtro    : {args.filtro or '-'}")
print(f"  colecao   : {args.colecao or '-'}")
print(f"  version   : {args.version}")
print(f"  num_class : {args.num_class}")
# print(f"  janela    : {args.janela or '-'}")
print(f"{'='*60}\n")

# ---------------------------------------------------------------------------
# Bacias e parâmetros fixos
# ---------------------------------------------------------------------------
nameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614',
    '7616', '745', '7424', '773', '7612', '7613', '765',
    '7618', '7561', '755', '7617', '7564', '761111','761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757', '771', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443','7544', '7438',
    '763', '7591', '7592', '7622', '746','7712', '752',
]
param = {
    'assetCol':    'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
    'asset_filters': {
        'gap_fill':    'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill',
        'temporalA':   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',
        'spatial_int': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_int',
        'frequency':   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency',
        'spatial_all': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_all',
        'spatial_Sieve': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_sieve',
        'temporal_CC' : 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalbyCC',
        'estabilidade': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/EstabilidadeCols',
        'correcoes':    'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/correcoes',
        'class_final':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/toExport',
    },
    'colecoes_ant': {
        'Map71':  'projects/mapbiomas-public/assets/brazil/lulc/collection7_1/mapbiomas_collection71_integration_v1',
        'Map80':  'projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1',
        'Map90':  'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'Map100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    },
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_bacias':        'projects/ee-solkancengine17/assets/shape/bacias_shp_caatinga_div_49_regions',
    'asset_biomas_raster': 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'assetBiomas':         'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'collection': '11.0',
    'biome':      'CAATINGA',
    'scale':      30,
    'year_inic':  1985,
    'year_end':   2025,
    'driverFolder': 'AREA-EXPORT-COL10',
    'changeAcount': False,
    'numeroTask':   0,
    'numeroLimit':  50,
    'conta': {
        '0': 'solkanGeodatin',
        '1': 'superconta'
    }
}

# ---------------------------------------------------------------------------
# Remapeamento de classes segundo --num_class
#
# classMapB : classes originais MapBiomas (entrada do remap)
# classNew_10: saída com 10 classes — mantém afloramento (29) distinto de (25)
# classNew_7 : saída com 7 classes  — une afloramento (29) → área não vegetada (25)
# ---------------------------------------------------------------------------
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

classNew  = classNew_10 if args.num_class == 10 else classNew_7
# classes esperadas na saída (documentação — não filtra o cálculo)
# num_class=10: {3,4,12,15,19,21,25,27,29,33,36} — requer fonte com esses códigos de entrada
# num_class=7 : {3,4,12,21,25,27,33}             — funciona mesmo com filtros de 7 classes
lsClasses = [3, 4, 12, 15, 19, 21, 25, 27, 29, 33, 36] if args.num_class == 10 else [3, 4, 12, 21, 25, 27, 33]
# ---------------------------------------------------------------------------
# Flags e asset derivados dos argumentos
# ---------------------------------------------------------------------------
isImgCol = (args.tipo in ('filter', 'class'))
isFilter = (args.tipo == 'filter')
version  = args.version

if args.tipo == 'filter':
    assetFilters = param['asset_filters'][args.filtro]
elif args.tipo == 'class':
    assetFilters = param['assetCol']
else:
    assetFilters = param['colecoes_ant'][args.colecao]

# Subfolder incluso no nome do CSV exportado
if args.tipo == 'filter':
    subfolder = f"_{args.filtro}"
elif args.tipo == 'class':
    subfolder = "_class"
else:
    subfolder = f"_{args.colecao}"
subfolder += f"_nc{args.num_class}"

print(f"asset selecionado  : {assetFilters}")
print(f"subfolder de saida : {subfolder}")

# ---------------------------------------------------------------------------
relatorios = open("relatorioTaskXContas.txt", 'a+')


def gerenciador(cont):
    #=====================================
    # gerenciador de contas para controlar
    # processos task no gee
    #=====================================
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)
    if str(cont) in numberofChange:
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project=projAccount)
            print('The Earth Engine package initialized successfully!')
        except ee.EEException:
            print('The Earth Engine package failed to initialize!')
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')
        tarefas = tasks(n=param['numeroTask'], return_list=True)
        for lin in tarefas:
            relatorios.write(str(lin) + '\n')
    elif cont > param['numeroLimit']:
        return 0
    cont += 1
    return cont


##############################################
###     Helper function
###    @param item
##############################################
def convert2featCollection(item):
    item = ee.Dictionary(item)
    return ee.Feature(ee.Geometry.Point([0, 0])).set(
        'classe', item.get('classe'),
        'area',   item.get('sum')
    )


#########################################################################
####     Calculate area crossing a cover map (deforestation, mapbiomas)
####     and a region map (states, biomes, municipalites)
####      @param image
####      @param geometry
#########################################################################
def calculateArea(image, pixelArea, geometry):
    pixelArea = pixelArea.addBands(image.rename('classe'))
    reducer = ee.Reducer.sum().group(1, 'classe')
    optRed = {
        'reducer':    reducer,
        'geometry':   geometry,
        'scale':      param['scale'],
        'bestEffort': True,
        'maxPixels':  1e13
    }
    areas = pixelArea.reduceRegion(**optRed)
    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    return ee.FeatureCollection(areas)


def iterandoXanoImCruda(imgMapp, limite):
    geomRecBacia = ee.FeatureCollection([ee.Feature(ee.Geometry(limite), {'id_codigo': 1})])
    maskRecBacia = geomRecBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    imgMapp    = imgMapp.updateMask(maskRecBacia)
    imgAreaRef = ee.Image.pixelArea().divide(10000).updateMask(maskRecBacia)

    yearEnd = param['year_end']
    if not isImgCol:
        # coleções anteriores têm cobertura até anos diferentes
        offset_map = {'Map100': 1, 'Map90': 2, 'Map80': 3, 'Map71': 4}
        yearEnd -= offset_map.get(args.colecao, 0)

    areaGeral = ee.FeatureCollection([])
    for year in range(param['year_inic'], yearEnd + 1):
        bandAct   = 'classification_' + str(year)
        # class_final já contém os valores originais (incluindo cl.49/50); não reclassificar
        if args.filtro == 'class_final':
            mapToCalc = imgMapp.select(bandAct)
        else:
            mapToCalc = imgMapp.select(bandAct).remap(classMapB, classNew)
        areaTemp  = calculateArea(mapToCalc.rename('classe'), imgAreaRef, limite)
        areaTemp  = areaTemp.map(lambda feat: feat.set('year', year))
        areaGeral = areaGeral.merge(areaTemp)
    return areaGeral


#exporta a feicao de area para o Drive
def processoExportar(areaFeat, nameT, ipos):
    optExp = {
        'collection':  areaFeat,
        'description': nameT,
        'folder':      param['driverFolder'],
    }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start()
    print(f"🔉 {ipos} salvando ... 📲  {nameT} ...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
lstBands    = ['classification_' + str(yy) for yy in range(1985, 2026)]
bioma250mil = (ee.FeatureCollection(param['assetBiomas'])
               .filter(ee.Filter.eq('Bioma', 'Caatinga'))
               .geometry())

knowImgcolg = False
account = 1
if param['changeAcount']:
    account = gerenciador(account)

numebacias = len(nameBacias)

if isImgCol:
    print("-------- processing isImgCol -----")
    imgsMaps = ee.ImageCollection(assetFilters)
    print('imgsMaps version histogram:', imgsMaps.aggregate_histogram('version').getInfo())

    # diagnóstico: mostra quais classes existem no asset para o primeiro ano
    # útil para verificar se --num_class 10 é compatível com o asset (requer códigos 15,19,36 na entrada)
    _first_img   = imgsMaps.first()
    _first_band  = 'classification_' + str(param['year_inic'])
    _hist_classes = (_first_img.select(_first_band)
                     .reduceRegion(ee.Reducer.frequencyHistogram(),
                                   scale=500, bestEffort=True, maxPixels=1e9)
                     .getInfo())
    print(f"🔍 classes no asset (band {_first_band}): {_hist_classes}")
    print("   → num_class=10 requer entrada com códigos {15,18,19,36,42-48,62} para produzir {15,19,36} na saída")

    if knowImgcolg:
        print(f"versions quantity = {imgsMaps.aggregate_histogram('version').getInfo()}")

    getid_bacia = (imgsMaps.first().get('id_bacias').getInfo() or
                   imgsMaps.first().get('id_bacia').getInfo())
    print(f"bacia property from first image: {getid_bacia}")

    # Para --tipo class, o assetCol é por bacia mas pode não ter 'id_bacias' na
    # primeira imagem — força o Branch A (mosaico .min()) que funciona para ambos.
    use_mosaic = bool(getid_bacia) or (args.tipo == 'class')

    if use_mosaic:
        mapClassMod = imgsMaps.filter(ee.Filter.eq('version', version))
        print("show size ImCol", mapClassMod.size().getInfo())
        print(f"########## 🔊 FILTRADO POR VERSÃO {version} | num_class={args.num_class} 🔊 ###############")
        sizeimgCol = mapClassMod.size().getInfo()
        print(f"🚨 número de mapas/bacias: {sizeimgCol}")

        nameCSV = (
            'areaXclasse_' + param['biome']
            + '_Col' + param['collection']
            + subfolder
            + '_vers_' + str(version)
        )
        print("iremos exportar com:", nameCSV)

        if sizeimgCol > 0:
            area_mapsGeral = ee.FeatureCollection([])
            for cc, nbacia in enumerate(nameBacias):
                print(f"# {cc+1}/{numebacias} +++++++++++++++ bacia {nbacia} ++++++++++")
                ftcol_bacias = (ee.FeatureCollection(param['asset_bacias'])
                                .filter(ee.Filter.eq('nunivotto4', nbacia))
                                .geometry())
                limitInt      = bioma250mil.intersection(ftcol_bacias)
                mapClassBacia = mapClassMod.min()
                areaM = iterandoXanoImCruda(mapClassBacia, limitInt)
                areaM = ee.FeatureCollection(areaM).map(
                    lambda feat: feat.set('id_bacia', nbacia)
                )
                area_mapsGeral = area_mapsGeral.merge(areaM)
            processoExportar(area_mapsGeral, nameCSV, cc)

    else:
        print(f"########## 🔊 FILTRADO POR VERSÃO {version} (sem id_bacias) 🔊 ###############")
        mapClassYY   = imgsMaps.filter(ee.Filter.eq('version', version))
        print("🚨 número de mapas:", imgsMaps.size().getInfo())
        immapClassYY = ee.Image().byte()
        for yy in range(param['year_inic'], param['year_end'] + 1):
            nmIm     = 'CAATINGA-' + str(yy) + '-' + str(version)
            nameBand = 'classification_' + str(yy)
            imTmp    = mapClassYY.filter(ee.Filter.eq('system:index', nmIm)).first().rename(nameBand)
            if yy == param['year_inic']:
                immapClassYY = imTmp.byte()
            else:
                immapClassYY = immapClassYY.addBands(imTmp.byte())

        nameCSV = (
            'areaXclasse_' + param['biome']
            + '_Col' + param['collection']
            + subfolder
            + '_vers_' + str(version)
        )
        for cc, nbacia in enumerate(nameBacias):
            ftcol_bacias = (ee.FeatureCollection(param['asset_bacias'])
                            .filter(ee.Filter.eq('nunivotto4', nbacia))
                            .geometry())
            limitInt  = bioma250mil.intersection(ftcol_bacias)
            areaM     = iterandoXanoImCruda(immapClassYY, limitInt)
            nameCSVBa = nameCSV + '_' + nbacia
            processoExportar(areaM, nameCSVBa, cc)

else:
    # Coleção anterior — asset Image único (não ImageCollection)
    print("########## 🔊 COLEÇÃO ANTERIOR (Image raster) ###############")
    print(f"  colecao  : {args.colecao}")
    print(f"  asset    : {assetFilters}")
    bioCaat        = ee.Image(param['asset_biomas_raster']).eq(5)
    mapClassRaster = ee.Image(assetFilters).byte().updateMask(bioCaat)
    print("bandas disponíveis:", mapClassRaster.bandNames().getInfo())

    nameCSV = (
        'areaXclasse_' + param['biome']
        + '_Col' + param['collection']
        + subfolder
        + '_vers_' + str(version)
    )
    area_mapsGeral = ee.FeatureCollection([])
    for cc, nbacia in enumerate(nameBacias):
        print(f"#{cc}/{numebacias} +++ BACIA {nbacia} +++")
        ftcol_bacias = (ee.FeatureCollection(param['asset_bacias'])
                        .filter(ee.Filter.eq('nunivotto4', nbacia))
                        .geometry())
        limitInt = bioma250mil.intersection(ftcol_bacias)
        areaM    = iterandoXanoImCruda(mapClassRaster, limitInt)
        areaM    = ee.FeatureCollection(areaM).map(
            lambda feat: feat.set('id_bacia', nbacia)
        )
        area_mapsGeral = area_mapsGeral.merge(areaM)

    nameCSV += '_remap'
    print(f"#{cc} exportando => {nameCSV}")
    processoExportar(area_mapsGeral, nameCSV, cc)
