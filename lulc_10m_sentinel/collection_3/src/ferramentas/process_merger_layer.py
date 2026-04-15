#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''
import os
import ee 
import sys
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
# Certifique-se que estes módulos existem no seu ambiente
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

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
sys.setrecursionlimit(1000000000)

# ... (Seus parâmetros permanecem iguais) ...
param = {
    'inputAssetpolg': {'id':'users/CartasSol/coleta/polygonsCorr'},
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'assetMap': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
    'input_solo': 'users/diegocosta/doctorate/Bare_Soils_Caatinga',
    'outputAsset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',
    'asset_florestErrNe' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/shpExtraspoligons_rev_sombrasrelNer',
    'asset_florestErrRa' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/shpExtraspoligons_rev_sombrasrelRaf',
    'asset_afloramentoPol' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/shpExtraspoligons_rev_afloramento',
    'asset_restingaNeri' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/poligons_region_restingaNeri',
    'asset_restingaRafa' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/poligons_region_restingaRafa',
    'correct_past_to_Grass' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/shpExtras/geom_correct21_12_7612_7613_76116',
    'asset_mask_aflora':'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/layer_afloramento_campo_cluster',
    'asset_campo_chapada': 'users/mapbiomascaatinga04/ROI_AREAS_CAMPO_CHAPADA',
    'asset_bioma_raster' : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'asset_uso_mata_atlantica': 'projects/ee-mapbiomascaatinga04/assets/bacias_mata_caatinga',
    'year_first': 2016,
    'year_end': 2025,
    'versionInput': 5,
    'versionOutput': 7,
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62,75],
    'classNew':  [3, 4, 3, 3,12,12,21,21,21,21,21,25,25,25,25,33,29,25,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21,49,50,21,25],
    'numeroTask': 6,
    'numeroLimit': 14,
    'conta' : {
        '0': 'caatinga01',
        '4': 'caatinga02',
        '6': 'caatinga03',
        '8': 'caatinga04',
        '10': 'caatinga05',        
        '12': 'solkan1201',         
    }
}
nameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765'
]
nameBaciasRodadas = [ ] # "757","755","754","753"

dict_class = {
    '3':  'Forest Formation',
    '4':  'Savanna Formation',
    '12': 'Grassland',
    '21': 'Mosaic of Uses',
    '22': 'Non vegetated area',
    '29': 'Rocky Outcrop',
    '33': 'Water',
    '50': 'restinga',
    '49': 'restinga',
    '48': 'Lavouras Perenes',
    '9' : 'Forest Plantation'
}

lst_Bacia_aflo = [
    '754','755','756','757','763',
    '764','765','766','771','772','7741',
    '7742','776','777','778','7615',
    '7616','7617','7618','7619'
]
lst_bacias_restinga = ["757","755","754","753"]
lst_bacias_relebo = [
    '741', '7421', '7422', '744', '745', '746', '7492', '751', '752', 
    '753', '754', '756', '7621', '763', '765', '771', '772', '773', 
    '7741', '7742', '776', '7612', '7615', '7619', '7613'
]
lst_bacias_campo_chapada = ['776', '7741']
lst_bacias_uso_MA = ['757', '758', '759', '76111', '76116', '771', '772', '773']

#============================================================
#========================METODOS=============================
#============================================================

mapsSoil = ee.Image(param['input_solo'])
layerSoilYY = ee.Image.constant(0)
for yyear in range(param['year_first'], param['year_end'] + 1):
    if yyear < 2019:
        bandSoil = f"Caatinga_{yyear}_classification_{yyear}"
        layerSoilYY = layerSoilYY.add(mapsSoil.select(bandSoil).gt(0))
    
layerSoilYY = layerSoilYY.reduce(ee.Reducer.sum()).gt(1)

def GetPolygonsfromFolder():
    getlistPtos = ee.data.getList(param['inputAssetpolg'])    
    dict_pol = {}
    for idAsset in getlistPtos:         
        path_ = idAsset.get('id')
        lsFile =  path_.split("/")
        name = lsFile[-1]
        nameBacia = name.split('_')[1]
        dict_pol[nameBacia] = path_
    return  dict_pol


def corregir_pixels_Aflora(imgClass_temp, bufferBacia, maskAflo, nameBac):
    rec_maskAflo = maskAflo.unmask(0)
    lstBandNames = ['classification_' + str(yy) for yy in range(param['year_first'], param['year_end'] + 1)]
    imgClassFinal = ee.Image().toByte()

    for yyear in range(param['year_first'], param['year_end'] + 1):
        # print("###### change pixels Afloramento in year [{}] ########".format(yyear))
        bandaAct = 'classification_' + str(yyear)
        imgClasBand = ee.Image(imgClass_temp.select(bandaAct))
        imgClasBand = imgClasBand.where(rec_maskAflo.gt(0), 29)
        bandaAct = 'classification_' + str(yyear)
        imgClassFinal = imgClassFinal.addBands(imgClasBand.rename(bandaAct))

    return imgClassFinal.select(lstBandNames)

def corregir_pixels_inPol_Restinga(imgClass_temp, bufferBacia, maskBufferBacia , nameBac): # polRestinga,
    
    # coleção 10 camada para extrair a retingas 
    layerVers10 = ee.Image(param['assetMap']).updateMask(maskBufferBacia)
    
    # polRestinga = ee.Geometry(polRestinga)
    lstBandNames = ['classification_' + str(yy) for yy in range(param['year_first'], param['year_end'] + 1)]
    imgClassFinal = ee.Image().toByte()
    # maskBacias = bufferBacia.map
    # # O erro pode ocorrer aqui se bufferBacia for vazio
    # areaFixa = ee.Feature(bufferBacia.difference(polRestinga), {'value': 1})
    # areaToChange = ee.Feature(polRestinga, {'value': 0})
    # areaTo_mask = ee.FeatureCollection([areaFixa, areaToChange])
    # img_mask_err = areaTo_mask.reduceToImage(['value'], ee.Reducer.first())
    # maskToChange = img_mask_err.eq(0) 

    # maskRestinga = 

    for yyear in range(param['year_first'], param['year_end'] + 1):
        # print("###### change pixels Restinga in year [{}] ########".format(yyear))
        bandaAct = 'classification_' + str(yyear)
        imgClasBand = ee.Image(imgClass_temp.select(bandaAct))
        # mapRecCorregir = imgClasBand.updateMask(maskToChange).unmask(0)
        if yyear < 2025: 
            map_restarb = layerVers10.select(bandaAct).eq(49)
            map_restherb = layerVers10.select(bandaAct).eq(50)
        else:
            map_restarb = layerVers10.select('classification_2024').eq(49)
            map_restherb = layerVers10.select('classification_2024').eq(50)

        imgClasBand = imgClasBand.where(map_restarb.eq(1), ee.Image.constant(49))
        imgClasBand = imgClasBand.where(map_restherb.eq(1), ee.Image.constant(50))

        bandaAct = 'classification_' + str(yyear)
        imgClassFinal = imgClassFinal.addBands(imgClasBand.rename(bandaAct))

    return imgClassFinal.select(lstBandNames)

def corregir_pixels_inPol_Relevo(imgClass_temp, bufferBacia, polRelevo, nameBac):
    lstBandNames = ['classification_' + str(yy) for yy in range(param['year_first'], param['year_end'] + 1)]
    imgClassFinal = ee.Image().toByte()
    
    areaFixa = ee.Feature(bufferBacia.difference(polRelevo), {'value': 1})
    areaToChange = ee.Feature(polRelevo, {'value': 0})
    areaTo_mask = ee.FeatureCollection([areaFixa, areaToChange])
    img_mask_err = areaTo_mask.reduceToImage(['value'], ee.Reducer.first())

    maskToChange = img_mask_err.eq(0) 

    for yyear in range(param['year_first'], param['year_end'] + 1):
        # print("###### change pixels with Relevo in year [{}] ########".format(yyear))
        bandaAct = 'classification_' + str(yyear)
        imgClasBand = ee.Image(imgClass_temp.select(bandaAct))      
        mapRecCorregir = imgClasBand.updateMask(maskToChange).unmask(0)
        
        mapaBinarioDe3 = mapRecCorregir.eq(3) 
        mapaBinarioDe33 = mapRecCorregir.eq(33)
        mapaBinarioDe = mapaBinarioDe3.add(mapaBinarioDe33).gt(0)
        imgClasBand = imgClasBand.where(mapaBinarioDe.eq(1), mapaBinarioDe.multiply(4))
        
        bandaAct = 'classification_' + str(yyear)
        imgClassFinal = imgClassFinal.addBands(imgClasBand.rename(bandaAct))

    return imgClassFinal.select(lstBandNames)

def integration_soil_layer(imgClass_temp, bufferBacia, nameBac):
    lstBandNames = ['classification_' + str(yy) for yy in range(param['year_first'], param['year_end'] + 1)]
    imgClassFinal = ee.Image().toByte()

    for yyear in range(param['year_first'], param['year_end'] + 1):
        # print("###### change pixels with Soil in year [{}] ########".format(yyear))
        bandaAct = 'classification_' + str(yyear)
        imgClasBand = (ee.Image(imgClass_temp.select(bandaAct)) 
                        .remap(param['classMapB'], param['classNew'])       
                    )       
        imgClasBand = imgClasBand.where(layerSoilYY.eq(1), 25)
        imgClassFinal = imgClassFinal.addBands(imgClasBand.rename(bandaAct))

    return imgClassFinal.select(lstBandNames)

def corregir_pixels_campos_chapada(imgClass_temp, bufferBacia, maskChapada, nameBac):
    layerVers10 = ee.Image(param['assetMap'])        
    
    areaFixa = ee.Feature(bufferBacia.difference(maskChapada.geometry()), {'value': 0}) 
    areaToChange = ee.Feature(maskChapada.geometry(), {'value': 1})
    areaTo_mask = ee.FeatureCollection([areaFixa, areaToChange])
    maskToChange = areaTo_mask.reduceToImage(['value'], ee.Reducer.first())
    
    lstBandNames = ['classification_' + str(yy) for yy in range(param['year_first'], param['year_end'] + 1)]
    imgClassFinal = ee.Image().toByte()

    for yyear in range(param['year_first'], param['year_end'] + 1):
        # print("###### change pixels Campo in year [{}] ########".format(yyear))
        bandaAct = 'classification_' + str(yyear)
        imgClasBand = ee.Image(imgClass_temp.select(bandaAct))
        if yyear < 2025:
            layer_campo = layerVers10.select(bandaAct).eq(12)
        else:
            layer_campo = layerVers10.select('classification_2024').eq(12)
        layer_campo = maskToChange.eq(1).And(layer_campo.eq(1))
        imgClasBand = imgClasBand.where(layer_campo.eq(1), 12)
        bandaAct = 'classification_' + str(yyear)
        imgClassFinal = imgClassFinal.addBands(imgClasBand.rename(bandaAct))

    return imgClassFinal.select(lstBandNames)



#exporta a imagem classificada para o asset
def processoExportar(mapaRF,  nomeDesc, geom_bacia):    
    idasset =  os.path.join(param['outputAsset'], nomeDesc)
    optExp = {
        'image': ee.Image.cat(mapaRF).toByte(), 
        'description': nomeDesc, 
        'assetId': idasset, 
        'region': ee.Geometry(geom_bacia), 
        'scale': 10, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"}
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")

def gerenciador(cont):    
    numberofChange = [kk for kk in param['conta'].keys()]
    # print(numberofChange)    
    
    if str(cont) in numberofChange:
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) 
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 

        # Se relatorios for usado, precisa estar definido globalmente ou passado como parametro
        # relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')
        # tarefas = tasks(n= param['numeroTask'], return_list= True)
        # for lin in tarefas: relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

## ============================================================##
## ==================LOADING ALL DATASETS =====================##
## ============================================================##
changeCount = True
lstBands = ['classification_' + str(yy) for yy in range(param['year_first'], param['year_end'] + 1)]

dict_bacias_asset = GetPolygonsfromFolder()
lst_keyBacias = [kk for kk in dict_bacias_asset.keys()]

polg_sombra = ee.FeatureCollection(param['asset_florestErrNe']).merge(
                        ee.FeatureCollection(param['asset_florestErrRa'])).geometry()
# polg_restinga = ee.FeatureCollection(param['asset_restingaNeri']).merge(
#                         ee.FeatureCollection(param['asset_restingaRafa'])).geometry()

mask_afloramento = ee.Image(param['asset_mask_aflora'])


limite_chapada = ee.FeatureCollection(param['asset_campo_chapada'])
limit_regions_MA = ee.FeatureCollection(param['asset_uso_mata_atlantica'])

geoBacias = ee.FeatureCollection(param['asset_bacias_buffer']).map(lambda f: f.set('id_codigo', 1))

cont = 16
list_corr = []

# ============================================================
# LOOP PRINCIPAL COM CORREÇÃO DE ERRO DE GEOMETRIA VAZIA
# ============================================================
pos_inic = 0
pos_end = 50
for cc, nameBa in enumerate(nameBacias[pos_inic: pos_end]):
    
    if nameBa not in nameBaciasRodadas:

        print(f"########## 🔊 {cc + pos_inic + 1}/{len(nameBacias)}  LOADING BASIN {nameBa} IN VERSAO {param['versionInput']} 🔊 ###############")
        
        # 1. Obter a FeatureCollection da bacia
        limite_bacia_fc = geoBacias.filter(ee.Filter.eq('nunivotto4', nameBa))
        
        # 🟢 [CORREÇÃO 1]: Verificar se a bacia existe no asset vetorial
        # O getInfo() aqui é seguro pois estamos apenas pegando o tamanho, não baixando dados pesados.
        bacia_size = limite_bacia_fc.size().getInfo()
        
        if bacia_size == 0:
            print(f"🔴 ERRO: Bacia {nameBa} não encontrada no asset vetorial (size=0). Pulando...")
            continue
            
        # 2. Obter a Imagem de Entrada
        imgClass =  (ee.ImageCollection(param['input_asset'])
                        .filter(ee.Filter.eq('version', param['versionInput']))
                        .filter(ee.Filter.eq('id_bacias', nameBa ))
                        .first()
                )
        
        # 🟢 [CORREÇÃO 2]: Verificar se a imagem de entrada existe
        # Se first() retornar None, o Python falha ao tentar chamar métodos em NoneType
        if imgClass is None:
             print(f"🔴 ERRO: Imagem para Bacia {nameBa} (v{param['versionInput']}) não encontrada na coleção. Pulando...")
             continue
        
        # Se imgClass existe, mas é um objeto EE "nulo" (computado), precisamos verificar server-side
        # A maneira mais robusta é verificar uma propriedade, mas a verificação acima 'is None' captura o caso mais comum do .first() local

        # Agora é seguro obter informações
        name_imgClassSp = imgClass.get('system:index').getInfo()
        bandasImgMap = imgClass.bandNames().getInfo()
        print("Bacia ", nameBa, " => numero de bandas ", len(bandasImgMap))

        # Criar a máscara raster e a geometria para processamento
        mask_bacia_raster = limite_bacia_fc.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)     
        limite_bacia_geom = limite_bacia_fc.geometry()

        # Início do processamento
        imgBaClass = integration_soil_layer(imgClass, limite_bacia_geom, nameBa)

        print(" layer soil ", imgBaClass.bandNames().getInfo())
        
        if nameBa in lst_Bacia_aflo:
            imgBaClass = corregir_pixels_Aflora(imgBaClass, limite_bacia_geom, mask_afloramento, nameBa)

        if nameBa in lst_bacias_restinga:
            print("====== PROCESSANDO RESTINGA =======")
            imgBaClass = corregir_pixels_inPol_Restinga(imgBaClass, limite_bacia_geom, mask_bacia_raster, nameBa)
            # print("know bandas restinga ", imgBaClass.bandNames().getInfo())
        if nameBa in lst_bacias_campo_chapada:
            imgBaClass = corregir_pixels_campos_chapada(imgBaClass, limite_bacia_geom, limite_chapada, nameBa)

        # print("know bandas ", imgBaClass.bandNames().getInfo())

        name_mapExp = f"filterMixed_BACIA_{nameBa}_GTB_V{param['versionOutput']}"
        imgBaClass = imgBaClass.set(
                            'version', param['versionOutput'],
                            'biome', 'CAATINGA',
                            'collection', '3.0',
                            'id_bacias', nameBa,
                            'sensor', 'sentinel', 
                            'source','geodatin', 
                            'model', 'GTB', 
                            'system:footprint', limite_bacia_geom
                        )
        
        # Passando a geometria correta para a função de exportação
        processoExportar(imgBaClass.updateMask(mask_bacia_raster), name_mapExp, limite_bacia_geom)
        
        # cont = gerenciador(cont)