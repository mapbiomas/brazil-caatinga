
var keyAssetr = 'integracao'
var param = {
    
    'input_asset_t0' : "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    'input_asset_t1' : "projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_coverage_v2",
    'classMapB': [3, 4, 5, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45],
    'classNew':  [3, 4, 3, 3,12,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,33,33,21,21,21,21,21,21,21],
    'anos': [
        '1985','1986','1987','1988','1989','1990','1991','1992','1993','1994','1995','1996','1997','1998','1999',
        '2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
        '2015','2016','2017','2018','2019','2020','2021','2022'
    ],
    'geral':  true,
    'isImgCol': true,  
    'inBacia': true,
    'collection': '9.0',
    'version': 9,
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil', 
    'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrograficaCaatbuffer5k',
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-AGGREMENT-EXPORT', 
    'lsClasses': [3,4,12,21,22,33,29],
    'changeAcount': false,
    'numeroTask': 2,
    'numeroLimit': 2,
    'conta' : {
        '0': 'solkanGeodatin'
    }
}



// ##############################################
// ###     Helper function
// ###    @param item 
// ##############################################
function convert2featCollection (item){
    var item = ee.Dictionary(item);
    var feature = ee.Feature(ee.Geometry.Point([0, 0])).set(
        'classeConc', item.get('classeConc'),"area", item.get('sum'));
        
    return feature;
}
// #########################################################################
// ####     Calculate area crossing a cover map (deforestation, mapbiomas)
// ####     and a region map (states, biomes, municipalites)
// ####      @param image 
// ####      @param geometry
// #########################################################################
// # https://code.earthengine.google.com/5a7c4eaa2e44f77e79f286e030e94695
function calculateArea (image, pixelArea, geometry){

    var pixelArea = pixelArea.addBands(image.rename('classeConc')).clip(geometry)
    var reducer = ee.Reducer.sum().group(1, 'classeConc')
    var optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': param.scale,
        'bestEffort': true, 
        'maxPixels': 1e13
    }    
    var areas = pixelArea.reduceRegion(optRed);
    areas = ee.List(areas.get('groups')).map(function(item) { return convert2featCollection(item)})
    areas = ee.FeatureCollection(areas)    
    return areas
}
// # pixelArea, imgMapa, bioma250mil
// # pixelArea, immapClassYY, limitInt) 
function iterandoXanoImCruda(imgAreaRef, imgMappCC, limite, nameAggremClass, namBacia){
    var valClass = nameAggremClass.split("_")
    valClass = parseInt(valClass[2]);
    print("name to aggrement class " + nameAggremClass )
    print(" ==> ", valClass)
    var imgMappC8 = ee.Image(param['inputAsset']).clip(limite) 
    imgAreaRef = imgAreaRef.clip(limite);
    // # print(imgMappC8.getInfo())
    var areaGeral = ee.FeatureCollection([]);
    param.anos.forEach(function(year){

        var imgMapC8YY = imgMappC8.select('classification_' + year).remap(param['classMapB'], param['classNew'])   
        var imgMapCCyy = imgMappCC.select('classification_' + year).remap(param['classMapB'], param['classNew'])
        print(imgMapCCyy)
        var concordante = ee.Image(0).where(
                        imgMapC8YY.eq(valClass).and(imgMapCCyy.eq(valClass)), 1).where(
                            imgMapC8YY.neq(valClass).and(imgMapCCyy.eq(valClass)), 2).where(
                                imgMapC8YY.eq(valClass).and(imgMapCCyy.neq(valClass)), 3)
        concordante = concordante.updateMask(concordante.neq(0)).rename('territory_' + String(year));
        print("concordante ", concordante)
        var areatemp = calculateArea (concordante, imgAreaRef, limite) 
        print(areatemp)
        // print("Year area temporal  " + String(year)) ;
        areatemp = areatemp.map(
                        function(feat){
                            return feat.set(
                              'year', parseInt(year), 
                              'bacia', namBacia, 
                              'classe', valClass
                            );
                        }
                    ) 
                  
        areaGeral = areaGeral.merge(areatemp)
    }) 
    print("area geral ", areaGeral);
    return areaGeral;
}     
//exporta a imagem classificada para o asset
function processoExportar(areaFeat, nameT){      
    var optExp = {
          'collection': ee.FeatureCollection(areaFeat), 
          'description': nameT, 
          'folder': param.driverFolder        
        };    
    Export.table.toDrive(optExp) ;
    print(" salvando ... " + nameT + "..!")      ;
}


var bioma250mil = ee.FeatureCollection(param['assetBiomas'])
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry();
var pixelArea = ee.Image.pixelArea().divide(10000)
var exportSta = true
var verificarSalvos = true

var lstnameImgCorre = [
    "Agreement_Class_12",
    //# "Agreement_Class_15",
    "Agreement_Class_21",
    "Agreement_Class_22",
    //# "Agreement_Class_25",
    "Agreement_Class_3",
    "Agreement_Class_33",
    "Agreement_Class_4"
]
var dictCorre = {
    "Agreement_Class_12": 'AgrC_12',
    "Agreement_Class_15": 'AgrC_15',
    "Agreement_Class_21": 'AgrC_21',
    "Agreement_Class_22": 'AgrC_22',
    "Agreement_Class_25": 'AgrC_25',
    "Agreement_Class_3": 'AgrC_3',
    "Agreement_Class_33": 'AgrC_33',
    "Agreement_Class_4": 'AgrC_4'
}

var nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767', '771','773', '7741','7742','775','776','777',
    '778','76111', '76116','7612','7614','7615','7616','7617','7618',
    '7619', '7613','772'
];
var listBacFalta = [];
var version = param.version;
var knowImgcolg = false;
var isFilter = false;
var lstBands = [];
var nameCSV, areaM;
var subfolder = '';
var imgsMaps, mapClassMod;
param.anos.forEach(function(year){
    lstBands.push('classification_' + String(year));
});

var mapClass_t0 = ee.Image(param.input_asset_t0);
var mapClass_t1 = ee.Image(param.input_asset_t1);
print("know número de bandas mapClass_t0", mapClass_t0);
print("know número de bandas mapClass_t1", mapClass_t1);


nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_" + model + "_vers_" + str(version)
var cc = 0;
nameBacias.forEach(
    function(nbacia){           
        ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                        ee.Filter.eq('nunivotto3', nbacia)).geometry()
        limitInt = bioma250mil.intersection(ftcol_bacias)
        areaM = iterandoXanoImCruda(immapClassYY, limitInt, "", nbacia, "") 
        nameCSVBa = nameCSV + "_" + nbacia 
        processoExportar(areaM, nameCSVBa, cc)
    })

}
    
    
=