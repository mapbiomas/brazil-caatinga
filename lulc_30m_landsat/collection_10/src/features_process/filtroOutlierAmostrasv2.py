
#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
# cluster [WEKA CobWb ] == > https://link.springer.com/content/pdf/10.1007/BF00114265.pdf
'''

# --------------------------------------------------------------------------
# Bloco 1: Importação de Módulos e Inicialização do Earth Engine
# Descrição: Este bloco importa as bibliotecas necessárias, configura o
# ambiente para encontrar módulos locais e inicializa a conexão com a API
# do Google Earth Engine usando uma conta pré-configurada.
# --------------------------------------------------------------------------
import ee
import sys
import arqParametros as arqParam
import collections
collections.Callable = collections.abc.Callable  # Garante compatibilidade com novas versões do Python

# Adiciona o diretório pai ao path do sistema para importar módulos customizados
from pathlib import Path
import os
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)

# Importa funções para gerenciamento de contas e ferramentas do GEE
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
# Bloco 2: Definição de Parâmetros Globais
# Descrição: Este dicionário 'params' centraliza todas as configurações
# do script, como caminhos de assets, hiperparâmetros para os algoritmos
# de cluster e classificação, e informações para gerenciamento de contas.
# --------------------------------------------------------------------------
params = {
    'assetBacia': 'users/diegocosta/baciasRecticadaCaatinga',
    'assetROIs': {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalv2'},
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalClusterv2/',
    'pmtClustLVQ': {'numClusters': 6, 'learningRate': 0.0001, 'epochs': 800},
    'splitRois': 0.8,
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta': {
        '0': 'caatinga01', '5': 'caatinga02', '10': 'caatinga03',
        '15': 'caatinga04', '20': 'caatinga05', '25': 'solkan1201',
        '27': 'diegoGmail', '30': 'rodrigo', '34': 'Rafael'
    },
    'pmtRF': {
        'numberOfTrees': 60, 'variablesPerSplit': 6, 'minLeafPopulation': 3,
        'maxNodes': 10, 'seed': 0
    }
}

# Define a lista de anos e bacias para o processamento
list_anos = [k for k in range(1985, 2019)]
lsNamesBacias = arqParam.listaNameBacias
lsBacias = ee.FeatureCollection(params['assetBacia'])

# Define as bandas que serão usadas no treinamento do clusterizador
bandNames = [
    'median_gcvi', 'median_gcvi_dry', 'median_gcvi_wet', 'median_gvs', 'median_gvs_dry', 'median_gvs_wet',
    'median_hallcover', 'median_ndfi', 'median_ndfi_dry', 'median_ndfi_wet', 'median_ndvi', 'median_ndvi_dry',
    'median_ndvi_wet', 'median_nir_dry', 'median_nir_wet', 'median_savi_dry', 'median_savi_wet', 'median_swir1',
    'median_swir2', 'median_swir1_dry', 'median_swir1_wet', 'median_swir2_dry', 'median_swir2_wet', 'median_nir',
    'median_pri', 'median_red', 'median_savi', 'median_evi2', 'min_nir', 'min_red', 'min_swir1', 'min_swir2',
    'median_fns_dry', 'median_ndwi_dry', 'median_evi2_dry', 'median_sefi_dry', 'median_ndwi', 'median_red_dry',
    'median_wefi_wet', 'median_ndwi_wet'
]

# --------------------------------------------------------------------------
# Bloco 3: Funções Auxiliares e de Processamento
# Descrição: Este bloco contém as funções que encapsulam a lógica principal
# do script, como gerenciamento de tarefas, exportação de dados, coleta de
# amostras e a seleção do cluster principal.
# --------------------------------------------------------------------------

def gerenciador(cont):
    """Gerencia a troca de contas do GEE para balancear a fila de tarefas.

    A função verifica se o contador atingiu um limiar para trocar de conta
    e, em caso afirmativo, muda para o próximo usuário da lista para evitar
    o bloqueio por excesso de tarefas simultâneas.

    Args:
        cont (int): O contador que representa o estado atual do ciclo de tarefas.

    Returns:
        int: O contador atualizado para o próximo ciclo.
    """
    numberofChange = [kk for kk in params['conta'].keys()]

    if str(cont) in numberofChange:
        # Troca para a conta GEE especificada
        switch_user(params['conta'][str(cont)])
        ee.Initialize(project=get_project_from_account(params['conta'][str(cont)]))
        # Lista as tarefas ativas na conta atual
        tasks(n=params['numeroTask'], return_list=True)

    elif cont > params['numeroLimit']:
        cont = 0

    cont += 1
    return cont

def saveToAsset(collection, name):
    """Exporta uma FeatureCollection para um asset no Google Earth Engine.

    Args:
        collection (ee.FeatureCollection): A coleção de features a ser exportada.
        name (str): O nome do asset de saída (geralmente o ID da bacia).
    """
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': params['outAsset'] + name
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando ROIs da bacia {} ...!".format(name))

def GetPolygonsfromFolder(NameBacias):
    """Coleta e une todas as amostras (ROIs) de uma bacia específica.

    A função varre um diretório de assets no GEE, identifica todos os arquivos
    que pertencem à bacia informada e os une em uma única FeatureCollection.

    Args:
        NameBacias (str): O código ou nome da bacia cujas amostras serão coletadas.

    Returns:
        ee.FeatureCollection: Uma coleção contendo todas as amostras da bacia.
    """
    getlistPtos = ee.data.getList(params['assetROIs'])
    ColectionPtos = ee.FeatureCollection([])

    for idAsset in getlistPtos:
        path_ = idAsset.get('id')
        lsFile = path_.split("/")
        name = lsFile[-1]
        newName = name.split('_')

        # Verifica se o nome do asset corresponde à bacia de interesse
        if newName[0] == NameBacias:
            print(path_)
            FeatTemp = ee.FeatureCollection(path_)
            ColectionPtos = ColectionPtos.merge(FeatTemp)

    return ee.FeatureCollection(ColectionPtos)

def selectClassClusterAgrupado(dictFeat):
    """Identifica o cluster com o maior número de amostras em um histograma.

    Esta função é usada para encontrar o cluster mais representativo (outlier)
    após o processo de clusterização.

    Args:
        dictFeat (dict): Um dicionário onde as chaves são os IDs dos clusters e
                         os valores são a contagem de pontos em cada um.

    Returns:
        int or str: O ID do cluster que contém o maior número de pontos.
    """
    keyC = 0
    maxC = 0
    for kk, vv in dictFeat.items():
        if vv > maxC:
            maxC = vv
            keyC = kk
    print("Os cluster com maiores valores são <- {} -> ".format(keyC))
    return keyC

# --------------------------------------------------------------------------
# Bloco 4: Execução Principal do Script (Main)
# Descrição: Este é o ponto de entrada do script. Ele lê um arquivo de
# registro para saber quais bacias já foram processadas, e então inicia o
# loop principal que itera sobre cada bacia e ano para realizar o processo
# de limpeza de amostras via clusterização.
# --------------------------------------------------------------------------

# Abre os arquivos de registro para leitura e escrita
arqFeitos = open("registros/lsBaciasROIsfeitasBalanCluster3.txt", 'r')
baciasFeitas = []
for ii in arqFeitos.readlines():
    ii = ii.strip() # Remove quebras de linha
    baciasFeitas.append(ii)
arqFeitos.close() # Fecha o arquivo após a leitura

arqFeitos = open("registros/lsBaciasROIsfeitasBalanCluster3.txt", 'a+')
arqRelatorio = open("registros/Relatorio Cluster Outlier3.txt", 'a+')
cont = 0

# Loop principal para processar cada bacia hidrográfica
for nbacias in lsNamesBacias:

    # Pula a bacia se ela já estiver no registro de bacias concluídas
    if nbacias not in baciasFeitas:
        texto = " procesando a bacia " + nbacias
        print(texto)
        arqRelatorio.write(texto + '\n')

        # Coleta todas as amostras para a bacia atual
        ROIsTemp = GetPolygonsfromFolder(nbacias)
        colecaoPontos = ee.FeatureCollection([])

        # Itera sobre cada ano para processar as amostras anualmente
        for _ano in list_anos:
            texto = "ano: " + str(_ano)
            print(texto)
            arqRelatorio.write(texto + '\n')

            # Filtra as amostras para o ano corrente
            ROIsTempA = ROIsTemp.filter(ee.Filter.eq('year', _ano))

            # Separa 80% dos dados para treinamento do clusterizador
            ROIsTempA = ROIsTempA.randomColumn('random')
            trainingROI = ROIsTempA.filter(ee.Filter.lt('random', params['splitRois']))

            histo = trainingROI.aggregate_histogram('class').getInfo()
            classROIs = list(histo.keys())
            
            # Treina o clusterizador WEKA LVQ com os dados de treinamento
            params['pmtClustLVQ']['numClusters'] = len(classROIs)
            CLVQ = ee.Clusterer.wekaLVQ(**params['pmtClustLVQ']).train(trainingROI.select(bandNames), bandNames)
            
            # Aplica o clusterizador a todas as amostras do ano
            newROIsTempA = ROIsTempA.cluster(CLVQ, 'newclass')
            texto = "iterando por classes"
            print(texto)
            arqRelatorio.write(texto + '\n')

            # Para cada classe original, identifica o cluster principal
            for cc in classROIs:
                itemClassRoi = newROIsTempA.filter(ee.Filter.eq("class", int(cc)))
                histoTemp = itemClassRoi.aggregate_histogram('newclass').getInfo()
                
                # Seleciona o ID do cluster com mais amostras
                selCC = selectClassClusterAgrupado(histoTemp)

                # Filtra e mantém apenas as amostras que pertencem ao cluster principal
                trainingROI = itemClassRoi.filter(ee.Filter.eq('newclass', int(selCC)))
                
                texto = "classe {} com {} ptos".format(cc, trainingROI.size().getInfo())
                print(texto)
                arqRelatorio.write(texto + '\n')

                # Adiciona os pontos filtrados à coleção final
                colecaoPontos = colecaoPontos.merge(trainingROI)

        # Salva a coleção de pontos filtrados/balanceados para a bacia inteira
        texto = "Salvando a bacia {}".format(nbacias)
        print(texto)
        arqRelatorio.write(texto + '\n')
        arqFeitos.write(nbacias + '\n')
        saveToAsset(colecaoPontos, str(nbacias))
        
        # Gerencia a troca de contas para a próxima iteração
        cont = gerenciador(cont)

# Fecha os arquivos de registro ao final do processo
arqFeitos.close()
arqRelatorio.close()
