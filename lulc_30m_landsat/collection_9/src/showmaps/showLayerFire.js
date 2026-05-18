//var imageVisParam = {"opacity":1,"bands":["classes"],"min":1,"palette":["cecece","dae792","ff9a7c","ef00ff","ff3131"]};
var palettes = require('users/mapbiomas/modules:Palettes.js');
var legend = ui.Panel({style: {position: 'middle-right', padding: '8px 15px'}});
var vis = {
    visFire: {
        max: 1,
        min: 0,
        palette: [
            '#cb181d'
        ]
    },
    colecao: { 
        'min': 0, 
        'max': 62,  
        'palette': palettes.get('classification8')
    }
};
var anos = [
    1985,1986,1987,1988,1989,1990,1991,1992,1993,1994,
    1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,
    2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,
    2015,2016,2017,2018,2019,2020
];
Map.addLayer(ee.Image.constant(1), {min: 0, max: 1}, 'base');

var params = {
    asset_Col6 : 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
    asset_Col7 : 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
    asset_Col8 : 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
    asset_biomas: 'projects/mapbiomas-workspace/AUXILIAR/biomas-2019-raster',
    asset_sphBiomas: "projects/mapbiomas-workspace/AUXILIAR/biomas-2019",
    asset_fire: 'projects/mapbiomas-workspace/FOGO_COL2/SUBPRODUTOS/mapbiomas-fire-collection2-annual-burned-v1',
    lstClassMB:  [3, 4, 5,49, 9, 11, 12, 13, 29, 50, 15, 21, 23, 24, 25, 30, 31, 33, 39, 20, 40, 62, 41, 36, 46, 47, 48],
    lstClassRC:  [3, 4, 3, 3,22, 12, 12, 12, 12, 12, 21, 21, 22, 22, 22, 30, 33, 33, 21, 21, 21, 21, 21, 21, 21, 21, 21]
}

var anoSelect = '2020';
// --- --- --- Caaatinga --------------------------

var biomas = ee.Image(params.asset_biomas).eq(5).selfMask();
var col6 = ee.Image(params.asset_Col6).updateMask(biomas);
var col71 = ee.Image(params.asset_Col7).updateMask(biomas);
var col8 = ee.Image(params.asset_Col8).updateMask(biomas);

var imColFire = ee.Image(params.asset_fire).updateMask(biomas);
print("Coleção 2 de Fire por ano ",imColFire );

//============ camadas mapbiomas 6.0 -- 7.1 -- 8.0 ===================
var img6 = col6.select('classification_' + anoSelect )
                    .remap(params.lstClassMB, params.lstClassRC)
                    .rename('c6_class_' + anoSelect);    
var img71 = col71.select('classification_' + anoSelect )
                .remap(params.lstClassMB, params.lstClassRC)
                .rename('c71_class_' + anoSelect);   
var img8 = col8.select('classification_' + anoSelect )
                .remap(params.lstClassMB, params.lstClassRC)
                .rename('c8_class_' + anoSelect);

Map.addLayer(img6, vis.colecao, 'col 6.0_' + anoSelect, false);
Map.addLayer(img71, vis.colecao, 'col 7.1_' + anoSelect, false);
Map.addLayer(img8, vis.colecao, 'col 8.0_' + anoSelect, false);
Map.addLayer(imColFire.select("burned_area_" + anoSelect), vis.visFire, 'Fire' + anoSelect);