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
import collections

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('✅ The Earth Engine package initialized successfully!')
except Exception as e:
    print(f"❌ Erro ao inicializar o GEE: {e}")
    sys.exit()


lstFeats = [
    'soil_median_dry', 'shade_median_dry', 'ratio_median_dry', 'gli_median_wet', 'pri_median_dry', 'dswi5_median_dry', 'osavi_median', 'npv_median_wet', 'gcvi_median_mean', 'shade_median', 'shape_median', 'soil_median', 'ndfia_median_dry', 'mbi_median_dry', 'bsi_median_stdDev', 'nbr_median', 'wetness_median_dry', 'ndfia_median_mean', 'ndfia_median', 'iia_median_wet', 'brba_median_dry', 'cloud_median', 'nir_median', 'lswi_median_wet', 'ndvi_median', 'slope', 'rvi_median', 'gcvi_median_dry', 'shape_median_dry', 'cvi_median_dry', 'blue_median_dry', 'mbi_median', 'nddi_median', 'avi_median_mean', 'ndfia_median_stdDev', 'gcvi_median_stdDev', 'swir2_median_wet', 'ui_median_wet', 'red_median_wet', 'avi_median', 'co2flux_median_wet', 'shade_median_wet', 'red_median_dry', 'gemi_median', 'osavi_median_dry', 'awei_median_mean', 'brba_median', 'cloud_median_wet', 'bsi_median_mean', 'nbr_median_dry', 'ratio_median', 'gli_median_dry', 'wetness_median', 'green_median_wet', 'brightness_median_wet', 'ndmi_median_dry', 'blue_median', 'msi_median_dry', 'evi_median', 'lswi_median_dry', 'ndti_median_dry', 'ui_median_stdDev', 'blue_median_wet', 'lai_median', 'lai_median_wet', 'cvi_median', 'spri_median_wet', 'shape_median_wet', 'dswi5_median_wet', 'afvi_median', 'ndwi_median', 'avi_median_wet', 'gli_median', 'evi_median_wet', 'nir_median_dry', 'gvmi_median', 'cvi_median_wet', 'ndvi_median_dry', 'ui_median_mean', 'iia_median', 'ndwi_median_dry', 'co2flux_median',  'msi_median_wet', 'osavi_median_wet', 'green_median_dry', 'pri_median', 'ui_median_dry', 'ndbi_median_wet', 'nbr_median_wet', 'nddi_median_wet', 'osavi_median_mean', 'swir1_median_wet', 'bsi_median', 'hillshade', 'swir1_median', 'swir2_median', 'gvmi_median_dry', 'rvi_median_dry', 'ndti_median', 'red_median', 'gemi_median_wet', 'lswi_median', 'brightness_median_dry', 'awei_median_wet', 'gndvi_median_wet', 'gv_median_dry', 'osavi_median_stdDev', 'ndti_median_wet', 'ndvi_median_wet', 'afvi_median_wet', 'spri_median', 'avi_median_stdDev', 'ndmi_median', 'nir_median_wet', 'evi_median_dry', 'bsi_median_dry', 'ndbi_median', 'ndwi_median_wet', 'ratio_median_wet', 'soil_median_wet', 'gcvi_median', 'ui_median', 'rvi_median_wet', 'nddi_median_dry', 'msi_median', 'npv_median', 'swir1_median_dry', 'pri_median_wet', 'ndbi_median_dry', 'avi_median_dry', 'gvmi_median_wet', 'wetness_median_wet', 'dswi5_median', 'spri_median_dry', 'awei_median', 'gndvi_median', 'lai_median_dry', 'gv_median',  'ndfia_median_wet', 'mbi_median_wet', 'gndvi_median_dry', 'brba_median_wet', 'gv_median_wet', 'ndmi_median_wet', 'npv_median_dry', 'awei_median_dry', 'gemi_median_dry', 'bsi_median_wet', 'cloud_median_dry', 'afvi_median_dry', 'gcvi_median_wet', 'iia_median_dry', 'brightness_median', 'awei_median_stdDev', 'green_median', 'co2flux_median_dry', 'swir2_median_dry'
]


nameBacias = [
    # '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    # '752', '7616', '745', '7424', '773', '7612', '7613', 
    # '7618', '7561', '755', '7617', '7564', '761111','761112', 
    # '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    # '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    # '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    # '763', '7591', '7592', '7622', '746'
    "7424","7612","7561","7617","7564","76116","7438"
]




class make_resampling_cleaning(object):

    dictGroup = {
        'vegetation' : [3, 4],
        'agropecuaria': [15, 21], # Adicionado 18 e 19 conforme uso de classes agro
        'outros': [12, 22, 25, 33, 29, 36, 19]
    } 

    # dictQtLimit = {
    #     '3': 5000, '4': 10000, '12': 3200, '15': 8000,
    #     '18': 8000, '19': 3000, '21': 4000, '22': 3000,
    #     '25': 3000, '29': 2000, '33': 2000, '36': 1600
    # }
    dictQtLimit = {
        '3': 600,  '4': 1300, '12': 300, '15': 1050,
        '18': 100, '19': 120, '21': 750, '22': 400, 
        '25': 400, '29': 200, '33': 100, '36': 120
    }
    def __init__(self, path_Input, path_Output, prefixo, nbasin, anos_processar): # lstProcFails
        self.name_basin = nbasin
        print(f"\n======= Processando FeatureCollecton << {self.name_basin} >> =======\n Asset: {path_Input.split('/')[-1]}")

        # self.lstProcFails = lstProcFails
        self.asset_featc     = os.path.join(path_Input,  f'{prefixo}_{nbasin}')
        self.asset_featc_out = os.path.join(path_Output, f'{prefixo}_{nbasin}')
        self.dir_featSel = os.path.join(pathparent, 'dados', 'FS_col11_json')
        
        self.rate_learn = 0.1
        self.max_leaf_node = 50

        # Substituímos o range engessado pela lista dinâmica
        self.anos_processar = anos_processar
        
        self.make_dict_featSelect() 

        print("================================================================================")
        
    def make_dict_featSelect(self):
        """Carrega ou simula o dicionário de features selecionadas."""
        file_pathjson = os.path.join(self.dir_featSel, f"feat_sel_{self.name_basin}.json") 
        # print(file_pathjson)
        # print("anem bacia ", self.name_basin)
        try:
            with open(file_pathjson, 'r') as file:
                self.dict_features = json.load(file)
                print(self.dict_features[f"{self.name_basin}_1985"]['features'])
        except:
            print(f"⚠️ Aviso: Arquivo de features \n === {file_pathjson} ==== \n não encontrado. Usando fallback vazio.")
            self.dict_features = {}

    def downsamplesFC(self, dfOneClass, num_limit):
        """Faz um downsample usando coluna randômica de forma performática."""
        return dfOneClass.randomColumn('random').filter(ee.Filter.lt('random', num_limit))

    def processoExportar(self, ROIsFeat, IdAssetnameB):
        """Agenda a tarefa de exportação para a nuvem do Google."""
        nameB = IdAssetnameB.split("/")[-1]
        optExp = {
            'collection': ROIsFeat, 
            'description': nameB, 
            'assetId': IdAssetnameB          
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start() 
        print(f"⏳ Tarefa agendada: salvando ... {nameB}!")    


    def filter_list_featureCol(self, listfeatImp):
        lst_tmp = []
        for ind in listfeatImp:
            if ind in lstFeats:
                lst_tmp.append(ind)

        return lst_tmp

    def load_features_ROIs(self, make_complex, deletar_asset=False, by_year= True):
        
        pmtros_GTB = {
            'numberOfTrees': int(self.max_leaf_node), 
            'shrinkage': float(self.rate_learn),         
            'samplingRate': 0.45, 
            'loss': "LeastSquares",
            'seed': int(0)
        }
             
        # print(fc_tmp.first().propertyNames().getInfo())    

        # for idAssetOut in self.lstProcFails:
        #     print("preocssing ", idAssetOut)

        #     nyear = int(idAssetOut.split('/')[-1].split("_")[1])
            
        #     if deletar_asset:
        #         print(f"🗑️ Deletando .... {idAssetOut}")
        #         try: 
        #             ee.data.deleteAsset(idAssetOut)
        #         except: 
        #             pass
        # sys.exit()
        # ITERA APENAS NOS ANOS FALTANTES PASSADOS PARA A CLASSE
        for nyear in self.anos_processar:
            print(f"\n>>>>>> PROCESSANDO APENAS O ANO FALTANTE: {nyear} <<<<<<")
            if by_year:            
                fcYY = ee.FeatureCollection(f"{self.asset_featc}_{nyear}")
            else:                
                fcYY = ee.FeatureCollection(self.asset_featc).filter(ee.Filter.eq('year', nyear))
            # Garante que o nome de saída aponte para asset_output
            idAssetOut = self.asset_featc_out + f'_{nyear}'

            if deletar_asset:
                print(f"🗑️ Checando/Deletando asset antigo .... {idAssetOut}")
                try: 
                    ee.data.deleteAsset(idAssetOut)
                except: 
                    pass

            if make_complex:                               
                # Busca as bandas seguras
                try:
                    feat_selected = self.dict_features[f'{self.name_basin}_{nyear}']['features'][:60]
                except:
                    # Fallback (caso JSON falhe) para não travar o loop
                    feat_selected = ['blue_median', 'red_median', 'nir_median', 'swir1_median', 'ndvi_median']
                    
                print(f"[{nyear}] Extraindo e Filtrando Probabilidades com GTB...")
                # print("size feature Collection ", len(feat_selected))
                feat_selected = self.filter_list_featureCol(feat_selected)
                # print("new size feature Collection ", len(feat_selected))
                # sys.exit()
                # LISTA MESTRA para armazenar os blocos (Achata a computação e evita .merge em loop)
                lista_feature_collections = [] 

                for tipo, classes_in_group in self.dictGroup.items():
                    print("run group ", tipo)
                    fcYYtipo = fcYY.filter(ee.Filter.inList('class', classes_in_group))

                    if tipo in ['vegetation', 'agropecuaria']:
                        # Verifica server-side se o grupo tem amostras suficientes para treinar
                        n_grupo = fcYYtipo.size().getInfo()
                        if n_grupo < 2:
                            print(f"  ⚠️ Grupo '{tipo}' vazio ou insuficiente ({n_grupo} amostras) — adicionando sem GTB.")
                            lista_feature_collections.append(fcYYtipo)
                            continue

                        # Para vegetation: se classe 3 < 50 OU classe 4 < 600 → passa tudo sem GTB
                        if tipo == 'vegetation':
                            n_cl3 = fcYYtipo.filter(ee.Filter.eq('class', 3)).size().getInfo()
                            n_cl4 = fcYYtipo.filter(ee.Filter.eq('class', 4)).size().getInfo()
                            if n_cl3 < 50 or n_cl4 < 600:
                                print(f"  ⚠️ Vegetation insuficiente (cl3={n_cl3}, cl4={n_cl4}) — passando tudo sem GTB.")
                                lista_feature_collections.append(fcYYtipo)
                                continue

                        for nclass in classes_in_group:
                            fcYYbyClass = fcYYtipo.map(lambda f: f.set('is_target',
                                ee.Algorithms.If(ee.Number(f.get('class')).eq(nclass), 1, 0)))

                            # Verifica se há amostras da classe-alvo para classificar
                            n_target = fcYYbyClass.filter(ee.Filter.eq('is_target', 1)).size().getInfo()
                            if n_target == 0:
                                print(f"  ⚠️ Classe {nclass} sem amostras em {nyear} — pulando GTB para essa classe.")
                                continue

                            # Treina o GTB para reconhecer apenas essa classe vs o resto do grupo
                            classifierGTB = (ee.Classifier.smileGradientTreeBoost(**pmtros_GTB)
                                            .train(fcYYbyClass, 'is_target', feat_selected)
                                            .setOutputMode('PROBABILITY'))

                            # Classifica apenas os pixels que REALMENTE SÃO dessa classe
                            classROIsGTB = (fcYYbyClass.filter(ee.Filter.eq('is_target', 1))
                                                .classify(classifierGTB, 'label'))

                            # Fatiamento de probabilidade achatado
                            for ii in range(20, 100, 10):
                                frac_inic = ii / 100.0
                                frac_end = (ii + 10) / 100.0

                                bin_fc = classROIsGTB.filter(
                                    ee.Filter.And(
                                        ee.Filter.gt('label', frac_inic),
                                        ee.Filter.lte('label', frac_end)
                                    )
                                )

                                limit = self.dictQtLimit.get(str(nclass), 2000)
                                sizeFilt = bin_fc.size()

                                bin_fc_sampled = ee.Algorithms.If(
                                    sizeFilt.gt(limit),
                                    self.downsamplesFC(bin_fc, ee.Number(limit).divide(sizeFilt)),
                                    bin_fc
                                )

                                lista_feature_collections.append(ee.FeatureCollection(bin_fc_sampled))
                    else:
                        # Para o grupo "outros", apenas junta sem filtro GTB
                        lista_feature_collections.append(fcYYtipo)
                # sys.exit()
                # TRUQUE 3: O achatamento final
                # Converte a lista do Python em uma lista do GEE e achata em uma única camada
                feaReSamples_Final = ee.FeatureCollection(lista_feature_collections).flatten()
                
                # Remove colunas temporárias geradas (limpa o asset final)
                feaReSamples_Final = feaReSamples_Final.select(fcYY.first().propertyNames())

                # idAssetOut =  self.asset_featc + f'_{nyear}' 
                self.processoExportar(feaReSamples_Final, idAssetOut)

            else:
                # ====== MÉTODO SIMPLES (make_complex = False) ======
                print(f"[{nyear}] Aplicando Método Simples (Downsample Direto)...")
                lista_fc_simples = []
                
                # classes_configuradas = [int(k) for k in self.dictQtLimit.keys()]
                classes_configuradas = self.dictQtLimit['vegetation'] + self.dictQtLimit['agropecuaria']
                
                for nclass in classes_configuradas:
                    classROIs = fcYY.filter(ee.Filter.eq('class', nclass))
                    
                    limit = self.dictQtLimit[str(nclass)]
                    sizeFilt = classROIs.size().max(1)
                    
                    # Mesma matemática limpa para o método simples
                    fracao_manter = ee.Number(limit).divide(sizeFilt).min(1.0)
                    
                    classROIsSel = (classROIs.randomColumn('rand_simples')
                                            .filter(ee.Filter.lt('rand_simples', fracao_manter)))
                    lista_fc_simples.append(classROIsSel)

                outras_classes = fcYY.filter(ee.Filter.inList('class', self.dictQtLimit['outros']))
                lista_fc_simples.append(outras_classes)
                
                feaReSamples = ee.FeatureCollection(lista_fc_simples).flatten()
                # feaReSamples = feaReSamples.map(lambda feat: feat.set('class', ee.Number.parse(feat.get('class')).toFloat()))
                
                self.processoExportar(feaReSamples, idAssetOut)


def GetPolygonsfromFolder(dict_folder):
    # print("lista de classe ", lstClasesBacias)
    getlistPtos = ee.data.listAssets(dict_folder)
    assets_lista = getlistPtos['assets']
    # declarar lista para guardar cada um dos assets
    lst_asset = []

    for idAsset in assets_lista:
        path_ = idAsset['id']
        # print(path_)
        lst_asset.append(path_)    
    
    return  lst_asset



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
            dict_basinYYfails[nbacia] = [os.path.join(param["asset_output"], f'{nbacia}_{yyear}_cd') for yyear in list(range(1985, 2026))]
        else:
            # listando os falhos 
            lstFails = [os.path.join(param["asset_output"], f'{nbacia}_{yyear}_cd') for yyear in  range(1985, 2026) if yyear not in dict_basinYY[nbacia]]
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
    "asset_folder": "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCred",
    "asset_output": "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCredv2",
}

lista_assets = GetPolygonsfromFolder(param['asset_folder'])
print(f" we loaded {len(lista_assets)} asset from folder < {param['asset_folder'].split('/')[-1]} >")
# print(lista_assets[:3])

# dictProcs = get_dict_ROIs_fails(lista_assets)
# cc = 0
# for kkey, lstV in dictProcs.items():
#     print(cc,kkey, lstV)
#     cc += 1
# sys.exit()
lstBaciaSaveFail = False
makedictErro = False
# lista_assetsF = GetPolygonsfromFolder({'id': param['asset_output']})
# print(f" we loaded {len(lista_assetsF)} assets ROIs cleanes from folder < {param['asset_output'].split('/')[-1]} >")
# if len(lista_assetsF):
#     print(lista_assetsF)
# sys.exit()
# if lstBaciaSaveFail:
#     dictFailsProcs = get_dict_ROIs_fails(lista_assetsF)
#     cc = 0
#     for kkey, id_asset in dictFailsProcs.items():
#         print(f"#{cc} {kkey} with {len(id_asset)} assets faltantes ")
#         print(id_asset[0])
#         cc += 1
# else:
#     if makedictErro:
#         dictFailsProcs = make_dict_ROIs_byClass(lista_assetsF)
#         with open('dict_basin_year_ROIs_byClass.json', 'w') as arquivo_json:
#             json.dump(dictFailsProcs, arquivo_json, indent=4)
#         print("dictionary saved as dict_basin_year_ROIs_byClass.json")
#         cc = 0
#         for kkey, id_asset in dictFailsProcs.items():
#             print(f"#{cc} {kkey} with {id_asset} assets faltantes ")
#             cc += 1
#     else:
#         with open('dict_basin_year_ROIs_byClass.json', 'r') as arquivo_json:
#             dictFailsProcs = json.load(arquivo_json)
#         print("dictionary readed as dict_basin_year_ROIs_byClass.json")

nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614',
    '752', '7616', '745', '7424', '773', '7612', '7613',
    '7618', '7561', '755', '7617', '7564', '761111','761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757', '771', '7712', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438',
    '763', '7591', '7592', '7622', '746'
]
# nameBacias = ['7422', '7443', '7544']

# ── Levanta o que já está salvo no asset_output ──────────────────────────────
print(f"Verificando assets já salvos em: {param['asset_output'].split('/')[-1]} ...")
try:
    lista_assets_output = GetPolygonsfromFolder(param['asset_output'])
except Exception:
    lista_assets_output = []

saved_set = set()
for caminho in lista_assets_output:
    nome = caminho.split('/')[-1]   # rois_fromBasin_7754_1985
    partes = nome.split('_')
    # partes: ['rois', 'fromBasin', '<bacia>', '<ano>']
    if len(partes) >= 4 and partes[1] == 'fromBasin':
        saved_set.add((partes[2], int(partes[3])))

print(f"  {len(saved_set)} assets já encontrados no output — serão pulados.")
# ─────────────────────────────────────────────────────────────────────────────

# 1. Definimos EXATAMENTE o que precisa ser processado
procelstYear = True
bacias_faltantes = {
    "7424": [2025],
    "7612": [2025],
    "7561": [2025],
    "7617": [2025],
    "7564": [2025],
    "76116": [2025],
    "7438": [2025]
}
if len(bacias_faltantes.keys()) > 0:
    procelstYear = False
processing_byYear = True
cc = 0
for cc, nameBacia in enumerate(nameBacias[:]):
    if procelstYear:
        lstYear = [y for y in range(1985, 2026) if (nameBacia, y) not in saved_set]
        if not lstYear:
            print(f"#{cc}  >>> {nameBacia}  — todos os anos já salvos, pulando.")
            continue
        print(f"#{cc}  >>> {nameBacia}  — {len(lstYear)} anos a processar: {lstYear}")
        resampled_cleaned = make_resampling_cleaning(param["asset_folder"], param["asset_output"], "rois_fromBasin", nameBacia, lstYear)
        metodo_complexo = True
        resampled_cleaned.load_features_ROIs(metodo_complexo, False, processing_byYear)

    else:
        if nameBacia in list(bacias_faltantes.keys()):
            lstYear = [y for y in bacias_faltantes[nameBacia] if (nameBacia, y) not in saved_set]
            if not lstYear:
                print(f"#{cc}  >>> {nameBacia}  — todos os anos já salvos, pulando.")
                continue
            print(f"#{cc}  >>> {nameBacia}  — {len(lstYear)} anos a processar: {lstYear}")
            resampled_cleaned = make_resampling_cleaning(param["asset_folder"], param["asset_output"], "rois_fromBasin", nameBacia, lstYear)
            metodo_complexo = True
            resampled_cleaned.load_features_ROIs(metodo_complexo, False, processing_byYear)

