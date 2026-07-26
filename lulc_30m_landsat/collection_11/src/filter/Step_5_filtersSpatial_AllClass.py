#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os
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
    'output_asset': "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_all",
    'input_asset':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency',
    'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'last_year':   2025,
    'first_year':  1985,
    'janela':      5,
    'step':        1,
    'num_classes': 7,   # 7 ou 10
    'versionOut':  2,
    'versionInp':  2,
    'min_connect_pixel': 12,  # pixels com menos conexões são substituídos pela moda
    'kernel_radius':     4,   # raio do kernel de moda (janela 9×9 pixels ≈ 270m)
    'numeroTask':  6,
    'numeroLimit': 50,
    'conta': {
        '0':  'caatinga01',
        '6':  'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',
        '35': 'solkan1201',
        '42': 'solkanGeodatin',
        '49': 'superconta',
    }
}

lst_bands_years      = ['classification_' + str(yy) for yy in range(param['first_year'], param['last_year'] + 1)]
lst_bands_years_conn = [b + '_conn' for b in lst_bands_years]


def buildingLayerconnectado(imgClasse, maxNumbPixels):
    """Adiciona bandas de contagem de pixels conectados (_conn) à imagem."""
    bandaConectados = imgClasse.connectedPixelCount(
        maxSize=maxNumbPixels,
        eightConnected=True
    ).rename(lst_bands_years_conn)
    return imgClasse.addBands(bandaConectados)


def apply_spatialFilterConn(name_bacia):
    min_connect_pixel = param['min_connect_pixel']
    kernel = ee.Kernel.square(param['kernel_radius'])  # janela 9×9 pixels (raio 4)

    geomBacia = (ee.FeatureCollection(param['asset_bacias_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', name_bacia)))
    geomBacia   = geomBacia.map(lambda f: f.set('id_codigo', 1))
    bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
    geomBacia   = geomBacia.geometry()

    ic = (ee.ImageCollection(param['input_asset'])
                .filter(ee.Filter.eq('version', param['versionInp']))
                .filter(ee.Filter.eq('id_bacias', name_bacia)))
    if 'Temporal' in param['input_asset']:
        ic = ic.filter(ee.Filter.eq('janela', param['janela']))

    n = ic.size().getInfo()
    print(f"  imagens carregadas para bacia {name_bacia}: {n}")

    imgClass = ic.first().updateMask(bacia_raster)
    print('  system:index:', imgClass.get('system:index').getInfo())

    # Adiciona bandas de conectividade se ainda não presentes
    existing_bands = imgClass.bandNames().getInfo()
    if lst_bands_years_conn[0] not in existing_bands:
        imgClass = buildingLayerconnectado(imgClass, min_connect_pixel)

    # Constrói lista de imagens filtradas e combina em uma única chamada
    band_images = []
    for yband_name in lst_bands_years:
        base      = imgClass.select(yband_name)
        maskConn  = imgClass.select(f'{yband_name}_conn').lt(min_connect_pixel)
        filtered  = base.reduceNeighborhood(reducer=ee.Reducer.mode(), kernel=kernel)
        rasterMap = base.blend(filtered.updateMask(maskConn)).rename(yband_name)
        band_images.append(rasterMap)

    class_output = ee.Image.cat(band_images)

    nameExp = f"filterSP_BACIA_{name_bacia}_GTB_V{param['versionOut']}_{param['num_classes']}cc"
    class_output = (class_output
                    .updateMask(bacia_raster)
                    .select(lst_bands_years)
                    .set(
                        'version',          param['versionOut'],
                        'biome',            'CAATINGA',
                        'collection',       '11.0',
                        'id_bacias',        name_bacia,
                        'sensor',           'Landsat',
                        'source',           'geodatin',
                        'model',            'GTB',
                        'step',             param['step'],
                        'num_class',        param['num_classes'],
                        'system:footprint', geomBacia,
                    ))
    processoExportar(class_output, nameExp, geomBacia)


def processoExportar(mapaRF, nomeDesc, geom_bacia):
    idasset = f"{param['output_asset']}/{nomeDesc}"
    optExp = {
        'image':           mapaRF,
        'description':     nomeDesc,
        'assetId':         idasset,
        'region':          geom_bacia,
        'scale':           30,
        'maxPixels':       1e13,
        'pyramidingPolicy': {'.default': 'mode'},
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start()
    print("salvando ... " + nomeDesc + "..!")
    for k, v in dict(task.status()).items():
        print(f"  {k} : {v}")


#============================================================
#======================= EXECUÇÃO ===========================
#============================================================
def gerenciador(cont):
    numberofChange = list(param['conta'].keys())
    print(numberofChange)

    if str(cont) in numberofChange:
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project=projAccount)
            print('The Earth Engine package initialized successfully!')
        except ee.EEException:
            print('The Earth Engine package failed to initialize!')

        with open("relatorioTaskXContas.txt", 'a+') as relatorios:
            relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')
            tarefas = tasks(n=param['numeroTask'], return_list=True)
            for lin in tarefas:
                relatorios.write(str(lin) + '\n')

    elif cont > param['numeroLimit']:
        return 0
    cont += 1
    return cont


listaNameBacias = [
    '7691', '7754', '7581', '7625', '7584', '751', '7614',
    '7616', '745', '7424', '773', '7612', '7613', '752',
    '7618', '7561', '755', '7617', '7564', '761111', '761112',
    '7741', '7422', '76116', '7761', '7671', '7615', '7411',
    '7764', '757', '771', '766', '7746', '753', '764',
    '7541', '7721', '772', '7619', '7443', '7544', '7438',
    '763', '7591', '7592', '746', '7712', '7622', '765'
]
# listaNameBacias = ["7613", "7746", "7741", "7591", "7581", "757"]

changeAcount  = False
knowMapSaved  = False
cont          = 49

if changeAcount:
    cont = gerenciador(cont)

listBacFalta = []
for cc, idbacia in enumerate(listaNameBacias):
    if knowMapSaved:
        try:
            imgtmp = (ee.ImageCollection(param['output_asset'])
                            .filter(ee.Filter.eq('version', param['versionOut']))
                            .filter(ee.Filter.eq('id_bacias', idbacia))
                            .first())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}",
                  len(imgtmp.bandNames().getInfo()), "bandas ✅")
        except:
            listBacFalta.append(idbacia)
    else:
        print(f"----- PROCESSING BACIA {idbacia} -------")
        apply_spatialFilterConn(idbacia)

if knowMapSaved:
    print("lista de bacias que faltam\n", listBacFalta)
    print("total", len(listBacFalta))
