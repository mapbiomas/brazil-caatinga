
var assetMatopiba = 'users/CartasSol/shapes/limiteMatopiba'; 
var matopiba = ee.FeatureCollection(assetMatopiba).geometry();

var pathEst = 'users/solkancengine17/shps_public/BR_ESTADOS_2022';
var shpEstados = ee.FeatureCollection(pathEst).filterBounds(matopiba);
              
//
var Legend = require('users/joaovsiqueira1/packages:Legend.js');
var Palettes = require('users/mapbiomas/modules:Palettes.js');
var paletteC7 = Palettes.get('classification7');
//
var asset = 'projects/earthengine-legacy/assets/projects/mapbiomas-workspace/COLECAO8/integracao';
var mapCol8 = ee.ImageCollection(asset).filter('version=="0-16"')
                              .min().select('classification_2022');

// mascara das classes naturais 
var classesNaturais = mapCol8.lt(14).add(mapCol8.eq(29)).add(mapCol8.eq(32)).add(mapCol8.eq(50));
var pixelArea = ee.Image.pixelArea().divide(10000).clip(matopiba);
pixelArea = pixelArea.multiply(classesNaturais);

lstEst.forEach(
    function(idUF){
        var regionEst = estadosMatopiba.filter(ee.Filter.eq('SIGLA_UF', idUF));
        // print(regionEst)
        var param  = {
              'reducer': ee.Reducer.sum(),
              'geometry': regionEst.geometry(),
              'scale': 30,
              'maxPixels': 1e13
          }
        var hist = pixelArea.reduceRegion(param)
        print("estado " + idUF, hist.values());
        print(" AREA_KM2 ", regionEst.first().get('AREA_KM2'));
        
})

Map.addLayer(mapCol8, {format: 'png', palette: paletteC7, min: 0, max: 62 }, "mapbiomas 2022");
Map.addLayer(classesNaturais , {min: 0, max: 1, palette: '000000, ff0acb'}, 'classes naturais');
var regoes = ee.Image().byte().paint({
  featureCollection: estadosMatopiba,
  color: 1,
  width: 1
});
Map.addLayer(regoes, {palette: 'AA2630'}, 'estadosMatopiba')