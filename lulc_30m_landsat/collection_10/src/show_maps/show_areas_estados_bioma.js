var show_Caat = true;
var asset_est_r = 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster';
var asset_est_v = 'projects/mapbiomas-workspace/AUXILIAR/estados-2017';
var asset_semiarido = 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024';
var asset_biomas = 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil'; 
var lstEst = ['21','22','23','24','25','26','27','28','29','31','32'];
var estados_raster = ee.Image(asset_est_r);
var estados_vetor = ee.FeatureCollection(asset_est_v)
                          .filter(ee.Filter.inList('CD_GEOCUF', lstEst));
var semiarido = ee.FeatureCollection(asset_semiarido);
print("show metadata estados ", estados_vetor);
print("área do semiarido ", semiarido.geometry().area());
var shp_caatinga = ee.FeatureCollection(asset_biomas)
                        .filter(ee.Filter.eq('CD_Bioma', 2))
                        .geometry();
print("show metadados biomas ", shp_caatinga);
print("area biomas ", shp_caatinga.area());
Map.addLayer(estados_raster, {}, 'raster');
Map.addLayer(estados_vetor, {color: 'green'}, 'vetor');
Map.addLayer(semiarido, {}, 'Semiarido', false);
Map.addLayer(shp_caatinga, {color: 'yellow'}, 'limit Caatinga', show_Caat);

if (show_Caat){
    print("==== show areas of Caatinga limit ===");
}else{
    print("==== show areas of Semiarido limit ===");
}

var dictEst = {
    '21': 'MARANHÃO',
    '22': 'PIAUÍ',
    '23': 'CEARÁ',
    '24': 'RIO GRANDE DO NORTE',
    '25': 'PARAÍBA',
    '26': 'PERNAMBUCO',
    '27': 'ALAGOAS',
    '28': 'SERGIPE',
    '29': 'BAHIA',
    '31': 'MINAS GERAIS',
    '32': 'ESPÍRITO SANTO'
}

lstEst.forEach(
    function(num_id){
        print("estado == " + dictEst[String(num_id)]);
        var est_rec = estados_vetor.filter(ee.Filter.eq('CD_GEOCUF', num_id));
        print("área de estados ", est_rec.geometry().area());
        
        if (show_Caat){
            est_rec = est_rec.geometry().intersection(shp_caatinga);
            print(est_rec.area())
        }else{
            est_rec = est_rec.geometry().intersection(semiarido.geometry());
        }
        
    }  
)