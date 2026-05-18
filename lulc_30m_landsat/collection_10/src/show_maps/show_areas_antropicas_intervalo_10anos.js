
var visualizar = {
    antropic: {
        min: 0, max: 5,
        palette: ['#ffffff','#d8d8d8','#009295','#839220','#fec000','#9a1e23']
    },
    antropic_base: {min: 0, max: 1},
    antropic_depois : {
        min: 0, max: 2,
        palette: ['#ffffff','#ff9800','#730093']
    }
} 
// Spectral bands selected
var spectralBands = ['blue', 'red', 'green', 'nir', 'swir1', 'swir2'];
var param = { 
    assetMapC10: 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification',   
    vetor_biomas_250: 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    years: [
        ['1985','1994'],
        ['1995','2004'],
        ['2005','2014'],
        ['2015','2024']
    ],
    classes_antropics: [ 9,15,18,19,20,21,22,23,24,25,26,30,32,36,37,38,39,40,41,42,43,44,45,46,47,48,62,75],
    classes_base:      [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
};

var shp_ibge = ee.FeatureCollection(param.vetor_biomas_250)
                      .filter(ee.Filter.eq('CD_Bioma', 2))
                      .map(function(feat){return feat.set('id_code', 1)});
print("show ibge ", shp_ibge);
var mask_biome = shp_ibge.reduceToImage(['id_code'], ee.Reducer.first());

var outputVersion = '0-7';
var banda_activa = 'classification_2024'
var imgMapCol10 =  ee.ImageCollection(param.assetMapC10)
                        .filter(ee.Filter.eq('version', outputVersion))
                        .mosaic()
                        .updateMask(mask_biome);
print("show metadata ", imgMapCol10);
var decada = 1;
var mapa_antropic_decada = ee.Image.constant(0).updateMask(mask_biome);
param.years.forEach(
    function(list_years){
        var band_inic = 'classification_' + list_years[0];
        var band_end = 'classification_' + list_years[1];
        var img_tmp_inic = imgMapCol10.select(band_inic)
                                .remap(param.classes_antropics, param.classes_base, 0);
        if (list_years[0] == '1985'){
            mapa_antropic_decada = mapa_antropic_decada.add(img_tmp_inic);
            decada += 1;
        }
        var img_tmp_end = imgMapCol10.select(band_end)
                                .remap(param.classes_antropics, param.classes_base, 0);
        var img_diference = img_tmp_end.subtract(img_tmp_inic).eq(1).multiply(decada);
        
        mapa_antropic_decada = mapa_antropic_decada.add(img_diference);
        decada += 1;
        Map.addLayer(img_tmp_end, visualizar.antropic_base, 'base ' + list_years[1], false);
})

Map.addLayer(ee.Image.constant(1), visualizar.antropic_base, 'base');
var outline = ee.Image().byte().paint({
            featureCollection: shp_ibge,
            color: 1,
            width: 1.5
        });

Map.addLayer(mapa_antropic_decada, visualizar.antropic, 'mapa antropic_decada');
var mapa_antropic = mapa_antropic_decada.remap([0,1,2,3,4,5], [0,1,2,2,2,2]);
Map.addLayer(mapa_antropic, visualizar.antropic_depois, 'mapa antropic serie');
Map.addLayer(outline, {palette: '000000'}, 'bioma');

