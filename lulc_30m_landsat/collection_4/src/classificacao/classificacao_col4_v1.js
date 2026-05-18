
// Compute a cloud score.  This expects the input image to have the common
// band names: ["red", "blue", etc], so it can work across sensors.
var cloudScore = function(img) {
    // A helper to apply an expression and linearly rescale the output.
    var rescale = function(img, exp, thresholds) {
      return img.expression(exp, {img: img})
          .subtract(thresholds[0]).divide(thresholds[1] - thresholds[0]);
    };
  
    // Compute several indicators of cloudyness and take the minimum of them.
    var score = ee.Image(1.0);
    // Clouds are reasonably bright in the blue band.
    score = score.min(rescale(img, 'img.blue', [0.1, 0.3]));
  
    // Clouds are reasonably bright in all visible bands.
    score = score.min(rescale(img, 'img.red + img.green + img.blue', [0.2, 0.8]));
  
    // Clouds are reasonably bright in all infrared bands.
    score = score.min(
        rescale(img, 'img.nir + img.swir1 + img.swir2', [0.3, 0.8]));
  
    // Clouds are reasonably cool in temperature.
    score = score.min(rescale(img, 'img.temp', [300, 290]));
  
    // However, clouds are not snow.
    var ndsi = img.normalizedDifference(['green', 'swir1']);
    return score.min(rescale(ndsi, 'img', [0.8, 0.6]));
  };

var processoExportar = function(mapaRF, nameB, ano, regionB){
    var assetoutRF = 'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/ver1/'  
    mapaRF = mapaRF.set('biome', 'CAATINGA')
    //mapaRF = mapaRF.set('grid_name', nameB)
    mapaRF = mapaRF.set('id_bacia', nameB)
    mapaRF = mapaRF.set('year', ano)
    //mapaRF = mapaRF.set('biome', 'CAATINGA')
    var nomeDesc = 'RF_'+ nameB + '_'+ ano
    
    var optExp = {
        image: mapaRF, 
        description: nomeDesc, 
        assetId:assetoutRF + nomeDesc , 
        pyramidingPolicy: {
            '.default': 'mode'
        },
        //dimensions, 
        region: regionB, 
        scale: 30, 
        maxPixels: 1e13
    }

    Export.image.toAsset(optExp)
}

var dict = ee.Dictionary({
    amp_evi2: 40
    ,amp_gv: 46
    ,amp_ndfi: 165
    ,amp_ndvi: 51
    ,amp_ndwi: 64
    ,amp_npv: 11
    ,amp_sefi: 36
    ,amp_soil: 11
    ,amp_wefi: 81
    ,ano: 2017
    ,carta: 'SE-23-X-A'
    ,'class': 27
    ,median_blue: 840
    ,median_blue_dry: 808
    ,median_blue_wet: 1071
    ,median_cai: 37
    ,median_cai_dry: 36
    ,median_cai_wet: 59
    ,median_cloud: 8
    ,median_evi2: 50
    ,median_evi2_dry: 12
    ,median_evi2_wet: 51
    ,median_fns: 200
    ,median_fns_dry: 175
    ,median_fns_wet: 200
    ,median_gcvi: 255
    ,median_gcvi_dry: 82
    ,median_gcvi_wet: 255
    ,median_green: 738
    ,median_green_dry: 701
    ,median_green_wet: 925
    ,median_gv: 45
    ,median_gvs: 78
    ,median_gvs_dry: 4
    ,median_gvs_wet: 78
    ,median_hallcover: 52123
    ,median_ndfi: 186
    ,median_ndfi_dry: 24
    ,median_ndfi_wet: 187
    ,median_ndvi: 75
    ,median_ndvi_dry: 26
    ,median_ndvi_wet: 75
    ,median_ndwi: 71
    ,median_ndwi_dry: 9
    ,median_ndwi_wet: 71
    ,median_nir: 3382
    ,median_nir_dry: 1554
    ,median_nir_wet: 3472
    ,median_npv: 6
    ,median_pri: 7
    ,median_pri_dry: 6
    ,median_pri_wet: 9
    ,median_red: 479
    ,median_red_dry: 458
    ,median_red_wet: 979
    ,median_savi: 49
    ,median_savi_dry: 13
    ,median_savi_wet: 50
    ,median_sefi: 200
    ,median_sefi_dry: 166
    ,median_sefi_wet: 200
    ,median_shade: 44
    ,median_soil: 0
    ,median_swir1: 1565
    ,median_swir1_dry: 1525
    ,median_swir1_wet: 2381
    ,median_swir2: 575
    ,median_swir2_dry: 553
    ,median_swir2_wet: 1398
    ,median_temp: 295
    ,median_wefi: 107
    ,median_wefi_dry: 32
    ,median_wefi_wet: 110
    ,min_blue: 803
    ,min_green: 698
    ,min_nir: 1539
    ,min_red: 447
    ,min_swir1: 1502
    ,min_swir2: 541
    ,min_temp: 295
    ,stdDev_blue: 107850
    ,stdDev_cai: 10331
    ,stdDev_cloud: 1572
    ,stdDev_evi2: 17426
    ,stdDev_fns: 11452
    ,stdDev_gcvi: 77628
    ,stdDev_green: 93673
    ,stdDev_gv: 20031
    ,stdDev_gvs: 33468
    ,stdDev_hallcover: 27139
    ,stdDev_ndfi: 72448
    ,stdDev_ndvi: 21984
    ,stdDev_ndwi: 28523
    ,stdDev_nir: 853992
    ,stdDev_npv: 4316
    ,stdDev_pri: 1613
    ,stdDev_red: 216071
    ,stdDev_savi: 16397
    ,stdDev_sefi: 15054
    ,stdDev_shade: 13016
    ,stdDev_soil: 4530
    ,stdDev_swir1: 361327
    ,stdDev_swir2: 365506
    ,stdDev_temp: 3721
    ,stdDev_wefi: 34880
})
//print(dict.size())
print(dict.keys())
var dictPtos = ee.Dictionary({
    amp_ev2: 12
    ,amp_gv: 14
    ,amp_ndf: 70
    ,amp_ndv: 22
    ,amp_ndw: 26
    ,amp_npv: 6
    ,amp_sef: 33
    ,amp_sol: 12
    ,amp_wef: 20
    ,ano: 2017
    ,carta: 'SE-23-X-A'
    ,'class': 27
    ,mdn_bl_d: 865
    ,mdn_bl_w: 1107
    ,mdn_c_d: 48
    ,mdn_c_w: 55
    ,mdn_cld: 6
    ,mdn_fns: 193
    ,mdn_fns_d: 172
    ,mdn_fns_w: 197
    ,mdn_gcv: 238
    ,mdn_gcv_d: 184
    ,mdn_gcv_w: 255
    ,mdn_grn: 790
    ,mdn_grn_d: 758
    ,mdn_grn_w: 1056
    ,mdn_gvs: 61
    ,mdn_gvs_d: 37
    ,mdn_gvs_w: 62
    ,mdn_hll: 52089
    ,mdn_ndf: 167
    ,mdn_ndf_d: 119
    ,mdn_ndf_w: 172
    ,mdn_ndv: 58
    ,mdn_ndv_d: 41
    ,mdn_ndv_w: 62
    ,mdn_ndw: 47
    ,mdn_ndw_d: 28
    ,mdn_ndw_w: 47
    ,mdn_npv: 9
    ,mdn_nr_d: 2651
    ,mdn_nr_w: 2860
    ,mdn_pr_d: 2
    ,mdn_pr_w: 6
    ,mdn_rd_d: 630
    ,mdn_rd_w: 1120
    ,mdn_sf_d: 170
    ,mdn_sf_w: 197
    ,mdn_shd: 56
    ,mdn_sv_d: 28
    ,mdn_sv_w: 37
    ,mdn_sw1: 1994
    ,mdn_sw2: 1010
    ,mdn_swr1_d: 1923
    ,mdn_swr1_w: 2870
    ,mdn_swr2_d: 952
    ,mdn_swr2_w: 1637
    ,mdn_tmp: 297
    ,mdn_v2_d: 27
    ,mdn_v2_w: 36
    ,mdn_wf_d: 70
    ,mdn_wf_w: 78
    ,medin_c: 50
    ,medn_bl: 931
    ,medn_gv: 27
    ,medn_nr: 2748
    ,medn_pr: 6
    ,medn_rd: 716
    ,medn_sf: 192
    ,medn_sl: 3
    ,medn_sv: 36
    ,medn_v2: 36
    ,medn_wf: 75
    ,min_blu: 853
    ,min_grn: 751
    ,min_nir: 2623
    ,min_red: 627
    ,min_tmp: 294
    ,mn_swr1: 1910
    ,mn_swr2: 930
    ,stdDev_c: 3012
    ,stdDev_gv: 4085
    ,stdDv_1: 355865
    ,stdDv_b: 87362
    ,stdDv_cl: 799
    ,stdDv_f: 9367
    ,stdDv_gc: 29780
    ,stdDv_gr: 112204
    ,stdDv_gvs: 10637
    ,stdDv_h: 23963
    ,stdDv_ndf: 21430
    ,stdDv_ndv: 7330
    ,stdDv_ndw: 8200
    ,stdDv_np: 1891
    ,stdDv_nr: 136283
    ,stdDv_p: 2081
    ,stdDv_r: 191106
    ,stdDv_s2: 257866
    ,stdDv_sf: 10229
    ,stdDv_sh: 2718
    ,stdDv_sl: 3737
    ,stdDv_sv: 3647
    ,stdDv_t: 2805
    ,stdDv_v2: 3815
    ,stdDv_w: 5312
})
//print(dictPtos.size())
print(dictPtos.keys())
  
// A mapping from a common name to the sensor-specific bands.
var LC8_BANDS = ['B2',   'B3',    'B4',  'B5',  'B6',    'B7',    'B10'];
var STD_NAMES = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'temp'];


var bioma = "CAATINGA"

//var anos = ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994','1995','1996','1997','1998','1999','2000','2001','2002','2003',
//          '2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017'];
var anos = [2017]

// var visclass = {"min": 0, "max": 29,
//         "palette": "d5d5e5,129912,1f4423,006400,00ff00," +
//                     "687537,76a5af,29eee4,77a605,935132,ff9966,45c2a5," +
//                     "b8af4f,f1c232,ffffb2,f6b26b,f6b26b,a0d0de," +
//                     "e974ed,d5a6bd,c27ba0,FBF3C7,d0670f," +
//                     "dd7e6b,b7b7b7,ff99ff," +
//                     "0000ff,d5d5e5,afafaf,f76262",
//         "format": "png"
// }
var visNDFI = {'min':0, 'max':200, 'palette':ndfi_color};
var visNDFI100 = {'min':0, 'max':100, 'palette':ndfi_color};
var ndfi_color ='FFFFFF,FFFCFF,FFF9FF,FFF7FF,FFF4FF,FFF2FF,FFEFFF,FFECFF,FFEAFF,FFE7FF,FFE5FF,FFE2FF,FFE0FF,FFDDFF,FFDAFF,FFD8FF,FFD5FF,FFD3FF,FFD0FF,FFCEFF,'+
                'FFCBFF,FFC8FF,FFC6FF,FFC3FF,FFC1FF,FFBEFF,FFBCFF,FFB9FF,FFB6FF,FFB4FF,FFB1FF,FFAFFF,FFACFF,FFAAFF,FFA7FF,FFA4FF,FFA2FF,FF9FFF,FF9DFF,FF9AFF,'+
                'FF97FF,FF95FF,FF92FF,FF90FF,FF8DFF,FF8BFF,FF88FF,FF85FF,FF83FF,FF80FF,FF7EFF,FF7BFF,FF79FF,FF76FF,FF73FF,FF71FF,FF6EFF,FF6CFF,FF69FF,FF67FF,'+
                'FF64FF,FF61FF,FF5FFF,FF5CFF,FF5AFF,FF57FF,FF55FF,FF52FF,FF4FFF,FF4DFF,FF4AFF,FF48FF,FF45FF,FF42FF,FF40FF,FF3DFF,FF3BFF,FF38FF,FF36FF,FF33FF,'+
                'FF30FF,FF2EFF,FF2BFF,FF29FF,FF26FF,FF24FF,FF21FF,FF1EFF,FF1CFF,FF19FF,FF17FF,FF14FF,FF12FF,FF0FFF,FF0CFF,FF0AFF,FF07FF,FF05FF,FF02FF,FF00FF,'+
                'FF00FF,FF0AF4,FF15E9,FF1FDF,FF2AD4,FF35C9,FF3FBF,FF4AB4,FF55AA,FF5F9F,FF6A94,FF748A,FF7F7F,FF8A74,FF946A,FF9F5F,FFAA55,FFB44A,FFBF3F,FFC935,'+
                'FFD42A,FFDF1F,FFE915,FFF40A,FFFF00,FFFF00,FFFB00,FFF700,FFF300,FFF000,FFEC00,FFE800,FFE400,FFE100,FFDD00,FFD900,FFD500,FFD200,FFCE00,FFCA00,'+
                'FFC600,FFC300,FFBF00,FFBB00,FFB700,FFB400,FFB000,FFAC00,FFA800,FFA500,FFA500,F7A400,F0A300,E8A200,E1A200,D9A100,D2A000,CA9F00,C39F00,BB9E00,'+
                'B49D00,AC9C00,A59C00,9D9B00,969A00,8E9900,879900,7F9800,789700,709700,699600,619500,5A9400,529400,4B9300,439200,349100,2D9000,258F00,1E8E00,'+
                '168E00,0F8D00,078C00,008C00,008C00,008700,008300,007F00,007A00,007600,007200,006E00,006900,006500,006100,005C00,005800,005400,005000,004C00';


var visNDFI = {'min':0, 'max':200, 'palette':ndfi_color};
var visNDFI100 = {'min':0, 'max':100, 'palette':ndfi_color};

var dirasset = 'projects/mapbiomas-workspace/MOSAICOS/workspace-c3';
//var dirout = 'projects/mapbiomas-workspace/AMOSTRAS/Caatinga_v18_85a17/'
var dirout = 'users/diegocosta/PEJanela5';

var terrain = ee.Image("JAXA/ALOS/AW3D30_V1_1").select("AVE");
  
var assetBacia = 'users/CartasSol/shapes/baciasN2CaatingaB25000'

var baciasB = ee.FeatureCollection(assetBacia)


//var slope = ee.Terrain.slope(terrain).clip(limite_Caatinga);
var square = ee.Kernel.square({radius: 5});

var ROIg = ee.FeatureCollection(dirout)

ROIg = ROIg.select(ee.List(dictPtos.keys()), ee.List(dict.keys()))


var gridFeatureCollection = ee.FeatureCollection('ft:1wCmguQD-xQs2gMH3B-hdOdrwy_hZAq4XFw1rU8PN')
                              .filterBounds(baciasB)
                                
var nameCartas = gridFeatureCollection.reduceColumns(ee.Reducer.toList(), ['name']).get('list');                           
var bandNames = ee.List([
            "amp_evi2","amp_gv","amp_ndfi", "amp_ndvi","amp_ndwi","amp_npv",
            "amp_soil", "amp_wefi","median_blue","median_blue_dry", "median_blue_wet", 
            "median_cai", "median_cai_dry", "median_cai_wet", "median_cloud",
            "median_evi2","median_evi2_dry", "median_evi2_wet", "median_fns","median_fns_dry", 
            "median_fns_wet","median_gcvi", "median_green","median_gv","median_gvs", 
            "median_hallcover", "median_ndfi", "median_ndvi","median_ndwi","median_nir",
            "median_npv","median_pri","median_pri_dry","median_pri_wet","median_red", 
            "median_savi", "median_shade","median_soil","median_swir1", "median_temp", "median_wefi", 
            "median_wefi_dry","median_wefi_wet", 
            "min_blue","min_green","min_nir","min_red","min_swir1","min_swir2","min_temp", 
            "stdDev_blue","stdDev_cai","stdDev_cloud","stdDev_evi2","stdDev_fns",
            "stdDev_gcvi", "stdDev_green", "stdDev_gv", "stdDev_gvs","stdDev_hallcover","stdDev_ndfi", 
            "stdDev_ndvi", "stdDev_ndwi", "stdDev_nir", "stdDev_npv", 
            "stdDev_pri", "stdDev_red","stdDev_savi","stdDev_shade", 
            "stdDev_soil","stdDev_swir1", "stdDev_temp","stdDev_wefi"
        ]);
  


var visParMedian = {'bands':['m_swir1','m_nir','m_red'], 'gain':[0.08, 0.06,0.2],'gamma':0.5 };
var collection = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT_TOA');


// Define visualization parameters for a true color image.
var vizParams = { bands: ['B4', 'B3', 'B2'], max: 0.4, gamma: 1.6};
var mosaicoTotal = ee.ImageCollection(dirasset)
                        //.filterMetadata('grid_name', 'equals', cartas[0]);
print("aqui mosaico",  mosaicoTotal.limit(2));                

var pmtRF = {
        numberOfTrees: 500,
        variablesPerSplit: 30,
        minLeafPopulation:1,
        outOfBagMode: true
        };

// var classMapbiomas = ee.Image(ee.ImageCollection('projects/mapbiomas-workspace/COLECAO3_1/classificacao-dev')
//                       .filterMetadata('biome', 'equals', 'CAATINGA')
//                      .filterMetadata('grid_name', 'equals', 'SB-24-Y-D').first())
                    
var optMosaci = {
    gamma: 1,
    max: 1960.08,
    min: 475.92,
    opacity: 1,
    bands:["median_red","median_gre","median_blu"]
};

var nameBacias = baciasB.reduceColumns(ee.Reducer.toList(), ['ID_NIVEL2']).get('list');

ee.List(anos).evaluate(function(variosAnos){
    variosAnos.forEach(function(ano){
        
        var training = ROIg.filterMetadata('ano', 'equals', ano);
                      
        ee.List(nameBacias).evaluate(function(lsBacias){
            var lsImcRFxBacia = ee.List([])
            lsBacias.forEach(function(namB){
                var baciaTemp = baciasB.filterMetadata('ID_NIVEL2', 'equals', namB)
                
                var ptosXbacia = training.filterBounds(baciaTemp)
                
                var classifier = ee.Classifier.randomForest(pmtRF).train(ptosXbacia, 'class', bandNames);
                // criar uma geometria que junte as cartas que contem a bacia em estudo
                //var conjCartasBacia = gridFeatureCollection.filterBounds(baciaTemp).union()

                var mosaicTemp = mosaicoTotal.filterMetadata('year', 'equals', ano)
                                             .filterBounds(baciaTemp).mosaic()
                
                mosaicTemp = ee.Image(mosaicTemp).clip(baciaTemp)

                var resl = 'RF_'+ namB + '_' + ano
                var classified = mosaicTemp.classify(classifier, resl)
                
                processoExportar(classified, namB, ano, baciaTemp.geometry())
                //lsImcRFxBacia = lsImcRFxBacia.add(classified)
            })

            // var ColRFxBacia = ee.ImageCollection.fromImages(lsImcRFxBacia)
            // var imgRFxBacia = ee.Image(ColRFxBacia.mosaic())

            // ee.List(nameCartas).evaluate(function(lsCartas){
            //     lsCartas.forEach(function(nameC){
            //         var myCarta = gridFeatureCollection.filterMetadata('name', 'equals', nameC);
            //         var mapaRF = imgRFxBacia.clip(myCarta)
                    
            //         mapaRF = mapaRF.set('biome', 'CAATINGA')
            //         mapaRF = mapaRF.set('grid_name', nameC)
            //         mapaRF = mapaRF.set('year', ano)
            //         //mapaRF = mapaRF.set('biome', 'CAATINGA')
            //         var nomeDesc = 'RF_'+ nameC + '_'+ ano
                    
            //         var optExp = {
            //             image: mapaRF, 
            //             description: nomeDesc, 
            //             assetId:assetoutRF + nomeDesc , 
            //             //pyramidingPolicy, 
            //             //dimensions, 
            //             region: myCarta, 
            //             scale: 30, 
            //             maxPixels: 1e13
            //         }

            //         Export.image.toAsset(optExp)

            //     })
            // })

        })

        // Map.addLayer(myMosaic, vizParams, 'Mosaicos' + ano);
        // Map.addLayer(mosaicMapbiomas, optMosaci, 'mosMapbiomas' + ano);
        // Map.addLayer(classMapbiomas , visclass, bandasss)                            
        // Map.addLayer(classified , visclass, resl)
    })
})
  
                  
  