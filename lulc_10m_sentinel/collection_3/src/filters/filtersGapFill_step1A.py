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

class processo_gapfill(object):

    options = {
            # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/Gap-fill',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
            'input_asset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
            'output_asset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Gap-fill',
            'inputAsset10': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
            'asset_gedi': 'users/potapovpeter/GEDI_V27',
            'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
            'classNew':  [3, 4, 3, 3, 3, 12, 12, 12, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21, 21,  4, 12, 21, 25],
            'version_input': 5,
            'version_output': 5,
            'date_inic': 2016,
            'date_end': 2025
            
        }


    def __init__(self, nameBacia, conectarPixels):
        self.id_bacias = nameBacia
        self.geom_bacia = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                                        .filter(ee.Filter.eq('nunivotto4', nameBacia))
                        )
        self.geom_bacia = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster =  self.geom_bacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)                                                    
        self.geom_bacia = self.geom_bacia.geometry()   
        # print("geometria ", len(self.geom_bacia.getInfo()['coordinates']))
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['date_inic'], self.options['date_end'] + 1)]
        self.years = [yy for yy in range(self.options['date_inic'], self.options['date_end'] + 1)]
        # print("lista de years \n ", self.years)
        self.conectarPixels = conectarPixels
        self.version = self.options['version_input']
        # self.model = modelo
        # BACIA_7712_2024_GTB_col10-v_4
        # projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyVA/BACIA_757_GTB_col10-v_10
        self.name_imgClass = f"BACIA_{nameBacia}_GTB_col2S2-v_{self.options['version_input']}" # self.version
        # self.name_imgClass = 'BACIA_corr_mista_' + nameBacia + '_V2'
        
        
        # https://code.earthengine.google.com/4f5c6af0912ce360a5adf69e4e6989e7
        self.imgMap10 = ee.Image(self.options['inputAsset10']).updateMask(self.bacia_raster)
        # .remap(self.options['classMapB'], 
        
        print("carregando imagens a serem processadas com Gap Fill")  
        print("from >> ", self.options['input_asset']) 
        print(" >>>>>>>>> read >>> ", self.name_imgClass)       
        self.imgClass = ee.Image(os.path.join(self.options['input_asset'],self.name_imgClass))

        # self.imgClass = self.imgClass.select(self.lstbandNames)
        print("todas as bandas \n === > ", self.imgClass.bandNames().getInfo())
        # sys.exit()
   
        
        
    def dictionary_bands(self, key, value):
        imgT = ee.Algorithms.If(
                        ee.Number(value).eq(2),
                        self.imgClass.select([key]).byte(),
                        ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
                    )
        return ee.Image(imgT)

    def applyGapFill(self):
        # lst_band_conn = []
        valueMask = -9999
        baseImgMap = ee.Image().toByte()
        previousImage = None       
        lstBandas = [f'classification_{yy}' for yy in self.years] 
        for cc, yyear in enumerate(self.years):
            bandActive = f'classification_{yyear}'
            currentImage = (self.imgClass                                       
                                    .select(bandActive)
                                    .remap(self.options['classMapB'], self.options['classNew'])                                  
                                    .rename(bandActive)
                            )
            print("adding >> ", bandActive)
            if yyear == self.options['date_inic']:                
                currentMap10 = (self.imgMap10
                                    .updateMask(self.bacia_raster)
                                    .reduce(ee.Reducer.first())
                                    .remap(self.options['classMapB'],self.options['classNew'])                                                  
                            )
                print("banda do reducer >>> ", currentMap10.bandNames().getInfo())
                # selecciona todos os pixels que estão com gap e que tem agora valor valueMask
                maskGap = currentImage.mask().Not() #.gt(1).unmask(valueMask).eq(valueMask)
                bandBlend = currentMap10.updateMask(maskGap) # seleciona todos os pixels da mascara
                # onde estão os valores com valueMask colocar os pixels mapbiomas
                newBandActive = currentImage.unmask(0).blend(bandBlend)

            # elif  yyear > self.options['date_inic'] and yyear < self.options['date_end']:                                          
            else:
                print("------ processo intermediario ---- ")
                # Selecionando as áreas om Gaps
                maskGap = currentImage.mask().Not() #.gt(1).unmask(valueMask).eq(valueMask)
                # get the first Pixel without null
                rasterFirst = baseImgMap.select(lstBandas[cc - 1])
                print(f"get pixels gaps from >>> {rasterFirst.bandNames().getInfo()} saved")
                # rasterFirst = (rasterFirst
                #                 .reduce(ee.Reducer.firstNonNull())
                #                 .updateMask(self.bacia_raster)
                #         )
                rasterFirst = rasterFirst.updateMask(maskGap)

                # onde estão os valores com valueMask colocar os pixels mapbiomas
                newBandActive = currentImage.unmask(0).blend(rasterFirst)

                # if yyear == self.options['date_end'] - 1:
                #     previousImage = copy.deepcopy(newBandActive)  
                #     print("addiding 2024 em imagem previa ")
            # else:
            #     print("finalizando  >> ", bandActive)
            #     # selecciona todos os pixels que estão com gap e que tem agora valor valueMask
            #     maskGap = currentImage.mask().Not()  #.gt(1).unmask(valueMask).eq(valueMask)            
            #     newBandActive = currentImage.unmask(0).where(maskGap.eq(1), previousImage)
            
            ### ==============================================================####
            baseImgMap = baseImgMap.addBands(newBandActive)    
            print(baseImgMap.bandNames().getInfo())           
        # sys.exit()
        imageFilledTn = ee.Image.cat(baseImgMap).select(self.lstbandNames)
        return imageFilledTn.updateMask(self.bacia_raster)

    def processing_gapfill(self):

        # apply the gap fill
        imageFilled = self.applyGapFill()
        print(" 🚨🚨🚨  Applying filter Gap Fill 🚨🚨🚨 ")
        print(imageFilled.bandNames().getInfo())
        # sys.exit()
        name_toexport = f'filterGF_BACIA_{self.id_bacias}_GTB_V{self.options['version_output']}'
        imageFilled = (ee.Image(imageFilled)
                        .updateMask(self.bacia_raster)
                        .set(
                            'version', self.options['version_output'], 
                            'biome', 'CAATINGA',
                            'source', 'geodatin',
                            'model', "GTB",
                            'type_filter', 'gap_fill',
                            'collection', '3.0',
                            'id_bacias', self.id_bacias,
                            'sensor', 'Sentinel',
                            'system:footprint' , self.geom_bacia.coordinates()
                        )
        )
        
        self.processoExportar(imageFilled, name_toexport)

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':self.geom_bacia,#.getInfo()['coordinates'],
            'scale': 10, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))


param = {    
    'bioma': "CAATINGA", #nome do bioma setado nos metadados  
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',        
        '35': 'solkan1201',   
        '42': 'solkanGeodatin', 
        '49': 'superconta', 
    }
}
relatorios = open("relatorioTaskXContas.txt", 'a+')
#============================================================
#========================METODOS=============================
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
            ee.Initialize(project= projAccount) # project='ee-cartas775sol'
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
    '751', '7691', '7754', '7581', '7625', '7584', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765', 
]
# listaNameBacias = ['7746', '7619', '763']
# listaNameBacias = [ "7613","7746","7754","7741","773","761112","7591","7581","757"]
# listaNameBacias = [ "755","7622","746","7591","7544","7443", "766", "757", "7764", "7671", "7422", "7564"]
# listaNameBacias = ["7591"]
cont = 49
start_date = 0
# cont = gerenciador(cont)
# applyGdfilter = False
for cc, idbacia in enumerate(listaNameBacias[start_date:]):
    print("-----------------------------------------")
    print(f"----- #{cc + start_date}/{len(listaNameBacias)} PROCESSING BACIA {idbacia} -------")   
    try: 
        aplicando_gapfill = processo_gapfill(idbacia, False) # added band connected is True
        aplicando_gapfill.processing_gapfill()
    except:
        print(f"basin {idbacia} with erro ")