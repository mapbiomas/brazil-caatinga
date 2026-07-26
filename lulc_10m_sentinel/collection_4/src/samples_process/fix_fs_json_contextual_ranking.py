#!/usr/bin/env python3
"""
Corrige o desalinhamento no FS_col2S2_v3.json:
As 14 bandas de contexto estrutural foram adicionadas à lista 'bandas'
mas sem os valores correspondentes em 'ranking'.
Este script adiciona ranking=0 para cada banda sem ranking,
garantindo len(bandas) == len(ranking) em todas as entradas.
"""
import json
import os

CONTEXTUAL_BANDS = [
    'osavi_median_mean', 'osavi_median_stdDev',
    'gcvi_median_mean', 'gcvi_median_stdDev',
    'avi_median_mean', 'avi_median_stdDev',
    'ndfia_mean', 'ndfia_stdDev',
    'bsi_median_mean', 'bsi_median_stdDev',
    'ui_median_mean', 'ui_median_stdDev',
    'awei_median_mean', 'awei_median_stdDev',
]

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, '..', 'dados', 'jsons', 'FS_col2S2_v3.json')

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

fixed = 0
already_ok = 0

for basin, years in data.items():
    for year, entry in years.items():
        nb = len(entry['bandas'])
        nr = len(entry['ranking'])
        if nb == nr:
            already_ok += 1
            continue
        # adiciona zeros para cobrir as bandas sem ranking
        entry['ranking'].extend([0] * (nb - nr))
        fixed += 1

print(f"Entradas já corretas : {already_ok}")
print(f"Entradas corrigidas  : {fixed}")

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

print(f"JSON salvo em: {json_path}")
