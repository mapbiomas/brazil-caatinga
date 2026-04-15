

/**
 * import modules
 */
var bns = require('users/mapbiomas/mapbiomas-mosaics:modules/BandNames.js');
var csm = require('users/mapbiomas/mapbiomas-mosaics:modules/CloudAndShadowMasking.js');
var col = require('users/mapbiomas/mapbiomas-mosaics:modules/Collection.js');
var dtp = require('users/mapbiomas/mapbiomas-mosaics:modules/DataType.js');
var ind = require('users/mapbiomas/mapbiomas-mosaics:modules/SpectralIndexes.js');
var mis = require('users/mapbiomas/mapbiomas-mosaics:modules/Miscellaneous.js');
var mos = require('users/mapbiomas/mapbiomas-mosaics:modules/Mosaic.js');
var sma = require('users/mapbiomas/mapbiomas-mosaics:modules/SmaAndNdfi.js');
var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text');
var visualizar = {
    visclassCC: {
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
    vismosaicoGEE: {
        'min': 0.001, 'max': 0.4,
        bands: ['red', 'green', 'blue']
    },
    props: {  
        textColor: 'ff0000', 
        outlineColor: 'ffffff', 
        outlineWidth: 1.5, 
        outlineOpacity: 0.2
    }
} 
// Spectral bands selected
var spectralBands = ['blue', 'red', 'green', 'nir', 'swir1', 'swir2'];
var param = { 
    assetMapC80: 'projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1',
    assetMapC90: 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
    asset_MapCX : 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyVA',
    assetrecorteCaatCerrMA : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/recorteCaatCeMA',
    asset_bacias_raster: 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',  
    asset_collectionId: 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    assetBacia: 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',    
    anos: ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
           '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
           '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
           '2015','2016','2017','2018','2019','2020','2021','2022','2023','2024'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    
    listaNameBacias: [
        '741','7421','7422','744','745','746','7492','751','752',
        '753', '754','755','756','757','758','759','7621','7622','763',
        '764','765','766','767','771','772','773', '7741','7742','775',
        '776','777','778','76111','76116','7612','7613','7614','7615',
        '7616','7617','7618','7619'
    ],
    classMapB: [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,40,41,46,47,48,49,50,62],
    classNew:  [3, 4, 3, 3,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,18,18,18,18,18,18, 3,12,18],
    listValbaciasN1: [106,103,107,104,110]
}
var selBacia = 'all';
var yearcourrent = 2020;
var dateStart = ee.Date.fromYMD(yearcourrent, 1, 1);
var dateEnd = ee.Date.fromYMD(yearcourrent, 12, 31);
var version = 1;
var assetCol10 = param.asset_MapCX;
// if (version > 5){
//     assetCol9 = param.asset_MapC9P;
// }
var banda_activa = 'classification_' + String(yearcourrent);
print("banda activa ", banda_activa);

// Regions Caatinga, parte do Cerrado e Mata Atlântica 
var limitBoundCaat = ee.FeatureCollection(param.assetrecorteCaatCerrMA)

var FeatColbacia = ee.FeatureCollection(param.assetBacia);
var baciaRaster = ee.ImageCollection(param.asset_bacias_raster).max().gt(0);
// var maskBacia = baciaRaster.eq(104).add(baciaRaster.eq(103))
//                           .add(baciaRaster.eq(106)).add(baciaRaster.eq(107));
                          
var imgMapCol8 = ee.Image(param.assetMapC80).select(banda_activa);
var imgMapCol9 = ee.Image(param.assetMapC90).select(banda_activa);
print("imgMapCol8 ", imgMapCol8);
print("imgMapCol9 ", imgMapCol9);

var imgMapCol10GTB =  ee.ImageCollection(assetCol10)
                            .filter(ee.Filter.eq('version', version))
                            .select(banda_activa);
                            // .max().clip(shp_limit.geometry());
print(" show metadata of  imgMapCol10GTB", imgMapCol10GTB);
                            
var Mosaicos = ee.ImageCollection(param.assetIm).filter(
                        ee.Filter.eq('biome', 'CAATINGA')).select(param.bandas);

var collectionGEE = ee.ImageCollection(param.asset_collectionId)
                        .filter(ee.Filter.date(dateStart, dateEnd))
                        .filter(ee.Filter.bounds(limitBoundCaat))
                        .mosaic().updateMask(baciaRaster)
                        .select(spectralBands);    

// ========================================================================= //
// set as 'all' to show all map or set the basin from pamareter dictionary
// ========================================================================= //
var imgMapCol10GTBjoin = null;
if (selBacia === 'all'){    
    imgMapCol10GTBjoin = imgMapCol10GTB.min();

}else{
    FeatColbacia = FeatColbacia.filter(ee.Filter.eq('nunivotto4', selBacia));   
    imgMapCol10GTBjoin = imgMapCol10GTB.filter(ee.Filter.eq("id_bacia", selBacia)); 
    Mosaicos = Mosaicos.filterBounds(FeatColbacia);
}

print(" 📍 imagem no Asset Geral Mapbiomas Col 8.0  ‼️", imgMapCol8);
print(" 📍 imagem no Asset Geral Mapbiomas Col 9.0  ‼️", imgMapCol9);
print(" 📍 imagem no Asset Geral X Bacias col 10 GTB", imgMapCol10GTB);

var mosaic_year = Mosaicos.filter(ee.Filter.eq('year', yearcourrent))
                      .median().updateMask(baciaRaster);                     
Map.addLayer(FeatColbacia, {color: 'green'}, 'bacia');
Map.addLayer(mosaic_year, visualizar.visMosaic,'Mosaic Col8', false);
Map.addLayer(imgMapCol8, visualizar.visclassCC,'Col80_' + String(yearcourrent), false);
Map.addLayer(imgMapCol9,  visualizar.visclassCC, 'Col90_'+ String(yearcourrent), false);
Map.addLayer(collectionGEE, visualizar.vismosaicoGEE,'Mosaic GEE', true);
Map.addLayer(imgMapCol10GTBjoin,  visualizar.visclassCC, 'Class GTB' + String(version), true);









