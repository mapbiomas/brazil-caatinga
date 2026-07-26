
var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = palettes.get('brazil');
var visMosaic = { min: 0.012, max: 0.22, bands: ['red', 'green', 'blue'] };
var nyear = '2023';
// Asset mapbiomas
var asset_col10 = "projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_coverage_v2";
var asset_classification = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1'; //BACIA_765_' + nyear + '_GTB_col11_BND_fm-v_2';

var asset_mosaic_32day = 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY';
var asset_bacias = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions';
var bacia_show = '765';

var shp_bacias = ee.FeatureCollection(asset_bacias)
                        .filter(ee.Filter.eq('nunivotto4', bacia_show))
                        .geometry();
var raster_class = ee.ImageCollection(asset_classification)
                            .filter(ee.Filter.eq('version', 2))
                            .filter(ee.Filter.eq('year', parseInt(nyear)));
                            
print("show metadata ", raster_class);

var raster_mapbiomas = ee.Image(asset_col10);

var mosaic_32dayMax = ee.ImageCollection(asset_mosaic_32day)
                        .filterDate(nyear + '-01-01', nyear + '-12-31')
                        .filterBounds(shp_bacias)
                        .max();
var mosaic_32dayMedian = ee.ImageCollection(asset_mosaic_32day)
                        .filterDate(nyear + '-01-01', nyear + '-12-31')
                        .filterBounds(shp_bacias)
                        .median();

Map.addLayer(mosaic_32dayMax, visMosaic, 'mosaico Max');
Map.addLayer(mosaic_32dayMedian, visMosaic, 'mosaico Median');

Map.addLayer(raster_mapbiomas, {
    bands: ['classification_' + nyear], 
    min: 0, 
    max: 75, 
    palette: palette, 
    format: 'png'
}, 
'Mapbiomas ' + nyear);

Map.addLayer(raster_class, {
    bands: ['classification_' + nyear], 
    min: 0, 
    max: 75, 
    palette: palette, 
    format: 'png'
}, 
'col11 ' + nyear);