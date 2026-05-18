#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CORREÇÃO DE AMOSTRAS (ROIs)
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
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable  # Garante compatibilidade com novas versões do Python

# Adiciona o diretório pai ao path do sistema para importar módulos customizados
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
# Bloco 2: Propósito do Script e Parâmetros de Configuração
# Descrição: Este script serve como uma etapa de correção. Após um processo
# de filtragem ou redução de amostras (provavelmente pelo script
# filter_ROIs_red.py), este código verifica se alguma classe de amostra foi
# perdida acidentalmente. Se uma classe foi removida, ele a reinsere a partir
# da coleção de amostras original, garantindo que o conjunto final de ROIs
# contenha todas as classes originais.
# --------------------------------------------------------------------------
param = {
    # Asset de saída final para as amostras corrigidas
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_DS_v4corrCC',
    'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_DS_v4corrCC',

    # Asset de entrada contendo as amostras originais (antes da redução)
    'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C',
    'asset_joinsGrBaMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_V4C',

    # Asset de entrada contendo as amostras já filtradas/reduzidas (a serem corrigidas)
    'outAssetROIsred': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_DS_v4CC',
    'outAssetROIsredMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_DS_v4CC',

    # Período de análise
    'yearInicial': 1985,
    'yearFinal': 2024,
}

# Lista de todas as bacias a serem processadas
nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', '752', '7616', '745',
    '7424', '773', '7612', '7613', '7618', '7561', '755', '7617', '7564', '761111',
    '761112', '7741', '7422', '76116', '7761', '7671', '7615', '7411', '7764', '757',
    '771', '7712', '766', '7746', '753', '764', '7541', '7721', '772', '7619', '7443',
    '765', '7544', '7438', '763', '7591', '7592', '7622', '746'
]

# --------------------------------------------------------------------------
# Bloco 3: Funções Auxiliares de Gerenciamento de Assets
# Descrição: Este bloco contém as funções responsáveis por interagir com
# os assets do Google Earth Engine, seja para exportar novas coleções ou
# para mover/renomear assets existentes.
# --------------------------------------------------------------------------

def processoExportar(ROIsFeat, IdAssetnameB):
    """Inicia uma tarefa de exportação de uma FeatureCollection para um asset.

    Args:
        ROIsFeat (ee.FeatureCollection): A coleção de features a ser exportada.
        IdAssetnameB (str): O caminho completo do asset de destino.
    """
    nameB = IdAssetnameB.split("/")[-1]
    optExp = {
        'collection': ROIsFeat,
        'description': nameB,
        'assetId': IdAssetnameB
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("salvando ... " + nameB + "..!")

def sendFilenewAsset(idSource, idTarget):
    """Move (renomeia) um asset do GEE de um local para outro.

    Esta operação é muito mais rápida do que reexportar os dados, sendo ideal
    para quando o conteúdo do asset não precisa de modificação.

    Args:
        idSource (str): O caminho completo do asset de origem.
        idTarget (str): O caminho completo do asset de destino.
    """
    ee.data.renameAsset(idSource, idTarget)

# --------------------------------------------------------------------------
# Bloco 4: Execução Principal do Script (Main)
# Descrição: Este é o ponto de entrada e o coração do script. Ele itera
# sobre cada bacia e cada ano, compara os conjuntos de amostras (o original
# e o filtrado), e decide se precisa corrigir e reexportar os dados, ou
# apenas mover o asset já existente para o local final.
# --------------------------------------------------------------------------
print("vai exportar em ", param['assetOutMB'])
listYears = [k for k in range(param['yearInicial'], param['yearFinal'] + 1)]

# Loop principal que itera sobre cada bacia e cada ano
for _nbacia in nameBacias[6:]:
    for cc, nyear in enumerate(listYears[:]):
        # Constrói o nome do asset para a bacia e ano atuais
        nameFeatROIs = f"{_nbacia}_{nyear}_cd"

        # Carrega as duas coleções de amostras: a original e a já reduzida
        ROIs_DScc = ee.FeatureCollection(os.path.join(param['asset_joinsGrBaMB'], nameFeatROIs))
        ROIs_RedCC = ee.FeatureCollection(os.path.join(param['outAssetROIsredMB'], nameFeatROIs))

        # Obtém a lista de classes únicas presentes em cada coleção
        dictDScc = ROIs_DScc.aggregate_histogram('class').getInfo()
        dictRedcc = ROIs_RedCC.aggregate_histogram('class').getInfo()

        lstCCds = [int(float(ccs)) for ccs in list(dictDScc.keys())]
        lstCCred = [int(float(ccs)) for ccs in list(dictRedcc.keys())]
        print(f"lista all {lstCCds}  \n  >>>> {lstCCred}")

        # Identifica as classes que estão no conjunto original mas faltam no conjunto reduzido
        lstCCfails = [cc for cc in lstCCds if cc not in lstCCred]
        print("lista de classes faltantes ", lstCCfails)
        
        idAssetOut = os.path.join(param['assetOutMB'], nameFeatROIs)

        # Lógica de decisão: corrigir ou mover
        if len(lstCCfails) > 0:
            # Se houver classes faltando, reinsere-as na coleção reduzida
            print(f"CORRIGINDO: {len(lstCCfails)} classes faltando para {nameFeatROIs}. Re-exportando...")
            featCCfails = ROIs_DScc.filter(ee.Filter.inList('class', lstCCfails))
            ROIs_RedCC = ROIs_RedCC.merge(featCCfails)
            
            # Exporta a coleção corrigida para o destino final
            processoExportar(ROIs_RedCC, idAssetOut)

        else:
            # Se não houver classes faltando, o asset reduzido está correto.
            # Apenas o move para o destino final, o que é mais eficiente.
            source = os.path.join(param['outAssetROIsredMB'], nameFeatROIs)
            try:
                print(f"MOVENDO: Nenhuma classe faltando. Movendo {nameFeatROIs} para o destino final.")
                sendFilenewAsset(source, idAssetOut)
                print(cc, ' => move ', nameFeatROIs, f" to Folder in {idAssetOut}")
            except Exception as e:
                print(f"Erro ao mover o asset {nameFeatROIs}. Pode já existir no destino. Detalhe: {e}")