#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os
import ee
# import gee
import json
import sys
import pandas as pd
from tqdm import tqdm
import register_parameters as reg_param
import collections
collections.Callable = collections.abc.Callable

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
    'asset_rois_grid1': {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesInd_MBV4'},
    # 'asset_rois_grid2': {'id' : 'projects/nexgenmap/SAMPLES/Caatinga/ROIs'},
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_IndAllv4C',
    # 'asset_roi_basins': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_Ind',
    'asset_roi_basins': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesIndV3',
    'asset_grad' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
    'anoInicial': 2016,
    'anoFinal': 2024,
    'changeCount': True,
    'numeroTask': 6,
    'numeroLimit': 18,
    'conta': {
        '0': 'caatinga01',
        '3': 'caatinga02',
        '6': 'caatinga03',
        '9': 'caatinga04',
        '12': 'caatinga05',
        '15': 'solkan1201',
        '30': 'diegoGmail',
        '35': 'solkanGeodatin',
        '40': 'superconta'
    },
}

def ask_ifGrid_ROIS_saved( dict_asset, printName, listtoLoad): 
    # a lista de todos os asset dentro da pasta principal definina em param.asset_rois_grid1
    getlstFeat2 = ee.data.getList(dict_asset)
    print(f" we have {len(getlstFeat2)} featshp of ROIs")
    sizeFeat = 0
    featAllRois = ee.FeatureCollection([])
    cc = 0
    lstPresent =[]
    for idAsset in tqdm(getlstFeat2):    
        # print(idAsset)     
        path_ = idAsset['id']
        name_feat = path_.split('/')[-1]
        idGrade = int(name_feat.split("_")[-1])

        # entra na lista de grades que pertencem a bacia selecionada 
        if idGrade in listtoLoad:
            lstPresent.append(idGrade)
            print(f"#{cc}  >> {idGrade}  adding >> from {name_feat}")
            shpROIS = ee.FeatureCollection(path_)
            if cc < 1:
                sizeFeat = shpROIS.size().getInfo()
                print("quantidade de samples ", sizeFeat)            
            featAllRois = featAllRois.merge(shpROIS)
            cc += 1
    # verificar se estão todas as possiveis grades dentro 
    # das verificadas 
    lstFailss = []
    for idgrade in listtoLoad:
        if idgrade not in lstPresent:
            lstFailss.append(idgrade)
    return featAllRois, lstFailss

def ask_byGrid_saved( dict_asset, printName, listtoLoad): 
    getlstFeat2 = ee.data.getList(dict_asset)
    assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']
    lstPath2 = [kk for kk in getlstFeat2]
    print(f" we have {len(lstPath2)} featshp of ROIs")
    lstGridFails = []
    # sys.exit()
    lstPathFeat = []
    for idAsset in tqdm(lstPath2):    
        # print(idAsset)     
        path_ = idAsset['id']
        name_feat = path_.replace(assetbase + '/', '')
        # if printName:
        #     print(f" loading {name_feat}")
        # print(name_feat.split("_"))
        idGrid = int(name_feat.split("_")[2])
        # print()
        if idGrid in listtoLoad:
            print(f" >>>>>  loading and merged  <<<< {name_feat} ")
            lstPathFeat.append(path_)

    print("cleaning the sampes ", lstPathFeat[:3])
    nlstPathFeats = []
    for idGrid in listtoLoad:
        templst = []
        cc = 0
        for npath in lstPathFeat:
            if str(idGrid) in npath:
                print("#", cc, " adding >> ", npath.replace(assetbase + '/', ''))
                cc += 1
                templst.append(npath)   

        templstw = templst
        if len(templst) > 40:
            templstw = [npath for npath in templst if len(npath.split('_')) > 3]            
            print("cleaning the sampes ", templst[:3])

        elif len(templst) < 40 and len(templst) > 1:
            lstGridFails.append([idGrid, len(templst)])
        
        nlstPathFeats += templstw

    featAllRois = ee.FeatureCollection([])
    for npath in nlstPathFeats:
        feat_tmp = ee.FeatureCollection(path_)
        featAllRois = featAllRois.merge(feat_tmp)
    
    return featAllRois, lstGridFails

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


def getPathCSV (nfolder):
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])
    # folder of CSVs ROIs
    roisPath = '/dados/' + nfolder
    mpath = pathparent + roisPath
    print("path of CSVs Rois is \n ==>",  mpath)
    return mpath


def gerenciador(cont):
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    print(numberofChange)
    
    if str(cont) in numberofChange:
        print(f"inicialize in account #{cont} <> {param['conta'][str(cont)]}")
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!')         
        # relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:   
            print(str(lin))         
            # relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

pathJson = getPathCSV("regJSON/")  

listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', 
    '7438', '763', '7591', '7592', '7622', '746'
]
getdictGrid = False
printarNomeLoaded = True
shpbacias = ee.FeatureCollection(param['asset_bacias_buffer'])
# shpFeatAsset = ask_byGrid_saved(param['asset_rois_grid'])
shpGridCaat = ee.FeatureCollection(param['asset_grad'])
print("   loading Grid polygons to group by regions  ")
# dictbasinGrid = {}
# if getdictGrid:
#     dictbasinGrid = getDictionaryBasinGrid(listaNameBacias, shpGridCaat, shpbacias)
# else:
#     dictbasinGrid = reg_param.dictbasinGrid
#     if printarNomeLoaded:
#         for kbasin, lstG in dictbasinGrid.items():
#             print(kbasin, lstG)

b_file = open(pathJson +  "dict_basin_49_lista_grades.json", 'r')
dictbasinGrid = json.load(b_file)
for kkey, lstVal in dictbasinGrid.items():
    print(f"{kkey} >> {lstVal}")

cont = 0
cont = gerenciador(cont)

dictROIsclass = {}
# sys.exit()
listaGrid_fails = []
for cc, nbacia in enumerate(listaNameBacias[:]):
    region_bacia = shpbacias.filter(ee.Filter.eq('nunivotto4', nbacia))
    print(f"# {cc + 1} loading geometry basin {nbacia} <> {region_bacia.size().getInfo()}")

    lstIdsReg = dictbasinGrid[nbacia]
    print(" ==== loading ROIs points from folder ==== ")   
    featROIsreg, lstFails =  ask_ifGrid_ROIS_saved( param['asset_rois_grid1'], printarNomeLoaded, lstIdsReg) # param['asset_rois_grid1'],
    # sys.exit()
    if len(lstFails) > 0:
        listaGrid_fails += lstFails
    name_export = 'rois_fromGrade_' + nbacia 
    # print(f"==== bacia {nbacia}==== <{featROIsreg.size().getInfo()}> ======")
    # print(featROIsreg.aggregate_histogram('class').getInfo())
    # dictROIsclass[nbacia] = featROIsreg.aggregate_histogram('class').getInfo()
    print(featROIsreg.aggregate_histogram('year').getInfo())
     # adding the before ROIs with natural class
    # assetROIsBasin = param['asset_roi_basins'] + '/' + name_export 
    # featBefROIs = ee.FeatureCollection(assetROIsBasin)
    # featROIsreg = featROIsreg.merge(featBefROIs)
    
    # save_ROIs_toAsset(featROIsreg, name_export)
    cont = gerenciador(cont)

# with open('dict_ROIs_basin_class_distribution.json', 'w') as arquivo_json:
#     json.dump(dictROIsclass, arquivo_json, indent=4)

# if len(listaGrid_fails) > 0:
#     df = pd.DataFrame(listaGrid_fails, columns=['idGrid', 'sizeSaved'])
#     df.to_csv('lista_gride_with_failsYearSavedv2.csv')
