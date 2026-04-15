var param = {
    'asset_baciasN4' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4good',
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga'
}

var baciaN2 = ee.FeatureCollection(param.asset_bacias)
var baciasN4 = ee.FeatureCollection(param.asset_baciasN4)
print(baciasN4.limit(2))
var lsBacias = ["7422","76111","76116","7612","7613",'7614',"7615","7617",
                "7618","7619","7742","7616","772","7742"]
var bacia_show = lsBacias[0]
lsBacias.forEach(function(nameBacia){
    print("processing bacia = " + nameBacia);
    var baciaN2Select = baciaN2.filter(ee.Filter.eq('nunivotto3', nameBacia)).geometry();
    baciaN2Select = baciaN2Select.buffer(-2000)
    // print(baciaN2Select.size());
    var baciasN4_sel = baciasN4.filterBounds(baciaN2Select);
    var lstN4 = baciasN4_sel.reduceColumns(ee.Reducer.toList(), ['fid']).get('list').getInfo();
    // print()
    if (bacia_show == nameBacia){    
        Map.addLayer(baciaN2Select, {color: 'ffbf94'}, "BaciaN2");
        Map.addLayer(baciasN4_sel, {color: '821d33'}, "BaciasN4");
    }
    print('ids ', lstN4)
})