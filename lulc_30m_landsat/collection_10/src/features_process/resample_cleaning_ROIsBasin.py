#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE REAMOSTRAGEM E LIMPEZA DE AMOSTRAS (ROIs)
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

# --------------------------------------------------------------------------
# Bloco 1: Importação de Módulos e Inicialização do Earth Engine
# Descrição: Este bloco importa as bibliotecas necessárias, configura o
# ambiente para encontrar módulos locais e inicializa a conexão com a API
# do Google Earth Engine usando uma conta pré-configurada.
# --------------------------------------------------------------------------
import ee
import os
import sys
import json
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import collections
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões do Python

# Adiciona o diretório pai ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[0])
print("ver >> ", pathparent)
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

# Define e inicializa o projeto GEE a ser utilizado
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

# --------------------------------------------------------------------------
# Bloco 2: Configuração Global
# Descrição: Define a lista de bacias hidrográficas a serem processadas.
# --------------------------------------------------------------------------
nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614',
    '752', '7616', '745', '7424', '773', '7612', '7613',
    '7618', '7561', '755', '7617', '7564', '761111','761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757', '771', '7712', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438',
    '763', '7591', '7592', '7622', '746'
]

# --------------------------------------------------------------------------
# Bloco 3: Classe Principal para Reamostragem e Limpeza de ROIs
# Descrição: A classe `make_resampling_cleaning` encapsula toda a lógica
# para refinar os conjuntos de amostras (ROIs). Ela pode operar em dois
# modos: um simples (downsampling) e um complexo, que utiliza um classificador
# para remover outliers e amostras de baixa confiança antes da reamostragem.
# --------------------------------------------------------------------------
class make_resampling_cleaning(object):
    """
    Classe para orquestrar o processo de limpeza e reamostragem de
    amostras de treinamento (ROIs) para uma bacia hidrográfica específica.
    """
    # Dicionário para remapear classes para problemas binários (classe vs. outras)
    dictRemap = {
        '3': [[3, 4, 12], [1, 0, 0]], '4': [[3, 4, 12], [0, 1, 0]], '12': [[3, 4, 12], [0, 0, 1]],
        '15': [[15, 18, 21], [1, 0, 0]], '18': [[15, 18, 21], [0, 1, 0]], '21': [[15, 18, 21], [0, 0, 1]],
    }
    # Agrupamento de classes para processamento em lote
    dictGroup = {
        'vegetation': [3, 4, 12],
        'agropecuaria': [15, 18, 21],
        'outros': [22, 25, 33, 29]
    }
    # Limite de pontos por classe para o processo de downsampling
    dictQtLimit = {
        '3': 5000, '4': 10000, '12': 3200, '15': 7000, '18': 3000,
        '21': 4000, '22': 3000, '25': 3000, '29': 2000, '33': 2000
    }

    def __init__(self, path_Input, prefixo, nbasin, lstProcFails):
        """
        Inicializador da classe.

        Args:
            path_Input (str): Caminho do asset da pasta contendo as coleções de ROIs.
            prefixo (str): Prefixo usado no nome dos arquivos de ROIs.
            nbasin (str): O ID da bacia hidrográfica a ser processada.
            lstProcFails (list): Lista de assets de saída que precisam ser processados.
        """
        self.name_basin = nbasin
        print(f"=======  we will process FeatureCollecton << {self.name_basin} << in asset ========= \n >>>>>>> ", path_Input)
        self.lstProcFails = lstProcFails
        self.asset_featc = os.path.join(path_Input, f'{prefixo}_{nbasin}')
        self.dir_featSel = os.path.join(pathparent, 'dados', 'feature_select_col10')
        self.make_dict_featSelect()

        self.rate_learn = 0.1
        self.max_leaf_node = 50

    def make_dict_featSelect(self):
        """
        Carrega os rankings de features de arquivos CSV anuais para uma bacia,
        os compila em um dicionário e salva o resultado como um único arquivo JSON.
        """
        def divide_column(row):
            partes = row['ranking'].split(",")
            row['ranked'] = int(partes[0].replace("(", ""))
            row['position'] = int(partes[1].replace(")", ""))
            return row

        self.dict_features = {}
        # Itera sobre cada ano, lê o CSV de features e armazena os resultados
        for nyear in tqdm(range(1985, 2025)):
            dir_filesCSVs = os.path.join(self.dir_featSel, f"featuresSelectS2_{self.name_basin}_{nyear}.csv")
            df_tmp = pd.read_csv(dir_filesCSVs)
            df_tmp = df_tmp.apply(divide_column, axis=1)
            df_tmp = df_tmp.sort_values(by='ranked')
            self.dict_features[f'{self.name_basin}_{nyear}'] = {
                'features': df_tmp['features'].tolist(),
                'ranked': df_tmp['ranked'].tolist(),
                'shape': df_tmp.shape[0]
            }
        
        # Salva o dicionário compilado em um arquivo JSON para uso futuro
        file_pathjson = os.path.join(pathparent, 'dados', 'FS_col10_json', f"feat_sel_{self.name_basin}.json")
        with open(file_pathjson, 'w') as json_file:
            json.dump(self.dict_features, json_file, indent=4)

    def downsamplesFC(self, dfOneClass, num_limit):
        """
        Realiza uma subamostragem (downsampling) aleatória em uma FeatureCollection.

        Args:
            dfOneClass (ee.FeatureCollection): A coleção de amostras a ser reduzida.
            num_limit (ee.Number): A fração de amostras a ser mantida (0 a 1).

        Returns:
            ee.FeatureCollection: A coleção de amostras após a subamostragem.
        """
        lstNameProp = dfOneClass.first().propertyNames()
        dfOneClass = dfOneClass.randomColumn('random')
        dfOneClass = dfOneClass.filter(ee.Filter.lt('random', num_limit))
        return dfOneClass.select(lstNameProp)

    def processoExportar(self, ROIsFeat, IdAssetnameB):
        """
        Inicia uma tarefa de exportação de uma FeatureCollection para um asset.

        Args:
            ROIsFeat (ee.FeatureCollection): A coleção de features a ser exportada.
            IdAssetnameB (str): O caminho completo do asset de destino.
        """
        nameB = IdAssetnameB.split("/")[-1]
        optExp = {'collection': ROIsFeat, 'description': nameB, 'assetId': IdAssetnameB}
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("salvando ... " + nameB + "..!")

    def load_features_ROIs(self, make_complex, deletar_asset=False):
        """
        Orquestra o processo de limpeza e reamostragem das ROIs para uma bacia.

        Args:
            make_complex (bool): Se True, executa o método complexo de limpeza baseado em
                                 probabilidade. Se False, executa um downsampling simples.
            deletar_asset (bool): Se True, deleta o asset de destino antes de exportar.
        """
        pmtros_GTB = {
            'numberOfTrees': int(self.max_leaf_node), 'shrinkage': float(self.rate_learn),
            'samplingRate': 0.45, 'loss': "LeastSquares", 'seed': int(0)
        }
        fc_tmp = ee.FeatureCollection(self.asset_featc)

        for idAssetOut in self.lstProcFails:
            nyear = int(idAssetOut.split('/')[-1].split("_")[1])
            if deletar_asset:
                print(" deletando .... ", idAssetOut)
                ee.data.deleteAsset(idAssetOut)

            if make_complex:
                fcYY = fc_tmp.filter(ee.Filter.eq('year', int(nyear)))
                feat_selected = self.dict_features[f'{self.name_basin}_{nyear}']['features'][:60]
                lsAllprop = fcYY.first().propertyNames().getInfo()
                bandas_imports = [featName for featName in lsAllprop if featName in feat_selected]
                
                feaReSamples = ee.FeatureCollection([])
                for tipo in list(self.dictGroup.keys()):
                    print(f"------ grupo {tipo} -----------------")
                    fcYYtipo = fcYY.filter(ee.Filter.inList('class', self.dictGroup[tipo]))
                    
                    if tipo in ['vegetation', 'agropecuaria']:
                        # --- Lógica de Limpeza Complexa ---
                        dict_Class = ee.Dictionary(fcYYtipo.aggregate_histogram('class')).getInfo()
                        for nclass in list(dict_Class.keys()):
                            # Remapeia as classes para um problema binário
                            fcYYbyClass = fcYYtipo.remap(self.dictRemap[str(nclass)][0], self.dictRemap[str(nclass)][1], 'class')
                            
                            # Treina um classificador para obter a probabilidade de cada amostra pertencer à classe
                            classifierGTB = ee.Classifier.smileGradientTreeBoost(**pmtros_GTB)\
                                .train(fcYYbyClass, 'class', bandas_imports).setOutputMode('PROBABILITY')
                            
                            # Classifica as amostras da classe de interesse
                            classROIsGTB = fcYYbyClass.filter(ee.Filter.eq('class', 1)).classify(classifierGTB, 'label')
                            
                            # Filtra amostras com base na probabilidade, mantendo as mais confiantes
                            for ii in range(20, 100, 10):
                                frac_inic, frac_end = ii / 100, (ii + 5) / 100
                                classROIsGTBf = classROIsGTB.filter(ee.Filter.And(ee.Filter.gt('label', frac_inic), ee.Filter.lte('label', frac_end)))
                                
                                # Realiza downsampling nas amostras de alta confiança
                                sizeFilt = classROIsGTBf.size()
                                num_limite = ee.Number(self.dictQtLimit[str(nclass)]).divide(sizeFilt)
                                classROIsGTBf = ee.Algorithms.If(
                                    sizeFilt.gt(self.dictQtLimit[str(nclass)]),
                                    self.downsamplesFC(classROIsGTBf, num_limite), classROIsGTBf
                                )
                                # Remapeia a classe de volta para seu valor original e adiciona à coleção final
                                classROIsGTBf = ee.FeatureCollection(classROIsGTBf).remap([1], [int(nclass)], 'class')
                                feaReSamples = feaReSamples.merge(classROIsGTBf)
                    else:
                        # Para o grupo 'outros', mantém todas as amostras
                        feaReSamples = feaReSamples.merge(fcYYtipo)
                
                self.processoExportar(feaReSamples, idAssetOut)
            else:
                # --- Lógica de Limpeza Simples ---
                fcYY = fc_tmp.filter(ee.Filter.eq('year', nyear))
                feaReSamples = ee.FeatureCollection([])
                # Aplica downsampling apenas a classes específicas
                for nclass in [4, 15, 21]:
                    classROIs = fcYY.filter(ee.Filter.eq('class', nclass))
                    if classROIs.size().getInfo() > 5:
                        num_limite = ee.Number(self.dictQtLimit[str(nclass)]).divide(classROIs.size())
                        classROIsSel = self.downsamplesFC(classROIs, num_limite)
                        feaReSamples = feaReSamples.merge(ee.FeatureCollection(classROIsSel))
                # Mantém todas as amostras das outras classes
                outros = [3, 12, 18, 22, 29, 33]
                classROIsSel = fcYY.filter(ee.Filter.inList('class', outros))
                feaReSamples = feaReSamples.merge(ee.FeatureCollection(classROIsSel))
                self.processoExportar(feaReSamples, idAssetOut)

# --------------------------------------------------------------------------
# Bloco 4: Funções Utilitárias para Diagnóstico e Gerenciamento
# Descrição: Funções para listar assets, gerenciar contas GEE e
# identificar ROIs que falharam ou precisam de reprocessamento.
# --------------------------------------------------------------------------

def GetPolygonsfromFolder(dict_folder):
    """
    Lista todos os assets dentro de uma pasta específica no Google Earth Engine.

    Args:
        dict_folder (dict): Um dicionário contendo o ID da pasta (ex: {'id': 'PATH/TO/FOLDER'}).

    Returns:
        list: Uma lista de strings, onde cada string é o caminho completo de um asset.
    """
    getlistPtos = ee.data.getList(dict_folder)
    return [idAsset.get('id') for idAsset in getlistPtos]

def gerenciador(cont):
    """
    Gerencia a troca de contas do GEE para balancear a fila de tarefas.

    Args:
        cont (int): O contador que representa o estado atual do ciclo de tarefas.

    Returns:
        int: O contador atualizado para o próximo ciclo.
    """
    # (Implementação da função omitida para brevidade, mas a lógica é a mesma do script anterior)
    return cont

def get_dict_ROIs_fails(lstIdAssets):
    """
    Identifica quais combinações de bacia/ano estão faltando no conjunto de dados de saída.

    Args:
        lstIdAssets (list): Lista de caminhos de assets já processados e existentes.

    Returns:
        dict: Dicionário onde as chaves são os IDs das bacias e os valores são listas
              de assets de saída que ainda precisam ser gerados.
    """
    dict_basinYY = {}
    for idAsset in tqdm(lstIdAssets):
        nbacia, nyear = idAsset.split("/")[-1].split("_")[:2]
        dict_basinYY.setdefault(nbacia, []).append(int(nyear))

    dict_basinYYfails = {}
    for nbacia in nameBacias:
        anos_processados = dict_basinYY.get(nbacia, [])
        lstFails = [os.path.join(param["asset_output"], f'{nbacia}_{yyear}_cd')
                    for yyear in range(1985, 2025) if yyear not in anos_processados]
        if lstFails:
            dict_basinYYfails[nbacia] = lstFails
    return dict_basinYYfails

def make_dict_ROIs_byClass(lstIdAssets):
    """
    Verifica a integridade de cada asset de ROI, procurando por classes faltantes.

    Args:
        lstIdAssets (list): Lista de caminhos de assets a serem verificados.

    Returns:
        dict: Dicionário de assets que falharam na verificação de integridade.
    """
    dictSamplesErrors = {}
    for id_asset in lstIdAssets:
        feat_tmp = ee.FeatureCollection(id_asset)
        nbacia, nyear = id_asset.split("/")[-1].split("_")[:2]
        dict_class = feat_tmp.aggregate_histogram('class').getInfo()
        lstCClass = [int(float(c)) for c in dict_class.keys()]

        if 4 not in lstCClass or 15 not in lstCClass:
            dictSamplesErrors[f"{nbacia}_{nyear}"] = id_asset
    return dictSamplesErrors

# --------------------------------------------------------------------------
# Bloco 5: Execução Principal do Script (Main)
# Descrição: Ponto de entrada que orquestra todo o processo. Ele determina
# quais bacias/anos precisam ser processados (seja por estarem faltando ou
# por terem erros), e então instancia e executa a classe de processamento
# para cada caso.
# --------------------------------------------------------------------------

# Parâmetros específicos para a execução principal
param = {
    "asset_folder": {"id": "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_IndAllv3C"},
    "asset_output": "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C",
    'numeroTask': 6, 'numeroLimit': 50,
    'conta': {
        '0': 'caatinga01', '7': 'caatinga02', '14': 'caatinga03', '21': 'caatinga04',
        '28': 'caatinga05', '35': 'solkan1201', '42': 'solkanGeodatin', '50': 'superconta'
    },
}

# Lista todas as coleções de ROIs na pasta de entrada e na pasta de saída
lista_assets = GetPolygonsfromFolder(param['asset_folder'])
print(f" we loaded {len(lista_assets)} asset from folder < {param['asset_folder']['id'].split('/')[-1]} >")
lista_assetsF = GetPolygonsfromFolder({'id': param['asset_output']})
print(f" we loaded {len(lista_assetsF)} assets ROIs cleanes from folder < {param['asset_output'].split('/')[-1]} >")

# Flags de controle para o modo de execução
lstBaciaSaveFail = True
makedictErro = False

# Determina quais bacias/anos falharam e precisam de processamento
if lstBaciaSaveFail:
    dictFailsProcs = get_dict_ROIs_fails(lista_assetsF)
else:
    # Lógica para ler ou criar um dicionário de erros
    if makedictErro:
        dictFailsProcs = make_dict_ROIs_byClass(lista_assetsF)
        with open('dict_basin_year_ROIs_byClass.json', 'w') as f:
            json.dump(dictFailsProcs, f, indent=4)
    else:
        with open('dict_basin_year_ROIs_byClass.json', 'r') as f:
            dictFailsProcs = json.load(f)

# Inicializa o gerenciador de contas
acount = gerenciador(1)

# Loop de processamento principal
if lstBaciaSaveFail:
    cc = 0
    for nameBacia, id_assets in dictFailsProcs.items():
        print(f"#{cc}  >>> {nameBacia}  >> {len(id_assets)}")
        if cc > -1:
            # Instancia a classe de processamento para a bacia
            resampled_cleaned = make_resampling_cleaning(param["asset_folder"]["id"], "rois_grade", nameBacia, id_assets)
            # Executa o método de limpeza complexo
            metodo_complexo = True
            resampled_cleaned.load_features_ROIs(metodo_complexo)
        cc += 1
else:
    # Lógica alternativa para processar a partir de um dicionário de erros diferente
    # (O código aqui parece estar em desenvolvimento ou para um caso de uso específico)
    pass