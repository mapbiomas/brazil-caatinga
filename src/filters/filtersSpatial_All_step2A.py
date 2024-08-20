#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
# https://code.earthengine.google.com/0c432999045898bb6e40c1fb7238d32f
'''

import ee
import os 
import gee
import json
import csv
import copy
import sys
import math
import arqParametros as arqParams 
import collections
collections.Callable = collections.abc.Callable
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

param = {      
    'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3/',
    # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV3',
    # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/TemporalV3',
    # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2/',
    'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3',
    # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel',
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',            
    'last_year' : 2023,
    'first_year': 1985,
    'janela': 3,
    'step': 1,
    'versionOut' : 38,
    'versionInp' : 37,
    'numeroTask': 6,
    'numeroLimit': 90,
    'conta' : {
        '0': 'caatinga01',   # 
        '2': 'caatinga02',
        '4': 'caatinga03',
        '6': 'caatinga04',
        '8': 'caatinga05',        
        '10': 'solkan1201',    
        '12': 'solkanGeodatin',
        '14': 'diegoUEFS',
        '16': 'superconta'     
    }
}
lst_bands_years = ['classification_' + str(yy) for yy in range(param['first_year'], param['last_year'] + 1)]

def buildingLayerconnectado(imgClasse):
    lst_band_conn = ['classification_' + str(yy) + '_conn' for yy in range(param['first_year'], param['last_year'] + 1)]
    # / add connected pixels bands
    imageFilledConnected = imgClasse.addBands(
                                imgClasse.connectedPixelCount(200, True).rename(lst_band_conn))

    return imageFilledConnected


def apply_spatialFilterConn (name_bacia, nmodel):
    frequencyNat = False
    min_connect_pixel = 12
    geomBacia = ee.FeatureCollection(param['asset_bacias_buffer']).filter(
                ee.Filter.eq('nunivotto3', name_bacia)).first().geometry()


    if 'Temporal' in param['input_asset']:
        name_imgClass = 'filterTP_BACIA_'+ name_bacia + f"_GTB_J{param['janela']}_V" + str(param['versionInp'])
    elif "Frequenc" in param['input_asset']:
        name_imgClass = 'filterFQ_BACIA_'+ name_bacia + "_V" + str(param['versionInp'])
    elif 'Gap-fill' in param['input_asset']:
        # filterGF_BACIA_745_GTB_V30
        pass

    # imgClass = ee.Image(param['input_asset'] + "/" + name_imgClass)#.clip(geomBacia) 
    if frequencyNat:
        print("carregando frequency Natural ")
        frecuencia = 'frequence'
    else:
        frecuencia = 'frequence_natUso'

    imgClass = ee.ImageCollection(param['input_asset']).filter(
                            ee.Filter.eq('version', param['versionInp'])).filter(
                                    ee.Filter.eq('id_bacia', name_bacia ))

    if "Temporal" in param['input_asset']:
        imgClass = imgClass.filter(ee.Filter.eq('step', 2))
    
    imgClass = imgClass.first()
    print('  show metedata imgClass', imgClass.get('system:index').getInfo())
    # print(imgClass.aggregate_histogram('system:index').getInfo())
    # sys.exit()
    numBands = len(imgClass.bandNames().getInfo())
    print(' numero de bandas ', numBands)
    if numBands <= 40:
        imgClass = buildingLayerconnectado(imgClass)

    for cc, yband_name in enumerate(lst_bands_years[:]):
        moda_kernel = imgClass.select(yband_name).focal_mode(2 , 'square', 'pixels')
        moda_kernel = moda_kernel.updateMask(imgClass.select(yband_name+'_conn').lte(min_connect_pixel))

        if cc == 0:
            class_output = imgClass.select(yband_name).blend(moda_kernel)
        else:
            class_tmp = imgClass.select(yband_name).blend(moda_kernel)
            class_output = class_output.addBands(class_tmp)
    
    nameExp = 'filterSP_BACIA_'+ str(name_bacia) + "_" + nmodel + "_V" + str(param['versionOut']) + '_step' + str(param['step'])

    # class_output = class_output.set('version', param['versionSP'])
    class_output = class_output.clip(geomBacia).set(
                        'version', param['versionOut'], 'biome', 'CAATINGA',
                        'collection', '9.0', 'id_bacia', name_bacia,
                        'sensor', 'Landsat', 'source','geodatin', 
                        'model', nmodel, 'step', param['step'], 
                        'system:footprint', geomBacia# imgClass.get('system:footprint')
                    )
    processoExportar(class_output,  nameExp, geomBacia)

#exporta a imagem classificada para o asset
def processoExportar(mapaRF,  nomeDesc, geom_bacia):
    
    idasset =  param['output_asset'] + nomeDesc
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId':idasset, 
        'region': geom_bacia.getInfo()['coordinates'],
        'scale': 30, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"}
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))



#============================================================
#========================METODOS=============================
#============================================================
def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    if str(cont) in numberofChange:
        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        return 0
    
    cont += 1    
    return cont


listaNameBacias = [
    '744','741','7422','745','746','7492','751','752','753',
    '755','759','7621','7622', '763','764','765','766',
    '767', '771', '772','773','7741','776','7742','775', 
    '777', '778','76111','76116','7612','7613','7615','7616',
    '7617','7618','7619','756','757','758','754', '7614', '7421'
]
# listaNameBacias = [
#     '752', '766', '753', '776', '764', '765', '7621', '744', 
#     '756','757','758','754','7614', '7421'
# ]
lstBacias = ['754', '7622','7741', '7615']
changeAcount = False
lstqFalta =  []
cont = 0
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3'
if changeAcount:
    cont = gerenciador(cont)
version = 30
modelo = 'GTB'
listBacFalta = []
knowMapSaved = False
for cc, idbacia in enumerate(listaNameBacias[:]):   
    if knowMapSaved:
        try:
            nameMap = 'filterGF_BACIA_'+ str(idbacia) + "_V" + str(version)
            # # nameMap = 'filterSP_BACIA_'+ str(idbacia) + "_V" + str(version)
            # print(nameMap)
            # imgtmp = ee.Image(input_asset + nameMap)
            imgtmp = ee.ImageCollection(input_asset).filter(
                            ee.Filter.eq('version', version)).filter(
                                ee.Filter.eq('id_bacia', idbacia )).filter(
                                    ee.Filter.eq('model', "RF")).first()
            # print("know how many images exist ", imgtmp.size().getInfo())
            print(f" {cc} loading {imgtmp.get('system:index').getInfo()}", len(imgtmp.bandNames().getInfo()), "bandas ")
        except:
            listBacFalta.append(idbacia)
    else: 
        if idbacia not in lstBacias:
            cont = gerenciador(cont)            
            print("----- PROCESSING BACIA {} -------".format(idbacia))        
            apply_spatialFilterConn(idbacia, modelo)
            


if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))