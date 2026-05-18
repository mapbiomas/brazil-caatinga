#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import copy
import sys
import collections
collections.Callable = collections.abc.Callable
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise



param = {
    'asset_rois_grid': {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/PANTANAL/SAMPLES_GRID'},
    'asset_bacias_buffer' : 'users/gee_arcplan/regs_mb_pantanal',
}

def ask_byGrid_saved(dict_asset):
    getlstFeat = ee.data.getList(dict_asset)
    lst_temporalAsset = []
    assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']
    for idAsset in getlstFeat[:]:         
        path_ = idAsset.get('id')        
        name_feat = path_.replace( assetbase + '/', '')
        print("reading <==> " + name_feat)
        idGrade = name_feat.split('_')[2]
        # name_exp = 'rois_grade_' + str(idGrade) + "_" + str(nyear)
        if int(idGrade) not in lst_temporalAsset:
            lst_temporalAsset.append(int(idGrade))
    
    return lst_temporalAsset



lstIdCode = [kk for kk in range(1, 322)]
lstFeatAsset = ask_byGrid_saved(param['asset_rois_grid'])
print("   lista de feat ", lstFeatAsset[:5] )
print("  == size ", len(lstFeatAsset))
# sys.exit()
lst_Grid_fails = []
for cc, item in enumerate(lstIdCode[:]):
    print(f"# {cc + 1} loading geometry grade {item}")   
    if item not in lstFeatAsset:
        lst_Grid_fails.append(item)

print(" ==> ", lst_Grid_fails)
print(f" # {len(lst_Grid_fails)} grid fails to save ")


