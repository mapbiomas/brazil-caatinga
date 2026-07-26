#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
#
# Filtro temporal por classes prioritárias — janelas 3, 4 e 5 aplicadas no
# mesmo script. Detecta ilhas isoladas (T-!T-T, T-!T-!T-T, T-!T-!T-!T-T)
# para cada classe prioritária e corrige os pixels intermediários.
#
# Otimização anti-timeout: usa lista de bandas individuais (client-side) em vez
# de addBands acumulado, evitando grafo de ~200+ níveis que causa timeout no
# serializador GEE.
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


class processo_filterTemporal(object):
    """
    Filtro temporal por classes prioritárias — janelas 3, 4 e 5.

    Para cada classe em priority_classes e para cada janela [3, 4, 5],
    detecta ilhas temporais isoladas e substitui os pixels intermediários
    pelo valor da classe do ano vizinho estável.

    Detecção por valor direto de classe (não flag binário):
      win3: b[i-1]==C, b[i]!=C, b[i+1]==C  → b[i] ← b[i-1]
      win4: b[i]==C, b[i+1]!=C, b[i+2]!=C, b[i+3]==C
              → b[i+1] ← b[i],  b[i+2] ← b[i+3]
      win5: b[i]==C, b[i+1]!=C, b[i+2]!=C, b[i+3]!=C, b[i+4]==C
              → b[i+1] ← b[i],  b[i+2] ← b[i],  b[i+3] ← b[i+4]

    Otimização anti-timeout:
      Usa lista de bandas individuais (bands[i]) + ee.Image.cat() em vez de
      addBands acumulado, evitando grafo de ~200+ níveis no serializador GEE.
    """

    options = {
        'output_asset':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/TemporalbyCC',
        'input_asset':   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Frequency',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'last_year':  2025,
        'first_year': 2016,
        'step':       1,
        # Classes prioritárias a corrigir (valor direto GEE)
        'priority_classes': [3, 4, 21],
        # Janelas aplicadas em sequência, por classe
        'windows': [3, 4, 5],
    }

    def __init__(self, name_bacia):
        self.id_bacias    = name_bacia
        self.versoutput   = 7
        self.versionInput = 7

        geomBacia = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                         .filter(ee.Filter.eq('nunivotto4', name_bacia)))
        geomBacia         = geomBacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia   = geomBacia.geometry()

        self.lst_band_names = [
            'classification_' + str(yy)
            for yy in range(self.options['first_year'], self.options['last_year'] + 1)
        ]

        # Filtros diferem conforme o tipo de asset de entrada
        col = ee.ImageCollection(self.options['input_asset'])
        if 'Temporal' in self.options['input_asset']:
            col = (col.filter(ee.Filter.eq('id_bacia',  name_bacia))
                      .filter(ee.Filter.eq('version',   self.versionInput)))
        else:
            col = (col.filter(ee.Filter.eq('id_bacias', name_bacia))
                      .filter(ee.Filter.eq('version',   self.versionInput)))

        self.img_class = col.first().updateMask(self.bacia_raster)
        print(f"  system:index: {self.img_class.get('system:index').getInfo()}")
        print(f"  bandas: {len(self.img_class.bandNames().getInfo())}")

    # ── Núcleo do filtro ──────────────────────────────────────────────────────

    def apply_window_byclass(self, result, window_size, class_value):
        """
        Aplica filtro temporal para uma classe específica e tamanho de janela.

        Mantém lista de bandas individuais durante o loop para evitar que o
        grafo GEE cresça exponencialmente com addBands encadeados.
        """
        n = len(self.lst_band_names)
        bands = [result.select(i) for i in range(n)]

        if window_size == 3:
            for i in range(1, n - 1):
                msk = (bands[i-1].eq(class_value)
                       .And(bands[i].neq(class_value))
                       .And(bands[i+1].eq(class_value)))
                bands[i] = bands[i].where(msk, bands[i-1])

        elif window_size == 4:
            for i in range(0, n - 3):
                msk = (bands[i].eq(class_value)
                       .And(bands[i+1].neq(class_value))
                       .And(bands[i+2].neq(class_value))
                       .And(bands[i+3].eq(class_value)))
                bands[i+1] = bands[i+1].where(msk, bands[i])
                bands[i+2] = bands[i+2].where(msk, bands[i+3])

        elif window_size == 5:
            for i in range(0, n - 4):
                msk = (bands[i].eq(class_value)
                       .And(bands[i+1].neq(class_value))
                       .And(bands[i+2].neq(class_value))
                       .And(bands[i+3].neq(class_value))
                       .And(bands[i+4].eq(class_value)))
                bands[i+1] = bands[i+1].where(msk, bands[i])
                bands[i+2] = bands[i+2].where(msk, bands[i])
                bands[i+3] = bands[i+3].where(msk, bands[i+4])

        return ee.Image.cat(bands).rename(self.lst_band_names)

    # ── Orquestrador ─────────────────────────────────────────────────────────

    def applyTemporalFilter(self):
        """
        Para cada classe prioritária aplica janelas 3, 4 e 5 em sequência.
        Exporta o resultado final como asset GEE.
        """
        result = self.img_class

        for class_value in self.options['priority_classes']:
            for window_size in self.options['windows']:
                print(f"  aplicando janela {window_size} para classe {class_value}")
                result = self.apply_window_byclass(result, window_size, class_value)

        classes_str = '_'.join(str(c) for c in self.options['priority_classes'])
        img_output = (result
                      .select(self.lst_band_names)
                      .updateMask(self.bacia_raster)
                      .set(
                          'version',          self.versoutput,
                          'id_bacias',        self.id_bacias,
                          'biome',            'CAATINGA',
                          'type_filter',      'temporal_byclass',
                          'collection',       '4.0',
                          'janela',           5,
                          'sensor',           'Sentinel',
                          'source',           'geodatin',
                          'model',            'GTB',
                          'step',             self.options['step'],
                          'priority_classes', classes_str,
                          'system:footprint', self.geom_bacia,
                      ))

        name_exp = (f"filterTP_BACIA_{self.id_bacias}_GTB"
                    f"_J5_V{self.versoutput}_CC{classes_str}")
        self.processoExportar(img_output, name_exp, self.geom_bacia)

    def processoExportar(self, mapaRF, nomeDesc, geom_bacia):
        idasset = os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
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
        print(f"salvando ... {nomeDesc} ..!")
        for k, v in dict(task.status()).items():
            print(f"  {k} : {v}")

#============================================================
#======================= EXECUÇÃO ===========================
#============================================================


listaNameBacias = [
    '7691', '7754', '7581', '7625', '751', '7614',
    '752', '7616', '745', '7424', '773', '7612', '7613',
    '7618', '7561', '755', '7617', '7564', '761111', '761112',
    '7741', '7422', '76116', '7671', '7615', '7411',
    '7764', '757', '771', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438',
    '763', '7591', '7592', '7622', '746', '7712', '7584', '7761'
]


def verficar_bacias_inTask():
    """Retorna True enquanto o input (Frequency) ainda não tem todas as bacias."""
    versionInp = 7
    imgCol_temp = (ee.ImageCollection(processo_filterTemporal.options['input_asset'])
                        .filter(ee.Filter.eq('version', versionInp)))
    num_img = imgCol_temp.size().getInfo()
    print(f"  input: {num_img}/{len(listaNameBacias)} bacias prontas")
    return num_img < len(listaNameBacias)


# False → aguarda input completo, submete TemporalbyCC tasks
# True  → pula submissão, verifica output (tasks já enviadas anteriormente)
knowMapSaved = False
listBacFalta = []

if not knowMapSaved:
    # Fase 1: aguardar o input (Frequency) ter todas as bacias
    while verficar_bacias_inTask():
        print(" .... esperar mais 5 minutos ... ")
        time.sleep(300)

    # Fase 2: submeter tasks do TemporalbyCC
    for cc, idbacia in enumerate(listaNameBacias):
        print(f"----- PROCESSING BACIA {idbacia} -------")
        proc = processo_filterTemporal(idbacia)
        proc.applyTemporalFilter()
else:
    # Verificar output (TemporalbyCC)
    output_asset = processo_filterTemporal.options['output_asset']
    for cc, idbacia in enumerate(listaNameBacias):
        try:
            imgtmp = (ee.ImageCollection(output_asset)
                            .filter(ee.Filter.eq('version',   7))
                            .filter(ee.Filter.eq('id_bacias', idbacia))
                            .first())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}",
                  len(imgtmp.bandNames().getInfo()), "bandas ✅")
        except Exception:
            listBacFalta.append(idbacia)

    print("lista de bacias que faltam\n", listBacFalta)
    print("total", len(listBacFalta))
