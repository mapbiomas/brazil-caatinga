
var Palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = Palettes.get('classification7');
var vis = {
    mapbiomas: {
        'min': 0,
        'max': 62,
        'palette': palette,
        'format': 'png'
    },
    incidents: {
        min:0, 
        max:8,
        palette:[
            "#C8C8C8","#FED266","#FBA713","#cb701b","#cb701b", 
            "#a95512","#a95512","#662000","#662000","#cb181d"
        ],
        format: 'png'
    },
    states: {
        min:1, 
        max:5,
        palette: "#C8C8C8,#AE78B2,#772D8F,#4C226A,#22053A"
    },
    combination: {
        min: 1, 
        max: 6,
        palette: "#C9C9C9,#F0F076,#782E90,#f4a295,#ff6d56,#ff2200"
    },
    bioma: {
        featureCollection: null,
        color: 'CD_Bioma',
        width: 2
    }
        
};

var classMapB =  [ 3, 4, 5, 6, 9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62];
var classNew =   [ 3, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0];
// var asset_classificacao = "projects/mapbiomas-workspace/COLECAO2_3/classificacao";
//var asset_integracao = "projects/mapbiomas-workspace/COLECAO2_3/classificacao-ft";
//var asset_integracao = "projects/mapbiomas-workspace/COLECAO2_3/integracao";

var param = {
    'asset_integracao' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    'asset_biomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'asset_inciden': 'projects/mapbiomas-arida/incidencias',
    'year_start': 1985,
    'year_end': 2022,
    'expor_img': true
}
var dictCDbiomas = {
    '1': 'Amazônia',
    '2': 'Caatinga',
    '3': 'Cerrado',
    '4': 'Mata Atlântica',
    '5': 'Pampa',
    '6': 'Pantanal'
};
var lstCombinationValues = [1,2,3,4,5,6];
var dictCombination = {
    '1': 'persistence',
    '2': 'One incident',
    '3': 'Toggle',
    '4': 'low states',
    '5': 'medium states',
    '6': 'high states'
}
var dictcombVal = {
    '1': [0,1],
    '2': [1,2],
    '3': [1,2],
    '4': [1,2],
    '5': [5,3],
    '6': [5,5]
}
var bandActual = "classification_2022"

var bbiomas = ee.FeatureCollection(param.asset_biomas);
var mapsMapbiomas = ee.Image(param.asset_integracao);
print("mapas da Coleção 8",mapsMapbiomas); 
var years = ee.List.sequence(param.year_start, param.year_end).getInfo();
print("list of years ", years)
// remap to natural class
var col8mapEst = mapsMapbiomas.select('classification_' + param.year_start).remap(classMapB, classNew).gt(0);

// building stavel class map
var lstBand = ee.List([]);
var lstImgs = ee.List([])
years.forEach(function(year){
    var bandCC = 'classification_' + year.toString();
    lstBand = lstBand.add(bandCC);
    var tmpClass = mapsMapbiomas.select(bandCC);
    lstImgs = lstImgs.add(tmpClass.rename("classification"))
    tmpClass = tmpClass.remap(classMapB, classNew).gt(0);
    col8mapEst = col8mapEst.multiply(tmpClass);
}) 
print("lista de bandass ", lstBand);
print('Lista de images ', lstImgs);
// imc_carta
// var colectionMaps = convertListBandName_to_ImgCollection(lstBand, mapsMapbiomas);
var colectionMaps = ee.ImageCollection.fromImages(lstImgs)
print("coletionm masp ", colectionMaps)

var colMapsInc = ee.ImageCollection(param.asset_inciden)
var mapInc = colMapsInc.filter(ee.Filter.eq('MAP','INCIDENCE'))
var mapStat = colMapsInc.filter(ee.Filter.eq('MAP','STATE'))
print("colMapsInc ", colMapsInc);
print("mapInc ", mapInc);
print("mapStat ", mapStat);



var LimiteCaat = ee.Image().byte().paint(vis.bioma); 

// adding maps 
print(mapsMapbiomas.select(bandActual))


Map.addLayer(ee.Image.constant(1), {min:0, max: 1}, "base")
Map.addLayer(mapsMapbiomas.select(bandActual).updateMask(col8mapEst), vis.mapbiomas, bandActual);
Map.addLayer(mapInc, vis.incidents, "incidents", false);
Map.addLayer(mapStat, vis.states, "States", false);
Map.addLayer(LimiteCaat, {palette: 'FF0000'}, 'Caatinga');