#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin

Junta todas as FeatureCollections de amostras por grade (gradeROIs_{id_grade}_{year})
que compõem cada bacia hidrográfica e exporta como um único asset por bacia.
"""
import os
import ee
import json
import sys

from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)

import configure_account_projects_ee
import gee_tools
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import switch_user, tasks

projAccount = get_current_account()
print(f"projeto selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('Earth Engine inicializado com sucesso!')
except ee.EEException:
    print('Falha ao inicializar o Earth Engine!')
    sys.exit(1)

param = {
    'asset_rois_grade': {
        'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_byGrades_emb'
    },
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/ROIs/ROIs_by_BasinGroup',
    'asset_grade': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
    'anoInicial': 2016,
    'anoFinal': 2025,
    'numeroTask': 6,
    'numeroLimit': 18,
    'conta': {
        '0':  'caatinga01',
        '3':  'caatinga02',
        '6':  'caatinga03',
        '9':  'caatinga04',
        '12': 'caatinga05',
        '15': 'solkan1201',
        '30': 'diegoGmail',
        '35': 'solkanGeodatin',
        '40': 'superconta',
    },
}

# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def get_csv_path(nfolder):
    """Retorna o caminho da pasta de CSVs/JSONs relativa ao script."""
    mpath = os.getcwd()
    pathparent = str(Path(mpath).parents[0])
    return pathparent + '/dados/' + nfolder


def gerenciador(cont):
    """Rotaciona contas GEE para distribuir tarefas exportadas."""
    numberofChange = list(param['conta'].keys())
    if str(cont) in numberofChange:
        print(f"alternando para conta #{cont} <> {param['conta'][str(cont)]}")
        switch_user(param['conta'][str(cont)])
        projAcc = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project=projAcc)
            print('Earth Engine reinicializado com sucesso!')
        except ee.EEException:
            print('Falha ao reinicializar o Earth Engine!')

        tarefas = tasks(n=param['numeroTask'], return_list=True)
        for lin in tarefas:
            print(str(lin))

    elif cont > param['numeroLimit']:
        return 0

    cont += 1
    return cont


def list_all_assets_paginated(folder_id):
    """
    Lista TODOS os assets de uma pasta usando paginação via nextPageToken.
    Retorna a lista completa de dicts de asset.
    """
    all_assets = []
    page_token = None
    page = 0
    while True:
        params = {'parent': folder_id}
        if page_token:
            params['pageToken'] = page_token
        response = ee.data.listAssets(params)
        batch = response.get('assets', [])
        all_assets.extend(batch)
        page += 1
        page_token = response.get('nextPageToken')
        print(f"  página {page}: {len(batch)} assets  (total acumulado: {len(all_assets)})")
        if not page_token:
            break
    return all_assets


def build_grade_index(folder_id, ano_inicial, ano_final):
    """
    Lista todos os assets da pasta (com paginação) e indexa por id_grade,
    filtrando pelo padrão gradeROIs_{id_grade}_{year} e pelo intervalo de anos.

    Retorna dict: id_grade (int) -> [path, ...]
    """
    print(f"\n  indexando assets em: {folder_id}")
    all_assets = list_all_assets_paginated(folder_id)
    print(f"  {len(all_assets)} assets no total")

    grade_index = {}
    ignorados = 0
    for asset in all_assets:
        path_ = asset['id']
        name_feat = path_.split('/')[-1]

        if not name_feat.startswith('gradeROIs_'):
            ignorados += 1
            continue

        parts = name_feat.split('_')
        if len(parts) < 3:
            ignorados += 1
            continue

        try:
            id_grade = int(parts[1])
            year = int(parts[2])
        except ValueError:
            ignorados += 1
            continue

        if not (ano_inicial <= year <= ano_final):
            continue

        grade_index.setdefault(id_grade, []).append(path_)

    print(f"  {len(grade_index)} grades indexadas ({ano_inicial}-{ano_final})"
          + (f" | {ignorados} assets ignorados (nome fora do padrão)" if ignorados else ""))
    return grade_index


def merge_grade_rois_for_basin(grade_index, grades_ids):
    """
    A partir do índice pré-construído, mescla todos os assets cujo id_grade
    esteja em grades_ids.

    Retorna (featAllRois, grades_ausentes).
    """
    matched_paths = []
    grades_presentes = set()

    for id_grade in grades_ids:
        paths = grade_index.get(id_grade, [])
        if paths:
            matched_paths.extend(paths)
            grades_presentes.add(id_grade)

    grades_ausentes = sorted(g for g in grades_ids if g not in grades_presentes)

    if not matched_paths:
        print("  AVISO: nenhum asset encontrado para esta bacia.")
        return ee.FeatureCollection([]), grades_ausentes

    feat_merged = ee.FeatureCollection(matched_paths[0])
    for path_ in matched_paths[1:]:
        feat_merged = feat_merged.merge(ee.FeatureCollection(path_))

    print(f"  {len(matched_paths)} assets mesclados | "
          f"{len(grades_presentes)} grades presentes | "
          f"{len(grades_ausentes)} ausentes: {grades_ausentes}")
    return feat_merged, grades_ausentes


def save_rois_to_asset(collection, name):
    """Exporta uma FeatureCollection como asset no GEE."""
    asset_id = param['asset_output'] + '/' + name
    task = ee.batch.Export.table.toAsset(
        collection=collection,
        description=name,
        assetId=asset_id,
    )
    task.start()
    print(f"  exportando '{name}' -> {asset_id}")


# ---------------------------------------------------------------------------
# Configuração principal
# ---------------------------------------------------------------------------

pathJson = get_csv_path("regJSON/")

listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614',
    '752', '7616', '745', '7424', '773', '7612', '7613',
    '7618', '7561', '755', '7617', '7564', '761111', '761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757', '771', '7712', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '765', '7544',
    '7438', '763', '7591', '7592', '7622', '746',
]

with open(pathJson + "dict_basin_49_lista_grades.json", 'r') as b_file:
    dictbasinGrid = json.load(b_file)

# ---------------------------------------------------------------------------
# Loop principal: mescla grades por bacia e exporta
# ---------------------------------------------------------------------------

# Indexa todos os assets uma única vez (com paginação completa)
grade_index = build_grade_index(
    param['asset_rois_grade']['id'],
    param['anoInicial'],
    param['anoFinal'],
)

grades_fails_global = []

for cc, nbacia in enumerate(listaNameBacias):
    print(f"\n{'='*60}")
    print(f"# {cc + 1}/{len(listaNameBacias)}  bacia: {nbacia}")

    grades_ids = set(dictbasinGrid[nbacia])
    print(f"  grades esperadas ({len(grades_ids)}): {sorted(grades_ids)}")

    feat_rois, grades_ausentes = merge_grade_rois_for_basin(grade_index, grades_ids)

    if grades_ausentes:
        grades_fails_global.append({'bacia': nbacia, 'grades_ausentes': grades_ausentes})

    name_export = 'rois_fromGrade_' + nbacia
    save_rois_to_asset(feat_rois, name_export)

if grades_fails_global:
    print("\n=== GRADES AUSENTES POR BACIA ===")
    for item in grades_fails_global:
        print(f"  bacia {item['bacia']}: {item['grades_ausentes']}")
