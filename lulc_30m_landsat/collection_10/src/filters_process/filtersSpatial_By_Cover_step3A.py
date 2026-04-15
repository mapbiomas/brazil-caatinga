#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE PÓS-CLASSIFICAÇÃO (FILTRO ESPACIAL CONDICIONAL)
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
# Bloco 2: Funções e Parâmetros do Filtro Espacial Condicional                     #
# Descrição: Esta seção contém a lógica para um filtro espacial avançado.          #
# Diferente de um filtro simples, este aplica regras de correção específicas       #
# para diferentes classes, como Savana e Agropecuária, para remover ruído de       #
# forma mais inteligente e contextual.                                             #
# --------------------------------------------------------------------------------#
param = {
    'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_int',
    'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalA',
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'last_year': 2024, 'first_year': 1985,
    'janela': 5, 'step': 1,
    'versionOut': 10, 'versionInp': 10,
    'numeroTask': 6, 'numeroLimit': 50,
    'conta': {
        '0': 'caatinga01', '6': 'caatinga02', '14': 'caatinga03',
        '21': 'caatinga04', '28': 'caatinga05', '35': 'solkan1201',
        '42': 'solkanGeodatin', '16': 'superconta'
    }
}
lst_bands_years = ['classification_' as yy) for yy in range(param['first_year'], param['last_year'] + 1)]

def buildingLayerconnectado(imgClasse, maxNumbPixels):
    """
    Adiciona bandas de contagem de pixels conectados a uma imagem de classificação.

    Para cada banda de classificação anual, esta função calcula o tamanho do
    aglomerado (patch) de pixels de mesma classe ao qual cada pixel pertence.

    Args:
        imgClasse (ee.Image): A imagem de entrada, contendo a série temporal de classificação.
        maxNumbPixels (int): O tamanho máximo do aglomerado a ser considerado.

    Returns:
        ee.Image: A imagem original com as bandas de contagem de pixels conectados adicionadas.
    """
    lst_band_conn = ['classification_' as yy) + '_conn' for yy in range(param['first_year'], param['last_year'] + 1)]
    bandaConectados = imgClasse.connectedPixelCount(
        maxSize=maxNumbPixels,
        eightConnected=True
    ).rename(lst_band_conn)
    return imgClasse.addBands(bandaConectados)

def apply_spatialFilterConn(name_bacia):
    """
    Orquestra o processo de filtro espacial condicional para uma bacia.

    Esta função identifica pequenos aglomerados de pixels (ruído) e os substitui
    aplicando diferentes filtros de vizinhança (`mode`, `min`) com base em
    regras específicas para as classes envolvidas (ex: Savana, Agropecuária).

    Args:
        name_bacia (str): O ID da bacia a ser processada.
    """
    min_connect_pixel = 12
    geomBacia_fc = ee.FeatureCollection(param['asset_bacias_buffer'])\
        .filter(ee.Filter.eq('nunivotto4', name_bacia))
    bacia_raster = geomBacia_fc.map(lambda f: f.set('id_codigo', 1))\
        .reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    geomBacia = geomBacia_fc.geometry()

    # Carrega a imagem de classificação e adiciona as bandas de conectividade
    imgClass = ee.ImageCollection(param['input_asset'])\
        .filter(ee.Filter.eq('version', param['versionInp']))\
        .filter(ee.Filter.eq('id_bacias', name_bacia)).first().updateMask(bacia_raster)
    imgClass = buildingLayerconnectado(imgClass, min_connect_pixel)

    class_output = ee.Image().byte()

    # Itera sobre cada ano da série temporal para aplicar o filtro
    for yband_name in lst_bands_years[:]:
        
        # 1. Máscara principal: identifica pixels em aglomerados menores que `min_connect_pixel`
        maskConn = imgClass.select(f'{yband_name}_conn').lt(min_connect_pixel)

        # 2. Máscaras condicionais: identificam pixels de classes específicas
        maskSavUso = imgClass.select(yband_name).eq(4).Or(imgClass.select(yband_name).eq(21))
        maskUsoSolo = imgClass.select(yband_name).eq(21).Or(imgClass.select(yband_name).eq(22))

        # 3. Cálculo dos filtros de vizinhança (focais)
        kernel = ee.Kernel.square(4)
        base = imgClass.select(yband_name)

        # Filtro de MODO: substitui o pixel pela classe mais comum na vizinhança (suavização geral)
        filterImageSavUs = base.reduceNeighborhood(reducer=ee.Reducer.mode(), kernel=kernel)

        # Filtro de MÍNIMO: substitui pela menor classe na vizinhança (útil para regras direcionais)
        # Ex: tende a converter pequenas ilhas de Agropecuária (21) em Savana (4)
        filterImageUsoSav = base.reduceNeighborhood(reducer=ee.Reducer.min(), kernel=kernel)
        filterImageUsoSol = base.reduceNeighborhood(reducer=ee.Reducer.min(), kernel=kernel)

        # 4. Aplicação das máscaras aos resultados dos filtros
        filterImageSavUs = filterImageSavUs.updateMask(maskSavUso).updateMask(maskConn)
        filterImageUsoSav = filterImageUsoSav.updateMask(maskSavUso).updateMask(maskConn)
        filterImageUsoSol = filterImageUsoSol.updateMask(maskUsoSolo).updateMask(maskConn)

        # 5. Mesclagem hierárquica (blending) para aplicar as regras
        # Começa com a imagem original e aplica as correções em camadas.
        # A última mesclagem (`blend`) tem prioridade sobre as anteriores.
        rasterMap = base.blend(filterImageUsoSav)\
                        .blend(filterImageSavUs)\
                        .blend(filterImageUsoSol)\
                        .rename(yband_name)

        class_output = class_output.addBands(rasterMap)

    # Define os metadados e exporta a imagem final
    nameExp = f"filterSP_BACIA_{name_bacia}_GTB_V{param['versionOut']}"
    class_output = class_output.updateMask(bacia_raster)\
        .select(lst_bands_years)\
        .set({
            'version': param['versionOut'], 'biome': 'CAATINGA', 'collection': '10.0',
            'id_bacias': name_bacia, 'sensor': 'Landsat', 'source': 'geodatin',
            'model': 'GTB', 'step': param['step'], 'system:footprint': geomBacia
        })
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