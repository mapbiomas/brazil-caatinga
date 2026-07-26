#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import sys
import ee
import random
# Ajuste o caminho das suas libs locais
pathparent = str('/home/superuser/Dados/projAlertas/proj_alertas_ML/src')
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account

projAccount = get_current_account()
print(f"Projeto selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
except Exception as e:
    print("Erro de Inicialização:", e)
    raise



def share_assets_in_folder(folder_path, user_email, role='viewer'):
    """
    Compartilha todos os assets dentro de uma pasta com um usuário específico.
    role: 'viewer' (leitor) ou 'writer' (editor)
    """
    print(f"📂 Acessando pasta: {folder_path}")
    
    # 1. Listar todos os assets dentro da pasta
    try:
        asset_list = ee.data.listAssets({'parent': folder_path})['assets']
    except Exception as e:
        print(f"❌ Erro ao listar assets: {e}")
        return

    print(f"Found {len(asset_list)} assets. Iniciando compartilhamento...")

    for cc, asset in enumerate(asset_list):
        asset_id = asset['id']
        asset_type = asset['type']
        
        # Só processamos FeatureCollections (ou imagens se desejar)
        if asset_type == 'TABLE' or asset_type == 'FEATURE_COLLECTION':
            try:
                # 2. Obter a política de permissão atual
                acl = ee.data.getAssetAcl(asset_id)
                
                # 3. Adicionar o novo usuário à lista de permissões
                # No EE, a chave para leitores é 'viewers'
                current_viewers = acl.get('viewers', [])
                
                if user_email not in current_viewers:
                    current_viewers.append(user_email)
                    
                    # 4. Atualizar o ACL do Asset
                    # O formato esperado é um JSON serializado com as listas de permissões
                    ee.data.setAssetAcl(asset_id, {
                        'viewers': current_viewers,
                        'all_users_can_read': True # Defina como True se quiser tornar público
                    })
                    print(f"✅ #{cc}  >>> Compartilhado: {asset_id.split('/')[-1]}")
                else:
                    print(f"ℹ️ Usuário já tinha acesso a: {asset_id.split('/')[-1]}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao compartilhar {asset_id}: {e}")

# --- CONFIGURAÇÃO ---
ASSET_ALERTS_FOLDER = "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/rois_grades_cerr_caat_embeddin"
# EMAIL_DESTINO = "mapbiomas_caatinga04@gmail.com"
EMAIL_DESTINO = "solkan.cengine17@gmail.com"

share_assets_in_folder(ASSET_ALERTS_FOLDER, EMAIL_DESTINO)