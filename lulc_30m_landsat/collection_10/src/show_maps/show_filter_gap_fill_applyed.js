
var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text');
var visualizar = {
    visclassCC: {
            "min": 0, 
            "max": 69,
            "palette":  palettes.get('classification9'),
            "format": "png"
    },
    vismosaicoGEE: {
        'min': 0.001, 'max': 0.15,
        bands: ['red', 'green', 'blue']
    },
    
} 
var  options = {
    'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill',
    'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyVA',
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    'asset_collectionId': 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    'version_input': 10,
    'version_output': 10,
    'years': ['1985','1986','1987','1988','1989','1990','1991','1992']
    
}

var mosaicEE = ee.ImageCollection(options.asset_collectionId);
var img_col_gaps = ee.ImageCollection(options.input_asset)
                            .filter(ee.Filter.eq('version', options.version_input));
print(" Show metadata of map classification ", img_col_gaps);
var img_col_applied = ee.ImageCollection(options.output_asset)
                            .filter(ee.Filter.eq('version', options.version_output));


options.years.forEach(function(nyear){
    var band_activate = 'classification_' + nyear;
    var img_year_gaps = img_col_gaps.mosaic().select(band_activate);
    print("show metadata from img Year of gaps", img_year_gaps);
    var img_year_fapplied = img_col_applied.mosaic().select(band_activate);

    var dateStart = ee.Date.fromYMD(parseInt(nyear), 1, 1);
    var dateEnd = ee.Date.fromYMD(parseInt(nyear), 12, 31);
    var mosGEEyy = mosaicEE.filter(ee.Filter.date(dateStart, dateEnd)).median();
    
    Map.addLayer(mosGEEyy, visualizar.vismosaicoGEE, 'Mosaico EE' + nyear, false);
    Map.addLayer(img_year_gaps, visualizar.visclassCC, 'r-gaps ' + nyear, false);
    Map.addLayer(img_year_fapplied, visualizar.visclassCC, 'r-fapplied ' + nyear, false);
})