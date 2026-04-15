var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = palettes.get('brazil');

// ─── Visualização ─────────────────────────────────────────────────────────────
var visualizar = {
    visclass:  { min: 0, max: 75, palette: palette, format: 'png' },
    visMosaic: { min: 0.012, max: 0.22, bands: ['red', 'green', 'blue'] }
};
// sequencias de filtros
// filter Gap-fil >> Spatial >> Temporal J3 >> TemporalA J3 >> Temporal J4 >> TemporalA J4
// >> Temporal J5 >> TemporalA J5 >> Spatial_int >> Frequency >> Spatial All

// ─── Parâmetros ───────────────────────────────────────────────────────────────
var param = {
    assetMap:   'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    assetclass: 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
    asset_filters: {
        gap_fill:    "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill",
        temporalN:   "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalNat",
        temporalA:   "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt",
        spatial_int: "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_int",
        frequency:   "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency",
        spatial_all: "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_all"
    },
    assetIm:    'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    assetBacia: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    bandas:     ['red', 'green', 'blue', 'nir', 'swir1', 'swir2'],
    yearMin:    1985,
    yearMax:    2025,
    listaNameBacias: [
        'all', '765', '7544', '7541', '7411', '746', '7591',
        '7592', '761111', '761112', '7612', '7613', '7614',
        '7615', '771', '7712', '772', '7721', '773', '7741',
        '7754', '7761', '7764', '7691', '7581', '7625', '7584',
        '751', '752', '7616', '745', '7424', '7618', '7561',
        '755', '7617', '7564', '7422', '76116', '7671', '757',
        '766', '753', '764', '7619', '7443', '7438', '763',
        '7622', '7746'
    ],
    versions:          ['1', '2', '3', '4', '5'],
    numero_class:      [7, 10],
    version_posClase:  [1, 2]
};

// ─── Estado ──────────────────────────────────────────────────────────────────
var year_show         = 2024;
var bacia_show        = 'all';
var version_show      = '1';
var ver_posclass_show = param.version_posClase[0];   // 1
var num_class_show    = param.numero_class[0];        // 7
var janela_show       = 3;
var filters_show = {
    gap_fill:    false,
    temporalN:   false,
    temporalA:   false,
    spatial_int: false,
    frequency:   false,
    spatial_all: false
};

// ─── Assets base ─────────────────────────────────────────────────────────────
var shp_bacias_all = ee.FeatureCollection(param.assetBacia)
    .map(function(f) { return f.set('id_cod', 1); });

var mosaic_norm = ee.ImageCollection(param.assetIm)
    .filterBounds(shp_bacias_all.geometry())
    .select(param.bandas);

var map_col10 = ee.Image(param.assetMap);
var ic_class  = ee.ImageCollection(param.assetclass);

// ─── Mapas ───────────────────────────────────────────────────────────────────
var Map_esq = ui.Map({ style: { border: '2px solid #1a237e' } });
var Map_dir = ui.Map({ style: { border: '2px solid #1b5e20', stretch: 'both' } });
Map_esq.setOptions('SATELLITE');
Map_dir.setOptions('SATELLITE');

var linker = ui.Map.Linker([Map_esq, Map_dir]);

var splitPanel = ui.SplitPanel({
    firstPanel:  linker.get(0),
    secondPanel: linker.get(1),
    orientation: 'horizontal',
    wipe:        true,
    style:       { stretch: 'both' }
});

// ─── Controle de geração (anti-race para callbacks assíncronos) ───────────────
var _gen = 0;
var _primeiraVez = true;

// ─── Estado da imagem multi-banda col11 (atualizado em atualizar()) ───────────
var img_col11_allbands = null;

// ─── Nomes das classes MapBiomas ──────────────────────────────────────────────
var classNames = {
    3: 'Floresta', 4: 'Savana', 12: 'Campestre', 
    15: 'Pastagem', 19: 'Lavoura', 21: 'Mos. Uso',
    25: 'Urb./Solo Exp.', 29: 'Afloramento', 33: 'Água',
    36: 'Perene'
};

// ─── Painel do gráfico de série temporal do pixel ────────────────────────────
var chartPixelPanel = ui.Panel({
    style: {
        stretch: 'horizontal',
        height: '100px',
        padding: '2px 4px',
        backgroundColor: '#f5f5f5',
        border: '1px solid #ccc'
    }
});
chartPixelPanel.add(ui.Label(
    'Clique em um pixel para ver a série temporal.',
    { color: '#555', fontSize: '10px' }
));

// ─── Função de inspeção de pixel ─────────────────────────────────────────────
function onMapClick(coords) {
    if (!img_col11_allbands) {
        chartPixelPanel.clear();
        chartPixelPanel.add(ui.Label('⚠️ Aguarde o carregamento do mapa.', { color: 'orange' }));
        return;
    }
    chartPixelPanel.clear();
    chartPixelPanel.add(ui.Label('⏳ Carregando série do pixel...', { color: 'gray', fontSize: '11px' }));

    var point = ee.Geometry.Point([coords.lon, coords.lat]);

    img_col11_allbands.reduceRegion({
        reducer: ee.Reducer.first(),
        geometry: point,
        scale: 30,
        maxPixels: 1e6
    }).evaluate(function(vals) {
        chartPixelPanel.clear();

        if (!vals) {
            chartPixelPanel.add(ui.Label('⚠️ Sem dado neste pixel.', { color: 'red' }));
            return;
        }

        var years = [];
        for (var y = param.yearMin; y <= param.yearMax; y++) { years.push(y); }

        // DataTable: [Ano, Classe, {role:'style'}, {role:'tooltip'}]
        var header = ['Ano', 'Classe',
                      { role: 'style',   type: 'string' },
                      { role: 'tooltip', type: 'string', p: { html: true } }];
        var rows = [header];

        years.forEach(function(ano) {
            var banda     = 'classification_' + ano;
            var classe    = vals[banda];
            var classeInt = (classe !== null && classe !== undefined) ? parseInt(classe) : 0;
            var cor       = (classeInt > 0 && palette[classeInt])
                            ? palette[classeInt] : '#e0e0e0';
            var nome      = classNames[classeInt] || ('Classe ' + classeInt);
            // ScatterChart: estilo por ponto — círculo colorido de tamanho fixo
            rows.push([
                ano,
                1,
                'point {size: 3; fill-color: ' + cor + '; stroke-color: ' + cor + '}',
                '<b>' + ano + '</b><br/>' + nome + ' (' + classeInt + ')'
            ]);
        });

        chartPixelPanel.add(ui.Label(
            coords.lat.toFixed(4) + ', ' + coords.lon.toFixed(4) +
            ' | bacia: ' + bacia_show + ' | v' + version_show,
            { fontSize: '9px', color: '#444', margin: '0px 0 1px 2px' }
        ));

        var chart = ui.Chart(rows)
            .setChartType('ScatterChart')
            .setOptions({
                title: '',
                hAxis: { format: '####', textStyle: { fontSize: 7 }, gridlines: { count: 5 },
                         viewWindow: { min: param.yearMin, max: param.yearMax } },
                vAxis: {
                    viewWindow: { min: 0, max: 2 },
                    ticks: [],
                    gridlines:    { count: 0 },
                    baselineColor: 'transparent'
                },
                legend:    { position: 'none' },
                tooltip:   { isHtml: true },
                chartArea: { width: '94%', height: '50%' }
            });
        chart.style().set({ stretch: 'horizontal', height: '75px' });
        chartPixelPanel.add(chart);
    });
}

// ─── Helper: adiciona camada pós-class se o asset tiver dados ────────────────
// Verifica tamanho do IC assincronamente; só adiciona se ainda for a geração
// atual, evitando sobreposição de camadas de chamadas anteriores a atualizar().
// janela: opcional; quando fornecido filtra a propriedade 'janela' (apenas para camadas temporais).
function addPosClassLayer(assetPath, banda, mask_bacia, label, my_gen, janela) {
    var ic_raw = ee.ImageCollection(assetPath);
    var ic = ic_raw
        .filter(ee.Filter.eq('version', ver_posclass_show))
        .filter(ee.Filter.eq('num_class', num_class_show));

    if (janela !== undefined) {
        ic = ic.filter(ee.Filter.eq('janela', janela));
    }

    if (bacia_show !== 'all') {
        ic = ic.filter(ee.Filter.eq('id_bacias', bacia_show));
    }

    var layerLabel = (janela !== undefined)
        ? label + ' j' + janela + ' v' + ver_posclass_show + ' nc' + num_class_show
        : label + ' v' + ver_posclass_show + ' nc' + num_class_show;

    ic.size().evaluate(function(n) {
        if (_gen !== my_gen) return;

        if (n > 0) {
            var img = ic.max().select(banda).updateMask(mask_bacia);
            Map_dir.addLayer(img, visualizar.visclass, layerLabel, true);
        } else {
            print('Aviso: ' + label + ' não possui dados para os filtros selecionados.');
        }
    });
}

// ─── Função de atualização ────────────────────────────────────────────────────
function atualizar() {
    _gen++;
    var my_gen = _gen;
    var banda    = 'classification_' + year_show;
    var year_mos = year_show > 2024 ? 2024 : year_show;

    var shp_sel = (bacia_show === 'all')
        ? shp_bacias_all
        : shp_bacias_all.filter(ee.Filter.eq('nunivotto4', bacia_show));

    var mask_bacia = shp_sel.map(function(f) { return f.set('id_cod', 1); })
                            .reduceToImage(['id_cod'], ee.Reducer.first());
    var date_inic = ee.Date.fromYMD(year_mos, 1, 1);
    var mosaic_year = mosaic_norm.filter(ee.Filter.date( date_inic, date_inic.advance(1, 'year'))).median();

    var col10_img = map_col10.updateMask(mask_bacia).select(banda);

    var ic_filt = ic_class
        .filter(ee.Filter.stringContains('system:index', 'fm-v_' + version_show));
    if (bacia_show !== 'all') {
        ic_filt = ic_filt.filter(ee.Filter.eq('id_bacias', bacia_show));
    }
    var col11_img = ic_filt.select(banda).max();

    var bordas = ee.Image().byte()
        .paint(shp_sel, 1, 1)
        .visualize({ palette: 'FF0000', opacity: 0.8 });

    Map_esq.layers().reset([]);
    Map_dir.layers().reset([]);

    // ── mapa esquerdo: Col10 + filtros pós-class selecionados ────────────────
    Map_esq.addLayer(mosaic_year, visualizar.visMosaic, 'Mosaico ' + year_show, true);
    Map_esq.addLayer(col10_img,   visualizar.visclass,  'Col10 '   + year_show, true);

    if (filters_show.gap_fill)    addPosClassLayer( param.asset_filters.gap_fill,    banda, mask_bacia, 'Gap-fill',    my_gen);
    if (filters_show.temporalN)   addPosClassLayer( param.asset_filters.temporalN,   banda, mask_bacia, 'TemporalNat', my_gen, janela_show);
    if (filters_show.temporalA)   addPosClassLayer( param.asset_filters.temporalA,   banda, mask_bacia, 'TemporalAnt', my_gen, janela_show);
    if (filters_show.spatial_int) addPosClassLayer( param.asset_filters.spatial_int, banda, mask_bacia, 'Spatial-int', my_gen);
    if (filters_show.frequency)   addPosClassLayer( param.asset_filters.frequency,   banda, mask_bacia, 'Frequency',   my_gen);
    if (filters_show.spatial_all) addPosClassLayer( param.asset_filters.spatial_all, banda, mask_bacia, 'Spatial-all', my_gen);

    Map_esq.addLayer(bordas,        {},                  'Bacias',                true);
    Map_esq.addLayer(shp_bacias_all, { color: '00000000' }, 'FC Bacias (inspector)', false);

    // ── mapa direito: Col11 classificação ────────────────────────────────────
    Map_dir.addLayer(mosaic_year, visualizar.visMosaic, 'Mosaico ' + year_show,                      true);
    Map_dir.addLayer(col11_img,   visualizar.visclass,  'Col11 v'  + version_show + ' ' + year_show, true);
    Map_dir.addLayer(bordas,       {},                   'Bacias',                                     true);
    Map_dir.addLayer(shp_bacias_all, { color: '00000000' }, 'FC Bacias (inspector)',                  false);

    // Atualiza imagem multi-banda para inspeção de pixel
    img_col11_allbands = ic_filt.max();

    if (_primeiraVez) {
        if (bacia_show === 'all') {
            Map_dir.setCenter(-39.259, -9.092, 7);
        } else {
            Map_dir.centerObject(shp_sel, 9);
        }
        _primeiraVez = false;
    }

    lbl_ano_val.setValue(String(year_show));
}

// ─── Slider de ano ───────────────────────────────────────────────────────────
var lbl_ano_val = ui.Label(String(year_show), {
    fontWeight: 'bold', fontSize: '15px', color: '#4a148c',
    margin: '4px 10px 4px 6px', width: '44px'
});

var slider_year = ui.Slider({
    min: param.yearMin, max: param.yearMax, value: year_show, step: 1,
    style: { stretch: 'horizontal', margin: '4px 8px' }
});
slider_year.onSlide(function(v) {
    year_show = Math.round(v);
    lbl_ano_val.setValue(String(year_show));
});
slider_year.onChange(function(v) {
    year_show = Math.round(v);
    lbl_ano_val.setValue(String(year_show));
    atualizar();
});

// ─── Selects ─────────────────────────────────────────────────────────────────
var sel_version = ui.Select({
    items: param.versions, value: version_show, placeholder: 'Versão...',
    onChange: function(v) { version_show = v; atualizar(); },
    style: { stretch: 'horizontal', margin: '2px 0px' }
});

var sel_bacia = ui.Select({
    items: param.listaNameBacias, value: bacia_show, placeholder: 'Bacia...',
    onChange: function(b) { bacia_show = b; atualizar(); },
    style: { stretch: 'horizontal', margin: '2px 0px' }
});

var sel_ver_pos = ui.Select({
    items: param.version_posClase.map(String), value: String(ver_posclass_show),
    placeholder: 'v.pos...',
    onChange: function(v) { ver_posclass_show = parseInt(v, 10); atualizar(); },
    style: { stretch: 'horizontal', margin: '2px 0px' }
});

var sel_num_class = ui.Select({
    items: param.numero_class.map(String), value: String(num_class_show),
    placeholder: 'n.cl...',
    onChange: function(v) { num_class_show = parseInt(v, 10); atualizar(); },
    style: { stretch: 'horizontal', margin: '2px 0px' }
});

// ─── Checkboxes de filtros pós-class ─────────────────────────────────────────
function makeCheckbox(label, key) {
    return ui.Checkbox({
        label:    label,
        value:    false,
        onChange: function(checked) { filters_show[key] = checked; atualizar(); },
        style:    { margin: '3px 0px', fontSize: '12px' }
    });
}

// ─── Seletor de janela temporal (visível apenas quando Nat ou Ant estão ativos) ──
var sel_janela = ui.Select({
    items: ['3', '4', '5'], value: String(janela_show), placeholder: 'Janela...',
    onChange: function(v) { janela_show = parseInt(v, 10); atualizar(); },
    style: { stretch: 'horizontal', margin: '2px 0px' }
});

var panel_janela = ui.Panel(
    [
        ui.Label('Janela temporal:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 8px' }),
        sel_janela
    ],
    ui.Panel.Layout.Flow('vertical'),
    { shown: false, padding: '0px' }
);

function updateJanelaVisibility() {
    panel_janela.style().set('shown', filters_show.temporalN || filters_show.temporalA);
}

var cb_gap_fill    = makeCheckbox('Gap-fill',    'gap_fill');

var cb_temporalN = ui.Checkbox({
    label: 'Temporal Nat', value: false,
    onChange: function(checked) { filters_show.temporalN = checked; updateJanelaVisibility(); atualizar(); },
    style: { margin: '3px 0px', fontSize: '12px' }
});

var cb_temporalA = ui.Checkbox({
    label: 'Temporal Ant', value: false,
    onChange: function(checked) { filters_show.temporalA = checked; updateJanelaVisibility(); atualizar(); },
    style: { margin: '3px 0px', fontSize: '12px' }
});

var cb_spatial_int = makeCheckbox('Spatial int', 'spatial_int');
var cb_frequency   = makeCheckbox('Frequency',   'frequency');
var cb_spatial_all = makeCheckbox('Spatial all', 'spatial_all');

// ─── Cabeçalhos sobrepostos nos mapas ────────────────────────────────────────
Map_esq.add(ui.Panel([
    ui.Label('◀ Col. 10 + Pós-class', {
        fontWeight: 'bold', fontSize: '13px', color: '#ffffff',
        backgroundColor: '#1a237ecc', padding: '3px 8px', margin: '4px'
    })
], null, { position: 'top-left', padding: '0px', margin: '0px' }));

Map_dir.add(ui.Panel([
    ui.Label('Col. 11 Classificação ▶', {
        fontWeight: 'bold', fontSize: '13px', color: '#ffffff',
        backgroundColor: '#1b5e20cc', padding: '3px 8px', margin: '4px'
    })
], null, { position: 'top-right', padding: '0px', margin: '0px' }));

// ─── Painel lateral ──────────────────────────────────────────────────────────
function sectionLabel(txt, color) {
    return ui.Label(txt, {
        fontWeight: 'bold', fontSize: '11px', color: '#ffffff',
        backgroundColor: color || '#37474f',
        padding: '3px 6px', margin: '10px 0px 4px 0px',
        stretch: 'horizontal'
    });
}

var panel_side = ui.Panel(
    [
        ui.Label('Controles', {
            fontWeight: 'bold', fontSize: '14px', color: '#1a237e',
            margin: '4px 0px 6px 0px'
        }),

        // ── Col.11 ──
        sectionLabel('Col. 11', '#1b5e20'),
        ui.Label('Versão:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' }),
        sel_version,
        ui.Label('Bacia:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' }),
        sel_bacia,

        // ── Pós-classificação ──
        sectionLabel('Pós-class  ◀', '#1a237e'),
        ui.Label('Versão pós-class:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' }),
        sel_ver_pos,
        ui.Label('Nº classes:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' }),
        sel_num_class,
        ui.Label('Filtros (ordem de aplicação):', {
            fontSize: '11px', color: '#555', fontStyle: 'italic', margin: '6px 0px 2px 0px'
        }),
        cb_gap_fill,
        cb_temporalN,
        cb_temporalA,
        panel_janela,
        cb_spatial_int,
        cb_frequency,
        cb_spatial_all,

        // ── Série temporal do pixel ──
        sectionLabel('Série temporal do pixel', '#37474f'),
        chartPixelPanel
    ],
    ui.Panel.Layout.Flow('vertical'),
    {
        width:           '300px',
        padding:         '8px',
        backgroundColor: '#fafafa',
        border:          '1px solid #ccc'
    }
);

// ─── Layout principal ─────────────────────────────────────────────────────────
var panel_slider = ui.Panel(
    [
        ui.Label('Ano:', { fontWeight: 'bold', fontSize: '12px', margin: '6px 4px 6px 12px' }),
        lbl_ano_val,
        slider_year
    ],
    ui.Panel.Layout.Flow('horizontal'),
    {
        border: '1px solid #bbb', padding: '6px 8px',
        backgroundColor: '#e8e8e8', stretch: 'horizontal'
    }
);

var panel_maps = ui.Panel(
    [splitPanel],
    ui.Panel.Layout.Flow('vertical', true),
    { stretch: 'both' }
);

Map_esq.onClick(onMapClick);
Map_dir.onClick(onMapClick);

var panel_content = ui.Panel(
    [panel_maps, panel_slider],
    ui.Panel.Layout.Flow('vertical'),
    { stretch: 'both' }
);

var panel_main = ui.Panel(
    [panel_side, panel_content],
    ui.Panel.Layout.Flow('horizontal'),
    { stretch: 'both' }
);

ui.root.widgets().reset([panel_main]);
ui.root.setLayout(ui.Panel.Layout.Flow('vertical'));

// ─── Carga inicial ────────────────────────────────────────────────────────────
atualizar();
