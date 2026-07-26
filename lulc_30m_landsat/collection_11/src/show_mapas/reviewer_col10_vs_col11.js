var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = palettes.get('brazil');

// ─── Parâmetros ───────────────────────────────────────────────────────────────
var param = {
    asset_caat_buffer: 'users/CartasSol/shapes/caatinga_buffer5km',
    asset_bacias:      'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    asset_map110:      'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-11/GENERAL/classification-caa',
    asset_map100:      'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    yearMin: 1985,
    yearMax: 2025,
};

// ─── Remap Col10 → nomenclatura Col11 ────────────────────────────────────────
var classMapB = [3,4,5,6,9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62,75];
var classNew  = [3,4,4,4,4,12,12,13,21,21,21,21,21,25,25,25,25,33,29,25,33,12,33,21,33,33,21,21,21,21,21,21,21,21,21,21,49,50,21,25];

// ─── Visualização ─────────────────────────────────────────────────────────────
var palettes    = require('users/mapbiomas/modules:Palettes.js');
var palette     = palettes.get('brazil');
var palette_vis = palette.slice(0);
palette_vis[13] = '#BEDC9C';
var visclass      = { min: 0, max: 75, palette: palette_vis, format: 'png' };
// 1=perda(red)  2=estável(gray)  3=ganho(blue)
var visChange     = { min: 1, max: 3, palette: ['FF0000', 'AAAAAA', '0000FF'], format: 'png' };


// ─── Assets base ──────────────────────────────────────────────────────────────
var shp_bacias = ee.FeatureCollection(param.asset_bacias);

var bioma5kbuf = ee.FeatureCollection(param.asset_caat_buffer)
                            .map(function(f) { return f.set('id_codigo', 1); });
var bioma5k_raster = bioma5kbuf.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0);
var borda_caatinga = ee.Image().byte()
    .paint(bioma5kbuf, 1, 2)
    .visualize({ palette: ['FF0000'], opacity: 0.9 });

var img_col10    = ee.Image(param.asset_map100).updateMask(bioma5k_raster);
var ic_col11     = ee.ImageCollection(param.asset_map110);


// ─── Estado ───────────────────────────────────────────────────────────────────
var year_show    = 2023;
var _primeiraVez = true;

// ─── Mapa ─────────────────────────────────────────────────────────────────────
var Map_view = ui.Map();
Map_view.setOptions('SATELLITE');
Map_view.drawingTools().setShown(false);

// ─── Camada de mudança por classe ─────────────────────────────────────────────
// Red=perda  Gray=estável  Blue=ganho
function buildChangeLayer(img_c10, img_c11, targetClass) {
    var in10 = img_c10.eq(targetClass);
    var in11 = img_c11.eq(targetClass);
    return ee.Image(0)
        .where(in10.and(in11.not()), 1)  // perda
        .where(in10.and(in11),       2)  // estável
        .where(in10.not().and(in11), 3)  // ganho
        .selfMask();
}

// ─── Atualizar mapa ───────────────────────────────────────────────────────────
function atualizar() {
    var banda      = 'classification_' + year_show;
    // col10 usa no máximo 2023 (último ano disponível na coleção 10)
    var yearCol10  = Math.min(year_show, 2023);
    var bandaCol10 = 'classification_' + yearCol10;

    // Col10 remapeado para nomenclatura col11
    var col10_yr = img_col10.select(bandaCol10)
                .remap(classMapB, classNew).rename('class');

    // Col11 final (já com todas as regras aplicadas)
    // filter primeiro para evitar imagens sem a banda (retornariam 0 bandas no mosaic)
    var col11_yr = ic_col11.filter(ee.Filter.eq('year', year_show))
                    .first().rename('class');
                    
    Map_view.layers().reset([]);

    // Adicionadas de baixo para cima: última camada = topo do painel + topo visual
    Map_view.addLayer(shp_bacias,
        { color: '888888', fillColor: '00000000' },
        'bacias_shp', false);    

    Map_view.addLayer(col10_yr, visclass, 'Collection 10 — ' + yearCol10, true);
    Map_view.addLayer(col11_yr, visclass, 'Collection 11 — ' + year_show, true);

    Map_view.addLayer(buildChangeLayer(col10_yr, col11_yr, 21), visChange,
        'change_use_cc21 — ' + year_show, false);

    Map_view.addLayer(buildChangeLayer(col10_yr, col11_yr, 4), visChange,
        'change_use_cc4 — ' + year_show, false);

    Map_view.addLayer(buildChangeLayer(col10_yr, col11_yr, 3), visChange,
        'change_use_cc3 — ' + year_show, false);

    Map_view.addLayer(borda_caatinga, {}, 'Limite Caatinga', true);

    if (_primeiraVez) {
        Map_view.setCenter(-39.259, -9.092, 7);
        _primeiraVez = false;
    }
    lbl_ano_val.setValue(String(year_show));
}

// ─── Helpers de UI ────────────────────────────────────────────────────────────
function sectionLabel(txt, color) {
    return ui.Label(txt, {
        fontWeight: 'bold', fontSize: '11px', color: '#ffffff',
        backgroundColor: color || '#37474f',
        padding: '3px 6px', margin: '8px 0px 4px 0px', stretch: 'horizontal'
    });
}

function legendRow(color, label) {
    return ui.Panel([
        ui.Label('', {
            backgroundColor: color, padding: '6px 14px',
            margin: '2px 6px 2px 2px', border: '1px solid #bbb'
        }),
        ui.Label(label, { fontSize: '11px', margin: '3px 0px', color: '#333' })
    ], ui.Panel.Layout.Flow('horizontal'), { padding: '0px', margin: '1px 0px' });
}

// ─── Slider de ano ────────────────────────────────────────────────────────────
var lbl_ano_val = ui.Label(String(year_show), {
    fontWeight: 'bold', fontSize: '15px', color: '#4a148c',
    margin: '4px 6px', width: '44px'
});
var slider_year = ui.Slider({
    min: param.yearMin, max: param.yearMax, value: year_show, step: 1,
    style: { stretch: 'horizontal', margin: '4px 4px' }
});
slider_year.onSlide( function(v) { year_show = Math.round(v); lbl_ano_val.setValue(String(year_show)); });
slider_year.onChange(function(v) { year_show = Math.round(v); atualizar(); });

var panel_slider = ui.Panel(
    [ui.Label('Ano:', { fontWeight: 'bold', fontSize: '12px', margin: '4px 4px' }),
     lbl_ano_val, slider_year],
    ui.Panel.Layout.Flow('horizontal'),
    { padding: '2px', margin: '2px 0px' }
);

// ─── Legenda das camadas de mudança ───────────────────────────────────────────
var panel_legend = ui.Panel([
    sectionLabel('Legenda — Camadas de Mudança', '#6a1b9a'),
    legendRow('#FF0000', 'Perda   — era a classe em Col10, não em Col11'),
    legendRow('#AAAAAA', 'Estável — classe em Col10 e Col11'),
    legendRow('#0000FF', 'Ganho   — não era em Col10, passou a ser em Col11'),
    ui.Label('Col10 remapeado para nomenclatura Col11',
        { fontSize: '10px', color: '#888', fontStyle: 'italic', margin: '4px 2px 2px 2px' }),
    sectionLabel('Legenda — Regras do Export Final', '#b71c1c'),
    legendRow('#FF6600', 'rule 0→21: pixel sem classe (0) → vira 21'),
    legendRow('#FFDD00', 'rule 24→21: Col10 classe 24 → força 21 no output'),
    legendRow(palette[29] || '#c9b99a', 'afloramento estável: blend da layer class 29'),
], ui.Panel.Layout.Flow('vertical'), { padding: '0px', margin: '0px' });

// ─── Descrição de camadas ──────────────────────────────────────────────────────
var panel_layers_info = ui.Panel([
    sectionLabel('Camadas (de cima p/ baixo)', '#455a64'),
    ui.Label('Limite Caatinga — borda vermelha', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
    ui.Label('Collection 11 — classificação final col11', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
    ui.Label('Collection 10 — remapeado → col11', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
    ui.Label('change_use_cc3  — mudanças classe 3 (Floresta)', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
    ui.Label('change_use_cc4  — mudanças classe 4 (Savana)', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
    ui.Label('change_use_cc21 — mudanças classe 21 (Mos. Uso)', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
    ui.Label('bacias_shp — shapefile das bacias', { fontSize: '10px', color: '#333', margin: '2px 2px' }),
], ui.Panel.Layout.Flow('vertical'), { padding: '0px', margin: '0px' });

// ─── Painel lateral ───────────────────────────────────────────────────────────
var panel_side = ui.Panel(
    [
        ui.Label('Col10 × Col11 — Revisor', {
            fontWeight: 'bold', fontSize: '14px', color: '#1a237e',
            margin: '4px 0px 6px 0px'
        }),
        sectionLabel('Selecionar Ano', '#37474f'),
        panel_slider,
        panel_legend,
        panel_layers_info,
    ],
    ui.Panel.Layout.Flow('vertical'),
    { width: '330px', padding: '8px', backgroundColor: '#fafafa', border: '1px solid #ccc' }
);

// ─── Layout principal ─────────────────────────────────────────────────────────
var panel_map  = ui.Panel([Map_view], ui.Panel.Layout.Flow('vertical'), { stretch: 'both' });
var panel_main = ui.Panel([panel_side, panel_map], ui.Panel.Layout.Flow('horizontal'), { stretch: 'both' });

ui.root.widgets().reset([panel_main]);
ui.root.setLayout(ui.Panel.Layout.Flow('vertical'));

// ─── Carga inicial ────────────────────────────────────────────────────────────
atualizar();
