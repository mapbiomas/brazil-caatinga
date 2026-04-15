// https://code.earthengine.google.com/2202ea423200aad7d6b60743100d9727
var param = {
    asset_bacias: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    asset_mosaic_mapbiomas: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
    asset_new_mosaic: 'projects/nexgenmap/MapBiomas2/LANDSAT/mosaics-normalized'
}

var limit_bacias = ee.FeatureCollection(param.asset_bacias);
var yearCurrent = 1987;
var imgColJ = ee.ImageCollection(param.asset_mosaic_mapbiomas)
                            .filter(ee.Filter.eq('biome', 'CAATINGA'))
                            .filter(ee.Filter.eq('year', yearCurrent));

var imgCol = ee.ImageCollection(param.asset_new_mosaic).filter(
                              ee.Filter.eq('year', yearCurrent));
print(imgCol);
var imgCol_wet = imgCol.filter(ee.Filter.eq('periode',  'wet'))  ;
var imgCol_dry = imgCol.filter(ee.Filter.eq('periode',  'dry'));



var vis = {
    pmtoWet : {
        min:0, max: 7500, 
        bands:["red_wet","green_wet","blue_wet"]
    },
    pmtoDry : {
         min:0, max: 7500, 
         bands:["red_dry","green_dry","blue_dry"]
    },
    pmtoJWet : {
        min:30, max: 3500, 
        bands:["red_median_wet","green_median_wet","blue_median_wet"]
    },
    pmtoJDry : {
        min:30, max: 3500, 
        bands:["red_median_dry","green_median_dry","blue_median_dry"]
    }
};

Map.addLayer(imgColJ, vis.pmtoJWet, 'imgCJWet', false);   
Map.addLayer(imgColJ, vis.pmtoJDry, 'imgCJDry', false) ;
Map.addLayer(imgCol_wet, vis.pmtoWet, 'imgCWet');
Map.addLayer(imgCol_dry, vis.pmtoDry, 'imgCDry');
Map.addLayer(limit_bacias, {color: 'green'}, 'regiaos');


