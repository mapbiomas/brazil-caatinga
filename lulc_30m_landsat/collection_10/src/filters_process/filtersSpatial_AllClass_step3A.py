#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE PÓS-CLASSIFICAÇÃO (FILTRO ESPACIAL)
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
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões do Python

# Adiciona o diretório pai ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[0])
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
# Bloco 2: Funções e Parâmetros do Filtro Espacial                                 #
# Descrição: Esta seção contém a lógica principal para a aplicação do filtro       #
# espacial. O objetivo é remover o ruído "sal e pimenta" dos mapas de              #
# classificação, eliminando pequenos grupos de pixels isolados e substituindo-os   #
# pela classe mais comum em sua vizinhança.                                        #
# --------------------------------------------------------------------------------#
param = {
    'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_all',
    'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'last_year': 2024,
    'first_year': 1985,
    'janela': 5,
    'step': 1,
    'versionOut': 10,
    'versionInp': 10,
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta': {
        '0': 'caatinga01', '6': 'caatinga02', '14': 'caatinga03',
        '21': 'caatinga04', '28': 'caatinga05', '35': 'solkan1201',
        '42': 'solkanGeodatin', '16': 'superconta'
    }
}
lst_bands_years = [f'classification_{yy}' for yy in range(param['first_year'], param['last_year'] + 1)]

def buildingLayerconnectado(imgClasse, maxNumbPixels):
    """
    Adiciona bandas de contagem de pixels conectados a uma imagem de classificação.

    Para cada banda de classificação anual, esta função calcula o tamanho do
    aglomerado (patch) de pixels de mesma classe ao qual cada pixel pertence.
    O resultado é adicionado como uma nova banda (ex: 'classification_1985_conn').

    Args:
        imgClasse (ee.Image): A imagem de entrada, contendo a série temporal de classificação.
        maxNumbPixels (int): O tamanho máximo do aglomerado a ser considerado.

    Returns:
        ee.Image: A imagem original com as bandas de contagem de pixels conectados adicionadas.
    """
    lst_band_conn = ['classification_' as yy) + '_conn' for yy in range(param['first_year'], param['last_year'] + 1)]
    
    # Calcula o tamanho do patch para cada pixel em todas as bandas de classificação
    bandaConectados = imgClasse.connectedPixelCount(
        maxSize=maxNumbPixels,
        eightConnected=True
    ).rename(lst_band_conn)
    
    # Adiciona as novas bandas à imagem original
    return imgClasse.addBands(bandaConectados)

def apply_spatialFilterConn(name_bacia):
    """
    Orquestra o processo de filtro espacial para uma bacia hidrográfica.

    Esta função identifica pequenos aglomerados de pixels (ruído) e os substitui
    pela classe mais frequente em sua vizinhança (filtro de modo focal),
    preservando áreas maiores e consolidadas.

    Args:
        name_bacia (str): O ID da bacia a ser processada.
    """
    # Define o tamanho mínimo que um aglomerado de pixels deve ter para ser mantido
    min_connect_pixel = 12
    
    # Carrega a geometria e a máscara raster da bacia
    geomBacia_fc = ee.FeatureCollection(param['asset_bacias_buffer'])\
        .filter(ee.Filter.eq('nunivotto4', name_bacia))
    bacia_raster = geomBacia_fc.map(lambda f: f.set('id_codigo', 1))\
        .reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    geomBacia = geomBacia_fc.geometry()

    # Carrega a imagem de classificação da bacia
    imgClass = ee.ImageCollection(param['input_asset'])\
        .filter(ee.Filter.eq('version', param['versionInp']))\
        .filter(ee.Filter.eq('id_bacias', name_bacia)).first().updateMask(bacia_raster)
    
    # Adiciona as bandas de contagem de pixels conectados
    imgClass = buildingLayerconnectado(imgClass, min_connect_pixel)
    
    # Cria uma imagem vazia para armazenar o resultado final
    class_output = ee.Image().byte()

    # Itera sobre cada ano da série temporal para aplicar o filtro
    for yband_name in lst_bands_years[:]:
        
        # 1. Cria uma máscara identificando os pixels que pertencem a aglomerados pequenos
        maskConn = imgClass.select(f'{yband_name}_conn').lt(min_connect_pixel)

        # 2. Aplica um filtro de modo focal para encontrar a classe mais comum na vizinhança
        kernel = ee.Kernel.square(4)  # Janela de vizinhança 9x9 (raio de 4 pixels)
        filterImageClass = imgClass.select(yband_name).reduceNeighborhood(
            reducer=ee.Reducer.mode(),
            kernel=kernel
        )
        
        # Aplica o resultado do filtro de modo apenas onde a máscara é verdadeira
        filterImageSavUs = filterImageClass.updateMask(maskConn)

        # 3. Combina o resultado: mantém os pixels originais e substitui apenas os ruidosos
        base = imgClass.select(yband_name)
        rasterMap = base.blend(filterImageSavUs).rename(yband_name)

        # Adiciona a banda do ano processado à imagem de saída
        class_output = class_output.addBands(rasterMap)
    
    # Define os metadados da imagem final
    nameExp = f"filterSP_BACIA_{name_bacia}_GTB_V{param['versionOut']}"
    class_output = class_output.updateMask(bacia_raster)\
        .select(lst_bands_years)\
        .set({
            'version': param['versionOut'], 'biome': 'CAATINGA', 'collection': '10.0',
            'id_bacias': name_bacia, 'sensor': 'Landsat', 'source': 'geodatin',
            'model': 'GTB', 'step': param['step'], 'system:footprint': geomBacia
        })
    
    # Inicia a exportação do resultado
    processoExportar(class_output, nameExp, geomBacia)

# --------------------------------------------------------------------------------#
# Bloco 3: Funções Auxiliares de Exportação e Gerenciamento de Tarefas             #
# Descrição: Contém a função para exportar os resultados como assets no GEE e a    #
# função para gerenciar as contas, evitando o excesso de tarefas simultâneas.      #
# --------------------------------------------------------------------------------#
def processoExportar(mapaRF, nomeDesc, geom_bacia):
    """
    Exporta uma imagem como um asset no Google Earth Engine.

    Args:
        mapaRF (ee.Image): A imagem a ser exportada.
        nomeDesc (str): A descrição da tarefa e o nome base do asset.
        geom_bacia (ee.Geometry): A geometria da bacia para delimitar a exportação.
    """
    idasset = os.path.join(param['output_asset'], nomeDesc)
    optExp = {
        'image': mapaRF, 'description': nomeDesc, 'assetId': idasset,
        'region': geom_bacia, 'scale': 30, 'maxPixels': 1e13,
        "pyramidingPolicy": {".default": "mode"}
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start()
    print("salvando ... " + nomeDesc + "..!")

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
# Descrição: Este bloco define a lista de bacias a serem processadas e inicia      #
# o loop principal, chamando a função de filtro espacial para cada uma delas.      #
# --------------------------------------------------------------------------------#
listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', '7616', '745', '7424',
    '773', '7612', '7613', '752', '7618', '7561', '755', '7617', '7564', '761111',
    '761112', '7741', '7422', '76116', '7761', '7671', '7615', '7411', '7764', '757',
    '771', '766', '7746', '753', '764', '7541', '7721', '772', '7619', '7443',
    '7544', '7438', '763', '7591', '7592', '746', '7712', '7622', '765',
]
listaNameBacias = ["7613", "7746", "7741", "7591", "7581", "757"]

# --- Loop Principal de Execução ---
knowMapSaved = False
for cc, idbacia in enumerate(listaNameBacias[:]):
    if knowMapSaved:
        # Lógica para verificar se o mapa já foi salvo (desativada)
        pass
    else:
        print("----- PROCESSING BACIA {} -------".format(idbacia))
        # Chama a função principal do filtro espacial
        apply_spatialFilterConn(idbacia)