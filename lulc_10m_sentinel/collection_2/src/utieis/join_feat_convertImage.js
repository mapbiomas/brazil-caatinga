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

var dictBacias = {
    '7754': 1,
    '7691': 1,
    '7625': 1,
    '7584': 2,
    '746': 3,
    '752': 3,
    '753': 0,
    '765': 3,
    '771': 0,
    '773': 0,
    '7616': 2,
    '7564': 0,
    '7581': 0,
    '7618': 0,
    '7746': 0,
    '745': 3,
    '7424': 1,
    '7614': 1,
    '7561': 2,
    '755': 1,
    '7617': 2,
    '761111': 1,
    '7741': 3,
    '7422': 1,
    '7761': 1,
    '7671': 1,
    '7615': 2,
    '7411': 1,
    '7764': 2,
    '757': 2,
    '766': 3,
    '764': 3,
    '7541': 3,
    '7721': 2,
    '7619': 2,
    '7443': 3,
    '7544': 2,
    '7438': 2,
    '763': 1,
    '7591': 1,
    '7622': 4,
}


var asset_bacias = 'users/mapbiomascaatinga04/bacias_final_caatingaa';
var baciaSHP = ee.FeatureCollection(asset_bacias);
print(" aqui ver a bacia de buffer ", baciaSHP)
var featCol = ee.FeatureCollection([])
var lstBaciaSel = [
    '7754','7691','7625','7584','746','752','753','765','771','773','7616',
    '7564','7581','7618','7746','745','7424','7614','7561','755','7617',
    '761111','7741','7422','7761','7671','7615','7411','7764','757','766',
    '764','7541','7721','7619','7443','7544','7438','763','7591','7622',
];

var lstDoubroGeom = [
    '7625','7616','7424','7614','7561','755','7617','7741',
    '7422','7761','7671','7615','7411','757','766','764',
    '7541','7721','7619','7443','765','7544','7438','763',
    '7622','746',
];

var listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753','764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', 
    '7438', '763', '7591', '7592', '7622', '746'
];
var geo  = null;
var tmpfeat2 = null; 
var asset_out_raster= 'projects/ee-solkancengine17/assets/caat_49_regions_bacias';
var nameExp = 'raster_bacias_reg_';
var count = 1;
listaNameBacias.forEach(function(nbacia){
    var tmpfeat = baciaSHP.filter(ee.Filter.eq('nunivotto4', nbacia)).first();
    print("condicion ", lstBaciaSel.indexOf(nbacia))
    if (lstBaciaSel.indexOf(nbacia) > -1){
        print(" nbacia = " + nbacia);
        if (nbacia === '752'){
            print(tmpfeat.geometry().geometries())
            geo = ee.List(tmpfeat.geometry().geometries()).get(dictBacias[nbacia]);
            // print(" 752 ", geo)
            geo = ee.Geometry(geo);
            print(" listas duplicadas 752", geo);
        }else{
            if (lstDoubroGeom.indexOf(nbacia) > -1){
                // print(" " + nbacia )
                geo = ee.List(tmpfeat.geometry().coordinates()).get(dictBacias[nbacia]);
                print("    " + nbacia, geo);
                geo = ee.List(geo).get(0)
                print(" listas duplicadas ", geo);
            }else{
                geo = ee.List(tmpfeat.geometry().coordinates()).get(dictBacias[nbacia]);
                print("lista simples  ", geo);
            }
        }
        if (nbacia !== '752'){
            print('aqui ele modificou ')
            geo = ee.Geometry.Polygon(geo);
        }
        print("geometry ", geo);
        tmpfeat2 = baciaSHP.filter(ee.Filter.eq('nunivotto4', nbacia)).first();
        tmpfeat = ee.Feature(geo);
        tmpfeat = tmpfeat.copyProperties(tmpfeat2);
        Map.addLayer(geo, {color: 'yellow'}, 'bacias');
    };
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

Map.addLayer(baciaSHP, {color: 'green'}, "bacias");

var asset_out= 'projects/ee-solkancengine17/assets/shape'
var nameE = 'bacias_caatinga_div_49_regions'
processoExportar(featCol, nameE, asset_out);
