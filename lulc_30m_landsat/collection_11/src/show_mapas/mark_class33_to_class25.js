/**
 * mark_class33_to_class25.js
 *
 * Visualização para identificar onde a classe 33 deve virar 25.
 * Desenhe polígonos manualmente no mapa e rode salvarGeometrias() no console.
 *
 * Ajuste as variáveis abaixo e execute.
 */

var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette  = palettes.get('brazil');

// ─── AJUSTE AQUI ─────────────────────────────────────────────────────────────
var year_current = 2024;   // ano a visualizar
var version_show = '1';    // versão da classificação col11
// ─────────────────────────────────────────────────────────────────────────────

var param = {
    assetclass:   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
    inputAsset10: 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    assetIm:      'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    assetBacia:   'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    assetOut:     'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/correcoes/mask_class33_to_25',
};

var CLASS_WATER   = 33;
var CLASS_NON_VEG = 25;

// ─── Dados ───────────────────────────────────────────────────────────────────
var banda    = 'classification_' + year_current;
var year_mos = year_current > 2024 ? 2024 : year_current;

var shp_bacias = ee.FeatureCollection(param.assetBacia);

var mosaic_year = ee.ImageCollection(param.assetIm)
    .filter(ee.Filter.eq('biome', 'CAATINGA'))
    .filter(ee.Filter.eq('year', year_mos))
    .select(['red', 'green', 'blue', 'nir', 'swir1', 'swir2'])
    .median();

var col11_img = ee.ImageCollection(param.assetclass)
    .filter(ee.Filter.stringContains('system:index', 'fm-v_' + version_show))
    .select(banda)
    .mosaic();

// Col10 integrada — banda do ano
var col10_img = ee.Image(param.inputAsset10).select(banda);

// Máscara apenas da classe 33
var mask33 = col11_img.eq(CLASS_WATER);

// ─── Camadas ─────────────────────────────────────────────────────────────────
Map.setOptions('SATELLITE');
Map.setCenter(-39.259, -9.092, 7);

Map.addLayer(mosaic_year,
    { min: 0, max: 2000, bands: ['red_median', 'green_median', 'blue_median'] },
    'Mosaico ' + year_current);

Map.addLayer(col11_img,
    { min: 0, max: 75, palette: palette, format: 'png' },
    'Classificação col11 v' + version_show + ' ' + year_current);

Map.addLayer(col10_img,
    { min: 0, max: 75, palette: palette, format: 'png' },
    'Col10 integrada ' + year_current, false);

Map.addLayer(col11_img.updateMask(mask33),
    { min: 33, max: 33, palette: ['FF0000'] },
    'Classe 33 (destaque vermelho)');

Map.addLayer(ee.Image().byte().paint(shp_bacias, 1, 1),
    { palette: ['ffffff'], opacity: 0.6 },
    'Bacias');

// ─── Salvar geometrias desenhadas ─────────────────────────────────────────────
/**
 * Após desenhar os polígonos no mapa (ferramentas nativas do GEE Code Editor),
 * chame esta função no console: salvarGeometrias(geometry)
 *
 * Passe a variável geometry (ou um array de geometrias) criada pelo desenho.
 * Exemplo de uso no console:
 *   salvarGeometrias(geometry)          // geometria única
 *   salvarGeometrias([geometry, geometry2])  // múltiplas
 */
function salvarGeometrias(geoms) {
    var lista = Array.isArray(geoms) ? geoms : [geoms];

    var features = lista.map(function(g, i) {
        return ee.Feature(g, {
            id:             i + 1,
            classe_origem:  CLASS_WATER,
            classe_destino: CLASS_NON_VEG,
            ano_referencia: year_current,
            version:        version_show,
            descricao:      'Troca classe 33 por 25'
        });
    });

    var fc = ee.FeatureCollection(features);
    var assetId = param.assetOut + '_v' + version_show + '_' + year_current;

    Export.table.toAsset({
        collection:  fc,
        description: 'mask_class33_to_25_v' + version_show + '_' + year_current,
        assetId:     assetId,
    });

    print('Task criada — ' + lista.length + ' polígono(s) → ' + assetId);
}

print('Ano: ' + year_current + ' | Versão: ' + version_show);
print('Para salvar: salvarGeometrias(geometry)');

// Expõe para chamada manual no console do GEE Code Editor
exports.salvarGeometrias = salvarGeometrias;
