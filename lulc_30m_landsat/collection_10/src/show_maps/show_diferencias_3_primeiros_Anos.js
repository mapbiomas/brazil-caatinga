var UIUtils = require('users/agrosatelite_mapbiomas/packages:UIUtils.js')
var palettes = require('users/mapbiomas/modules:Palettes.js');
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
    },
    raster_cruzado : {
      "opacity":1,
      "bands":["classes"],
      "min":1,
      "palette":["a6a6a6","d9d9d9","dbed55","ff5050","990033"]
    },
    presencia : {
        max: 2,
        min: -1,
        palette: ['#D23519','#FFFFFF','#7D7C7CFF','#085F05FF']
    },
}

var styles = {
    style_painel: {
        width: "350px",
        height: "150px",
        margin: '2px"',
        padding: '10px',
        position: 'bottom-left',
    },
    style_title: {
        fontWeight: 'bold', 
        fontSize: '10px', 
        margin: '0 0 0 0px', 
        padding: '0'
    },
    sytle_legend: {
        fontWeight: 'bold', 
        fontSize: '16px', 
        margin: '0 0 0 0', 
        padding: '0'
    },
    style_label: {
        backgroundColor: '#FFFFFF',
        // Use padding to give the box height and width.
        padding: '8px',
        margin: '0 0 4px 0'
    },
    style_select: {
        width: '100%',
        height: '90px',
        margin: '0px',
        padding: '0px'
    },
    style_chart:  {
        width: "100%",
        height: "140px",
        margin: '0px"',
        padding: '0px'
    },
    style_chart2: {
        stretch: 'horizontal',
        height: '138px',
        margin: '0px"',
        padding: '0px'
    },
    style_painel_principal: {
        width: '100%',
        height: '230px',
        position: 'bottom-center',
        margin: "0px",
        padding: "0px"
    }


}
var optionsCharts = {
    option_charClass : {
        hAxis: {
            format: 'YYYY', 
            gridlines: {count: 7}
        },
        vAxis: {
          viewWindow: {  min: 0,  max: 62  }
        },
        lineWidth: 1,
        pointSize: 2
    },
}
var param = {
    assetFilters: 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials',
    asset_Map : "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    asset_bacias: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    pontos_accuracy: 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col4_points_w_edge_and_edited_v1',
    asset_biomas_raster : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    asset_bioma: 'projects/diegocosta/assets/lm_bioma_250',
    asset_mosaic: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',  
    asset_collectionId: 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    nyears: [
        '1986','1987','1988','1989','1990','1991','1992','1993','1994',
        '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
        '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
        '2015','2016','2017','2018','2019','2020','2021','2022','2023',
    ],
}
var lst_years = ee.List.sequence(1986, 2023).getInfo();
var year_courrent = lst_years[0]
var classe_savana = 4;
var classe_uso = 21;
var classe_act = 'savana';
var version = 8;
var raster_filters = ee.ImageCollection(param.assetFilters)
                               .filter(ee.Filter.eq('version', version))   
                               .max();
var position = 0; 

// functions 
function loadResult(cyear) {  
    print(cyear);
    // Map.clear();
    // Map.add(toolPanel)
    // Map.add(panel)
    var ano_pre = String(parseInt(cyear) - 1);
    var ano_pos = String(parseInt(cyear) + 1);
    print(ee.String("lista de 3 anos consecutivos ")
              .cat(ano_pre).cat(" <> ")
              .cat(String(cyear))
              .cat(" <> ").cat(ano_pos) 
            );

    var mapa_pre = raster_filters.select('classification_' + ano_pre);
    var mapa_year =  raster_filters.select('classification_' + cyear);
    var mapa_pos =  raster_filters.select('classification_' + ano_pos);
    var classe_pre = mapa_pre.eq(classe_savana);
    var classe_year = mapa_year.eq(classe_savana);
    var classe_pos = mapa_pos.eq(classe_savana);
    // mask_mudanca = mask_mudanca.remap([2,1,0,-1], [])
    var mudanca_pre_courr = classe_year.multiply(2).subtract(classe_pre);
    print("show metadata ", mudanca_pre_courr);
    var mask_pre_cour = mudanca_pre_courr.neq(0);
    var mudanca_courr_pos = classe_pos.multiply(2).subtract(classe_year);
    var mask_courr_pos = mudanca_courr_pos.neq(0);
    var mudanca_pos_pre = classe_pos.multiply(2).subtract(classe_pre);
    var mask_pos_pre = mudanca_pos_pre.neq(0);

    Map.addLayer(ee.Image.constant(1), {min:0, max: 1}, 'base');
    Map.addLayer(mudanca_pre_courr.updateMask(mask_pre_cour), vis.presencia, "precensa " + ano_pre + " " + cyear); //.updateMask(mask_pre_cour)
    Map.addLayer(mudanca_courr_pos.updateMask(mask_courr_pos), vis.presencia, "precensa " + cyear + " " + ano_pos); //.updateMask(mask_courr_pos)
    Map.addLayer(mudanca_pos_pre.updateMask(mask_pos_pre), vis.presencia, "precensa " + ano_pre + " " + ano_pos);  //.updateMask(mask_pos_pre) 

    Map.addLayer(mapa_pre, vis.map_class, "classe "+ ano_pre, false);
    Map.addLayer(mapa_year, vis.map_class, "classe "+ cyear, false);
    Map.addLayer(mapa_pos, vis.map_class, "classe "+ ano_pos, false);
       
};

var toolPanel = ui.Panel({
    widgets: [ui.Label('')],
    layout: ui.Panel.Layout.flow("vertical"),
    style: styles.style_painel
});

var legendPanel = ui.Panel({
    style: styles.style_title
});
toolPanel.add(legendPanel);

var legendTitle = ui.Label( 'Legenda', styles.sytle_legend );
legendPanel.add(legendTitle);

var makeRow = function(color, name) {
    // Create the label that is actually the colored box.
    var colorBox = ui.Label({ style:  {
        backgroundColor: color,
        // Use padding to give the box height and width.
        padding: '8px',
        margin: '0 0 4px 0'
    } });

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

toolPanel.add(makeRow('#D23519', classe_act + ' em ano anterior'))
toolPanel.add(makeRow('#7D7C7C',  classe_act + ' em ambos anos'))
toolPanel.add(makeRow('#085F05', classe_act + ' em ano activo'))
Map.add(toolPanel)
loadResult(year_courrent)

// var yearSelector = UIUtils.getSequenceSelector(1986, 2023);
// yearSelector.style().set(styles.style_select);
// yearSelector.onClick(loadResult);

// var chartPanel = ui.Panel({
//     widgets: [ui.Label('CLICK EM UM ANO PARA ANALISAR')],
//     layout: ui.Panel.Layout.flow("horizontal"),
//     style: styles.style_chart
// });

var currentPoint = null;

// Map.onClick(function(latlong){
//     chartPanel.clear();
//     currentPoint = ee.Geometry.Point([latlong.lon, latlong.lat]);
    
//     var chart1 = ui.Chart.image.series({
//           imageCollection: result, 
//           region: currentPoint, 
//           reducer: ee.Reducer.median(), 
//           scale: 30
//     }).setChartType('ScatterChart');
//     chart1.setOptions(optionsCharts.option_charClass);
//     chart1.style().set(styles.style_chart2);    
//     chartPanel.add(chart1); 
// });


// var panel = ui.Panel({
//     widgets: [chartPanel], // yearSelector
//     layout: ui.Panel.Layout.flow("vertical"),
//     style: styles.style_painel_principal
// });
// // var clearLayersButton = UIUtils.getClearLayersButton();
// // / Map.onClick(plotSerie);
// // Map.add(clearLayersButton)
// Map.add(panel)

