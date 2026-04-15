// --- CONFIGURAÇÃO E ASSETS ---
var palettes = require('users/mapbiomas/modules:Palettes.js');
var vis = {
    mosaico: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },
    vismosaicoGEE: {
        'min': 0.001, 'max': 0.15,
        bands: ['red', 'green', 'blue']
    },
    map_class: {
        min: 0,
        max: 69,
        palette: palettes.get('classification9')
    }
};

var param = {
    // CAMINHOS BASE (A lógica de versão será aplicada sobre o sentinel)
    // ATENÇÃO: Ajuste a string base conforme sua estrutura de pastas real
    asset_map_sentinel_base: 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
    asset_map_landsat: 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',    
    // Assets auxiliares
    asset_bacias: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    asset_biomas_raster: 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41', 
    asset_mosaic_sentinelp2: 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',
    asset_mosaic_sentinelp1: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
    asset_collectionId: 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',    
    // Anos disponíveis
    nyears: [ '2016','2017','2018','2019','2020','2021','2022','2023','2024','2025' ],
    bands_show: ['red_median', 'green_median', 'blue_median']
};
var versions = ['1','2','3','4'];
var regions = ee.FeatureCollection(param.asset_bacias).map(function(feat){return feat.set('idCod', 1)});
var mask_region = regions.reduceToImage(['idCod'], ee.Reducer.first());
var asset_cobert_extra = 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined';
Map.addLayer(regions, {color: 'green'}, 'bacias', false);
var maptmp , asset_map;                    


param.nyears.forEach(function(yyear){
    var bnd_map = 'classification_' + yyear;
    print("Showing map >> " + yyear);
    var asset_mosaic_s2 = param.asset_mosaic_sentinelp1;
    if (yyear > 2023){
        asset_mosaic_s2 = param.asset_mosaic_sentinelp2;
    }
    var mosaicoS2 = ee.ImageCollection(asset_mosaic_s2)
                        .filter(ee.Filter.eq('year', parseInt(yyear)))
                        .mosaic()
                        .select(param.bands_show)
                        .updateMask(mask_region);
                        
    print("reading year " + yyear, mosaicoS2);
    Map.addLayer(mosaicoS2, vis.mosaico, 'mosaic_' + yyear, false);

    versions.forEach(function(version){
        if ((version == '1') || (version == '2')){
            asset_map = param.asset_map_sentinel_base;
        }else{
            asset_map = asset_cobert_extra;
        }
        var maptmp = ee.ImageCollection(asset_map)
                            .filter(ee.Filter.eq('version', parseInt(version)))
                            .mosaic().select(bnd_map);
        print("show metadado ", map);

        Map.addLayer(maptmp, vis.map_class, 'map_' + yyear + '_v' + version, false);
    })    
    
})


