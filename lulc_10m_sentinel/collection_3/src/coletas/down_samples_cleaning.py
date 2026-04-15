#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Otimizado por: Gemini (Assistent AI)
    Original: Geodatin - Dados e Geoinformacao
    DISTRIBUIDO COM GPLv2
"""

import os
import sys
import pandas as pd
import numpy as np
from glob import glob
from pathlib import Path
from sklearn.ensemble import IsolationForest
from tqdm import tqdm # Barra de progresso eficiente

# Configuração de caminhos
current_path = Path(os.getcwd())
pathparent = str(current_path.parents[0])
print(f"Scripts path >> {pathparent}")
sys.path.append(pathparent)

# --- CONFIGURAÇÕES GLOBAIS ---

# Lista original limpa (removendo duplicatas com set e ordenando)
RAW_COLUMNS = [
    '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
    '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', 
    '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', 
    '63', 'fvi_median', 'fvi_median_dry', 'fvi_median_wet', 'vi_median', 'vi_median_dry', 'vi_median_wet', 'wei_median', 'wei_median_dry', 
    'wei_median_wet', 'lue_median', 'lue_median_dry', 'lue_median_wet', 'lue_min', 'lue_stdDev', 'rba_median', 'rba_median_dry', 
    'rba_median_wet', 'rightness_median', 'rightness_median_dry', 'rightness_median_wet', 'si_median', 'si_median_dry', 'si_median_wet', 
    'ai_median', 'ai_median_dry', 'ai_stdDev', 'loud_median_dry', 'loud_median_wet', 'loud_min', 'loud_stdDev', 'swi5_median', 
    'swi5_median_dry', 'swi5_median_wet', 'vi2_amp', 'vi2_median', 'vi2_median_dry', 'vi2_median_wet', 'vi2_stdDev', 'cvi_median', 
    'cvi_median_dry', 'cvi_median_wet', 'cvi_stdDev', 'emi_median', 'emi_median_dry', 'emi_median_wet', 'li_median', 'li_median_dry', 
    'li_median_wet', 'reen_median', 'reen_median_dry', 'reen_median_texture', 'reen_median_wet', 'reen_min', 'reen_stdDev', 'v_amp', 
    'v_max', 'v_median', 'v_median_dry', 'v_median_wet', 'v_min', 'v_stdDev', 'vmi_median', 'vmi_median_dry', 'vmi_median_wet', 
    'vs_amp', 'vs_max', 'vs_median', 'vs_median_dry', 'vs_median_wet', 'vs_min', 'vs_stdDev', 'allcover_median', 'allcover_stdDev', 
    'illshade', 'ia_median', 'ia_median_dry', 'ia_median_wet', 'swi_median', 'swi_median_dry', 'swi_median_wet', 'bi_median', 
    'bi_median_dry', 'bi_median_wet', 'dbi_median', 'dbi_median_dry', 'dbi_median_wet', 'ddi_median', 'ddi_median_dry', 'ddi_median_wet', 
    'dfi_amp', 'dfi_max', 'dfi_median', 'dfi_median_dry', 'dfi_median_wet', 'dfi_min', 'dfi_stdDev', 'dfia', 'dfia_2', 'dmi_median', 
    'dmi_median_dry', 'dmi_median_wet', 'dti_median', 'dti_median_dry', 'dti_median_wet', 'dvi_amp', 'dvi_median', 'dvi_median_dry', 
    'dvi_median_wet', 'dvi_stdDev', 'dwi_amp', 'dwi_median', 'dwi_median_dry', 'dwi_median_wet', 'dwi_stdDev', 'ir_median', 
    'ir_median_contrast', 'ir_median_dry', 'ir_median_dry_contrast', 'ir_median_wet', 'ir_min', 'ir_stdDev', 'pv_amp', 'pv_max', 
    'pv_median', 'pv_median_dry', 'pv_median_wet', 'pv_min', 'pv_stdDev', 'savi_median', 'savi_median_dry', 'savi_median_wet', 
    'ri_median', 'ri_median_dry', 'ri_median_wet', 'atio_median', 'atio_median_dry', 'atio_median_wet', 'ed_edge_2_median', 
    'ed_edge_2_median_dry', 'ed_edge_2_median_wet', 'ed_edge_2_min', 'ed_edge_2_stdDev', 'ed_edge_3_median', 'ed_edge_3_median_dry', 
    'ed_edge_3_median_wet', 'ed_edge_3_min', 'ed_edge_3_stdDev', 'ed_edge_4_median', 'ed_edge_4_median_dry', 'ed_edge_4_median_wet', 
    'ed_edge_4_min', 'ed_edge_4_stdDev', 'ed_median', 'ed_median_contrast', 'ed_median_dry', 'ed_median_dry_contrast', 'ed_median_wet', 
    'ed_min', 'ed_stdDev', 'i_median', 'i_median_dry', 'i_median_wet', 'avi_median', 'avi_median_dry', 'avi_median_wet', 'avi_stdDev', 
    'efi_median', 'efi_median_dry', 'efi_stdDev', 'hade_amp', 'hade_max', 'hade_median', 'hade_median_dry', 'hade_median_wet', 
    'hade_min', 'hade_stdDev', 'hape_median', 'hape_median_dry', 'hape_median_wet', 'lope', 'oil_amp', 'oil_max', 'oil_median', 
    'oil_median_dry', 'oil_median_wet', 'oil_min', 'oil_stdDev', 'wir1_median', 'wir1_median_dry', 'wir1_median_wet', 'wir1_min', 
    'wir1_stdDev', 'wir2_median', 'wir2_median_dry', 'wir2_median_wet', 'wir2_min', 'wir2_stdDev', 'efi_amp', 'efi_median_wet', 
    'etness_median', 'etness_median_dry', 'etness_median_wet'
]

# Remove duplicatas mantendo consistência
LST_COLUMNS = sorted(list(set(RAW_COLUMNS)))

YEAR_INIC = 2016
YEAR_END = 2025

class AnomalyDetector:
    # Dicionário estático para mapeamento
    DICT_CLASS = {
        3: 0, 4: 1, 12: 3, 15: 4, 18: 5, 
        21: 6, 22: 7, 33: 8, 29: 9
    }

    def __init__(self, csv_path, list_columns):
        self.csv_path = Path(csv_path)
        print(f"Loading {self.csv_path.name}...")
        self.nbacia = self.csv_path.stem
        self.list_columns = list_columns
        
    def preprocess_geodata(self, df):
        """Realiza o pré-processamento vetorizado (muito mais rápido que apply row-by-row)"""
        
        # 1. Mapeamento de Classe
        df['classe'] = df['class'].map(self.DICT_CLASS)
        
        # 2. Extração de Geometria via Regex Vetorizado
        # Assume formato: {"type":"Point","coordinates":[LONG, LAT]}
        # O Regex captura dois grupos numéricos dentro dos colchetes
        coords = df['.geo'].str.extract(r'coordinates":\[(.*?),(.*?)\]')
        df['Longitude'] = coords[0].astype(float)
        df['Latitude'] = coords[1].astype(float)
        
        return df

    def run_process(self):
        # Leitura única do CSV
        try:
            df_full = pd.read_csv(self.csv_path)
        except Exception as e:
            print(f"Erro ao ler {self.csv_path}: {e}")
            return

        # Pré-processamento inicial (Geometry e Classes)
        df_full = self.preprocess_geodata(df_full)
        
        lst_cleaned_dfs = []
        
        # Loop pelos anos
        years = range(YEAR_INIC, YEAR_END + 1)
        for year in tqdm(years, desc=f"Processando Bacia {self.nbacia}"):
            df_year = df_full[df_full['year'] == year].copy()
            
            if df_year.empty:
                continue

            # Garante que temos as colunas necessárias para o modelo
            cols_to_use = [c for c in self.list_columns if c in df_year.columns]
            
            # Divide os dados para limpeza (Floresta/Savana/Campo vs Pasto/Agri/Mosaico)
            # Grupo 1: Classes 3, 4, 12
            mask_g1 = df_year['class'].isin([3, 4, 12])
            clean_g1 = self.apply_isolation_forest(df_year[mask_g1], cols_to_use)
            
            # Grupo 2: Classes 15, 18, 21
            mask_g2 = df_year['class'].isin([15, 18, 21])
            clean_g2 = self.apply_isolation_forest(df_year[mask_g2], cols_to_use)
            
            # Grupo 3: Outros (sem limpeza, apenas concatenação)
            mask_g3 = df_year['class'].isin([22, 33, 29])
            others_g3 = df_year[mask_g3]

            # Concatena resultados do ano
            df_year_cleaned = pd.concat([clean_g1, clean_g2, others_g3])
            
            # Mantém apenas colunas relevantes para exportação
            cols_export = list(set(cols_to_use + ['Longitude', 'Latitude', 'classe', 'year', 'class']))
            # Intersecção segura de colunas
            cols_export = [c for c in cols_export if c in df_year_cleaned.columns]
            
            lst_cleaned_dfs.append(df_year_cleaned[cols_export])
    
        if lst_cleaned_dfs:
            data_final = pd.concat(lst_cleaned_dfs)
            output_path = self.csv_path.replace('/rois/', '/rois/cleaned/')
            data_final.to_csv(output_path, index=False)
            print(f"Exportado com sucesso: {output_path} | Shape final: {data_final.shape}")
        else:
            print("Nenhum dado processado para exportar.")

    def apply_isolation_forest(self, df_subset, feature_cols):
        if df_subset.empty:
            return df_subset
            
        X = df_subset[feature_cols]
        
        # Tratamento de NaN simples se houver (IsolationForest não gosta de NaN)
        X = X.fillna(0) 

        # Isolation Forest
        clf = IsolationForest(
            n_estimators=300, # 500 pode ser overkill para muitos dados, 300 é robusto
            contamination='auto',
            bootstrap=True,
            n_jobs=-1,
            random_state=42
        )
        
        # Ajuste e Predição
        # O modelo retorna 1 para inliers e -1 para outliers
        y_pred = clf.fit_predict(X)
        
        # Filtrar inliers (valor 1)
        return df_subset[y_pred == 1].copy()

# --- EXECUÇÃO ---

if __name__ == "__main__":
    # Defina seus caminhos aqui
    BASE_DIR = Path('/home/superuser/Dados/mapbiomas/dev_col2_Sentinel_MB/src/dados/rois')
    
    # Pega todos os CSVs recursivamente ou na pasta
    csv_files = list(BASE_DIR.glob('*.csv'))
    
    # Filtra para não processar os arquivos que já são "_cleaned"
    csv_files = [f for f in csv_files if '_cleaned' not in f.name]

    print(f"Encontrados {len(csv_files)} arquivos para processar.")

    # Loop principal para processar TODOS os arquivos
    for csv_file in csv_files:
        try:
            processor = AnomalyDetector(csv_file, LST_COLUMNS)
            processor.run_process()
        except Exception as e:
            print(f"Falha crítica no arquivo {csv_file}: {e}")