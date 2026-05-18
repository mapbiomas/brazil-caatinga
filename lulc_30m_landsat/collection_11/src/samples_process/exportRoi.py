#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE EXPORTAÇÃO DE AMOSTRAS PARA O DRIVE
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee 
import sys
import os
from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account

projAccount = get_current_account()
print(f"Projeto selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('✅ The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('❌ The Earth Engine package failed to initialize!', e)
    sys.exit()
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit()

# Dicionário de parâmetros enxuto
param = {    
    'asset_ROISall_joins': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/rois_resample_featmaps',
    'folder_drive': 'ROIs_FeatMaps_Allvar',
    'showAssetFeat': False
}

# -------------------------------------------------------------------------
# FUNÇÕES
# -------------------------------------------------------------------------
def listar_assets_na_pasta(folder_id):
    """
    Substitui o obsoleto ee.data.getList por ee.data.listAssets,
    que é o padrão atual da API do Google Earth Engine.
    """
    try:
        # Puxa a lista de assets (limitado nativamente se houver milhares, mas seguro)
        lista_completa = ee.data.listAssets({'parent': folder_id})['assets']
        colection_ptos = [asset['name'] for asset in lista_completa]
        return colection_ptos
    except Exception as e:
        print(f"Erro ao listar assets na pasta {folder_id}: {e}")
        return []

def processoExportar_toDrive(ROIsFeat, nameB, nfolder):    
    """Configura e dispara a tarefa para o Google Drive"""
    optExp = {
          'collection': ROIsFeat, 
          'description': nameB, 
          'folder': nfolder          
    }
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print(f" ⏳ Tarefa enviada para o Drive: {nameB} ...!")    

# -------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# -------------------------------------------------------------------------

# Lista de bacias que JÁ FORAM processadas (ou que não devem ser rodadas)
bacias_ja_processadas = [
    "7438","752","7584","761111","7591", "751", "7422",
    "7619","765","7712","773","7746","7615","7411","7424",
    "745","755","7561", "7564",'7616','7443','746','753',
    '7541', '7544','757','7581','7592','761112','76116',
    '7612','7613','7614','7617','7618','7619','7622','7625',
    '763','764','766','7671','7691','771','772','7721','7741',
    '7754','7761','7764'
]

print("Buscando amostras no GEE...")
folder_alvo = param['asset_ROISall_joins']

# 1. Pega todos os caminhos dos assets dentro da pasta alvo
caminhos_assets = listar_assets_na_pasta(folder_alvo)

if not caminhos_assets:
    print(f"⚠️ Nenhum asset encontrado na pasta: {folder_alvo}")
    sys.exit()

print(f"Encontrados {len(caminhos_assets)} assets no servidor.")

# 2. Itera sobre os assets e filtra
for cc, asset_path in enumerate(caminhos_assets):        
    # Extrai apenas o nome do arquivo final (ex: 'samples_7438_1990')
    nome_asset_completo = asset_path.split("/")[-1]
    
    # A sua lógica original dividia pelo '_' e pegava o último elemento.
    # Ex: se o nome for 'samples_7438', ele pega '7438'. 
    # (Cuidado se o nome for 'samples_7438_1990', pois o [-1] será '1990')
    codigo_bacia = nome_asset_completo.split("_")[-1] 
    
    if param['showAssetFeat']:
        print(f"Lendo: {nome_asset_completo}")

    # Se a bacia NÃO estiver na lista de processadas, envia pro Drive
    if codigo_bacia not in bacias_ja_processadas:
        print(f" #{cc} Carregando e exportando => {nome_asset_completo}")
        
        # Instancia a FeatureCollection
        ROIs = ee.FeatureCollection(asset_path)       
        
        # Dispara a exportação usando o nome completo do asset para evitar sobrescrições no Drive
        processoExportar_toDrive(ROIs, nome_asset_completo, param['folder_drive'])              
    else:
        # Bacia já consta na lista de ignoradas/concluídas
        print(f" ⏭️ Bacia ignorada (já processada): < {codigo_bacia} >")

print("\n=================================================")
print("Todas as novas tarefas foram agendadas com sucesso!")
print("Acompanhe o status na aba 'Tasks' do Code Editor.")
print("=================================================")

# 📡 Bônus: Monitor de Tarefas (Task Tracker) no Python
print("\n=================================================")
print("Todas as tarefas foram enviadas! Iniciando monitoramento...")
print("=================================================")
import time
def monitorar_tarefas():
    while True:
        # Busca todas as tarefas do usuário logado
        tarefas = ee.batch.Task.list()
        
        # Filtra apenas as tarefas que estão ativas (rodando ou na fila)
        tarefas_ativas = [t for t in tarefas if t.state in ['READY', 'RUNNING']]
        
        if not tarefas_ativas:
            print("\n✅ TODAS AS TAREFAS FORAM CONCLUÍDAS (Ou falharam). Verifique seu Asset!")
            break
            
        print(f"\n[{time.strftime('%X')}] Status atual:")
        for t in tarefas_ativas:
            # Imprime o nome da tarefa, o status e o tempo decorrido
            print(f" -> {t.config['description']}: {t.state}")
            
        # Espera 30 segundos antes de checar novamente (para não bombardear o servidor)
        time.sleep(30)

# Inicia o monitoramento
monitorar_tarefas()