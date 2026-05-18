//https://code.earthengine.google.com/a439f870a02b371daf094c5b6cf6de34
//https://code.earthengine.google.com/c6be8cee51ed15cb9cd80c031f8f2729
var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text')

var visualizar = {
    visclassCC: {
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
    props: {  
        textColor: 'ff0000', 
        outlineColor: 'ffffff', 
        outlineWidth: 1.5, 
        outlineOpacity: 0.2
    }
} 

var param = { 
    assetMapC7: 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
    assetMapC8: 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
    asset_pre_mabiomas: 'projects/mapbiomas-workspace/COLECAO9/classificacao',
    asset_mixed: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    asset_caat_buffer: 'users/CartasSol/shapes/caatinga_buffer5km',
    asset_baciasN1raster: 'projects/mapbiomas-workspace/AUXILIAR/bacias-nivel-1-raster',
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',    
    assetBacia: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",    
    anos: ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
           '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
           '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
           '2015','2016','2017','2018','2019','2020','2021','2022'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    bioma: 'CAATINGA',
    listaNameBacias: [
        '741','7421','7422','744','745','746','7492','751','752',
        '753', '754','755','756','757','758','759','7621','7622','763',
        '764','765','766','767','771','772','773', '7741','7742','775',
        '776','777','778','76111','76116','7612','7613','7614','7615',
        '7616','7617','7618','7619'
    ],
    classMapB: [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,40,41,46,47,48,49,50,62],
    classNew:  [3, 4, 3, 3,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,18,18,18,18,18,18, 3,12,18],

}

var yearcourrent = 2020;
var version = '5';
var caatinga5km = ee.FeatureCollection(param.asset_caat_buffer).geometry();
var banda_activa = 'classification_' + String(yearcourrent)
var FeatColbacia = ee.FeatureCollection(param.assetBacia);

var imgMapCol71= ee.Image(param.assetMapC7).select(banda_activa).clip(caatinga5km);
var imgMapCol8= ee.Image(param.assetMapC8).select(banda_activa).clip(caatinga5km);

var imgMapCol9v5 =  ee.ImageCollection(param.asset_pre_mabiomas)
                            .filter(ee.Filter.eq("biome", param.bioma))
                            .filter(ee.Filter.eq('version', version))
                            .filter(ee.Filter.eq('year', yearcourrent))
                            .first()
print("  imgMapCol9v5", imgMapCol9v5);
var imgMapCol9v9 =  ee.ImageCollection(param.asset_pre_mabiomas)
                            .filter(ee.Filter.eq("biome", param.bioma))
                            .filter(ee.Filter.eq('version', '9'))
                            .filter(ee.Filter.eq('year', yearcourrent))
                            .first()
print("  imgMapCol9v9", imgMapCol9v9);

var Mosaicos = ee.ImageCollection(param.assetIm).filter(
                        ee.Filter.eq('biome', 'CAATINGA')).select(param.bandas);

// ========================================================================= //
// set as 'all' to show all map or set the basin from pamareter dictionary
// ========================================================================= //

print(" 📍 imagem no Asset Geral Mapbiomas Col 7.1  ‼️", imgMapCol71);
print(" 📍 imagem no Asset Geral Mapbiomas Col 8.0  ‼️", imgMapCol8);
print(" 📍 imagem no Asset Geral Mapbiomas col 9 version 5", imgMapCol9v5);
print(" 📍 imagem no Asset Geral  Mapbiomas col 9 version 9", imgMapCol9v9);

var mosaic_year = Mosaicos.filter(ee.Filter.eq('year', yearcourrent)).median();                     
Map.addLayer(FeatColbacia, {color: 'green'}, 'bacia');
Map.addLayer(mosaic_year, visualizar.visMosaic,'Mosaic Col8');


Map.addLayer(imgMapCol9v9,  visualizar.visclassCC, 'Class Vers 9', false);
Map.addLayer(imgMapCol9v5,  visualizar.visclassCC, 'Class vers 5', false);
Map.addLayer(imgMapCol71, visualizar.visclassCC,'Col71_' + String(yearcourrent), false);
Map.addLayer(imgMapCol8,  visualizar.visclassCC, 'Col8_'+ String(yearcourrent), false);






