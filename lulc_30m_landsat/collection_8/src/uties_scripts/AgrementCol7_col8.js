// https://code.earthengine.google.com/6f8c27cb200425fc47e77e475a908abe
var ano = 2021
var nivel_legenda = 2      // nivel 1 ou 2
Map.addLayer(ee.Image.constant(1), {min:0, max: 1}, 'base ');
// AZUL somente na col 8
// VERMELHO somente col7.1
// CINZA mapeado nos 2 

var Palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = Palettes.get('classification7');
var vis = {
          'min': 0,
          'max': 62,
          'palette': palette,
          'format': 'png'
      };
var bioma250mil = ee.FeatureCollection('projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil')
                            .filter(ee.Filter.eq('Bioma', 'Caatinga'));
var assetCol71 = 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1';
var class_col71 = ee.Image(assetCol71).clip(bioma250mil.geometry());


var asset = 'projects/mapbiomas-workspace/COLECAO8/integracao';
var version = '0-1';
var class_col8 = ee.ImageCollection(asset)
    .filter(ee.Filter.eq('version', version)).min().clip(bioma250mil.geometry());
    
if (nivel_legenda == 1) {
  var class_col71_remap = class_col71.select('classification_'+ano)
          .remap([3,4,5,49,11,12,13,32,29,50,15,19,39,20,40,62,41,36,46,47,48, 9,21,23,24,30,25,33,31],
                 [1,1,1, 1,10,10,10,10,10,10,14,14,14,14,14,14,14,14,14,14,14,14,14,22,22,22,22,26,26])
          .rename('col71')
  
  var class_col8_remap = class_col8.select('classification_'+ano)
          .remap([3,4,5,49,11,12,13,32,29,50,15,19,39,20,40,62,41,36,46,47,48, 9,21,23,24,30,25,33,31],
                 [1,1,1, 1,10,10,10,10,10,10,14,14,14,14,14,14,14,14,14,14,14,14,14,22,22,22,22,26,26])
          .rename('S2')
          
  // listar classes para performar a análise 
  var classes = [1,10,14,22,26];
          
} else if (nivel_legenda == 2) {
  var class_col71_remap = class_col71.select('classification_'+ano)
          .remap([3,4,5,49,11,12,13,32,29,50,15,19,39,20,40,62,41,36,46,47,48, 9,21,23,24,30,25,33,31],
                 [3,4,5,49,11,12,13,32,29,50,15,18,18,18,18,18,18,18,18,18,18, 9,21,23,24,30,25,33,31])
          .rename('col71')
  
  var class_col8_remap = class_col8.select('classification_'+ano)
          .remap([3,4,5,49,11,12,13,32,29,50,15,19,39,20,40,62,41,36,46,47,48, 9,21,23,24,30,25,33,31],
                 [3,4,5,49,11,12,13,32,29,50,15,18,18,18,18,18,18,18,18,18,18, 9,21,23,24,30,25,33,31])
          .rename('S2')
          
  // listar classes para performar a análise 
  var classes = [3,4,5,49,11,12,13,32,29,50,15,18,9,21,23,24,30,25,33,31];
          
}

// listar anos para poerformar a análise
var years = [2021];


// para cada classe 
classes.forEach(function(class_i) {
  // para cada ano
  var images = ee.Image([]);

  years.forEach(function(year_j) {
    // selecionar a classificação do ano j
    var col8_j = class_col8_remap;
    var col71_j = class_col71_remap;
    
    // calcular concordância
    var conc = ee.Image(0).where(col8_j.eq(class_i).and(col71_j.eq(class_i)), 1)   // [1]: Concordância
                          .where(col8_j.eq(class_i).and(col71_j.neq(class_i)), 2)  // [2]: Apenas Sentinel
                          .where(col8_j.neq(class_i).and(col71_j.eq(class_i)), 3)  // [3]: Apenas Landsat
                          //.updateMask(biomes.eq(4));
    
    conc = conc.updateMask(conc.neq(0)).rename('territory_' + year_j);
    
    // build sinthetic image to compute areas
    var synt = ee.Image(0).where(conc.eq(1), col8_j)
                          .where(conc.eq(2), col71_j)
                          .where(conc.eq(3), col8_j)
                          .updateMask(conc)
                          .rename(['classification_' + year_j]);
    // build database
    images = images.addBands(conc).addBands(synt);
    
      Map.addLayer(images.select(['territory_' + year_j]), {palette: [
        'gray', 'blue', 'red'], min:1, max:3}, year_j + ' Agreement - Class ' + class_i, false);

  });
  
});



Map.addLayer(class_col71_remap, vis, 'Col 7.1 '+ano, false)
Map.addLayer(class_col8_remap, vis, 'Col 8 '+ano, false)



print("show limit Caatinga ", bioma250mil);
var blank = ee.Image(0).mask(0);
var outline = blank.paint(bioma250mil, 'AA0000', 2); 
var visPar = {'palette':'000000','opacity': 0.6};
Map.addLayer(outline, visPar, 'bioma250mil', true);