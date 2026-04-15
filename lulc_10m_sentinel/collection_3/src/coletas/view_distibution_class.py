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
import json
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
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '7544', '7438', 
    '763', '7591', '7592', '746', '7712', '7622', '765'
]
ASSET_INPUT = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_clean'


def convert_distribuition_ideal(fc_ROIs):

    lst_class_present = [3,4,12,15,20,24,25,29,33,41]
    lst_class_end = [3,4,12,15,18,25,25,29,33,18]
    big_ROIs = [3, 4, 15]
    dict_prop = {
        3: 800,
        4: 1600,
        15: 1200,
    }
    fc_ROIs = (fc_ROIs.filter(ee.Filter.inList('class', lst_class_present))
                        .remap(lst_class_present, lst_class_end, 'class')
    )
    fc_other =fc_ROIs.filter(ee.Filter.inList('class', big_ROIs).Not())
    for nclass in big_ROIs:
        fc_tmp = fc_ROIs.filter(ee.Filter.eq('class', nclass))
        size_fc = ee.Number(fc_tmp.size())
        porcent = ee.Number(dict_prop[nclass]).divide(size_fc)
        fc_tmp = fc_tmp.randomColumn("rc")
        fc_tmp = fc_tmp.filter(ee.Filter.lt('rc', porcent))
        print(f"classe {nclass} >>> {fc_tmp.size().getInfo()}")

        fc_other = fc_other.merge(fc_tmp)

    return fc_other


dict_bacia_class = {}
lstClass = []

if __name__ == '__main__':
    for nbacia in listaNameBacias[:1]:
        name_feat = f'rois_grade_{nbacia}'
        asset_id_full = f"{ASSET_INPUT}/{name_feat}"
        col_full = ee.FeatureCollection(asset_id_full)
        print(f"============= processing bacia {nbacia} ===================")
        dict_class = col_full.aggregate_histogram('class').getInfo()
        print(dict_class)
        print(" ---------------- new -----------------")
        col_rois_dist = convert_distribuition_ideal(col_full)
        print(col_rois_dist.aggregate_histogram('class').getInfo())
        dict_bacia_class[nbacia] = dict_class
        for kk in dict_class.keys():
            if kk not in lstClass:
                lstClass.append(kk)


# print("lista de classes ", lstClass)

# with open("dict_lst_distribuition_class_by_basin_v3.json", "w") as outfile:
#     json.dump(dict_bacia_class, outfile)