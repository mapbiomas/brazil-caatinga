var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text');
var visualizar = {
    visclassCC: {
            "min": 0, 
            "max": 62,
            "palette":  palettes.get('classification8'),
            "format": "png"
    },
    visSec: {
        min: 1, max:7,
        palette: 'FFFFB2,32A65E,02D659,7c0a02,9932CC,ff6347,A4ADB2'
    },
    water: {
        min:0, max: 1,
        palette: '192cd7'
    },
    irrigate: {
        min:1, max: 2,
        palette: ['#e3b4eb','#3d1452']  // #d082de, #9932cc
    },
    fire: {
        min:0, max: 1,
        palette: 'd73619'
    },
    reservatorio: {
        min: 1, 
        max: 4, 
        palette: ['#0000FE','#00C4DA','#E5538C','#AC0024']
    }

}; 
/**
     * Exports a raster image to Google Drive.
     * 
     * @param {ee.Image} rasterExport - The raster image to be exported.
     * @param {string} descExport - The description of the exported image.
     * @param {ee.Geometry|ee.FeatureCollection} geo_limit - The geographic limit for the exported image.
     * 
     * @returns {void} - This function does not return any value.
     * 
     * @throws {Error} - Throws an error if the export operation fails.
     * 
     * @example
     * // Export a raster image to Google Drive
     * var rasterImage = ee.Image('projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1');
     * var description = 'exported_raster_image';
     * var geographicLimit = ee.FeatureCollection('projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022');
     * exportLayersofInterest(rasterImage, description, geographicLimit);
*/
function exportLayersofInterest(rasterExport, descExport, geo_limit){
    
    var pmtrosExpor = {
        image: rasterExport,
        description: descExport,
        folder: 'raster_priority',
        crs: 'EPSG:4326',
        region: geo_limit,
        fileFormat: 'GeoTIFF',
        scale: 30,
        maxPixels: 1e13,
        formatOptions: {cloudOptimized: true}
    }
    Export.image.toDrive(pmtrosExpor);
    
}

var param = {
    'asset_semirarido': 'projects/mapbiomas-workspace/AUXILIAR/semiarido',
    'asset_muncipio': 'projects/mapbiomas-workspace/AUXILIAR/municipios-2019',
    "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
    'asset_municipiosSemiarido': 'projects/mapbiomas-arida/ALERTAS/auxiliar/municipios-2019_semiarido',
    'asset_br': 'projects/mapbiomas-workspace/AUXILIAR/brasil_2km',
    'asset_Cover_Col8': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',  
    'asset_transicao': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_transitions_v1',
    'asset_annual_water': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_water_collection2_annual_water_coverage_v1',
    'asset_desf_vegsec': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_deforestation_secondary_vegetation_v2',
    'asset_irrigate_agro': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_irrigated_agriculture_v1',
    "asset_semiarido2024": 'users/nerivaldogeo/limite_novo_semiarido',
    "asset_biomas_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
    'asset_fire_annual': 'projects/mapbiomas-workspace/FOGO_COL2/SUBPRODUTOS/mapbiomas-fire-collection2-annual-burned-v2',
    "asset_Reservatorio": 'projects/mapbiomas-workspace/AMOSTRAS/GTAGUA/OBJETOS/CLASSIFICADOS/TESTE_1_raster',
    exportar: false,
    ano: 'classification_2022',
    classMapB:   [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,46,47,48,49,50,62],
    classNew:    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    classNAgro:  [0, 0, 0, 0, 0, 0, 0,41,41,41, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,48,41,41,39,41,41,48,48,48, 0, 0, 0],
};
var classeVegSec = [
    3, 4, 5, 11, 12, 15, 21, 23, 24, 25, 31, 32, 33, 41, 50,
    100, 103, 104, 105, 109, 111, 112, 113, 115, 120, 121, 123, 124, 125, 129,
    130, 131, 132, 133, 139, 141, 146, 148, 149, 150, 162, 200, 203, 204, 205,
    211, 212, 213, 223, 225, 229, 231, 232, 233, 249, 250, 300, 303, 304, 305,
    309, 311, 312, 313, 315, 320, 321, 323, 324, 325, 329, 330, 331, 332, 333,
    339, 341, 346, 348, 349, 350, 403, 404, 405, 411, 412, 413, 429, 432, 449,
    450, 509, 515, 520, 521, 524, 530, 539, 541, 546, 548, 562, 603, 604, 605,
    611, 612, 613, 629, 632, 649, 650, 700, 703, 704, 705, 709, 711, 712, 713,
    715, 720, 721, 723, 724, 725, 729, 730, 731, 732, 733, 739, 741, 746, 748,
    749, 750, 762
];
var classeVegSec7 = [
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    7, 7, 7
];
var showSemiarido = true;

var band_class = 'classification_2022';
var shpLimitBr = ee.FeatureCollection(param.asset_br);
print("show metadados Brasil " , shpLimitBr);
var biomas = ee.FeatureCollection(param.Im_bioma_250);
print("show metadados biomas do Brasil " , biomas);
var caatinga = biomas.filter(ee.Filter.eq("CD_Bioma", 2));
var shpSemiAr = ee.FeatureCollection(param.asset_semirarido);
var shpSemiAr24 = ee.FeatureCollection(param.asset_semiarido2024);
var areaSemiar24 = shpSemiAr24.geometry().area().divide(10000);
var areasemia21 = shpSemiAr.geometry().area().divide(10000);
var areaBr = shpLimitBr.geometry().area().divide(10000);
var areaCaat = caatinga.geometry().area().divide(10000);
var limiteReg = caatinga.geometry();
print("area total do Brasil ", areaBr);
print("area semirarido 2024 ", areaSemiar24);
var percent = ee.Number(areaSemiar24).divide(areaBr).multiply(100);
print("Semiarido representa % do brasil ", percent);
print("area Caartinga ", areaCaat);
print("area semirarido 2017 ", areasemia21);
print("ganhou áreas ", areaSemiar24 - areasemia21);
if (showSemiarido){
    print("setando o limite para o Semiárido");
    limiteReg = shpSemiAr24.geometry();
}else{
    print("O limite está setado para Caatinga!");
}

var shpMunpicio = ee.FeatureCollection(param.asset_muncipio);
var shpMnpioSemiaA = ee.FeatureCollection(param.asset_municipiosSemiarido);
var mapbiomasCol8 = ee.Image(param.asset_Cover_Col8).clip(limiteReg);
var mapbiomasCol8_22 = mapbiomasCol8.select('classification_2022');

Map.addLayer(ee.Image.constant(1), {palette: 'white'}, 'base', false);
Map.addLayer(ee.Image.constant(1), {palette: 'black'}, 'base-black');
Map.addLayer(shpMnpioSemiaA, {color: 'blue'}, 'shp municipios', false);

var shpBrasil = ee.Image().byte().paint({
                      featureCollection: shpLimitBr, color: 1, width: 1.8 });
Map.addLayer(shpBrasil, {palette: 'black'}, 'shp Brasil');

var shpSArido = ee.Image().byte().paint({
                      featureCollection: shpSemiAr, color: 1, width: 2.8 });
Map.addLayer(shpSArido, {palette: 'yellow'}, 'shp_arido', false);

var shpSArido24 = ee.Image().byte().paint({
                      featureCollection: shpSemiAr24, color: 1, width: 2.0 });
Map.addLayer(shpSArido24, {palette: 'red'}, 'shp_arido_2024');
Map.addLayer(mapbiomasCol8_22, visualizar.visclassCC, 'Col8 semiarido');


// camada remapeada de mapbiomasCol8_22
var layersAgro = mapbiomasCol8_22.remap(param.classMapB, param.classNAgro);
var band22Mapbiomas = "annual_Agriculture_from_Cover_2022";
exportLayersofInterest(layersAgro, band22Mapbiomas, shpSemiAr24.geometry());

var mapbiomasCol8_85 = mapbiomasCol8.select("classification_1985");
var pasto_a22_15 = mapbiomasCol8_22.eq(15).selfMask();
var mosaico_a22_21 = mapbiomasCol8_22.eq(21).selfMask();
var agro_a22 = mapbiomasCol8_22.remap(param.classMapB, param.classNew).selfMask();

var bandwaterclass = "annual_water_coverage_2022";
var imgWater = ee.Image(param.asset_annual_water).clip(limiteReg);
print(" asset imagens mapas water ", imgWater);
var imgWaterYY = imgWater.select(bandwaterclass);


var bandDesfVegSec = "classification_2021";
var mapsdesfVegSec = ee.Image(param.asset_desf_vegsec).clip(limiteReg);
print(" mapas de desforestação e Vegetação Secundaria ", mapsdesfVegSec);
var mapsdesfVegSec21 = mapsdesfVegSec.select(bandDesfVegSec);
mapsdesfVegSec21 = mapsdesfVegSec21.remap(classeVegSec, classeVegSec7);
var mascVegSec = mapsdesfVegSec21.gt(2).add(mapsdesfVegSec21.lt(7)).gt(1);
mapsdesfVegSec21 = mapsdesfVegSec21.updateMask(mascVegSec).selfMask();
bandDesfVegSec = "classification_1987";
var mapsdesfVegSec87 = mapsdesfVegSec.select(bandDesfVegSec);
mapsdesfVegSec87 = mapsdesfVegSec87.remap(classeVegSec, classeVegSec7);
mascVegSec = mapsdesfVegSec87.gt(2).add(mapsdesfVegSec87.lt(7)).gt(1);
mapsdesfVegSec87 = mapsdesfVegSec87.updateMask(mascVegSec).selfMask();

var bandIrrigat = "irrigated_agriculture_2022";
var mapsIrrigate = ee.Image(param.asset_irrigate_agro).clip(limiteReg);
print("mapas de irrigação ", mapsIrrigate);
var mapsIrrigateYY = mapsIrrigate.select(bandIrrigat);
mapsIrrigateYY = mapsIrrigateYY.divide(100).toByte();



var bandFire = "burned_area_2022";
var mapsFire = ee.Image(param.asset_fire_annual).clip(limiteReg);
print("Mapas de fire ", mapsFire);
var mapsFireYY = mapsFire.select(bandFire);

print(" pastagem 2022 ", pasto_a22_15);
print(" Mosaico de uso 2022 ", mosaico_a22_21);
print("Agropecuaria 2022", agro_a22);

var pasto_a85_15 = mapbiomasCol8_85.eq(15).selfMask();
var mosaico_a85_21 = mapbiomasCol8_85.eq(21).selfMask();
var agro_a85 = mapbiomasCol8_85.remap(param.classMapB, param.classNew).selfMask();

print(" pastagem 1985 ", pasto_a85_15);
print(" Mosaico de uso 1985 ", mosaico_a85_21);
print("Agropecuaria 1985", agro_a85);

var lstBiomes = ['CAATINGA','CERRADO','MATAATLANTICA'];
var reservatorio = ee.ImageCollection(param.asset_Reservatorio)
                        .filter(ee.Filter.eq('version', '2'))
                        .filter(ee.Filter.inList('biome', lstBiomes));

var reserv85 = reservatorio.filter(ee.Filter.eq('year', 1985)).mosaic().clip(limiteReg);
var reserv22 = reservatorio.filter(ee.Filter.eq('year', 2022)).mosaic().clip(limiteReg);

Map.addLayer(pasto_a22_15, {min: 0, max: 1, palette: '#edde8e'}, 'Col8 pasto 22', false);
Map.addLayer(mosaico_a22_21, {min: 0, max: 1, palette: '#ffefc3'}, 'Col8 mosaic 22', false);
Map.addLayer(agro_a22, {min: 0, max: 1, palette: '#E974ED'}, 'Col8 agro 22', false);

Map.addLayer(mapsdesfVegSec21, visualizar.visSec, 'Veg Secundaria 21', false);
Map.addLayer(imgWaterYY, visualizar.water, 'Annual Water 22', false);
Map.addLayer(mapsIrrigateYY, visualizar.irrigate, 'Annual Irrigate 22', false);
Map.addLayer(mapsFireYY, visualizar.fire, 'Annual Fire 22', false);
Map.addLayer(reserv22, visualizar.reservatorio, 'Annual Servatorio 22', false);

// exportar a camada de reservatorios de agua 
bandwaterclass = "annual_water_reservatorios_2022";
exportLayersofInterest(reserv22, bandwaterclass, shpSemiAr24.geometry())

bandwaterclass = "annual_water_coverage_1985";
bandDesfVegSec = "classification_1985";
bandIrrigat = "irrigated_agriculture_1985";
bandFire = "burned_area_1985";
imgWaterYY = imgWater.select(bandwaterclass);
mapsIrrigateYY = mapsIrrigate.select(bandIrrigat);
mapsFireYY = mapsFire.select(bandFire);

Map.addLayer(pasto_a85_15, {min: 0, max: 1, palette: '#edde8e'}, 'Col8 pasto 85', false);
Map.addLayer(mosaico_a85_21, {min: 0, max: 1, palette: '#ffefc3'}, 'Col8 mosaic 85', false);
Map.addLayer(agro_a85, {min: 0, max: 1, palette: '#E974ED'}, 'Col8 agro 85', false);
Map.addLayer(mapsdesfVegSec87, visualizar.visSec, 'Veg Secundaria 87', false);
Map.addLayer(imgWaterYY, visualizar.water, 'Annual Water 85', false);
Map.addLayer(mapsIrrigateYY, visualizar.irrigate, 'Annual Irrigate 85', false);
Map.addLayer(mapsFireYY, visualizar.fire, 'Annual Fire 85', false);
Map.addLayer(reserv85, visualizar.reservatorio, 'Annual Servatorio 85', false);

if(param.exportar){
    var nameExp = 'municipios-2019_semiarido';
    Export.table.toAsset({
        collection: shpMunpicio, 
        description: nameExp, 
        assetId: 'projects/mapbiomas-arida/ALERTAS/auxiliar/' + nameExp
    });
}


