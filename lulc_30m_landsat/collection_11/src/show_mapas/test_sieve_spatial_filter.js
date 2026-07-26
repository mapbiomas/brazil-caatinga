// =====================================================================
// Teste do Filtro Espacial Sieve — Pós-Classificação Col11 Caatinga
// Asset entrada: Classify_fromEEMV1joined (version + id_bacias)
// Compara original vs filtrado com controles interativos de parâmetros
// =====================================================================

var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette  = palettes.get('brazil');

// ─── Parâmetros globais do filtro ─────────────────────────────────────────────
var nativeScale       = 30;      // resolução Landsat (m)
var max_filter_pixels = 25;      // tamanho mínimo de fragmento (pixels)
var kernel_size       = 9;       // kernel da moda (pixels, valor ímpar)
// maxSize para connectedPixelCount: deve ser >> minPix para detectar estruturas finas
// longas. Com maxSize=500, um segmento de rio de 20px numa estrutura de 200px retorna
// 200 (protegido), enquanto um blob isolado de 20px retorna 20 (filtrado).
var max_cc_size       = 25;
// Se true: detecta "pixels ponte" (vizinhos opostos da mesma classe) e os preserva,
// protegendo estruturas lineares finas mesmo que pequenas no total.
var use_bridge_detect = true;
// Classes preservadas mesmo sendo fragmentos pequenos (exceções ao filtro)
// Nota: remap(exc, exc) reaplica o valor original sobre qualquer substituição
var excessions_class  = [33, 29, 25];
// Raio de erosão morfológica: detecta interior compacto (px). Kernel = 2*r+1.
// erode_radius=2 → kernel 5×5 → feições ≥5px de largura têm interior.
var erode_radius      = 2;
// Fragmentos com cc > thin_cc_threshold E sem interior compacto são tratados
// como estruturas finas (preservados). Fragmentos menores são sempre filtrados.
var thin_cc_threshold = 50;
// Grupos de classes tratados como uma mesma feição para CC, erosão e bridge detect.
// Fragmentos de uma classe são preservados se fazem parte de uma mancha maior do grupo.
// Ex: cl21 adjacente a cl15 herda o CC total do grupo → não é filtrado.
var class_merge_groups = [[15, 21], [4, 12]];

// ─── Parâmetros do app ────────────────────────────────────────────────────────
var param = {
    assetInput:  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
    assetBacias: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    assetMosaic: 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    yearMin: 1985,
    yearMax: 2025,
    versions: ['1', '2', '3', '4', '5'],
    listaNameBacias: [
        '765',  '7544',   '7541',  '7411',  '746',   '7591',  '7592',
        '761111','761112','7612',  '7613',  '7614',  '7615',  '771',
        '7712', '772',    '7721',  '773',   '7741',  '7746',  '7754',
        '7761', '7764',   '7691',  '7581',  '7625',  '7584',  '751',
        '752',  '7616',   '745',   '7424',  '7618',  '7561',  '755',
        '7617', '7564',   '7422',  '76116', '7671',  '757',   '766',
        '753',  '764',    '7619',  '7443',  '7438',  '763',   '7622'
    ]
};

// ─── Nomes das classes ────────────────────────────────────────────────────────
var classNames = {
    3: 'Floresta', 4: 'Savana', 5: 'Mangue', 9: 'Silvicultura',
    12: 'Campestre', 15: 'Pastagem', 19: 'Lavoura Anual',
    21: 'Mos. Uso Agropec.', 25: 'Urb./Solo Exp.',
    29: 'Afloramento', 33: 'Água', 36: 'Lavoura Perene'
};

// ─── Estado ───────────────────────────────────────────────────────────────────
var year_show    = 2020;
var bacia_show   = '7584';
var version_show = '5';
var _gen         = 0;
var _primeiraVez = true;

// ─── Filtro Espacial (Sieve Filter) ──────────────────────────────────────────
/**
 * Aplica filtro espacial para redução de ruído (Sieve Filter).
 * Substitui fragmentos pequenos pela moda da vizinhança ksize x ksize.
 *
 * @param {ee.Image}  image      imagem de classes (1 banda)
 * @param {number}    ksize      tamanho do kernel da moda (pixels)
 * @param {number}    minPix     limiar de tamanho de fragmento (pixels)
 * @param {Array}     exclasses  classes preservadas (nunca substituídas)
 */
var modeSpatialFilter = function(image, ksize, minPix, exclasses) {
    var projection = image.projection();

    // Força análise de conectividade na escala nativa (30 m)
    var imgForConnect = image.reproject({ crs: projection, scale: nativeScale });

    // ── Mescla de classes para conectividade ─────────────────────────────────
    // Classes em cada grupo são tratadas como uma mesma feição para CC, erosão e
    // bridge detect. Evita filtrar fragmentos que fazem parte de manchas maiores
    // de classes ecologicamente equivalentes (ex: Pastagem ↔ Mosaico, Savana ↔ Campestre).
    // A imagem de saída continua com as classes originais (usa imgForConnect).
    var imgMerged = imgForConnect;
    for (var _gi = 0; _gi < class_merge_groups.length; _gi++) {
        var _grp = class_merge_groups[_gi];
        for (var _gj = 1; _gj < _grp.length; _gj++) {
            imgMerged = imgMerged.where(imgMerged.eq(_grp[_gj]), _grp[0]);
        }
    }

    // ── Conectividade com maxSize grande ──────────────────────────────────────
    // Calculada sobre imgMerged: classes do mesmo grupo são contadas juntas.
    // maxSize=500: estruturas finas longas retornam CC real, não valor truncado.
    var connect_1 = imgMerged.connectedPixelCount(max_cc_size, true);   // 8-conn
    var connect_2 = imgMerged.connectedPixelCount(max_cc_size, false);  // 4-conn

    // ── Detecção de "pixels ponte" (estruturas finas) ─────────────────────────
    // Calculada sobre imgMerged: ponte entre cl15 e cl21 é detectada como intra-grupo.
    //
    //   Pares opostos verificados:
    //     (+1,0) ↔ (-1,0)  →  eixo horizontal
    //     (0,+1) ↔ (0,-1)  →  eixo vertical
    //     (+1,+1) ↔ (-1,-1) →  diagonal principal
    //     (-1,+1) ↔ (+1,-1) →  diagonal secundária
    var nbands = imgMerged.neighborhoodToBands(ee.Kernel.square(1));
    var bn = ee.String(imgMerged.bandNames().get(0));

    var nb_p10  = nbands.select(bn.cat('_1_0'));    // (+1, 0)
    var nb_n10  = nbands.select(bn.cat('_-1_0'));   // (-1, 0)
    var nb_p01  = nbands.select(bn.cat('_0_1'));    // (0, +1)
    var nb_n01  = nbands.select(bn.cat('_0_-1'));   // (0, -1)
    var nb_p11  = nbands.select(bn.cat('_1_1'));    // (+1, +1)
    var nb_n11  = nbands.select(bn.cat('_-1_-1')); // (-1, -1)
    var nb_n1p1 = nbands.select(bn.cat('_-1_1'));   // (-1, +1)
    var nb_p1n1 = nbands.select(bn.cat('_1_-1'));   // (+1, -1)

    var is_bridge =
        imgMerged.eq(nb_p10).and(imgMerged.eq(nb_n10))    // horizontal
        .or(imgMerged.eq(nb_p01).and(imgMerged.eq(nb_n01)))   // vertical
        .or(imgMerged.eq(nb_p11).and(imgMerged.eq(nb_n11)))   // diagonal ↗↙
        .or(imgMerged.eq(nb_n1p1).and(imgMerged.eq(nb_p1n1)));// diagonal ↖↘

    // Se bridge_detect estiver desligado, nenhum pixel é tratado como "ponte"
    var not_bridge = use_bridge_detect ? is_bridge.not() : ee.Image.constant(1);

    // ── Erosão morfológica: detectar interior compacto ────────────────────────
    // Calculada sobre imgMerged: interior de uma mancha {15,21} é detectado mesmo
    // que os pixels internos alternem entre as duas classes.
    var lmin = imgMerged.focalMin(erode_radius, 'square', 'pixels');
    var lmax = imgMerged.focalMax(erode_radius, 'square', 'pixels');
    var survived = lmin.eq(imgMerged).and(lmax.eq(imgMerged));

    // Dilata o interior de volta para marcar toda a mancha como compacta
    var compact_region = survived
        .reproject({ crs: projection, scale: nativeScale })
        .focalMax(erode_radius, 'square', 'pixels').gt(0);

    // Estruturas finas: cc > thin_cc_threshold E sem interior compacto
    // (rios, florestas ciliares, corredores lineares)
    var is_thin = connect_1.gt(thin_cc_threshold).and(compact_region.not());

    // Extrai e guarda as estruturas finas antes do filtro (valores originais)
    var thin_layer = imgForConnect.updateMask(is_thin);

    // ── Imagem de referência (moda da vizinhança) ─────────────────────────────
    // Usa imgForConnect (classes originais, 30 m explícito)
    var mode_img = imgForConnect.focalMode(ksize, 'square', 'pixels');

    // ── Aplicação do filtro ───────────────────────────────────────────────────
    // Filtra APENAS pixels que são: (a) fragmento pequeno E (b) não são "ponte"
    var mode_all = mode_img.mask(connect_1.lte(minPix).and(not_bridge));

    // Classe 21: 4-conn (mais restrito) + proteção de "ponte"
    // connect_2 reflete o grupo {15,21} mesclado → cl21 ligada a cl15 não é filtrada
    var mode_21  = mode_img.mask(
        imgForConnect.eq(21).and(connect_2.lte(minPix)).and(not_bridge)
    );

    // Composição: original → moda geral → moda cl21 → restaura finas → exceções
    var filtered = imgForConnect
        .blend(mode_all)
        .blend(mode_21)
        .blend(thin_layer)
        .blend(imgForConnect.remap(exclasses, exclasses));

    return filtered.rename(image.bandNames());
};

// ─── Assets base ──────────────────────────────────────────────────────────────
var shp_bacias_all = ee.FeatureCollection(param.assetBacias);
var mosaic_col     = ee.ImageCollection(param.assetMosaic)
                       .select(['red', 'green', 'blue', 'nir', 'swir1', 'swir2']);
var ic_input       = ee.ImageCollection(param.assetInput);

// ─── Mapas Split ──────────────────────────────────────────────────────────────
var Map_esq = ui.Map({ style: { border: '2px solid #1a237e' } });
var Map_dir = ui.Map({ style: { border: '2px solid #b71c1c', stretch: 'both' } });
Map_esq.setOptions('SATELLITE');
Map_dir.setOptions('SATELLITE');
Map_esq.setControlVisibility({ layerList: true, fullscreenControl: false });
Map_dir.setControlVisibility({ layerList: true, fullscreenControl: false });

var linker     = ui.Map.Linker([Map_esq, Map_dir]);
var splitPanel = ui.SplitPanel({
    firstPanel:  linker.get(0),
    secondPanel: linker.get(1),
    orientation: 'horizontal',
    wipe:        true,
    style:       { stretch: 'both' }
});

// ─── Cabeçalhos flutuantes dos mapas ──────────────────────────────────────────
var lbl_hdr_esq = ui.Label('◀ Original', {
    fontWeight: 'bold', fontSize: '12px', color: '#ffffff',
    backgroundColor: '#1a237ecc', padding: '3px 8px', margin: '4px'
});
var lbl_hdr_dir = ui.Label('Filtrado ▶', {
    fontWeight: 'bold', fontSize: '12px', color: '#ffffff',
    backgroundColor: '#b71c1ccc', padding: '3px 8px', margin: '4px'
});
Map_esq.add(ui.Panel([lbl_hdr_esq], null,
    { position: 'top-left',  padding: '0px', margin: '0px' }));
Map_dir.add(ui.Panel([lbl_hdr_dir], null,
    { position: 'top-right', padding: '0px', margin: '0px' }));

// ─── Visualizações ────────────────────────────────────────────────────────────
var visclass  = { min: 0, max: 75, palette: palette };
var visMosaic = { min: 0.012, max: 0.22, bands: ['red', 'green', 'blue'] };
var visDiff   = { min: 1, max: 1, palette: ['FF4500'] };

// ─── Painel de estatísticas ───────────────────────────────────────────────────
var statsPanel = ui.Panel({
    style: {
        stretch: 'horizontal', padding: '4px 6px',
        backgroundColor: '#f5f5f5', border: '1px solid #ddd'
    }
});
statsPanel.add(ui.Label('Aguardando "Aplicar"...', {
    color: '#888', fontSize: '10px', fontStyle: 'italic'
}));

// ─── Série temporal do pixel ──────────────────────────────────────────────────
var chartPanel = ui.Panel({
    style: {
        stretch: 'horizontal', height: '80px', padding: '2px 4px',
        backgroundColor: '#f5f5f5', border: '1px solid #ccc'
    }
});
chartPanel.add(ui.Label('Clique no mapa para ver a série temporal.',
    { color: '#555', fontSize: '10px' }));

var img_ref_allbands = null;

function onMapClick(coords) {
    if (!img_ref_allbands) return;
    chartPanel.clear();
    chartPanel.add(ui.Label('Carregando...', { color: 'gray', fontSize: '10px' }));

    var point = ee.Geometry.Point([coords.lon, coords.lat]);
    img_ref_allbands.reduceRegion({
        reducer: ee.Reducer.first(), geometry: point, scale: 30, maxPixels: 1e6
    }).evaluate(function(vals) {
        chartPanel.clear();
        if (!vals) {
            chartPanel.add(ui.Label('Sem dado neste pixel.', { color: 'red', fontSize: '10px' }));
            return;
        }
        var rows = [['Ano', 'Classe',
            { role: 'style', type: 'string' },
            { role: 'tooltip', type: 'string', p: { html: true } }]];
        for (var y = param.yearMin; y <= param.yearMax; y++) {
            var cl  = vals['classification_' + y];
            var ci  = (cl !== null && cl !== undefined) ? parseInt(cl, 10) : 0;
            var cor = (ci > 0 && palette[ci]) ? palette[ci] : 'e0e0e0';
            var nm  = classNames[ci] || ('Cl.' + ci);
            rows.push([y, 1,
                'point {size:3; fill-color:#' + cor + '; stroke-color:#' + cor + '}',
                '<b>' + y + '</b><br/>' + nm + ' (' + ci + ')']);
        }
        chartPanel.add(ui.Label(
            coords.lat.toFixed(4) + ', ' + coords.lon.toFixed(4),
            { fontSize: '9px', color: '#444', margin: '0px 0 1px 2px' }
        ));
        var chart = ui.Chart(rows).setChartType('ScatterChart').setOptions({
            title: '', legend: { position: 'none' }, tooltip: { isHtml: true },
            hAxis: { format: '####', textStyle: { fontSize: 7 }, gridlines: { count: 6 },
                     viewWindow: { min: param.yearMin, max: param.yearMax } },
            vAxis: { viewWindow: { min: 0, max: 2 }, ticks: [], gridlines: { count: 0 },
                     baselineColor: 'transparent' },
            chartArea: { width: '94%', height: '55%' }
        });
        chart.style().set({ stretch: 'horizontal', height: '65px' });
        chartPanel.add(chart);
    });
}
Map_esq.onClick(onMapClick);
Map_dir.onClick(onMapClick);

// ─── Função de atualização ────────────────────────────────────────────────────
function atualizar() {
    _gen++;
    var my_gen   = _gen;
    var banda    = 'classification_' + year_show;
    var year_mos = year_show > 2024 ? 2024 : year_show;

    lbl_hdr_esq.setValue('◀ Original v' + version_show + ' | ' + year_show);
    lbl_hdr_dir.setValue('Filtrado k=' + kernel_size +
                         ' mp=' + max_filter_pixels + ' ▶');

    // Geometria da bacia
    var shp_sel = shp_bacias_all.filter(ee.Filter.eq('nunivotto4', bacia_show));
    var mask_bacia = shp_sel.map(function(f) { return f.set('id_cod', 1); })
                            .reduceToImage(['id_cod'], ee.Reducer.first());
    var geom_bacia = shp_sel.geometry();

    // Mosaico de referência
    var mosaic_year = mosaic_col
        .filter(ee.Filter.date(year_mos + '-01-01', (year_mos + 1) + '-01-01'))
        .filterBounds(geom_bacia)
        .median();

    // Borda da bacia
    var bordas = ee.Image().byte()
        .paint(shp_sel, 1, 1)
        .visualize({ palette: 'FF0000', opacity: 0.9 });

    // ── Carrega imagem original ───────────────────────────────────────────────
    var ic_ver = ic_input
        .filter(ee.Filter.eq('version',  parseInt(version_show, 10)))
        .filter(ee.Filter.eq('id_bacias', bacia_show));

    var img_original = ic_ver.first()
        .select(banda)
        .updateMask(mask_bacia);

    // ── Aplica o filtro ───────────────────────────────────────────────────────
    var img_filtered = modeSpatialFilter(
        img_original, kernel_size, max_filter_pixels, excessions_class
    ).rename([banda]);

    // ── Pixels modificados (diferença original → filtrado) ────────────────────
    var diff_layer = img_original.neq(img_filtered).selfMask();

    // ── Renderiza mapas ───────────────────────────────────────────────────────
    Map_esq.layers().reset([]);
    Map_dir.layers().reset([]);

    Map_esq.addLayer(mosaic_year, visMosaic, 'Mosaico ' + year_show, true);
    Map_esq.addLayer(img_original, visclass, 'Original', true);
    Map_esq.addLayer(bordas, {}, 'Bacia', true);

    Map_dir.addLayer(mosaic_year, visMosaic, 'Mosaico ' + year_show, true);
    Map_dir.addLayer(img_filtered, visclass, 'Filtrado', true);
    Map_dir.addLayer(diff_layer.visualize(visDiff), {}, 'Pixels modificados (laranja)', true);
    Map_dir.addLayer(bordas, {}, 'Bacia', true);

    // Imagem multi-banda para série temporal do pixel (referência = original)
    img_ref_allbands = ic_ver.first().updateMask(mask_bacia);

    if (_primeiraVez) {
        Map_dir.centerObject(shp_sel, 9);
        _primeiraVez = false;
    }

    lbl_ano_val.setValue(String(year_show));

    // ── Estatísticas assíncronas ──────────────────────────────────────────────
    statsPanel.clear();
    statsPanel.add(ui.Label('Calculando...', { color: 'gray', fontSize: '10px', fontStyle: 'italic' }));

    diff_layer.reduceRegion({
        reducer:    ee.Reducer.sum(),
        geometry:   geom_bacia,
        scale:      30,
        maxPixels:  1e10,
        bestEffort: true
    }).evaluate(function(result) {
        if (_gen !== my_gen) return;
        statsPanel.clear();

        var totalMod = result ? (result[banda] || 0) : 0;

        statsPanel.add(ui.Label(
            'Bacia: ' + bacia_show +
            '  Ano: ' + year_show +
            '  v' + version_show,
            { fontWeight: 'bold', fontSize: '10px', color: '#1a237e' }
        ));
        statsPanel.add(ui.Label(
            'kernel=' + kernel_size + 'px  minFragmento=' + max_filter_pixels + 'px' +
            '  erode=' + erode_radius + '  thinCC>' + thin_cc_threshold,
            { fontSize: '10px', color: '#555' }
        ));
        statsPanel.add(ui.Label(
            'Total pixels modificados: ' + totalMod,
            { fontSize: '11px', color: '#b71c1c', fontWeight: 'bold', margin: '3px 0px' }
        ));

        // Histograma: quais classes foram SUBSTITUÍDAS (pixels originais que mudaram)
        img_original.updateMask(diff_layer).reduceRegion({
            reducer:    ee.Reducer.frequencyHistogram(),
            geometry:   geom_bacia,
            scale:      30,
            maxPixels:  1e10,
            bestEffort: true
        }).evaluate(function(hist) {
            if (_gen !== my_gen || !hist || !hist[banda]) return;

            var h     = hist[banda];
            var linhas = [];
            for (var cl in h) { linhas.push({ cl: parseInt(cl, 10), n: h[cl] }); }
            linhas.sort(function(a, b) { return b.n - a.n; });

            statsPanel.add(ui.Label('Classe substituída → nº de pixels:', {
                fontSize: '10px', color: '#444', fontWeight: 'bold', margin: '4px 0px 1px 0px'
            }));
            linhas.slice(0, 9).forEach(function(item) {
                var nm  = classNames[item.cl] || ('Cl.' + item.cl);
                var pct = totalMod > 0 ? ((item.n / totalMod) * 100).toFixed(1) : '0.0';
                statsPanel.add(ui.Label(
                    'Cl.' + item.cl + ' ' + nm + ': ' + item.n + ' (' + pct + '%)',
                    { fontSize: '10px', color: '#333', margin: '0px 0px 1px 6px' }
                ));
            });
        });
    });
}

// ─── Helpers de UI ────────────────────────────────────────────────────────────
function sectionLabel(txt, bgColor) {
    return ui.Label(txt, {
        fontWeight: 'bold', fontSize: '11px', color: '#ffffff',
        backgroundColor: bgColor || '#37474f',
        padding: '3px 6px', margin: '8px 0px 3px 0px', stretch: 'horizontal'
    });
}

function makeSliderRow(label_text, min_v, max_v, init_v, step_v, onChange_cb) {
    var lbl_val = ui.Label(String(init_v), {
        fontWeight: 'bold', fontSize: '11px',
        width: '28px', margin: '3px 0px 3px 4px', color: '#b71c1c'
    });
    var sldr = ui.Slider({
        min: min_v, max: max_v, value: init_v, step: step_v,
        style: { stretch: 'horizontal', margin: '2px 0px' }
    });
    sldr.onSlide( function(v) { lbl_val.setValue(String(Math.round(v))); });
    sldr.onChange(function(v) { lbl_val.setValue(String(Math.round(v))); onChange_cb(Math.round(v)); });

    return ui.Panel(
        [
            ui.Label(label_text, { fontSize: '10px', color: '#555', width: '88px', margin: '3px 0px' }),
            sldr, lbl_val
        ],
        ui.Panel.Layout.Flow('horizontal'),
        { stretch: 'horizontal', margin: '1px 0px' }
    );
}

// ─── Slider de ano ────────────────────────────────────────────────────────────
var lbl_ano_val = ui.Label(String(year_show), {
    fontWeight: 'bold', fontSize: '15px', color: '#4a148c',
    margin: '4px 10px 4px 6px', width: '44px'
});
var slider_year = ui.Slider({
    min: param.yearMin, max: param.yearMax, value: year_show, step: 1,
    style: { stretch: 'horizontal', margin: '4px 8px' }
});
slider_year.onSlide( function(v) { year_show = Math.round(v); lbl_ano_val.setValue(String(year_show)); });
slider_year.onChange(function(v) { year_show = Math.round(v); atualizar(); });

// ─── Sliders de parâmetros do filtro ─────────────────────────────────────────
var slider_kernel = makeSliderRow('Kernel (px):', 3, 21, kernel_size, 2,
    function(v) { kernel_size = v; });

var slider_minpix = makeSliderRow('Min. pixeis:', 5, 100, max_filter_pixels, 5,
    function(v) { max_filter_pixels = v; });

var slider_maxcc = makeSliderRow('maxSize CC:', 50, 1000, max_cc_size, 50,
    function(v) { max_cc_size = v; });

var slider_eroderadius = makeSliderRow('Erode radius:', 1, 6, erode_radius, 1,
    function(v) { erode_radius = v; });

var slider_thincc = makeSliderRow('Min CC fino:', 10, 300, thin_cc_threshold, 10,
    function(v) { thin_cc_threshold = v; });

// ─── Toggle de detecção de pontes ────────────────────────────────────────────
var lbl_bridge_val = ui.Label(use_bridge_detect ? 'ON' : 'OFF', {
    fontWeight: 'bold', fontSize: '11px',
    color: use_bridge_detect ? '#1b5e20' : '#b71c1c',
    width: '32px', margin: '3px 0px 3px 4px'
});
var chk_bridge = ui.Checkbox({
    label:   'Preservar estruturas finas (bridge detect)',
    value:   use_bridge_detect,
    style:   { fontSize: '11px', color: '#333', margin: '4px 0px' },
    onChange: function(v) {
        use_bridge_detect = v;
        lbl_bridge_val.setValue(v ? 'ON' : 'OFF');
        lbl_bridge_val.style().set('color', v ? '#1b5e20' : '#b71c1c');
    }
});

// ─── Campo de exceções ────────────────────────────────────────────────────────
var txt_exclasses = ui.Textbox({
    value:       excessions_class.join(','),
    placeholder: 'ex: 33,29,25',
    style:       { stretch: 'horizontal', margin: '2px 0px', fontSize: '11px' },
    onChange:    function(v) {
        var parsed = v.split(',')
            .map(function(s) { return parseInt(s.trim(), 10); })
            .filter(function(n) { return !isNaN(n); });
        excessions_class = parsed;
    }
});

// ─── Seletores ────────────────────────────────────────────────────────────────
var sel_bacia = ui.Select({
    items:       param.listaNameBacias,
    value:       bacia_show,
    placeholder: 'Bacia...',
    onChange:    function(b) { bacia_show = b; },
    style:       { stretch: 'horizontal', margin: '2px 0px' }
});

var sel_version = ui.Select({
    items:       param.versions,
    value:       version_show,
    placeholder: 'Versão...',
    onChange:    function(v) { version_show = v; },
    style:       { stretch: 'horizontal', margin: '2px 0px' }
});

// ─── Botão Aplicar ────────────────────────────────────────────────────────────
var btn_apply = ui.Button({
    label:   '✔  Aplicar',
    onClick: function() { atualizar(); },
    style: {
        stretch: 'horizontal', fontWeight: 'bold', fontSize: '13px',
        color: '#ffffff', backgroundColor: '#c62828',
        margin: '4px 0px 6px 0px', padding: '5px'
    }
});

// ─── Legenda ──────────────────────────────────────────────────────────────────
function makeLegend() {
    var items = [
        { id: 4,  name: 'Savana'         },
        { id: 3,  name: 'Floresta'       },
        { id: 12, name: 'Campestre'      },
        { id: 15, name: 'Pastagem'       },
        { id: 21, name: 'Mos. Uso Agr.'  },
        { id: 19, name: 'Lavoura Anual'  },
        { id: 36, name: 'Lavoura Perene' },
        { id: 29, name: 'Afloramento'    },
        { id: 33, name: 'Água'           },
        { id: 25, name: 'Urb./Solo Exp.' }
    ];
    return ui.Panel(
        items.map(function(c) {
            var cor = palette[c.id] || 'cccccc';
            var icon = ui.Label({
                style: {
                    backgroundColor: cor,
                    width: '13px', height: '13px',
                    margin: '2px 5px 2px 0px', border: '1px solid #aaa'
                }
            });
            return ui.Panel(
                [icon, ui.Label(c.id + ' — ' + c.name,
                    { fontSize: '10px', color: '#333', margin: '1px 0px' })],
                ui.Panel.Layout.Flow('horizontal'),
                { margin: '0px', padding: '0px' }
            );
        }),
        ui.Panel.Layout.Flow('vertical'),
        { padding: '0px' }
    );
}

// ─── Painel lateral ───────────────────────────────────────────────────────────
var panel_side = ui.Panel(
    [
        ui.Label('Filtro Espacial Sieve', {
            fontWeight: 'bold', fontSize: '14px', color: '#b71c1c',
            margin: '4px 0px 0px 0px'
        }),
        ui.Label('Col11 Caatinga — Teste de parâmetros', {
            fontSize: '10px', color: '#666', margin: '0px 0px 4px 0px'
        }),
        btn_apply,

        sectionLabel('Bacia / Versão', '#37474f'),
        ui.Label('Bacia:', { fontSize: '10px', color: '#555', margin: '3px 0px 1px 0px' }),
        sel_bacia,
        ui.Label('Versão do asset:', { fontSize: '10px', color: '#555', margin: '3px 0px 1px 0px' }),
        sel_version,

        sectionLabel('Parâmetros do Filtro', '#c62828'),
        slider_kernel,
        slider_minpix,
        slider_maxcc,
        ui.Label('maxSize CC: cap de conectividade. ↑ protege estruturas longas.', {
            fontSize: '9px', color: '#888', fontStyle: 'italic', margin: '0px 0px 4px 0px'
        }),
        slider_eroderadius,
        slider_thincc,
        ui.Label('Erode radius + Min CC fino: manchas com cc > Min CC fino e\n' +
                 'sem interior compacto (erosão) são preservadas como estruturas finas.',
            { fontSize: '9px', color: '#888', fontStyle: 'italic', margin: '0px 0px 4px 0px' }
        ),
        chk_bridge,
        ui.Label(
            'Bridge detect: preserva pixels com vizinhos opostos da mesma\n' +
            'classe (tendrils, florestas ciliares, corredores finos).',
            { fontSize: '9px', color: '#888', fontStyle: 'italic', margin: '0px 0px 4px 0px' }
        ),
        ui.Label('Classes de exceção (preservadas):', {
            fontSize: '10px', color: '#555', margin: '6px 0px 1px 0px'
        }),
        txt_exclasses,
        ui.Label('Classe 21 usa conectividade 4 (mais restrito).', {
            fontSize: '9px', color: '#888', fontStyle: 'italic', margin: '2px 0px 0px 0px'
        }),

        sectionLabel('Estatísticas de mudança', '#455a64'),
        statsPanel,

        sectionLabel('Legenda de classes', '#455a64'),
        makeLegend(),

        sectionLabel('Série temporal do pixel', '#455a64'),
        chartPanel
    ],
    ui.Panel.Layout.Flow('vertical'),
    {
        width: '300px', padding: '8px',
        backgroundColor: '#fafafa', border: '1px solid #ccc'
    }
);

// ─── Barra de ano ─────────────────────────────────────────────────────────────
var panel_slider = ui.Panel(
    [
        ui.Label('Ano:', {
            fontWeight: 'bold', fontSize: '12px', margin: '6px 4px 6px 12px'
        }),
        lbl_ano_val,
        slider_year
    ],
    ui.Panel.Layout.Flow('horizontal'),
    {
        border: '1px solid #bbb', padding: '4px 8px',
        backgroundColor: '#eeeeee', stretch: 'horizontal'
    }
);

// ─── Layout principal ─────────────────────────────────────────────────────────
var panel_maps    = ui.Panel([splitPanel], ui.Panel.Layout.Flow('vertical', true), { stretch: 'both' });
var panel_content = ui.Panel([panel_maps, panel_slider], ui.Panel.Layout.Flow('vertical'), { stretch: 'both' });
var panel_main    = ui.Panel([panel_side, panel_content], ui.Panel.Layout.Flow('horizontal'), { stretch: 'both' });

ui.root.widgets().reset([panel_main]);
ui.root.setLayout(ui.Panel.Layout.Flow('vertical'));

// ─── Carga inicial ────────────────────────────────────────────────────────────
atualizar();
