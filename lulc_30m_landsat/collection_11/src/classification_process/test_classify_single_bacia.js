// =============================================================
// TEST: Classificação por Bacia — versão simplificada para debug
// Traduzido de classificacao_NotN_newBasin_Float_col10_probVC4.py
// Rode no GEE Code Editor: code.earthengine.google.com
// =============================================================

// ---- PARÂMETROS DE TESTE (altere aqui) ----------------------
var NBACIA  = '751';   // bacia a testar
var NYEAR   = 2020;    // ano a testar
var VERSION = 1;
// -------------------------------------------------------------

var ASSET_BACIAS  = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions';
var ASSET_COLECAO = 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY';
var ASSET_ROIS    = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/ROIs/ROIs_clean_downsamplesCCred';
var ASSET_OUT     = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1';

var BND_L = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2'];

var PMT_GTB = {
  numberOfTrees: 35,
  shrinkage:     0.1,
  samplingRate:  0.65,
  loss:          'LeastSquares',
  seed:          0,
};

var LST_FEAT_SELECT = [
  'green_median_dry',  'green_median_wet',
  'red_median_dry',    'red_median_wet',   'swir1_median_wet',
  'swir2_median_wet',  'swir2_median',     'swir2_median_dry',
  'ndti_median_dry',   'ndti_median_wet',  'ndti_median',
  'gli_median_dry',
  'ndvi_median',       'ndvi_median_dry',  'ndvi_median_wet',
  'ndwi_median_dry',   'ndwi_median',      'ndwi_median_wet',
  'awei_median',       'awei_median_wet',  'awei_median_dry',
];

// =============================================================
// MOSAICO
// =============================================================
function buildMosaic(geometry, nyear) {
  var col = ee.ImageCollection(ASSET_COLECAO)
    .filterBounds(geometry)
    .filter(ee.Filter.date(nyear + '-01-01', nyear + '-12-31'))
    .select(BND_L);

  var bndMedian = BND_L.map(function(b) { return b + '_median';     });
  var bndWet    = BND_L.map(function(b) { return b + '_median_wet'; });
  var bndDry    = BND_L.map(function(b) { return b + '_median_dry'; });

  var mosaicYear = col.max().rename(bndMedian);
  var mosaicWet  = col.filter(ee.Filter.date(nyear + '-01-01', nyear + '-07-31')).max().rename(bndWet);
  var mosaicDry  = col.filter(ee.Filter.date(nyear + '-08-01', nyear + '-12-31')).max().rename(bndDry);

  return ee.Image.cat([mosaicYear, mosaicWet, mosaicDry]).clip(geometry);
}

// =============================================================
// ÍNDICES ESPECTRAIS
// Apenas os índices presentes em LST_FEAT_SELECT:
//   ndti, gli, ndvi, ndwi, awei
// =============================================================
function addIndices(mosaic) {
  var sufixos = ['_median', '_median_wet', '_median_dry'];
  var indices = [];

  sufixos.forEach(function(s) {

    // ndti = (swir1 - swir2) / (swir1 + swir2)
    if (LST_FEAT_SELECT.indexOf('ndti' + s) >= 0) {
      indices.push(
        mosaic.expression(
          'float((swir1 - swir2) / (swir1 + swir2))',
          { swir1: mosaic.select('swir1' + s), swir2: mosaic.select('swir2' + s) }
        ).rename('ndti' + s)
      );
    }

    // ndvi = (nir - red) / (nir + red)
    if (LST_FEAT_SELECT.indexOf('ndvi' + s) >= 0) {
      indices.push(
        mosaic.expression(
          'float((nir - red) / (nir + red))',
          { nir: mosaic.select('nir' + s), red: mosaic.select('red' + s) }
        ).rename('ndvi' + s)
      );
    }

    // ndwi = (nir - swir2) / (nir + swir2)
    if (LST_FEAT_SELECT.indexOf('ndwi' + s) >= 0) {
      indices.push(
        mosaic.expression(
          'float((nir - swir2) / (nir + swir2))',
          { nir: mosaic.select('nir' + s), swir2: mosaic.select('swir2' + s) }
        ).rename('ndwi' + s)
      );
    }

    // gli = (2*green - red - blue) / (2*green + red + blue)
    if (LST_FEAT_SELECT.indexOf('gli' + s) >= 0) {
      indices.push(
        mosaic.expression(
          'float((2*green - red - blue) / (2*green + red + blue))',
          { green: mosaic.select('green' + s), red: mosaic.select('red' + s), blue: mosaic.select('blue' + s) }
        ).rename('gli' + s)
      );
    }

    // awei = 4*(green - swir2) - (0.25*nir + 2.75*swir1)
    if (LST_FEAT_SELECT.indexOf('awei' + s) >= 0) {
      indices.push(
        mosaic.expression(
          'float(4*(green - swir2) - (0.25*nir + 2.75*swir1))',
          {
            green: mosaic.select('green' + s),
            swir2: mosaic.select('swir2' + s),
            nir:   mosaic.select('nir' + s),
            swir1: mosaic.select('swir1' + s),
          }
        ).rename('awei' + s)
      );
    }
  });

  return ee.Image.cat([mosaic].concat(indices));
}

// =============================================================
// PIPELINE PRINCIPAL
// =============================================================
print('=== Classificando bacia ' + NBACIA + ' | ano ' + NYEAR + ' ===');

// 1. Geometria da bacia
var bacias_fc   = ee.FeatureCollection(ASSET_BACIAS).filter(ee.Filter.eq('nunivotto4', NBACIA));
var baciabuffer = bacias_fc.geometry();

// Visualiza a bacia
Map.centerObject(baciabuffer, 8);
Map.addLayer(baciabuffer, {color: 'blue'}, 'Bacia ' + NBACIA);

// 2. Mosaico
var mosaic = buildMosaic(baciabuffer, NYEAR);
print('Bandas do mosaico:', mosaic.bandNames());

// Visualiza RGB do mosaico
Map.addLayer(mosaic, {bands: ['red_median', 'green_median', 'blue_median'], min: 0, max: 0.3}, 'RGB ' + NYEAR);

// 3. Índices espectrais
var mosaicFull    = addIndices(mosaic);
var mosaicClassif = mosaicFull.select(LST_FEAT_SELECT);
print('Features para classificação:', mosaicClassif.bandNames());

// 4. ROIs
var anoAmostra = NYEAR <= 2024 ? NYEAR : 2024;
var roisPath   = ASSET_ROIS + '/rois_fromBasin_' + NBACIA + '_' + anoAmostra;
var ROIs = ee.FeatureCollection(roisPath);
print('ROIs carregados:', ROIs.size());

// 5. Classificador
var classifier = ee.Classifier.smileGradientTreeBoost(PMT_GTB)
  .train(ROIs, 'class', LST_FEAT_SELECT);

// 6. Classificação
var bandResult = 'classification_' + NYEAR;
var classified = mosaicClassif.classify(classifier, bandResult);

// Visualização do resultado
var palette = ['#1f8d49','#FFFFB2','#d4271e','#0000FF','#edde8e','#C27BA0','#f5b3be','#db7239'];
Map.addLayer(classified, {min: 3, max: 33, palette: palette}, 'Classificação ' + NYEAR);
print('Classificação OK — banda:', bandResult);

// =============================================================
// EXPORT (descomente para exportar)
// =============================================================
/*
classified = classified.set({
  id_bacia:   NBACIA,
  version:    VERSION,
  biome:      'CAATINGA',
  classifier: 'GTB',
  collection: '11.0',
  sensor:     'Landsat',
  year:       NYEAR,
  bands:      'fm',
});

var nomeDesc = 'BACIA_' + NBACIA + '_' + NYEAR + '_GTB_col11_BND_fm-v_' + VERSION;
Export.image.toAsset({
  image:           classified,
  description:     nomeDesc,
  assetId:         ASSET_OUT + '/' + nomeDesc,
  region:          baciabuffer,
  scale:           30,
  maxPixels:       1e13,
  pyramidingPolicy: {'.default': 'mode'},
});
*/
