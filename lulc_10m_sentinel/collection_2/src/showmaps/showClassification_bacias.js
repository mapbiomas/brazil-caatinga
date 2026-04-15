
var param = { 
    assetMap: 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',   
    assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX',  
    // assetclass_pos : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/toExport',     
    // assetclass_pos : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill',  
    // assetclass_pos: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/ilumination', 
    assetclass_pos: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/grass_Aflor', 
    assetclass_posCW: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/clean_water',
    asset_mosaicS2: 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3',  
    asset_mosaicL: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',  
    assetBacia: 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',   
    asset_region_img_buffer: 'projects/ee-solkancengine17/assets/bacias_imagem',      
    years: ['2016','2017','2018','2019','2020','2021','2022','2023'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    classMapB : [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62],
    classNew  : [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21,21,21,21, 4,12,21],
    //'743','732','747',
    listaNameBacias: [
        'all','7754', '7691', '7581', '7625', '7584', '751', '752', '7616', '745', '7424', '773', 
        '7612', '7613', '7614', '7618', '7561', '755', '7617', '7564', '761111', '761112', 
        '7741', '7422', '76116', '7761', '7671', '7615', '7411', '7764', '757', '771', '7712', 
        '766', '7746', '753','764', '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
        '763', '7591', '7592', '7622', '746'
    ],       
    listBiomas: ['CERRADO','CAATINGA','MATAATLANTICA']
}
var palettes = require('users/mapbiomas/modules:Palettes.js');
var visualizar = {
    visclass: {
            "min": 0, 
            "max": 62,
            "palette":  palettes.get('classification8'),
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
var raster_bacias = ee.ImageCollection(param.asset_region_img_buffer);
var mosaic_S2 = ee.ImageCollection(param.asset_mosaicS2).filter(
                                ee.Filter.inList('biome', param.listBiomas)).select(
                                    param.bandas);

var mosaic_L8 = ee.ImageCollection(param.asset_mosaicL).filter(
                                        ee.Filter.inList('biome', param.listBiomas)).select(
                                            param.bandas);


var map_col90 = ee.Image(param.assetMap).updateMask(raster_bacias.mosaic().gt(0));
print("map_col90 ",map_col90);
var year_show = '2023';
var versAct = '4';
var banda_activa = "classification_" + year_show;
var bacia_activa = "All Basin";
// var banda_ref = "CLASS_" +  year_show;
//var bacia_focused = '741';
var mapS2_version = ee.ImageCollection(param.assetclass)
                        .filter(ee.Filter.eq('version', versAct)).min();
var mapS2_versPos = ee.ImageCollection(param.assetclass_pos)
                        .filter(ee.Filter.eq('version', parseInt(versAct)));

var mapS2_versPosCW = ee.ImageCollection(param.assetclass_posCW)
                        .filter(ee.Filter.eq('version', parseInt(versAct)));

if (param.assetclass_pos.indexOf('grass_Aflor') !== -1){
    mapS2_versPos = mapS2_versPos.filter(ee.Filter.eq('type_filter', 'grassland'));
}else if (param.assetclass_pos.indexOf('Temporal') !== -1){
    mapS2_versPos = mapS2_versPos.filter(ee.Filter.eq('janela', cJanela));
}                       
print("show metadata fof maps versions coleção S2 ", mapS2_versPos);
print("know the size collection ", mapS2_versPos.size());



// --- chart -------------------------------------------------------------------
var collection_param = param.years.map(function (year_current) {
    return ee.Feature(null, {
        'year': year_current,
        'class_bnd': 'classification_' + year_current,        
        'system_yValue': 0
    });
});

var barra_year = ui.Chart.feature.byFeature(collection_param, 'year', 'system_yValue')
    .setChartType('LineChart')
    .setOptions({
        legend: 'none',
        lineWidth: 1,
        pointSize: 5,
        height: '60px',
        width: '100%',
        margin: '0px',
        padding: '0px',
        vAxis: {
            gridlines: {
                count: 0
            }
        },
        chartArea: {
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
var textbox_Bacia = ui.Textbox({ 
    placeholder: "All Basin", 
    value: 'All Basin',
    onChange: function(text){
        bacia_activa = String(text);
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
textbox_Bacia.style().set({
    position: 'bottom-center',
    width: '15%',
    height: '85px',
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

Map_esq.setOptions("SATELLITE");
Map_dir.setOptions("SATELLITE");

var FeatBacias = ee.Image().byte().paint(shp_bacias, 1, 1);
FeatBacias = FeatBacias.visualize({palette: 'FF0000', 'opacity': 0.7});

var mosaic_S2_year = mosaic_S2.filter(ee.Filter.eq('year', parseInt(year_show))).median();
mosaic_S2_year = mosaic_S2_year.updateMask(raster_bacias.mosaic().gt(0));

var mosaic_L8_year = mosaic_L8.filter(ee.Filter.eq('year', parseInt(year_show))).median();
mosaic_L8_year = mosaic_L8_year.updateMask(raster_bacias.mosaic().gt(0));

Map_dir.addLayer(mosaic_S2_year, visualizar.visMosaic, "mosaic_S2 ");

var map_Vers = mapS2_version.select(banda_activa).remap(param.classMapB, param.classNew);  
var map_Vers_Poss = mapS2_versPos.max().select(banda_activa).remap(param.classMapB, param.classNew);
var map_Vers_PossCW = mapS2_versPosCW.max().select(banda_activa).remap(param.classMapB, param.classNew);
Map_dir.addLayer(map_Vers, visualizar.visclass, "Map S2 v" + versAct + ' ' + year_show);
Map_dir.addLayer(map_Vers_Poss, visualizar.visclass, "Map poss S2 v" + versAct + ' ' + year_show);
Map_dir.addLayer(map_Vers_PossCW, visualizar.visclass, "Map poss CW S2 v" + versAct + ' ' + year_show);
Map_dir.addLayer(FeatBacias, {}, "bacia");

Map_esq.addLayer(mosaic_L8_year, visualizar.visMosaic, "mosaic_L8");
Map_esq.addLayer(map_col90.select(banda_activa), visualizar.visclass, "col 9.0 " + year_show);


var linker = ui.Map.Linker([Map_esq, Map_dir]);
Map_dir.setCenter(-40.45, -9.669, 13);

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
    // var lay_mosaic_norm_d0 = Map_dir.layers().get(0);
    var lay_mosaic_norm_d = Map_dir.layers().get(0);
    var mlayer_ver= Map_dir.layers().get(1);    
    var map_lay_ba = Map_dir.layers().get(2);
    var mapPoss_lay_ba = Map_dir.layers().get(3);
    var mapPossCW_lay_ba = Map_dir.layers().get(4);
    var mShape_ba = Map_dir.layers().get(5);
    
    Map_dir.layers().remove(mShape_ba);
    Map_dir.layers().remove(mapPoss_lay_ba);
    Map_dir.layers().remove(mapPossCW_lay_ba);
    Map_dir.layers().remove(map_lay_ba);    
    Map_dir.layers().remove(mlayer_ver);
    Map_dir.layers().remove(lay_mosaic_norm_d);
    

    var lay_mosaic_norm_e = Map_esq.layers().get(0);  
    var mlayer_col9 = Map_esq.layers().get(1);  

    Map_esq.layers().remove(lay_mosaic_norm_e);
    Map_esq.layers().remove(mlayer_col9);

    mosaic_S2_year = mosaic_S2.filter(ee.Filter.eq('year', parseInt(year_show)))
                                    .median().updateMask(raster_bacias.mosaic().gt(0));
    mosaic_L8_year = mosaic_L8.filter(ee.Filter.eq('year', parseInt(year_show)))
                                    .median().updateMask(raster_bacias.mosaic().gt(0));
                                
    // images classificadas selecionadas por ano 
    map_Vers = mapS2_version.select(banda_activa).remap(param.classMapB, param.classNew);
    map_Vers_Poss = mapS2_versPos.select(banda_activa).remap(param.classMapB, param.classNew);
    map_Vers_PossCW = mapS2_versPosCW.select(banda_activa).remap(param.classMapB, param.classNew);
   
    var lay_mosaic_norm_dir = ui.Map.Layer(mosaic_S2_year, visualizar.visMosaic, 'mosaic_S2', true);
    var lay_mosaic_norm_esq = ui.Map.Layer(mosaic_L8_year, visualizar.visMosaic, 'mosaic_L8', true);  
    var mlayer_version = ui.Map.Layer(map_Vers, visualizar.visclass, "Map S2 v" + versAct + ' ' + year_show);  
    var mlayer_versionPoss = ui.Map.Layer(map_Vers_Poss, visualizar.visclass, "Map Poss S2 v" + versAct + ' ' + year_show); 
    var mlayer_versionPossCW = ui.Map.Layer(map_Vers_PossCW, visualizar.visclass, "Map Poss S2 v" + versAct + ' ' + year_show); 
    var mlayer_Col9 = ui.Map.Layer(map_col90.select(banda_activa), visualizar.visclass, "Col 90_ " + year_show);

    FeatBacias = ee.Image().byte().paint(shp_bacias, 1, 1);
    FeatBacias = FeatBacias.visualize({palette: 'FF0000', 'opacity': 0.7});
    map_lay_ba = ui.Map.Layer(FeatBacias, {}, "bacias SHP" , true);

    Map_dir.layers().insert(1, lay_mosaic_norm_dir);
    Map_dir.layers().insert(2, mlayer_version);    
    Map_dir.layers().insert(3, mlayer_versionPoss);
    Map_dir.layers().insert(4, mlayer_versionPossCW);
    Map_dir.layers().insert(5, map_lay_ba);

    
    Map_esq.layers().insert(1, lay_mosaic_norm_esq);
    Map_esq.layers().insert(2, mlayer_Col9);    
    
    if (bacia_activa !== "All Basin"){
        var featBacia = shp_bacias.filter(ee.Filter.eq('nunivotto4', bacia_activa));
        var layerShpBacia = ui.Map.Layer(featBacia, {color: 'red'}, 'Bacia Inspect', true);
        Map_dir.layers().insert(5, layerShpBacia);
    }
}


var panel0 = ui.Panel([splitPanel],
    ui.Panel.Layout.Flow('vertical', true), {
        stretch: 'both'
    }
);

// Map_dir.setCenter(-39.259, -9.092, 10)
var panel_region = ui.Panel([label_ini, button_vis, textbox_Bacia, label_fin],
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

