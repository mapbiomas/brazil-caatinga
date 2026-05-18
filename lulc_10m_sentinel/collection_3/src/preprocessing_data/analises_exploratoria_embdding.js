
var vis = {
    embedding: {
        // bands: ["A00","A01","A02"],
        // bands: ['A01', 'A16', 'A09']
        bands: ['A01', 'A25', 'A50'],
        min: {
            2017: -0.2679,
            2018: -0.2679,
            2019: -0.2679,
            2020: -0.2761,
            2021: -0.2844,
            2022: -0.2761,
            2023: -0.2761,
            2024: -0.2679,
        },
        max: {
            2017: 0.31,
            2018: 0.2679,
            2019: 0.3188,
            2020: 0.2844,
            2021: 0.2679,
            2022: 0.2844,
            2023: 0.2679,
            2024: 0.2761
        },
      
    },
};
var asset_caat = 'users/CartasSol/shapes/nCaatingaBff3500';
var asset_emb = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL";
// var date_inic = ee.Date.fromYMD(2016, 2, 1); 

var limitCaat =  ee.FeatureCollection(asset_caat).map(function(feat){return feat.set('id_cod', 1)});
var mask_caat = limitCaat.reduceToImage(['id_cod'], ee.Reducer.first());
var imgCemb = ee.ImageCollection(asset_emb)
                    .filterBounds(limitCaat)
                    .sort('system:time_start')
                    
                    
print("show metadados ", imgCemb);
var lstDate = imgCemb.reduceColumns(
                  ee.Reducer.toList(2), 
                  ['system:time_start', 'system:time_end']
              ).get('list');
// get lista of par date distinct               
lstDate = ee.List(lstDate).distinct();
lstDate.evaluate(function(lista_date){
    lista_date.forEach(function(date_par){
        var time_start = ee.Date(date_par[0]);
        var time_end = ee.Date(date_par[1]);
        print(time_start, time_end)
        var mosaic_year = ee.Image(imgCemb
                                    .filterDate(time_start, time_end)
                                    .mosaic()
                                );
        Map.addLayer(mosaic_year, vis.embedding, String(time_start.get('year').getInfo()));
    })
})
