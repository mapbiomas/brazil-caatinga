#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee
import sys
import os
import json
from pathlib import Path
import collections

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('✅ The Earth Engine package initialized successfully!')
except Exception as e:
    print(f"❌ Erro ao inicializar o GEE: {e}")
    sys.exit()

# =========================================================================
# PARÂMETROS GERAIS
# =========================================================================
lst_Classe = [3, 4, 12, 15, 19, 21, 25, 29, 33, 36]
quant_PtosxClass = [1000, 2500, 600, 1850, 850, 1000, 650, 500, 600, 600]

# Mapeia as classes para os limites padrão em um dicionário Python
base_limits = dict(zip(lst_Classe, quant_PtosxClass))

nameBacias = [
    # '7411', '7754', '7691', '7581', '7625', '7584', '751', 
    # '7614', '752', '7616', '745', '7424', '773', '7612', '7613', 
    # '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    # '7741', '7422', '76116', '7761', '7671', '7615', '7764', 
    # '757', '771', '7712', '766', '7746', '753', '764', '7721', 
    # '772', '7619', '765', '7438', '7591', '7592', '7622', '746', 
    # '7541', '7443', '7544', '763'    
    "7424","7612","7561","7617","7564","76116","7438"
]


assets_input_stat = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/stats_mosaics_ba/all_statisticsMosaicC9_'
asset_input = "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesv1CC"
assets_output = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCred'

# =========================================================================
# CARREGA FALTANTES — se o JSON existir, processa só os que faltam
# =========================================================================
JSON_FALTANTES = os.path.join(
    os.path.dirname(__file__),
    '../utis_scripts/dict_bacias_anos_faltantes_CCred_fromBasin.json'
)

# if os.path.exists(JSON_FALTANTES):
#     with open(JSON_FALTANTES, 'r', encoding='utf-8') as f:
#         dict_faltantes = json.load(f)
#     # Filtra nameBacias para só as que têm faltantes
#     nameBacias = [b for b in nameBacias if b in dict_faltantes]
#     print(f"Modo FALTANTES: {len(nameBacias)} bacias com anos pendentes (fonte: {os.path.basename(JSON_FALTANTES)})")
# else:
#     dict_faltantes = None
#     print("JSON de faltantes não encontrado — processando todas as bacias/anos.")

# =========================================================================
# LÓGICA DE PROCESSAMENTO
# =========================================================================
print(f"Iniciando agendamento de tarefas para {len(nameBacias)} bacias...")

total_tasks = 0

for basin in nameBacias:
    # anos_basin = dict_faltantes[basin] if dict_faltantes else list(range(1985, 2026))
    anos_basin = [2025]
    for year in anos_basin:
        
        # 1. Tratativa para 2024 e 2025 usarem a referência estatística de 2023
        year_stats = 2023 if year in [2024, 2025] else year
        
        # Constrói o caminho dos Assets
        try:
            asset_in_stats = f"{assets_input_stat}{basin}"
            fc_stats = ee.FeatureCollection(asset_in_stats)
            print("size feature Collection   ", fc_stats.size().getInfo())
        except:
            asset_in_stats = f"{assets_input_stat}{'741'}"
            

        asset_in_target = f"{asset_input}/rois_fromGrade_{basin}_{year}"
        asset_id_out = f"{assets_output}/rois_fromBasin_{basin}_{year}"
        
        # 2. Carrega as FeatureCollections
        fc_stats = ee.FeatureCollection(asset_in_stats).filter(ee.Filter.eq('year', year))
        fc_target = ee.FeatureCollection(asset_in_target)

        
        # 3. Lógica Server-Side para verificar se Classe 15 > Classe 4
        size_4 = fc_stats.filter(ee.Filter.eq('class', 4)).size()
        size_15 = fc_stats.filter(ee.Filter.eq('class', 15)).size()
        
        # Retorna um booleano do lado do servidor (True se 15 for maior que 4)
        is_15_greater = size_15.gt(size_4)
        
        lista_fc_classes = []
        
        # 4. Aplica o downsample classe por classe
        for nclass in lst_Classe:
            fc_class = fc_target.filter(ee.Filter.eq('class', nclass))
            
            # Condição dinâmica para trocar os limites de 4 e 15
            if nclass == 4:
                # Se 15 > 4, o limite de 4 cai para 1850. Senão, fica 2500.
                limit = ee.Algorithms.If(is_15_greater, base_limits[15], base_limits[4])
            elif nclass == 15:
                # Se 15 > 4, o limite de 15 sobe para 2500. Senão, fica 1850.
                limit = ee.Algorithms.If(is_15_greater, base_limits[4], base_limits[15])
            else:
                limit = base_limits[nclass]
            
            # Cálculo seguro da fração de retenção
            size_class = fc_class.size().max(1) # Impede divisão por zero caso a classe não exista
            fraction = ee.Number(limit).divide(size_class).min(1.0) # Trava em 100% (1.0)
            
            # Aplica o filtro de downsample
            fc_sampled = fc_class.randomColumn('rand_bin').filter(ee.Filter.lt('rand_bin', fraction))
            lista_fc_classes.append(fc_sampled)
            
        # 5. Achata tudo em uma única FeatureCollection final
        fc_final = ee.FeatureCollection(lista_fc_classes).flatten()
        
        # 6. Exportação
        task_name = asset_id_out.split("/")[-1]
        
        task = ee.batch.Export.table.toAsset(
            collection=fc_final,
            description=task_name,
            assetId=asset_id_out
        )
        
        task.start()
        total_tasks += 1
        
        print(f"✅ Tarefa enviada: {task_name}")

print("\n" + "="*50)
print(f"🚀 Um total de {total_tasks} tarefas foram enfileiradas no Earth Engine!")
print("="*50)