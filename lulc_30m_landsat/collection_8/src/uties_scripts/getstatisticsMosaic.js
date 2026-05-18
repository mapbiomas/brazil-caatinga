var vis = {
    mosaic: {
            bands: ['swir1_median', 'nir_median', 'red_median'],
            gain: [0.08, 0.06, 0.2],
            gamma: 0.85
    },
};
var lst_bnd = [
        "blue_median","green_median","red_median","nir_median",
        "swir1_median","swir2_median",         
        "blue_median_wet","green_median_wet","red_median_wet",
        "nir_median_wet","swir1_median_wet","swir2_median_wet",
        "blue_median_dry","green_median_dry","red_median_dry",
        "nir_median_dry","swir1_median_dry","swir2_median_dry", 
    ];
var get_stats_mean = function(img, geomet){
    // Add reducer output to the Features in the collection.
    var pmtoRed = {
        reducer: ee.Reducer.mean(),
        geometry: geomet,
        scale: 30,
        maxPixels: 1e9
    }
    var statMean = img.reduceRegion(pmtoRed);
    print('viewer stats ', statMean)
    
}
var get_stats_standardDeviations = function(img, geomet){
    // Add reducer output to the Features in the collection.
    var pmtoRed = {
        reducer: ee.Reducer.stdDev(),
        geometry: geomet,
        scale: 30,
        maxPixels: 1e9
    }
    var statstdDev = img.reduceRegion(pmtoRed);
    print('viewer stats Desvio padrão ', statstdDev)
}

var params = {
    'asset_mosaic_mapbiomas': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    'asset_bacias': 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga',
    'biomes': ['CAATINGA','CERRADO','MATAATLANTICA']
};
var year = 2022;  

var limitCaat = ee.FeatureCollection(params.asset_bacias);
var collection = ee.ImageCollection(params.asset_mosaic_mapbiomas)
                        .filter(ee.Filter.eq('version', '1'))
                        .filter(ee.Filter.eq('year', year))
                        .filterBounds(limitCaat).select(lst_bnd);
print(" viewer collections ", collection.size());
print("show the first ", collection.first());
print(collection.aggregate_histogram('version'));


var lst_ids = collection.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()

lst_ids.slice(2).forEach(function(idim){
    print('processin image ' + idim);
    var imgtmp = collection.filter(ee.Filter.eq('system:index', idim)).first();
    var mgeomet = imgtmp.geometry();
    get_stats_mean(imgtmp, mgeomet);
    get_stats_standardDeviations(imgtmp, mgeomet);
})
Map.addLayer(limitCaat, {color: 'green'}, 'Bacias Caatinga');
Map.addLayer(collection, vis.mosaic, 'mosaic');