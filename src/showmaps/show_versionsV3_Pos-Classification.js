//https://code.earthengine.google.com/a439f870a02b371daf094c5b6cf6de34
//https://code.earthengine.google.com/c6be8cee51ed15cb9cd80c031f8f2729
var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text')

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
    visIncident : {
        max: 5,
        min: 1,
        palette: ['#faf3dd','#c8d5b9','#f19c79','#fec601','#013a63']
    },
    props: {  
        textColor: 'ff0000', 
        outlineColor: 'ffffff', 
        outlineWidth: 1.5, 
        outlineOpacity: 0.2
    }
} 
function set_class_level1(feat){
    var dict_points = ee.Dictionary({
            'afloramentos': 29,
            'agricultura': 21,
            'agua': 33,
            'aquicultura': 33,
            'campo': 12,
            'carnaúbas': 21,
            'desmatamento': 22 ,
            'exotica': 21,
            'floresta': 3,
            'mineração': 22,
            'mosaico de uso': 21,
            'pastagem': 21,
            'regeneração savana': 4,
            'savana': 4,
            'solo exposto': 22,
            'urbano': 22,
            'áreas não vegetadas': 22
    })
    return feat.set('level_1', dict_points.get(feat.get('classe')))
}
var param = { 
    assetMapC7: 'projects/mapbiomas-workspace/public/collection7_1/mapbiomas_collection71_integration_v1',
    assetMapC8: 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
    asset_MapC9X : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVX',
    asset_MapC9P : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVP',
    asset_MapC9Y : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVY',
    asset_ptosDifLapigvsCol7: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/occTab_acc_Dif_Caat_mapbiomas_71_integration_v1',
    asset_ptosDifLapigvsCol8: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/occTab_acc_Dif_Caat_mapbiomas_80_integration_v1',
    asset_Gapfill : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2',   
    asset_Spatial : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3', 
    asset_Temporal : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/TemporalV3', 
    assset_Frequency: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV3',
    assset_Estavel: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel',
    asset_mixed: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    asset_mata_atlantica: 'projects/mapbiomas-workspace/COLECAO9/pos_classificacao-ma/MA_col9_p10e_v135',
    asset_baciasN1raster: 'projects/mapbiomas-workspace/AUXILIAR/bacias-nivel-1-raster',
    asset_points_campo: 'users/nerivaldogeo/pontos_campo_caatinga',
    asset_gedi: 'users/potapovpeter/GEDI_V27',
    asset_bioma_raster : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',    
    assetBacia: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga", 
    asset_caat_buffer: 'users/CartasSol/shapes/caatinga_buffer5km',   
    anos: ['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
           '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
           '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
           '2015','2016','2017','2018','2019','2020','2021','2022'],
    bandas: ['red_median', 'green_median', 'blue_median'],
    
    listaNameBacias: [
        '741','7421','7422','744','745','746','7492','751','752',
        '753', '754','755','756','757','758','759','7621','7622','763',
        '764','765','766','767','771','772','773', '7741','7742','775',
        '776','777','778','76111','76116','7612','7613','7614','7615',
        '7616','7617','7618','7619'
    ],
    classMapB: [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,40,41,46,47,48,49,50,62],
    classNew:  [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33,21,21,21,21,21,21,21, 3,12,21],
    classesMapAmp:  [3, 4, 3, 3,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,18,18,18,18,18,18, 3,12,18],
}

function makeDiferencebettwenPoints(feat){   
    var classRef = ee.Number(feat.get('CLASS_' + String(lstYearshow[0])));
    var classCf = ee.Number(feat.get('classification'))
    return feat.set('diferente', classRef.neq(classCf));
}


function get_layerIncidentes (mapYY71, mapYY80, mapYY90){
    mapYY71 = mapYY71.remap(param.classMapB, param.classNew);
    mapYY80 = mapYY80.remap(param.classMapB, param.classNew);
    var mapAdding = mapYY71.addBands(mapYY80).addBands(mapYY90);
    var incidentesMaps = mapAdding.reduce(ee.Reducer.countRuns())
                                    .subtract(1).rename('incidentes');
    var statesMaps = mapAdding.reduce(ee.Reducer.countDistinctNonNull()).rename('states');
    var modaMaps = mapAdding.reduce(ee.Reducer.mode());
    ///logica de definição de classes está embasada no fato de termos 3 coleções de entrada
    //para analisar mais coleções a logica precisa ser reestruturada
    var clas1_add = incidentesMaps.eq(0).selfMask();
    var clas2_add = incidentesMaps.eq(1).and(mapAdding.select(2).subtract(modaMaps).eq(0)).selfMask();
    var clas3_add = incidentesMaps.eq(1).and(mapAdding.select(0).subtract(modaMaps).eq(0)).selfMask();
    var clas4_add = incidentesMaps.eq(2).and(statesMaps.eq(2)).selfMask();
    var clas5_add = incidentesMaps.eq(2).and(statesMaps.eq(3)).selfMask();

    var outMaps = clas1_add.blend(clas2_add.multiply(2))
                    .blend(clas3_add.multiply(3))
                    .blend(clas4_add.multiply(4))
                    .blend(clas5_add.multiply(5))
                    .rename('classes');
    
    return outMaps
}
var showErrorsAcc = false;
var selBacia = 'all';
var baciaProcura = '757';
var yearcourrent = 2020;
var lstYearshow = [2020,2022]
var modelo = "GTB";
var version = 30;
var newvers = 16;
var incluieMA = true;
var assetCol9 = param.asset_MapC9X;
if (version > 5){
    assetCol9 = param.asset_MapC9P;
}
var mapMT = ee.Image(param.asset_mata_atlantica);
var biomaRasterCaat = ee.Image(param.asset_bioma_raster).eq(5);
var biomaRaster = biomaRasterCaat
if (incluieMA){
    biomaRaster = biomaRaster.add(ee.Image(param.asset_bioma_raster).eq(2));
}
var banda_activa = 'classification_' + String(yearcourrent)
var bandas_activas = [];
lstYearshow.forEach(function(yyear){bandas_activas.push('classification_' + String(yyear)) })
var FeatColbacia = ee.FeatureCollection(param.assetBacia);
var caatBuffer = ee.FeatureCollection(param.asset_caat_buffer).geometry();

var baciaRaster = ee.Image(param.asset_baciasN1raster);
// var maskBacia = baciaRaster.eq(104).add(baciaRaster.eq(103))
//                           .add(baciaRaster.eq(106)).add(baciaRaster.eq(107));
var imgGEDI = ee.ImageCollection(param.asset_gedi).mosaic().updateMask(biomaRaster);
var maskGEDI = imgGEDI.gte(7);
var pointsCampo = ee.FeatureCollection(param.asset_points_campo)
                    .filter(ee.Filter.neq('classe', null));
// pointsCampo = pointsCampo.map(set_class_level1);
print("show points collected in campo ", pointsCampo);
print("dictionary of property classe ", pointsCampo.aggregate_histogram('classe'));
// print("dictionary of property level 1 ", pointsCampo.aggregate_histogram('level_1'));
var featSearch = FeatColbacia.filter(ee.Filter.eq('nunivotto3', baciaProcura));

var imgMapCol71= ee.Image(param.assetMapC7).updateMask(biomaRaster)
                        .select(bandas_activas);
var imgMapCol8= ee.Image(param.assetMapC8).updateMask(biomaRaster)
                        .select(bandas_activas);
var lstVer15inic = [
                '7421','754','756','757','758','7614','766',
                '752', '766', '776', '764','765', '7621', '744', 
                '753'
        ];
var imgMapCol9GTB =  ee.ImageCollection(param.asset_MapC9Y)
                            .filter(ee.Filter.eq('version', version))
                            .filter(ee.Filter.eq("classifier", 'GTB'))
                            .select(bandas_activas);

var imgMapCol9RF = ee.ImageCollection(param.asset_MapC9Y)
                      .filter(ee.Filter.eq('version', version))
                      .filter(ee.Filter.eq("classifier", "RF"))
                      .select(bandas_activas);

print("  imgMapCol9GTB ", imgMapCol9GTB);
var imgMapCol9GF = ee.ImageCollection(param.asset_Gapfill)
                        .filter(ee.Filter.eq('version', 18))
                        .select(bandas_activas);
print(" know metadata from imgMapCol Gapfill ", imgMapCol9GF);
var imgMapCol9FQ = ee.ImageCollection(param.assset_Frequency)
                        .filter(ee.Filter.eq('version', version))
                        // .filter(ee.Filter.eq('type_filter', 'frequence'))
                        .select(bandas_activas);

var imgMapCol9SPstp1 = ee.ImageCollection(param.asset_Spatial)
                        .filter(ee.Filter.eq('version', version))
                        .filter(ee.Filter.eq('step', 1))
                        .select(bandas_activas);
print("spacial step 1", imgMapCol9SPstp1)
var imgMapCol9TP = ee.ImageCollection(param.asset_Temporal)
                        .filter(ee.Filter.eq('version', version))
                        // .filter(ee.Filter.neq('janela', 3))
                        .select(bandas_activas);
var imgMapCol9TPJ3 = ee.ImageCollection(param.asset_Temporal)
                        .filter(ee.Filter.eq('version', version))
                        .filter(ee.Filter.neq('janela', 3))
                        .select(bandas_activas);            
var imgMapCol9TPJ4 = ee.ImageCollection(param.asset_Temporal)
                        .filter(ee.Filter.eq('version', version))
                        .filter(ee.Filter.neq('janela', 4))
                        .select(bandas_activas); 

var imgMapCol9TPJ5 = ee.ImageCollection(param.asset_Temporal)
                        .filter(ee.Filter.eq('version', version))
                        .filter(ee.Filter.neq('janela', 5))
                        .select(bandas_activas); 



var Mosaicos = ee.ImageCollection(param.assetIm).filter(
                        ee.Filter.eq('biome', 'CAATINGA')).select(param.bandas);

var pointRefCol80compY = null;
var propYYPoints = ['CLASS_' + String(lstYearshow[0]), bandas_activas[0]] ;
var pointRefCol80comp = ee.FeatureCollection(param.asset_ptosDifLapigvsCol8)
                            .select(propYYPoints).filterBounds(featSearch);
print(ee.String("size pontos lapig ").cat('CLASS_' + String(lstYearshow[0])) , pointRefCol80comp.size());
pointRefCol80comp = pointRefCol80comp.filter(ee.Filter.neq('CLASS_' + String(lstYearshow[0]), 27));

print("pontos lapig ", pointRefCol80comp.limit(4));

var listAllClass =    [3,4,10,15,18,22,27,33];
var listAllClassrem = [3,4,12,21,21,22,27,33];
pointRefCol80comp = pointRefCol80comp.remap(
                              listAllClass, listAllClassrem, 
                              'CLASS_' + String(lstYearshow[0])
                          );
print(" show metadata points Reference ", pointRefCol80comp);
// ========================================================================= //
// set as 'all' to show all map or set the basin from pamareter dictionary
// ========================================================================= //
var imgMapCol9GTBjoin = null;
var imgMapCol9RFjoin = null;
var imgMapCol9GFjoin = null;
var imgMapCol9FQjoin = null;
var imgMapCol9SPstp1join = null;
var imgMapCol9TPJ3join = null;
var imgMapCol9TPJ4join = null;
var imgMapCol9TPJ5join = null;
var imgMapmixedJoin = null;
var ptosfromBacia = null;


if (selBacia === 'all'){
    imgMapCol9RFjoin = imgMapCol9RF.min().updateMask(biomaRaster);  
    imgMapCol9GTBjoin = imgMapCol9GTB.min().updateMask(biomaRaster);     
    imgMapCol9GFjoin = imgMapCol9GF.min().updateMask(biomaRaster);                           
    imgMapCol9SPstp1join = imgMapCol9SPstp1.min().updateMask(biomaRaster);
    imgMapCol9FQjoin = imgMapCol9FQ.min().updateMask(biomaRaster);
    imgMapCol9TPJ3join = imgMapCol9TPJ3.min().updateMask(biomaRaster);
    imgMapCol9TPJ4join = imgMapCol9TPJ4.min().updateMask(biomaRaster);
    imgMapCol9TPJ5join = imgMapCol9TPJ5.min().updateMask(biomaRaster);    
    // imgMapmixedJoin = imgMapmixed.min().updateMask(biomaRaster);

}else{
    FeatColbacia = FeatColbacia.filter(ee.Filter.eq('nunivotto3', selBacia));  
    imgMapCol9RFjoin = imgMapCol9RF.filter(ee.Filter.eq("id_bacia", selBacia))
                                  .updateMask(biomaRaster)
                                  .remap(param.classMapB, param.classNew);
    imgMapCol9GTBjoin = imgMapCol9GTB.filter(ee.Filter.eq("id_bacia", selBacia))
                                .updateMask(biomaRaster)
                                .remap(param.classMapB, param.classNew);     
    imgMapCol9SPstp1join = imgMapCol9SPstp1.filter(ee.Filter.eq("id_bacia", selBacia)).min().updateMask(biomaRaster);
    imgMapCol9TPJ3join = imgMapCol9TPJ3.filter(ee.Filter.eq("id_bacia", selBacia)).min().updateMask(biomaRaster);
    imgMapCol9TPJ4join = imgMapCol9TPJ4.filter(ee.Filter.eq("id_bacia", selBacia)).min().updateMask(biomaRaster);
    imgMapCol9TPJ5join = imgMapCol9TPJ5.filter(ee.Filter.eq("id_bacia", selBacia)).min().updateMask(biomaRaster);
    imgMapCol9GFjoin = imgMapCol9GF.filter(ee.Filter.eq("id_bacia", selBacia)).min().updateMask(biomaRaster);
    imgMapCol9FQjoin = imgMapCol9FQ.filter(ee.Filter.eq("id_bacia", selBacia)).min().updateMask(biomaRaster);
}

var imgAnalisesChange = imgMapCol9FQjoin;
var incidencias = get_layerIncidentes(
                                imgMapCol71.select('classification_' +  String(bandas_activas[0])), 
                                imgMapCol8.select('classification_' +  String(bandas_activas[0])), 
                                imgAnalisesChange.select('classification_' +  String(bandas_activas[0]))
                            );

print(" 📍 imagem no Asset Geral Mapbiomas Col 7.1  ‼️", imgMapCol71);
print(" 📍 imagem no Asset Geral Mapbiomas Col 8.0  ‼️", imgMapCol8);
print(" 📍 imagem no Asset Geral X Bacias col 9 GTB", imgMapCol9GTBjoin);
print(" 📍 imagem no Asset Geral X Bacias pos-Class col 9 Gap Fill", imgMapCol9GFjoin);
print(" 📍 imagem no Asset Geral X Bacias pos-Class col 9 Spatial", imgMapCol9SPstp1join);
print(" 📍 imagem no Asset Geral X Bacias pos-Class col 9 Frequence ", imgMapCol9FQjoin);

var mosaic_year = Mosaicos.filter(ee.Filter.eq('year', yearcourrent)).median();                     
Map.addLayer(FeatColbacia, {color: 'green'}, 'bacia', false);
Map.addLayer(mosaic_year, visualizar.visMosaic,'Mosaic Col8', false);

var baciaBuf = ee.Image().byte().paint({
                    featureCollection: FeatColbacia,
                    color: 1,
                    width: 1.5
                    });
var pointsLapigC = imgAnalisesChange.select(bandas_activas[0]).rename('classification')
                    .sampleRegions({
                        collection: pointRefCol80comp,
                        properties: propYYPoints, 
                        scale: 30, 
                        geometries: true
                    })
print("pontos resamples lapic ", pointsLapigC)
pointsLapigC =  pointsLapigC.map(makeDiferencebettwenPoints);
pointsLapigC = pointsLapigC.filter(ee.Filter.eq('diferente', 1));
print("pontos revisados ", pointsLapigC.limit(10));


Map.addLayer(imgMapCol71.select(bandas_activas[0]), visualizar.visclassCC,'Col71_' + String(lstYearshow[0]), false);
Map.addLayer(imgMapCol8.select(bandas_activas[0]),  visualizar.visclassCC, 'Col8_'+ String(lstYearshow[0]), false);
Map.addLayer(mapMT.select(bandas_activas[0]),  visualizar.visclassCC, 'Col9 Mata Atlan_'+ String(lstYearshow[0]), false);
var mapGTBAno1 = imgMapCol9GTBjoin.select(bandas_activas[0]).remap(param.classMapB, param.classNew);
Map.addLayer(mapGTBAno1,  visualizar.visclassCC, 'Class GTB ' + String(version), false);
var mapRFAno1 = imgMapCol9RFjoin.select(bandas_activas[0]).remap(param.classMapB, param.classNew);
Map.addLayer(mapRFAno1,  visualizar.visclassCC, 'Class RF ' + String(version), false);
Map.addLayer(imgMapCol9GFjoin.select(bandas_activas[0]),  visualizar.visclassCC, 'Class Gap-fill ' + String(version), false);
Map.addLayer(imgMapCol9SPstp1join.select(bandas_activas[0]),  visualizar.visclassCC, 'CC Spatial Step 1 ' + String(version), false);
Map.addLayer(imgMapCol9TPJ3join.select(bandas_activas[0]),  visualizar.visclassCC, 'CC Temporal J3 ' + String(version), false);
Map.addLayer(imgMapCol9TPJ4join.select(bandas_activas[0]),  visualizar.visclassCC, 'CC Temporal J4 ' + String(version), false);
Map.addLayer(imgMapCol9TPJ5join.select(bandas_activas[0]),  visualizar.visclassCC, 'CC Temporal J5 ' + String(version), false);
Map.addLayer(imgMapCol9FQjoin.select(bandas_activas[0]),  visualizar.visclassCC, 'CC Frequency ' + String(version), false);

Map.addLayer(imgMapCol71.select(bandas_activas[1]), visualizar.visclassCC,'Col71_' + String(lstYearshow[1]), false);
Map.addLayer(imgMapCol8.select(bandas_activas[1]),  visualizar.visclassCC, 'Col8_'+ String(lstYearshow[1]), false);
var mapGTBAno2 = imgMapCol9GTBjoin.select(bandas_activas[1]).remap(param.classMapB, param.classNew);
Map.addLayer(mapGTBAno2.updateMask(biomaRasterCaat),  visualizar.visclassCC, 'Class GTB ' + String(version), false);
var mapRFAno2 = imgMapCol9RFjoin.select(bandas_activas[1]).remap(param.classMapB, param.classNew);
Map.addLayer(mapRFAno2.updateMask(biomaRasterCaat),  visualizar.visclassCC, 'Class RF ' + String(version), false);
Map.addLayer(imgMapCol9GFjoin.select(bandas_activas[1]),  visualizar.visclassCC, 'Class Gap-fill ' + String(version), false);
Map.addLayer(imgMapCol9SPstp1join.select(bandas_activas[1]),  visualizar.visclassCC, 'CC Spatial Step 1 ' + String(version), false);
Map.addLayer(imgMapCol9TPJ3join.select(bandas_activas[1]),  visualizar.visclassCC, 'CC Temporal J3 ' + String(version), false);
Map.addLayer(imgMapCol9TPJ4join.select(bandas_activas[1]),  visualizar.visclassCC, 'CC Temporal J4 ' + String(version), false);
Map.addLayer(imgMapCol9TPJ5join.select(bandas_activas[1]),  visualizar.visclassCC, 'CC Temporal J5 ' + String(version), false);
Map.addLayer(imgMapCol9FQjoin.select(bandas_activas[1]),  visualizar.visclassCC, 'CC Frequency ' + String(version), false);
Map.addLayer(maskGEDI.selfMask(), {min:0, max: 1, palette: 'BDE861'}, 'mask GEDI', false);
Map.addLayer(baciaBuf, {palette: 'FF0000'}, 'caatinga buffer');
// Map.centerObject(featSearch);
if (showErrorsAcc){
    var listaPontos = [3,4,12,21,22,33];
    listaPontos.forEach(function(nClasse){
        var temFeatPoint =  pointsLapigC.filter(ee.Filter.eq('CLASS_' + String(lstYearshow[0]), nClasse));
        // print(nClasse, temFeatPoint);
        Map.addLayer(temFeatPoint , {color: 'red'}, 'ptos classe ' + String(nClasse), false);
    })
}

var legend = ui.Panel({style: {position: 'bottom-left', padding: '8px 15px'}});
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
    value: 'Coincidencias das classes',
    style: {
          fontWeight: 'bold',
          fontSize: '16px',
          margin: '0px 0 4px 0px'
      }
  });
  
  legend.add(title);
  legend.add(makeRow('#faf3dd','Concordante'));
  legend.add(makeRow('#c8d5b9','Concordante Recente'));
  legend.add(makeRow('#f19c79','Discordante Recente'));
  legend.add(makeRow('#fec601','Discordante'));
  legend.add(makeRow('#013a63','Muito discordante'));
  Map.add(legend);



