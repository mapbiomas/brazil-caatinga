#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
SCRIPT DE FILTRO — Camada de Rios Finos
Produzido por Geodatin - Dados e Geoinformação
DISTRIBUÍDO COM GPLv2

Detecta corpos de coberturas finas como rios  e solo exposto (classe 33 e classe 25) 
    em toda a série temporal 1985-2025 por bacia,
utilizando morfologia matemática (abertura: erosão 5×5 → dilatação 5×5):

  Condições para "rio fino":
    1. patch de água com > 30 pixels conectados  (objeto real, não ruído)
    2. desaparece após abertura morfológica 5×5   (é fino, não largo)

A camada resultante é a UNIÃO de todos os anos (rio fino em qualquer ano).

Anos estáveis: anos onde a área total de água ≥ média − σ da série.
  → Extraídos de: dados/areasCol11/areaXclasse_CAATINGA_Col11.0_Map100_nc7_vers_10_remap.csv
  → Salvo como propriedade `anos_estaveis` no asset de saída

Saída: imagem binária por bacia (1 = rio fino) em:
  projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/layer_rios_finos
'''

import ee
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
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


# ─── Anos estáveis: área de água ≥ média − σ ─────────────────────────────────
_CSV_AREAS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '../dados/areasCol11/areaXclasse_CAATINGA_Col11.0_Map100_nc7_vers_10_remap.csv'
)
_df        = pd.read_csv(_CSV_AREAS)
_agua_ano  = _df[_df['classe'] == 33].groupby('year')['area'].sum()
_mean_agua = _agua_ano.mean()
_std_agua  = _agua_ano.std()
_threshold = _mean_agua - _std_agua

ANOS_ESTAVEIS = sorted(_agua_ano[_agua_ano >= _threshold].index.tolist())

print(f"threshold água: {_threshold:.0f} ha  (média={_mean_agua:.0f}, σ={_std_agua:.0f})")
print(f"anos estáveis ({len(ANOS_ESTAVEIS)}): {ANOS_ESTAVEIS}")
# 32 anos: 1985-2000, 2002-2012, 2020-2024
# excluídos (seca): 2001, 2013-2019, 2025
# ─────────────────────────────────────────────────────────────────────────────


class processo_filterCoberturasFinas(object):
    """
    Gera camada de rios finos por bacia (imagem binária, união de todos os anos).

    Algoritmo:
      Para cada ano da série:
        1. Extrai pixels de água (classe 33)
        2. connected = connectedPixelCount → rios reais têm > min_connected px
        3. Abertura morfológica: erode(5×5) → dilate(5×5)
        4. thin = água AND real (>30px) AND some após abertura (é fino)
      União temporal (max) de todos os anos → máscara binária única.

    Anti-timeout: usa lista de bandas individuais + ee.Image.cat() em vez de
    addBands acumulado. Profundidade do grafo: ~8 níveis por banda, 2 níveis
    para cat+reduce → não escala quadraticamente.
    """

    options = {
        # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/layer_rios_finos',
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/layer_coberturas_finas',
        'input_asset':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/EstabilidadeCols',
        'asset_bacias': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'first_year':    1985,
        'last_year':     2025,
        'step':          1,
        'classes_finas':  [21,25], # 33,
        'erode_radius':  1,    # kernel 3×3: radius=2 → 2*2+1=3 px de lado
        'dilate_radius': 3,    # kernel 7×7: radius=4 → 2*4+1=7 px de lado
        'min_connected': 15,   # patches com > 15 px conectados = objeto real
    }

    clase_name = 'rios_finos'   

    def __init__(self, name_bacia):
        self.id_bacias     = name_bacia
        self.versoutput    = 1
        self.version_input = 4

        geomBacia = (ee.FeatureCollection(self.options['asset_bacias'])
                         .filter(ee.Filter.eq('nunivotto4', name_bacia)))
        geomBacia         = geomBacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia   = geomBacia.geometry()

        self.lst_band_names = [
            'classification_' + str(yy)
            for yy in range(self.options['first_year'], self.options['last_year'] + 1)
        ]

        col = (ee.ImageCollection(self.options['input_asset'])
                  .filter(ee.Filter.eq('id_bacia',  name_bacia))
                  .filter(ee.Filter.eq('version',   self.version_input)))
        self.img_class = col.first().updateMask(self.bacia_raster)
        print(f"  system:index: {self.img_class.get('system:index').getInfo()}")
        print(f"  bandas: {len(self.img_class.bandNames().getInfo())}")

    # ── Detecção de rios finos ────────────────────────────────────────────────

    def _detect_thin_coberturas(self):
        """
        Detecta rios finos em cada ano e retorna a união como imagem binária.

        Algoritmo por banda (ano):
          is_water  : pixels de água (classe 33)
          is_soil_expost : pixels de solo exposto (classe 25)
          eroded    : focal_min 3×3 — remove estruturas finas e bordas
          dilated   : focal_max 7x7 sobre eroded — re-expande núcleos sobreviventes
                      além do tamanho original (7 > 3), cobrindo toda a borda
          thin_raw  : is_water AND NOT dilated
                      → corpos largos: núcleo sobrevive erosão e cobre tudo com
                        dilatação maior; rios finos: somem na erosão, dilated=0
          thin      : thin_raw AND connectedPixelCount > min_connected
                      → descarta ruído isolado, mantém rios conectados reais

        União temporal: reduce(max) sobre todos os anos → 1 se detectado
        em qualquer ano da série.
        """
        erode_r  = self.options['erode_radius']
        dilate_r = self.options['dilate_radius']
        min_c    = self.options['min_connected']
        thin_cc       = self.options['class_fina']
        thin_bands = []
        if thin_cc == 25:
            self.clase_name = 'solos_exp_finos'

        for band_name in self.lst_band_names:
            classif  = self.img_class.select(band_name)
            is_water = classif.eq(thin_cc)

            # Abertura assimétrica: erode 5×5, dilate 9×9
            eroded  = is_water.focal_min(radius=erode_r,  kernelType='square', units='pixels')
            dilated = eroded.focal_max(  radius=dilate_r, kernelType='square', units='pixels')

            # Diferença: era água mas não coberto pela re-expansão → rio fino
            thin_raw = is_water.And(dilated.Not())

            # Mantém só patches com > min_c pixels conectados
            thin = thin_raw.And(
                thin_raw.connectedPixelCount(min_c + 1, True).gt(min_c)
            )
            thin_bands.append(thin)

        # União temporal: rio fino em pelo menos 1 ano da série
        rios_finos = (ee.Image.cat(thin_bands)
                        .reduce(ee.Reducer.max())
                        .rename(self.clase_name))
        return rios_finos

    # ── Orquestrador ─────────────────────────────────────────────────────────

    def applyCoberturasFinasFilters(self):
        """
        Detecta rios finos, aplica máscara da bacia e exporta.

        Propriedades do asset de saída:
          anos_estaveis     : anos (CSV) onde área água ≥ média−σ (str CSV)
          n_anos_estaveis   : contagem
          threshold_agua_ha : limite usado (inteiro, ha)
        """
        rios_finos = self._detect_thin_coberturas()
        rios_finos = rios_finos.updateMask(self.bacia_raster).selfMask().toByte()

        anos_str   = ','.join(str(y) for y in ANOS_ESTAVEIS)
        img_output = rios_finos.set(
            'version',           self.versoutput,
            'id_bacia',          self.id_bacias,
            'biome',             'CAATINGA',
            'type_filter',       self.clase_name,
            'collection',        '11.0',
            'sensor',            'Landsat',
            'source',            'geodatin',
            'model',             'GTB',
            'step',              self.options['step'],
            'anos_estaveis',     anos_str,
            'n_anos_estaveis',   len(ANOS_ESTAVEIS),
            'threshold_agua_ha', round(_threshold),
            'erode_radius',      self.options['erode_radius'],
            'min_connected',     self.options['min_connected'],
            'system:footprint',  self.geom_bacia,
        )

        name_exp = f"riosFinos_BACIA_{self.id_bacias}_V{self.versoutput}"
        self.processoExportar(img_output, name_exp, self.geom_bacia)

    def processoExportar(self, mapaRF, nomeDesc, geom_bacia):
        idasset = os.path.join(self.options['output_asset'], nomeDesc)
        optExp  = {
            'image':            mapaRF,
            'description':      nomeDesc,
            'assetId':          idasset,
            'region':           geom_bacia,
            'scale':            30,
            'maxPixels':        1e13,
            'pyramidingPolicy': {'.default': 'mode'},
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start()
        print(f"salvando ... {nomeDesc} ..!")
        for k, v in dict(task.status()).items():
            print(f"  {k} : {v}")


# ─── Parâmetros de gerenciamento ──────────────────────────────────────────────
param = {
    'numeroTask':  6,
    'numeroLimit': 16,
    'changeConta': False,
    'conta': {
        '0':  'caatinga01',
        '4':  'caatinga02',
        '6':  'caatinga03',
        '8':  'caatinga04',
        '10': 'caatinga05',
        '12': 'solkan1201',
        '14': 'solkanGeodatin',
        '16': 'superconta',
    }
}

relatorios = open("relatorioTaskXContas.txt", 'a+')

#============================================================
#======================= EXECUÇÃO ===========================
#============================================================
def gerenciador(cont):
    numberofChange = list(param['conta'].keys())
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


listaNameBacias = [
    '7691', '7754', '7581', '7625', '751', '7614',
    '752', '7616', '745', '7424', '773', '7612', '7613',
    '7618', '7561', '755', '7617', '7564', '761111', '761112',
    '7741', '7422', '76116', '7671', '7615', '7411',
    '7764', '757', '771', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438',
    '763', '7591', '7592', '7622', '746', '7712', '7584', '7761'
]

changeAcount = False
knowMapSaved = False
cont = 16

if changeAcount:
    cont = gerenciador(cont)

output_asset = processo_filterCoberturasFinas.options['output_asset']
listBacFalta = []

for cc, idbacia in enumerate(listaNameBacias[:]):
    if knowMapSaved:
        try:
            imgtmp = (ee.ImageCollection(output_asset)
                            .filter(ee.Filter.eq('version',  1))
                            .filter(ee.Filter.eq('id_bacia', idbacia))
                            .first())
            print(f" > {cc} loading {imgtmp.get('system:index').getInfo()} coberturas_finas OK")
        except:
            listBacFalta.append(idbacia)
    else:
        print(f"----- PROCESSING BACIA {idbacia} -------")
        proc = processo_filterCoberturasFinas(idbacia)
        proc.applyCoberturasFinasFilters()

if knowMapSaved:
    print("lista de bacias que faltam\n", listBacFalta)
    print("total", len(listBacFalta))
