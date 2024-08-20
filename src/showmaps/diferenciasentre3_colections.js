var UIUtils = require('users/agrosatelite_mapbiomas/packages:UIUtils.js')
var mapbiomas_palette = require('users/mapbiomas/modules:Palettes.js').get('classification8')

/***************Mask Brazil *************************/

var roi = ee.FeatureCollection("FAO/GAUL/2015/level0")
  .filterMetadata('ADM0_NAME', 'equals', 'Brazil')


/******************************************************/

/************** mask Bioma **************************/ 

// var biomaList = ['Cerrado', 'Caatinga', 'Pantanal', 'Pampa', 'Amazônia', 'Mata Atlântica']

// var biomaList = ['Caatinga']

var bioma = ee.FeatureCollection("projects/mapbiomas-workspace/AUXILIAR/ESTATISTICAS/COLECAO9/biomes-coastal-zone")
            // .filter(ee.Filter.inList("Bioma", biomaList)) 
            
var planet = ee.Image('projects/planet-nicfi/assets/basemaps/americas/planet_medres_normalized_analytic_2023-01_mosaic')
            
/******************************************************/
var maskIRECE = ee.FeatureCollection('projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_irece')


var agric_remap = ee.ImageCollection('projects/mapbiomas-workspace/COLECAO9/agricultura')
                .filter(ee.Filter.eq('version', '4'))


var c9Collection = ee.ImageCollection('projects/mapbiomas-workspace/COLECAO9/integracao')
                .filter(ee.Filter.eq('version', '0-7')).mosaic()
var c8Collection =  ee.Image('projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1')
                  .addBands(ee.Image(0).rename('classification_2023'), null, true)


var result = ee.ImageCollection(
  ee.List.sequence(1985, 2023).map(function(year) {
  var yearInt = ee.Number(year).int();
  var strYear =(ee.String(yearInt));
  var timeStart = ee.Date(strYear.cat('-01-01')).millis()
  
  var mapb9 = c9Collection.select(ee.String('classification_').cat(yearInt)).rename('C9_MapBiomas');
  var mapb8 = c8Collection.select(ee.String('classification_').cat(yearInt)).rename('C8_MapBiomas');
  var agric = agric_remap.filter(ee.Filter.eq('year', yearInt)).max().rename('agric_remap');
  
  return mapb9.addBands(mapb8).addBands(agric)
        .set('year', yearInt)
        .set('system:time_start', timeStart)

        .selfMask()
})
)
var mask_Irece = ee.Image().byte().paint({
                    featureCollection: maskIRECE,
                    color: 1,
                    width: 1.5
                    });


var palette = ['#c27ba0',' #f3b4f1', '#dd7e6b', ' #ff99ff']

var classes = {
  
  // // 'LavouraTemporaria':{
    
    // 'Cana':{
    //   n_classe: 'Cana',
    //   id: 20,
    //   cor: '#C27BA0'
    // },
    
    // 'Soja':{
    //   n_classe: 'Soja',
    //   id: 39,
    //   cor: '#e075ad'
    //   },
      
    // 'Arroz':{
    //   n_classe: 'Arroz',
    //   id: 40,
    //   cor: '#982c9e'
    //   },
    // 'Algodao':{
    //   n_classe: 'Arroz',
    //   id: 62,
    //   cor: 'blue'
    //   },
      
    // 'OutraLavouraTemporaria':{
    //   n_classe: 'Outra Lavoura Temporária',
    //   id: 41,
    //   cor: '#e787f8'
    //   },

  // },
 
  // // 'LavouraPerene':{
  
    // 'Café':{
    //   n_classe: 'Cafe',
    //   id: 46,
    //   cor: '#cca0d4'
    //   },
      
    // 'Citrus':{
    //   n_classe: 'd082de',
    //   id: 47,
    //   cor: '#af2a2a'
    //   },
  
      // 'Palm':{
      // n_classe: 'Palm Plantation',
      // id: 35,
      // cor: '#cd49e4'
      // },
      
    // 'Outra Lavoura Perene':{
    //   n_classe: 'Outra Lavoura Perene',
    //   id: 48,
    //   cor: '#cd49e4'
    //   },
    
    // 'Silvicultura':{
    //   n_classe: 'silvicultura',
    //   id: 9,
    //   // cor:mapbiomas_palette[9]
    // }
  // }
    
    //'demais_classes': {
      
    'Mosaico de usos':{
      n_classe: 'Mosaico de usos',
      id: 21,
      cor: '#cd49e4'
      },
      
    // }

  }



// functions 

function loadResult(year) {
  
  if (!year) return;
          
          
        Object.keys(classes).forEach(function(key) {
          
          var color = mapbiomas_palette[classes[key].id]
    
          var id = classes[key].id


         var mapbiomas_c8 = result.filter(ee.Filter.eq('year', parseInt(year))).select('C8_MapBiomas').max();
         var mapbiomas_c9 = result.filter(ee.Filter.eq('year', parseInt(year))).select('C9_MapBiomas').max();
         var agric_remap_ft = result.filter(ee.Filter.eq('year', parseInt(year))).select('agric_remap').max().eq(id);
         
         var c9_silv_ft = mapbiomas_c8.eq(id).remap([1], [2]);
         var c8_silv_ft = mapbiomas_c9.eq(id);

         
         var diff = c9_silv_ft.unmask().add(c8_silv_ft.unmask());

        Map.addLayer(planet, imageVisParam, 'Planet Jan 2023', false)
        
        Map.addLayer(mapbiomas_c8, {palette: mapbiomas_palette, min:0, max: 62}, 'mapbiomas_c8', false)
        Map.addLayer(mapbiomas_c9, {palette: mapbiomas_palette, min:0, max: 62}, 'mapbiomas_c9', false)
        
        Map.addLayer(diff.selfMask(), {palette: ['#00ff00', 'red', 'blue'], min:1, max: 3}, "Diff C8-FT Vs C7-V0 "  + " id " +  id + "-" +   key, true);
        Map.addLayer(c8_silv_ft.selfMask(), {palette: color}, 'C7.1  -  id ' + id + ' Classe ' +  key, false);
        Map.addLayer(c9_silv_ft.selfMask(), {palette: color}, 'C8   - id ' + id + ' Classe ' +  key, false);
        Map.addLayer(agric_remap_ft.selfMask(), {palette: color}, 'remap   - id ' + id + ' Classe ' +  key, false);
        Map.addLayer(bioma.style({fillColor: '00000000', color:'778da9', width: 1}), {}, 'bioma')
        
        Map.addLayer(mask_Irece, {palette: 'FF0000'}, 'mascara Irece');

        });

}




// Deixar apenas a borda das featureCollentions
var brasil = ee.FeatureCollection("FAO/GAUL/2015/level0")
.filterMetadata ('ADM0_NAME', 'equals', 'Brazil')

var uf = ee.FeatureCollection('projects/mapbiomas-workspace/AUXILIAR/ESTATISTICAS/COLECAO7/state')

// Map.addLayer(brasil.style({color: '26458d', fillColor: 'white'}))
// Map.addLayer(uf.style({color: 'grey', width: 0.5, fillColor: '00000000'}))

// Map.centerObject(brasil, 4)

//Criar Lagenda




var toolPanel = ui.Panel({
  widgets: [ui.Label('')],
  layout: ui.Panel.Layout.flow("vertical"),
  style: {
    width: "350px",
    height: "150px",
    margin: '2px"',
    padding: '10px',
    position: 'top-left',
  }
});



var legendPanel = ui.Panel({
  style:{fontWeight: 'bold', fontSize: '10px', margin: '0 0 0 8px', padding: '0'}});
toolPanel.add(legendPanel);

var legendTitle = ui.Label(
    'Legenda',
    {fontWeight: 'bold', fontSize: '16px', margin: '0 0 4px 0', padding: '0'});
legendPanel.add(legendTitle);

var makeRow = function(color, name) {
  // Create the label that is actually the colored box.
  var colorBox = ui.Label({
    style: {
      backgroundColor: color,
      // Use padding to give the box height and width.
      padding: '8px',
      margin: '0 0 4px 0'
    }
  });

  // Create the label filled with the description text.
  var description = ui.Label({
    value: name,
    style: {margin: '0 0 8px 6px'}
  });

  return ui.Panel({
    widgets: [colorBox, description],
    layout: ui.Panel.Layout.Flow('horizontal')
  });
};

toolPanel.add(makeRow('#00ff00', 'Apenas na Coleção 9'))
toolPanel.add(makeRow('red',   'Apenas na Coleção 8'))
toolPanel.add(makeRow('blue', 'presente na C8 e C9'))
Map.add(toolPanel)

// UI


//-----------------------------------------CRIAR GRÁFICO DE NDVI

var Modisbands = ['sur_refl_b03', 'sur_refl_b01', 'sur_refl_b02', 'sur_refl_b07', 'SummaryQA', "NDVI"]
var ModisCollection = ee.ImageCollection('MODIS/006/MOD13Q1')
    .filterDate('2000-01-01', '2023-12-31')
    .select(Modisbands, ['BLUE', 'RED', 'NIR', 'SWIR', 'BQA', "NDVI"])
    .map(function(image){
      var mask = image.select('BQA')
      var freeCloud = image.updateMask(mask.not())
      var reescaled = freeCloud.divide(10000)
     
      return reescaled.copyProperties(image, ["system:time_start"])
    })

var yearSelector = UIUtils.getSequenceSelector(1985, 2023)

yearSelector.style().set({
  width: '100%',
  height: '90px',
  margin: '0px',
  padding: '0px'
});

yearSelector.onClick(loadResult);



var chartPanel = ui.Panel({
    widgets: [ui.Label('CLICK EM UM ANO PARA ANALISAR')],
  layout: ui.Panel.Layout.flow("horizontal"),
  style: {
    width: "100%",
    height: "140px",
    margin: '0px"',
    padding: '0px'
  }
});



var currentPoint = null;

Map.onClick(function(latlong){
  chartPanel.clear();
  currentPoint = ee.Geometry.Point([latlong.lon, latlong.lat]);
  
    var chart1 = ui.Chart.image.series({
        imageCollection: result, 
        region: currentPoint, 
        reducer: ee.Reducer.median(), 
        scale: 30
      })
      .setChartType('ScatterChart');
      
    chart1.setOptions({
      hAxis: {
        format: 'YYYY', 
        gridlines: {
          count: 7
        }
      },
      vAxis: {
        viewWindow: {
          min: 0,
          max: 62
        }
      },
      lineWidth: 1,
      pointSize: 2
    });
  
    chart1.style().set({
      stretch: 'horizontal',
      height: '138px',
      margin: '0px"',
      padding: '0px'
    });
    
    chartPanel.add(chart1);

  
  
  var chart = ui.Chart.image.series(ModisCollection.select("NDVI"), currentPoint, ee.Reducer.median(), 30)
  chart.setChartType('LineChart')
  chart.setOptions({
          windth: true,
          interpolateNulls: true,
          series: {
              0: {lineWidth: 1, pointSize: 1 },

            }})
  chart.style().set({
    "width": '50%',
    "max-width": '90%',
    "max-height": '100%'
  });
   chartPanel.add(chart);
  
  });


var panel = ui.Panel({
  widgets: [chartPanel, yearSelector],
  layout: ui.Panel.Layout.flow("vertical"),
  style: {
    width: '100%',
    height: '230px',
    position: 'bottom-center',
    margin: "0px",
    padding: "0px"
  }
});

var clearLayersButton = UIUtils.getClearLayersButton();


// Map.onClick(plotSerie);
Map.add(clearLayersButton)
Map.add(panel)
// Map.centerObject(ee.Geometry.Point([-39.179, -8.93]), 6);


