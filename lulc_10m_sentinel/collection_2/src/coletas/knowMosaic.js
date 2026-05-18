var vis= {
    mosaico: {
        min: 20, max: 2500,
        bands: ["red_median","green_median","blue_median"]
    }
}
var lstYears = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023];
var lstBiomas = ['CAATINGA','CERRADO','MATAATLANTICA'];  //
var asset_mosaic = 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3';
var imgC = ee.ImageCollection(asset_mosaic).filter(ee.Filter.inList('biome', lstBiomas));


print("know número de imagens por ano ", imgC.aggregate_histogram('year'));
print("show metadata ", imgC.limit(10));
print("Know how many image the asset have ", imgC.size());
var showMosaic = false;
lstYears.forEach(function(nyear){
    var imgCYY = imgC.filter(ee.Filter.eq('year', nyear));
    if (nyear === 2023){
        showMosaic = true;
    }
    Map.addLayer(imgCYY, vis.mosaico, 'mosaic-' + String(nyear), showMosaic);
})


