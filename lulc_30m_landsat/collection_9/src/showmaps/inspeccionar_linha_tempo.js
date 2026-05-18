var palette = require('users/mapbiomas/modules:Palettes.js');

var year = 2020

var year2= 1987

var version = 18
var ultimaVers = 20
var step = 3

var windowf = 3

var windows = 4

var windowt = 5



var visclassCC= {
            "min": 0, 
            "max": 62,
            "palette":  palette.get('classification8'),
            "format": "png"
    };
var listBaciasGap = [
    '744', '752', '753', '754','756','757','758',
    '7614', '7421', '764', '765', '776', '766',
]

var caatinga = ee.Image('projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41').eq(5);

var bacia = ee.FeatureCollection('projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga');
var assetGapfill = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2';
var assetTemporal = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/TemporalV3';
var collectionGapf = ee.ImageCollection(assetGapfill)
                        .filter(ee.Filter.eq('version', 15));                        
collectionGapf = collectionGapf.merge(
                        ee.ImageCollection(assetGapfill)
                            .filter(ee.Filter.eq('version', 13))
                            .filter(ee.Filter.inList('id_bacia', listBaciasGap).not())
                    ).min().updateMask(caatinga);

var collectionJ3 = ee.ImageCollection(assetTemporal)
                        .filter(ee.Filter.eq('version', 20))
                        .filter(ee.Filter.eq('janela', windowf))
                        //.filter(ee.Filter.eq('step', step))
                        .min().updateMask(caatinga);
                       
var collectionJ4 = ee.ImageCollection(assetTemporal)
                        .filter(ee.Filter.eq('version', version))
                        .filter(ee.Filter.eq('janela', windows))
                        //.filter(ee.Filter.eq('step', step))
                        .min().updateMask(caatinga);
                        
var collectionJ5 = ee.ImageCollection(assetTemporal)
                        .filter(ee.Filter.eq('version', version))
                        .filter(ee.Filter.eq('janela', windowt))
                        //.filter(ee.Filter.eq('step', step))
                        .min().updateMask(caatinga);

var collectionFREQ = ee.ImageCollection('projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV3')
                        .filter(ee.Filter.eq('version', version))
                        //.filter(ee.Filter.eq('janela', windowt))
                        //.filter(ee.Filter.eq('step', step))
                        .min().updateMask(caatinga);
                        
                        
var collectionDESC = ee.ImageCollection('projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3')
                          .filter(ee.Filter.eq('filter', 'spatial_use'))                          
                          .min().updateMask(caatinga);
// print(collectionDESC.aggregate_histogram('system:index'))
var pasture = ee.ImageCollection('projects/mapbiomas-workspace/COLECAO9/integracao')

Map.addLayer(pasture)
                        
//Map.addLayer(collectionJ3.select('classification_'+year),visclassCC,'classificationJ3_'+year+'_versão_'+version)
//Map.addLayer(collectionJ4.select('classification_'+year),visclassCC,'classificationJ4_'+year+'_versão_'+version)
//Map.addLayer(collectionJ5.select('classification_'+year),visclassCC,'classificationJ5_'+year+'_versão_'+version)
//Map.addLayer(collectionFREQ.select('classification_'+year),visclassCC,'classificationFreq_'+year+'_versão_'+version)



var inspector = ui.Panel([ui.Label('Click to get info')]);
Map.add(inspector);


Map.onClick(function(coords) {
  // Show the loading label.
  inspector.widgets().set(0, ui.Label({
    value: 'Loading...',
    style: {color: 'gray'}
  }));
  
  
  var point = ee.Geometry.Point([coords.lon, coords.lat])
  
  var selectedFeature = bacia.filterBounds(point);
  
  selectedFeature.evaluate(function(selectedFeature) {
    // Verifica se há alguma feição no ponto clicado.
    if (selectedFeature.features.length > 0) {
      // Caso positivo, seleciona a primeira feição.
      var protectedArea = selectedFeature.features[0];
      
      // Obtém as propriedades da primeira feição.
      var properties = protectedArea.properties;
      
      // Inicializa a lista que armazenará as informações.
      var rows = [];
      
      // Itera sobre as chaves (nomes das propriedades) do objeto properties.
      Object.keys(properties).forEach(function(property) {
        // Obtém o valor da propriedade.
        var value = properties[property];

        // Cria uma Label com a formatação "Nome da Propriedade: Valor"
        var row = ui.Label(property + ': ' + value);
        
        // Adiciona a Label à lista rows.
        rows.push(row);
      });
      
      // Adiciona as informações no painel de informações.
      inspector.widgets().reset(rows);
    } else {
      // Mostra mensagem no painel quando nenhuma feição for selecionada.
      inspector.widgets().reset([ui.Label('No feature selected.')]);
    }
  });
})


var legend = ui.Panel({
    style: {
        position: 'bottom-left',
        width: '500px',
        height: '750px',
        padding: '8px 15px'
    }
});

Map.add(legend);

function getCoordSerie(coords){
    // Add a red dot for the point clicked on.
    var point = ee.Geometry.Point(coords.lon, coords.lat);

      var chartJ3 = ui.Chart.image.regions(collectionJ3, point, ee.Reducer.mean(),30)
              //.setSeriesNames(['Co2Flux', 'Ajustes'])
              .setOptions({title: 'Variação classes mapeadas Janela 3 vers ' + String(ultimaVers),
                    vAxis: {title: 'Nº da classe mapeada'},
                    hAxis: {title: 'Anos'},
                    //colors: ['#e0440e', '#e6693e', '#ec8f6e', '#f3b49f', '#f6c7b6'],
                    lineWidth: 0,
                    pointSize: 5,
                    });
      var chartJ4 = ui.Chart.image.regions(collectionJ4, point, ee.Reducer.mean(),30)
              //.setSeriesNames(['Co2Flux', 'Ajustes'])
              .setOptions({title: 'Variação classes mapeadas Janela 4 vers ' + String(ultimaVers),
                    vAxis: {title: 'Nº da classe mapeada'},
                    hAxis: {title: 'Anos'},
                    //colors: ['#e0440e', '#e6693e', '#ec8f6e', '#f3b49f', '#f6c7b6'],
                    lineWidth: 0,
                    pointSize: 5,
                    });
      var chartJ5 = ui.Chart.image.regions(collectionJ5, point, ee.Reducer.mean(),30)
              //.setSeriesNames(['Co2Flux', 'Ajustes'])
              .setOptions({title: 'Variação classes mapeadas Janela 5 vers ' + String(ultimaVers),
                    vAxis: {title: 'Nº da classe mapeada'},
                    hAxis: {title: 'Anos'},
                    //colors: ['#e0440e', '#e6693e', '#ec8f6e', '#f3b49f', '#f6c7b6'],
                    lineWidth: 0,
                    pointSize: 5,
                    });

    var dot = ui.Map.Layer(point, {color: 'FF0000'});
    Map.layers().set(3, dot);

    legend.clear();
    legend.add(chartJ3);
    legend.add(chartJ4);
    legend.add(chartJ5);
    
    
} 

Map.onClick(getCoordSerie);
Map.style().set('cursor', 'crosshair');


var label = ui.Label('Year Selector');
var slider1 = ui.Slider({
      min:1985,
      max: 2023,
      step: 1,
  style: {stretch: 'horizontal', width:'500px'},
  onChange: updateLayer
});




function updateLayer(value){
    var year = slider1.getValue();
    print(ee.String("showing year ==> ").cat(value));
    Map.layers().reset();
    var collection = collectionFREQ.select('classification_' + year);
    var collectionSec = collectionFREQ.select('classification_' + Number(year + 1))
    var filterDesc = collectionDESC.select('classification_' + Number(year))
    var filterDescSec = collectionDESC.select('classification_' + Number(year + 1))

    var uso2022 = collectionSec.eq(21).subtract(collection.eq(21)).eq(1);
    var change_uso_YYConnected = uso2022.connectedPixelCount(10, true) 
    var mask_Uso_kernel = uso2022.updateMask(change_uso_YYConnected.lte(min_connect_pixel))
    var newMask = uso2022.focalMin(2).focalMax(4);
    var maskPixelsRem = uso2022.updateMask(newMask.eq(0))    
    
    
    Map.addLayer(collectionGapf.select('classification_'+ year), visclassCC)
    Map.addLayer(collection,visclassCC,'classificationFreq_' + String(year))
    Map.addLayer(collectionSec,visclassCC,'classificationFreq_' + String(year + 1))
    Map.addLayer(filterDesc,visclassCC,'classificationDesc_' + String(year))
    Map.addLayer(filterDescSec,visclassCC,'classificationDesc_' + String(year + 1))
    
    Map.addLayer(uso2022.selfMask(), {palette: ['red'], min:-1, max:1}, 'Uso -');
    Map.addLayer(maskPixelsRem.selfMask(), {palette: ['blue'], min:0, max:1}, 'Alertas21 -');
   
}
    
updateLayer();

// Create a panel that contains both the slider and the label.
var panel = ui.Panel({
        widgets: [label, slider1],
        layout: ui.Panel.Layout.flow('vertical'),
        style: {position: 'bottom-right',width: '520px'
    }
});

// Add the panel to the map.
Map.add(panel);

