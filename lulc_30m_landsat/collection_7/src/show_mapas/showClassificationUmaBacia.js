var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text')

var visualizar = {
    visclassCC: {
            "min": 0, 
            "max": 45,
            "palette":  palettes.get('classification6'),
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
    assetMap: 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
    assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classificationV2',
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',    
    assetBacia: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",    
    anos: ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
           '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
           '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
           '2015','2016','2017','2018','2019'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    
    listaNameBacias: [
        '741','7421','7422','744','745','746','7492','751','752',
        '753', '754','755','756','757','758','759','7621','7622','763',
        '764','765','766','767','771','772','773', '7741','7742','775',
        '776','777','778','76111','76116','7612','7613','7614','7615',
        '7616','7617','7618','7619'
    ],
    classMapB: [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45],
    classNew: [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33, 21,33,33,21,21,21,21,21,21,21]

}
var selBacia = '741';
var yearcourrent = 2020;
var FeatColbacia = ee.FeatureCollection(param.assetBacia);
var imgMapCol6= ee.Image(param.assetMap).clip(FeatColbacia.geometry());
var imgMapCol7= ee.ImageCollection(param.assetclass).min();

print("imagem no Asset Geral Mapbiomas Col 6", imgMapCol6);
print("imagem no Asset Geral X Bacias col 7", imgMapCol7);

var Mosaicos = ee.ImageCollection(param.assetIm).filter(
                        ee.Filter.eq('biome', 'CAATINGA')).select(param.bandas);


var MapMosaic = ui.Map.Layer({
                            "eeObject": Mosaicos.filter(ee.Filter.eq('year', yearcourrent)).median(),
                            'visParams': visualizar.visMosaic,
                            'name': 'Mosaic Col7',
                            'shown': true,
                            'opacity': 1
                        })
var imgMapCol6temp = imgMapCol6.select('classification_' + String(yearcourrent)).remap(param.classMapB, param.classNew);
var MapCol6 = ui.Map.Layer({
                    "eeObject": imgMapCol6temp,
                    'visParams': visualizar.visclassCC,
                    'name': 'Col6_' + String(yearcourrent),
                    'shown': false,
                    'opacity': 1
                })

var MapCol7 = ui.Map.Layer({
                    "eeObject": imgMapCol7.select('classification_' + String(yearcourrent)),
                    'visParams': visualizar.visclassCC,
                    'name': 'Col7_Class',
                    'shown': true,
                    'opacity': 1
                })



Map.add(MapMosaic);
Map.add(MapCol6);
Map.add(MapCol7)