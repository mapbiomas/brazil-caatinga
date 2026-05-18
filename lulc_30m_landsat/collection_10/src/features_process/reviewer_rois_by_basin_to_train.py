#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE VERIFICAÇÃO DE AMOSTRAS
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
# Bloco 2: Propósito do Script e Funções de Verificação                            #
# Descrição: O objetivo deste script é diagnosticar e verificar a integridade      #
# das coleções de amostras (ROIs), imprimindo um histograma de classes para        #
# cada bacia e ano, garantindo que os dados estão prontos para as próximas         #
# etapas. As funções abaixo implementam diferentes estratégias de leitura.         #
# --------------------------------------------------------------------------------#

def GetPolygonsfromFolder(dict_idasset):
    """Lista todos os asset IDs dentro de uma pasta específica no GEE.

    Args:
        dict_idasset (dict): Um dicionário contendo o ID da pasta do GEE,
                             no formato {'id': 'path/to/folder'}.

    Returns:
        list[str]: Uma lista com os caminhos completos de cada asset na pasta.
    """
    getlistPtos = ee.data.getList(dict_idasset)
    list_idasset = []
    for idAsset in getlistPtos:
        path_ = idAsset.get('id')
        list_idasset.append(path_)
    return list_idasset

def reviewer_samples_byYear(dir_asset, nbasin, nlistYears):
    """Verifica amostras assumindo que cada ano é um asset separado.

    Esta função itera sobre uma lista de anos, constrói o nome do asset para
    cada combinação de bacia/ano, carrega a FeatureCollection e imprime
    um histograma da propriedade 'class'.

    Args:
        dir_asset (str): O caminho da pasta no GEE que contém os assets anuais.
        nbasin (str): O ID da bacia hidrográfica a ser verificada.
        nlistYears (list[int]): A lista de anos a serem iterados.
    """
    for cc, nyear in enumerate(nlistYears[:]):
        nameFeatROIs = f"{nbasin}_{nyear}_cd"
        idAsset = os.path.join(dir_asset, nameFeatROIs)
        try:
            feat_tmp = ee.FeatureCollection(idAsset)
            print(f"#{cc} >> {nyear} : ", feat_tmp.aggregate_histogram('class').getInfo())
        except Exception as e:
            print(f"#{cc} >> {nyear} : ERRO ao carregar o asset {idAsset} - {e}")

def reviewer_samples_byFC(dir_asset, nbasin, nlistYears):
    """Verifica amostras de um único asset que contém todos os anos.

    Esta função carrega um único asset por bacia e, em seguida, itera sobre
    a lista de anos, filtrando a coleção para cada ano e imprimindo o
    histograma da propriedade 'class'.

    Args:
        dir_asset (str): O caminho da pasta no GEE que contém o asset da bacia.
        nbasin (str): O ID da bacia, usado para construir o nome do asset.
        nlistYears (list[int]): A lista de anos para filtrar e verificar.
    """
    nameFeatROIs = f"rois_fromGrade_{nbasin}"
    idAsset = os.path.join(dir_asset, nameFeatROIs)
    try:
        featB = ee.FeatureCollection(idAsset)
        for cc, nyear in enumerate(nlistYears[:]):
            feat_tmp = featB.filter(ee.Filter.eq('year', nyear))
            print(f"#{cc} >> {nyear} : ", feat_tmp.aggregate_histogram('class').getInfo())
    except Exception as e:
        print(f"ERRO ao carregar o asset da bacia {idAsset} - {e}")

# --------------------------------------------------------------------------------#
# Bloco 3: Execução Principal do Script (Main)                                     #
# Descrição: Este bloco define os parâmetros de execução, determina a              #
# estratégia de verificação (um asset por ano ou um por bacia) e, em seguida,      #
# itera sobre as bacias para executar a verificação.                               #
# --------------------------------------------------------------------------------#

# Parâmetros de execução
param = {
    'asset_sample_rev': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C',
    'yearInicial': 1985,
    'yearFinal': 2024,
}

# Lista de bacias a serem verificadas
nameBacias = [
    '765', '7544', '7541'
]

# Gera a lista de anos e lista os assets na pasta de destino
listYears = [k for k in range(param['yearInicial'], param['yearFinal'] + 1)]
list_idassets = GetPolygonsfromFolder({'id': param['asset_sample_rev']})

# Decide a estratégia de revisão com base no número de assets encontrados
filtrarFC = True
if len(list_idassets) > len(nameBacias):
    # Se houver mais assets que bacias, assume-se um asset por ano/bacia.
    print("ESTRATÉGIA: Verificação por assets anuais individuais.")
    filtrarFC = False
else:
    # Caso contrário, assume-se um único asset consolidado por bacia.
    print("ESTRATÉGIA: Verificação por asset único de bacia (filtrando por ano).")

# Limpa a lista da memória, pois não será mais usada
del list_idassets

# Loop principal para executar a verificação em cada bacia
for ii, _nbacia in enumerate(nameBacias[:]):
    print(f"\n# {ii} Verificando a bacia: {_nbacia}")
    if filtrarFC:
        # Chama a função que lê um asset único e filtra por ano
        reviewer_samples_byFC(param['asset_sample_rev'], _nbacia, listYears)
    else:
        # Chama a função que lê um asset para cada ano
        reviewer_samples_byYear(param['asset_sample_rev'], _nbacia, listYears)