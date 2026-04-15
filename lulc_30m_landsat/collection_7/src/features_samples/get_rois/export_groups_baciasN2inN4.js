var param = {
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'asset_baciasN2' : 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_nivel-4'
 }
 
 var bacias = ee.FeatureCollection(param.asset_bacias)
 var baciasN2 = ee.FeatureCollection(param.asset_baciasN2)
 //nunivotto3
 print(baciasN2.limit(2))
 print(bacias)
 
 Map.addLayer(baciasN2, {color: 'green'}, 'baciaN4')
 Map.addLayer(bacias, {color: 'red'}, 'baciaN2')
 
 var exportFeat = function(featCol, name){
                         var path_exp = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/joins/';
                         var pmtos = {
                           collection: featCol,
                           description: name,
                           assetId: path_exp + name
                         }
                         Export.table.toAsset(pmtos);
                     };
                     
 var listaNameBacias = [
     '741','7421','7422','744','745','746','7492','751','752','753',
     '754','755','756','757','758','759','7621','7622','763','764',
     '765','766','767','771','772','773', '7741','7742','775','776',
     '777','778','76111','76116','7612','7613','7614','7615','7616',
     '7617','7618','7619'
 ]
 print("show of list ", listaNameBacias);
 listaNameBacias.forEach(function(nameB){
                     var featB = bacias.filter(ee.Filter.eq('nunivotto3', nameB)).geometry();
                     var featC = baciasN2.filterBounds(featB);
                     featC = featC.map(function(feat){return feat.set('nunivotto3', nameB)})
                     print(featC);
                     exportFeat(featC, 'grupo_' + nameB)
             })
 
 
 