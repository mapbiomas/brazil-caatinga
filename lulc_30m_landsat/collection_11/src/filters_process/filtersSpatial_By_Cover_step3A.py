#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
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

param = {      
    'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_int',
    # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
    'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill',
    # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalA',
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',            
    'last_year' : 2025,
    'first_year': 1985,
    'janela': 3,
    'step': 1,
    'num_classes': 7,  # 7, 10
    'versionOut' : 1,
    'versionInp' : 1,
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta' : {
        '0': 'caatinga01',   # 
        '6': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',        
        '35': 'solkan1201',    
        '42': 'solkanGeodatin',
        # '14': 'diegoUEFS',
        '16': 'superconta'     
    }
}
lst_bands_years = ['classification_' + str(yy) for yy in range(param['first_year'], param['last_year'] + 1)]

def buildingLayerconnectado(imgClasse, maxNumbPixels):
    lst_band_conn = ['classification_' + str(yy) + '_conn' for yy in range(param['first_year'], param['last_year'] + 1)]
    # / add connected pixels bands
    # maxNumbPixels = 20
    bandaConectados = imgClasse.connectedPixelCount(
                                            maxSize= maxNumbPixels, 
                                            eightConnected= True
                                        ).rename(lst_band_conn)
    imageFilledConnected = imgClasse.addBands(bandaConectados)

    return imageFilledConnected


def apply_spatialFilterConn (name_bacia):
    # frequencyNat = False
    # no scripts do gapFill estava com 10
    min_connect_pixel = 12
    geomBacia = (ee.FeatureCollection(param['asset_bacias_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', name_bacia))
        )
    geomBacia = geomBacia.map(lambda f: f.set('id_codigo', 1))
    bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)            
    geomBacia = geomBacia.geometry()

    imgClass = (ee.ImageCollection(param['input_asset'])
                        .filter(ee.Filter.eq('version', param['versionInp']))
                        .filter(ee.Filter.eq('id_bacias', name_bacia ))
                        .filter(ee.Filter.eq('num_class', param['num_classes'] ))
                )
    print(" we load ", imgClass.size().getInfo())
    if "Temporal" in param['input_asset']:
        imgClass = (imgClass
                            # .filter(ee.Filter.eq('step', 1))
                            .filter(ee.Filter.eq('janela', 5)))
    print(" we load ", imgClass.size().getInfo())
    imgClass = imgClass.first().updateMask(bacia_raster)
    print('  show metedata imgClass', imgClass.get('system:index').getInfo())
    
    # print(imgClass.aggregate_histogram('system:index').getInfo())
    # sys.exit()
    numBands = len(imgClass.bandNames().getInfo())
    print(' numero de bandas ', numBands)
    if numBands <= 49:
        imgClass = buildingLayerconnectado(imgClass, min_connect_pixel)
    # sys.exit()

    class_output = ee.Image().byte()

    # https://code.earthengine.google.com/b24c36d4d749a00d619eee4d4cbdde58
    for cc, yband_name in enumerate(lst_bands_years[:]):
        # print(" processing band >> ", yband_name)
        maskConn = imgClass.select(f'{yband_name}_conn').lt(min_connect_pixel)#.selfMask()

        #### -- Aplica o filtro da maioria --- ###
        maskSavUso = imgClass.select(yband_name).eq(4).Or(imgClass.select(yband_name).eq(21))
        # maskSavFlorest = imgClass.select(yband_name).eq(4).Or(imgClass.select(yband_name).eq(3))
        maskUsoSolo = imgClass.select(yband_name).eq(21).Or(imgClass.select(yband_name).eq(22))

        ### // Define o tamanho da janela do filtro (3x3 neste caso)   ///
        ###  // var kernel = ee.Kernel.square(1); ### // Raio de 1 pixel (janela 3x3) //
        kernel = ee.Kernel.square(4) ####// Raio de 2 pixels (janela 5x5)
        # --- Imagem base original ---
        base = imgClass.select(yband_name)
        ####  a savana dentro dos pixels conectados será classe Uso   ####

        filterImageSavUs = (imgClass.select(yband_name)
                        .reduceNeighborhood(
                            reducer= ee.Reducer.mode(),
                            kernel= kernel
                        ))
        filterImageUsoSav = (imgClass.select(yband_name)
                                .reduceNeighborhood(
                                    reducer= ee.Reducer.min(),
                                    kernel= kernel
                                ))

        filterImageUsoSol = (imgClass.select(yband_name)
                                .reduceNeighborhood(
                                    reducer= ee.Reducer.min(),
                                    kernel= kernel
                                ))
        filterImageSavUs = filterImageSavUs.updateMask(maskSavUso).updateMask(maskConn)
        filterImageUsoSav = filterImageUsoSav.updateMask(maskSavUso).updateMask(maskConn)
        # # filterImageSavFo = filterImageSavFo.updateMask(maskSavFlorest).updateMask(maskConn)
        filterImageUsoSol = filterImageUsoSol.updateMask(maskUsoSolo).updateMask(maskConn)
        # --- Aplicar suavização final sobre step2 ---
        # step3 = step2.where(maskUsoSolo.And(maskConn), filterImageUsoSol)

        # moda_kernel = imgClass.select(yband_name).focal_mode(2 , 'square', 'pixels')
        # moda_kernel = moda_kernel.updateMask()
        # --- Aplica máscara original para evitar buracos invisíveis ---
        rasterMap = (base
                        .blend(filterImageUsoSav)
                        .blend(filterImageSavUs) # add
                        .blend(filterImageUsoSol)
                        .rename(yband_name))

        class_output = class_output.addBands(rasterMap)
        # print(' comrpovando as bandas adicionadas \n', class_output.bandNames().getInfo())
    
    nameExp = f"filterSP_BACIA_{name_bacia}_GTB_V{param['versionOut']}_{param['num_classes']}cc"
    # class_output = class_output.set('version', param['versionSP'])
    class_output = (class_output.updateMask(bacia_raster)
                    .select(lst_bands_years)
                    .set(
                        'version', param['versionOut'], 'biome', 'CAATINGA',
                        'collection', '11.0', 'id_bacias', name_bacia,
                        'sensor', 'Landsat', 'source','geodatin', 
                        'model', 'GTB', 'step', param['step'], 
                        'num_class',  param['num_classes'] ,
                        'system:footprint', geomBacia
                    ))
    processoExportar(class_output,  nameExp, geomBacia)
    # sys.exit()
#exporta a imagem classificada para o asset
def processoExportar(mapaRF,  nomeDesc, geom_bacia):
    
    idasset =  os.path.join(param['output_asset'], nomeDesc)
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId': idasset, 
        'region': geom_bacia,  # .getInfo()['coordinates']
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

relatorios = open("relatorioTaskXContas.txt", 'a+')
#============================================================
#======================= METODOS ============================
#============================================================
def gerenciador(cont):    
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)
    
    if str(cont) in numberofChange:
        
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 

        # tasks(n= param['numeroTask'], return_list= True) 
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:            
            relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont


listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765',     
]
# listaNameBacias = [ "7613","7746","7754","7741","773","761112","7591","7581","757"]
# listaNameBacias = [ "7613","7746","7741","7591","7581","757"] #
lstBacias = []
changeAcount = False
lstqFalta =  []
cont = 16
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill'
if changeAcount:
    cont = gerenciador(cont)
version = 5
modelo = 'GTB'
listBacFalta = []
knowMapSaved = False
for cc, idbacia in enumerate(listaNameBacias[:]):   
    if knowMapSaved:
        try:
            nameMap = f"filterGF_BACIA_{idbacia}_GTB_V{version}"
            # # nameMap = 'filterSP_BACIA_'+ str(idbacia) + "_V" + str(version)
            # print(nameMap)
            # imgtmp = ee.Image(input_asset + nameMap)
            imgtmp = (ee.ImageCollection(input_asset)
                            # .filter(ee.Filter.eq('version', version))
                            .filter(ee.Filter.eq('id_bacia', idbacia ))
                            .first()
                )
            # print("know how many images exist ", imgtmp.size().getInfo())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}", len(imgtmp.bandNames().getInfo()), "bandas ✅ ")
        except:
            listBacFalta.append(idbacia)
    else: 
        if idbacia not in lstBacias:
            # cont = gerenciador(cont)            
            print("----- PROCESSING BACIA {} -------".format(idbacia))        
            apply_spatialFilterConn(idbacia)

if knowMapSaved:
    print("lista de bacias que faltam \n ",listBacFalta)
    print("total ", len(listBacFalta))