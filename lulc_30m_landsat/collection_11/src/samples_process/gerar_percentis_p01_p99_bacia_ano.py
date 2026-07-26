#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2

Gera percentis p01/p99 das 18 bandas brutas (annual/wet/dry) para cada
combinação bacia × ano usando multiprocessing — cada worker inicializa
EE de forma independente e salva um JSON isolado por combinação.

Estrutura de saída:
  src/dados/percentis_p01_p99/{nbacia}_{nyear}.json  ← individuais
  src/dados/dict_percentis_p01_p99_bacia_ano.json    ← merge final

Uso:
  python gerar_percentis_p01_p99_bacia_ano.py              # usa N_WORKERS=8
  python gerar_percentis_p01_p99_bacia_ano.py 12           # usa 12 workers
  python gerar_percentis_p01_p99_bacia_ano.py --merge      # só faz o merge
  python gerar_percentis_p01_p99_bacia_ano.py --merge-clean # merge + apaga individuais
"""

import os
import sys
import json
from pathlib import Path
from multiprocessing import Pool

# =========================================================
# Configuração — visível para os workers via fork (Linux)
# =========================================================
ASSET_BACIAS     = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions'
ASSET_COLLECTION = 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY'
BND_L = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']

LST_BAND_IMP = [
    'blue_median',     'green_median',     'red_median',     'nir_median',     'swir1_median',     'swir2_median',
    'blue_median_dry', 'green_median_dry', 'red_median_dry', 'nir_median_dry', 'swir1_median_dry', 'swir2_median_dry',
    'blue_median_wet', 'green_median_wet', 'red_median_wet', 'nir_median_wet', 'swir1_median_wet', 'swir2_median_wet',
]

P_LOW  = 1
P_HIGH = 99
SCALE  = 150  # metros — suficiente para percentis

NAME_BACIAS = [
    '765', '7544', '7541', '7411', '746', '7591', '7592',
    '761111', '761112', '7612', '7613', '7614', '7615',
    '771', '7712', '772', '7721', '773', '7741', '7746',
    '7754', '7761', '7764', '7691', '7581', '7625', '7584',
    '751', '752', '7616', '745', '7424', '7618', '7561',
    '755', '7617', '7564', '7422', '76116', '7671', '757',
    '766', '753', '764', '7619', '7443', '7438', '763', '7622'
]

ANOS = list(range(1985, 2026))

# Diretório de saída (relativo ao parent do script)
_SCRIPT_DIR = Path(__file__).resolve().parent
_PARENT_DIR = _SCRIPT_DIR.parent
OUTPUT_DIR  = str(_PARENT_DIR / 'dados' / 'percentis_p01_p99')
OUTPUT_JSON = str(_PARENT_DIR / 'dados' / 'dict_percentis_p01_p99_bacia_ano.json')

N_WORKERS_DEFAULT = 8


# =========================================================
# Funções de worker (executadas em processos filhos)
# =========================================================

def init_worker(proj_account):
    """Inicializa EE em cada processo worker antes de processar tasks."""
    import ee
    ee.Initialize(project=proj_account)


def compute_one(args):
    """
    Computa percentis p01/p99 para uma combinação (nbacia, nyear).
    Salva resultado em OUTPUT_DIR/{nbacia}_{nyear}.json.
    Retorna (nbacia, nyear, status_str).
    """
    import ee

    nbacia, nyear = args
    out_path = os.path.join(OUTPUT_DIR, f"{nbacia}_{nyear}.json")

    if os.path.exists(out_path):
        return nbacia, nyear, "skip"

    try:
        bnd_year = [b + '_median'     for b in BND_L]
        bnd_dry  = [b + '_median_dry' for b in BND_L]
        bnd_wet  = [b + '_median_wet' for b in BND_L]

        col_ee    = ee.ImageCollection(ASSET_COLLECTION).select(BND_L)
        fc_bacias = ee.FeatureCollection(ASSET_BACIAS)
        geom      = fc_bacias.filter(ee.Filter.eq('nunivotto4', nbacia)).geometry()

        mosaic_year = col_ee.filter(ee.Filter.date(f'{nyear}-01-01', f'{nyear}-12-31')).median().rename(bnd_year)
        mosaic_dry  = col_ee.filter(ee.Filter.date(f'{nyear}-08-01', f'{nyear}-12-31')).median().rename(bnd_dry)
        mosaic_wet  = col_ee.filter(ee.Filter.date(f'{nyear}-01-01', f'{nyear}-07-31')).median().rename(bnd_wet)
        img         = mosaic_year.addBands(mosaic_dry).addBands(mosaic_wet).clip(geom)

        stats = img.select(LST_BAND_IMP).reduceRegion(
            reducer=ee.Reducer.percentile([P_LOW, P_HIGH]),
            geometry=geom,
            scale=SCALE,
            maxPixels=1e13,
            bestEffort=True
        ).getInfo()

        with open(out_path, 'w') as f:
            json.dump(stats, f)

        return nbacia, nyear, "ok"

    except Exception as e:
        return nbacia, nyear, f"ERRO: {e}"


# =========================================================
# Merge: agrupa todos os JSONs individuais em um único dict
# =========================================================

def merge_jsons(output_dir, output_json, clean=False):
    """
    Lê todos os arquivos {nbacia}_{nyear}.json de output_dir e
    os combina em um único dict salvo em output_json.
    Se clean=True, apaga os individuais após o merge.
    """
    dict_out = {}
    arquivos  = sorted(f for f in os.listdir(output_dir) if f.endswith('.json'))

    for fname in arquivos:
        stem   = fname[:-5]               # remove .json
        nyear  = stem.rsplit('_', 1)[1]   # último segmento é o ano
        nbacia = stem.rsplit('_', 1)[0]   # tudo antes é o código da bacia

        with open(os.path.join(output_dir, fname), 'r') as f:
            stats = json.load(f)

        if nbacia not in dict_out:
            dict_out[nbacia] = {}
        dict_out[nbacia][nyear] = stats

    total = sum(len(v) for v in dict_out.values())
    with open(output_json, 'w') as f:
        json.dump(dict_out, f, indent=2)

    print(f"Merge concluído: {total} combinações → {output_json}")

    if clean:
        for fname in arquivos:
            os.remove(os.path.join(output_dir, fname))
        os.rmdir(output_dir)
        print(f"Pasta {output_dir} e {len(arquivos)} JSONs individuais removidos.")

    return dict_out


# =========================================================
# Principal
# =========================================================

if __name__ == '__main__':

    # Argumento opcional: número de workers, --merge ou --merge-clean
    only_merge  = '--merge'       in sys.argv
    merge_clean = '--merge-clean' in sys.argv
    n_workers   = N_WORKERS_DEFAULT
    for arg in sys.argv[1:]:
        if arg.isdigit():
            n_workers = int(arg)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if only_merge or merge_clean:
        modo = "--merge-clean" if merge_clean else "--merge"
        print(f"Modo {modo}: agrupa os JSONs existentes{' e apaga individuais' if merge_clean else ''}.")
        merge_jsons(OUTPUT_DIR, OUTPUT_JSON, clean=merge_clean)
        sys.exit(0)

    # Resolve conta GEE no processo principal (não nos workers)
    sys.path.insert(0, str(_PARENT_DIR))
    from configure_account_projects_ee import get_current_account
    proj_account = get_current_account()
    print(f"projeto GEE: {proj_account}")

    # Filtra combinações ainda não computadas
    tasks_list = [
        (nbacia, nyear)
        for nbacia in NAME_BACIAS
        for nyear  in ANOS
        if not os.path.exists(os.path.join(OUTPUT_DIR, f"{nbacia}_{nyear}.json"))
    ]

    total = len(NAME_BACIAS) * len(ANOS)
    print(f"Total combinações    : {total}")
    print(f"Já computadas (skip) : {total - len(tasks_list)}")
    print(f"A computar agora     : {len(tasks_list)}")
    print(f"Workers paralelos    : {n_workers}\n")

    if not tasks_list:
        print("Nada a fazer. Executando merge final...")
        merge_jsons(OUTPUT_DIR, OUTPUT_JSON)
        sys.exit(0)

    completed = 0
    errors    = 0

    with Pool(
        processes=n_workers,
        initializer=init_worker,
        initargs=(proj_account,)
    ) as pool:
        for nbacia, nyear, status in pool.imap_unordered(compute_one, tasks_list):
            if status == "skip":
                continue
            elif status == "ok":
                completed += 1
            else:
                errors += 1

            done = completed + errors
            print(f"  [{done}/{len(tasks_list)}] {nbacia}/{nyear}: {status}")

    print(f"\nConcluído — ok: {completed}  erros: {errors}")
    print("Executando merge final...")
    merge_jsons(OUTPUT_DIR, OUTPUT_JSON)
