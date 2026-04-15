#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee 
import sys
import os
import json
from pathlib import Path
from tqdm import tqdm
import collections

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('✅ The Earth Engine package initialized successfully!')
except Exception as e:
    print(f"❌ Erro ao inicializar o GEE: {e}")
    sys.exit()

def processoExportar(ROIsFeat, IdAsset, nameB):
    """Agenda a tarefa de exportação para a nuvem do Google."""
   
    optExp = {
        'collection': ROIsFeat, 
        'description': nameB, 
        'assetId': f"{IdAsset}/{nameB}"          
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start() 
    print(f"⏳ Tarefa agendada: salvando ... {nameB}!")   


dictGroup = {
        'vegetation' : [3, 4],
        'agropecuaria': [15, 21], # Adicionado 18 e 19 conforme uso de classes agro
        'outros': [12, 22, 25, 33, 29, 36, 19]
    } 

dictQtLimit = {
    '3': 5000, '4': 10000, '12': 3200, '15': 8000,
    '18': 8000, '19': 3000, '21': 4000, '22': 3000,
    '25': 3000, '29': 2000, '33': 2000, '36': 1600
}
param = {
    "asset_folder": "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_byBasinInd",
    "asset_output": "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesv1CC",
}

nameBacias = ['7422', '7443', '7544']
# 1. Definimos EXATAMENTE o que precisa ser processado
procelstYear = True
bacias_faltantes = {
    '7422': [2020],
    '7443': [2021],
    '7544': [2005, 2015]
}
if len(bacias_faltantes.keys()) > 0:
    procelstYear = False
    
cc = 0
for cc, (nameBacia, lst_year) in enumerate(bacias_faltantes.items()): 

    for nyear in lst_year:
        print(f"#{cc} name Bacia {nameBacia}  >>> year {nyear}  ")     
        
        # ====== MÉTODO SIMPLES (make_complex = False) ======
        print(f"[{nyear}] Aplicando Método Simples (Downsample Direto)...")
        lista_fc_simples = []
        asset_feat_rois = f"{param["asset_folder"]}/rois_fromGrade_{nameBacia}" 
        fcYY = ee.FeatureCollection(asset_feat_rois).filter(ee.Filter.eq('year', nyear)) 
        
        classes_configuradas = dictGroup['vegetation'] + dictGroup['agropecuaria']
        
        for nclass in classes_configuradas:
            classROIs = fcYY.filter(ee.Filter.eq('class', nclass))
            
            limit = dictQtLimit[str(nclass)]
            sizeFilt = classROIs.size().max(1)
            
            # Mesma matemática limpa para o método simples
            fracao_manter = ee.Number(limit).divide(sizeFilt).min(1.0)
            
            classROIsSel = (classROIs.randomColumn('rand_simples')
                                    .filter(ee.Filter.lt('rand_simples', fracao_manter)))
            lista_fc_simples.append(classROIsSel)

        outras_classes = fcYY.filter(ee.Filter.inList('class', dictGroup['outros']))
        lista_fc_simples.append(outras_classes)
        
        feaReSamples = ee.FeatureCollection(lista_fc_simples).flatten()
        # feaReSamples = feaReSamples.map(lambda feat: feat.set('class', ee.Number.parse(feat.get('class')).toFloat()))
        
        processoExportar(feaReSamples, param["asset_output"], f"rois_fromGrade_{nameBacia}_{nyear}")
