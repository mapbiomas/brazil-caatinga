#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CÁLCULO DE ÁREA POR CLASSE E BACIA
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
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões

# Adiciona diretórios pais ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
print("parents ", pathparent)
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
# Bloco 2: Funções Principais de Cálculo de Área                                   #
# Descrição: Este bloco contém as funções centrais que executam o cálculo de      #
# área. A função `calculateArea` realiza a operação de baixo nível no GEE,         #
# enquanto `iterandoXanoImCruda` orquestra o processo, iterando sobre a série      #
# temporal para calcular a área para cada ano.                                     #
# --------------------------------------------------------------------------------#

def convert2featCollection(item):
    """
    Função auxiliar para formatar a saída do redutor `sum().group()`.

    Converte um dicionário retornado pelo redutor em um `ee.Feature` com as
    propriedades 'classe' e 'area'.

    Args:
        item (ee.Dictionary): O dicionário de entrada (ex: {'classe': 3, 'sum': 1234.5}).

    Returns:
        ee.Feature: Um feature sem geometria com as propriedades formatadas.
    """
    item = ee.Dictionary(item)
    return ee.Feature(None, {'classe': item.get('classe'), "area": item.get('sum')})

def calculateArea(image, pixelArea, geometry):
    """
    Calcula a área total para cada classe em uma imagem dentro de uma geometria.

    Utiliza o método `reduceRegion` com um redutor agrupado para somar as áreas
    de pixels para cada valor de classe único na imagem.

    Args:
        image (ee.Image): Uma imagem de banda única contendo as classes.
        pixelArea (ee.Image): Uma imagem onde cada pixel tem o valor de sua área.
        geometry (ee.Geometry): A região de interesse para o cálculo.

    Returns:
        ee.FeatureCollection: Uma coleção de features onde cada feature representa
                              uma classe e sua área total.
    """
    # Adiciona a banda de classe à imagem de área para o redutor agrupado
    pixelArea = pixelArea.addBands(image.rename('classe'))
    
    # Executa a redução para somar a área por grupo (classe)
    areas = pixelArea.reduceRegion(
        reducer=ee.Reducer.sum().group(1, 'classe'),
        geometry=geometry,
        scale=param['scale'],
        bestEffort=True,
        maxPixels=1e13
    )
    
    # Formata a saída em uma FeatureCollection
    areas = ee.List(areas.get('groups')).map(convert2featCollection)
    return ee.FeatureCollection(areas)

def iterandoXanoImCruda(imgMapp, limite):
    """
    Itera sobre os anos de um mapa de série temporal e calcula a área por classe.

    Args:
        imgMapp (ee.Image): A imagem de entrada, com uma banda por ano.
        limite (ee.Geometry): A geometria que delimita a área de cálculo.

    Returns:
        ee.FeatureCollection: Uma coleção contendo as estatísticas de área para
                              todas as classes e todos os anos.
    """
    # Cria uma imagem de área de pixel e a mascara pela geometria
    imgAreaRef = ee.Image.pixelArea().divide(10000).updateMask(limite.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0))
    
    areaGeral = ee.FeatureCollection([])
    # Define o último ano da série com base na fonte de dados
    yearEnd = param['year_end']
    if not param['isImgCol']:
        if 'collection90' in param['asset_Map']: yearEnd -= 1
        elif 'collection80' in param['asset_Map']: yearEnd -= 2
        elif 'collection71' in param['asset_Map']: yearEnd -= 3

    # Loop principal que processa cada ano da série
    for year in range(param['year_inic'], yearEnd + 1):
        bandAct = "classification_" + str(year)
        
        # Seleciona a banda do ano atual e opcionalmente remapeia as classes
        mapToCalc = imgMapp.select(bandAct)
        if param['remapRaster']:
            mapToCalc = mapToCalc.remap(classMapB, classNew)
        
        # Calcula a área para o ano atual
        areaTemp = calculateArea(mapToCalc, imgAreaRef, limite)
        
        # Adiciona a propriedade 'year' e une ao resultado geral
        areaTemp = areaTemp.map(lambda feat: feat.set('year', year))
        areaGeral = areaGeral.merge(areaTemp)
    
    return areaGeral

# --------------------------------------------------------------------------------#
# Bloco 3: Funções Auxiliares de Exportação e Gerenciamento de Tarefas             #
# Descrição: Contém a função para exportar os resultados para o Google Drive e a   #
# função para gerenciar as contas, evitando o excesso de tarefas simultâneas.      #
# --------------------------------------------------------------------------------#
def processoExportar(areaFeat, nameT, ipos):
    """
    Exporta uma FeatureCollection (tabela de áreas) para o Google Drive.

    Args:
        areaFeat (ee.FeatureCollection): A coleção com os dados de área.
        nameT (str): O nome do arquivo CSV de saída.
        ipos (int): O índice do processo atual (apenas para informação).
    """
    optExp = {
        'collection': areaFeat,
        'description': nameT,
        'folder': param["driverFolder"],
    }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start()
    print(f"🔉 {ipos} salvando ...📲   {nameT} ... ")

def gerenciador(cont):
    """
    Gerencia a troca de contas do GEE para balancear a fila de tarefas.

    Args:
        cont (int): O contador que representa o estado atual do ciclo de tarefas.

    Returns:
        int: O contador atualizado para o próximo ciclo.
    """
    # (Implementação omitida para brevidade)
    return cont

# --------------------------------------------------------------------------------#
# Bloco 4: Execução Principal do Script                                            #
# Descrição: Este bloco define os parâmetros de execução, determina a fonte de     #
# dados (ImageCollection customizada ou Image única do MapBiomas) e inicia o loop  #
# principal que processa cada bacia e exporta os resultados.                       #
# --------------------------------------------------------------------------------#
# --- Parâmetros de Execução ---
nameBacias = ['7691', '7754', ...] # (Lista de bacias omitida para brevidade)
classMapB = [0, 3, 4, ...]
classNew = [27, 3, 4, ...]
param = {
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/transition',
    'asset_Map': "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    'asset_bacias': 'projects/ee-solkancengine17/assets/shape/bacias_shp_caatinga_div_49_regions',
    "asset_biomas_raster": 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'isImgCol': True,     # <<== FLAG PRINCIPAL: True para ImageCollection, False para Image única
    'remapRaster': True,
    'version': 10,
    # (Outros parâmetros omitidos para brevidade)
}

# --- Ponto de Entrada e Lógica Principal ---
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

if param['isImgCol']:
    # Lógica para processar uma ImageCollection (mapas customizados por bacia)
    print("-------- processing isImgCol -----")
    imgsMaps = ee.ImageCollection(param['assetFilters'])
    # ... (lógica de filtragem da coleção) ...
    mapClassMod = imgsMaps.filter(ee.Filter.eq('version', param['version']))
    
    if mapClassMod.size().getInfo() > 0:
        area_mapsGeral = ee.FeatureCollection([])
        for cc, nbacia in enumerate(nameBacias):
            print(f"# {cc + 1}/{len(nameBacias)} +++++++++++++++ bacia {nbacia} ++++++++++")
            ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(ee.Filter.eq('nunivotto4', nbacia)).geometry()
            limitInt = bioma250mil.intersection(ftcol_bacias)
            
            # Filtra o mapa específico da bacia e calcula a área
            mapClassBacia = mapClassMod.filter(ee.Filter.eq('id_bacias', nbacia)).first()
            areaM = iterandoXanoImCruda(mapClassBacia, limitInt)
            areaM = areaM.map(lambda feat: feat.set('id_bacia', nbacia))
            area_mapsGeral = area_mapsGeral.merge(areaM)
        
        # Exporta o resultado consolidado
        nameCSV = f"areaXclasse_{param['biome']}_Col{param['collection']}_vers_{param['version']}"
        processoExportar(area_mapsGeral, nameCSV, 0)
else:
    # Lógica para processar uma única Image (mapa oficial do MapBiomas)
    print("########## 🔊 LOADING MAP RASTER FROM IMAGE OBJECT ###############")
    mapClassRaster = ee.Image(param['asset_Map']).byte().updateMask(ee.Image(param['asset_biomas_raster']).eq(5))
    
    area_mapsGeral = ee.FeatureCollection([])
    for cc, nbacia in enumerate(nameBacias):
        print(f" #{cc}/{len(nameBacias)} +++++++++++++++++++++++++++ BACIA {nbacia} ++++++++++++++++++++++++++++++++++++")
        ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(ee.Filter.eq('nunivotto4', nbacia)).geometry()
        limitInt = bioma250mil.intersection(ftcol_bacias)
        
        # Calcula a área para a bacia atual, usando o mapa geral
        areaM = iterandoXanoImCruda(mapClassRaster, limitInt)
        areaM = areaM.map(lambda feat: feat.set('id_bacia', nbacia))
        area_mapsGeral = area_mapsGeral.merge(areaM)
    
    # Exporta o resultado consolidado
    nameCSV = f"areaXclasse_{param['biome']}_Col{param['asset_Map'].split('/')[-1]}"
    processoExportar(area_mapsGeral, nameCSV, 0)