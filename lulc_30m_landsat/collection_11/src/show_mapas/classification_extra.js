var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette  = palettes.get('brazil');
var vis = {
    mosaico: {'bands':['R','G','B'],'min':64,'max':5454,'gamma':1.8},
    ind_ndvi: {min:-0.55,max:0.8, palette: ['8bc4f9', 'c9995c', 'c7d270','8add60','097210']},
    mapbiomas_s2: { min: 0, max: 75, palette: palette, format: 'png' },
    nova_class: {min: 1, max: 6, palette:['1e28d6','ffd0b7','d3d245','228718','5bff5c']}
};

// =============================================================
// ÍNDICES ESPECTRAIS — Planet NICFI (bandas: R, G, B, N)
// ndti e awei NÃO calculados: requerem SWIR, indisponível no Planet
// =============================================================
function addIndices(mosaic) {
    var R = mosaic.select('R');
    var G = mosaic.select('G');
    var B = mosaic.select('B');
    var N = mosaic.select('N');

    // ndvi = (N - R) / (N + R)
    var ndvi = N.subtract(R).divide(N.add(R))
                .rename('ndvi');

    // gli = (2*G - R - B) / (2*G + R + B)
    var gli = G.multiply(2).subtract(R).subtract(B)
               .divide(G.multiply(2).add(R).add(B))
               .rename('gli');

    // ndwi = (G - N) / (G + N)
    var ndwi = G.subtract(N).divide(G.add(N))
                .rename('ndwi');

    // gcvi = (N / G) - 1
    var gcvi = N.divide(G).subtract(1)
                .rename('gcvi');

    // evi = 2.4 * (N - R) / (N + R + 1)
    var evi = N.subtract(R).multiply(2.4)
               .divide(N.add(R).add(1))
               .rename('evi');

    // gndvi = (N - G) / (N + G)
    var gndvi = N.subtract(G).divide(N.add(G))
                 .rename('gndvi');

    return mosaic.addBands([ndvi, gli, ndwi, gcvi, evi, gndvi]);
}

// =============================================================
// EXPORT DO MOSAICO CLASSIFICADO
// =============================================================
function exportClassified(img, region, region_name, year, id_asset_ouput) {
    var desc = 'classified_planet_' + region_name + '_' + year;
    Export.image.toAsset({
        image:       img.toByte(),
        description: desc,
        assetId:     id_asset_ouput + '/' + desc,
        region:      region,
        scale:        4.77,
        maxPixels:    1e13,
        pyramidingPolicy: { '.default': 'mode' }   // modo para imagem categórica
    });
    print('Export agendado:', desc);
}

// This collection is not publicly accessible. To sign up for access,
// please see https://developers.planet.com/docs/integrations/gee/nicfi
var asset_nicfi = 'projects/planet-nicfi/assets/basemaps/americas';
var input_asset_S2 = 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export'  
////// Vieira 
var asset_output = "projects/project-502fb1ce-2af9-4f8f-a37/assets";
var asset_reg_viera = "projects/project-502fb1ce-2af9-4f8f-a37/assets/G_Vieira";
var asset_reg_morrao = "projects/project-502fb1ce-2af9-4f8f-a37/assets/g_morrao";
var year_courrent = 2024;
var date_inic = ee.Date.fromYMD(year_courrent, 3, 1);
var region_act = 'morrao' // 'viera'
var shp_area_est = ee.FeatureCollection(asset_reg_viera);
if (region_act == 'morrao'){
    shp_area_est = ee.FeatureCollection(asset_reg_morrao);
}
var area_ampliada = shp_area_est.geometry().buffer(1500).bounds();
var col_sent = ee.ImageCollection(input_asset_S2)
                  .filter(ee.Filter.eq('version', 7)).max()
                  .select('classification_' + String(year_courrent))
                  .clip(area_ampliada);

print("show metadado Sentinel ", col_sent);
var mosaico = ee.ImageCollection(asset_nicfi)
                  .filter(ee.Filter.date(date_inic, date_inic.advance(3, 'month')))
                  .mosaic()
                  .clip(area_ampliada);

var raster_indexs  = addIndices(mosaico);
var bandas_imports = raster_indexs.bandNames();
print('Bandas no mosaico + índices:', bandas_imports);

// ── visualização ──────────────────────────────────────────────────────────────
Map.addLayer(mosaico,                         vis.mosaico,      'planet ' + String(year_courrent));
Map.addLayer(raster_indexs.select('ndvi'),    vis.ind_ndvi,     'NDVI',    false);
Map.addLayer(raster_indexs.select('gli'),     vis.ind_ndvi,     'GLI',     false);
Map.addLayer(raster_indexs.select('ndwi'),    vis.ind_ndvi,     'NDWI',    false);
Map.addLayer(col_sent, vis.mapbiomas_s2, 'col S2 ');

// ── export do mosaico Planet + índices para asset ─────────────────────────────
Export.image.toAsset({
    image:       raster_indexs.toFloat(),
    description: 'planet_nicfi_indices_' + region_act + '_' + year_courrent,
    assetId:     asset_output + '/planet_nicfi_indices_' + region_act + '_' + year_courrent,
    region:      area_ampliada,
    scale:        4.77,   // resolução nativa Planet NICFI
    maxPixels:    1e13,
    pyramidingPolicy: { '.default': 'mean' }
});
// Paint all the polygon edges with the same number and width, display.
var outline = ee.Image().byte().paint(shp_area_est, 1, 2);
Map.addLayer(outline, {palette: 'FF0000'}, 'ROI ' + region_act);
Map.centerObject(shp_area_est, 15);

/// parte do classificador 
var samples_rois = agua.merge(solo).merge(pastagem).merge(floresta).merge(savana)

var samples_ROIsInfo = raster_indexs.sampleRegions({
        collection: samples_rois,
        properties: ['class'],   // deve ser array
        scale:      4,
        tileScale:  8
})

var pmtGTB = {
    'numberOfTrees': 30, 
    'shrinkage': 0.1,         
    'samplingRate': 0.65, 
    'loss': "LeastSquares",
    'seed': 0
}

var classifierGTB = ee.Classifier.smileGradientTreeBoost(pmtGTB).train(
                                                    samples_ROIsInfo, 'class', bandas_imports)              
var classifiedGTB = raster_indexs.classify(classifierGTB);
Map.addLayer(classifiedGTB, vis.nova_class, 'mosaico Class', false);

exportClassified(classifiedGTB, area_ampliada, region_act, year_courrent, asset_output);