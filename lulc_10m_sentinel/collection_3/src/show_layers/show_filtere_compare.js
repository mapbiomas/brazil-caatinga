/**
 * @title App de Visualização de Filtros Sentinel-2 (Caatinga) - v3 (Modern UI)
 * @description Visualizador comparativo com Menu Retrátil, Filtro de Bacias e Controle de Camadas.
 * @author Expert GEE
 */

// --- 1. CONFIGURAÇÃO E ASSETS ---

// Importação de utilitários
var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text'); 

var classificationPalette = palettes.get('classification9');

var vis = {
    mosaico: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },
    map_class: {
        min: 0,
        max: 69,
        palette: classificationPalette
    }
};

var assets = {
    filters: {
        'classifications': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
        'Gap Fill': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Gap-fill',
        'Temporal Nativo': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalN',
        'Temporal Anterior': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalA',
        'Frequência': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Frequency',
        'Espacial All Class': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_all',
        'Espacial Int': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_int'
    },
    regions: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    uso_cobertura: 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
    caatinga: 'users/CartasSol/shapes/nCaatingaBff3000',
    mosaic_p1: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3', 
    mosaic_p2: 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3'              
};

var availableYears = ['2016','2017','2018','2019','2020','2021','2022','2023','2024','2025'];
var availableVersions = ['1', '2', '3', '4', '5'];

// Lista de nomes/IDs para as bacias
var listaNameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764', '7691', '7581', '7625', '7584', '751',      
    '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752'
];

// Adiciona opção de "Todas" no início da lista para o dropdown
var dropdownItems = ['all_basin'].concat(listaNameBacias);

// --- 2. PREPARAÇÃO DE DADOS ESPACIAIS (BASE) ---
// 1. Carrega as regiões originais e define um ID padrão
var regionsOriginal = ee.FeatureCollection(assets.regions).map(function(feat){
    return feat.set('idCod', 1);
});

// 2. Prepara as Listas para união segura
var regionsList = regionsOriginal.toList(500); // Aumentei margem para garantir
var namesList = ee.List(listaNameBacias);

// Define o tamanho baseando-se no menor valor para evitar erros de índice
var count = regionsList.size().min(namesList.size());

// 3. Criação da FeatureCollection com Rótulos (Método Indexado Seguro)
// Usamos uma sequência numérica para pegar (get) o item certo de cada lista
var indices = ee.List.sequence(0, count.subtract(1));

var regionsWithLabels = ee.FeatureCollection(indices.map(function(i) {
    var index = ee.Number(i);
    var feat = ee.Feature(regionsList.get(index)); // Pega a Geometria
    var labelText = ee.String(namesList.get(index)); // Pega o Nome
    
    // Retorna a feição original com a nova propriedade 'label_id'
    return feat.set('label_id', labelText);
}));
var scale = 5000; 
var labelImages = regionsWithLabels.map(function(feat) {
  var labelText = ee.String(feat.get('label_id'));
  var center = feat.geometry().centroid();
  return text.draw(center, labelText, scale, {
    textColor: 'black',
    outlineColor: 'white',
    outlineWidth: 2,
    fontSize: 14,
    fontType: 'Arial'
  });
});
var labels = ee.ImageCollection(labelImages).mosaic();


// --- 3. ESTADO DA APLICAÇÃO ---

var appState = {
    year: '2023',
    version: '1',
    basin: 'all_basin', // Estado para o filtro da bacia
    activeLayers: {} 
};

// Inicializa estado dos checkboxes
Object.keys(assets.filters).forEach(function(key) {
    appState.activeLayers[key] = (key === 'Espacial Int'); 
});


// --- 4. INTERFACE DE USUÁRIO (MODERNA) ---

// Estilos CSS-like
var styles = {
    panel: {
        width: '350px', 
        padding: '10px', 
        backgroundColor: '#ffffff',
        border: '1px solid #ddd'
    },
    card: {
        border: '1px solid #eeeeee', // Borda para simular o card
        backgroundColor: '#fafafa',
        padding: '10px',
        margin: '8px 0'
        // Removidos: borderRadius, boxShadow (não suportados)
    },
    header: {
        fontSize: '18px', 
        fontWeight: 'bold', 
        color: '#2c3e50',
        margin: '0 0 10px 0'
    },
    subHeader: {
        fontSize: '13px',
        fontWeight: 'bold',
        color: '#7f8c8d',
        margin: '0 0 5px 0',
        // textTransform: 'uppercase'
    },
    select: {
        stretch: 'horizontal',
        margin: '0 0 5px 0'
    }
};

// -- Componentes de Mapa --
var leftMap = ui.Map();
var rightMap = ui.Map();

// [MODIFICAÇÃO] LayerList ativado para permitir ligar/desligar camadas nos mapas
leftMap.setControlVisibility({layerList: true, zoomControl: false, mapTypeControl: false});
rightMap.setControlVisibility({layerList: true, zoomControl: true, mapTypeControl: true}); 

var linker = ui.Map.Linker([leftMap, rightMap]);

var splitPanel = ui.SplitPanel({
    firstPanel: leftMap,
    secondPanel: rightMap,
    wipe: true,
    style: {stretch: 'both'}
});

// -- Painel Lateral --
var controlPanel = ui.Panel({style: styles.panel});

// Cabeçalho com botão de fechar
var headerPanel = ui.Panel({
    layout: ui.Panel.Layout.flow('horizontal'),
    style: {stretch: 'horizontal', margin: '0 0 10px 0'}
});
var title = ui.Label('Filtros Caatinga S2', styles.header);
var closeButton = ui.Button({
    label: '✕',
    style: {margin: '0 0 0 auto', color: 'red'}, // Alinha à direita
    onClick: toggleSidebar
});
headerPanel.add(title).add(closeButton);


// --- CARD 1: Seleção Temporal e Versão ---
var timeCard = ui.Panel({style: styles.card});
timeCard.add(ui.Label('Configuração', styles.subHeader));

var flexContainer = ui.Panel({layout: ui.Panel.Layout.flow('horizontal'), style: {stretch: 'horizontal'}});

var selectYear = ui.Select({
    items: availableYears,
    value: appState.year,
    placeholder: 'Ano',
    onChange: function(value) {
        appState.year = value;
        updateMaps();
    },
    style: {stretch: 'horizontal', margin: '0 5px 0 0'}
});

var selectVersion = ui.Select({
    items: availableVersions,
    value: appState.version,
    placeholder: 'Versão',
    onChange: function(value) {
        appState.version = value;
        updateMaps();
    },
    style: {stretch: 'horizontal', margin: '0 0 0 5px'}
});

flexContainer.add(selectYear).add(selectVersion);
timeCard.add(flexContainer);


// --- CARD 2: Filtro Espacial (Bacias) ---
var regionCard = ui.Panel({style: styles.card});
regionCard.add(ui.Label('Filtro Regional', styles.subHeader));

var selectBasin = ui.Select({
    items: dropdownItems,
    value: appState.basin,
    onChange: function(value) {
        appState.basin = value;
        updateMaps();
    },
    style: styles.select
});
regionCard.add(ui.Label('Selecione a Bacia (nunivotto4):', {fontSize:'11px', color:'gray'}));
regionCard.add(selectBasin);


// --- CARD 3: Camadas de Filtro ---
var layersCard = ui.Panel({style: styles.card});
layersCard.add(ui.Label('Camadas do Processamento', styles.subHeader));

Object.keys(assets.filters).forEach(function(key) {
    var chk = ui.Checkbox({
        label: key,
        value: appState.activeLayers[key],
        style: {margin: '2px 0'},
        onChange: function(checked) {
            appState.activeLayers[key] = checked;
            updateMaps(); 
        }
    });
    layersCard.add(chk);
});

// Montagem do Painel
controlPanel.add(headerPanel);
controlPanel.add(timeCard);
controlPanel.add(regionCard);
controlPanel.add(layersCard);
controlPanel.add(ui.Label('Mapas: Esq=Mosaico | Dir=Classificação', {fontSize:'10px', color:'#999', margin:'20px 0'}));


// --- LÓGICA DE MOSTRAR/OCULTAR MENU ---

var showButton = ui.Button({
    label: '☰ Menu',
    style: {
        position: 'top-left',
        padding: '0px',
        shown: false // Começa oculto pois o painel está aberto
    },
    onClick: toggleSidebar
});

// Adiciona o botão flutuante ao mapa esquerdo
leftMap.add(showButton);

function toggleSidebar() {
    var isShown = controlPanel.style().get('shown');
    if (isShown) {
        controlPanel.style().set('shown', false); // Oculta painel
        showButton.style().set('shown', true);    // Mostra botão
    } else {
        controlPanel.style().set('shown', true);  // Mostra painel
        showButton.style().set('shown', false);   // Oculta botão
    }
}


// --- 5. LÓGICA DE PROCESSAMENTO E ATUALIZAÇÃO ---

function getMosaicLayer(year, mask) {
    var assetPath = assets.mosaic_p1;
    if (parseInt(year) > 2023) {
        assetPath = assets.mosaic_p2;
    }
    
    var mosaic = ee.ImageCollection(assetPath)
        .filter(ee.Filter.eq('year', parseInt(year)))
        .mosaic()
        .select(vis.mosaico.bands)
        .updateMask(mask);
        
    return mosaic;
}

function updateMaps() {
    var year = appState.year;
    var version = appState.version;
    var bandName = 'classification_' + year;
    var currentBasin = appState.basin;

    // --- 5.1 FILTRAGEM DINÂMICA DA REGIÃO ---
    var activeRegion;
    
    if (currentBasin === 'all_basin') {
        activeRegion = regionsOriginal;
    } else {
        // [REQUISITO] Filtrar pela propriedade 'nunivotto4' usando o valor selecionado
        activeRegion = regionsOriginal.filter(ee.Filter.eq('nunivotto4', currentBasin));
    }

    // Cria a máscara baseada APENAS na região ativa
    var mask_active = activeRegion.reduceToImage(['idCod'], ee.Reducer.first());

    // --- 5.2 ATUALIZAR MAPA ESQUERDO ---
    leftMap.layers().reset();
    
    // Mosaico Recortado pela Bacia Ativa
    var mosaicImg = getMosaicLayer(year, mask_active);
    leftMap.addLayer(mosaicImg, vis.mosaico, 'Mosaico Sentinel-2');
    
    // Coleção 10 (MapBiomas)
    var mapbiomas = ee.Image(assets.uso_cobertura)
        .select(bandName)
        .updateMask(mask_active);
    leftMap.addLayer(mapbiomas, vis.map_class, 'Coleção 10 (LULC)', false); // false = off por padrão
    
    // Contorno da(s) Bacia(s) Selecionada(s)
    var empty = ee.Image().byte();
    var outline = empty.paint({
      featureCollection: activeRegion,
      color: 1,
      width: 2
    });
    leftMap.addLayer(outline, {palette: '000000'}, 'Contorno Bacia(s)');

    // Limite Caatinga
    var caatinga = ee.FeatureCollection(assets.caatinga);
    var caatingaOutline = empty.paint({
        featureCollection: caatinga,
        color: 1,
        width: 1
    });
    leftMap.addLayer(caatingaOutline, {palette: 'red'}, 'Limite Caatinga', false);
    
    // Rótulos (Sempre visíveis para contexto)
    leftMap.addLayer(labels, {}, 'Rótulos Bacias');


    // --- 5.3 ATUALIZAR MAPA DIREITO ---
    rightMap.layers().reset();
    
    Object.keys(assets.filters).forEach(function(filterName) {
        if (appState.activeLayers[filterName]) {
            var assetPath = assets.filters[filterName];
            var col = ee.ImageCollection(assetPath);
            
            // Filtro de versão
            var imgFiltered = col.filter(ee.Filter.eq('version', parseInt(version)));
            
            // Filtro específico para assets temporais
            if ((assetPath.indexOf('TemporalN') > 0 ) & (assetPath.indexOf('TemporalA') > 0 )){
                imgFiltered = imgFiltered.filter(ee.Filter.eq('janela', 5));
            }
            
            // Tratamento de erro para coleção vazia
            var finalImage = ee.Image(ee.Algorithms.If(
                imgFiltered.size(), 
                imgFiltered.mosaic().select(bandName).updateMask(mask_active), 
                ee.Image().byte() 
            ));
            
            rightMap.addLayer(finalImage, vis.map_class, filterName);
        }
    });

    // --- 5.4 CENTRALIZAR ---
    // Centraliza na geometria ativa (seja todas ou uma específica)
    leftMap.centerObject(activeRegion, (currentBasin === 'all_basin' ? 6 : 9));
}

// --- 6. INICIALIZAÇÃO ---

ui.root.clear();
// O Painel é adicionado primeiro, o SplitPanel preenche o resto
ui.root.add(controlPanel);
ui.root.add(splitPanel);

// Primeira renderização
updateMaps();

print("App v3 (Modern UI) carregado com sucesso.");