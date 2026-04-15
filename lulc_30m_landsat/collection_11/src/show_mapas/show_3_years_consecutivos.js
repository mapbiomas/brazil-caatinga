var bloqueiaAtualizacaoGrafico = false;
var palettes = require('users/mapbiomas/modules:Palettes.js');

// ─── Visualização ─────────────────────────────────────────────────────────────
var vis = {
    visMosaic: { min: 0.012, max: 0.22, bands: ['red', 'green', 'blue'] },
    map_class: { min: 0, max: 69, palette: palettes.get('classification9') }
};

// ─── Parâmetros ───────────────────────────────────────────────────────────────
var param = {
    assetMap:           'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    asset_Map_max_year: 2023,
    assetclass:         'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
    asset_filters: {
        gap_fill:    'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill',
        temporalN:   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalNat',
        temporalA:   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/TemporalAnt',
        spatial_int: 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_int',
        frequency:   'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Frequency',
        spatial_all: 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_all'
    },
    assetIm:         'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    asset_bacias:    'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    pontos_accuracy: 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col4_points_w_edge_and_edited_v1',
    versions:         ['1', '2', '3', '4', '5'],
    numero_class:     [7, 10],
    version_posClase: [1, 2],
    nyears: [
        '1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
        '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
        '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
        '2015','2016','2017','2018','2019','2020','2021','2022','2023','2024',
        '2025'
    ]
};

// ─── Estado ──────────────────────────────────────────────────────────────────
var version_show      = '1';
var ver_posclass_show = param.version_posClase[0];   // 1
var num_class_show    = param.numero_class[0];        // 7
var janela_show       = 3;
var antes_show        = 'classificador';
var depois_show       = 'gap_fill';

// ─── Rótulos dos passos ───────────────────────────────────────────────────────
var stepLabels = {
    classificador: 'Classificador Col11',
    gap_fill:      'Gap-fill',
    temporalN:     'Temporal Nat',
    temporalA:     'Temporal Ant',
    spatial_int:   'Spatial int',
    frequency:     'Frequency',
    spatial_all:   'Spatial all'
};
var stepKeys  = ['classificador', 'gap_fill', 'temporalN', 'temporalA', 'spatial_int', 'frequency', 'spatial_all'];
var stepItems = stepKeys.map(function(k) { return { label: stepLabels[k], value: k }; });

// ─── Assets base ─────────────────────────────────────────────────────────────
var bacias         = ee.FeatureCollection(param.asset_bacias);
var mapbiomasCol10 = ee.Image(param.assetMap);
var mosaicEE       = ee.ImageCollection(param.assetIm);

// ─── Helper: IC filtrado por passo + bacia ────────────────────────────────────
function getStepIC(stepName, bacia_selected) {
    var ic;
    if (stepName === 'classificador') {
        ic = ee.ImageCollection(param.assetclass)
               .filter(ee.Filter.stringContains('system:index', 'fm-v_' + version_show));
    } else {
        ic = ee.ImageCollection(param.asset_filters[stepName])
               .filter(ee.Filter.eq('version', ver_posclass_show))
               .filter(ee.Filter.eq('num_class', num_class_show));
        if (stepName === 'temporalN' || stepName === 'temporalA') {
            ic = ic.filter(ee.Filter.eq('janela', janela_show));
        }
    }
    if (bacia_selected) {
        ic = ic.filter(ee.Filter.eq('id_bacias', bacia_selected));
    }
    return ic;
}

// ─── Interface ────────────────────────────────────────────────────────────────
ui.root.clear();

var panel = ui.Panel({ style: { width: '340px', stretch: 'vertical', padding: '8px' } });
panel.add(ui.Label('Inspeção de Bacias — Col11', { fontWeight: 'bold', fontSize: '15px', color: '#1a237e' }));

function sectionLbl(txt, color) {
    return ui.Label(txt, {
        fontWeight: 'bold', fontSize: '11px', color: '#ffffff',
        backgroundColor: color || '#37474f',
        padding: '3px 6px', margin: '8px 0 3px 0', stretch: 'horizontal'
    });
}

// ── Bacia e Ano ──
panel.add(sectionLbl('Bacia e Ano', '#37474f'));
panel.add(ui.Label('Bacia:', { fontSize: '11px', color: '#555' }));
var selectBacia = ui.Select({ placeholder: 'Carregando...', style: { stretch: 'horizontal' } });
panel.add(selectBacia);

var lbl_ano = ui.Label('2024', { fontWeight: 'bold', fontSize: '14px', color: '#4a148c', margin: '2px 0' });
var sliderAno = ui.Slider({ min: 1985, max: 2025, value: 2024, step: 1, style: { stretch: 'horizontal' } });
panel.add(ui.Panel(
    [ui.Label('Ano:', { fontSize: '11px', color: '#555', margin: '4px 6px 0 0' }), lbl_ano],
    ui.Panel.Layout.Flow('horizontal')
));
panel.add(sliderAno);

// ── Col11 Classificador ──
panel.add(sectionLbl('Col. 11', '#1b5e20'));
panel.add(ui.Label('Versão (classificador):', { fontSize: '11px', color: '#555' }));
var sel_version = ui.Select({
    items: param.versions, value: version_show,
    onChange: function(v) { version_show = v; atualizarAnoVisualizado(); },
    style: { stretch: 'horizontal', margin: '2px 0' }
});
panel.add(sel_version);

// ── Pós-class ──
panel.add(sectionLbl('Pós-classificação', '#1a237e'));
panel.add(ui.Label('Versão pós-class:', { fontSize: '11px', color: '#555' }));
var sel_ver_pos = ui.Select({
    items: param.version_posClase.map(String), value: String(ver_posclass_show),
    onChange: function(v) { ver_posclass_show = parseInt(v, 10); atualizarAnoVisualizado(); },
    style: { stretch: 'horizontal', margin: '2px 0' }
});
panel.add(sel_ver_pos);

panel.add(ui.Label('Nº classes:', { fontSize: '11px', color: '#555' }));
var sel_num_class = ui.Select({
    items: param.numero_class.map(String), value: String(num_class_show),
    onChange: function(v) { num_class_show = parseInt(v, 10); atualizarAnoVisualizado(); },
    style: { stretch: 'horizontal', margin: '2px 0' }
});
panel.add(sel_num_class);

var sel_janela_widget = ui.Select({
    items: ['3', '4', '5'], value: String(janela_show),
    onChange: function(v) { janela_show = parseInt(v, 10); atualizarAnoVisualizado(); },
    style: { stretch: 'horizontal', margin: '2px 0' }
});
var panel_janela = ui.Panel(
    [ui.Label('Janela temporal:', { fontSize: '11px', color: '#555' }), sel_janela_widget],
    ui.Panel.Layout.Flow('vertical'),
    { shown: false, padding: '0' }
);
panel.add(panel_janela);

function updateJanelaVisibility() {
    var show = (antes_show === 'temporalN' || antes_show === 'temporalA' ||
                depois_show === 'temporalN' || depois_show === 'temporalA');
    panel_janela.style().set('shown', show);
}

// ── Seleção de camadas ──
panel.add(sectionLbl('Camadas (Antes / Depois)', '#455a64'));
panel.add(ui.Label('◀ Antes (camada inferior):', { fontSize: '11px', color: '#555' }));
var sel_antes = ui.Select({
    items: stepItems, value: antes_show,
    onChange: function(v) { antes_show = v; updateJanelaVisibility(); atualizarAnoVisualizado(); },
    style: { stretch: 'horizontal', margin: '2px 0' }
});
panel.add(sel_antes);

panel.add(ui.Label('▶ Depois (camada superior):', { fontSize: '11px', color: '#555' }));
var sel_depois = ui.Select({
    items: stepItems, value: depois_show,
    onChange: function(v) { depois_show = v; updateJanelaVisibility(); atualizarAnoVisualizado(); },
    style: { stretch: 'horizontal', margin: '2px 0' }
});
panel.add(sel_depois);

// ── Marcador de bacias ──
panel.add(sectionLbl('Marcador', '#546e7a'));
var marcarBtn = ui.Button({
    label: '✔️ Marcar / Desmarcar bacia',
    style: { stretch: 'horizontal', backgroundColor: '#ffd1dc' },
    onClick: marcarOuDesmarcarBacia
});
panel.add(marcarBtn);
var listaMarcadas = [];
var marcadasPanel = ui.Panel([ui.Label('Bacias marcadas:', { fontSize: '11px' })]);
panel.add(marcadasPanel);

// ── Gráficos ──
var chartPanel  = ui.Panel();
panel.add(chartPanel);
var panelGrafico = ui.Panel({ style: { margin: '4px 0' } });

// ── Comparação de versões ──
var colecaoInputs = [];
var classeInput   = ui.Textbox({ placeholder: 'Ex: 15 (Pastagem)' });
var painelColecoes = ui.Panel({ layout: ui.Panel.Layout.flow('vertical') });
painelColecoes.add(ui.Label('Coleções:', { fontSize: '11px' }));
painelColecoes.add(ui.Button({
    label: '➕ Adicionar Coleção',
    onClick: function() {
        var input = ui.Textbox({ placeholder: 'ID da ImageCollection' });
        colecaoInputs.push(input);
        painelColecoes.add(input);
    }
}));
var painelComparacao = ui.Panel({ style: { stretch: 'horizontal', padding: '6px', border: '1px solid lightgray', margin: '6px 0' } });
painelComparacao.add(ui.Label('Comparação de coleções por classe', { fontWeight: 'bold', fontSize: '11px' }));
painelComparacao.add(painelColecoes);
painelComparacao.add(ui.Label('Classe (ex: 15):', { fontSize: '11px' }));
painelComparacao.add(classeInput);
painelComparacao.add(ui.Button({
    label: '📊 Gerar Gráfico Comparativo',
    style: { stretch: 'horizontal', backgroundColor: '#d0f0d0' },
    onClick: gerarGraficoComparativo
}));
panel.add(painelComparacao);
panel.add(panelGrafico);

// ─── Mapas ───────────────────────────────────────────────────────────────────
var controlsVis = { layerList: true, zoomControl: false, mapTypeControl: false };
var lblStyle    = { fontWeight: 'bold', textAlign: 'center' };

var mapAnt   = ui.Map();
var mapAtual = ui.Map();
var mapPost  = ui.Map();
ui.Map.Linker([mapAnt, mapAtual, mapPost]);
mapAnt.setControlVisibility(controlsVis);
mapAtual.setControlVisibility(controlsVis);
mapPost.setControlVisibility(controlsVis);

var tituloAnt   = ui.Label('Anterior:', lblStyle);
var tituloAtual = ui.Label('Selecionado:', lblStyle);
var tituloPost  = ui.Label('Posterior:', lblStyle);

var mapasHorizontal = ui.Panel({
    widgets: [
        ui.Panel({ widgets: [tituloAnt,   mapAnt],   layout: ui.Panel.Layout.Flow('vertical'), style: { stretch: 'both' } }),
        ui.Panel({ widgets: [tituloAtual, mapAtual], layout: ui.Panel.Layout.Flow('vertical'), style: { stretch: 'both' } }),
        ui.Panel({ widgets: [tituloPost,  mapPost],  layout: ui.Panel.Layout.Flow('vertical'), style: { stretch: 'both' } })
    ],
    layout: ui.Panel.Layout.Flow('horizontal'),
    style:  { stretch: 'both' }
});

var painelCompleto = ui.Panel({
    widgets: [panel, mapasHorizontal],
    layout:  ui.Panel.Layout.Flow('horizontal'),
    style:   { stretch: 'both' }
});
ui.root.add(painelCompleto);

// ─── Preenchimento de bacias ──────────────────────────────────────────────────
bacias.aggregate_array('nunivotto4').evaluate(function(codigos) {
    var opcoes = codigos.map(function(c) { return { label: String(c), value: c }; });
    selectBacia.items().reset(opcoes);
    selectBacia.setValue('751');
});

// ─── Marcador ─────────────────────────────────────────────────────────────────
function marcarOuDesmarcarBacia() {
    var codigo = selectBacia.getValue();
    if (!codigo) return;
    var idx = listaMarcadas.indexOf(codigo);
    if (idx > -1) { listaMarcadas.splice(idx, 1); }
    else          { listaMarcadas.push(codigo); }
    atualizarListaMarcadas();
}

function atualizarListaMarcadas() {
    marcadasPanel.clear();
    marcadasPanel.add(ui.Label('Bacias marcadas:', { fontSize: '11px' }));
    listaMarcadas.forEach(function(c) { marcadasPanel.add(ui.Label('• ' + c, { fontSize: '11px' })); });
}

// ─── Camadas por mapa (1 ano) ─────────────────────────────────────────────────
var camadasAnt   = [];
var camadasAtual = [];
var camadasPost  = [];

function carregarCamadasAno(map, listaCamadas, ano, bacia, raster_bacia, centrar) {
    var bacia_selected = selectBacia.getValue();
    var anoCol10 = Math.min(ano, param.asset_Map_max_year);

    var ic_antes  = getStepIC(antes_show,  bacia_selected);
    var ic_depois = getStepIC(depois_show, bacia_selected);

    var img_antes  = ic_antes.first().select(['classification_' + ano]).updateMask(raster_bacia);
    var img_depois = ic_depois.first().select(['classification_' + ano]).updateMask(raster_bacia);
    var img_col10  = mapbiomasCol10.select(['classification_' + anoCol10]).updateMask(raster_bacia);

    var dateStart = ee.Date.fromYMD(parseInt(ano), 1, 1);
    var mosaico   = mosaicEE.filter(ee.Filter.date(dateStart, dateStart.advance(1, 'year')))
                            .median().updateMask(raster_bacia);

    var layerMosaico = ui.Map.Layer(mosaico,    vis.visMosaic, 'Mosaico ' + ano,                         true);
    var layerCol10   = ui.Map.Layer(img_col10,  vis.map_class, 'Col10 '   + anoCol10,                    false);
    var layerAntes   = ui.Map.Layer(img_antes,  vis.map_class, stepLabels[antes_show]  + ' ' + ano,      false);
    var layerDepois  = ui.Map.Layer(img_depois, vis.map_class, stepLabels[depois_show] + ' ' + ano,      true);

    map.layers().add(layerMosaico);
    map.layers().add(layerCol10);
    map.layers().add(layerAntes);
    map.layers().add(layerDepois);
    listaCamadas.push(layerMosaico, layerCol10, layerAntes, layerDepois);

    if (centrar) { map.centerObject(bacia, 9); }
}

// ─── atualizarAnoVisualizado ──────────────────────────────────────────────────
function atualizarAnoVisualizado() {
    var bacia_selected = selectBacia.getValue();
    var anoMapa = Math.round(sliderAno.getValue());
    lbl_ano.setValue(String(anoMapa));
    if (!bacia_selected) return;

    var bacia = bacias.filter(ee.Filter.eq('nunivotto4', bacia_selected));
    var raster_bacia = bacia.map(function(f) { return f.set('id_codigo', 1); })
                            .reduceToImage(['id_codigo'], ee.Reducer.first());

    var anosLocais = [
        Math.max(1985, anoMapa - 1),
        anoMapa,
        Math.min(2025, anoMapa + 1)
    ];

    tituloAnt.setValue('Anterior: '   + anosLocais[0]);
    tituloAtual.setValue('Selecionado: ' + anosLocais[1]);
    tituloPost.setValue('Posterior: '  + anosLocais[2]);

    camadasAnt.forEach(function(l) { mapAnt.layers().remove(l); });
    camadasAtual.forEach(function(l) { mapAtual.layers().remove(l); });
    camadasPost.forEach(function(l) { mapPost.layers().remove(l); });
    camadasAnt = []; camadasAtual = []; camadasPost = [];

    carregarCamadasAno(mapAnt,   camadasAnt,   anosLocais[0], bacia, raster_bacia, false);
    carregarCamadasAno(mapAtual, camadasAtual, anosLocais[1], bacia, raster_bacia, true);
    carregarCamadasAno(mapPost,  camadasPost,  anosLocais[2], bacia, raster_bacia, false);
}

// ─── atualizarInterface (gráfico de área + acurácia) ─────────────────────────
function atualizarInterface() {
    if (bloqueiaAtualizacaoGrafico) return;
    atualizarAnoVisualizado();

    chartPanel.clear();
    chartPanel.add(ui.Label('🔄 Carregando gráficos...', { color: 'gray', fontSize: '11px' }));

    var bacia_selected = selectBacia.getValue();
    if (!bacia_selected) return;

    var bacia     = bacias.filter(ee.Filter.eq('nunivotto4', bacia_selected));
    var mapa_area = getStepIC(depois_show, bacia_selected).first();

    var listaResultados = [];
    param.nyears.forEach(function(anoNum) {
        var nomeBanda = 'classification_' + anoNum;
        var imagem = ee.Image.cat(
            ee.Image.pixelArea().divide(10000).rename('area'),
            mapa_area.select([nomeBanda])
        );
        var stats = imagem.reduceRegion({
            reducer:   ee.Reducer.sum().group({ groupField: 1, groupName: 'class' }),
            geometry:  bacia.geometry(),
            scale:     30,
            maxPixels: 1e13
        });
        stats.evaluate(function(result) {
            listaResultados.push({ ano: anoNum, grupos: result && result.groups ? result.groups : [] });
            if (listaResultados.length === param.nyears.length) {
                listaResultados.sort(function(a, b) { return a.ano - b.ano; });
                chartPanel.clear();
                gerarGrafico(listaResultados);
                exibirAcuracia(bacia_selected);
                panelGrafico.clear();
            }
        });
    });
}

// ─── gerarGrafico ─────────────────────────────────────────────────────────────
function gerarGrafico(resultado) {
    if (!resultado || resultado.length === 0) {
        chartPanel.add(ui.Label('Sem dados disponíveis.'));
        return;
    }
    var tabela = {};
    var anos   = [];

    resultado.forEach(function(f) {
        var ano = f.ano;
        anos.push(ano);
        var presentes = {};
        (f.grupos || []).forEach(function(g) {
            var classe = g.hasOwnProperty('class') ? g.class : g.hasOwnProperty('group') ? g.group : undefined;
            if (classe === undefined || g.sum === undefined) return;
            var chave = String(classe);
            if (!tabela[chave]) tabela[chave] = [];
            tabela[chave].push(g.sum);
            presentes[chave] = true;
        });
        Object.keys(tabela).forEach(function(c) { if (!presentes[c]) tabela[c].push(0); });
    });

    var classesOrdenadas = Object.keys(tabela)
        .filter(function(c) {
            var lista = tabela[c];
            return (!isNaN(Number(c)) && Array.isArray(lista) && lista.length === anos.length &&
                    lista.some(function(v) { return typeof v === 'number' && isFinite(v); }));
        })
        .map(Number).sort(function(a, b) { return a - b; });

    if (classesOrdenadas.length === 0) {
        chartPanel.add(ui.Label('Sem classes válidas para o gráfico.'));
        return;
    }

    var header = ['Ano'].concat(classesOrdenadas.map(String));
    var dados  = [header];
    anos.forEach(function(ano, i) {
        var linha = [ano];
        classesOrdenadas.forEach(function(c) { linha.push(tabela[c][i]); });
        dados.push(linha);
    });

    var paletaClass = palettes.get('classification9');
    var cores = classesOrdenadas.map(function(c) { return paletaClass[parseInt(c)] || '#000000'; });

    chartPanel.add(ui.Chart(dados).setChartType('LineChart').setOptions({
        title:     'Área por Classe (ha) — ' + stepLabels[depois_show],
        hAxis:     { title: 'Ano' },
        vAxis:     { title: 'Área (ha)' },
        curveType: 'function',
        lineWidth: 2,
        pointSize: 3,
        series:    cores.map(function(cor) { return { color: cor }; })
    }));
}

// ─── exibirAcuracia ───────────────────────────────────────────────────────────
function exibirAcuracia(idBacia) {
    var pontosVal = ee.FeatureCollection(param.pontos_accuracy);
    var legenda_dict = ee.Dictionary({
        'FORMA\u00c7\u00c3O FLORESTAL': 3, 'FORMA\u00c7\u00c3O SAV\u00c2NICA': 4, 'MANGUE': 3,
        'FLORESTA ALAG\u00c1VEL': 3, 'FLORESTA INUND\u00c1VEL': 3, 'FLORESTA PLANTADA': 3,
        'RESTINGA ARB\u00d3REA': 12, 'CAMPO ALAGADO E \u00c1REA PANTANOSA': 12,
        'FORMA\u00c7\u00c3O CAMPESTRE': 12, 'OUTRA FORMA\u00c7\u00c3O N\u00c3O FLORESTAL': 12,
        'APICUM': 12, 'AFLORAMENTO ROCHOSO': 29, 'RESTINGA HERB\u00c1CEA': 12,
        'PASTAGEM': 15, 'AGRICULTURA': 19, 'LAVOURA TEMPOR\u00c1RIA': 19, 'SOJA': 19,
        'CANA': 19, 'ARROZ': 19, 'ALGOD\u00c3O': 19, 'OUTRAS LAVOURAS TEMPOR\u00c1RIAS': 19,
        'LAVOURA PERENE': 36, 'CAF\u00c9': 36, 'CITRUS': 36, 'DEND\u00ca': 36,
        'OUTRAS LAVOURAS PERENES': 36, 'SILVICULTURA': 36, 'MOSAICO DE USOS': 21,
        'PRAIA, DUNA E AREAL': 25, 'PRAIA E DUNA': 25, '\u00c1REA URBANIZADA': 25,
        'VEGETA\u00c7\u00c3O URBANA': 25, 'INFRAESTRUTURA URBANA': 25, 'MINERA\u00c7\u00c3O': 25,
        'OUTRAS \u00c1REAS N\u00c3O VEGETADAS': 25, 'OUTRA \u00c1REA N\u00c3O VEGETADA': 25,
        'CORPO D\u2019\u00c1GUA': 33, 'RIO, LAGO E OCEANO': 33, 'AQUICULTURA': 33,
        'N\u00c3O OBSERVADO': 27
    });

    var bacia    = bacias.filter(ee.Filter.eq('nunivotto4', idBacia));
    var anos     = param.nyears.slice(0, 38);
    var linhas   = [['Ano', 'Acurácia']];
    var total    = anos.length;
    var concluidos = 0;

    chartPanel.add(ui.Label('✅ Calculando acurácia global por ano...', { fontSize: '11px' }));

    anos.forEach(function(ano) {
        var campo     = 'CLASS_' + ano;
        var nomeBanda = 'classification_' + ano;
        var pontosAno = pontosVal.filterBounds(bacia.geometry())
                                 .filter(ee.Filter.notNull([campo]))
                                 .filter(ee.Filter.neq(campo, ''));
        var pontosConvertidos = pontosAno.map(function(f) {
            var classeNome = ee.String(f.get(campo)).trim();
            var classeCod  = legenda_dict.get(classeNome);
            return ee.Algorithms.If(classeCod, f.set('classe_ref', classeCod), null);
        }).filter(ee.Filter.notNull(['classe_ref']));

        var imagem   = getStepIC(depois_show, idBacia).first().select([nomeBanda]);
        var amostras = imagem.sampleRegions({
            collection: pontosConvertidos, properties: ['classe_ref'], scale: 30, geometries: false
        });
        amostras.errorMatrix('classe_ref', nomeBanda).accuracy().evaluate(function(valor) {
            concluidos++;
            if (valor !== null && valor !== undefined && isFinite(valor)) { linhas.push([ano, valor]); }
            if (concluidos === total) {
                var hdr = linhas.shift();
                var ord = linhas.sort(function(a, b) { return a[0] - b[0]; });
                ord.unshift(hdr);
                if (ord.length > 1) {
                    chartPanel.add(ui.Chart(ord).setChartType('ScatterChart').setOptions({
                        title: 'Acurácia Global por Ano',
                        hAxis: { title: 'Ano' }, vAxis: { title: 'Acurácia' },
                        pointSize: 4, lineWidth: 2
                    }));
                }
            }
        });
    });
}

// ─── gerarGraficoComparativo ──────────────────────────────────────────────────
function gerarGraficoComparativo() {
    bloqueiaAtualizacaoGrafico = true;
    var classe = parseInt(classeInput.getValue());
    if (isNaN(classe)) { ui.alert('Classe inválida'); bloqueiaAtualizacaoGrafico = false; return; }

    var bacia = bacias.filter(ee.Filter.eq('nunivotto4', selectBacia.getValue()));
    var anos  = ee.List.sequence(1985, 2025);
    panelGrafico.clear();
    panelGrafico.add(ui.Label('🔄 Processando comparações...', { fontSize: '11px' }));

    var colecoes = colecaoInputs
        .map(function(input) { var id = input.getValue(); return id ? { id: id, ic: ee.ImageCollection(id) } : null; })
        .filter(function(obj) { return obj !== null; });

    var restantes     = colecoes.length;
    var todosResultados = [];

    colecoes.forEach(function(colecao) {
        var imagens = anos.map(function(ano) {
            var nome = ee.String('classification_').cat(ee.Number(ano).format('%d'));
            return colecao.ic.select(nome).max().eq(classe)
                .multiply(ee.Image.pixelArea().divide(10000)).rename('area')
                .reduceRegion({ reducer: ee.Reducer.sum(), geometry: bacia.geometry(), scale: 30, maxPixels: 1e13 })
                .get('area');
        });
        ee.List(imagens).evaluate(function(valores) {
            todosResultados.push({ id: colecao.id, dados: valores });
            restantes--;
            if (restantes === 0) {
                panelGrafico.clear();
                var header = ['Ano'].concat(todosResultados.map(function(v) { return v.id; }));
                var linhas = [header];
                for (var i = 0; i < 41; i++) {
                    var linha = [1985 + i];
                    todosResultados.forEach(function(v) { linha.push((v.dados && v.dados[i]) ? v.dados[i] : 0); });
                    linhas.push(linha);
                }
                panelGrafico.add(ui.Chart(linhas).setChartType('LineChart').setOptions({
                    title: 'Comparação entre versões — Classe ' + classe,
                    hAxis: { title: 'Ano' }, vAxis: { title: 'Área (ha)' },
                    lineWidth: 2, pointSize: 3
                }));
                ui.util.debounce(function() { bloqueiaAtualizacaoGrafico = false; }, 300)();
            }
        });
    });
}

// ─── Eventos ─────────────────────────────────────────────────────────────────
selectBacia.onChange(function() { if (!bloqueiaAtualizacaoGrafico) atualizarInterface(); });
sliderAno.onSlide(function(v)   { lbl_ano.setValue(String(Math.round(v))); });
sliderAno.onChange(atualizarAnoVisualizado);
