// ==============================================================================
// 3. PARÂMETROS DE VISUALIZAÇÃO
// ==============================================================================
var Palette = require('users/mapbiomas-global/LULC:LULC_palette.js');
var vis_LULC = Palette.get('vis_LULC');
var ver_S2Col4 = '0-02-11-spt-1';

var vis = {
    roads:   {min: 0, max: 1, palette: ['ff0000']},
    mosaico: {min: 0, max: 2000, bands: ['red_median', 'green_median', 'blue_median']}
};

// ==============================================================================
// 2. ASSETS DAS COLEÇÕES
// ==============================================================================
var param = {
    // Estradas — banda first_year_line (int16, ano 1985-2025; 0 = nunca confirmado)
    asset_roads:    'projects/mapbiomas-workspace/AMOSTRAS/col11/ROADS/roads_federal_state_rasters_part2_10m',
    // coleção 4 sentinel integrada sem filtros
    asset_col4: 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-4/INTEGRATION/classification',
    // Coleção 4.0 Sentinel integrada com Filtros aplicados
    asset_col4_filter: 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-4/INTEGRATION/classification-ft',
    // Mosaico Sentinel — camada RGB de contexto (fundo de tudo)
    asset_mosaic_sentinelp1: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',
    asset_mosaic_sentinelp2: 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3',

    // bandas disponíveis nos assets col4: classification_2017 .. classification_2025 (sem 2016)
    yearMin: 2017,
    yearMax: 2025
}
var s2_col4 = ee.ImageCollection(param.asset_col4);
var s2_col4_ft = ee.ImageCollection(param.asset_col4_filter);
print('integration vesion', s2_col4_ft.aggregate_histogram('version'));
// Adiciona a Coleção 4 (integrada )
var imgCol4ft = s2_col4_ft.filter(ee.Filter.eq('version', ver_S2Col4)).mosaic();
print("imagin Colection ", imgCol4ft);

var imgRoadsRaw = ee.ImageCollection(param.asset_roads)
                    .mosaic()
                    .select('first_year_line');

// ==============================================================================
// 4. INTERFACE — SLIDER DE ANO (ITERATIVO)
// ==============================================================================
var panel = ui.Panel({style: {position: 'top-left', width: '220px', padding: '8px'}});
panel.add(ui.Label('Coleção 4 — Integração + Estradas', {fontWeight: 'bold', fontSize: '14px'}));
panel.add(ui.Label('Filtro v' + ver_S2Col4, {fontSize: '11px', color: 'gray'}));
panel.add(ui.Label('Ano:', {fontWeight: 'bold', margin: '8px 0 0 0'}));

var sliderAno = ui.Slider({
    min: param.yearMin, max: param.yearMax, value: 2023, step: 1,
    style: {width: '95%'}
});
panel.add(sliderAno);

panel.add(ui.Label('Camadas (fundo → topo):', {fontWeight: 'bold', margin: '8px 0 0 0'}));
panel.add(ui.Label('1. Coleção 4 sem filtro'));
panel.add(ui.Label('2. Coleção 4 filtrada'));
panel.add(ui.Label('3. Estradas (destaque)'));
panel.add(ui.Label('4. Mosaico Sentinel (fundo, oculto)'));

Map.add(panel);

// ==============================================================================
// 5. LÓGICA DE ATUALIZAÇÃO — redesenha as camadas para o ano selecionado
// ==============================================================================
function atualizarMapa() {
    Map.layers().reset([]);

    var year     = sliderAno.getValue();
    var bandaAno = 'classification_' + year;

    var estradasAtivas = imgRoadsRaw.gt(0).and(imgRoadsRaw.lte(year));

    var asset_mosaic_s2 = year < 2024 ? param.asset_mosaic_sentinelp1 : param.asset_mosaic_sentinelp2;
    var mosaicoS2 = ee.ImageCollection(asset_mosaic_s2)
                        .filter(ee.Filter.eq('year', year))
                        .mosaic()
                        .select(vis.mosaico.bands);

    Map.addLayer(s2_col4.select(bandaAno), vis_LULC, 'Coleção 4 Integração Sem Filtro - ' + year, true);
    Map.addLayer(imgCol4ft.select(bandaAno), vis_LULC, 'Coleção 4 Integração Filtrada - ' + year, true);
    Map.addLayer(estradasAtivas.selfMask(), vis.roads, 'Estradas — destaque (' + year + ')', false);
    Map.addLayer(mosaicoS2, vis.mosaico, 'Mosaico Sentinel (' + year + ')', false);
}

sliderAno.onChange(atualizarMapa);
atualizarMapa();

