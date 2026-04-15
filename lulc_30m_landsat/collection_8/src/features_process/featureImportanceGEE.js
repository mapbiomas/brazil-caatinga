// https://code.earthengine.google.com/6519a5c231470952084bc47ed36f58c2
///=================================================///
// SCRIPT DE COLETA DE FEATURE IMPORTANCE POR BACIA
// Produzido por Geodatin - Dados e Geoinformacao
// DISTRIBUIDO COM GPLv2
///=================================================///
var param = {    
    'assetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv4N4/',
    'anoInicial': 1985,
    'anoFinal': 2022,
    'numeroTask': 6,
    'numeroLimit': 4,
    'conta' : {
        '0': 'caatinga04'              
    },
    'pmtGTB': {
        'numberOfTrees': 72, 
        'shrinkage': 0.005, 
        'samplingRate': 0.8, 
        'loss': 'Huber', //'LeastAbsoluteDeviation', 
        'seed': 0
    },
    'pmtRF': {
        'numberOfTrees': 265, 
        'variablesPerSplit': 25,
        'minLeafPopulation': 40,
        'bagFraction': 0.8,
        'seed': 0
    },
};

//lista de anos
var list_anos = [];
for(var yyear = param.anoInicial; yyear < param.anoFinal + 1; yyear++){
    list_anos.push(yyear);
}
print('lista de anos', list_anos);

// nome das bacias que fazem parte do bioma (42 bacias)
var nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
];

var bandas_imports = [
    'rvi_median', 'cvi_median_dry', 'shape_median_wet', 
    'ratio_median',  'swir1_stdDev', 'gcvi_median_wet', 
    'swir2_median',  'ndwi_median', 'blue_min', 'avi_median_wet', 
    'cvi_median',  'lswi_median_wet', 'afvi_median_wet', 'iia_median', 
    'gemi_median_wet', 'ratio_median_wet', 'afvi_median', 'swir2_median_dry', 
    'mbi_median_wet', 'lswi_median_dry', 'nir_median', 'shape_median_dry', 
    'mbi_median_dry', 'nir_median_wet', 'green_median_wet', 'avi_median', 
    'blue_median',  'brightness_median', 'nir_stdDev', 'nir_min', 
    'swir2_median_wet', 'swir2_stdDev', 'swir2_min', 'brightness_median_wet', 
    'ndwi_median_wet', 'green_median', 'swir1_median_dry', 'gemi_median',  
    'osavi_median_dry', 'gcvi_median_dry', 'dswi5_median_wet', 'ndwi_median_dry', 
    'awei_median_wet', 'ratio_median_dry', 'gcvi_median', 'brba_median', 
    'ri_median_wet', 'rvi_median_wet', 'brba_median_dry', 'red_median_dry', 
    'green_stdDev', 'iia_median_wet', 'green_min', 'ui_median_dry', 
    'ui_median', 'wetness_median_dry', 'gli_median_dry', 'red_median_wet', 
    'dswi5_median', 'ri_median',  'mbi_median', 'red_min', 'green_median_texture', 
    'osavi_median_wet', 'wetness_median_wet', 'ui_median_wet', 'wetness_median', 
    'avi_median_dry', 'dswi5_median_dry', 'bsi_median', 'awei_median_dry', 
    'swir1_median_wet', 'gli_median_wet', 'gli_median', 'lswi_median', 
    'nir_median_dry','swir1_min', 'gemi_median_dry', 'red_median',  
    'shape_median'
];

var process_classification=  function (nameROis){
    var featRois = ee.FeatureCollection(param['assetROIs'] + nameROis);
    print("Laoding featCol with  features", featRois.size());
    print(featRois.first().propertyNames());
    var classifierGTB = ee.Classifier.smileGradientTreeBoost(param.pmtGTB)
                                    .train(featRois, 'class', bandas_imports);

    // # classifierRF = ee.Classifier.smileRandomForest(param['pmtRF'])
    // #                                 .train(featRois, 'class', lstBND)
    print('show befoire ' );
    var explainClass = classifierGTB.explain();
    // explainClass = classifierRF.explain()
    var dictImp = ee.Dictionary(explainClass).get("importance");
    // print('show ', dictImp);
    return dictImp;
};

var exportListFeatureImport= function(featCol, nameExp){
    var asset_exp = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/featureImp/' + nameExp;
    var paramExp = {
        collection: featCol, 
        description: nameExp, 
        assetId: asset_exp
    };
    
    Export.table.toAsset(paramExp);
};
var ponto = [-37.104, -7.33];

nameBacias.forEach(function(_nbacia){  //.slice(0,4)
    var dictImp = ee.FeatureCollection([]);
    print("loading bacia " + _nbacia);     
    list_anos.forEach(function(yyear){  //slice(0,2).
        var nameFeat = _nbacia + '_' + yyear.toString() + '_c1';
        print("loading FeatureCollection => ", nameFeat);
        var lstVar = process_classification(nameFeat);         
        
        var feattmp = ee.Feature(ee.Geometry.Point(ponto), {nameFeat: lstVar});
        dictImp = dictImp.merge(ee.FeatureCollection([feattmp]));
    });
    print(dictImp);
    var expFeat = "baciaV4_" + _nbacia;
    exportListFeatureImport(dictImp, expFeat);
});