var palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = palettes.get('brazil');

// Cópia da paleta com classe 13 substituída: preto → verde claro
var palette_vis = palette.slice(0);
palette_vis[13] = '#BEDC9C';

// ─── Visualização ─────────────────────────────────────────────────────────────
var visualizar = {
    visclass:  { min: 0, max: 75, palette: palette_vis, format: 'png' },
    visMosaic: { min: 300, max: 2100, bands: ['red_median', 'green_median', 'blue_median'] }
};

// ─── Parâmetros ───────────────────────────────────────────────────────────────
var param = {
    // Coleções anteriores usadas como fundo (Map71–Map100: single-image; Map110: IC → carregado como imgCol11)
    'colecoes_ant': {
        'Map71':  'projects/mapbiomas-public/assets/brazil/lulc/collection7_1/mapbiomas_collection71_integration_v1',
        'Map80':  'projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1',
        'Map90':  'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'Map100': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
        'Map110': 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-11/INTEGRATION/classification-ft',
    },
    col11_version: '0-4-12-spt-4',
    // Classificação inicial Sentinel (joined pré-filtros)
    assetclass: 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
    asset_filters: {
        'map_class': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/to_export',
        'Gap-fill':      'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Gap-fill',
        'Spatial Sieve': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Spatials_sieve',
        'Temporal A':    'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Temporal_Nat_Ant',
        'Frequency':     'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Frequency',
        'Temporal CC':   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/TemporalbyCC',
        'correction_integ': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/correcoes',
        'Class. Final':  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/toExport',
    },
    asset_mosaic_sentinelp2: 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',
    asset_mosaic_sentinelp1: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
    assetBacia: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    bandas:     ['red', 'green', 'blue', 'nir', 'swir1', 'swir2'],
    yearMin:    2016,
    yearMax:    2025,
    LAYERS:     ['Classificação', 'Gap-fill', 'Spatial Sieve', 'Temporal A', 'Frequency', 'Temporal CC', 'correction_integ', 'Class. Final', 'map_class'],
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
    versions:     ['5', '7'],
    numero_class: [7],
    assetBiomas:  'projects/mapbiomas-workspace/AUXILIAR/bioma_2025_e250k_5kbuffer'
};

// ─── Estado ───────────────────────────────────────────────────────────────────
var year_show = 2025;

// Estado independente por mapa; mutado pelos widgets de cada bloco
var esq = { layer: 'map_class', version: '7', numclass: 7 };
var dir = { layer: 'Gap-fill',      version: '5', numclass: 7 };
var colecao_fundo = 'Map110';  // coleção de fundo do mapa esquerdo (Camada 1)

// bacias disponíveis e quais estão selecionadas
var all_basins = [
    '765', '7544', '7541', '7411', '746', '7591',
    '7592', '761111', '761112', '7612', '7613', '7614',
    '7615', '771', '7712', '772', '7721', '773', '7741',
    '7754', '7761', '7764', '7691', '7581', '7625', '7584',
    '751', '752', '7616', '745', '7424', '7618', '7561',
    '755', '7617', '7564', '7422', '76116', '7671', '757',
    '766', '753', '764', '7619', '7443', '7438', '763',
    '7622', '7746'
];
var basins_selected = {};
(function() {
    all_basins.forEach(function(b) { basins_selected[b] = true; });
})();

function getSelectedBasins() {
    return all_basins.filter(function(b) { return basins_selected[b]; });
}

// ─── Assets base ──────────────────────────────────────────────────────────────
var shp_bacias_all = ee.FeatureCollection(param.assetBacia)
    .map(function(f) { return f.set('id_cod', 1); });

var shp_caatinga = ee.FeatureCollection(param.assetBiomas)
    .filter(ee.Filter.eq('Bioma', 'Caatinga'));
var borda_caatinga = ee.Image().byte()
    .paint(shp_caatinga, 1, 2)
    .visualize({ palette: ['FF0000'], opacity: 0.9 });

var ic_class  = ee.ImageCollection(param.assetclass);

// Col11: IC → carregado como mosaic estático (ee.Image() falha em IC path)
var imgCol11 = ee.ImageCollection(param.colecoes_ant['Map110'])
    .filter(ee.Filter.eq('version', param.col11_version))
    .mosaic();

// ─── Mapas ────────────────────────────────────────────────────────────────────
var Map_esq = ui.Map({ style: { border: '2px solid #1a237e' } });
var Map_dir = ui.Map({ style: { border: '2px solid #1b5e20', stretch: 'both' } });
Map_esq.setOptions('SATELLITE');
// Map_dir.setOptions('SATELLITE');

var linker = ui.Map.Linker([Map_esq, Map_dir]);
var splitPanel = ui.SplitPanel({
    firstPanel:  linker.get(0),
    secondPanel: linker.get(1),
    orientation: 'horizontal',
    wipe:        true,
    style:       { stretch: 'both' }
});

var _gen = 0;
var _primeiraVez = true;
var img_esq_allbands = null;
var img_dir_allbands = null;

// ─── Nomes das classes ────────────────────────────────────────────────────────
var classNames = {
    3: 'Floresta', 4: 'Savana', 12: 'Campestre', 13: 'Floresta Ciliar',
    15: 'Pastagem', 19: 'Lavoura', 21: 'Mos. Uso',
    25: 'Urb./Solo Exp.', 29: 'Afloramento', 33: 'Água', 36: 'Perene'
};

// ─── Série temporal do pixel ──────────────────────────────────────────────────
var chartPixelPanel_esq = ui.Panel({
    style: { stretch: 'horizontal', height: '100px', padding: '2px 4px',
             backgroundColor: '#f0f4ff', border: '1px solid #9fa8da' }
});
chartPixelPanel_esq.add(ui.Label('Clique em um pixel para ver a série do mapa esquerdo.',
    { color: '#555', fontSize: '10px' }));

var chartPixelPanel_dir = ui.Panel({
    style: { stretch: 'horizontal', height: '100px', padding: '2px 4px',
             backgroundColor: '#f1f8f1', border: '1px solid #a5d6a7' }
});
chartPixelPanel_dir.add(ui.Label('Clique em um pixel para ver a série do mapa direito.',
    { color: '#555', fontSize: '10px' }));

function buildPixelChart(panel, imgAllBands, coords, sideLabel) {
    if (!imgAllBands) {
        panel.clear();
        panel.add(ui.Label('⚠️ Aguarde o carregamento.', { color: 'orange' }));
        return;
    }
    panel.clear();
    panel.add(ui.Label('⏳ Carregando ' + sideLabel + '...', { color: 'gray', fontSize: '11px' }));

    var point = ee.Geometry.Point([coords.lon, coords.lat]);
    imgAllBands.reduceRegion({
        reducer: ee.Reducer.first(), geometry: point, scale: 10, maxPixels: 1e6
    }).evaluate(function(vals) {
        panel.clear();
        if (!vals) {
            panel.add(ui.Label('⚠️ Sem dado neste pixel (' + sideLabel + ').', { color: 'red' }));
            return;
        }
        var years = [];
        for (var y = param.yearMin; y <= param.yearMax; y++) { years.push(y); }
        var header = ['Ano', 'Classe',
                      { role: 'style', type: 'string' },
                      { role: 'tooltip', type: 'string', p: { html: true } }];
        var rows = [header];
        years.forEach(function(ano) {
            var banda = 'classification_' + ano;
            var cl    = vals[banda];
            var ci    = (cl !== null && cl !== undefined) ? parseInt(cl) : 0;
            var cor   = (ci > 0 && palette[ci]) ? palette[ci] : '#e0e0e0';
            var nome  = classNames[ci] || ('Classe ' + ci);
            rows.push([ano, 1,
                'point {size: 3; fill-color: ' + cor + '; stroke-color: ' + cor + '}',
                '<b>' + ano + '</b><br/>' + nome + ' (' + ci + ')']);
        });
        panel.add(ui.Label(
            sideLabel + ' | ' + coords.lat.toFixed(4) + ', ' + coords.lon.toFixed(4) +
            ' | bacias: ' + getSelectedBasins().length,
            { fontSize: '9px', color: '#444', margin: '0px 0 1px 2px' }));
        var chart = ui.Chart(rows).setChartType('ScatterChart').setOptions({
            title: '',
            hAxis: { format: '####', textStyle: { fontSize: 7 }, gridlines: { count: 5 },
                     viewWindow: { min: param.yearMin, max: param.yearMax } },
            vAxis: { viewWindow: { min: 0, max: 2 }, ticks: [], gridlines: { count: 0 },
                     baselineColor: 'transparent' },
            legend: { position: 'none' }, tooltip: { isHtml: true },
            chartArea: { width: '94%', height: '50%' }
        });
        chart.style().set({ stretch: 'horizontal', height: '75px' });
        panel.add(chart);
    });
}

function onMapClick(coords) {
    buildPixelChart(chartPixelPanel_esq, img_esq_allbands, coords, '◀ Fundo');
    buildPixelChart(chartPixelPanel_dir, img_dir_allbands, coords, 'Frente ▶');
}

// ─── Helpers de carregamento ──────────────────────────────────────────────────
function filterByVersion(ic, version_str) {
    return ic.filter(ee.Filter.eq('version', parseInt(version_str, 10)));
}

function buildCorrecoesIc(version_str) {
    return ee.ImageCollection(param.asset_filters['Corr. Pontuais'])
        .map(function(img) { return img.toUint8().toShort(); });
}

function addPosClassLayerToMap(mapObj, state_obj, banda, mask_bacia, my_gen, sel_list, is_all, onDone) {
    var isCC   = (state_obj.layer === 'Temporal CC' || state_obj.layer === 'Estabilidade' || state_obj.layer === 'Corr. Pontuais' || state_obj.layer === 'Class. Final' || state_obj.layer === 'map_class');
    var idProp = 'id_bacias';
    var ic;
    if (state_obj.layer === 'Corr. Pontuais') {
        ic = buildCorrecoesIc(state_obj.version);
        if (!is_all) { ic = ic.filter(ee.Filter.inList('id_bacias', sel_list)); }
    } else {
        ic = ee.ImageCollection(param.asset_filters[state_obj.layer])
            .filter(ee.Filter.eq('version', parseInt(state_obj.version, 10)));
        
        if (!is_all) {
            ic = ic.filter(ee.Filter.inList(idProp, sel_list));
        }
        print("Layer ==> " + state_obj.layer, ic);
    }

    var label = state_obj.layer + ' v' + state_obj.version + (isCC ? '' : ' nc' + state_obj.numclass);

    ic.size().evaluate(function(n) {
        if (_gen !== my_gen) return;
        if (n > 0) {
            mapObj.addLayer(ic.select(banda).mosaic().updateMask(mask_bacia),
                            visualizar.visclass, label, true);
        } else {
            print('Aviso: ' + state_obj.layer +
                  ' sem dados (v=' + state_obj.version + ' nc=' + state_obj.numclass + ')');
        }
        if (onDone) onDone();
    });
}

// ─── Mapa de nomes legíveis das coleções ──────────────────────────────────────
var colNames   = { 'Map71': 'Col7.1', 'Map80': 'Col8', 'Map90': 'Col9', 'Map100': 'Col10', 'Map110': 'Col11' };
var colMaxYear = { 'Map71': 2022,    'Map80': 2023,   'Map90': 2024,   'Map100': 2024,    'Map110': 2025 };

// ─── Cabeçalhos dinâmicos ─────────────────────────────────────────────────────
var lbl_header_esq = ui.Label('', {
    fontWeight: 'bold', fontSize: '13px', color: '#ffffff',
    backgroundColor: '#1a237ecc', padding: '3px 8px', margin: '4px'
});
var lbl_header_dir = ui.Label('', {
    fontWeight: 'bold', fontSize: '13px', color: '#ffffff',
    backgroundColor: '#1b5e20cc', padding: '3px 8px', margin: '4px'
});

function headerText(side, st) {
    if (st.layer === 'Classificação') {
        return side === 'esq'
            ? '◀ ' + (colNames[colecao_fundo] || colecao_fundo) + ' | Col.11 v' + st.version
            : 'Col. 11 v' + st.version + ' ▶';
    }
    var isCC = (st.layer === 'Temporal CC' || st.layer === 'Estabilidade' || st.layer === 'Corr. Pontuais' || st.layer === 'Class. Final' || st.layer === 'map_class');
    var txt = st.layer + ' v' + st.version + (isCC ? '' : ' nc' + st.numclass);
    return side === 'esq' ? '◀ ' + txt : txt + ' ▶';
}

function updateHeaders() {
    lbl_header_esq.setValue(headerText('esq', esq));
    lbl_header_dir.setValue(headerText('dir', dir));
}

Map_esq.add(ui.Panel([lbl_header_esq], null, { position: 'top-left',  padding: '0px', margin: '0px' }));
Map_dir.add(ui.Panel([lbl_header_dir], null, { position: 'top-right', padding: '0px', margin: '0px' }));

// ─── Função de atualização ────────────────────────────────────────────────────
function atualizar() {
    _gen++;
    var my_gen   = _gen;
    var banda    = 'classification_' + year_show;
    var year_mos = year_show;

    var sel_list = getSelectedBasins();
    var is_all   = (sel_list.length === all_basins.length);

    if (sel_list.length === 0) {
        print('⚠️ Nenhuma bacia selecionada.');
        lbl_bacia_count.setValue('0 bacia(s) selecionada(s)');
        return;
    }

    var shp_sel = is_all
        ? shp_bacias_all
        : shp_bacias_all.filter(ee.Filter.inList('nunivotto4', sel_list));

    var mask_bacia = shp_sel
        .map(function(f) { return f.set('id_cod', 1); })
        .reduceToImage(['id_cod'], ee.Reducer.first());

    // Mosaico Sentinel: p1 para < 2024, p2 para >= 2024
    var mosaicIC = year_mos < 2024
        ? ee.ImageCollection(param.asset_mosaic_sentinelp1)
        : ee.ImageCollection(param.asset_mosaic_sentinelp2);
    var mosaic_year = mosaicIC
        .filterBounds(shp_sel.geometry())
        .filter(ee.Filter.eq('year', year_mos))
        .mosaic();

    var bordas = ee.Image().byte()
        .paint(shp_sel, 1, 1)
        .visualize({ palette: 'FF0000', opacity: 0.8 });

    Map_esq.layers().reset([]);
    Map_dir.layers().reset([]);

    // Camadas fixas sempre no topo (bordas vermelhas)
    var addEsqTop = function() {
        Map_esq.addLayer(shp_sel,         {},                    'Bacias _shp',           false);
        Map_esq.addLayer(bordas,          {},                    'Bacias',                true);
        Map_esq.addLayer(borda_caatinga,  {},                    'Limite Caatinga',       true);
        Map_esq.addLayer(shp_bacias_all,  { color: '00000000' }, 'FC Bacias (inspector)', false);
    };
    var addDirTop = function() {
        Map_dir.addLayer(bordas,         {},                    'Bacias',                true);
        Map_dir.addLayer(borda_caatinga, {},                    'Limite Caatinga',       true);
        Map_dir.addLayer(shp_bacias_all, { color: '00000000' }, 'FC Bacias (inspector)', false);
    };

    // ── Mapa de Fundo (esquerdo) ──────────────────────────────────────────────
    Map_esq.addLayer(mosaic_year, visualizar.visMosaic, 'Mosaico ' + year_show, true);
    // Camada 1: coleção anterior selecionável (Map110 é IC, demais são single-image)
    var map_fundo = colecao_fundo === 'Map110'
        ? imgCol11
        : ee.Image(param.colecoes_ant[colecao_fundo]);
    var bandaFundo = 'classification_' + Math.min(year_show, colMaxYear[colecao_fundo] || year_show);
    Map_esq.addLayer(
        map_fundo.updateMask(mask_bacia).select(bandaFundo),
        visualizar.visclass, (colNames[colecao_fundo] || colecao_fundo) + ' ' + year_show, true
    );
    // Camada 2: Classificação sentinel ou filtro pós-class
    if (esq.layer === 'Classificação') {
        var ic_esq = filterByVersion(ic_class, esq.version);
        if (!is_all) ic_esq = ic_esq.filter(ee.Filter.inList('id_bacias', sel_list));
        Map_esq.addLayer(
            ic_esq.select(banda).mosaic().updateMask(mask_bacia),
            visualizar.visclass, 'Class. v' + esq.version + ' ' + year_show, true
        );
        addEsqTop();
    } else {
        addPosClassLayerToMap(Map_esq, esq, banda, mask_bacia, my_gen, sel_list, is_all, addEsqTop);
    }

    // ── Mapa de Frente (direito) ──────────────────────────────────────────────
    Map_dir.addLayer(mosaic_year, visualizar.visMosaic, 'Mosaico ' + year_show, true);
    var ic_ref = filterByVersion(ic_class, dir.version);
    if (!is_all) ic_ref = ic_ref.filter(ee.Filter.inList('id_bacias', sel_list));
    if (dir.layer === 'Classificação') {
        Map_dir.addLayer(
            ic_ref.select(banda).mosaic().updateMask(mask_bacia),
            visualizar.visclass, 'Class. v' + dir.version + ' ' + year_show, true
        );
        addDirTop();
    } else {
        addPosClassLayerToMap(Map_dir, dir, banda, mask_bacia, my_gen, sel_list, is_all, addDirTop);
    }

    // série temporal — mapa esquerdo
    if (esq.layer === 'Classificação') {
        var ic_esq_chart = filterByVersion(ic_class, esq.version);
        if (!is_all) ic_esq_chart = ic_esq_chart.filter(ee.Filter.inList('id_bacias', sel_list));
        img_esq_allbands = ic_esq_chart.mosaic();
    } else {
        var isCC_esq = (esq.layer === 'Temporal CC' || esq.layer === 'Estabilidade' || esq.layer === 'Corr. Pontuais' || esq.layer === 'Class. Final' || esq.layer === 'map_class');
        var idProp_esq = 'id_bacias';
        var ic_chart_esq;
        if (esq.layer === 'Corr. Pontuais') {
            ic_chart_esq = buildCorrecoesIc(esq.version);
            if (!is_all) { ic_chart_esq = ic_chart_esq.filter(ee.Filter.inList('id_bacia', sel_list)); }
        } else {
            ic_chart_esq = ee.ImageCollection(param.asset_filters[esq.layer])
                .filter(ee.Filter.eq('version', parseInt(esq.version, 10)));
            if (!isCC_esq) {
                ic_chart_esq = ic_chart_esq.filter(ee.Filter.eq('num_class', esq.numclass));
            }
            if (!is_all) {
                ic_chart_esq = ic_chart_esq.filter(
                    ee.Filter.inList(idProp_esq, sel_list));
            }
        }
        img_esq_allbands = ic_chart_esq.mosaic();
    }

    // série temporal — mapa direito
    if (dir.layer === 'Classificação') {
        img_dir_allbands = ic_ref.mosaic();
    } else {
        var isCC_dir = (dir.layer === 'Temporal CC' || dir.layer === 'Estabilidade' || dir.layer === 'Corr. Pontuais' || dir.layer === 'Class. Final' || dir.layer === 'map_class');
        var idProp_dir = 'id_bacias';
        var ic_chart;
        if (dir.layer === 'Corr. Pontuais') {
            ic_chart = buildCorrecoesIc(dir.version);
            if (!is_all) { ic_chart = ic_chart.filter(ee.Filter.inList('id_bacia', sel_list)); }
        } else {
            ic_chart = ee.ImageCollection(param.asset_filters[dir.layer])
                .filter(ee.Filter.eq('version', parseInt(dir.version, 10)));
            if (!isCC_dir) {
                ic_chart = ic_chart.filter(ee.Filter.eq('num_class', dir.numclass));
            }
            if (!is_all) {
                ic_chart = ic_chart.filter(
                    ee.Filter.inList(idProp_dir, sel_list));
            }
        }
        img_dir_allbands = ic_chart.mosaic();
    }

    if (_primeiraVez) {
        if (is_all) { Map_dir.setCenter(-39.259, -9.092, 7); }
        else        { Map_dir.centerObject(shp_sel, 9); }
        _primeiraVez = false;
    }
    lbl_ano_val.setValue(String(year_show));
    lbl_bacia_count.setValue(sel_list.length + ' bacia(s) selecionada(s)');
    updateHeaders();
}

// ─── Helpers de UI ────────────────────────────────────────────────────────────
function sectionLabel(txt, color) {
    return ui.Label(txt, {
        fontWeight: 'bold', fontSize: '11px', color: '#ffffff',
        backgroundColor: color || '#37474f',
        padding: '3px 6px', margin: '8px 0px 4px 0px', stretch: 'horizontal'
    });
}

// ─── Bloco de controles por mapa ──────────────────────────────────────────────
function makeSidePanel(side, state_obj, color, title) {
    var sel_layer = ui.Select({
        items:       param.LAYERS,
        value:       state_obj.layer,
        placeholder: 'Camada...',
        style:       { stretch: 'horizontal', margin: '2px 0px' }
    });

    var lbl_ver = ui.Label('Versão:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' });
    var sel_ver = ui.Select({
        items:       param.versions,
        value:       state_obj.version,
        placeholder: 'Versão...',
        style:       { stretch: 'horizontal', margin: '2px 0px' }
    });

    var lbl_nc = ui.Label('Nº de classes:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' });
    var sel_nc = ui.Select({
        items:       param.numero_class.map(String),
        value:       String(state_obj.numclass),
        placeholder: 'N classes...',
        style:       { stretch: 'horizontal', margin: '2px 0px' }
    });

    function refreshVis(layer) {
        var isClass = (layer === 'Classificação');
        lbl_nc.style().set('shown', !isClass);
        sel_nc.style().set('shown', !isClass);
    }

    refreshVis(state_obj.layer);

    sel_layer.onChange(function(v) { state_obj.layer   = v; refreshVis(v); });
    sel_ver.onChange(  function(v) { state_obj.version  = v; });
    sel_nc.onChange(   function(v) { state_obj.numclass = parseInt(v, 10); });

    var camadaLabel;
    if (side === 'esq') {
        var sel_colecao = ui.Select({
            items:       Object.keys(param.colecoes_ant),
            value:       colecao_fundo,
            placeholder: 'Coleção fundo...',
            onChange:    function(v) { colecao_fundo = v; },
            style:       { stretch: 'horizontal', margin: '2px 0px' }
        });
        camadaLabel = [
            ui.Label('Camada 1 (fundo):', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' }),
            sel_colecao,
            ui.Label('Camada 2:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' })
        ];
    } else {
        camadaLabel = [ui.Label('Camada:', { fontSize: '11px', color: '#555', margin: '4px 0px 1px 0px' })];
    }

    return ui.Panel(
        [sectionLabel(title, color)]
            .concat(camadaLabel)
            .concat([sel_layer, lbl_ver, sel_ver, lbl_nc, sel_nc]),
        ui.Panel.Layout.Flow('vertical'),
        { padding: '0px' }
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
slider_year.onChange(function(v) { year_show = Math.round(v); lbl_ano_val.setValue(String(year_show)); atualizar(); });

// ─── Botão Aplicar ────────────────────────────────────────────────────────────
var btn_apply = ui.Button({
    label:   '✔  Aplicar',
    onClick: function() { atualizar(); },
    style: {
        stretch: 'horizontal', fontWeight: 'bold', fontSize: '13px',
        color: '#ffffff', backgroundColor: '#1565c0',
        margin: '4px 0px 8px 0px', padding: '5px'
    }
});

// ─── Checkboxes de bacias ─────────────────────────────────────────────────────
var basin_checkboxes = {};

function makeBasinRows() {
    var rows = [];
    var row_widgets = [];

    all_basins.forEach(function(bacia) {
        (function(b) {
            var cb = ui.Checkbox({
                label:    b,
                value:    basins_selected[b],
                onChange: function(checked) { basins_selected[b] = checked; },
                style:    { margin: '1px 2px', fontSize: '10px', width: '53px' }
            });
            basin_checkboxes[b] = cb;
            row_widgets.push(cb);

            if (row_widgets.length === 5) {
                rows.push(ui.Panel(
                    row_widgets.slice(),
                    ui.Panel.Layout.Flow('horizontal'),
                    { padding: '0px', margin: '0px' }
                ));
                row_widgets = [];
            }
        })(bacia);
    });

    if (row_widgets.length > 0) {
        rows.push(ui.Panel(
            row_widgets,
            ui.Panel.Layout.Flow('horizontal'),
            { padding: '0px', margin: '0px' }
        ));
    }
    return rows;
}

function setAllBasins(val) {
    all_basins.forEach(function(b) {
        basins_selected[b] = val;
        basin_checkboxes[b].setValue(val);
    });
}

var lbl_bacia_count = ui.Label('49 bacia(s) selecionada(s)', {
    fontSize: '10px', color: '#666', fontStyle: 'italic', margin: '2px 0px 4px 0px'
});

var btn_all_b  = ui.Button({ label: 'Todas',  onClick: function() { setAllBasins(true);  }, style: { margin: '2px 3px 2px 0px', fontSize: '10px' } });
var btn_none_b = ui.Button({ label: 'Limpar', onClick: function() { setAllBasins(false); }, style: { margin: '2px 0px',          fontSize: '10px' } });

var panel_bacia_quick = ui.Panel(
    [btn_all_b, btn_none_b],
    ui.Panel.Layout.Flow('horizontal'),
    { padding: '0px', margin: '2px 0px 4px 0px' }
);

var basin_rows  = makeBasinRows();
var panel_bacias = ui.Panel(
    [sectionLabel('Bacias', '#37474f'), panel_bacia_quick, lbl_bacia_count].concat(basin_rows),
    ui.Panel.Layout.Flow('vertical'),
    { padding: '0px' }
);

// ─── Painel lateral ───────────────────────────────────────────────────────────
var panel_side = ui.Panel(
    [
        ui.Label('Controles', {
            fontWeight: 'bold', fontSize: '14px', color: '#1a237e',
            margin: '4px 0px 2px 0px'
        }),
        btn_apply,

        panel_bacias,

        makeSidePanel('esq', esq, '#1a237e', '◀ Mapa de Fundo'),
        makeSidePanel('dir', dir, '#1b5e20', 'Mapa de Frente ▶'),

        sectionLabel('◀ Série — Mapa de Fundo', '#1a237e'),
        chartPixelPanel_esq,
        sectionLabel('Série — Mapa de Frente ▶', '#1b5e20'),
        chartPixelPanel_dir
    ],
    ui.Panel.Layout.Flow('vertical'),
    { width: '300px', padding: '8px', backgroundColor: '#fafafa', border: '1px solid #ccc' }
);

// ─── Layout principal ─────────────────────────────────────────────────────────
var panel_slider = ui.Panel(
    [ui.Label('Ano:', { fontWeight: 'bold', fontSize: '12px', margin: '6px 4px 6px 12px' }),
     lbl_ano_val, slider_year],
    ui.Panel.Layout.Flow('horizontal'),
    { border: '1px solid #bbb', padding: '6px 8px', backgroundColor: '#e8e8e8', stretch: 'horizontal' }
);

var panel_maps    = ui.Panel([splitPanel], ui.Panel.Layout.Flow('vertical', true), { stretch: 'both' });
var panel_content = ui.Panel([panel_maps, panel_slider], ui.Panel.Layout.Flow('vertical'), { stretch: 'both' });
var panel_main    = ui.Panel([panel_side, panel_content], ui.Panel.Layout.Flow('horizontal'), { stretch: 'both' });

Map_esq.onClick(onMapClick);
Map_dir.onClick(onMapClick);

ui.root.widgets().reset([panel_main]);
ui.root.setLayout(ui.Panel.Layout.Flow('vertical'));

// ─── Carga inicial ────────────────────────────────────────────────────────────
atualizar();
