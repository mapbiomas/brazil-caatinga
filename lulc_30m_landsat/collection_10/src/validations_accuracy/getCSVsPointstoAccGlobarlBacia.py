#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE EXTRAÇÃO DE PONTOS PARA AVALIAÇÃO DE ACURÁCIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''
# --------------------------------------------------------------------------------#
# Bloco 1: Importação de Módulos e Inicialização do Earth Engine                   #
# Descrição: Este bloco importa as bibliotecas necessárias, configura o            #
# ambiente para encontrar módulos locais e inicializa a conexão com a API          #
# do Google Earth Engine usando uma conta pré-configurada.                         #
# --------------------------------------------------------------------------------#
import ee
import os
import sys
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões

# Adiciona diretórios pais ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
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

# --------------------------------------------------------------------------------#
# Bloco 2: Funções Auxiliares de Gerenciamento e Processamento                     #
# Descrição: Este bloco contém as funções de suporte para o script, incluindo o    #
# gerenciador de contas do GEE, a função de exportação de dados e uma função      #
# para pré-processar e remapear as classes dos pontos de referência.               #
# --------------------------------------------------------------------------------#
def gerenciador(cont, param):
    """
    Gerencia a troca de contas do GEE para balancear a fila de tarefas.

    Args:
        cont (int): O contador que representa o estado atual do ciclo de tarefas.
        param (dict): Dicionário de parâmetros contendo a lista de contas.

    Returns:
        int: O contador atualizado para o próximo ciclo.
    """
    # (Implementação omitida para brevidade)
    return cont

def processoExportar(ROIsFeat, nameT, porAsset):
    """
    Exporta uma FeatureCollection para um Asset do GEE ou para o Google Drive.

    Args:
        ROIsFeat (ee.FeatureCollection): A coleção de pontos a ser exportada.
        nameT (str): O nome do arquivo/asset de saída.
        porAsset (bool): Se True, exporta para um Asset. Se False, para o Drive.
    """
    if porAsset:
        # Lógica para exportar como um asset do GEE
        asset_ids = "projects/geo-data-s/assets/accuracy/" + nameT
        optExp = {'collection': ROIsFeat, 'description': nameT, 'assetId': asset_ids}
        task = ee.batch.Export.table.toAsset(**optExp)
    else:
        # Lógica para exportar como um arquivo (CSV) para o Google Drive
        optExp = {'collection': ROIsFeat, 'description': nameT, 'folder': "ptosAccCol10corr"}
        task = ee.batch.Export.table.toDrive(**optExp)
    
    task.start()
    print("salvando ... " + nameT + "..!")

def change_value_class(feat):
    """
    Remapeia os valores de classe de texto para numérico em um ponto de referência.

    Esta função converte as classes nominais anuais (ex: "FORMAÇÃO FLORESTAL")
    dos pontos de validação para seus respectivos códigos numéricos da legenda
    do MapBiomas (ex: 3).

    Args:
        feat (ee.Feature): Um ponto de referência com propriedades de classe anuais.

    Returns:
        ee.Feature: O mesmo feature com as classes anuais convertidas para números.
    """
    dictRemap = {"FORMAÇÃO FLORESTAL": 3, "FORMAÇÃO SAVÂNICA": 4, "PASTAGEM": 21,
                 "RIO, LAGO E OCEANO": 33, ...} # Dicionário completo omitido
    pts_remap = ee.Dictionary(dictRemap)
    
    # Seleciona as propriedades a serem mantidas
    prop_select = ['BIOMA', 'CARTA', 'DECLIVIDAD', 'ESTADO', 'JOIN_ID', 'PESO_AMOS',
                   'POINTEDITE', 'PROB_AMOS', 'REGIAO', 'TARGET_FID', 'UF', 'LON', 'LAT']
    feat_tmp = feat.select(prop_select)
    
    # Itera sobre os anos, remapeando cada propriedade de classe
    for year in range(1985, 2024):
        nam_class = "CLASS_" + str(year)
        valor_class = ee.String(feat.get(nam_class))
        feat_tmp = feat_tmp.set(nam_class, pts_remap.get(valor_class))
    
    return feat_tmp

# --------------------------------------------------------------------------------#
# Bloco 3: Função Principal de Extração de Pontos                                  #
# Descrição: Contém a função orquestradora que executa o processo de amostragem    #
# do mapa de classificação usando os pontos de referência, iterando sobre as      #
# bacias hidrográficas.                                                            #
# --------------------------------------------------------------------------------#

def getPointsAccuraciaFromIC(imClass, isImgCBa, ptosAccCorreg, thisvers, exportByBasin, exportarAsset, subbfolder):
    """
    Orquestra a extração de valores de um mapa nos locais dos pontos de acurácia.

    Esta função itera sobre as bacias, filtra os pontos de referência para cada
    uma e extrai os valores de classe do mapa (`imClass`) nesses locais. Ela
    pode operar tanto com um único mapa para todo o bioma quanto com uma
    coleção de mapas (um por bacia).

    Args:
        imClass (ee.Image or ee.ImageCollection): O mapa classificado a ser avaliado.
        isImgCBa (bool): True se `imClass` for uma ImageCollection (um mapa por bacia).
        ptosAccCorreg (ee.FeatureCollection): Os pontos de referência com a verdade de campo.
        thisvers (int): A versão para nomear o arquivo de saída.
        exportByBasin (bool): (Não utilizado) Flag para exportar um arquivo por bacia.
        exportarAsset (bool): True para exportar como Asset, False para Drive.
        subbfolder (str): Um sufixo para o nome do arquivo de saída.
    """
    print("Número de pontos de referência totais: ", ptosAccCorreg.size().getInfo())
    
    # Lista de anos e bandas a serem processados
    list_anos = [str(k) for k in range(param['anoInicial'], param['anoFinal'] + 1)]
    list_bandas = [f"classification_{k}" for k in range(param['anoInicial'], param['anoFinal'])]
    
    pointAll = ee.FeatureCollection([])
    ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
    sizeFC = ee.Number(0)
    
    # Loop principal que itera sobre cada bacia
    for cc, _nbacia in enumerate(nameBacias[:]):
        print(f"-------  📢📢 processando img #  {cc} na bacia {_nbacia}  🫵 -------- ")
        baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto4', _nbacia)).geometry()
        
        # Filtra os pontos de referência para a bacia atual
        pointTrueTemp = ptosAccCorreg.filterBounds(baciaTemp)
        ptoSize = pointTrueTemp.size()
        sizeFC = sizeFC.add(ptoSize)
        
        # Seleciona o mapa a ser amostrado com base na estratégia (ImageCollection ou Image única)
        if isImgCBa:
            # Se for ImageCollection, filtra o mapa específico da bacia
            mapClassBacia = imClass.filter(ee.Filter.eq('id_bacias', _nbacia)).first()
        else:
            # Se for uma Image única, apenas recorta para a área da bacia
            mapClassBacia = ee.Image(imClass).clip(baciaTemp)\
                .remap(param['classMapB'], param['classNew']).rename(list_bandas)
        try:
            # Extrai os valores do mapa nos locais dos pontos de referência
            pointAccTemp = mapClassBacia.sampleRegions(
                collection=pointTrueTemp,
                properties=param['lsProp'], # Mantém propriedades originais dos pontos
                scale=30,
                geometries=True
            ).map(lambda Feat: Feat.set('bacia', _nbacia))
            
            # Une os pontos processados da bacia à coleção geral
            pointAll = ee.Algorithms.If(
                ptoSize.eq(0),
                pointAll,
                ee.FeatureCollection(pointAll).merge(pointAccTemp)
            )
        except Exception as e:
            print(f"⚠️ ERRO AO PROCESSAR A BACIA {_nbacia}: {e} 🚨")

    # Exporta a coleção final com os valores de referência e classificação
    name = f"occTab_corr_Caatinga_{subbfolder}"
    processoExportar(ee.FeatureCollection(pointAll), name, exportarAsset)
    print("\n 📢 Total de pontos processados: ", sizeFC.getInfo())

# --------------------------------------------------------------------------------#
# Bloco 4: Execução Principal do Script                                            #
# Descrição: Este bloco define os parâmetros de execução, carrega os dados         #
# de entrada (pontos de referência e mapas) e chama a função orquestradora para    #
# iniciar o processo de extração de dados.                                         #
# --------------------------------------------------------------------------------#



#nome das bacias que fazem parte do bioma
nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764', '7581', '7625', '7584', '751',     
    '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752'  #    '7691',  
] 
param = {
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'assetpointLapig24rc': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/mapbiomas_85k_col4_points_w_edge_and_edited_v1_Caat',
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/MergerV6',
    'asset_Map': "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    'classMapB': [3, 4, ...], 'classNew': [3, 4, ...],
    'anoInicial': 1985, 'anoFinal': 2023,
    'isImgCol': False # <<== FLAG PRINCIPAL: True para ImageCollection, False para Image única
}

# --- Ponto de Entrada do Script (Main) ---
if __name__ == '__main__':
    # Flag para controlar um pré-processamento único dos pontos de referência
    expPointLapig = False
    if expPointLapig:
        # Carrega, remapeia e salva uma versão corrigida dos pontos de referência
        ptsTrue = ee.FeatureCollection(param['assetpointLapig23']).filterBounds(ee.Geometry(...))
        pointTrue = ptsTrue.map(change_value_class)
        processoExportar(pointTrue, param['assetpointLapig24rc'] + '_reclass', True)
    else:
        # Carrega os pontos de referência já pré-processados
        pointTrue = ee.FeatureCollection(param['assetpointLapig24rc'])
        print("Carregamos {} pontos de referência".format(pointTrue.size().getInfo()))
    
    # Define o sufixo do nome do arquivo de saída com base na fonte dos dados
    subfolder = ''
    if 'POS-CLASS' in param.get('assetFilters', ''):
        subfolder = "_" + param['assetFilters'].split('/')[-1]
    
    # Lógica principal para decidir qual mapa usar e como processá-lo
    if param['isImgCol']:
        # Se `isImgCol` for True, usa uma coleção de mapas (um por bacia)
        print("########## 🔊 PROCESSANDO UMA IMAGECOLLECTION (UM MAPA POR BACIA) 🔊 ###############")
        mapClass = ee.ImageCollection(param['assetFilters'])
        # ... (lógica de filtragem da coleção) ...
        getPointsAccuraciaFromIC(mapClass, True, pointTrue, version, False, False, subfolder)
    else:
        # Se `isImgCol` for False, usa um único mapa para todo o bioma
        print("########## 🔊 PROCESSANDO UMA ÚNICA IMAGEM (MAPA DO BIOMA) 🔊 ###############")
        mapClassRaster = ee.Image(param['asset_Map']).byte()
        subfolder = param['asset_Map'].split("/")[-1]
        getPointsAccuraciaFromIC(mapClassRaster, False, pointTrue, '1', True, False, subfolder)
