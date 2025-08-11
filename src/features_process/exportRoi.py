#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee 
# import gee
import sys
import os
import glob
from pathlib import Path
from tqdm import tqdm
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
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
# sys.setrecursionlimit(1000000000)

param = {    
    'asset_ROIs_manual': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2manualNN'},
    'asset_ROIs_cluster': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2clusterNN'},
    'asset_ROIs_automatic': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsv1N245'},
    'asset_ROIs_automatic': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN5allBND'},
    'asset_ROIs_grades': {"id" : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisGradesgrouped'},
    'asset_ROIS_bacia_grade': {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisGradesgroupedBuf'},
    'asset_ROIS_joinsBaGr': {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisJoinsbyBaciaNN'},
    'asset_ROISall_joins': {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_IndAllv3C'},
    'anoInicial': 1985,
    'anoFinal': 2024,
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta' : {
        '0': 'caatinga01',   # 
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '25': 'solkan1201',    
        '30': 'solkanGeodatin',
        '35': 'diegoUEFS',
        '40': 'superconta'   
    },
    'showFilesCSV' : False,
    'showAssetFeat': False
}

#lista de anos
list_anos = [k for k in range(param['anoInicial'],param['anoFinal'] + 1)]
print('lista de anos', list_anos)

#nome das bacias que fazem parte do bioma (38 bacias)
nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
# vizinhos selecionados para exportar
# nameBacias = [
#     "7438","752","7584","761111","7619","765","7712","773","7746",
#     "7591", "7615"
# ]

lstBaciasExp = [
    '7424', '7581', '745', '752', '7584', '7561', '7591',
    '761111', '761112', '757', '7592', '755', '7411', '7625'
]

print(f"processing {len(nameBacias)} bacias ")
#========================METODOS=============================
def GetPolygonsfromFolder(dictAsset):
    
    getlistPtos = ee.data.getList(dictAsset)
    ColectionPtos = []
    # print("bacias vizinhas ", nBacias)
    lstROIsAg = [ ]
    for idAsset in tqdm(getlistPtos):         
        path_ = idAsset.get('id')        
        ColectionPtos.append(path_) 
        name = path_.split("/")[-1]
        if param['showAssetFeat']:
            print("Reading ", name)
        
    return ColectionPtos


#========================METODOS=============================
#exporta a imagem classificada para o asset
def processoExportar(ROIsFeat, nameB, nfolder):    
    optExp = {
          'collection': ROIsFeat, 
          'description': nameB, 
          'folder': nfolder          
        }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameB + "..!")    


# sys.exit()

# get dir path of script 
npath = os.getcwd()
# get dir folder before to path scripts 
npath = str(Path(npath).parents[0])
# folder of CSVs ROIs
roisPath = '/dados/Col9_ROIs_grades/'
npath += roisPath
print("path of CSVs Rois is \n ==>",  npath)


lstPathCSV = glob.glob(npath + "*.csv")
lstNameFeat = []
for xpath in tqdm(lstPathCSV):
    nameCSV = xpath.split("/")[-1][:-4]
    if param['showFilesCSV']:
        print(" => " + nameCSV)
    lstNameFeat.append(nameCSV)


lstNameFeat = [
    "7438","752","7584","761111","7591", "751", "7422",
    "7619","765","7712","773","7746","7615","7411","7424",
    "745","755","7561", "7564",'7616','7443','746','753',
    '7541', '7544','757','7581','7592','761112','76116',
    '7612','7613','7614','7617','7618','7619','7622','7625',
    '763','764','766','7671','7691','771','772','7721','7741',
    '7754','7761','7764'
]
# lstNameFeat = []
# lstNameFeat = []
# sys.exit()
# iterando com cada uma das folders FeatC do asset
# 'asset_ROIs_cluster', 'asset_ROIs_manual', asset_ROIs_grades, asset_ROIS_bacia_grade
# asset_ROIS_joinsBaGr ,asset_ROISall_joins
lstKeysFolder = ['asset_ROISall_joins']   
for assetKey in lstKeysFolder:
    lstAssetFolder = GetPolygonsfromFolder(param[assetKey])
    # print(lstAssetFolder[:5])
    list_baciaYearFaltan = []
    # sys.exit()
    for cc, assetFeats in enumerate(lstAssetFolder[:]):        
        nameFeat = assetFeats.split("/")[-1].split("_")[-1]
        # print(nameFeat)
        if str(nameFeat) not in lstNameFeat:
            print(f" #{cc} loading FeatureCollection => ", assetFeats.split("/")[-1])
            try: 
                ROIs = ee.FeatureCollection(assetFeats)       
                # print(nameFeat, " ", ROIs.size().getInfo())     
                processoExportar(ROIs, nameFeat, "ROIs_Joined_Allv3")              
            except:
                # list_baciaYearFaltan.append(nameFeat)
                # arqFaltante.write(nameFeat + '\n')
                print("faltando ... " + nameFeat)
        else:
            print(f"basin < {nameFeat} > was prosseced")
        # arqFaltante.close()
        # cont = gerenciador(cont)