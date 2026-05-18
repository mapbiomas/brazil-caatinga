var vis = {
    mosaico: {
        bands: ["swir1_median","nir_median","red_median"],
        gamma: 1,
        max: 4119,
        min: 51
    }
};
var lst_biome = ['CAATINGA','CERRADO','MATAATLANTICA'];
var asset = 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3';
var c = ee.ImageCollection(asset).filter(ee.Filter.inList('biome', lst_biome));
print("size image collection ", c.size());
print("limit ", c.limit(3));
print("show list de biomes", c.aggregate_histogram('biome'));
var lst_year = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];

lst_year.forEach(function(nyear){
    var coletion_yy = c.filter(ee.Filter.eq('year', nyear));
    Map.addLayer(coletion_yy, vis.mosaico, String(nyear));
})
