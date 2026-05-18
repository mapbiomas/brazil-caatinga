#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#  SCRIPT DE CALCULO DE AREA POR AREAS PRIORITARIAS DA CAATINGA
#  Produzido por Geodatin - Dados e Geoinformacao
#  DISTRIBUIDO COM GPLv2

#  Relação de camadas para destaques:
#  Assentamento_Brasil - Asentamentos 
#  nucleos_desertificacao - Nucleos de desertificação,
#  UnidadesConservacao_S - Unidades de conservação  -> 'TipoUso' -> ["Proteção Integral", "Proteção integral",  "Uso Sustentável"]
#  unidade_gerenc_RH_SNIRH_2020- Unidade de gerenciamento de recursos Hidricos 
#  tis_poligonais_portarias -  Terras indígenas
#  prioridade-conservacao - Prioridade de conservação (usar apenas Extremamente alta)
#  florestaspublicas - Unidades de conservação
#  areas_Quilombolas - áreas quilombolas
#  macro_RH - Bacias hidrográficas 
#  reserva da biosfera - 'zona' ->  ["nucleo","transicao","amortecimento"]
#  Novo limite do semiarido 2024


'''
import ee
import os 
# import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount) #
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

def processoExportar(areaFeat, nameT):      
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': 'areas_shps_public'        
        }    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")   

param = {    
    "Assentamento_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
    "BR_ESTADOS_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
    "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
    "br_estados_shp": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
    "BR_Municipios_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
    "BR_Pais_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
    "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
    'vetor_biomas_250': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'biomas_250_rasters': 'projects/mapbiomas-workspace/AUXILIAR/RASTER/Bioma250mil',
    "Sigef_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sigef_Brasil",
    "Sistema_Costeiro_Marinho" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sistema_Costeiro_Marinho",
    "aapd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/aapd",
    "areas_Quilombolas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/areas_Quilombolas",
    "buffer_pts_energias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/buffer_pts_energias",
    "energias-dissolve-aneel" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/energias-dissolve-aneel",
    "florestaspublicas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/florestaspublicas",
    "imovel_certificado_SNCI_br" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/imovel_certificado_SNCI_br",
    "macro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
    "meso_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/meso_RH",
    "micro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/micro_RH",
    "pnrh_asd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_asd",
    "prioridade-conservacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/prioridade-conservacao-caatinga-ibama",
    "prioridade-conservacao-V1" : "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V1",
    "prioridade-conservacao-V2" : "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V2",
    "tis_poligonais_portarias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/tis_poligonais_portarias",
    "transposicao-cbhsf" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/transposicao-cbhsf",
    "nucleos_desertificacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
    "UnidadesConservacao_S" : "projects/mapbiomas-workspace/AUXILIAR/areas-protegidas",
    "unidade_gerenc_RH_SNIRH_2020" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
    "reserva_biosfera" : "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
    "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
    'semiarido' : 'users/mapbiomascaatinga04/semiarido_rec',
    "irrigacao": 'projects/ee-mapbiomascaatinga04/assets/polos_irrigaaco_atlas',
    "energiasE": 'projects/ee-mapbiomascaatinga04/assets/energias_renovaveis',
    "bacia_sao_francisco" : 'users/solkancengine17/shps_public/bacia_sao_francisco',
    "matopiba": 'projects/mapbiomas-fogo/assets/territories/matopiba'
}
lstEst = ['21','22','23','24','25','26','27','28','29','31','32']
lst_nameAsset = [
    'Assentamento_Brasil', 
    "nucleos_desertificacao",
    "UnidadesConservacao_S", 
    'areas_Quilombolas', 
    "macro_RH", "meso_RH", 
    'micro_RH', 
    'prioridade-conservacao-V1', 
    'prioridade-conservacao-V2', 
    'tis_poligonais_portarias', 
    "reserva_biosfera",
    'matopiba',
    "energiasE",    
    "bacia_sao_francisco",
]

dictEst = {
    '21': 'MARANHÃO',
    '22': 'PIAUÍ',
    '23': 'CEARÁ',
    '24': 'RIO GRANDE DO NORTE',
    '25': 'PARAÍBA',
    '26': 'PERNAMBUCO',
    '27': 'ALAGOAS',
    '28': 'SERGIPE',
    '29': 'BAHIA',
    '31': 'MINAS GERAIS',
    '32': 'ESPÍRITO SANTO'
}
feat_areas = ee.FeatureCollection([])
# Addicionando os dados de shp Caatinga
shp_Caatinga = (ee.FeatureCollection(param['vetor_biomas_250']) 
                    .filter(ee.Filter.eq('CD_Bioma', 2)).geometry()
                )

feat_tmp = ee.Feature(None, {})
feat_tmp = feat_tmp.set(
                'shp_region', 'Caatinga',
                'shp_subregion', 'Caatinga',
                'area_ha', ee.Number(shp_Caatinga.area()).divide(10000)
                )

feat_areas = feat_areas.merge(ee.FeatureCollection([feat_tmp]))
# Addicionando os dados de shp Semiarido
shp_Semiarido = ee.FeatureCollection(param['semiarido2024']).geometry()                   

feat_tmp = ee.Feature(None, {})
feat_tmp = feat_tmp.set(
                'shp_region', 'Semiarido',
                'shp_subregion', 'Semiarido',
                'area_ha', ee.Number(shp_Semiarido.area()).divide(10000)
                )

feat_areas = feat_areas.merge(ee.FeatureCollection([feat_tmp]))
estados_vetor = (ee.FeatureCollection(param['br_estados_shp'])
                          .filter(ee.Filter.inList('CD_GEOCUF', lstEst)))


lstlimit = ['estado', 'Caatinga', 'Semiarido']
for nlim in lstlimit:
    for mun_id in lstEst:
        est_rec = estados_vetor.filter(ee.Filter.eq('CD_GEOCUF', mun_id)).geometry()
        feat_tmp = ee.Feature(None, {})
        if nlim == 'estado':
            est_area = est_rec.area()
            feat_tmp = feat_tmp.set(
                'shp_region', dictEst[mun_id],
                'shp_subregion', dictEst[mun_id],
                'area_ha', ee.Number(est_area).divide(10000)
                )
        elif nlim == 'Caatinga':
            est_area = est_rec.intersection(shp_Caatinga).area()
            feat_tmp = feat_tmp.set(
                'shp_region', 'Caatinga',
                'shp_subregion', dictEst[mun_id],
                'area_ha', ee.Number(est_area).divide(10000)
                )
        else:
            est_area = est_rec.intersection(shp_Caatinga).area()
            feat_tmp = feat_tmp.set(
                'shp_region', 'Semiarido',
                'shp_subregion', dictEst[mun_id],
                'area_ha', ee.Number(est_area).divide(10000)
                )
        
        print(f"adding region > {nlim} and subregion {mun_id} ")
        feat_areas = feat_areas.merge(ee.FeatureCollection([feat_tmp]))



for name_asset in lst_nameAsset:
    print(f"load >> {name_asset}")
    shp_tmp = ee.FeatureCollection(param[name_asset]).geometry()

    for nlim in lstlimit:
        feat_tmp = ee.Feature(None, {})
        if nlim == 'estado':
            est_area = shp_tmp.area()
            feat_tmp = feat_tmp.set(
                'shp_region', name_asset,
                'shp_subregion', name_asset,
                'area_ha', ee.Number(est_area).divide(10000)
                )
        elif nlim == 'Caatinga':
            est_area = shp_tmp.intersection(shp_Caatinga).area()
            feat_tmp = feat_tmp.set(
                'shp_region', 'Caatinga',
                'shp_subregion', name_asset,
                'area_ha', ee.Number(est_area).divide(10000)
                )
        else:
            est_area = est_rec.intersection(shp_Caatinga).area()
            feat_tmp = feat_tmp.set(
                'shp_region', 'Semiarido',
                'shp_subregion', name_asset,
                'area_ha', ee.Number(est_area).divide(10000)
                )
        
        print(f"adding region > {nlim} and subregion {name_asset} ")
        feat_areas = feat_areas.merge(ee.FeatureCollection([feat_tmp]))


processoExportar(feat_areas, 'table_areas_shps_publicos')


