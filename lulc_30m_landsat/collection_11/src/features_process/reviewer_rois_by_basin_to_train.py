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
# import json
from pathlib import Path
# import arqParametros as arqParams 
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

# sys.setrecursionlimit(1000000000)
###################################################################################################
###  aplicar o scripts só para verificar se todas as amostras para anos e bacias estão prontas ####
###################################################################################################

def GetPolygonsfromFolder(dict_idasset):    
    getlistPtos = ee.data.getList(dict_idasset)
    list_idasset = []

    for idAsset in getlistPtos:         
        path_ = idAsset.get('id')
        list_idasset.append(path_)
    
    return  list_idasset

def reviewer_samples_byYear(dir_asset, nbasin, nlistYears, dict_missing):
    for cc, nyear in enumerate(nlistYears[:]):
        nameFeatROIs =  f"rois_fromBasin_{nbasin}_{nyear}"
        idAsset = os.path.join(dir_asset, nameFeatROIs)
        try:
            feat_tmp = ee.FeatureCollection(idAsset)
            print(f"#{cc} >> {nyear} : ", feat_tmp.aggregate_histogram('class').getInfo())
        except Exception as e:
            print(f"#{cc} >> {nyear} : FAILED - {e}")
            dict_missing.setdefault(nbasin, []).append(nyear)


def reviewer_samples_byFC(dir_asset, nbasin, nlistYears):
    nameFeatROIs =  f"rois_fromGrade_{nbasin}" 
    idAsset = os.path.join(dir_asset, nameFeatROIs)
    featB = ee.FeatureCollection(idAsset)
    for cc, nyear in enumerate(nlistYears[:]): 
        feat_tmp = featB.filter(ee.Filter.eq('year', nyear))
        print(f"#{cc} >> {nyear} : ", feat_tmp.aggregate_histogram('class').getInfo())

param = {     
    # 'asset_sample_rev': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCred',
    'asset_sample_rev': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCredv2',
    'yearInicial': 1985,
    'yearFinal': 2025,
}

nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712',  '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
# nameBacias = [
#     '765','7544', '7541'
# ]
listYears = [k for k in range(param['yearInicial'], param['yearFinal'] + 1)]
list_idassets = GetPolygonsfromFolder({'id': param['asset_sample_rev']})
filtrarFC = False
if len(list_idassets) > len(nameBacias):
    filtrarFC = False

del list_idassets

dict_missing = {}

for ii, _nbacia in enumerate(nameBacias[:]):
    print(f" # {ii} processing basin {_nbacia}")
    if filtrarFC:
        reviewer_samples_byFC(param['asset_sample_rev'], _nbacia, listYears)
    else:
        reviewer_samples_byYear(param['asset_sample_rev'], _nbacia, listYears, dict_missing)

print("\n=== ASSETS FALTANTES ===")
for kk, vv in dict_missing.items():
    print(f"{kk}:{vv}")