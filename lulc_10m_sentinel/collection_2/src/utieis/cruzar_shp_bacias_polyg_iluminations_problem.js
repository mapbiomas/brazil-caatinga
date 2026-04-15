var asset_ilumination = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/regions_iluminations_problems';
var asset_bacias_buffer = 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions'

var featIlum = ee.FeatureCollection(asset_ilumination);
print(featIlum)
var shpBaciabuf = ee.FeatureCollection(asset_bacias_buffer);
var lstIds = ['00000000000000000000', '00000000000000000001', '00000000000000000002',
              '00000000000000000003'];
              
              
lstIds.forEach(function(idf){
        var feattmp = featIlum.filter(ee.Filter.eq('system:index', idf));
        print(idf, feattmp);
        var regBaf = shpBaciabuf.filterBounds(feattmp);
        var lstIds = regBaf.reduceColumns(ee.Reducer.toList(), ['nunivotto4']).get('list');
        print(lstIds);
})

var dictRegIlBacia = {
    '00000000000000000000': {
        'id_bacia': ["7712","7721"],
        'year': 2021,
        'class_from': 21,
        'class_to': 4
    },
    '00000000000000000001': {
        'id_bacia': ["7561","757","7581","7584","7591","7592"],
        'year': 2016,
        'class_from': 4,
        'class_to': 21
    },
    '00000000000000000002': {
        'id_bacia': ["7584","761111","76116","7612"],
        'year': 2016,
        'class_from': 21,
        'class_to': 4
    },
    '00000000000000000003': {
        'id_bacia': ["7422","752"],
        'year': 2019,
        'class_from': 4,
        'class_to': 21
    }
}

var dict_BaciaId = {
    "7712": ['00000000000000000000'],
    "7721": ['00000000000000000000'], 
    "7561": ['00000000000000000001'],
    "757": ['00000000000000000001'],
    "7581": ['00000000000000000001'],
    "7584": ['00000000000000000001','00000000000000000002'],
    "7591": ['00000000000000000001'],
    "7592": ['00000000000000000001'],
    "76116": ['00000000000000000002'],
    "7612": ['00000000000000000002'],
    "761111": ['00000000000000000002'],
    "7422": ['00000000000000000003'],
    "752": ['00000000000000000003']
}