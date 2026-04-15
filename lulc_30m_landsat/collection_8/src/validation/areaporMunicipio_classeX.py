#-*- coding utf-8 -*-
import ee
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



param = {
    'inputAsset': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',    
    'sufixo': '_Spv2', 
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_municipios': "projects/mapbiomas-workspace/AUXILIAR/municipios-2020",
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXPORT-URB', 
    'lsClasses': [3,4,12,21,22,33,29],
    'numeroTask': 0,
    'numeroLimit': 37,
    'conta' : {
        '0': 'caatinga04'
    }
}



# pixelArea, imgMapa, bioma250mil
def iterandoXMunicipioImCruda(imgAreaRef, listProp, nYear):
    meuDF = pd.DataFrame({
                    'year': [],
                    'classe': [],
                    "area": [],
                    "CD_MUN": [],
                    "NM_MUN": [],
                    "SIGLA_UF": []
                })
    reducer = ee.Reducer.sum()
     
    # "CD_MUN", "NM_MUN", "SIGLA_UF"
    for cc, tuplaProp in enumerate(listProp):  
        print(cc, " municipio ==> ", tuplaProp[1])     
        geomunSHP = ee.FeatureCollection(param['asset_municipios']).filter(
                                ee.Filter.eq('CD_MUN', tuplaProp[0])).geometry()                    

        optRed = {
            'reducer': reducer,
            'geometry': geomunSHP,
            'scale': 30,
            'bestEffort': True, 
            'maxPixels': 1e13
        }            
        areas = imgAreaRef.rename('area').reduceRegion(**optRed)  
        areas = areas.get('area').getInfo()  
 
        # Create a dictionary with the data for the new row
        new_record = pd.DataFrame([{
                'year': nYear,
                'classe': 'urbano',
                "area": areas,
                "CD_MUN": tuplaProp[0],
                "NM_MUN": tuplaProp[1],
                "SIGLA_UF": tuplaProp[2]
            }])    

        # Append the dictionary to the DataFrame
        meuDF = pd.concat([meuDF, new_record], ignore_index=True) 

    nameCSV = 'areas_urbanas_municipios_' + str(nYear) + '.csv'
    # Reset the index
    meuDF = meuDF.reset_index(drop=True)
    meuDF.to_csv(nameCSV)

        
#exporta a imagem classificada para o asset
def processoExportar(areaFeat, nameT):      
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': param["driverFolder"]        
        }    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!") 






lstBands = ['classification_' + str(yy) for yy in range(1985, 2023)]
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()
print("show the atributos of bioma Caatinga ");


pixelArea = ee.Image.pixelArea().divide(10000)

munSHP = ee.FeatureCollection(param['asset_municipios']).filterBounds(bioma250mil);
print('show the atributos of Municipios ', munSHP.size().getInfo());


listMun = munSHP.reduceColumns(ee.Reducer.toList(3), ["CD_MUN", "NM_MUN", "SIGLA_UF"]).get('list').getInfo()
cont = 0
lstClaas = ['classification_1985', 'classification_2022']
imgMapp = ee.Image(param['inputAsset']).select(lstClaas);

for nyear in [2022]: #1985, 
    print(f"---- {str(nyear)} ----")
    bandAct = 'classification_' + str(nyear) 
    newimgMap = imgMapp.select(bandAct).eq(24)  # cidade s
    newimgMap = newimgMap.multiply(pixelArea)
   
    iterandoXMunicipioImCruda(newimgMap, listMun, nyear)  
