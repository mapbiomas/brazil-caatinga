
function processoExportarImage(rasterExp, nametoExp, assetOutput, myGeo){    
    var optExp = {
        'image': rasterExp,
        'description': nametoExp,
        'assetId': assetOutput + "/" + nametoExp,
        'scale': 10,
        'pyramidingPolicy': {'.default': 'mode'},
        'maxPixels': 1e13,
        'region': myGeo
      }
    Export.image.toAsset(optExp); 
}
var exportar = true;
var asset_limit = 'users/CartasSol/shapes/nCaatingaBff3500';
// var asset_estrada = 'projects/mapbiomas-arida/copy_estradas_osm_caa';
var asset_estrada = 'projects/mapbiomas-arida/estradas_dnit_caat';
// var asset_raster_estrada = 'projects/ee-solkancengine17/assets/raster_estradas_osm_Caatinga'
var asset_raster_estrada = 'projects/ee-solkancengine17/assets/estradas_dnit_caat'
var feat_estrada = ee.FeatureCollection(asset_estrada);
print("número de feature ", feat_estrada.size());
print('show metadata ', feat_estrada.limit(4));
var geoCaatinga = ee.FeatureCollection(asset_limit);



Map.addLayer(feat_estrada, {color: 'red'}, 'estrada');
Map.addLayer(geoCaatinga, {color: 'yellow'}, 'limitCaat');
Map.setOptions("SATELLITE");

if (exportar){
    var nameExport = 'estradas_dnit_caat';
    var assetExp = 'projects/ee-solkancengine17/assets';
    var featC_estrada = feat_estrada.map(function(feat){return feat.set('class', 1)});
    var raster_estrada = featC_estrada.reduceToImage(['class'], ee.Reducer.first());
    Map.addLayer(raster_estrada, {}, 'estrada raster');
    processoExportarImage(raster_estrada.selfMask(), nameExport, assetExp, geoCaatinga.geometry());
}else{
    print("read raster layer");
    var raster_estrada = ee.Image(asset_raster_estrada);
    Map.addLayer(raster_estrada, {}, 'estrada raster'); //
}