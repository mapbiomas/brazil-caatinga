var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = palettes.get('brazil');

var param =  {
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 19, 19, 19, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 22],
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/aggrements',
        "anoIntInit": 1985,
        "anoIntFin": 2025,
}

var year_courrents = '2020';
var mapBiomas = ee.Image(param.assetMapbiomas100).select('classification_' + year_courrents);
print("dado de mapbiomas ", mapBiomas);

var limitCaat = ee.FeatureCollection(param.asset_grad);
Map.addLayer(limitCaat, {color: 'green'}, 'limit Caatinga');

var reagion_samples = ee.ImageCollection(param.asset_mask_toSamples).mosaic().select("layer_samples_" + year_courrents);
print("dado de reagion_samples ", reagion_samples);

Map.addLayer(
    mapBiomas, 
    {
      min: 0, 
      max: 75, 
      palette: palette, 
      format: 'png'
    }, 
    'maps ' + year_courrents
);
Map.addLayer(reagion_samples.selfMask(), {min: 0, max:1}, 'samples');