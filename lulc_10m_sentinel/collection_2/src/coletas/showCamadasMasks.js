// 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',var palettes = require('users/mapbiomas/modules:Palettes.js');
var palettes = require('users/mapbiomas/modules:Palettes.js');
var vis= {
    mosaico: {
        min: 20, max: 2500,
        bands: ["red_median","green_median","blue_median"]
    },
    visclassCC: {
        "min": 0, 
        "max": 62,
        "palette":  palettes.get('classification8'),
        "format": "png"
    },
    visMask: {min:0, max: 1, palette: 'FF0000'}
}

var param = {
    lstYears: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
    lstBiomas: ['CAATINGA','CERRADO','MATAATLANTICA'],  //
    // asset_mosaic: 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',
    asset_mosaic: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
    asset_mask: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample',
    assetMapbiomas90: 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
    biomas_raster: 'projects/mapbiomas-workspace/AUXILIAR/biomas-2019-raster',
    asset_bacias_buffer: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
}

var biomaCaat = ee.Image(param.biomas_raster).eq(5);
var rasterMosaicS2 = ee.ImageCollection(param.asset_mosaic).filter(ee.Filter.inList('biome', param.lstBiomas));
var imMasks = ee.ImageCollection(param.asset_mask).mosaic();
var imMapbiomas90 = ee.Image(param.assetMapbiomas90).updateMask(biomaCaat);
var shp_bacias = ee.FeatureCollection(param.asset_bacias_buffer);

print("know bands of mask to samples ", imMasks);

print("know número de imagens por ano ", rasterMosaicS2.aggregate_histogram('year'));
print("show metadata ", rasterMosaicS2.limit(10));
print("Know how many image the asset have ", rasterMosaicS2.size());

// Map.addLayer(biomaCaat.selfMask(), {min:0, max: 1}, 'Caat')
var showMosaic = false;
param.lstYears.forEach(function(nyear){
    var imgCYY = rasterMosaicS2.filter(ee.Filter.eq('year', nyear));
    var bandaactiva = 'classification_' + String(nyear);
    var bandMask = 'mask_sample_' + String(nyear);
    
    if (nyear === 2023){
        showMosaic = true;
    }
    Map.addLayer(imgCYY, vis.mosaico, 'mosaic-' + String(nyear), showMosaic);
    Map.addLayer(imMapbiomas90.select(bandaactiva), vis.visclassCC, bandaactiva,  showMosaic);
    Map.addLayer(imMasks.select(bandMask).selfMask(), vis.visMask, 'mask_' + String(nyear), showMosaic);
    
})
// 7721, 761111
Map.addLayer(shp_bacias, {color: '#344e41'}, 'shp regions');