
var param = { 
    assetMap: 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',   
    assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classificationV1',    
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',    
    assetBacia: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",         
    years: ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
           '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
           '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
           '2015','2016','2017','2018'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    //'743','732','747',
    listaNameBacias: [
        'all','741','7421','7422','744','745','746','7492','751','752',
        '753', '754','755','756','757','758','759','7621','7622','763',
        '764','765','766','767','771','772','773', '7741','7742','775',
        '776','777','778','76111','76116','7612','7613','7614','7615',
        '7616','7617','7618','7619'
    ],       

}
var palettes = require('users/mapbiomas/modules:Palettes.js');
var visualizar = {
    visclass: {
            "min": 0, 
            "max": 45,
            "palette":  palettes.get('classification5'),
            "format": "png"
    },
    visMosaic: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },    
} 

// --- building all map as images , shp files and mosaics

var shp_bacias = ee.FeatureCollection(param.assetBacia);
var mosaic_norm = ee.ImageCollection(param.assetIm).filter(
                                ee.Filter.eq('biome', 'CAATINGA')).select(param.bandas);
var map_col6 = ee.Image(param.assetMap).clip(shp_bacias.geometry());
var year_show = '2017';
var banda_activa = "classification_" + year_show;
// var banda_ref = "CLASS_" +  year_show;
//var bacia_focused = '741';
var map_ver = ee.ImageCollection(param.assetclass).min();

// --- chart -------------------------------------------------------------------
var collection_param = param.years.map(function (year_current) {
    return ee.Feature(null, {
        'year': year_current,
        'class_bnd': 'classification_' + year_current,        
        'system:yValue': 0
    });
});

var barra_year = ui.Chart.feature.byFeature(collection_param, 'year', 'system:yValue')
    .setChartType('LineChart')
    .setOptions({
        legend: 'none',
        lineWidth: 1,
        pointSize: 5,
        height: 60,
        vAxis: {
            gridlines: {
                count: 0
            }
        },
        'chartArea': {
            left: 30,
            top: 10,
            right: 30,
            width: '100%',
            height: '80%'
        },
        hAxis: {
            textPosition: 'in',
            showTextEvery: 1,
            interpolateNulls: true,
            slantedTextAngle: 90,
            slantedText: true,
            textStyle: {
                color: '#000000',
                fontSize: 12,
                fontName: 'Arial',
                bold: false,
                italic: false
            }
        },
        tooltip :{
          trigger: 'none',
        },
        colors: ['#f0e896'],
        crosshair: {
            trigger: 'both',
            orientation: 'vertical',
            focused: {
                color: '#561d5e'
            }
        }
    });

barra_year.style().set({
    position: 'bottom-center',
    width: '100%',
    height: '60px',
    margin: '0px',
    padding: '0px',
});


barra_year.onClick(function (xValue, yValue, seriesName) {
    if (!xValue) return;
    var feature = ee.Feature(
        ee.FeatureCollection(collection_param)
        .filter(ee.Filter.eq('year', xValue))
        .first()
    );
    year_show = xValue;
    print("selecionado o ano ===> " + xValue)
//    aktualisier(year_show);
    
});

var label_ini = ui.Label('     ');
var label_fin = ui.Label('    ');

var button_vis = ui.Button({
    label: 'visualizar Map',
    onClick: function() {
        atualizar_visualization();
    }
});
var button_Merge = ui.Button({
    label: 'merge Map',
    onClick: function() {
    //   print(Map.getCenter());
    }
});

// mensagem de inicio .
// seletor_reg.setPlaceholder('Choose the version...');


button_vis.style().set({
    position: 'bottom-center',
    width: '15%',
    height: '80px',
    margin: '0px',
    padding: '0px',
})
button_Merge.style().set({
    position: 'bottom-center',
    width: '15%',
    height: '80px',
    margin: '0px',
    padding: '0px',
})
var style_label = {
    position: 'bottom-center',
    width: '20%',
    height: '20px',
    margin: '0px',
    padding: '0px',
}
label_ini.style().set(style_label)
label_fin.style().set(style_label)
// -----------------------------------------------------------------------
var Map_esq = ui.Map({
    style: {
        border: '2px solid black'
    }
});

var Map_dir = ui.Map({
    style: {
        stretch: 'both',
        border: '2px solid black'
    }
});

Map_esq.setOptions("SATELLITE")
Map_dir.setOptions("SATELLITE")

var FeatBacias = ee.Image().byte().paint(shp_bacias, 1, 1);
FeatBacias = FeatBacias.visualize({palette: 'FF0000', 'opacity': 0.7});

var mosaic_norm_year = mosaic_norm.filter(ee.Filter.eq('year', parseInt(year_show))).median();

Map_dir.addLayer(mosaic_norm_year, visualizar.visMosaic, "mosaic_norm");
Map_dir.addLayer(map_ver.select(banda_activa), visualizar.visclass, "ver Class");
Map_dir.addLayer(FeatBacias, {}, "bacia");

Map_esq.addLayer(mosaic_norm_year, visualizar.visMosaic, "mosaic_norm");
Map_esq.addLayer(map_col6.select(banda_activa), visualizar.visclass, "col 6");


var linker = ui.Map.Linker([Map_esq, Map_dir]);
Map_dir.setCenter(-39.259, -9.092, 10)

var splitPanel = new ui.SplitPanel({
    firstPanel: linker.get(0),
    secondPanel: linker.get(1),
    orientation: 'horizontal',
    wipe: false,
    style: {
        stretch: 'both'
    }
});


function atualizar_visualization() {

    banda_activa = "classification_" + year_show
  
    var lay_mosaic_norm_d = Map_dir.layers().get(1);
    var mlayer_ver= Map_dir.layers().get(2);    
    var map_lay_ba = Map_dir.layers().get(3);
    
    Map_dir.layers().remove(map_lay_ba);    
    Map_dir.layers().remove(mlayer_ver);
    Map_dir.layers().remove(lay_mosaic_norm_d);

    var lay_mosaic_norm_e = Map_esq.layers().get(1);  
    var mlayer_col6 = Map_esq.layers().get(2);  

    Map_esq.layers().remove(lay_mosaic_norm_e);
    Map_esq.layers().remove(mlayer_col6);

    var bacia_selected = shp_bacias;

    mosaic_norm_year = mosaic_norm.filter(ee.Filter.eq('year', parseInt(year_show))).median();
    // images classificadas selecionadas por ano 
    var map_vers = map_ver.select(banda_activa);

   
    var lay_mosaic_norm_dir = ui.Map.Layer(mosaic_norm_year, visualizar.visMosaic, 'mosaic_norm', true);
    var lay_mosaic_norm_esq = ui.Map.Layer(mosaic_norm_year, visualizar.visMosaic, 'mosaic_norm', true);  
    var mlayer_version = ui.Map.Layer(map_vers, visualizar.visclass, "ver Class" );   

    var mlayer_col6 = ui.Map.Layer(map_col6.select(banda_activa), visualizar.visclass, "Col 6" );
    

    FeatBacias = ee.Image().byte().paint(bacia_selected, 1, 1);
    FeatBacias = FeatBacias.visualize({palette: 'FF0000', 'opacity': 0.7});
    map_lay_ba = ui.Map.Layer(FeatBacias, {}, "ba-" , true);

    Map_dir.layers().insert(1, lay_mosaic_norm_dir);
    Map_dir.layers().insert(2, mlayer_version);    
    Map_dir.layers().insert(3, map_lay_ba);

    
    Map_esq.layers().insert(1, lay_mosaic_norm_esq);
    Map_esq.layers().insert(2, mlayer_col6);
    
    Map_dir.centerObject(bacia_selected, 8);   

}


var panel0 = ui.Panel([splitPanel],
    ui.Panel.Layout.Flow('vertical', true), {
        stretch: 'both'
    }
);

Map_dir.setCenter(-39.259, -9.092, 10)
var panel_region = ui.Panel([label_ini, button_Merge, button_vis, label_fin],
                                ui.Panel.Layout.Flow('horizontal'), 
                                {
                                    border: '2px solid black',
                                    height: '50px',
                                }
                            );

var panel_parametro = ui.Panel([panel_region],
                                ui.Panel.Layout.Flow('vertical'), {

                                }
                            );
var panel = ui.Panel([panel_parametro, panel0, barra_year],
                        ui.Panel.Layout.Flow('vertical'), {
                            stretch: 'both'
                        }
                    );

ui.root.widgets().reset([panel]);
ui.root.setLayout(ui.Panel.Layout.Flow('vertical'));

