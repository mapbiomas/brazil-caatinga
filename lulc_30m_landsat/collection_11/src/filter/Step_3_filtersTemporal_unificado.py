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


class processo_filterTemporal(object):
    """
    Filtro temporal unificado — janelas 3, 4 e 5 anos para classes naturais e
    antropogênicas. Detecta padrões T-!T-T, T-!T-!T-T e T-!T-!T-!T-T e corrige
    os pixels intermediários substituindo-os pelo valor do ano vizinho estável.

    Estratégia:
      - remap(classMapB, classNat) → flag 0/1 usado APENAS para detectar padrão
      - Substituição mantém a classe original do ano vizinho (não o flag)
      - Usa Python for-loops (client-side) → sem erros de índice server-side do GEE
    """

    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',
        'input_asset':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_sieve',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        # Mapeamento classes → flag (1=natural, 0=antropogênico)
        'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24,
                      25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
        'classNat':  [1, 1, 1, 1, 1,  1,  1,  1,  0,  0,  0,  0,  0,  0,  0,  0,
                       0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  0,  0],
        'last_year':   2025,
        'first_year':  1985,
        'num_classes': 7,
        'step':        1,
    }

    def __init__(self, name_bacia):
        self.id_bacias    = name_bacia
        self.versoutput   = 3
        self.versionInput = 3

        geomBacia = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                         .filter(ee.Filter.eq('nunivotto4', name_bacia)))
        geomBacia         = geomBacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia   = geomBacia.geometry()

        self.lst_band_names = [
            'classification_' + str(yy)
            for yy in range(self.options['first_year'], self.options['last_year'] + 1)
        ]

        self.img_class = (
            ee.ImageCollection(self.options['input_asset'])
                .filter(ee.Filter.eq('version',   self.versionInput))
                .filter(ee.Filter.eq('id_bacias', name_bacia))
                .filter(ee.Filter.eq('num_class', self.options['num_classes']))
                .first()
                .updateMask(self.bacia_raster)
        )
        print(f"  system:index: {self.img_class.get('system:index').getInfo()}")
        print(f"  bandas: {len(self.img_class.bandNames().getInfo())}")

    # ── Lógica do filtro ──────────────────────────────────────────────────────

    def _flag(self, img_band):
        """Converte uma banda de classe → flag binário (0=antrop, 1=natural)."""
        return img_band.remap(self.options['classMapB'], self.options['classNat'])

    def _mask_3(self, b0, b1, b2, target):
        """Detecta padrão: target - !target - target."""
        return (self._flag(b0).eq(target)
                .And(self._flag(b1).neq(target))
                .And(self._flag(b2).eq(target)))

    def _mask_4(self, b0, b1, b2, b3, target):
        """Detecta padrão: target - !target - !target - target."""
        return (self._flag(b0).eq(target)
                .And(self._flag(b1).neq(target))
                .And(self._flag(b2).neq(target))
                .And(self._flag(b3).eq(target)))

    def _mask_5(self, b0, b1, b2, b3, b4, target):
        """Detecta padrão: target - !target - !target - !target - target."""
        return (self._flag(b0).eq(target)
                .And(self._flag(b1).neq(target))
                .And(self._flag(b2).neq(target))
                .And(self._flag(b3).neq(target))
                .And(self._flag(b4).eq(target)))

    def apply_window(self, result, window_size, target_class):
        """
        Varre todas as posições da série e aplica a correção para um dado
        tamanho de janela e classe alvo.

        Substituição:
          win3: central ← b_anterior  (valor do ano estável imediatamente anterior)
          win4: b1 ← b0, b2 ← b3     (exterior esquerdo / exterior direito)
          win5: b1 ← b0, b2 ← b0, b3 ← b4

        Usa lista de bandas individuais em vez de addBands acumulado: evita
        grafo de ~228 níveis que excede o limite de recursão do serializador GEE.
        """
        n = len(self.lst_band_names)  # constante client-side (41)
        bands = [result.select(i) for i in range(n)]

        if window_size == 3:
            for i in range(1, n - 1):
                msk      = self._mask_3(bands[i-1], bands[i], bands[i+1], target_class)
                bands[i] = bands[i].where(msk, bands[i-1])

        elif window_size == 4:
            for i in range(0, n - 3):
                msk        = self._mask_4(bands[i], bands[i+1], bands[i+2], bands[i+3], target_class)
                bands[i+1] = bands[i+1].where(msk, bands[i])
                bands[i+2] = bands[i+2].where(msk, bands[i+3])

        elif window_size == 5:
            for i in range(0, n - 4):
                msk        = self._mask_5(bands[i], bands[i+1], bands[i+2], bands[i+3], bands[i+4], target_class)
                bands[i+1] = bands[i+1].where(msk, bands[i])
                bands[i+2] = bands[i+2].where(msk, bands[i])
                bands[i+3] = bands[i+3].where(msk, bands[i+4])

        return ee.Image.cat(bands).rename(self.lst_band_names)

    def applyTemporalFilter(self):
        """
        Aplica o filtro temporal unificado:
          - naturais (1): janelas 3, 4, 5
          - antropogênicas (0): janelas 3, 4, 5
        Exporta o resultado como asset GEE.
        """
        result = self.img_class

        for target_class in [1, 0]:
            tipo = 'natural' if target_class == 1 else 'antropogênico'
            for window_size in [3, 4, 5]:
                print(f"  aplicando janela {window_size} para classe {tipo} ({target_class})")
                result = self.apply_window(result, window_size, target_class)

        img_output = (result
                      .select(self.lst_band_names)
                      .updateMask(self.bacia_raster)
                      .set(
                          'version',          self.versoutput,
                          'id_bacias',        self.id_bacias,
                          'biome',            'CAATINGA',
                          'type_filter',      'temporal_unif',
                          'collection',       '11.0',
                          'janela',           5,
                          'sensor',           'Landsat',
                          'source',           'geodatin',
                          'model',            'GTB',
                          'step',             self.options['step'],
                          'num_class',        self.options['num_classes'],
                          'system:footprint', self.geom_bacia,
                      ))

        name_exp = (f"filterTP_BACIA_{self.id_bacias}_GTB"
                    f"_V{self.versoutput}_{self.options['num_classes']}cc")
        self.processoExportar(img_output, name_exp, self.geom_bacia)

    def processoExportar(self, mapaRF, nomeDesc, geom_bacia):
        idasset = os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
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
    'numeroLimit': 50,
    'conta': {
        '0':  'caatinga01',
        '6':  'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',
        '35': 'solkan1201',
        '42': 'solkanGeodatin',
        '49': 'superconta',
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
    '7691', '7754', '7581', '7625', '7584', '751', '7614',
    '7616', '745',  '7424', '773',  '7612', '7613', '752',
    '7618', '7561', '755',  '7617', '7564', '761111', '761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757',  '771',  '766',  '7746', '753',  '764',
    '7541', '7721', '772',  '7619', '7443', '7544', '7438',
    '763',  '7591', '7592', '746',  '7712', '7622', '765',
]
# listaNameBacias = ['7671', '757', '7438', '763', '7622']

changeAcount = False
knowMapSaved = False
cont         = 49

if changeAcount:
    cont = gerenciador(cont)

output_asset = processo_filterTemporal.options['output_asset']
listBacFalta = []

for cc, idbacia in enumerate(listaNameBacias):
    if knowMapSaved:
        try:
            imgtmp = (ee.ImageCollection(output_asset)
                            .filter(ee.Filter.eq('version',   1))
                            .filter(ee.Filter.eq('id_bacias', idbacia))
                            .first())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}",
                  len(imgtmp.bandNames().getInfo()), "bandas ✅")
        except:
            listBacFalta.append(idbacia)
    else:
        print(f"----- PROCESSING BACIA {idbacia} -------")
        proc = processo_filterTemporal(idbacia)
        proc.applyTemporalFilter()

if knowMapSaved:
    print("lista de bacias que faltam\n", listBacFalta)
    print("total", len(listBacFalta))
