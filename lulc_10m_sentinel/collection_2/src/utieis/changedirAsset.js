var assetin = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVY/bacia_7622_GTB_col9-S2_v1';
var assetout = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX/bacia_7622_GTB_col9-S2_v1';

var gg = function(assetIn, assetOut){
        ee.data.renameAsset(assetIn, assetOut);
}
// gg(assetin, assetout)


var palettes = require('users/mapbiomas/modules:Palettes.js');
var vis = {
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
var imgRaster = ee.Image(assetout);

Map.addLayer(imgRaster.select('classification_2023'), vis.visclass, '2023')