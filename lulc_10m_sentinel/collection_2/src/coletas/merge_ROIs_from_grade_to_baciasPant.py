#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
import copy
import sys
from tqdm import tqdm
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
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/PANTANAL/SAMPLES_BASIN',
    'asset_grad': 'projects/gee-arcplan/assets/grid_pantanal',
    'anoInicial': 2016,
    'anoFinal': 2022,
    'changeCount': True,

}

def ask_byGrid_saved(dict_asset, printName, listtoLoad):
    getlstFeat = ee.data.getList(dict_asset)
    assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']

    featAllRois = ee.FeatureCollection([])
    for idAsset in tqdm(getlstFeat[:]):         
        path_ = idAsset.get('id')   
        if printName:     
            name_feat = path_.replace( assetbase + '/', '')
            print(f" loading {name_feat}")
            idGrid = int(name_feat.split("_")[2])
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

def getDictionaryBasinGrid (shpGrade, shpRegions):
    mydictGrade = {}
    for ii in range(7):
        idreg = 'reg' + str(ii)
        feattmp = shpRegions.filter(ee.Filter.eq('id_reg', idreg))
        print(f"loading {idreg} with {feattmp.size().getInfo()}")
        featGradReg = shpGrade.filterBounds(feattmp.geometry())

        lstIDs = featGradReg.reduceColumns(ee.Reducer.toList(), ['GRID_ID']).get('list').getInfo()
        print(lstIDs)
        mydictGrade[idreg] = lstIDs

    return mydictGrade


getdictGrid = False
listaNameRegion = ['reg'+str(kk) for kk in range(0, 7)]
shpbacias = ee.FeatureCollection(param['asset_bacias_buffer'])
shpGridPant = ee.FeatureCollection(param['asset_grad'])
dictbasinGrid = {}   
if getdictGrid:
    dictbasinGrid = getDictionaryBasinGrid(shpGridPant, shpbacias)
else:
    dictbasinGrid = {
        'reg0': [
            135, 147, 159, 171, 183, 195, 208, 224, 240, 256, 272, 288, 108, 121, 
            134, 146, 158, 170, 182, 194, 207, 223, 239, 255, 271, 287, 81, 94, 
            107, 120, 133, 145, 157, 169, 181, 193, 206, 222, 238, 254, 270, 286, 
            302, 80, 93, 106, 119, 132, 144, 156, 168, 180, 192, 205, 221, 237, 
            253, 269, 285, 301, 310, 79, 92, 105, 118, 131, 143, 155, 167, 179, 
            191, 204, 220, 236, 252, 268, 284, 300, 309, 78, 91, 104, 117, 130, 
            142, 154, 166, 178, 190, 203, 219, 235, 251, 267, 283, 299, 308, 77, 
            90, 103, 116, 129, 141, 153, 165, 177, 189, 202, 218, 234, 250, 266, 
            282, 298, 50, 63, 76, 89, 102, 115, 128, 140, 152, 164, 176, 188, 201, 
            217, 233, 249, 265, 281, 297, 16, 27, 38, 49, 62, 75, 88, 101, 114, 127, 
            139, 151, 163, 175, 187, 200, 216, 232, 248, 264, 280, 296, 4, 15, 26, 37,
            48, 61, 74, 87, 100, 113, 126, 138, 150, 162, 174, 186, 199, 215, 231, 247, 
            263, 279, 295, 307, 3, 14, 25, 36, 47, 60, 73, 86, 99, 112, 125, 137, 149, 
            161, 173, 185, 198, 214, 230, 246, 262, 278, 294, 306, 2, 13, 24, 35, 46, 59, 
            72, 85, 98, 111, 124, 136, 148, 184, 197, 213, 229, 245, 261, 277, 293, 305, 
            1, 12, 23, 58, 71, 84, 97, 110, 196, 212, 228, 244, 260, 276, 292, 304, 211, 
            227, 243, 259, 275, 291, 303, 258, 274, 290, 257, 273, 289
        ],
        'reg1':[
            57, 70, 83, 96, 109, 122, 135, 56, 69, 82, 95, 108, 44, 55, 68, 81, 94, 10, 
            21, 32, 43, 54, 67, 80, 93, 9, 20, 31, 42, 53, 66, 79, 92, 105, 118, 8, 19, 
            30, 41, 52, 65, 78, 91, 104, 117, 7, 18, 29, 40, 51, 64, 77, 90, 103, 116, 6, 
            17, 28, 39, 50, 63, 76, 89, 102, 115, 5, 16, 27, 38, 49, 62, 75, 88, 101, 114, 
            4, 15, 26, 37, 48, 61, 74, 87, 100, 113, 3, 14, 25, 36, 47, 60, 73, 86, 99, 112, 
            2, 13, 24, 35, 46, 59, 72, 85, 98, 71, 84
        ],
        'reg2': [
            171, 183, 134, 146, 158, 170, 182, 194, 207, 133, 145, 157, 169, 181, 193, 206, 
            119, 132, 144, 156, 168, 180, 192, 205, 221, 118, 131, 143, 155, 167, 179, 191, 
            204, 220, 117, 130, 142, 154, 166, 178, 190, 203, 219, 116, 129, 141, 153, 165, 
            177, 189, 202, 218, 115, 128, 140, 152, 164, 176, 188, 201, 217, 127, 139, 151, 
            163, 175, 187, 200, 138, 150, 162, 174, 186
        ],
        'reg3': [
            208, 224, 240, 256, 272, 207, 223, 239, 255, 271, 206, 222, 238, 254, 270, 286, 
            221, 237, 253, 269, 285, 301, 220, 236, 252, 268, 284, 219, 235, 251, 267, 218, 
            234, 250, 266, 217
        ],
        'reg4':[
            199, 215, 231, 247, 295, 307, 198, 214, 230, 246, 262, 278, 294, 306, 197, 213, 
            229, 245, 261, 277, 293, 196, 212, 228, 244, 260, 276, 292, 211, 227, 243, 259
        ],
        'reg5':[
            285, 301, 268, 284, 300, 309, 267, 283, 299, 218, 234, 250, 266, 282, 201, 217, 
            233, 249, 265, 281, 200, 216, 232, 248, 264, 280, 296, 215, 231, 247, 263, 279, 
            246, 262, 245
        ],
        'reg6':[
            57, 70, 83, 96, 109, 122, 135, 56, 69, 82, 95, 108, 44, 55, 68, 81, 94, 10, 21, 
            32, 43, 54, 67, 80, 93, 9, 20, 31, 42, 53, 66, 79, 92, 105, 19, 30, 41, 52, 65, 
            78, 91, 104, 117, 18, 29, 40, 51, 64, 77, 90, 103, 116, 28, 39, 50, 63, 76, 89, 
            102, 115, 75, 88, 101, 114, 100, 113
        ]
    }


# sys.exit()
#loading all ROIs from grades of pantanal
printarNomeLoaded = True

for cc, nreg in enumerate(listaNameRegion[1:]):
    region_bacia = shpbacias.filter(ee.Filter.eq('nunivotto4', nreg))
    print(f"# {cc + 1} loading geometry basin {nreg} <> {region_bacia.size().getInfo()}")
    lstIdsReg = dictbasinGrid[nreg]
    # featROIsreg = shpFeatAsset.filter(ee.Filter.inList('GRID_ID', lstIdsReg))
    print(" ==== loading ROIs points from folder ==== ")   
    featROIsreg = ask_byGrid_saved(param['asset_rois_grid'], printarNomeLoaded, lstIdsReg)

    name_export = 'rois_grade_' + nreg 
    print(f"==== <{featROIsreg.size().getInfo()}> ======")
    save_ROIs_toAsset(featROIsreg, name_export)