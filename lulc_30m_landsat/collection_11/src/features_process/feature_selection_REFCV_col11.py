import ee
import os
import sys
import json
import time
import argparse
import pandas as pd
# import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFECV
from sklearn.model_selection import StratifiedKFold

# =================================================================
# INICIALIZAÇÃO GEE
# =================================================================
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
# from configure_account_projects_ee import get_current_account  # noqa: E402
# from gee_tools import *  # noqa: E402, F403

# projAccount = get_current_account()
# print(f"projeto >>> {projAccount}")

try:
    ee.Initialize(project= 'mapbiomas-caatinga-cloud04')
    print('✅ Earth Engine inicializado com sucesso!')
except Exception as e:
    print(f"❌ Erro ao inicializar o GEE: {e}")
    sys.exit()

# =================================================================
# PARÂMETROS
# =================================================================
nameBacias = [
    '7411', '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615',  
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7721', '772', '7619', '765', '7438', '7591', '7592', '7622',
    '746', '7541', '7443', '7544', '763'    
]
lst_years = list(range(1985, 2026))

# Diretório local (Samba) onde os JSONs serão salvos
dir_saida = Path('./FS_col11_json')
dir_saida.mkdir(parents=True, exist_ok=True)

# Configuração do RFECV
N_SPLITS = 3
MIN_FEATURES = 15 # Valor seguro para evitar um corte drástico

# =================================================================
# FUNÇÃO DE DOWNLOAD E PREPARAÇÃO IN-MEMORY
# =================================================================
def fetch_data_from_gee(bacia, ano):
    asset_id = f"projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesv1CC/rois_fromGrade_{bacia}_{ano}"
    
    try:
        fc = ee.FeatureCollection(asset_id)
        # Gera URL de download direto para CSV (rápido e não enche o HD de lixo)
        url = fc.getDownloadURL(filetype='csv')
        df = pd.read_csv(url)
        return df
    except Exception as e:
        print(f"⚠️ Asset não encontrado ou vazio: {asset_id}")
        return None

# =================================================================
# PIPELINE PRINCIPAL
# =================================================================
parser = argparse.ArgumentParser()
parser.add_argument('position_t0', type=str,  default=1, help="digite o inicio da lista de bacias  " )
parser.add_argument('position_t1', type=str,  default=1, help="digite o final da lista de bacias  " )
pos_inic = 0
pos_end = 10
try:
    args = parser.parse_args()
    pos_inic= int(args.position_t0)
    pos_end= int(args.position_t1)
except argparse.ArgumentTypeError as e:
    print(f"Invalid argument: {e}")

for bacia in nameBacias[pos_inic: pos_end]:
    for ano in lst_years:        
        arquivo_json = dir_saida / f"feat_sel_{bacia}_{ano}.json"
        
        # Pula se já foi processado (ótimo para retomar se o servidor reiniciar)
        if arquivo_json.exists():
            print(f"⏩ {bacia}_{ano} já processado. Pulando...")
            continue
            
        print(f"\n🔄 Processando Bacia {bacia} | Ano {ano}...")
        start_time = time.time()
        
        # 1. Carrega os dados
        df = fetch_data_from_gee(bacia, ano)
        if df is None or df.empty:
            continue
            
        # 2. Limpeza Bruta (Resolve o ValueError do NaN)
        df = df.fillna(0.0)
        colunas_lixo = ['system:index', '.geo', 'year', 'GRID_ID']
        df = df.drop(columns=[c for c in colunas_lixo if c in df.columns], errors='ignore')
        
        if 'class' not in df.columns:
            continue
            
        # 3. Escudo do StratifiedKFold (Resolve o UserWarning da classe com < 3 membros)
        contagem = df['class'].value_counts()
        classes_validas = contagem[contagem >= N_SPLITS].index
        classes_removidas = contagem[contagem < N_SPLITS].index
        
        if len(classes_removidas) > 0:
            print(f"   🧹 Classes removidas por poucas amostras: {list(classes_removidas)}")
            df = df[df['class'].isin(classes_validas)]
            
        if df['class'].nunique() < 2:
            print(f"   ⏭️ Bacia com apenas 1 classe válida. Ignorando RFECV.")
            continue

        # 4. Configuração das Matrizes
        X = df.drop(columns=['class'])
        y = df['class'].astype(int)
        
        print(f"   ⚙️ Iniciando RFECV (Features: {X.shape[1]}, Amostras: {X.shape[0]})...")
        
        # 5. OTIMIZAÇÃO MÁXIMA: Roda 1 único estimador padrão com step=0.05 (elimina 5% por vez)
        clf = RandomForestClassifier(n_estimators=800, n_jobs=1, random_state=42)
        cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
        
        # O step=0.05 faz o RFECV voar, descartando blocos de variáveis irrelevantes de uma vez
        rfecv = RFECV(
            estimator= clf,
            step= 0.05,
            cv= cv,
            scoring= 'accuracy',
            n_jobs=-1, # Usa todos os núcleos do seu servidor Arch Linux
            min_features_to_select= MIN_FEATURES,

        )        
        try:
            rfecv.fit(X, y)
        except Exception as e:
            print(f"   ❌ Erro no fit: {e}")
            continue
            
        # 6. Salva as melhores features no JSON
        melhores_features = list(X.columns[rfecv.support_])
        
        dict_result = {
            'optimal_number_of_features': int(rfecv.n_features_),
            'features': melhores_features
        }
        
        with open(arquivo_json, 'w') as f:
            json.dump(dict_result, f, indent=4)
            
        tempo_gasto = time.time() - start_time
        print(f"  ✅ Selecionadas {rfecv.n_features_} variáveis em {tempo_gasto:.2f} segundos.")