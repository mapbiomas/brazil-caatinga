#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import ee
import sys
import collections
collections.Callable = collections.abc.Callable
from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
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


# --- CONFIGURAÇÕES ---

listaNameBacias = [
    '7754', '7691',  '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '7544', '7438', 
    '763', '7591', '7592', '746', '7712', '7622', '765'
]

years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

ASSET_INPUT = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3_cleaned'
ASSET_OUTPUT = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3_clean'
lst_class_type = ['natural', 'agropec', 'others']
# Definição das classes
dict_class = {
    'natural': [3, 4, 12],
    'agropec': [15, 21, 24],
    'others': [20, 25, 29, 33, 41]
}

# --- LÓGICA OTIMIZADA ---

def save_ROIs_toAsset(collection, name):
    optExp = {
        'collection': collection,
        'description': name,
        'assetId':  f"{ASSET_OUTPUT}/{name}"
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()

    print(f"✅ Task iniciada para export {name}: {task.id}")


def processar_bacias(nbacia):
    print(f"--- Iniciando processamento de {nbacia} bacias ---")
    
    name_feat = f'rois_grade_{nbacia}'
    asset_id_full = f"{ASSET_INPUT}/{name_feat}"
    
    
    print(f"Processando: {name_feat} ...")
    print(asset_id_full)
    # asset_id_full = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3_cleaned/rois_grade_7754'
    featROIs_bacia = ee.FeatureCollection([])
    # 1. Carrega a coleção inteira
    try:
        col_full = ee.FeatureCollection(asset_id_full)
        # Verifica se existe (opcional, evita erro se asset não existir)
        print(col_full.aggregate_histogram('class').getInfo() )

        for nyear in years:
            # 2. Filtra pelos anos desejados (de uma vez só)
            col_years = col_full.filter(ee.Filter.eq('year', nyear))

            # 3. Aplica a lógica de limpeza (Split & Merge)
            for class_type in lst_class_type:
            
                # Parte A: Classes que NÃO precisam de probabilidade alta (Others)
                col_theClass = col_years.filter(ee.Filter.inList('class', dict_class[class_type]))

                if class_type != 'others':
                    col_theClass = col_theClass.filter(ee.Filter.gte('prob_value', 75))
        
        
                # Junta tudo
                featROIs_bacia = featROIs_bacia.merge(col_theClass)

        # 4. Exporta
        save_ROIs_toAsset(featROIs_bacia, name_feat)
    except:
        print(f"Erro ao ler asset {name_feat}. Pulando.")

    

if __name__ == '__main__':
    for nbacia in listaNameBacias[:1]:
        processar_bacias(nbacia)