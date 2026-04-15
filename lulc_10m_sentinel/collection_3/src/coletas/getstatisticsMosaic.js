var vis = {
    mosaic: {
            bands: ['swir1_median', 'nir_median', 'red_median'],
            gain: [0.08, 0.06, 0.2],
            gamma: 0.85
    },
};
var lst_bnd = [    
    'blue_median', 'blue_median_wet', 'blue_median_dry', 'blue_stdDev', 
    'green_median', 'green_median_dry', 'green_median_wet', 
    'green_median_texture', 'green_min', 'green_stdDev', 
    'red_median', 'red_median_dry', 'red_min', 'red_median_wet', 
    'red_stdDev', 'nir_median', 'nir_median_dry', 'nir_median_wet', 
    'nir_stdDev', 'red_edge_1_median', 'red_edge_1_median_dry', 
    'red_edge_1_median_wet', 'red_edge_1_stdDev', 'red_edge_2_median', 
    'red_edge_2_median_dry', 'red_edge_2_median_wet', 'red_edge_2_stdDev', 
    'red_edge_3_median', 'red_edge_3_median_dry', 'red_edge_3_median_wet', 
    'red_edge_3_stdDev', 'red_edge_4_median', 'red_edge_4_median_dry', 
    'red_edge_4_median_wet', 'red_edge_4_stdDev', 'swir1_median', 
    'swir1_median_dry', 'swir1_median_wet', 'swir1_stdDev', 'swir2_median', 
    'swir2_median_wet', 'swir2_median_dry', 'swir2_stdDev'
];
//exporta a imagem classificada para o asset
function processoExportar(areaFeat, nameT){      
        var optExp = {
              'collection': ee.FeatureCollection(areaFeat), 
              'description': nameT, 
              'assetId': params.asset_output      
            };    
        Export.table.toAsset(optExp) ;
        print(" salvando ... " + nameT + "..!")      ;
    }

function get_stats_min(img, geomet){
    // Add reducer output to the Features in the collection.
    var pmtoRed = {
        reducer: ee.Reducer.min(),
        geometry: geomet,
        scale: 30,
        maxPixels: 1e13
    }
    var statMin = img.reduceRegion(pmtoRed);
    print('viewer stats Minimum', statMin)
    return statMin;
}
function get_stats_max(img, geomet){
    // Add reducer output to the Features in the collection.
    var pmtoRed = {
        reducer: ee.Reducer.max(),
        geometry: geomet,
        scale: 30,
        maxPixels: 1e13
    }
    var statMax = img.reduceRegion(pmtoRed);
    print('viewer stats Maximum ', statMax)
    return statMax;
}
var get_stats_mean = function(img, geomet){
    // Add reducer output to the Features in the collection.
    var pmtoRed = {
        reducer: ee.Reducer.mean(),
        geometry: geomet,
        scale: 30,
        maxPixels: 1e13
    }
    var statMean = img.reduceRegion(pmtoRed);
    print('viewer stats ', statMean)
    return statMean;
}
var get_stats_standardDeviations = function(img, geomet){
    // Add reducer output to the Features in the collection.
    var pmtoRed = {
        reducer: ee.Reducer.stdDev(),
        geometry: geomet,
        scale: 30,
        maxPixels: 1e13
    }
    var statstdDev = img.reduceRegion(pmtoRed);
    print('viewer stats Desvio padrão ', statstdDev)
    return statstdDev;
}

var params = {
    'asset_mosaic_sentinel': 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
    'assetrecorteCaatCerrMA' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    'asset_bacias_buffer' : 'users/gee_arcplan/regs_mb_pantanal',
    'asset_output': 'projects/mapbiomas-workspace/AMOSTRAS/col9/PANTANAL', // sugiro criar o folder para as statisticas
    'biomes': ['CAATINGA','CERRADO','MATAATLANTICA']
};
var years = [2016,2017,2018,2019,2020,2021,2022,2023];  
var regions = ['reg6']; //'reg1','reg2','reg3','reg4','reg5',
var limitBiome = ee.FeatureCollection(params.asset_bacias_buffer);
var collection = ee.ImageCollection(params.asset_mosaic_sentinel)

print(" viewer collections ", collection.size());
print("show the first ", collection.first());
var regtmp, dict_stat, nameexp,rasterMosaic ;
var bndmean, bndstdDev, bnd;
regions.forEach(function(reg){
    regtmp = limitBiome.filter(ee.Filter.eq('id_reg', reg))
    print("loading region >> "+ reg, regtmp.size())
    regtmp = regtmp.geometry();
    var featColStats = ee.FeatureCollection([]);
    years.forEach(function(nyear){
        rasterMosaic = collection.filterBounds(regtmp).filter(ee.Filter.eq('year', nyear)).mosaic();
        dict_stat = ee.Dictionary({})
        dict_stat = dict_stat.set('id_reg', reg);
        dict_stat = dict_stat.set('year', nyear);
        var dict_Mean = get_stats_mean(rasterMosaic, regtmp);
        var dict_Std = get_stats_standardDeviations(rasterMosaic, regtmp);
        var dict_Min = get_stats_min(rasterMosaic, regtmp);
        var dict_Max = get_stats_max(rasterMosaic, regtmp);

        lst_bnd.forEach(function(bnd){
            dict_stat = dict_stat.set(bnd + '_mean', dict_Mean.get(bnd));
            dict_stat = dict_stat.set(bnd + '_stdDev', dict_Std.get(bnd));
            dict_stat = dict_stat.set(bnd + '_min', dict_Min.get(bnd));
            dict_stat = dict_stat.set(bnd + '_max', dict_Max.get(bnd));
        })        
        print("dict year ", dict_stat);
        var featStats = ee.Feature(regtmp.centroid(), dict_stat);
        featColStats = featColStats.merge(featStats);
    })
    nameexp = 'stats_mosaicS2_reg_' + reg;
    processoExportar(featColStats, nameexp);
})

Map.addLayer(limitBiome, {color: 'green'}, 'Bacias biome');
Map.addLayer(collection, vis.mosaic, 'mosaic');







