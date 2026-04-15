/**
 * user defined parameters
 */
// var 

var version = '1';


var vis = {
    mosaicnew: {
      'bands': ['swir1_median', 'nir_median', 'red_median'],
      // 'gain': '0.08,0.06,0.2',
      'min': 0.001, 'max': 0.4, 
      'gamma': 0.5
    },
    mosaicWet: {
        'bands': ['swir1_median_wet', 'nir_median_wet', 'red_median_wet'],
        // 'gain': '0.08,0.06,0.2',
        'min': 0.001, 'max': 0.4,
        'gamma': 0.5
    },
    mosaicDry: {
        'bands': ['swir1_median_dry', 'nir_median_dry', 'red_median_dry'],
        // 'gain': '0.08,0.06,0.2',
        'min': 0.001, 'max': 0.4,
        'gamma': 0.5
    },
    mosaico: {
        'bands':  ['swir1_median', 'nir_median', 'red_median'],
        'min': 50, 'max': 4500,        // 'gain': '0.08,0.06,0.2',
        'gamma': 0.5
    },
    mosaicoWet: {
        'bands':  ['swir1_median_wet', 'nir_median_wet', 'red_median_wet'],
        'min': 50, 'max': 4500,        
        'gamma': 0.5
    },
    mosaicoDry: {
        'bands':  ['swir1_median_dry', 'nir_median_dry', 'red_median_dry'],
        'min': 50, 'max': 4500,  
        'gamma': 0.5
    },
    new_evi: {
        min: 1300, max: 3000,
        palette: [
            '#ffffff','#ffffcc','#ffeda0','#fed976','#feb24c','#fd8d3c',
            '#bbeb2a','#28e348','#2c9f30','#1a621c'
        ]
    },
    evi: {
        min: 1300, max: 20000,
        palette: [
            '#ffffff','#ffffcc','#ffeda0','#fed976','#feb24c','#fd8d3c',
            '#bbeb2a','#28e348','#2c9f30','#1a621c'
        ]
    },
};
// // define a geometry
// var pathRow = '217073';

// var geometry = ee.Feature(
//     ee.FeatureCollection(regionAsset)
//         .filterMetadata('WRSPR', 'equals', pathRow)
//         .first())
//     .geometry();

var param = {
    'regionAsset': 'projects/mapbiomas-workspace/AUXILIAR/landsat-scenes',
    'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    "anoIntInit": 1985,
    "anoIntFin": 2023 
}
  
// define a list of parameters for each mosaic
var params = [
    { 'year': 1985, 'dateStart': '1985-01-01', 'dateEnd': '1985-12-31', 'territory': 'Caatinga' },
    { 'year': 1986, 'dateStart': '1986-01-01', 'dateEnd': '1986-12-31', 'territory': 'Caatinga' },
    { 'year': 1987, 'dateStart': '1987-01-01', 'dateEnd': '1987-12-31', 'territory': 'Caatinga' },
    { 'year': 1988, 'dateStart': '1988-01-01', 'dateEnd': '1988-12-31', 'territory': 'Caatinga' },
    { 'year': 1989, 'dateStart': '1989-01-01', 'dateEnd': '1989-12-31', 'territory': 'Caatinga' },
    { 'year': 2020, 'dateStart': '2020-01-01', 'dateEnd': '2020-12-31', 'territory': 'Caatinga' },
    { 'year': 2021, 'dateStart': '2021-01-01', 'dateEnd': '2021-12-31', 'territory': 'Caatinga' },
    { 'year': 2022, 'dateStart': '2022-01-01', 'dateEnd': '2022-12-31', 'territory': 'Caatinga' },
    { 'year': 2023, 'dateStart': '2023-01-01', 'dateEnd': '2023-12-31', 'territory': 'Caatinga' },
    { 'year': 2024, 'dateStart': '2024-01-01', 'dateEnd': '2024-12-31', 'territory': 'Caatinga' },
    
];


/**
 * import modules
 */
var bns = require('users/mapbiomas/mapbiomas-mosaics:modules/BandNames.js');
var csm = require('users/mapbiomas/mapbiomas-mosaics:modules/CloudAndShadowMasking.js');
var col = require('users/mapbiomas/mapbiomas-mosaics:modules/Collection.js');
var dtp = require('users/mapbiomas/mapbiomas-mosaics:modules/DataType.js');
var ind = require('users/mapbiomas/mapbiomas-mosaics:modules/SpectralIndexes.js');
var mis = require('users/mapbiomas/mapbiomas-mosaics:modules/Miscellaneous.js');
var mos = require('users/mapbiomas/mapbiomas-mosaics:modules/Mosaic.js');
var sma = require('users/mapbiomas/mapbiomas-mosaics:modules/SmaAndNdfi.js');

// Regions Caatinga, parte do Cerrado e Mata Atlântica 
var limitBoundCaat = ee.FeatureCollection(param.assetrecorteCaatCerrMA)
// Mosaico Landsat Mapbiomas 
var imgMosaic = ee.ImageCollection(param.asset_mosaic_mapbiomas)
                    .filterBounds(limitBoundCaat);

// landsat collections
var collectionId = 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY';

// Spectral bands selected
var spectralBands = ['blue', 'red', 'green', 'nir', 'swir1', 'swir2'];

// endemembers collection
var endmembers = sma.endmembers['landsat-8'];

/**
 * script to run the mosaics
 */
params.forEach(
    function (obj) {

        var collection = ee.ImageCollection(collectionId)
            .filter(ee.Filter.date(obj.dateStart, obj.dateEnd))
            .filter(ee.Filter.bounds(limitBoundCaat))
            .select(spectralBands);

        // // apply scaling factor
        // collection = collection.map(
        //     function (image) {
        //         return image.multiply(10000).copyProperties(image, ['system:time_start', 'system:time_end']);
        //     }
        // );
        if (obj.year < 2024){
            var imgMosaicYY = imgMosaic.filter(ee.Filter.eq('year', obj.year));
        } 

        // apply SMA
        collection = collection.map(
            function (image) {
                return sma.getFractions(image, endmembers);
            }
        );

        // calculate SMA indexes        
        collection = collection
            .map(sma.getNDFI)
            .map(sma.getSEFI)
            .map(sma.getWEFI)
            .map(sma.getFNS);

        // calculate Spectral indexes        
        collection = collection
            .map(ind.getCAI)
            .map(ind.getEVI2)
            .map(ind.getGCVI)
            .map(ind.getHallCover)
            .map(ind.getHallHeigth)
            .map(ind.getNDVI)
            .map(ind.getNDWI)
            .map(ind.getPRI)
            .map(ind.getSAVI);

        var mosaic = mos.getMosaic({
            'collection': collection,
            'dateStart': obj.dateStart,
            'dateEnd': obj.dateEnd,
            'bandReference': 'ndvi',
            'percentileDry': 25,
            'percentileWet': 75,
        });

        // get other bands
        mosaic = mis.getSlope(mosaic);
        mosaic = mis.getEntropyG(mosaic);

        // // set band data types
        // // mosaic = dtp.setBandTypes(mosaic);

        // set mosaic properties
        mosaic = mosaic
            .set('year', obj.year)
            .set('territory', obj.territory)
            .set('version', version);

        print(mosaic);
        print("lista de bandas ", mosaic.bandNames());

        var name = (
            obj.territory.replace(' ', '') + '-MosM-' +
            // pathRow + '-' +
            obj.year + '-' +
            version
        )//.toUpperCase();

        mosaic = mosaic.clip(limitBoundCaat);

        Map.addLayer(mosaic, vis.mosaicnew, name, false);
        Map.addLayer(mosaic, vis.mosaicWet, name + '_wet', false);
        Map.addLayer(mosaic, vis.mosaicDry, name + '_dry', false);
        Map.addLayer(mosaic.select("evi2_median"), vis.new_evi, 'new evi', false);
        if (obj.year < 2024){
            Map.addLayer(imgMosaicYY, vis.mosaico, 'mosMapbiomas-' + obj.year, false);
            Map.addLayer(imgMosaicYY, vis.mosaicoWet, 'mosMapbiomas-Wet' + obj.year, false);
            Map.addLayer(imgMosaicYY, vis.mosaicoDry, 'mosMapbiomas-Dry' + obj.year, false);
            Map.addLayer(imgMosaicYY.select("evi2_median"), vis.evi, 'mapbiomas evi', false);
        }
    }
);

// Map.centerObject(limitBoundCaat, 10);

