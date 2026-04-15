
var param = { 
    assetMap: 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',   
    // assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX',  
    assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill',   
    asset_mosaicS2: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',  
    asset_mosaicL: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',  
    assetBacia: 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',   
    asset_region_img_buffer: 'projects/ee-solkancengine17/assets/bacias_imagem',  
    // asset_estradas:  'projects/mapbiomas-arida/copy_estradas_osm_caa', 
    asset_estradas: 'projects/mapbiomas-arida/estradas_dnit_caat',  
    // asset_estradas_raster:  'projects/ee-solkancengine17/assets/raster_estradas_osm_Caatinga', 
    asset_estradas_raster: 'projects/ee-solkancengine17/assets/estradas_dnit_caat',
    years: ['2016','2017','2018','2019','2020','2021','2022','2023'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    classMapB : [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62],
    classNew  : [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21], 
    listBiomas: ['CERRADO','CAATINGA','MATAATLANTICA']
}
var palettes = require('users/mapbiomas/modules:Palettes.js');
var visualizar = {
    visclass: {
            "min": 0, 
            "max": 62,
            "palette":  palettes.get('classification8'),
            "format": "png"
    },
    visMosaic: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },    
} 


// --- building all map as images , shp files and mosaics

var shp_bacias = ee.FeatureCollection(param.assetBacia);
var raster_bacias = ee.ImageCollection(param.asset_region_img_buffer);
var mosaic_S2 = ee.ImageCollection(param.asset_mosaicS2).filter(
                                ee.Filter.inList('biome', param.listBiomas)).select(
                                    param.bandas);

var mosaic_L8 = ee.ImageCollection(param.asset_mosaicL).filter(
                                        ee.Filter.inList('biome', param.listBiomas)).select(
                                            param.bandas);


var map_col90 = ee.Image(param.assetMap).updateMask(raster_bacias.mosaic().gt(0));
print("map_col90 ",map_col90);
var year_show = '2016';
var versAct = '4';
var banda_activa = "classification_" + year_show;
var bacia_activa = "All Basin";
// var banda_ref = "CLASS_" +  year_show;
//var bacia_focused = '741';
var mapS2_version = ee.ImageCollection(param.assetclass).filter(ee.Filter.eq('version', parseInt(versAct))).max();
var feat_estrada = ee.FeatureCollection(param.asset_estradas);
var raster_estrada = ee.Image(param.asset_estradas_raster);
Map.setOptions("SATELLITE")


var FeatBacias = ee.Image().byte().paint(shp_bacias, 1, 1);
FeatBacias = FeatBacias.visualize({palette: 'FF0000', 'opacity': 0.7});

var mosaic_S2_year = mosaic_S2.filter(ee.Filter.eq('year', parseInt(year_show))).median();
mosaic_S2_year = mosaic_S2_year.updateMask(raster_bacias.mosaic().gt(0));

Map.addLayer(mosaic_S2_year, visualizar.visMosaic, "mosaic_S2 ");

var map_Vers = mapS2_version.select(banda_activa).remap(param.classMapB, param.classNew)
Map.addLayer(map_Vers, visualizar.visclass, "Map S2 v" + versAct + ' ' + year_show);
Map.addLayer(feat_estrada, {color: '#db4d4f'}, 'estrada', false);
Map.addLayer(raster_estrada, {max: 1 , palette: '#db4d4f'}, 'raster estrada');
Map.addLayer(FeatBacias, {}, "bacia");

