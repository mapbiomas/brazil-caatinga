#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import ee
import gee
import copy
import sys
from tqdm import tqdm
import register_parameters as reg_param
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


param = {
    # 'asset_rois_grid1': {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2'},
    'asset_rois_grid2': {'id' : 'projects/nexgenmap/SAMPLES/Caatinga/ROIs'},
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta3',
    'asset_grad' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
    'anoInicial': 2016,
    'anoFinal': 2022,
    'changeCount': True,
    'numeroTask': 6,
    'numeroLimit': 30,
    'conta': {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',
        '25': 'solkan1201',
        '30': 'diegoGmail',
        '35': 'solkanGeodatin',
        '40': 'superconta'
    },
}

def ask_byGrid_saved( dict_asset2, printName, listtoLoad):  # dict_asset1,
    # getlstFeat1 = ee.data.getList(dict_asset1)
    # assetbase1 = "projects/earthengine-legacy/assets/" + dict_asset1['id']
    getlstFeat2 = ee.data.getList(dict_asset2)
    assetbase2 = "projects/earthengine-legacy/assets/" + dict_asset2['id']
    # lstPath1 = [kk for kk in getlstFeat1]
    # print(f" we have {len(lstPath1)} featshp of ROIs")
    lstPath2 = [kk for kk in getlstFeat2]
    print(f" we have {len(lstPath2)} featshp of ROIs")
    # lstPath = lstPath1 + lstPath2
    # print(f" we have {len(lstPath)} featshp of ROIs")
    # sys.exit()
    featAllRois = ee.FeatureCollection([])
    for idAsset in tqdm(lstPath2):    
        # print(idAsset)     
        path_ = idAsset['id']
        if 'nexgenmap' in path_:
            name_feat = path_.replace(assetbase2 + '/', '')
        else:
            name_feat = path_.replace(assetbase1 + '/', '')
        if printName:
            print(f" loading {name_feat}")
        print(name_feat.split("_"))
        idGrid = int(name_feat.split("_")[2])
        print()
        if idGrid in listtoLoad:
            print("  >>>>> merged  <<<< ")
            feat_tmp = ee.FeatureCollection(path_)
            featAllRois = featAllRois.merge(feat_tmp)
    
    return featAllRois

def save_ROIs_toAsset(collection, name):
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': param['asset_output'] + "/" + name
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando ROIs da bacia $s ...!", name)

def getDictionaryBasinGrid (listaBacias, shpGrade, shpRegions):
    mydictGrade = {}
    for mbacia in listaBacias:
        feattmp = shpRegions.filter(ee.Filter.eq('nunivotto4', mbacia))
        print(f"loading {mbacia} with {feattmp.size().getInfo()}")
        featGradReg = shpGrade.filterBounds(feattmp.geometry())
        lstIDs = featGradReg.reduceColumns(ee.Reducer.toList(), ['indice']).get('list').getInfo()
        print(lstIDs)
        mydictGrade[mbacia] = lstIDs

    return mydictGrade

listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
getdictGrid = False
printarNomeLoaded = True
shpbacias = ee.FeatureCollection(param['asset_bacias_buffer'])
# shpFeatAsset = ask_byGrid_saved(param['asset_rois_grid'])
shpGridCaat = ee.FeatureCollection(param['asset_grad'])
print("   loading Grid polygons to group by regions  ")
dictbasinGrid = {}
if getdictGrid:
    dictbasinGrid = getDictionaryBasinGrid(listaNameBacias, shpGridCaat, shpbacias)
else:
    dictbasinGrid = reg_param.dictbasinGrid
    if printarNomeLoaded:
        for kbasin, lstG in dictbasinGrid.items():
            print(kbasin, lstG)

# sys.exit()
lst_Grid_fails = []
for cc, nbacia in enumerate(listaNameBacias[:]):
    region_bacia = shpbacias.filter(ee.Filter.eq('nunivotto4', nbacia))
    print(f"# {cc + 1} loading geometry basin {nbacia} <> {region_bacia.size().getInfo()}")

    lstIdsReg = dictbasinGrid[nbacia]
    print(" ==== loading ROIs points from folder ==== ")   
    featROIsreg = ask_byGrid_saved( param['asset_rois_grid2'], printarNomeLoaded, lstIdsReg) # param['asset_rois_grid1'],
    
    name_export = 'rois_grade_' + nbacia 
    print(f"==== bacia {nbacia}==== <{featROIsreg.size().getInfo()}> ======")
    save_ROIs_toAsset(featROIsreg, name_export)