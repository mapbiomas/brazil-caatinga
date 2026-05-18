import ee
import sys
from ee_plugin import Map
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
palette = [
    "#ffffff","#129912","#1f4423","#006400","#00ff00","#687537","#76a5af",
    "#29eee4","#77a605","#ad4413","#bbfcac","#45c2a5","#b8af4f","#f1c232",
    "#ffffb2","#ffd966","#f6b26b","#f99f40","#e974ed","#d5a6bd","#c27ba0",
    "#fff3bf","#ea9999","#dd7e6b","#aa0000","#ff8585","#0000ff","#d5d5e5",
    "#dd497f","#665a3a","#ff0000","#1f0478","#968c46","#0000ff","#4fd3ff",
    "#ba6a27","#f3b4f1","#02106f","#02106f","#e075ad","#982c9e","#e787f8",
    "#ebebe0","#c2c2a3","#6b6b47","#d0ffd0","#cca0d4","#d082de","#cd49e4",
    "#6b9932","#66ffcc","#000000","#000000","#000000","#000000","#000000",
    "#000000","#CC66FF","#FF6666","#006400","#8d9e8b","#f5d5d5","#84ff75"
]

vis = {
    'mapbiomas': {
        'min': 0,
        'max': 62,
        'palette': palette,
        'format': 'png'
    },
    'incidents': {
        'min': 0, 
        'max': 8,
        'palette':[
            "#C8C8C8","#FED266","#FBA713","#cb701b","#cb701b", 
            "#a95512","#a95512","#662000","#662000","#cb181d"
        ],
        'format': 'png'
    },
    'states': {
        'min': 1, 
        'max': 5,
        'palette': "#C8C8C8,#AE78B2,#772D8F,#4C226A,#22053A"
    },
    'combination': {
        'min': 1, 
        'max': 6,
        'palette': "#C9C9C9,#F0F076,#782E90,#f4a295,#ff6d56,#ff2200"
    },
    'bioma': {
        'featureCollection': None,
        'color': 'CD_Bioma',
        'width': 2
    }
        
};

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
    assetIdExp = 'users/mapbiomascaatinga01/Alertas/' + namesImExp
    myFolder = 'MAPBIOMAS-EXPORT';
    pmtroExpAsset = {
        'image': imgMaps.toUint8(),
        'description': namesImExp,
        'region': geometLimit.geometry(),
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
        'region': geometLimit.geometry(),
        'folder': myFolder,
        'maxPixels':1e13, 
        'scale': 30
    }
    task = ee.batch.Export.image.toDrive(**pmtroExpdrive)
    task.start()
    
    print("exporting Image Maps  " + namesImExp + " to Folder => " + myFolder);
    print(" and asset  => " + assetIdExp );

#//======================  Edição Usuario =======================================


classMapB =  [ 3, 4, 5, 6, 9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =   [ 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0];


param = {
    'asset_integracao' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    'asset_biomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'year_start': 1985,
    'year_end': 2022,
    'expor_img': True
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
bandActual = "classification_2022"

bbiomas = ee.FeatureCollection(param['asset_biomas']);
mapsMapbiomas = ee.Image(param['asset_integracao']);
print("mapas da Coleção 8", mapsMapbiomas.bandNames().getInfo()); 


# // remap to natural class
col8mapEst = mapsMapbiomas.select('classification_' + str(param['year_start'])).remap(classMapB, classNew).gt(0);

# // building stavel class map
lstBand = ee.List([]);
lstImages = ee.List([])
for year in range(param['year_start'], param['year_end']):
    # classification_2022
    bandCC = 'classification_' + str(year);
    print("===> remape band " + bandCC)
    lstBand = lstBand.add(bandCC);    
    tmpClass = mapsMapbiomas.select(bandCC) 
    lstImages =lstImages.add(tmpClass.rename('classification'))
    tmpClass = tmpClass.remap(classMapB, classNew).rename('classification');
    print("levando para a banda = ", tmpClass.bandNames().getInfo())
    col8mapEst = col8mapEst.multiply(tmpClass);

# // imc_carta
colectionMaps = ee.ImageCollection.fromImages(lstImages);

print("mapas da Coleção 8 remapeados", colectionMaps.first().bandNames().getInfo()); 

# // ************************** states ***********************************
image_states = colectionMaps.reduce(ee.Reducer.countDistinct());
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
combination = ee.Image.constant(0) #//.clip(geometry);
for value in lstCombinationValues:
    print("processing " + dictCombination[str(value)] + "combination");
    val_inc = dictcombVal[str(value)][0];
    val_sta = dictcombVal[str(value)][1];
    combination = combination.where(image_incidence.eq(val_inc).And(image_states.eq(val_sta)), value);

# // ******************************************************************** 

vis['bioma']['featureCollection'] = bbiomas;
LimiteCaat = ee.Image().byte().paint(vis['bioma']); 
Map.addLayer(LimiteCaat, {palette: 'FF0000'}, 'Caatinga');

print(mapsMapbiomas.select(bandActual).getInfo())
Map.addLayer(mapsMapbiomas.select(bandActual).updateMask(col8mapEst), vis['mapbiomas'], bandActual);
Map.addLayer(image_incidence.updateMask(col8mapEst), vis['incidents'], "incidents");
Map.addLayer(image_states.clip(bbiomas).updateMask(col8mapEst), vis['states'], "States");
Map.addLayer(combination.clip(bbiomas).updateMask(col8mapEst), vis['combination'], "Combination");
