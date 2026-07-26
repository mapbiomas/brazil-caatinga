/**
 * VISUALIZAÇÃO COMPARATIVA: LANDSAT (Col10) vs SENTINEL-2 (Versões)
 * Configuração: 3 Painéis (Ano-1, Ano, Ano+1)
 * Atualização: Suporte a seletor de Versão e visualização de TODAS as bacias.
 */

var palettes = require('users/mapbiomas/modules:Palettes.js');

// --- CONFIGURAÇÃO E ASSETS ---
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
    // Entrada do filtro (joined pré-correção de floresta)
    asset_input_joined:  'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
    // Saída do filtro de floresta (Gap-fill col11)
    asset_gap_fill:      'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/S2/POS-CLASS/Gap-fill',
    // Col11 — máscara de referência utilizada pelo filtro
    asset_col11:         'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-11/INTEGRATION/classification-ft',
    col11_version:       '0-4-12-spt-4',

    // Assets auxiliares
    asset_bacias: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    asset_mosaic_sentinelp2: 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',
    asset_mosaic_sentinelp1: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',

    version_inp: 5,   // versão do joined de entrada
    version_gap: 5,   // versão do Gap-fill exportado

    // Anos disponíveis
    nyears: [ '2016','2017','2018','2019','2020','2021','2022','2023','2024','2025' ],
};

// --- CARREGAMENTO DE DADOS ESTÁTICOS ---
var bacias = ee.FeatureCollection(param.asset_bacias)
                    .map(function(feat){return feat.set('idCod', 1)});

// Col11 integration (referência usada pelo filtro de floresta)
var lstBandMap = [
    'classification_2016','classification_2017','classification_2018','classification_2019',
    'classification_2020','classification_2021','classification_2022','classification_2023',
    'classification_2024','classification_2025'
];
var imgCol11Ref = ee.ImageCollection(param.asset_col11)
                    .filter(ee.Filter.eq('version', param.col11_version))
                    .mosaic()
                    .select(lstBandMap);

// Sentinel entrada (joined pré-filtro) — mosaico fixo
var imgInputJoined = ee.ImageCollection(param.asset_input_joined)
                    .filter(ee.Filter.eq('version', param.version_inp))
                    .mosaic();

// Sentinel saída (Gap-fill pós-filtro de floresta) — mosaico fixo
var imgGapFill = ee.ImageCollection(param.asset_gap_fill)
                    .filter(ee.Filter.eq('version', param.version_gap))
                    .mosaic();

// --- INTERFACE ---
ui.root.clear(); 

// Painel lateral
var panel = ui.Panel({style: {width: '250px', stretch: 'vertical', padding: '10px'}});
panel.add(ui.Label('Comparativo LULC', {fontWeight: 'bold', fontSize: '20px', color: '#2c3e50'}));
panel.add(ui.Label('Sentinel col2 — Filtro de Floresta', {fontSize: '14px', color: 'gray'}));
panel.add(ui.Label('__________________________'));

// 1. Seletor de Bacia
panel.add(ui.Label('1. Escolha a Bacia:', {fontWeight: 'bold'}));
var selectBacia = ui.Select({
    placeholder: 'Carregando bacias...', 
    style: {width: '95%'} 
});
panel.add(selectBacia);

// 2. Info versão (fixo — Gap-fill v5)
panel.add(ui.Label('Versão Gap-fill: v' + param.version_gap, {margin: '10px 0 0 0', color: '#2980b9'}));

// 3. Slider de Ano
panel.add(ui.Label('3. Janela Central (Ano):', {fontWeight: 'bold', margin: '10px 0 0 0'}));
var sliderAno = ui.Slider({
    min: 2016,
    max: 2025,
    value: 2020,
    step: 1,
    style: {width: '95%'}
});
panel.add(sliderAno);

// Legenda Info
panel.add(ui.Label('__________________________'));
panel.add(ui.Label('Camadas:', {fontWeight: 'bold'}));
panel.add(ui.Label('• Fundo: Mosaico Sentinel-2'));
panel.add(ui.Label('• Col11 ref (máscara floresta)'));
panel.add(ui.Label('• Entrada: joined pré-filtro'));
panel.add(ui.Label('• Saída: Gap-fill pós-filtro'));

// Widget de estilos
var stylesWidget = {
    labels: {fontWeight: 'bold', textAlign: 'center', backgroundColor: 'rgba(255, 255, 255, 0.9)', padding: '4px', margin: '0 0 0 40%'},
    controlsVis: {layerList: true, zoomControl: false, mapTypeControl: false, scaleControl: true}
}

// --- CONSTRUÇÃO DOS MAPAS (3 PAINÉIS) ---
var mapAnt = ui.Map();
var mapAtual = ui.Map();
var mapPost = ui.Map();
ui.Map.Linker([mapAnt, mapAtual, mapPost]);

mapAnt.setControlVisibility(stylesWidget.controlsVis);
mapAtual.setControlVisibility(stylesWidget.controlsVis);
mapPost.setControlVisibility(stylesWidget.controlsVis);

// Títulos sobre os mapas
var tituloAnt = ui.Label('Ano anterior', stylesWidget.labels);
var tituloAtual = ui.Label('Ano selecionado', stylesWidget.labels);
var tituloPost = ui.Label('Ano posterior', stylesWidget.labels);

mapAnt.add(tituloAnt);
mapAtual.add(tituloAtual);
mapPost.add(tituloPost);

// Layout Horizontal
var mapasHorizontal = ui.Panel({
    widgets: [mapAnt, mapAtual, mapPost], 
    layout: ui.Panel.Layout.Flow('horizontal'), 
    style: {stretch: 'both'}
});

var painelCompleto = ui.Panel({
    widgets: [panel, mapasHorizontal],
    layout: ui.Panel.Layout.Flow('horizontal'),
    style: {stretch: 'both'}
});

ui.root.add(painelCompleto);

// --- LÓGICA DE ATUALIZAÇÃO ---

// Arrays para rastrear camadas e remover depois
var camadasAnt = [];
var camadasAtual = [];
var camadasPost = [];

function atualizarInterface() {   
    // Limpa camadas antigas
    camadasAnt.forEach(function(layer) { mapAnt.layers().remove(layer); });
    camadasAtual.forEach(function(layer) { mapAtual.layers().remove(layer); });
    camadasPost.forEach(function(layer) { mapPost.layers().remove(layer); });
    camadasAnt = [];
    camadasAtual = [];
    camadasPost = [];

    var bacia_selected = selectBacia.getValue();
    var anoCentral = sliderAno.getValue();

    if (!bacia_selected) return;

    // --- 1. DEFINIR GEOMETRIA E MÁSCARA ---
    var featBacia, geomBacia;
    
    if (bacia_selected === 'ALL') {
        // Se for ALL, usamos todas as bacias. 
        featBacia = bacias; 
        geomBacia = bacias.geometry(); // Geometria unificada (pode ser pesada dependendo da complexidade)
    } else {
        // Filtra bacia específica
        featBacia = bacias.filter(ee.Filter.eq('nunivotto4', bacia_selected));
        geomBacia = featBacia.geometry();
    }

    // Cria a máscara visual (reduz a feature collection a uma imagem raster)
    var maskBacia = featBacia.reduceToImage(['idCod'], ee.Reducer.first());

    // imgInputJoined, imgGapFill e imgCol11Ref são carregados estaticamente no topo


    // Define os anos vizinhos
    var anosLocais = [
        Math.max(2016, anoCentral - 1),
        anoCentral,
        Math.min(2026, anoCentral + 1)
    ];

    // Atualiza Labels
    tituloAnt.setValue('Ano: ' + anosLocais[0]);
    tituloAtual.setValue('Ano: ' + anosLocais[1]);
    tituloPost.setValue('Ano: ' + anosLocais[2]);

    var maps = [mapAnt, mapAtual, mapPost];
    var listasCamadas = [camadasAnt, camadasAtual, camadasPost];

    // Loop para preencher os 3 mapas
    anosLocais.forEach(function(ano, i) {
        var map = maps[i];
        var listaCamadas = listasCamadas[i];
        
        // --- A. Mosaico Sentinel (Fundo) ---
        var mosaicoS2 = null; 
        if (ano < 2024){ 
            mosaicoS2 = ee.ImageCollection(param.asset_mosaic_sentinelp1);
        } else {
            mosaicoS2 = ee.ImageCollection(param.asset_mosaic_sentinelp2)
        }
        mosaicoS2 = mosaicoS2.filterBounds(geomBacia)
                            .filter(ee.Filter.eq('year', ano))
                            .mosaic().updateMask(maskBacia);
        var layerMosaicoS2 = ui.Map.Layer(mosaicoS2, vis.mosaico, 'Mosaico S2 ' + ano, false);
        
        var nomeBanda = 'classification_' + ano;

        // --- C. Col11 referência (máscara de floresta usada no filtro) ---
        var classCol11 = imgCol11Ref.select([nomeBanda]).updateMask(maskBacia);
        var layerCol11 = ui.Map.Layer(classCol11, vis.map_class, 'Col11 ref (' + ano + ')', false);

        // --- D. Entrada: joined pré-filtro de floresta ---
        var classInput = imgInputJoined.select([nomeBanda]).updateMask(maskBacia);
        var layerInput = ui.Map.Layer(classInput, vis.map_class, 'Entrada joined (' + ano + ')', false);

        // --- E. Saída: Gap-fill pós-filtro de floresta ---
        var classGapFill = imgGapFill.select([nomeBanda]).updateMask(maskBacia);
        var layerGapFill = ui.Map.Layer(classGapFill, vis.map_class, 'Gap-fill v' + param.version_gap + ' (' + ano + ')', true);

        // Centraliza mapa no painel do meio
        if (i === 1) {
            map.centerObject(featBacia, bacia_selected === 'ALL' ? 6 : 10);
        }

        // Adiciona na ordem (fundo → referência → entrada → saída)
        map.layers().add(layerMosaicoS2);
        map.layers().add(layerCol11);
        map.layers().add(layerInput);
        map.layers().add(layerGapFill);

        listaCamadas.push(layerMosaicoS2);
        listaCamadas.push(layerCol11);
        listaCamadas.push(layerInput);
        listaCamadas.push(layerGapFill);
    });
}

// --- PREPARAÇÃO LISTA DE BACIAS ---
var nameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751', 
    '752', '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622'
]

// Preenche lista de bacias + ALL
ee.List(nameBacias).sort().evaluate(function(codigos) {
    var opcoes = [];
    
    // Adiciona opção ALL no topo
    opcoes.push({label: 'TODAS (ALL)', value: 'ALL'});
    
    // Adiciona as demais
    codigos.forEach(function(c) {
        opcoes.push({label: String(c), value: c});
    });
    
    selectBacia.items().reset(opcoes);
    selectBacia.setValue(opcoes[0].value); // Seta 'ALL' como padrão, ou mude para index 1 para pegar a primeira bacia
});

// Event Listeners
selectBacia.onChange(atualizarInterface);
sliderAno.onChange(atualizarInterface);