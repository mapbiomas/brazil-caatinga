var param = { 
    assetMap: "projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV6_final/",
    //projects/mapbiomas-workspace/AMOSTRAS/col6/CAATINGA/classificacoes/classesV6_final/CAATINGA-1985-2
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/mosaics-normalized',    
    assetBacia: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",     
    
    years: ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
           '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
           '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
           '2015','2016','2017','2018','2019','2020'],
    bandas: ['red_median', 'green_median', 'blue_median'],

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
                                    ee.Filter.eq('collection', 6)).select(param.bandas);

var banda_activa = "classification_" + year_show;
var map_ver6_final;
var map_ver5_temporal;
param.years.forEach(function(yy){
    var img_year = "CAATINGA-" + yy;
    
    banda_activa = "classification_" + yy;
    var img_tmpv2 = ee.Image(param.assetMap + img_year +  '-2').rename(banda_activa);
    var img_tmpv1 = ee.Image(param.assetMap + img_year +  '-1').rename(banda_activa);
    if (yy === '1985'){
        map_ver6_final = img_tmpv2;
        map_ver5_temporal = img_tmpv1;
    }else{
        map_ver6_final = map_ver6_final.addBands(img_tmpv2);
        map_ver5_temporal = map_ver5_temporal.addBands(img_tmpv1);
    }
})



var year_show = '2020';
banda_activa = "classification_" + year_show


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
    atualizar_visualization(xValue)
    
});


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

print(mosaic_norm_year)
Map_dir.addLayer(mosaic_norm_year, visualizar.visMosaic, "mosaic_norm");
Map_dir.addLayer(map_ver6_final.select(banda_activa), visualizar.visclass, "ver 2 col6");

Map_dir.addLayer(FeatBacias, {}, "bacia");
Map_esq.addLayer(map_ver5_temporal.select(banda_activa), visualizar.visclass, "ver 1 col6");



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
  
    var lay_mosaic_norm_d = Map_dir.layers().get(0);
    var mlayer_v6_final = Map_dir.layers().get(1);
    var map_lay_ba = Map_dir.layers().get(2);
  

    var mlayer_v5_temp = Map_esq.layers().get(0);
    var mosaic_year;
    
    Map_dir.layers().remove(map_lay_ba);
    Map_dir.layers().remove(mlayer_v6_final);
    Map_dir.layers().remove(lay_mosaic_norm_d);

    Map_esq.layers().remove(mlayer_v5_temp);
    var bacia_selected = shp_bacias;
      

    mosaic_norm_year = mosaic_norm.filter(ee.Filter.eq('year', parseInt(year_show))).median();
    // images classificadas selecionadas por ano 
    var map_v6_final = map_ver6_final.select(banda_activa);
    var map_v5_temp = map_ver5_temporal.select(banda_activa) ;
    
   

    var lay_mosaic_norm_dir = ui.Map.Layer(mosaic_norm_year, visualizar.visMosaic, 'mosaic_norm', true);
    mlayer_v6_final = ui.Map.Layer(map_v6_final, visualizar.visclass, "ver 2 col6", true);    
    mlayer_v5_temp = ui.Map.Layer(map_v5_temp, visualizar.visclass, "ver 1 col6", true);

    FeatBacias = ee.Image().byte().paint(bacia_selected, 1, 1);
    FeatBacias = FeatBacias.visualize({palette: 'FF0000', 'opacity': 0.7});
    map_lay_ba = ui.Map.Layer(FeatBacias, {}, "bacia", true);

    Map_dir.layers().insert(0, lay_mosaic_norm_dir);
    Map_dir.layers().insert(1, mlayer_v6_final);    
    Map_dir.layers().insert(2, map_lay_ba);


    Map_esq.layers().insert(0, mlayer_v5_temp);    
    
    // if (bacia_focused != 'all'){
    //     Map_dir.centerObject(bacia_selected, 8)
    // }

}


var panel0 = ui.Panel([splitPanel],
    ui.Panel.Layout.Flow('vertical', true), {
        stretch: 'both'
    }
);


var panel = ui.Panel([panel0, barra_year],
                        ui.Panel.Layout.Flow('vertical'), {
                            stretch: 'both'
                        }
                    );

ui.root.widgets().reset([panel]);
ui.root.setLayout(ui.Panel.Layout.Flow('vertical'));

