
var keyAssetr = 'integracao'
var param = {
    
    'inputAsset' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    'assetCol': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVX" ,
    'assetColprob': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVP" ,
    'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fill',
    // 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Spatial',
    // 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Temporal',
    // 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Frequency',
    // 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    'asset_Map' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    // 'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/aggrements',
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
// #testes do dado
// # https://code.earthengine.google.com/8e5ba331665f0a395a226c410a04704d
// # https://code.earthengine.google.com/306a03ce0c9cb39c4db33265ac0d3ead
// # get raster with area km2

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

var modelsList = ['GTB','RF'];
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

// print("aaa ", param.assetFilters.indexOf('POS-CLASS'))
if (isFilter){ 
    if ((param.assetFilters.indexOf('POS-CLASS') > -1) ||  (param.assetFilters.indexOf('toExport') > -1)){
        subfolder = "_" + param['assetFilters'].split('/')[-1] ;
    }    
}else{  
    subfolder= '';
}

if (param.isImgCol){
    if (isFilter){
        imgsMaps = ee.ImageCollection(param.assetFilters);
    }else{
        if(version > 6){        
            print(" 🚨 Loading 🔊 >> " + param.assetColprob + " <<  🚨");
            imgsMaps = ee.ImageCollection(param.assetColprob);
        }else{
            imgsMaps = ee.ImageCollection(param.assetCol);
        }
    }
    var getid_bacia = imgsMaps.first().get('id_bacia').getInfo();
    print("we load bacia " + getid_bacia);
    if (knowImgcolg){
        print("versions quantity = ", imgsMaps.aggregate_histogram('version'));
    }
    if (getid_bacia){
        var nameBands = 'classification';
        var prefixo = "";
        modelsList.forEach(function(model){  
            if ((isFilter) & (model != 'RF')){
                mapClassMod = imgsMaps.filter(ee.Filter.eq('version', version));
            }else{
                mapClassMod = imgsMaps.filter(
                                ee.Filter.eq('version', version)).filter(
                                    ee.Filter.eq('classifier', model))
            }
            print("########## 🔊 FILTERED BY VERSION " + String(version) + " AND MODEL " + model + "🔊 ###############"); 
            var sizeimgCol = mapClassMod.size().getInfo();
            print(" 🚨 número de mapas bacias ", sizeimgCol); 
            nameCSV = 'areaXclasse_CAAT_Col90_' + model +  subfolder + "_vers_" + String(version);
                  
            if (sizeimgCol > 0){   
                var cc = 0;
                nameBacias.forEach(
                    function(nbacia) {           
                        var ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
                                                .filter(ee.Filter.eq('nunivotto3', nbacia)).geometry();
                        var limitInt = bioma250mil.intersection(ftcol_bacias);
                        var  mapClassBacia = mapClassMod.filter(ee.Filter.eq('id_bacia', nbacia)).first();
                        // print(mapClassBacia.getInfo())
                        lstnameImgCorre.forEach(
                            function(nameImgCorre){                                    
                                // print("sending name image to correction => ", nameImgCorre);
                                areaM = iterandoXanoImCruda(pixelArea, mapClassBacia, limitInt, nameImgCorre, nbacia) 
                                var nameCSVBa = nameCSV + "_" + dictCorre[nameImgCorre] + "_" +  nbacia; 
                                //  print(ee.FeatureCollection(areaM).first().getInfo())
                                print("show the feature Area << " + nameCSVBa + " >> ", ee.FeatureCollection(areaM).getInfo());
                                processoExportar(areaM, nameCSVBa, cc);
                            }
                        )
                        cc = cc + 1;
                    }
                )
            }
        })
        
    }else{
        print("########## 🔊 FILTERED BY VERSAO {version} 🔊 ###############");              
        var mapClassYY = mapClass.filter(ee.Filter.eq('version', version));
        print(" 🚨 número de mapas bacias ", mapClass.size().getInfo());
        var immapClassYY = ee.Image().byte();
        param.anos.forEach(
            function(yy){
                var nmIm = 'CAATINGA-' + str(yy) + '-' + str(version)
                var nameBands = 'classification_' + str(yy)
                imTmp = mapClassYY.filter(ee.Filter.eq('system:index', nmIm)).first().rename(nameBands)
                if (yy == 1985){
                    immapClassYY = imTmp.byte();
                }else{
                    immapClassYY = immapClassYY.addBands(imTmp.byte());
                }
            }
        )
        nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + "_" + model + "_vers_" + str(version)
        var cc = 0;
        nameBacias.forEach(
            function(nbacia){           
                ftcol_bacias = ee.FeatureCollection(param['asset_bacias']).filter(
                                ee.Filter.eq('nunivotto3', nbacia)).geometry()
                limitInt = bioma250mil.intersection(ftcol_bacias)
                areaM = iterandoXanoImCruda(pixelArea, immapClassYY, limitInt, "", nbacia, "") 
                nameCSVBa = nameCSV + "_" + nbacia 
                processoExportar(areaM, nameCSVBa, cc)
            })

    }
    
    
}else{
    print("########## 🔊 LOADING MAP RASTER FROM IMAGE OBJECT ###############");
    var assetPathRead = param['asset_Map']; 
    print(" ------ ", assetPathRead);
    var nameImg = assetPathRead.split('/')[-1].replace('mapbiomas_collection', '')
    var mapClassRaster = ee.Image(assetPathRead).byte()
    // ### call to function samples  #######
    nameCSV = 'areaXclasse_' + param['biome'] + "_Col" + nameImg

    nameBacias.forEach(
        function(nbacia){
            ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])
                                .filter(ee.Filter.eq('nunivotto3', nbacia)).geometry();
            limitInt = bioma250mil.intersection(ftcol_bacias);
            lstnameImgCorre.forEach(
                function(nameImgCorre){
                    print("sending name image to correction => ", nameImgCorre);                        
                    areaM = iterandoXanoImCruda(pixelArea, mapClassRaster, limitInt, nameImgCorre, nbacia, "") ;
                    nameCSVBa = nameCSV + "_" + nbacia;
                    print("  we processing ==> " + nameCSVBa + " -- ") ;
                    processoExportar(areaM, nameCSVBa, cc);
                }
            )

        }
    )
}