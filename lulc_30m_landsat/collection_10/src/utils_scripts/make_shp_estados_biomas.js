var make_shp = true;
var asset_biomas = 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil';
var asset_estados = 'projects/mapbiomas-workspace/AUXILIAR/estados-2016';
var asset_intersection = 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_estados_2016_buffer3K';
var shp_biomas = ee.FeatureCollection(asset_biomas);
var shp_estados = ee.FeatureCollection(asset_estados);

print("shp biomas ", shp_biomas);
print("shp estados  ", shp_estados);
if (make_shp){
    var cd_biomas = shp_biomas.reduceColumns(ee.Reducer.toList(), ['CD_Bioma']).get('list').getInfo();
    var feat_estados_biomas = ee.FeatureCollection([]);
    cd_biomas.forEach(
        function(cod_biomas){
            var feat_tmp = ee.Feature(shp_biomas
                                  .filter(ee.Filter.eq('CD_Bioma', cod_biomas))
                                  .first()).geometry();
            var regs_estados = shp_estados.filterBounds(feat_tmp);
            print("show size polygons " + cod_biomas, regs_estados);
            
            var regions_estados = regs_estados.map(
                                function(feat){
                                    var intersect = feat_tmp.intersection(feat.geometry());
                                    var shp_buffer = intersect.buffer(3000);
                                    var feat_exp = ee.Feature(shp_buffer, {'CD_Bioma': cod_biomas})
                                    feat_exp = feat_exp.copyProperties(feat, ['CD_GEOCUF', 'NM_ESTADO'])
                                    return feat_exp;
                                });
            feat_estados_biomas = feat_estados_biomas.merge(regions_estados).flatten();
    });
    
    
    var id_asset = 'projects/mapbiomas-workspace/AUXILIAR/';
    var name_export = 'biomas_IBGE_estados_2016_buffer3K';
    
    Export.table.toAsset({
                collection: feat_estados_biomas, 
                description: name_export, 
                assetId: id_asset + name_export
            });
        
}else{
    var shp_estados_biomas = ee.FeatureCollection(asset_intersection);
    Map.addLayer(shp_estados_biomas, {color: 'green'}, 'intersection');
}
