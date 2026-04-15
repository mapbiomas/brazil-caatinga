//https://code.earthengine.google.com/6897c6ab80591e9da337771bf6bcfdec

var getAllFeatsfromFolder = function(mpath){

    var getParam = ee.data.getList(mpath)    
    var featTotal = ee.FeatureCollection([])

    getParam.forEach(function(item){
        var name = item.id.split('/')[6];
        var feat_tmp = ee.FeatureCollection(item.id);
        print(ee.String("item = " + name + "| size = ").cat(feat_tmp.size()));
        featTotal = featTotal.merge(feat_tmp);
    })

    return featTotal;
}

var asset_bacias = 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga';
var bacias = ee.FeatureCollection(asset_bacias);
var asset_folder = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv3'};
var rois_all = getAllFeatsfromFolder(asset_folder);



Map.addLayer(bacias, {color: 'ffbf94'}, "alertas" )
Map.addLayer(rois_all, {color: '821d33'}, 'ROIs')

