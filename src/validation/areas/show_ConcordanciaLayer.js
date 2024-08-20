//var ano = 2021

var calculateArea = function (image, geometry) {

    var areas = pixelArea.addBands(image)
        .reduceRegion({
            reducer: ee.Reducer.sum().group(1),
            geometry: geometry,
            scale: 4,
            maxPixels: 1e12
        });

    areas = ee.List(areas.get('groups')).map(getProperties);

    return areas;
};

// AZUL somente na col 9
// VERMELHO somente col 8
// CINZA mapeado nos 2 

// listar anos para poerformar a análise
var years = 2022;
var selBacia = '773';
var yearcourrent = 2020;
var version = 5;

var asset_bacias = "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga"
var shpBacias = ee.FeatureCollection(asset_bacias)
                    .filter(ee.Filter.eq('nunivotto3', selBacia))
                    .geometry();

var bioma250mil = ee.FeatureCollection('projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil');
Map.addLayer(bioma250mil,{},'biomas',false)
var biomaMA = bioma250mil.filter(ee.Filter.eq('CD_Bioma', 4))

var Palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = Palettes.get('classification8');
var vis = {
          'min': 0,
          'max': 62,
          'palette': palette,
          'format': 'png'
      };

print(vis)


var class_col80 = ee.Image('projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1')//.clip(biomaMA)

//var class_col90 = ee.Image('projects/mapbiomas-workspace/COLECAO9/pos_classificacao-ma/MA_col9_p08b_v10').clip(biomaMA)
//var class_col90 = ee.Image('projects/mapbiomas-workspace/COLECAO9/pos_classificacao-ma/MA_col9_p10e_v21').clip(biomaMA)
    

var class_col90 = ee.ImageCollection('projects/mapbiomas-workspace/COLECAO9/integracao')
               .filter(ee.Filter.eq('version','0-1'))
               .mosaic()
//               .clip(biomaMA)
print('class_col90',class_col90)
//'0-1',


// listar classes para performar a análise 
var classes = [3,4,5,6,49,11,12,13,32,29,50,15,18,9,21,23,24,30,25,33,31];
    
var areaClass = null;
// para cada classe 
// para cada ano
var col8_j = class_col80.select('classification_'+ yearcourrent).clip(shpBacias);
var col9_j = class_col90.select('classification_'+ yearcourrent).clip(shpBacias);
classes.forEach(function(class_i) {
  var images = ee.Image([]);

  // selecionar a classificação do ano j
  
  // calcular concordância
  var conc = ee.Image(0).where(col8_j.eq(class_i).and(col9_j.eq(class_i)), 1)   // [1]: Concordância
                        .where(col8_j.neq(class_i).and(col9_j.eq(class_i)), 2)  // [3]: Apenas Landsat
                        .where(col8_j.eq(class_i).and(col9_j.neq(class_i)), 3)  // [2]: Apenas Sentinel
                        //.updateMask(biomes.eq(4));
  
    conc = conc.updateMask(conc.neq(0)).rename('territory_' + year_j);
    
    // build sinthetic image to compute areas
    var synt = ee.Image(0).where(conc.eq(1), col8_j)
                          .where(conc.eq(2), col9_j)
                          .where(conc.eq(3), col8_j)
                          .updateMask(conc)
                          .rename(['classification_' + year_j]);
    // build database
    images = images.addBands(conc).addBands(synt);
    
    Map.addLayer(images.select(['territory_' + year_j]), {palette: [
      'gray', 'blue', 'red'], min:1, max:3}, year_j + ' Agreement - Class ' + class_i, false);
    
    areaClass = calculateArea(conc, shpBacias)
    print('area da classe ' + class_i, areaClass);
});
Map.addLayer(col8_j, vis, 'Col 8   '+year_j, false)
Map.addLayer(col9_j, vis, 'Col9 '+year_j, false)





var blank = ee.Image(0).mask(0);
var outline = blank.paint(bioma250mil, 'AA0000', 2); 
var visPar = {'palette':'000000','opacity': 0.6};
Map.addLayer(outline, visPar, 'bioma250mil', false);