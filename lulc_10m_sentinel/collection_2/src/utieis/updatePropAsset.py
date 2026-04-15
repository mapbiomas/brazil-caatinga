#-*- coding utf-8 -*-
import os
import ee
import gee 
import sys
import json
from tqdm import tqdm
import random
from datetime import date
import pandas as pd
pd.set_option("mode.copy_on_write", True)
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable


pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project='ee-solkancengine17')
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

def gerenciador(conta):    
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    print("activando conta de >> {} <<".format(conta))        
    gee.switch_user(conta)
    projAccount = get_project_from_account(conta)
    try:
        ee.Initialize(project= projAccount) # project='ee-cartassol'
        print('The Earth Engine package initialized successfully!')
    except ee.EEException as e:
        print('The Earth Engine package failed to initialize!')       
    gee.tasks(n= 2, return_list= True)       

def sendFilenewAsset(idSource,  namePropert, valorProp):
    # moving file from repository Arida to Nextgenmap
    ee.data.updateAsset(
                    assetId= idSource,
                    asset= idSource,
                    updateFields= ["start_time", ee.Date.fromYMD(2024,9,23), namePropert, valorProp]
                )

listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]

# ee.data.renameAsset(sourceId, destinationId, callback)
asset_bacias_buffer = 'projects/ee-solkancengine17/assets/shape/bacias_hidrografica_caatinga_49_regions'
asset_output = 'projects/ee-solkancengine17/assets/bacias_imagem'
asset_input = 'projects/ee-solkancengine17/assets/bacias_imagem'
changeConta = False
fromImgCol = True
versionMapping = 10
if changeConta: 
    gerenciador('solkanCengine')

bacias_buffer = ee.FeatureCollection(asset_bacias_buffer)

lstCod = bacias_buffer.reduceColumns(ee.Reducer.toList(2), ['nunivotto4', 'id_codigo']).get('list').getInfo()
print(lstCod)



sys.exit()
lstFails = []
for cc, nbacia in enumerate(listaNameBacias[:1]):
    featregtmp = bacias_buffer.filter(ee.Filter.eq('nunivotto4', nbacia)).first()
    idCodigo = featregtmp.get('id_codigo').getInfo()
    print("the id_codigo >> ", idCodigo)

    nameImage = f'raster_bacias_reg_{nbacia}_{idCodigo}'
    print(cc, ' => Update Propertie ', nameImage, " the Image ")   
    nameProp = 'id_codigo'    
    try:        
        sendFilenewAsset(asset_input + '/' + nameImage, nameProp, int(idCodigo))
    except:
        lstFails.append(nbacia)

if len(lstFails):
    print(f" we added the basin {len(lstFails)} to list fails ")
    print(lstFails)
else:
    print(" ----- We don´t have basin in list fails --------")
print('========================================')
print("            finish process              ")