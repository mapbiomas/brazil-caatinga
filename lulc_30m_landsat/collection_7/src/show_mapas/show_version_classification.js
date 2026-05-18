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
    assetMap: 'projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1',
    // assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_GF',
    assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Sp',
    // assetclass : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Fq',
    asset_filted : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classificationV6',
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
var yearcourrent = 2000;
var banda_activa = 'classification_' + String(yearcourrent)
var FeatColbacia = ee.FeatureCollection(param.assetBacia);
var imgMapCol6= ee.Image(param.assetMap).clip(FeatColbacia.geometry());
var imgMapColfV1 =  ee.ImageCollection(param.assetclass)
                                  .filter(ee.Filter.eq('version', '1')).max();  
var imgMapColfV2 =  ee.ImageCollection(param.assetclass)
                                  .filter(ee.Filter.eq('version', '2')).max();

var bacias = FeatColbacia.filterBounds(points)
var lst = bacias.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list')
print("bacias faltantes ", lst)


print("imagem no Asset Geral Mapbiomas Col 6", imgMapCol6);
print("imagem no Asset Geral X Bacias col 7", imgMapColfV1);

var Mosaicos = ee.ImageCollection(param.assetIm).filter(
                        ee.Filter.eq('biome', 'CAATINGA')).select(param.bandas);
var mosaic_year = Mosaicos.filter(ee.Filter.eq('year', yearcourrent)).median()                     
Map.addLayer(FeatColbacia, {colro: 'green'}, 'bacia')
Map.addLayer(mosaic_year, visualizar.visMosaic,'Mosaic Col7');

var imgMapCol6temp = imgMapCol6.select(banda_activa).remap(param.classMapB, param.classNew);
Map.addLayer(imgMapCol6temp, visualizar.visclassCC,'Col6_' + String(yearcourrent), false);
Map.addLayer(imgMapColfV1.select(banda_activa),  visualizar.visclassCC, 'Col7_ClassV1')
Map.addLayer(imgMapColfV2.select(banda_activa),  visualizar.visclassCC, 'Col7_ClassV2')




