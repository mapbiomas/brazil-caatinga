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
import json
from pathlib import Path
import arqParametros as arqParams 
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
######################################################################################
### depois de aplicar o scripts filter_ROIs_red.py temos que passar este scripts     #
### para corregir a inclusão de amostras de outras classes que ficaram foras e devem #
### ser incluidas no ROIs                                                            #
######################################################################################

param = {     
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_DS_v4corrCC',
    'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_DS_v4corrCC',
    'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C',    
    'asset_joinsGrBaMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_V4C',
    'outAssetROIsred': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_DS_v4CC', 
    'outAssetROIsredMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_DS_v4CC', 
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
#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, IdAssetnameB):
    # id_asset = "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C"   
    nameB = IdAssetnameB.split("/")[-1]
    optExp = {
        'collection': ROIsFeat, 
        'description': nameB, 
        'assetId': IdAssetnameB          
        }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nameB + "..!")    

def sendFilenewAsset(idSource, idTarget):
    # moving file from repository Arida to Nextgenmap
    ee.data.renameAsset(idSource, idTarget)

print("vai exportar em ", param['assetOutMB'])
listYears = [k for k in range(param['yearInicial'], param['yearFinal'] + 1)]

for _nbacia in nameBacias[6:]:
    for cc, nyear in enumerate(listYears[:]): 
        nameFeatROIs =  f"{_nbacia}_{nyear}_cd" 

        ROIs_DScc = ee.FeatureCollection( os.path.join(param['asset_joinsGrBaMB'], nameFeatROIs)) 
        ROIs_RedCC = ee.FeatureCollection( os.path.join(param['outAssetROIsredMB'], nameFeatROIs)) 

        dictDScc = ROIs_DScc.aggregate_histogram('class').getInfo()
        dictRedcc = ROIs_RedCC.aggregate_histogram('class').getInfo()

        lstCCds = [int(float(ccs)) for ccs in list(dictDScc.keys())]
        lstCCred = [int(float(ccs)) for ccs in list(dictRedcc.keys())]
        print(f"lista all {lstCCds}  \n  >>>> {lstCCred}")
        lstCCfails = [cc for cc in lstCCds if cc not in lstCCred]
        print("lista de classes faltantes ", lstCCfails)
        idAssetOut = os.path.join(param['assetOutMB'], nameFeatROIs)
        
        if len(lstCCfails) > 0:
            featCCfails = ROIs_DScc.filter(ee.Filter.inList('class', lstCCfails))
            ROIs_RedCC = ROIs_RedCC.merge(featCCfails)            
            processoExportar(ROIs_RedCC, idAssetOut)
            print("exportando para ", idAssetOut)
        else:
            source = os.path.join(param['outAssetROIsredMB'], nameFeatROIs)
            try:
                sendFilenewAsset(source, idAssetOut) 
                print(cc, ' => move ', nameFeatROIs, f" to Folder in {idAssetOut}")
            except:
                print("errro ")
                            
            