
var visualizar = {
    visMosaic: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },
    props: {  
        textColor: 'ff0000', 
        outlineColor: 'ffffff', 
        outlineWidth: 1.5, 
        outlineOpacity: 0.2
    }
} 

var assetMosaic = 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2';
var asset_bacias = "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga";
var lstSat = ["l5","l7","l8"];
var imgCol = ee.ImageCollection(assetMosaic)
                  .filter(ee.Filter.eq('biome', 'CAATINGA'))
                  .filter(ee.Filter.inList('satellite', lstSat));

print("Lista das primeiras 10 imagens ", imgCol.limit(10));


var version = imgCol.reduceColumns(ee.Reducer.toList(), ['version']).get('list');
print("List Version ", ee.List(version).distinct());


var satelite = imgCol.reduceColumns(ee.Reducer.toList(), ['satellite']).get('list');
print("List satelite ", ee.List(satelite).distinct());


var limitBacia = ee.FeatureCollection(asset_bacias);


Map.addLayer(limitBacia, {color: 'green'}, 'limit Bacia');
Map.addLayer(imgCol.filter(ee.Filter.eq('year', 2020)), visualizar.visMosaic, "mosaic 2020");
Map.addLayer(imgCol.filter(ee.Filter.eq('year', 2023)), visualizar.visMosaic, "mosaic 2023");