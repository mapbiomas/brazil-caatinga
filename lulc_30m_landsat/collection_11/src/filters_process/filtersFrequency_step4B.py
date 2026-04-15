#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
FILTRO DE FREQUÊNCIA TEMPORAL — filtersFrequency_step4B.py
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2

Melhorias sobre filtersFrequency_step4A.py baseadas no notebook
apply_filters_frequency.ipynb:

  [1] Limiares dinâmicos por bacia — carregados de CSV gerado pelo notebook
      (apply_filters_frequency.ipynb → resultados_bacias_limiares.csv).
      Se a bacia não constar no CSV usa valores default configuráveis.

  [2] Filtro de frequência para classes ANTRÓPICAS [21, 22, 29] — além das
      naturais [3, 4, 12]. Cada grupo tem seus próprios limiares e mapa base.

  [3] Denominador dinâmico — stack.neq(0).reduce(ee.Reducer.count()) conta
      apenas os anos com pixel válido, não o total fixo de anos (/40).

  [4] Hierarquia explícita de classes — .where(m2.And(m1.Not()), ...) garante
      que cada classe só é atribuída se a de maior prioridade não cobriu o pixel.

  [5] Preservação com .unmask(banda) — se o mapa de frequência não atribuiu
      nenhuma classe dominante ao pixel, o valor original da banda é mantido.
      Substitui o .blend() anterior que não tratava naturais e antrópicas separadamente.

  [6] Verificação de bandas disponíveis — antes de montar a stack, filtra
      apenas as bandas que existem no asset, protegendo contra anos ausentes.

  [7] Máscara de grupo via remap inline — reclassifica o pixel do ano corrente
      diretamente em cada chamada para identificar se pertence ao grupo natural
      ou antrópico, capturando sub-classes (ex: class 5 → 3) corretamente.

Uso:
    python filtersFrequency_step4B.py
    python filtersFrequency_step4B.py [pos_inicio] [pos_fim]
'''

import ee
import os
import sys
import pandas as pd
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

# ---------------------------------------------------------------------------
# CSV com limiares ótimos gerado pelo notebook apply_filters_frequency.ipynb
# Colunas esperadas: bacia, l1_naturais, l2_naturais, l3_naturais,
#                            l1_antropicas, l2_antropicas, l3_antropicas
# ---------------------------------------------------------------------------
CSV_LIMIARES_PATH = os.path.join(os.path.dirname(__file__), 'aval_filters', 'aval_natural_antropic_xBacias.csv')

# Limiares default — usados quando a bacia não consta no CSV
# naturais:   l1=florestal(3), l2=savânica(4), l3=campestre(12)
# antropicas: l1=pastagem(21), l2=urbanizada(22), l3=afloramento(29)
LIMIAR_DEFAULT_NAT = {'l1': 0.70, 'l2': 0.80, 'l3': 0.60}
LIMIAR_DEFAULT_ANT = {'l1': 0.20, 'l2': 0.20, 'l3': 0.20}


def _carregar_limiares_csv(csv_path):
    '''Carrega limiares ótimos por bacia do CSV gerado pelo notebook.
    Retorna dict: { id_bacia: {'nat': {...}, 'ant': {...}} }
    '''
    if not os.path.exists(csv_path):
        print(f"[AVISO] CSV de limiares não encontrado: {csv_path}")
        print("        Usando limiares default para todas as bacias.")
        return {}
    df = pd.read_csv(csv_path)
    limiares = {}
    for _, row in df.iterrows():
        bacia = str(int(row['bacia']))
        limiares[bacia] = {
            'nat': {
                'l1': float(row['l1_naturais']),
                'l2': float(row['l2_naturais']),
                'l3': float(row['l3_naturais']),
            },
            'ant': {
                'l1': float(row['l1_antropicas']),
                'l2': float(row['l2_antropicas']),
                'l3': float(row['l3_antropicas']),
            },
        }
    print(f"[INFO] {len(limiares)} bacias carregadas do CSV de limiares.")
    return limiares


# ===========================================================================
class processo_filterFrequence(object):

    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency',
        'input_asset':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',

        # Reclassificação: agrupa sub-classes nas classes principais usadas no filtro
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 19, 19, 19, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 25],

        # Grupos de classes para o filtro de frequência
        # [MELHORIA 2] antrópicas agora também recebem filtro de frequência
        'naturais':   [3, 4, 12],    # florestal, savânica, campestre
        'antropicas': [19,21,25,29,36],  # pastagem/agricultura, área urbanizada, afloramento rochoso
        'janela_input': 5,
        'versionInput': 1,
        'num_classes':  7,   # 7, 10
        'last_year':    2025,
        'first_year':   1985,
    }

    def __init__(self, nameBacia, dict_limiares=None):
        self.id_bacias   = nameBacia
        self.versoutput  = 1
        self.versinput   = self.options['versionInput']  # [BUGFIX] era self.versionInput (I maiúsculo)
        janela           = self.options['janela_input']

        if self.options['num_classes'] == 7:
            self.options['antropicas'] = [21,25,29]
        # --- Geometria da bacia ---
        fc_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
            ee.Filter.eq('nunivotto4', nameBacia))
        geomBacia = fc_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia   = fc_bacia.geometry()

        # --- [MELHORIA 1] Limiares: CSV ótimo ou default ---
        if dict_limiares and nameBacia in dict_limiares:
            self.limiares_nat = dict_limiares[nameBacia]['nat']
            self.limiares_ant = dict_limiares[nameBacia]['ant']
            print(f"  [CSV]     nat={self.limiares_nat} | ant={self.limiares_ant}")
        else:
            self.limiares_nat = LIMIAR_DEFAULT_NAT.copy()
            self.limiares_ant = LIMIAR_DEFAULT_ANT.copy()
            print(f"  [DEFAULT] nat={self.limiares_nat} | ant={self.limiares_ant}")

        # --- Carrega imagem de entrada ---
        imgCol = (ee.ImageCollection(self.options['input_asset'])
                    .filter(ee.Filter.eq('version',   self.versinput))
                    .filter(ee.Filter.eq('num_class', self.options['num_classes']))
                    .filter(ee.Filter.eq('id_bacias', nameBacia)))
        if janela > 0:
            imgCol = imgCol.filter(ee.Filter.eq('janela', janela))
        self.imgClass = imgCol.first()

        # --- [MELHORIA 6] Verifica bandas disponíveis ---
        bandas_disponiveis = self.imgClass.bandNames().getInfo()
        todas_bandas = ['classification_' + str(yy)
                        for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.lstbandNames = [b for b in todas_bandas if b in bandas_disponiveis]
        self.years        = [int(b.split('_')[1]) for b in self.lstbandNames]
        print(f"  [INFO] {len(self.lstbandNames)} anos disponíveis: {self.years[0]}–{self.years[-1]}")

        # Projeção base (usada em setDefaultProjection por ano)
        self.proj = self.imgClass.select(self.lstbandNames[0]).projection()

        # --- Constrói mapas de frequência ---
        self._build_vegetation_map()   # naturais  → self.vegetation_map
        self._build_antrop_map()        # antrópicas → self.antrop_map

    # -----------------------------------------------------------------------
    # [MELHORIA 2 + 3 + 4] MAPA BASE NATURAL [3, 4, 12]
    # -----------------------------------------------------------------------
    def _build_freq_map(self, classes, limiares):
        '''Calcula mapa de classe dominante por frequência relativa.

        Args:
            classes  : lista de 3 classes em ordem de prioridade (maior → menor)
            limiares : dict com 'l1', 'l2', 'l3' (limiares relativos 0–1)

        Returns:
            ee.Image: mapa com valor = classe dominante (mascarado onde nenhuma domina)
        '''
        # Stack: apenas anos em que o pixel pertence ao grupo
        def reclass(b):
            return self.imgClass.select(b).remap(
                self.options['classMapB'], self.options['classNew'])

        stack = ee.ImageCollection([
            reclass(b)
                .updateMask(reclass(b).remap(classes, [1] * len(classes), 0).eq(1))
                .rename(b)
            for b in self.lstbandNames
        ]).toBands()

        # [MELHORIA 3] Denominador dinâmico: conta só pixels válidos (≠ 0)
        freqTot = stack.neq(0).reduce(ee.Reducer.count())
        freqs   = {c: stack.eq(c).reduce(ee.Reducer.sum()) for c in classes}

        # Proporções por classe
        prop = {c: freqs[c].divide(freqTot) for c in classes}

        # [MELHORIA 4] Hierarquia explícita: c1 > c2 > ... > cN (N classes)
        # limiares['l1'], ['l2'], ... ; para classes extras usa o último limiar disponível
        limiar_fallback = limiares.get(f'l{len(limiares)}', 0.20)
        masks = []
        mapa  = ee.Image(0)
        for i, c in enumerate(classes):
            li = limiares.get(f'l{i + 1}', limiar_fallback)
            mi = prop[c].gte(li)
            condition = mi
            for prev_m in masks:
                condition = condition.And(prev_m.Not())
            mapa = mapa.where(condition, c)
            masks.append(mi)

        return mapa.updateMask(mapa.gt(0))

    def _build_vegetation_map(self):
        '''Mapa de classe natural dominante — florestal(3) > savânica(4) > campestre(12).'''
        self.vegetation_map = self._build_freq_map(
            classes  = self.options['naturais'],   # [3, 4, 12]
            limiares = self.limiares_nat
        )

    def _build_antrop_map(self):
        '''Mapa de classe antrópica dominante — pastagem(21) > urbanizada(22) > afloramento(29).'''
        self.antrop_map = self._build_freq_map(
            classes  = self.options['antropicas'],  # [21, 22, 29]
            limiares = self.limiares_ant
        )

    # -----------------------------------------------------------------------
    # [MELHORIA 5 + 7] APLICA O FILTRO ANO A ANO
    # -----------------------------------------------------------------------
    def applyStabilityNaturalClass_byYear(self):
        '''Para cada ano:
          - pixels naturais   → substituídos pela classe dominante do vegetation_map
          - pixels antrópicos → substituídos pela classe dominante do antrop_map
          - .unmask(banda) garante que pixels sem classe dominante mantêm valor original
          - remap inline identifica o grupo do pixel, capturando sub-classes corretamente
        '''
        classes_nat = self.options['naturais']
        classes_ant = self.options['antropicas']
        rasterFinal = ee.Image().byte()

        for bandYY in self.lstbandNames:
            banda_orig = self.imgClass.select(bandYY)    # original (pode ter sub-classes)
            banda_recl = banda_orig.remap(self.options['classMapB'], self.options['classNew'])

            # [MELHORIA 7] Máscara via imgReclass — captura sub-classes no grupo
            mask_n = banda_recl.remap(classes_nat, [1] * len(classes_nat), 0).eq(1)
            mask_a = banda_recl.remap(classes_ant, [1] * len(classes_ant), 0).eq(1)

            # [MELHORIA 5] .unmask(banda_orig): se freq_map não atribuiu classe → mantém original
            corrigido = (banda_orig
                .where(mask_n, self.vegetation_map.unmask(banda_orig))
                .where(mask_a, self.antrop_map.unmask(banda_orig))
                .rename(bandYY)
                .setDefaultProjection(self.proj))

            rasterFinal = rasterFinal.addBands(corrigido)

        rasterFinal = (rasterFinal
            .select(self.lstbandNames)
            .updateMask(self.bacia_raster)
            .set(
                'version',     int(self.versoutput),
                'biome',       'CAATINGA',
                'type_filter', 'frequence',
                'from',        'TemporalAnt',
                'collection',  '11.0',
                'model',       'GTB',
                'id_bacias',   self.id_bacias,
                'sensor',      'Landsat',
                'num_class',   self.options['num_classes'],
                'system:footprint', self.geom_bacia,
            ))

        name_toexport = (f"filterFQ_BACIA_{self.id_bacias}_GTB"
                         f"_V{self.versoutput}_{self.options['num_classes']}cc")
        self.processoExportar(rasterFinal, name_toexport)

    # -----------------------------------------------------------------------
    def processoExportar(self, mapaRF, nomeDesc):
        idasset = os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image':           mapaRF,
            'description':     nomeDesc,
            'assetId':         idasset,
            'region':          self.geom_bacia,
            'scale':           30,
            'maxPixels':       1e13,
            'pyramidingPolicy': {'.default': 'mode'},
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start()
        print("salvando ... " + nomeDesc + "..!")
        for keys, vals in dict(task.status()).items():
            print(f"  {keys} : {vals}")


# ===========================================================================
# GERENCIADOR DE CONTAS
# ===========================================================================
param = {
    'numeroTask':  6,
    'numeroLimit': 20,
    'conta': {
        '0':  'caatinga01',
        '2':  'caatinga02',
        '4':  'caatinga03',
        '6':  'caatinga04',
        '8':  'caatinga05',
        '10': 'solkan1201',
        '12': 'solkanGeodatin',
        '14': 'superconta',
    }
}
relatorios = open("relatorioTaskXContas.txt", 'a+')


def gerenciador(cont):
    numberofChange = list(param['conta'].keys())
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


# ===========================================================================
# LISTA DE BACIAS (col11 — 49 bacias)
# ===========================================================================
listaNameBacias = [
    '765', '7544', '7541',  '746', '7591', '7592', '7411',
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751',     
    '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752'
]

# ===========================================================================
# EXECUÇÃO PRINCIPAL
# ===========================================================================
# Fatiamento via CLI: python filtersFrequency_step4B.py [pos_inicio] [pos_fim]
pos_inicio = int(sys.argv[1]) if len(sys.argv) > 1 else 0
pos_fim    = int(sys.argv[2]) if len(sys.argv) > 2 else len(listaNameBacias)

dict_limiares = _carregar_limiares_csv(CSV_LIMIARES_PATH)

output_asset = processo_filterFrequence.options['output_asset']
versoutput   = 1   # deve coincidir com self.versoutput da classe
num_classes  = processo_filterFrequence.options['num_classes']

# --- 1. Verifica quais bacias já foram exportadas ---
print("\n[INFO] Verificando bacias já processadas no asset...")
bacias_ok    = set()
bacias_falta = []

for idbacia in listaNameBacias[pos_inicio:pos_fim]:
    try:
        col = (ee.ImageCollection(output_asset)
                 .filter(ee.Filter.eq('id_bacias',  idbacia))
                 .filter(ee.Filter.eq('version',    versoutput))
                 .filter(ee.Filter.eq('num_class',  num_classes)))
        if col.size().getInfo() > 0:
            bacias_ok.add(idbacia)
            print(f"  [OK]    bacia {idbacia}")
        else:
            bacias_falta.append(idbacia)
            print(f"  [FALTA] bacia {idbacia}")
    except Exception as exc:
        bacias_falta.append(idbacia)
        print(f"  [ERRO]  bacia {idbacia}: {exc}")

print(f"\n[RESUMO] {len(bacias_ok)} já processadas | {len(bacias_falta)} a processar\n")

# --- 2. Processa apenas as bacias que faltam ---
for cc, idbacia in enumerate(bacias_falta):
    print(f"--------- #{cc + 1}/{len(bacias_falta)} PROCESSANDO BACIA {idbacia} ---------")
    proc = processo_filterFrequence(idbacia, dict_limiares=dict_limiares)
    proc.applyStabilityNaturalClass_byYear()

print("\n[FIM] Todas as bacias pendentes foram submetidas.")
