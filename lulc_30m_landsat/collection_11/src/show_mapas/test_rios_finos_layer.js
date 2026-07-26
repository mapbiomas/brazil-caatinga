// ─────────────────────────────────────────────────────────────────────────────
// Visualização — Camada Rios Finos (preview inline + asset salvo)
// Sem widgets. Edite os parâmetros abaixo e rode no GEE Code Editor.
// ─────────────────────────────────────────────────────────────────────────────
// https://code.earthengine.google.com/d5c2df1c47f2967f87904da125c5bba4

// ═══ PARÂMETROS ══════════════════════════════════════════════════════════════
var BACIA           = '7741';
// anos para preview inline
var ANOS            = [ 
        1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 
        1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 
        2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 
        2021, 2022, 2023, 2024
];
var VERSION_CLASS   = 4;   // EstabilidadeCols
var VERSION_RIOS    = 1;   // layer_rios_finos (asset salvo)

// Parâmetros do algoritmo (devem espelhar filtersRiosFinos_layer.py)
var ERODE_RADIUS  = 2;   // kernel 5×5
var DILATE_RADIUS = 4;   // kernel 9×9
var MIN_CONNECTED = 15;

// Mostrar camadas do asset já exportado?
var SHOW_SAVED_ASSET = false;

var ASSET_CLASS  = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/EstabilidadeCols';
var ASSET_RIOS   = 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/layer_rios_finos';
var ASSET_BACIAS = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions';
// ═════════════════════════════════════════════════════════════════════════════

var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette  = palettes.get('brazil');
var visClass = { min: 0, max: 75, palette: palette };

// ─── Geometria da bacia ───────────────────────────────────────────────────────
var bacia_fc = ee.FeatureCollection(ASSET_BACIAS)
    .filter(ee.Filter.eq('nunivotto4', BACIA));
var geom = bacia_fc.geometry();
Map.centerObject(geom, 10);
Map.addLayer(ee.Image().byte().paint(bacia_fc, 1, 2),
             { palette: ['#ff6600'] }, 'Limite bacia ' + BACIA, true);

// ─── Carregar classificação ───────────────────────────────────────────────────
var img_class = ee.ImageCollection(ASSET_CLASS)
    .filter(ee.Filter.eq('id_bacia', BACIA))
    .filter(ee.Filter.eq('version',  VERSION_CLASS))
    .first();

// ─── Camadas anuais de classificação (desligadas por padrão) ─────────────────
ANOS.forEach(function(ano) {
    var band  = 'classification_' + ano;
    var layer = img_class.select(band).updateMask(img_class.select(band).gt(0));
    Map.addLayer(layer, visClass, 'Class ' + ano, false);
});

// ─── Algoritmo inline ─────────────────────────────────────────────────────────
// Para cada ano de ANOS: erode 5×5, dilate 9×9, diferença, filtro conectividade
// União dos anos → máscara de rios finos para preview
var thin_bands = ANOS.map(function(ano) {
    var classif  = img_class.select('classification_' + ano);
    var is_water = classif.eq(33);

    // Abertura assimétrica: erode 5×5 → dilate 9×9
    // Corpos largos: núcleo sobrevive erosão e dilate cobre toda a área original
    // Rios finos: somem na erosão → dilated=0 → aparecem na diferença
    var eroded  = is_water.focal_min(ERODE_RADIUS, 'square', 'pixels');
    var dilated = eroded.focal_max(DILATE_RADIUS, 'square', 'pixels');

    // Diferença: era água mas não coberto pela re-expansão
    var thin_raw = is_water.and(dilated.not());

    // Conectividade: apenas patches > MIN_CONNECTED px conectados
    return thin_raw.and(
        thin_raw.connectedPixelCount(MIN_CONNECTED + 1, true).gt(MIN_CONNECTED)
    );
});

var rios_preview = ee.Image.cat(thin_bands).reduce(ee.Reducer.max()).rename('rios_finos');

// ─── Camadas de preview ───────────────────────────────────────────────────────
var ultimo_ano = ANOS[ANOS.length - 1];
var base_class = img_class
    .select('classification_' + ultimo_ano)
    .updateMask(img_class.select('classification_' + ultimo_ano).gt(0));

// 1. Máscara binária dos rios finos detectados (ciano)
Map.addLayer(
    rios_preview.selfMask(),
    { palette: ['#c925ff'], min: 1, max: 1 },
    '[PREVIEW] Rios Finos (união ' + ANOS.length + ' anos)',
    true
);

// 2. Classificação do último ano com rios finos sobrepostos como classe 33
var com_rios_preview = base_class.where(rios_preview, ee.Image.constant(33));
Map.addLayer(
    com_rios_preview,
    visClass,
    '[PREVIEW] Class ' + ultimo_ano + ' + Rios Finos',
    true
);

// 3. Rios finos PERDIDOS no último ano (classificação ≠ 33 mas foi detectado)
var agua_classif = base_class.eq(33);
Map.addLayer(
    rios_preview.and(agua_classif.not()).selfMask(),
    { palette: ['#ff0000'], min: 1, max: 1 },
    '[PREVIEW] Rio fino PERDIDO em ' + ultimo_ano,
    false
);

// 4. Rios finos CORRETOS no último ano (classificação == 33 e detectado)
Map.addLayer(
    rios_preview.and(agua_classif).selfMask(),
    { palette: ['#c925ff'], min: 1, max: 1 },
    '[PREVIEW] Rio fino CORRETO em ' + ultimo_ano,
    false
);

// 5. Intermediário — thin_raw sem filtro de conectividade (último ano)
//    Útil para ver o que o filtro connectedPixelCount está removendo
var is_water_last = img_class.select('classification_' + ultimo_ano).eq(33);
var eroded_last   = is_water_last.focal_min(ERODE_RADIUS, 'square', 'pixels');
var dilated_last  = eroded_last.focal_max(DILATE_RADIUS, 'square', 'pixels');
var thin_raw_last = is_water_last.and(dilated_last.not());
Map.addLayer(
    thin_raw_last.selfMask(),
    { palette: ['#ffff00'], min: 1, max: 1 },
    '[DEBUG] Thin raw ' + ultimo_ano + ' (sem filtro connect.)',
    false
);

// ─── Asset salvo (apenas se SHOW_SAVED_ASSET = true) ─────────────────────────
if (SHOW_SAVED_ASSET) {
    var img_rios = ee.ImageCollection(ASSET_RIOS)
        .filter(ee.Filter.eq('id_bacia', BACIA))
        .filter(ee.Filter.eq('version',  VERSION_RIOS))
        .first();

    Map.addLayer(
        img_rios.select('rios_finos').selfMask(),
        { palette: ['#0000ff'], min: 1, max: 1 },
        '[ASSET] Rios Finos v' + VERSION_RIOS + ' (exportado)',
        true
    );

    print('═══ Asset salvo — Bacia ' + BACIA + ' ═══');
    print('Anos estáveis:', img_rios.get('anos_estaveis'));
    print('Nº anos estáveis:', img_rios.get('n_anos_estaveis'));
    print('Threshold água (ha):', img_rios.get('threshold_agua_ha'));
    print('Erode radius:', img_rios.get('erode_radius'));
    print('Dilate radius:', img_rios.get('dilate_radius'));
    print('Min connected px:', img_rios.get('min_connected'));
}

// ─── Info no console ──────────────────────────────────────────────────────────
print('═══ Rios Finos PREVIEW — Bacia ' + BACIA + ' ═══');
print('Anos usados:', ANOS);
print('erode=' + ERODE_RADIUS + ' (5×5)  dilate=' + DILATE_RADIUS + ' (9×9)  min_connected=' + MIN_CONNECTED);

var area_preview = rios_preview.selfMask()
    .multiply(ee.Image.pixelArea()).divide(1e4)
    .reduceRegion({ reducer: ee.Reducer.sum(), geometry: geom, scale: 30, maxPixels: 1e10 });
print('Área total rios finos preview (ha):', area_preview);
