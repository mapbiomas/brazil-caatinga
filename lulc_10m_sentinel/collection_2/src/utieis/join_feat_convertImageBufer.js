function processoExportar(areaFeat, nameT, asset_output){      
    var optExp = {
          'collection': ee.FeatureCollection(areaFeat), 
          'description': nameT, 
          'assetId': asset_output + "/" + nameT     
        };    
    Export.table.toAsset(optExp) ;
    print(" salvando ... " + nameT + "..!")      ;
}

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

var asset_bacias_buffer = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions';
var bacia_buffer = ee.FeatureCollection(asset_bacias_buffer);
print(" aqui ver a bacia de buffer ", bacia_buffer)
var featCol = ee.FeatureCollection([])
var lstBaciaSel = ['761111', '7721', '7591'];

var listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753','764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', 
    '7438', '763', '7591', '7592', '7622', '746'
]
var geo  = null;
var tmpfeat2 = null; 
var asset_out_raster= 'projects/ee-solkancengine17/assets/bacias_imagem';
var nameExp = 'raster_bacias_reg_';
var count = 1;
listaNameBacias.forEach(function(nbacia){
    var tmpfeat = bacia_buffer.filter(ee.Filter.eq('nunivotto4', nbacia)).first();
    if (lstBaciaSel.indexOf(nbacia) > -1){
        print(" nbacia = " + nbacia);
        if (nbacia === '7721'){
            print(" ", nbacia )
            geo = ee.List(tmpfeat.geometry().coordinates()).get(2);
            // print(" kkk ggg ", geo);
        }else{
            geo = ee.List(tmpfeat.geometry().coordinates()).get(1);
            // print("==> geo ", geo);
        }
        geo = ee.Geometry.Polygon(geo);
        print("geometry ", geo);
        tmpfeat2 = bacia_buffer.filter(ee.Filter.eq('nunivotto4', nbacia)).first();
        tmpfeat = ee.Feature(geo, {});
        tmpfeat = tmpfeat.copyProperties(tmpfeat2);
        Map.addLayer(geo, {color: 'yellow'}, 'bacias');
    }
    tmpfeat = ee.Feature(tmpfeat).set('id_codigo', count);
    print(" " + nbacia, tmpfeat);
    geo = tmpfeat.geometry();
    featCol = featCol.merge(ee.FeatureCollection([tmpfeat]));
    var imgBacia = ee.FeatureCollection([tmpfeat]).reduceToImage(['id_codigo'], ee.Reducer.first())
    imgBacia = imgBacia.set('id_codigo', count);
    processoExportarImage(imgBacia, nameExp + nbacia + "_" +  String(count),asset_out_raster,  geo)
    count += 1;
})
print("featCol ", featCol);

Map.addLayer(bacia_buffer, {color: 'green'}, "bacias");

var asset_out= 'projects/ee-solkancengine17/assets/shape'
var nameE = 'bacias_hidrografica_caatinga_49_regions'
processoExportar(featCol, nameE, asset_out);
