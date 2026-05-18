#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
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
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

class processo_filterAvaliationNatAnt(object):

    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency',
        'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',
        # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalV3',
        # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill',
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        "asset_points_reference": 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col4_points_w_edge_and_edited_v1',
        'classMapB':     [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
        'classNew':      [3, 4, 3, 3, 12, 12, 15, 19, 19, 19, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 25],
        # 'classNew':    [3, 4, 3, 3, 12, 12, 21, 21, 21, 21, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21,  4, 12, 21, 25],
        'classNat':      [1, 1, 1, 1,  1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  1,  1,  0,  0],  
        'versionInput': 1,
        'janela_input': 5,
        'num_classes': 10,  # 7, 10   
        'last_year' : 2024,
        'first_year': 1985
    }


    naturais = [3, 4, 12]
    antropicas = [21, 22, 29]
    anos = list(range(1985, 2025, 5))
    limiares = [0.2, 0.4, 0.6, 0.8]

    classeDictNaturais = {
        'FORMAÇÃO FLORESTAL': 3,
        'FORMAÇÃO SAVÂNICA': 4,
        'FORMAÇÃO CAMPESTRE': 12
    }

    classeDictAntropicas = {
        'PASTAGEM': 21, 'AGRICULTURA': 21, 'LAVOURA TEMPORÁRIA': 21, 'SOJA': 21,
        'CANA': 21, 'ARROZ': 21, 'ALGODÃO': 21, 'OUTRAS LAVOURAS TEMPORÁRIAS': 21,
        'LAVOURA PERENE': 21, 'CAFÉ': 21, 'CITRUS': 21, 'DENDÊ': 21,
        'OUTRAS LAVOURAS PERENES': 21,  'MOSAICO DE USOS': 21,
        'PRAIA, DUNA E AREAL': 22, 'PRAIA E DUNA': 22, 'ÁREA URBANIZADA': 22,
        'VEGETAÇÃO URBANA': 22, 'INFRAESTRUTURA URBANA': 22, 'MINERAÇÃO': 22,
        'OUTRAS ÁREAS NÃO VEGETADAS': 22, 'OUTRA ÁREA NÃO VEGETADA': 22,
        'APICUM': 22, 'AFLORAMENTO ROCHOSO': 29
    }

    def __init__(self, nameBacia):
        self.id_bacias = nameBacia
        self.versionInput = 1
        self.step = 1
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer']).filter(
                                                   ee.Filter.eq('nunivotto4', nameBacia))  
        geomBacia = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)            
        self.geom_bacia = self.geom_bacia.geometry()     


        self.imgClass =(ee.ImageCollection(self.options['input_asset'])
                                    .filter(ee.Filter.eq('version', self.versionInput))
                                    .filter(ee.Filter.eq('num_class', self.options['num_classes']))
                                    # só o Gap-fill tem id_bacia o resto tem id_bacias
                                    .filter(ee.Filter.eq('janela',  self.options['janela_input']))
                                    .filter(ee.Filter.eq('id_bacias', nameBacia))                 
                                    # .first()
                        )        
        # print(" total of  image class ", self.imgClass.size().getInfo())
        self.imgClass = self.imgClass.first()
        self.proj = self.imgClass.select('classification_2015').projection()

        # print("numero de bandas ", self.imgClass.bandNames().getInfo())
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]
        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]

        self.pontos_reference = (ee.FeatureCollection(self.options['asset_points_reference'])
                                        .filterBounds(self.geom_bacia))


    def avaliar_combo(self, classes, classe_dict, label, ano):
        limiares = [0.2, 0.4, 0.6, 0.8]

        classe_keys = list(classe_dict.keys())
        dict_js = ee.Dictionary(classe_dict)

        pontos_valid = (self.pontos_reference
                            .filter(ee.Filter.inList(f'CLASS_{ano}', classe_keys))
                            .map(lambda f: f.set('ref', dict_js.get(f.get(f'CLASS_{ano}'))))
                    )
        # Lista de bandas disponíveis no asset
        bandas_disponiveis = self.imgClass.bandNames()

        # Gera lista de bandas válidas disponíveis
        bandas = ['classification_' + str(a) for a in range(1985, 2025)]
        bandas_validas = [b for b in bandas if bandas_disponiveis.contains(b).getInfo()]

        stack = ee.ImageCollection([
            self.imgClass.select(b).updateMask(self.imgClass.select(b).remap(classes, [1]*len(classes)).eq(1)).rename(b)
            for b in bandas_validas
        ]).toBands()

        freqs = {c: stack.eq(c).reduce(ee.Reducer.sum()) for c in classes}
        freqTot = stack.neq(0).reduce(ee.Reducer.count())

        combinacoes = [[l1, l2, l3] for l1 in limiares for l2 in limiares for l3 in limiares]
        melhores = {'acc': -1, 'l1': None, 'l2': None, 'l3': None}

        for lim in combinacoes:
            l1, l2, l3 = lim
            m1 = freqs[classes[0]].divide(freqTot).gte(l1)
            m2 = freqs[classes[1]].divide(freqTot).gte(l2)
            m3 = freqs[classes[2]].divide(freqTot).gte(l3)

            novaClasse = ee.Image(0).where(m1, classes[0])\
                .where(m2.And(m1.Not()), classes[1])\
                .where(m3.And(m1.Not()).And(m2.Not()), classes[2])

            bandaAno = self.imgClass.select(f'classification_{ano}')
            mascara = bandaAno.remap(classes, [1]*len(classes)).eq(1)

            reclass = (bandaAno.where(mascara, novaClasse.unmask(0))
                        .rename('map_class').setDefaultProjection(self.proj)
            )

            pontos_classificados = pontos_valid.map(lambda f: f.set(
                'map_class',
                reclass.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry= f.geometry(),#.centroid(30),
                    scale=30,
                    maxPixels=1e9
                ).get('map_class')
            ))

            pontos_validos = pontos_classificados.filter(ee.Filter.notNull(['map_class', 'ref']))


            pontos_acerto = pontos_validos.map(lambda f: f.set(
                'acerto',
                ee.Number(f.get('ref')).eq(ee.Number(f.get('map_class'))).int()
            ))

            total = pontos_acerto.size()
            acertos = pontos_acerto.aggregate_sum('acerto')
            acc = ee.Number(acertos).divide(total).getInfo()

            print(f"   🔍 {label} — ACC: {acc:.2f} | Limiar: {lim}")
            if acc > melhores['acc']:
                melhores.update({'acc': acc, 'l1': l1, 'l2': l2, 'l3': l3})

        print(f"✅ Melhor {label}: {melhores}")
        return melhores

    def apply_process(self):
        melhores_nat = self.avaliar_combo(self.naturais, self.classeDictNaturais, 'Naturais', 2015)
        melhores_ant = self.avaliar_combo(self.antropicas, self. classeDictAntropicas, 'Antrópicas', 2015)
        return {'bacia': self.id_bacias, 'naturais': melhores_nat, 'antropicas': melhores_ant}



caminho_csv         = './aval_filters/aval_natural_antropic_xBacias.csv'
caminho_limiares    = './aval_filters/resultados_bacias_limiares.csv'
resultados = []
# 1. Carrega bacias já processadas, se o arquivo existir
if os.path.exists(caminho_csv):
    df_existente = pd.read_csv(caminho_csv)
    bacias_processadas = set(df_existente['bacia'].astype(int).tolist())

    # Preenche a lista 'resultados' com dados do CSV
    for _, row in df_existente.iterrows():
          resultados.append({
              'bacia': str(int(row['bacia'])),
              'naturais': {
                  'acc': float(row['acc_naturais']),
                  'l1': float(row['l1_naturais']),
                  'l2': float(row['l2_naturais']),
                  'l3': float(row['l3_naturais'])
              },
              'antropicas': {
                  'acc': float(row['acc_antropicas']),
                  'l1': float(row['l1_antropicas']),
                  'l2': float(row['l2_antropicas']),
                  'l3': float(row['l3_antropicas'])
              }
          })

    print(f"🔁 {len(bacias_processadas)} bacias já processadas.")
else:
    # Se não existir, inicializa lista vazia e cria os CSVs com cabeçalho
    bacias_processadas = set()
    pd.DataFrame(columns=[
        'bacia',
        'acc_naturais', 'l1_naturais', 'l2_naturais', 'l3_naturais',
        'acc_antropicas', 'l1_antropicas', 'l2_antropicas', 'l3_antropicas'
    ]).to_csv(caminho_csv, index=False)
    pd.DataFrame(columns=[
        'bacia', 'l1_naturais', 'l2_naturais', 'l3_naturais',
        'l1_antropicas', 'l2_antropicas', 'l3_antropicas'
    ]).to_csv(caminho_limiares, index=False)
    print("📄 Arquivos CSV criados com cabeçalho.")



listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765', 
    '752', 
]
resultados = []
for cc, idbacia in enumerate(listaNameBacias[:]):
    if int(idbacia)  in bacias_processadas:
        print(f"⏩ Bacia {idbacia} já processada. Pulando...")
        continue

    try:
        print(" ")
        print(f"--------- 📢 #{cc} PROCESSING BACIA {idbacia} ---------")
        print("----------------------------------------------")
        # cont = gerenciador(cont)
        aplicando_FrequenceFilter = processo_filterAvaliationNatAnt(idbacia)
        res = aplicando_FrequenceFilter.apply_process()
        resultados.append(res)

        linha = {
            'bacia': res['bacia'],
            'acc_naturais': res['naturais']['acc'],
            'l1_naturais': res['naturais']['l1'],
            'l2_naturais': res['naturais']['l2'],
            'l3_naturais': res['naturais']['l3'],
            'acc_antropicas': res['antropicas']['acc'],
            'l1_antropicas': res['antropicas']['l1'],
            'l2_antropicas': res['antropicas']['l2'],
            'l3_antropicas': res['antropicas']['l3']
        }

        df_linha = pd.DataFrame([linha])
        df_linha.to_csv(caminho_csv, mode='a', header=False, index=False)

        # Salva também no CSV de limiares (consumido por filtersFrequency_step4B.py)
        linha_lim = {
            'bacia':          res['bacia'],
            'l1_naturais':    res['naturais']['l1'],
            'l2_naturais':    res['naturais']['l2'],
            'l3_naturais':    res['naturais']['l3'],
            'l1_antropicas':  res['antropicas']['l1'],
            'l2_antropicas':  res['antropicas']['l2'],
            'l3_antropicas':  res['antropicas']['l3'],
        }
        pd.DataFrame([linha_lim]).to_csv(caminho_limiares, mode='a', header=False, index=False)

        print(f"✅ Bacia {idbacia} processada e salva.")

    except Exception as e:
        print(f"❌ Erro na bacia {idbacia}: {e}")

    # sys.exit()