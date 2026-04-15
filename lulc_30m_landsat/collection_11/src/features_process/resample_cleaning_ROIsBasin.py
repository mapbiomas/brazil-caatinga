#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee 
import sys
import os
import json
from pathlib import Path
from tqdm import tqdm
import pandas as pd
from tabulate import tabulate
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
print("ver >> ", pathparent)
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
from gee_tools import *
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

nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]

class make_resampling_cleaning(object):
    dictRemap = {
        '3': [[3,4,12], [1,0,0]],
        '4': [[3,4,12], [0,1,0]],
        '12': [[3,4,12], [0,0,1]],
        '15': [[15,18,21], [1,0,0]],
        '18': [[15,18,21], [0,1,0]],
        '21': [[15,18,21], [0,0,1]],
    }
    dictGroup = {
        'vegetation' : [3,4,12],
        'agropecuaria': [15,19,21],
        'outros': [22,25,33,29,36]
    } # 

    dictQtLimit = {
        '3': 5000,
        '4': 10000,
        '12': 3200,
        '15': 8000,
        '19': 3000,
        '21': 4000,
        '22': 3000,
        '25': 3000,
        '29': 2000,
        '33': 2000,
        '36': 1600
    }

    def __init__(self, path_Input, prefixo, nbasin, lstProcFails):
        self.name_basin = nbasin
        print(f"=======  we will process FeatureCollecton << {self.name_basin} << in asset ========= \n >>>>>>> ", path_Input)   
        self.processar = False 
        self.lstProcFails = lstProcFails
        self.asset_featc = os.path.join(path_Input, f'{prefixo}_{nbasin}')
        self.dir_featSel = os.path.join(pathparent, 'dados', 'feature_select_col11')
        self.make_dict_featSelect() 
        # self.dictProcFails = dictProcFails
        # lstKeysB = list(dictProcFails.keys())
        # if self.name_basin in lstKeysB:    
        #     self.dir_featSel = os.path.join(pathparent, 'dados', 'feature_select_col11')        
        #     self.make_dict_featSelect()            
        #     self.processar = True

        self.rate_learn = 0.1
        self.max_leaf_node = 50
                
        file_pathjson = os.path.join(pathparent, 'dados', 'FS_col11_json', f"feat_sel_{self.name_basin}.json") 
        # Open the file in write mode and save the dictionary as JSON
        with open(file_pathjson, 'w') as json_file:
            json.dump(self.dict_features, json_file, indent=4) # Using indent for pretty printing
            
    def downsamplesFC(self, dfOneClass, num_limit):
        lstNameProp = dfOneClass.first().propertyNames()
        dfOneClass = dfOneClass.randomColumn('random')
        dfOneClass = dfOneClass.filter(ee.Filter.lt('random', num_limit))
        return dfOneClass.select(lstNameProp)


    #exporta a imagem classificada para o asset
    def processoExportar(self, ROIsFeat, IdAssetnameB):
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


    def load_features_ROIs(self, make_complex, deletar_asset= False):
        
        pmtros_GTB= {
            'numberOfTrees': int(self.max_leaf_node), 
            'shrinkage': float(self.rate_learn),         
            'samplingRate': 0.45, 
            'loss': "LeastSquares",#'Huber',#'LeastAbsoluteDeviation', 
            'seed': int(0)
        }
        # if self.processar:
        # em self.asset_featc se guarda o asset do ROIs bacia a sere processado
        # dentro dessa FeatureCollection tem todos os anos de amostras agrupadas 
        fc_tmp = ee.FeatureCollection(self.asset_featc)     
        # nessa lista de   self.lstProcFails são salvas todas as possiveis saidas 
        # das featureCollections das ROIs      
        for idAssetOut in self.lstProcFails:
            nyear =  int(idAssetOut.split('/')[-1].split("_")[1])
            if deletar_asset:
                print(" deletando .... ", idAssetOut)
                ee.data.deleteAsset(idAssetOut)
            if make_complex:                               
                fcYY = fc_tmp.filter(ee.Filter.eq('year', int(nyear)))
                # print(f"we load {fcYY.size().getInfo()} samples ")
                feat_selected = self.dict_features[f'{self.name_basin}_{nyear}']['features'][:60]
                # print("features selected ", len(feat_selected))
                lsAllprop = fcYY.first().propertyNames().getInfo()
                bandas_imports = [featName for featName in lsAllprop if featName in feat_selected]
                print("bands importance ", len(bandas_imports))
                # print(bandas_imports)
                feaReSamples = ee.FeatureCollection([])            
                for tipo in list(self.dictGroup.keys()):
                    print(f"------ grupo {tipo} -----------------")
                    fcYYtipo = fcYY.filter(ee.Filter.inList('class', self.dictGroup[tipo]))
                    if tipo in ['vegetation', 'agropecuaria']:                             
                        dict_Class = ee.Dictionary(fcYYtipo.aggregate_histogram('class')).getInfo()
                        print('processing > ', self.dictGroup[tipo])
                        for nclass in list(dict_Class.keys()):
                            print("filter by class == ", nclass)
                            fcYYbyClass = fcYYtipo.remap(self.dictRemap[str(nclass)][0], self.dictRemap[str(nclass)][1], 'class') 
                            # treinamdo para amostras de duas classes 
                            classifierGTB = (ee.Classifier.smileGradientTreeBoost(**pmtros_GTB)
                                            .train(fcYYbyClass, 'class', bandas_imports)
                                            .setOutputMode('PROBABILITY'))
                            # classificando para a classe de valor 1
                            classROIsGTB = (fcYYbyClass.filter(ee.Filter.eq('class', 1))
                                                .classify(classifierGTB, 'label'))
                            # print("first feat classif ", classROIsGTB.size().getInfo())
                            
                            step = 5
                            for ii in range(20, 100, 10):
                                frac_inic = ii/100
                                frac_end = (ii + step)/100 
                                classROIsGTBf = (classROIsGTB.filter(
                                                    ee.Filter.And(
                                                        ee.Filter.gt('label', frac_inic),
                                                        ee.Filter.lte('label', frac_end)
                                                    )
                                                ))
                                sizeFilt = classROIsGTBf.size()# .getInfo()
                                num_limite = ee.Number(self.dictQtLimit[str(nclass)]).divide(ee.Number(sizeFilt))
                                
                                # if sizeFilt > self.dictQtLimit[str(nclass)]:                                
                                classROIsGTBf = ee.Algorithms.If(
                                                    ee.Algorithms.IsEqual(ee.Number(sizeFilt).gt(self.dictQtLimit[str(nclass)]), 1),
                                                    self.downsamplesFC(classROIsGTBf, num_limite), classROIsGTBf
                                            )                            
                                
                                classROIsGTBf = ee.FeatureCollection(classROIsGTBf).remap([1], [int(nclass)], 'class')
                                feaReSamples = feaReSamples.merge(classROIsGTBf)
                    else:
                        print('processing > ', self.dictGroup[tipo])
                        feaReSamples = feaReSamples.merge(fcYYtipo)

                
                
                self.processoExportar(feaReSamples, idAssetOut ) # f'{self.name_basin}_{nyear}_cd'
            else:
                # if nyear in self.dictProcFails[self.name_basin]:
                fcYY = fc_tmp.filter(ee.Filter.eq('year', nyear))
                print("histograma de classe ", fcYY.aggregate_histogram('class').getInfo())
                feaReSamples = ee.FeatureCollection([]) 
                classROIsSel = None
                for nclass in [4, 15, 21]:
                    print("filter by class == ", nclass)
                    classROIs = fcYY.filter(ee.Filter.eq('class', nclass))
                    sizeFilt = classROIs.size().getInfo()
                    if sizeFilt > 5:
                        num_limite = ee.Number(self.dictQtLimit[str(nclass)]).divide(ee.Number(sizeFilt))
                        classROIsSel = self.downsamplesFC(classROIs, num_limite)
                        feaReSamples = feaReSamples.merge(ee.FeatureCollection(classROIsSel))

                outros =  [3,12,18,22,29,33]
                classROIsSel = fcYY.filter(ee.Filter.inList('class', outros))
                feaReSamples = feaReSamples.merge(ee.FeatureCollection(classROIsSel))              
                feaReSamples = feaReSamples.map(lambda feat: feat.set('class', ee.Number.parse(feat.get('class')).toFloat()))
                self.processoExportar(feaReSamples, idAssetOut)

        # else:
        #     print(f"---- Bacia {self.name_basin} foi processada em todos os anos -----")    

def GetPolygonsfromFolder(dict_folder):
    # print("lista de classe ", lstClasesBacias)
    getlistPtos = ee.data.listAssets(dict_folder['id'])
    assets_lista = getlistPtos['assets']
    # declarar lista para guardar cada um dos assets
    lst_asset = []

    for idAsset in assets_lista:
        path_ = idAsset['id']
        # print(path_)
        lst_asset.append(path_)    
    
    return  lst_asset

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


def get_dict_ROIs_fails(lstIdAssets):
    dict_basinYY = {}
    # levantamento dos ROIs feitos 
    for idAsset in tqdm(lstIdAssets):
        nameROIs = idAsset.split("/")[-1]
        partes = nameROIs.split("_")
        nbacia = partes[0]
        nyear = partes[1]
        lstKeys = list(dict_basinYY.keys())
        if nbacia in lstKeys:
            mylist = dict_basinYY[nbacia]
            mylist.append(int(nyear))
            dict_basinYY[nbacia] = mylist
        else:
            dict_basinYY[nbacia] = [int(nyear)]

    #Levantamento dos ROIs que faltam 
    dict_basinYYfails = {}
    lstBacias = list(dict_basinYY.keys())
    for nbacia in nameBacias:
        if nbacia not in lstBacias:
            dict_basinYYfails[nbacia] = [os.path.join(param["asset_output"], f'{nbacia}_{yyear}_cd') for yyear in list(range(1985, 2025))]
        else:
            # listando os falhos 
            lstFails = [os.path.join(param["asset_output"], f'{nbacia}_{yyear}_cd') for yyear in  range(1985, 2025) if yyear not in dict_basinYY[nbacia]]
            # registrando no dictionario 
            if len(lstFails) > 0:
                dict_basinYYfails[nbacia] = lstFails

    return dict_basinYYfails

def make_dict_ROIs_byClass(lstIdAssets):
    dictSamplesErrors = {}
    for id_asset in lstIdAssets:
        print(f'processing >> {id_asset}')
        feat_tmp = ee.FeatureCollection(id_asset)
        partes = id_asset.split("/")[-1].split("_")
        nbacia = partes[0]
        nyear = partes[1]
        dict_class = feat_tmp.aggregate_histogram('class').getInfo()
        print(f"samples from {nbacia} >> {nyear} :   {dict_class}")
        lstCClass = []
        amostras_float = True
        try:
            lstCClass =[int(cclas) for cclas in  list(dict_class.keys())]
            amostras_float = False
        except:
            lstCClass =[int(float(cclas)) for cclas in  list(dict_class.keys())]

        if 4 not in lstCClass or 15 not in lstCClass:
            dictSamplesErrors[f"{nbacia}_{nyear}"] = id_asset
        if not amostras_float:
            dictSamplesErrors[f"{nbacia}_{nyear}"] = id_asset

    return dictSamplesErrors


#================================= teste feito no code editor ========
# https://code.earthengine.google.com/c419b4781c6469fcedd46449245cbd40

param = {
    "asset_folder": {"id": "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_byBasinInd"},
    "asset_output": "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesv1CC",
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta' : {
        '0': 'caatinga01',   # 
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',
        '35': 'solkan1201',                  
        '42': 'solkanGeodatin',
        '50': 'superconta'   
    },
}
lstFeats = lst_columns = [
    'afvi_median', 'afvi_median_dry', 'afvi_median_wet',
    'avi_median', 'avi_median_dry', 'avi_median_wet', 'awei_median', 'awei_median_dry',
    'awei_median_wet', 'blue_median', 'blue_median_dry', 'blue_median_wet', 'brba_median',
    'brba_median_dry', 'brba_median_wet', 'brightness_median', 'brightness_median_dry',
    'bsi_median', 'bsi_median_1', 'bsi_median_2','brightness_median_wet',
    'co2flux_median', 'co2flux_median_dry', 'co2flux_median_wet',
    'cvi_median', 'cvi_median_dry', 'cvi_median_wet', 'dswi5_median', 'dswi5_median_dry',
    'dswi5_median_wet', 'evi_median', 'evi_median_dry', 'evi_median_wet', 'gcvi_median',
    'gcvi_median_dry', 'gcvi_median_wet', 'gemi_median', 'gemi_median_dry', 'gemi_median_wet',
    'gli_median', 'gli_median_dry', 'gli_median_wet', 'green_median', 'green_median_dry',
    'green_median_wet', 'gsavi_median', 'gsavi_median_dry', 'gsavi_median_wet', 'gv_median',
    'gv_median_dry', 'gv_median_wet', 'gvmi_median', 'gvmi_median_dry', 'gvmi_median_wet',
    'hillshade', 'iia_median', 'iia_median_dry', 'iia_median_wet', 'lswi_median',
    'lswi_median_dry', 'lswi_median_wet', 'mbi_median', 'mbi_median_dry', 'mbi_median_wet',
    'msavi_median', 'msavi_median_dry', 'msavi_median_wet', 'nbr_median', 'nbr_median_dry',
    'nbr_median_wet', 'ndbi_median', 'ndbi_median_dry', 'ndbi_median_wet', 'nddi_median',
    'nddi_median_dry', 'nddi_median_wet', 'ndfia', 'ndfia_1', 'ndfia_2',
    'ndmi_median', 'ndmi_median_dry', 'ndmi_median_wet', 'ndti_median', 'ndti_median_dry',
    'ndti_median_wet', 'ndvi_median', 'ndvi_median_dry', 'ndvi_median_wet', 'ndwi_median',
    'ndwi_median_dry', 'ndwi_median_wet', 'nir_median', 'nir_median_contrast', 'nir_median_dry',
    'nir_median_dry_contrast', 'nir_median_wet', 'npv_median', 'npv_median_dry', 'npv_median_wet',
    'osavi_median', 'osavi_median_dry', 'osavi_median_wet', 'ratio_median', 'ratio_median_dry',
    'ratio_median_wet', 'red_median', 'red_median_contrast', 'red_median_dry', 'red_median_dry_contrast',
    'red_median_wet', 'ri_median', 'ri_median_dry', 'ri_median_wet', 'rvi_median',
    'rvi_median_1', 'rvi_median_wet', 'shade_median', 'shade_median_dry', 'shade_median_wet',
    'shape_median', 'shape_median_dry', 'shape_median_wet', 'slope', 'soil_median',
    'soil_median_dry', 'soil_median_wet', 'swir1_median', 'swir1_median_dry', 'swir1_median_wet',
    'swir2_median', 'swir2_median_dry', 'swir2_median_wet', 'ui_median', 'ui_median_dry',
    'ui_median_wet', 'wetness_median', 'wetness_median_dry', 'wetness_median_wet'
]

lista_assets = GetPolygonsfromFolder(param['asset_folder'])
print(f" we loaded {len(lista_assets)} asset from folder < {param['asset_folder']['id'].split('/')[-1]} >")
# print(lista_assets[:3])

# dictProcs = get_dict_ROIs_fails(lista_assets)
# cc = 0
# for kkey, lstV in dictProcs.items():
#     print(cc,kkey, lstV)
#     cc += 1
# sys.exit()
lstBaciaSaveFail = False
makedictErro = False
lista_assetsF = GetPolygonsfromFolder({'id': param['asset_output']})
print(f" we loaded {len(lista_assetsF)} assets ROIs cleanes from folder < {param['asset_output'].split('/')[-1]} >")
if len(lista_assetsF):
    print(lista_assetsF)
# sys.exit()
if lstBaciaSaveFail:
    dictFailsProcs = get_dict_ROIs_fails(lista_assetsF)
    cc = 0
    for kkey, id_asset in dictFailsProcs.items():
        print(f"#{cc} {kkey} with {len(id_asset)} assets faltantes ")
        print(id_asset[0])
        cc += 1
else:
    if makedictErro:
        dictFailsProcs = make_dict_ROIs_byClass(lista_assetsF)
        with open('dict_basin_year_ROIs_byClass.json', 'w') as arquivo_json:
            json.dump(dictFailsProcs, arquivo_json, indent=4)
        print("dictionary saved as dict_basin_year_ROIs_byClass.json")
        cc = 0
        for kkey, id_asset in dictFailsProcs.items():
            print(f"#{cc} {kkey} with {id_asset} assets faltantes ")
            cc += 1
    else:
        with open('dict_basin_year_ROIs_byClass.json', 'r') as arquivo_json:
            dictFailsProcs = json.load(arquivo_json)
        print("dictionary readed as dict_basin_year_ROIs_byClass.json")


# sys.exit()
acount = gerenciador(1)

if lstBaciaSaveFail:
    cc = 0
    for nameBacia, id_assets in dictFailsProcs.items():     
        print(id_assets[0])   
        print(f"#{cc}  >>> {nameBacia}  >> {len(id_assets)}")
        # sys.exit()
        if cc > -1 : 
            resampled_cleaned = make_resampling_cleaning(param["asset_folder"]["id"], "rois_grade", nameBacia, id_assets)
            # processar = resampled_cleaned.processar
            # if processar:
            metodo_complexo = True
            resampled_cleaned.load_features_ROIs(metodo_complexo)
        cc += 1
        # acount = gerenciador(acount)

else:
    cc = 0
    newDictProc = {}
    for kkey, id_asset in dictFailsProcs.items():
        print(f"#{cc} {kkey} with {id_asset.replace('projects/earthengine-legacy/assets/' + param['asset_output'], '')} assets faltantes ")
        if cc > -1 : 
            nameBacia = id_asset.split('/')[-1].split("_")[0]
            if nameBacia ==  '':  # 7712
                feat_tmp = ee.FeatureCollection(id_asset)
                dict_class = feat_tmp.aggregate_histogram('class').getInfo()
                print(f"samples from {nameBacia}  :   {dict_class}")

            lstNbacias = list(newDictProc.keys())
            if nameBacia in lstNbacias:
                lst_tmp = newDictProc[nameBacia]
                lst_tmp.append(id_asset) 
                newDictProc[nameBacia] = lst_tmp
            else:
                newDictProc[nameBacia] = [id_asset]

        cc += 1

    # print(newDictProc)
    # sys.exit()
    # processando por Bacias 
    
    cc = 0
    for nameBacia, id_assets in newDictProc.items(): 
        print(f"#{cc}  >>> {nameBacia}  >> {len(id_assets)}")
        if cc > -1 : 
            resampled_cleaned = make_resampling_cleaning(param["asset_folder"]["id"], "rois_grade", nameBacia, id_assets)
            metodo_complexo = False
            resampled_cleaned.load_features_ROIs(metodo_complexo, True)

        cc += 1