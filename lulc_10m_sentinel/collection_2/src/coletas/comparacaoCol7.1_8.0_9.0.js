

var Palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = Palettes.get('classification8');
var vis = {
    cobertura : {
        'min': 0,
        'max': 62,
        'palette': palette,
        'format': 'png'
    },
    diferencia: {
        'min': 1,
        'max': 2,
        'palette': 'd52a14,a2d514',
        'format': 'png'
    },
    stable: {
        'min': 0,
        'max': 1,
        'palette': '#ffb703',
        'format': 'png'
    },
    fire: {
        'min': 0,
        'max': 1,
        'palette': '#780000',
        'format': 'png'
    }, //6c584c
    coincidentes: {
        'min': 0,
        'max': 1,
        'palette': '#6c584c',
        'format': 'png'
    },
};
var param = {
    'assetMapbiomas60': 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
    'assetMapbiomas71': 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
    'assetMapbiomas80': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
    'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1', 
    'asset_estaveis': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_estaveis_v2',
    'asset_fire_mask': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5',
    'asset_Coincidencia': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_coinciden',
    "showLegend": true
}

Map.addLayer(ee.Image.constant(1), {min: 0, max: 1}, 'base');
var asset_ImBiomas = 'projects/mapbiomas-workspace/AUXILIAR/biomas-2019-raster';
var limitBioma = ee.Image(asset_ImBiomas).eq(5).selfMask();
Map.addLayer(limitBioma, {}, 'Bioma Raster', false)

// Define a list of years to export
var years = [
    '1985', '1986', '1987', '1988', '1989', 
    '1990', '1991', '1992', '1993', '1994', 
    '1995', '1996', '1997', '1998', '1999', 
    '2000', '2001', '2002', '2003', '2004', 
    '2005', '2006', '2007', '2008', '2009', 
    '2010', '2011', '2012', '2013', '2014', 
    '2015', '2016', '2017', '2018', '2019', 
    '2020', '2021', '2022'
];

//var years = [2021]
var igual_Class71_90 = null;    
var maskChangeCC71_90 = null;  
var igual_Class80_90 = null;     
var maskChangeCC80_90 = null; 


var class_in =  [3,4,5,6,49,11,12,13,32,29,50,15,19,39,20,40,62,41,36,46,47,48,9,21,22,23,24,30,25,33,31]
var class_out = [3,4,3,6,3,11,12,12,12,29,12,21,21,21,21,21,21,21,21,21,21,21,21,21,25,25,25,25,25,33,33]

years.forEach(function(year) {  
    var band_activa = 'classification_' + year;
    // 7.1 - Classificação Integração 
    var mapsCol71 = ee.Image(param.assetMapbiomas71)
                                    .mask(limitBioma).select(band_activa)
                                    .remap(class_in, class_out)//.rename('class')
    
    // 8.0 - Classificação Integração 
    var mapsCol80 = ee.Image(param.assetMapbiomas80)
                        .mask(limitBioma).select(band_activa)
                        .remap(class_in, class_out)//.rename('class')
    
    // 9.0 - Classificação Integração 
    var mapsCol90 = ee.Image(param.assetMapbiomas90)
                            .mask(limitBioma).select(band_activa)
                            .remap(class_in, class_out)//.rename('class')

    var raster_stable = ee.ImageCollection(param.asset_estaveis)
                                .mosaic().select('mask_estavel_' + year);
    print("raster stable ", raster_stable);

    var raster_fire = ee.ImageCollection(param.asset_fire_mask)
                                .mosaic().select("mask5wfire_" + year)
    print("raster fire ", raster_fire);

    var raster_coincid = ee.ImageCollection(param.asset_Coincidencia)
                                .mosaic().select("coincidencia_" + year)
    print("raster coincidentes  ", raster_coincid);

    
    igual_Class71_90 = mapsCol71.eq(mapsCol90).remap([1],[2]);    
    maskChangeCC71_90 = limitBioma.blend(igual_Class71_90);
    igual_Class80_90 = mapsCol80.eq(mapsCol90).remap([1],[2]);    
    maskChangeCC80_90 = limitBioma.blend(igual_Class80_90);
    
    
    Map.addLayer(mapsCol71, vis.cobertura, 'Col 7.1 '+ year, false);
    Map.addLayer(mapsCol80, vis.cobertura, 'Col 8.0 '+ year, false);
    Map.addLayer(mapsCol90, vis.cobertura, 'Col 9.0 '+ year, false);

    Map.addLayer(maskChangeCC71_90, vis.diferencia, 'maskChGTBcc71_90_'+ year, false); 
    Map.addLayer(maskChangeCC80_90, vis.diferencia, 'maskChGTBcc80_90_'+ year, false);
    Map.addLayer(raster_stable, vis.stable, 'stable_C90_'+ year, false);
    Map.addLayer(raster_fire.eq(0).selfMask(), vis.fire, 'fire_C90_'+ year, false);
    Map.addLayer(raster_coincid.lt(3).selfMask(), vis.coincidentes, 'coincid_C90_'+ year, false);
    // if (year === '1985'){
    //     class_mask_final = mask_final.rename('mask_' + year) 
    // }else{
    //     class_mask_final = class_mask_final.addBands(mask_final.rename('mask_' + year)); 
    // }
  
})

if (param.showLegend){
    var legend = ui.Panel({style: {position: 'bottom-center', padding: '8px 15px'}}); 

    var makeRow = function(color, name) {
    var colorBox = ui.Label({
        style: {color: '#ffffff',
        backgroundColor: color,
        padding: '10px',
        margin: '0 0 4px 0',
        }
    });
    var description = ui.Label({
        value: name,
        style: {
        margin: '0px 0 4px 6px',
        }
    }); 
    return ui.Panel({
        widgets: [colorBox, description],
        layout: ui.Panel.Layout.Flow('horizontal')}
    )};

    var title = ui.Label({
    value: 'Pixels change',
    style: {fontWeight: 'bold',
        fontSize: '16px',
        margin: '0px 0 4px 0px'}});

    legend.add(title);
    legend.add(makeRow('#d52a14','1 - Pixels com Mudanças'));
    legend.add(makeRow('#a2d514','2 - Pixels Estaveis'));
    Map.add(legend);

}