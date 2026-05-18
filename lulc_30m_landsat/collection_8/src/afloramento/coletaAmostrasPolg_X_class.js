//https://code.earthengine.google.com/3069a20708e8d4a9b483932fbb5f91ea
var featuresreduce = [
    'blue_median', 'green_median','red_median', 'nir_median', 'nir_median_dry', 
    'nir_median_wet', 'nir_min', 'nir_stdDev', 'swir1_median', 'swir1_median_dry', 
    'swir1_median_wet', 'swir1_min', 'swir1_stdDev', 'swir2_median', 'swir2_median_wet',
    'swir2_median_dry', 'swir2_stdDev', 'ndvi_median_dry', 'evi2_median_dry', 
    'evi2_median_wet', 'evi2_amp', 'evi2_stdDev', 'savi_median_dry', 'gcvi_median_dry', 'slope'
]
var palettes = require('users/mapbiomas/modules:Palettes.js');
var vis = { 
    'mapbiomas': {
        'min': 0, 
        'max': 62,  
        'palette': palettes.get('classification7')
    },
    'points': {
        color: '#FF7803',
    },
    'maskAfloramento': {
        min: 0,
        max: 1,
        palette: ['FFFFFF','FE9929']
    },
    'visMosaic': {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },
};

var exportSHPAflor = function(featCol, nameshp){
    var outAssetROIs = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/AFLORAMENTO';
    var optExp = {
            'collection': featCol,
            'description': nameshp,
            'assetId': outAssetROIs+ "/" + nameshp
        }

    Export.table.toAsset(optExp)
    print("exportando ROIs da bacia $s ...!", nameshp)
}

var assetAflor = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/AFLORAMENTO/poligons_manual_aflor';

var biomes = ['CAATINGA','CERRADO','MATAATLANTICA'];
var assetMosaic = 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2';
var assetMapbiomas71= 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1';
var assetMapbiomas8= 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/CLASS/ClassCol8V5';
var asset_aflo = 'users/RrochaGglEngine/MAPBIOMAS/afloramentos_caatinga_col8';
var featAflor = ee.FeatureCollection(asset_aflo);
var polgAflo = ee.FeatureCollection(assetAflor);
print("show the first feat ", featAflor.first());
var histog = featAflor.aggregate_histogram('TIPO_AFLOR');
print("Tipo de afloramento ", histog);
var banda_activa = 'classification_1985';
var list_typeAflo = [
        'Encosta de morro',
        'Lajedo ou Lajeiro',
        // 'Topo de morro',
        // 'Topo de serra',
        // 'Topo de colina'
    ];
var imagens_mosaic = ee.ImageCollection(assetMosaic).filter(
                        ee.Filter.inList('biome', biomes))
                            .select(featuresreduce).mosaic();
var lst_years = [
'1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
'1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
'2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
'2015','2016','2017','2018','2019','2020','2021'
];
var mapsLULC = ee.Image(assetMapbiomas71);
var imgMapCol8V3 =  ee.ImageCollection(assetMapbiomas8).max();
var maskAflora = ee.Image.constant(0);
lst_years.forEach(function(yyear){
var bandAct = 'classification_' + yyear;
var mapyear = mapsLULC.select(bandAct).eq(29);
maskAflora = maskAflora.add(mapyear);
});
maskAflora = maskAflora.gt(0);

Map.addLayer(imagens_mosaic, vis.visMosaic, 'mosaic');
Map.addLayer(mapsLULC.select(banda_activa), vis.mapbiomas, 'map 1985');
Map.addLayer(imgMapCol8V3.select(banda_activa),  vis.mapbiomas, 'Col8_ClassV5' + banda_activa);
Map.addLayer(maskAflora.selfMask(), vis.maskAfloramento, 'afloramento');
Map.addLayer(featAflor.filter(ee.Filter.inList('TIPO_AFLOR',list_typeAflo)), vis.points, 'pontos');
Map.addLayer(polgAflo, {}, 'poligons');
Map.setCenter(-41.029, -5.896, 10);
Map.setOptions("SATELLITE");

// exportando os poligons de afloramento Encosta
var nameExp = "shp_encosta_aflo";
exportSHPAflor(encosta, nameExp);

// exportando os poligons de afloramento Morro
var nameExp = "shp_morro_aflo";
exportSHPAflor(morro, nameExp);

// exportando os poligons de afloramento Lajedo
var nameExp = "shp_lajedo_aflo";
exportSHPAflor(lajedo, nameExp);

// exportando os poligons de afloramento Solo
var nameExp = "shp_solo_Not_aflo";
exportSHPAflor(solo, nameExp);

// exportando os poligons de afloramento Campestre
var nameExp = "shp_campestre_Not_aflo";
exportSHPAflor(campestre, nameExp);

// exportando os poligons de afloramento Encosta Para Predict
var nameExp = "shp_encosta_aflo_Pred";
exportSHPAflor(encostaPred, nameExp);

// exportando os poligons de afloramento Morro Para Predict
var nameExp = "shp_morro_aflo_Pred";
exportSHPAflor(morroPred, nameExp);

// exportando os poligons de afloramento Lajedo Para Predict
var nameExp = "shp_lajedo_aflo_Pred";
exportSHPAflor(lajeadoPred, nameExp);
