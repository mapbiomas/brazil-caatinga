#-*- coding utf-8 -*-
import ee
import gee
import os
import sys
import pandas as pd
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


# def convertListBandName_to_ImgCollection(lstBands, ImageMap):

#     lstBands = lstBands.map(lambda bandAct: ImageMap.select(bandAct).toByte().rename('classification')); 
#     return ee.ImageCollection.fromImages(lstBands);        

def apply_incidence (imgActual, imgPrevious):
 
    imgincidence = ee.Image(imgPrevious).select(["incidence"]);
    
    classification0 = ee.Image(imgPrevious).select(["classification"]);
    classification1 = ee.Image(imgActual).select(["classification"]);
    
    imgincidence = imgincidence.where(
                        classification0.neq(classification1), 
                        imgincidence.add(1)
                    );    
    return imgActual.addBands(imgincidence);    

def exportMaps(imgMaps, namesImExp, geometLimit):
    assetIdExp = 'projects/mapbiomas-arida/incidencias/' + namesImExp
    myFolder = 'MAPBIOMAS-EXPORT';
    pmtroExpAsset = {
        'image': imgMaps.toUint8(),
        'description': namesImExp,
        'region': geometLimit,
        "pyramidingPolicy":{".default": "mode"},
        'assetId': assetIdExp,
        'maxPixels':1e13, 
        'scale': 30          
    };    
    task = ee.batch.Export.image.toAsset(**pmtroExpAsset)
    task.start() 
    

    pmtroExpdrive = {
        'image': imgMaps.toUint8(),
        'description': namesImExp,
        'region': geometLimit,
        'folder': myFolder,
        'maxPixels':1e13, 
        'scale': 30
    }
    task = ee.batch.Export.image.toDrive(**pmtroExpdrive)
    task.start()
    
    print("exporting Image Maps  " + namesImExp + " to Folder => " + myFolder);
    print(" and asset  => " + assetIdExp );

#//======================  Edição Usuario =======================================
def gerenciador(cont, paramet):
    #0, 18, 36, 54]
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee
    # cada conta vai rodar com 18 cartas X 3 anos
    #=====================================
    numberofChange = [kk for kk in paramet['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(paramet['conta'][str(cont)]))        
        gee.switch_user(paramet['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= paramet['numeroTask'], return_list= True)        
    
    elif cont > paramet['numeroLimit']:
        cont = -1
    
    cont += 1    
            
    return cont


##############################################
###     Helper function
###    @param item 
##############################################
def convert2featCollection (item):
    item = ee.Dictionary(item)

    feature = ee.Feature(ee.Geometry.Point([0, 0])).set(
        'classe', item.get('classe'),"area", item.get('sum'))
        
    return feature

#########################################################################
####     Calculate area crossing a cover map (deforestation, mapbiomas)
####     and a region map (states, biomes, municipalites)
####      @param image 
####      @param geometry
#########################################################################
# https://code.earthengine.google.com/5a7c4eaa2e44f77e79f286e030e94695
def calculateArea (image, pixelArea, geometry):

    pixelArea = pixelArea.rename('area').addBands(image.rename('classe')).clip(geometry)      
    reducer = ee.Reducer.sum().group(1, 'classe')
    optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': 30,
        'bestEffort': True, 
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)

    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

#exporta a imagem classificada para o asset
def processoExportar(areaFeat, nameT):      
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': 'AREAS_INCIDENCIAS_CC'        
        }    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")  



classMapB =  [ 3, 4, 5, 6, 9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =   [ 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0];


param = {
    'asset_integracao' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    'asset_biomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'asset_est': 'users/CartasSol/shapes/estados_2010',
    'asset_estadosBioma': 'projects/mapbiomas-workspace/AUXILIAR/ESTATISTICAS/COLECAO8/VERSAO-1/refined_biome_per_state',
    'year_start': 1985,
    'year_end': 2022,
    'expor_img': False,
    'numeroTask': 6,
    'numeroLimit': 35,
    'conta' : {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',
        # '25': 'diegoGmail',   
        '30': 'solkan1201'
    },
}
dictCDbiomas = {
    '1': 'Amazônia',
    '2': 'Caatinga',
    '3': 'Cerrado',
    '4': 'Mata Atlântica',
    '5': 'Pampa',
    '6': 'Pantanal'
};
lstCombinationValues = [1,2,3,4,5,6];
dictCombination = {
    '1': 'persistence',
    '2': 'One incident',
    '3': 'Toggle',
    '4': 'low states',
    '5': 'medium states',
    '6': 'high states'
}
dictcombVal = {
    '1': [0,1],
    '2': [1,2],
    '3': [1,2],
    '4': [1,2],
    '5': [5,3],
    '6': [5,5]
}
bandActual = "classification 2022"
estados_bioma = ee.FeatureCollection(param['asset_estadosBioma']);
# lst_estados_bioma = estados_bioma.reduceColumns(ee.Reducer.toList(2), ['FEATURE_ID', 'NAME_PT_BR']).getInfo()
lst_state_biome = [
    [65363, 'Pampa [Rio Grande do Sul]'], 
    [65316, 'Cerrado [Rondônia]'], 
    [65321, 'Cerrado [Pará]'],   [65324, 'Cerrado [Tocantins]'], 
    [65326, 'Cerrado [Maranhão]'], [65328, 'Cerrado [Mato Grosso]'], 
    [65331, 'Cerrado [Piauí]'], [65344, 'Cerrado [Bahia]'], 
    [65347, 'Cerrado [Minas Gerais]'],  [65349, 'Cerrado [São Paulo]'], 
    [65351, 'Cerrado [Paraná]'], [65353, 'Cerrado [Mato Grosso do Sul]'], 
    [65356, 'Cerrado [Goiás]'], [65358, 'Cerrado [Distrito Federal]'],
    [65330, 'Caatinga [Piauí]'],  [65332, 'Caatinga [Ceará]'], 
    [65333, 'Caatinga [Rio Grande do Norte]'], [65335, 'Caatinga [Paraíba]'], 
    [65337, 'Caatinga [Pernambuco]'], [65339, 'Caatinga [Alagoas]'], 
    [65341, 'Caatinga [Sergipe]'],  [65343, 'Caatinga [Bahia]'], 
    [65346, 'Caatinga [Minas Gerais]'], [65329, 'Pantanal [Mato Grosso]'], 
    [65355, 'Pantanal [Mato Grosso do Sul]'], 
    [65315, 'Amazônia [Amazônia]'], 
    [65317, 'Amazônia [Acre]'],  [65318, 'Amazônia [Amazonas]'], 
    [65319, 'Amazônia [Roraima]'], [65320, 'Amazônia [Pará]'], 
    [65322, 'Amazônia [Amapá]'], [65323, 'Amazônia [Tocantins]'],     
    [65325, 'Amazônia [Maranhão]'], [65327, 'Amazônia [Mato Grosso]'], 
    [65334, 'Mata Atlântica [Rio Grande do Norte]'], [65336, 'Mata Atlântica [Paraíba]'], 
    [65338, 'Mata Atlântica [Pernambuco]'], [65340, 'Mata Atlântica [Alagoas]'], 
    [65342, 'Mata Atlântica [Sergipe]'], [65345, 'Mata Atlântica [Bahia]'], 
    [65348, 'Mata Atlântica [Minas Gerais]'], [65350, 'Mata Atlântica [SãoPaulo]'], 
    [65352, 'Mata Atlântica [Paraná]'], [65354, 'Mata Atlântica [Mato Grosso do Sul]'], 
    [65357, 'Mata Atlântica [Goiás]'], [65359, 'Mata Atlântica [Espírito Santo]'], 
    [65360, 'Mata Atlântica [Rio de Janeiro]'], [65361, 'Mata Atlântica [Santa Catarina]'], 
    [65362, 'Mata Atlântica [Rio Grande do Sul]']
]

print("Lista de todos os biomas estados \n ", lst_state_biome)
print("rodaremos ", len(lst_state_biome))
# bbiomas = ee.FeatureCollection(param['asset_biomas']);
# sys.exit()
contAuth = 30
contAuth = gerenciador(contAuth, param)
for cc, idEstB in enumerate(lst_state_biome):
    FEATURE_ID = idEstB[0]
    nome_estadoBioma = idEstB[1].replace(" ", "_")
    nome_estadoBioma = nome_estadoBioma.replace("[", "_")
    nome_estadoBioma = nome_estadoBioma.replace("]", "")
    print(f'# {cc} => processing estado {nome_estadoBioma}')
    estado_atual = estados_bioma.filter(ee.Filter.eq('FEATURE_ID', FEATURE_ID)).geometry()
    # print(estado_atual.getInfo())
    # sys.exit()
    mapsMapbiomas = ee.Image(param['asset_integracao']).clip(estado_atual);
    if cc < 1:
        print("mapas da Coleção 8", mapsMapbiomas.bandNames().getInfo()); 

    # // remap to natural class
    col8mapEst = mapsMapbiomas.select('classification_' + str(param['year_start'])).remap(classMapB, classNew).gt(0);

    # // building stavel class map
    lstBand = ee.List([]);
    lstImages = ee.List([])
    # for year in range(param['year_start'], param['year_end'] + 1):
    #     # classification_2022
    #     bandCC = 'classification_' + str(year);
    #     # print(f"{FEATURE_ID} ===> remape band " + bandCC)
    #     lstBand = lstBand.add(bandCC);    
    #     tmpClass = mapsMapbiomas.select(bandCC)
    #     tmpClass = tmpClass.remap(classMapB, classNew).rename('classification');
    #     # lstImages =lstImages.add(tmpClass)        
    #     # print("levando para a banda = ", tmpClass.bandNames().getInfo())
    #     col8mapEst = col8mapEst.add(tmpClass.gt(0));
    # # estavel real 
    # col8mapEst = col8mapEst.gt(0)

    for year in range(param['year_start'], param['year_end'] + 1):
        # classification_2022
        bandCC = 'classification_' + str(year);
        lstBand = lstBand.add(bandCC); 
        # print(f"{FEATURE_ID} ===> remape band " + bandCC)   
        tmpClass = mapsMapbiomas.select(bandCC)
        tmpClass = tmpClass.updateMask(col8mapEst).rename('classification');
        lstImages =lstImages.add(tmpClass)        
        # print("levando para a banda = ", tmpClass.bandNames().getInfo())

    # // imc_carta
    colectionMaps = ee.ImageCollection.fromImages(lstImages);
    print("mapas da Coleção 8 remapeados", colectionMaps.first().bandNames().getInfo()); 

    # // ************************** states ***********************************
    image_states = colectionMaps.reduce(ee.Reducer.countDistinct()).rename('state');
    # //**********************************************************************
    # // ************************ incidence **********************************
    imagefirst = ee.Image(colectionMaps.first()).addBands(
                                ee.Image.constant(0).toByte().rename( "incidence"));
    print("know imagem 1 ", imagefirst.bandNames().getInfo())

    image_incidence = colectionMaps.iterate(apply_incidence, imagefirst);
    image_incidence = ee.Image(image_incidence).select(["incidence"]);
    print("know imagem incidence  ", image_incidence.bandNames().getInfo())
    # sys.exit()
    # // *********************************************************************
    # // ********************** processing combination ***********************
    # combination = ee.Image.constant(0) #//.clip(geometry);
    # for value in lstCombinationValues:
    #     print("processing " + dictCombination[str(value)] + "combination");
    #     val_inc = dictcombVal[str(value)][0];
    #     val_sta = dictcombVal[str(value)][1];
    #     combination = combination.where(image_incidence.eq(val_inc).And(image_states.eq(val_sta)), value);

    # // ******************************************************************** 
    # // Export incicdnet bioo+'_image_incidence'

    image_incidence = image_incidence.set(
                        'MAP', 'INCIDENCE',
                        'FEATURE_ID', FEATURE_ID, 
                        'NAME_PT_BR', nome_estadoBioma
                    )
    image_states = image_states.set(
                        'MAP', 'STATE',
                        'FEATURE_ID', FEATURE_ID, 
                        'NAME_PT_BR', nome_estadoBioma
                    )
    # combination = combination.set(
    #                     'MAP', 'COMBINATION',
    #                     'FEATURE_ID', FEATURE_ID, 
    #                     'NAME_PT_BR', nome_estadoBioma
    #                 )
    if param['expor_img']:
        name_export = 'maps_incidence_' + str(FEATURE_ID);
        exportMaps(image_incidence, name_export, estado_atual);
        name_export = 'maps_state_' + str(FEATURE_ID);
        exportMaps(image_states, name_export, estado_atual);
        # name_export = 'maps_combination_' + str(FEATURE_ID);
        # exportMaps(combination, name_export, estado_atual);   
        # change de conta 
        contAuth = gerenciador(contAuth, param)
        
    else:
        pixelArea = ee.Image.pixelArea().divide(10000).clip(estado_atual) 
        areaTemp = calculateArea (image_incidence, pixelArea, estado_atual)  
        name_export = 'table_areas_incidence_All_class_' + str(FEATURE_ID);
        processoExportar(areaTemp, name_export)

        # - pixelArea = ee.Image.pixelArea().divide(10000) 
        # - maskState = image_states.gt(0)
        # - image_states = image_states.updateMask(maskState)
        # areaTemp = calculateArea (image_states, pixelArea, estado_atual)  
        name_export = 'table_areas_state_All_class_' + str(FEATURE_ID);
        # processoExportar(areaTemp, name_export)
    
    