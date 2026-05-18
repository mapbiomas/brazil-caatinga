#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Otimizado por: Gemini (Assistent AI)
    Original: Geodatin - Dados e Geoinformacao
    DISTRIBUIDO COM GPLv2
"""

import ee
import os
import sys
import collections
collections.Callable = collections.abc.Callable
from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


# --- 1. DEFINIÇÃO DE ASSETS E VARIÁVEIS ---
year_inic = 2016
year_end = 2025

# Asset de Entrada (Amostras Brutas)
ASSET_INPUT = {"id": "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3"}

# Asset de Saída (Amostras Limpas)
# Corrigi o final do nome para '_cleaned' para manter padrão
ASSET_OUTPUT_ID = "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3_cleaned"

# Lista de bandas (Features) para o modelo aprender
BANDS = [
    'A00', 'A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08', 'A09', 'A10', 'A11', 'A12', 'A13', 
    'A14', 'A15', 'A16', 'A17', 'A18', 'A19', 'A20', 'A21', 'A22', 'A23', 'A24', 'A25', 'A26', 'A27', 
    'A28', 'A29', 'A30', 'A31', 'A32', 'A33', 'A34', 'A35', 'A36', 'A37', 'A38', 'A39', 'A40', 'A41', 
    'A42', 'A43', 'A44', 'A45', 'A46', 'A47', 'A48', 'A49', 'A50', 'A51', 'A52', 'A53', 'A54', 'A55', 
    'A56', 'A57', 'A58', 'A59', 'A60', 'A61', 'A62', 'A63', 'afvi_median', 'afvi_median_dry', 'afvi_median_wet', 
    'avi_median', 'avi_median_dry', 'avi_median_wet', 'awei_median', 'awei_median_dry', 'awei_median_wet', 
    'blue_median', 'blue_median_dry', 'blue_median_wet',  'brba_median', 
    'brba_median_dry', 'brba_median_wet', 'brightness_median', 'brightness_median_dry', 'brightness_median_wet', 
    'bsi_median', 'bsi_median_dry', 'bsi_median_wet',  'cvi_median', 'cvi_median_dry', #  'cai_median', 'cai_median_dry',
    'cvi_median_wet', 'dswi5_median', 'dswi5_median_dry', 'dswi5_median_wet', # 'evi2_median', 'evi2_median_dry', 'evi2_median_wet',
    'evi_median', 'evi_median_dry', 'evi_median_wet', 
    'gcvi_median', 'gcvi_median_dry', 'gcvi_median_wet', 'gemi_median', 'gemi_median_dry', 
    'gemi_median_wet', 'gli_median', 'gli_median_dry', 'gli_median_wet', 'green_median', 'green_median_dry', 
    'green_median_texture', 'green_median_wet',  'gv_median', 
    'gv_median_dry', 'gv_median_wet', 'gvmi_median', 'gvmi_median_dry', 'gvmi_median_wet', 
    'iia_median', 'iia_median_dry', 'iia_median_wet', 'lswi_median', 'lswi_median_dry', 
    'lswi_median_wet', 'mbi_median', 'mbi_median_dry', 'mbi_median_wet', 'ndbi_median', 'ndbi_median_dry', 
    'ndbi_median_wet', 'nddi_median', 'nddi_median_dry', 'nddi_median_wet', 'ndfia', 
    'ndmi_median', #'ndfi_median_dry', 'ndfi_median_wet',
    'ndmi_median_dry', 'ndmi_median_wet', 'ndti_median', 'ndti_median_dry', 'ndti_median_wet', 
    'ndvi_median', 'ndvi_median_dry', 'ndvi_median_wet',  'ndwi_median', 'ndwi_median_dry', 
    'ndwi_median_wet', 'nir_median', 'nir_median_contrast', 'nir_median_dry', 'nir_median_dry_contrast', 
    'nir_median_wet', 'npv_median', 'npv_median_dry', 'npv_median_wet', 
    'osavi_median', 'osavi_median_dry', 'osavi_median_wet',
    #'pri_median', 'pri_median_dry', 'pri_median_wet', 
    'ratio_median', 'ratio_median_dry', 'ratio_median_wet', 'red_median', 'red_median_contrast', 'red_median_dry', 
    'red_median_dry_contrast', 'red_median_wet',  'ri_median', 'ri_median_dry', 'ri_median_wet', 
    'rvi_median', 'rvi_median_dry', 'rvi_median_wet',
    # 'savi_median', 'savi_median_dry', 'savi_median_wet', 
    # 'sefi_median', 'sefi_median_dry', 
    'slope', 
    'soil_median', 'soil_median_dry', 'soil_median_wet', 'swir1_median', 
    'swir1_median_dry', 'swir1_median_wet', 'swir2_median', 'swir2_median_dry', 'swir2_median_wet', 
    'ui_median', 'ui_median_dry', 'ui_median_wet', 
    # 'wefi_median', 'wefi_median_wet', 
    'wetness_median', 'wetness_median_dry', 'wetness_median_wet'
]

def save_ROIs_toAsset(collection, name):
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': os.path.join(ASSET_OUTPUT_ID, name)
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print(f"✅  exportando ROIs da bacia {name} to Asset  ... Task ID: {task.id}!")
    # print("Acompanhe o progresso na aba 'Tasks' do Code Editor ou via task.status()")


def match_bands(lst_bandas_rois):
    lst_bnd_e = []
    for kk in BANDS:
        if kk in lst_bandas_rois:
            lst_bnd_e.append(kk)
    return lst_bnd_e

def run_cleaning_process(name_export):
    print(f"\n--- Processando Bacia: {name_export} ---")
    
    asset_input_read = os.path.join(ASSET_INPUT['id'], name_export)
    try:
        samples_ROIs = ee.FeatureCollection(asset_input_read)
        # Check simples de acesso
        _ = samples_ROIs.first().get('year').getInfo()
    except:
        print(f"Erro ao acessar {asset_input_read} ou coleção vazia.")
        return
    
    feat_cleaned_exp = ee.FeatureCollection([])

    for yyear in range(year_inic, year_end + 1):
        feat_tmp = samples_ROIs.filter(ee.Filter.eq('year', yyear))
        
        # Pula se não tiver amostras no ano
        if feat_tmp.size().getInfo() == 0:
            continue
            
        print(f"Ano {yyear}: processando...")
        
        # Ajuste de bandas (borda vs miolo)
        if yyear == 2016 or yyear == 2025:
            lista_bandas_prop = BANDS[64:] 
        else:
            lista_bandas_prop = BANDS
            
        # ---------------------------------------------------------
        # 1. TREINAMENTO
        # ---------------------------------------------------------
        classifier = ee.Classifier.smileGradientTreeBoost(
            numberOfTrees=60,
            shrinkage=0.1,
            samplingRate=1.0,
            maxNodes=5,         # Mantendo seu parâmetro conservador
            loss='LeastAbsoluteDeviation'
        ).train(
            features=feat_tmp,
            classProperty='class',
            inputProperties=lista_bandas_prop
        )

        # ---------------------------------------------------------
        # 2. CLASSIFICAÇÃO EM CADEIA
        # ---------------------------------------------------------
        
        # Passo A: Classifica para obter a CLASSE PREDITA (Rótulo Duro)
        # Gera a propriedade: 'class_gtb'
        classified_hard = feat_tmp.classify(classifier, 'class_gtb')

        # Passo B: Classifica para obter o ARRAY DE PROBABILIDADES
        # Gera a propriedade: 'class_gtb_p' (que é uma lista/array)
        classified_all = classified_hard.classify(
            classifier.setOutputMode('MULTIPROBABILITY'), 
            'class_gtb_p'
        )

        # ---------------------------------------------------------
        # 3. REDUÇÃO (ARRAY -> ESCALAR) E FILTRAGEM
        # ---------------------------------------------------------
        def extract_prob_and_filter(feat):
            # 1. Recupera as classes para comparar
            y_real = feat.get('class')
            y_pred = feat.get('class_gtb')
            
            # 2. Processa a probabilidade
            # Pega o array bruto
            prob_array = ee.Array(feat.get('class_gtb_p'))
            # Acha o valor máximo dentro do array (a certeza da escolha)
            max_val = prob_array.reduce(ee.Reducer.max(), [0]).get([0])
            # Converte para 0-100 e Inteiro
            prob_int = ee.Number(max_val).multiply(100).toInt()
            
            # 3. Define as condições de filtro
            # Consistência: O modelo concorda com o dado original?
            is_consistent = ee.Algorithms.IsEqual(y_real, y_pred)
            # Confiança: A certeza é maior que o limiar (ex: 65)?
            is_confident = prob_int.gte(65) # <--- AQUI VOCÊ CONTROLA O RIGOR
            
            # 4. Retorna a feature com a NOVA PROPRIEDADE
            return feat.set({
                'prob_value': prob_int,  # <--- NOVA PROPRIEDADE SALVA (0-100)
                'keep_sample': is_consistent
            })

        # Aplica a função map
        processed_samples = classified_all.map(extract_prob_and_filter)
        
        # Filtra baseado na flag que criamos
        cleaned_samples = processed_samples.filter(ee.Filter.eq('keep_sample', True))
        
        # Remove as propriedades temporárias pesadas (o array e a flag)
        # Mantemos 'prob_value' e 'class_gtb' pois são úteis
        cols_final = cleaned_samples.first().propertyNames().removeAll(['class_gtb_p', 'keep_sample'])
        cleaned_final = cleaned_samples.select(cols_final)
        
        # Merge no acumulador final
        feat_cleaned_exp = feat_cleaned_exp.merge(cleaned_final)

    # Exportação final
    if feat_cleaned_exp.size().getInfo() > 0:
        save_ROIs_toAsset(feat_cleaned_exp, name_export)
    else:
        print(f"⚠️  Bacia {name_export} sem dados após limpeza.")
    

listaNameRegion = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]

if __name__ == '__main__':
    for cc, nbacia in enumerate(listaNameRegion[:1]):
        nbacia_rois = f"rois_grade_{nbacia}"
        print(f" # {cc}    ---- > {nbacia_rois}")
        run_cleaning_process(nbacia_rois)