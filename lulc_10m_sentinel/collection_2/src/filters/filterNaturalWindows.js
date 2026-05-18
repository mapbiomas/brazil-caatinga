//https://code.earthengine.google.com/a439f870a02b371daf094c5b6cf6de34
//https://code.earthengine.google.com/c6be8cee51ed15cb9cd80c031f8f2729
var palettes = require('users/mapbiomas/modules:Palettes.js');
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
    props: {  
        textColor: 'ff0000', 
        outlineColor: 'ffffff', 
        outlineWidth: 1.5, 
        outlineOpacity: 0.2
    },
    maskFlor : {
        min: 0,
        max: 1,
        palette: '000000, ff0000'
    },
    maskContaF : {
        min: 0,
        max: 5,
        palette: '000000,DAF7A6,FFC300,C70039,581845'
    },
    maskContSav : {
        min: 0,
        max: 4,
        palette: '000000,e59866,FFC300,FFC300'
    },
    maskcomp : {
        min: 0,
        max: 1,
        palette: '000000, ff00ab'
    }
} 

var param = { 
    assetMapC8: 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',
    assetPol: 'users/CartasSol/coleta/polygonsCorr/nbacia_',
    asset_bioma_raster : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    asset_filted : {
        'spatial': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3',
        'temporal': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/TemporalV3',
        'frequencia': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/FrequencyV3'
    },
    assetIm: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',    
    assetBacia: "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga",    
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
};
var incluieMA = true;
var version = 18;
var janela = 5
var selBacia = '775';
var yearcourrent = 1986;
var banda_activa = 'classification_' + String(yearcourrent);
var FeatColbacia = ee.FeatureCollection(param.assetBacia);
var imgMapCol80= ee.Image(param.assetMapC8)//.clip(FeatColbacia.geometry());
var poligon = ee.FeatureCollection(param.assetPol + selBacia + "_" + yearcourrent.toString())
var biomaRaster = ee.Image(param.asset_bioma_raster).eq(5);
if (incluieMA){
    biomaRaster = biomaRaster.add(ee.Image(param.asset_bioma_raster).eq(2));
}

var imgMapCol9TempV8 =  ee.ImageCollection(param.asset_filted.temporal)
                                    .filter(ee.Filter.eq('version', version))
                                    .filter(ee.Filter.eq('janela', janela))
                                    .min();

imgMapCol9TempV8 = imgMapCol9TempV8.select(banda_activa);
var imgMapCol8FreqV1 =  ee.ImageCollection(param.asset_filted.frequencia)
                                    .filter(ee.Filter.eq('version', version)).min();
var mapYear85 = imgMapCol8FreqV1.select('classification_1985');
var mapYear86 = imgMapCol8FreqV1.select('classification_1986');
var mapYear88 = imgMapCol8FreqV1.select('classification_1988');
var mapYear90 = imgMapCol8FreqV1.select('classification_1990');
var mapYear95 = imgMapCol8FreqV1.select('classification_1995');
var mapYear20 = imgMapCol8FreqV1.select('classification_2020');

print("imagem no Asset Geral X Bacias col 8", imgMapCol8FreqV1);
var lstbands = ee.List([])
var lstSeq = ee.List.sequence(1,38).getInfo();
print("lista de sequencia de numeros ", lstSeq)
var maskFlorRec = ee.Image.constant(0);
var contFlorest = ee.Image.constant(0);
var contSavana = ee.Image.constant(0);
param.anos.slice(0, 5).forEach(function(yyear){
    var bandaAct = 'classification_' + yyear
    print("banda " + bandaAct)
    lstbands = lstbands.add(bandaAct)
    var mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
    var maskFlorest = mapFloresttmp.eq(3);
    maskFlorRec = maskFlorRec.add(maskFlorest)//.gt(0);
})
// maskFlorRec = maskFlorRec.gt(0);
param.anos.slice(0, 5).forEach(function(yyear){
    var bandaAct = 'classification_' + yyear
    lstbands = lstbands.add(bandaAct);
    var mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
    var maskFlorest = mapFloresttmp.eq(3);
    contFlorest = contFlorest.add(maskFlorest.multiply(maskFlorRec.gt(0)));
    contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec.gt(0)));
})
var limAno = 5;
var maskcomparativa = contFlorest.gt(contSavana);  // incluir todos estes pixeis
// addiciona_removidos = maskcomparativa.subtract(imgMapCol8FreqV1.select(bandaAct).eq(3)) // valores com 1 ficam valores com -1 somem
var pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0); // resgatam pixeis que não sao da classe 3 ou 4e coloca os de savana maior
var bandaAct = 'classification_1989'
var florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1988').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
print('1989 florestAno_men2 ', bandaAct, florestAno_men2)
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0); // pixelsIncluisao;

// pixelsExcluidos = pixelsExcluidos.add(florestAno_men2);

print('1989 florestAno_men2 ', florestAno_men2)


var imgMapCol8temp = imgMapCol80.select(banda_activa).remap(param.classMapB, param.classNew);
Map.addLayer(imgMapCol8temp, visualizar.visclassCC, 'Col80_' + String(yearcourrent), false);

Map.addLayer(mapYear85,  visualizar.visclassCC, 'Col8_1985', false);
Map.addLayer(mapYear86,  visualizar.visclassCC, 'Col8_1986', false);
Map.addLayer(mapYear88,  visualizar.visclassCC, 'Col8_1988', false);
Map.addLayer(mapYear90,  visualizar.visclassCC, 'Col8_1990', false);
Map.addLayer(mapYear95,  visualizar.visclassCC, 'Col8_1995', false);
Map.addLayer(mapYear20,  visualizar.visclassCC, 'Col8_2020', false);

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 89', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 89', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 89', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 89', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 89', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 89', false);

// var knowFalta = FeatColbacia.filterBounds(Points)
// var lstBacia = knowFalta.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list');
// print("lista das bacias ", lstBacia)
// Map.addLayer(knowFalta, {color: 'red'}, "baciasFiletrs")

limAno += 1;
var yyear = '1990'
var bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
var mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec.gt(0)));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec.gt(0)));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1989').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)
// pixelsExcluidos = pixelsExcluidos.add(florestAno_men2);

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 90', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 90', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 90', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 90', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 90', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 90', false);




limAno += 1;
var yyear = '1991'
var bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
var mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1990').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)
// pixelsExcluidos = pixelsExcluidos.add(florestAno_men2);

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 91', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 91', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 91', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 91', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 91', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 91', false);


limAno += 1;
yyear = '1992'
bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1991').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)

// pixelsExcluidos = pixelsExcluidos.add(florestAno_men2);

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 92', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 92', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 92', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 92', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 92', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 92', false);


limAno += 1;
yyear = '1993'
bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1992').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)



Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 93', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 93', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 93', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 93', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 93', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 93', false);


limAno += 1;
yyear = '1994'
bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1993').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)



Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 94', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 94', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 94', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 94', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 94', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 94', false);


limAno += 1;
yyear = '1995'
bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
// juntar a remo~]ao os pixeis savana maior que floresta
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1994').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 95', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 95', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 95', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 95', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 95', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 95', false);


limAno += 1;
yyear = '1996'
bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1995').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 96', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 96', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 96', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 96', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 96', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 96', false);




limAno += 1;
yyear = '1997'
bandaAct = 'classification_' + yyear
lstbands = lstbands.add(bandaAct)
mapFloresttmp = imgMapCol8FreqV1.select(bandaAct);
maskFlorRec = maskFlorRec.add(mapFloresttmp.eq(3));
contFlorest = contFlorest.add(mapFloresttmp.eq(3).multiply(maskFlorRec).gt(0));
contSavana = contSavana.add(mapFloresttmp.eq(4).multiply(maskFlorRec).gt(0));

maskcomparativa = contFlorest.gt(contSavana);
pixelsExcluidos = maskFlorRec.gt(0).multiply(limAno).subtract(contFlorest.add(contSavana));
pixelsExcluidos = pixelsExcluidos.add(contSavana.gt(contFlorest)).gt(0);

florestAno_men2 = imgMapCol8FreqV1.select( 'classification_1996').eq(3).add(imgMapCol8FreqV1.select(bandaAct).eq(3));
florestAno_men2 = florestAno_men2.eq(2).add(maskcomparativa).gt(0);
florestAno_men2 = florestAno_men2.subtract(pixelsExcluidos).gt(0)

Map.addLayer(maskFlorRec, visualizar.maskFlor, 'maskFloresta 97', false);
Map.addLayer(contFlorest.updateMask(contFlorest.gt(0)), visualizar.maskContaF, 'ContadFloresta 97', false);
Map.addLayer(contSavana.updateMask(contSavana.gt(0)), visualizar.maskContSav, 'contadSavana 97', false);
Map.addLayer(maskcomparativa, visualizar.maskcomp, 'comparativa 97', false);
Map.addLayer(florestAno_men2.selfMask(), {min:0, max:1, palette: '000000,FF00ff'}, 'incluir 97', false);
Map.addLayer(pixelsExcluidos.selfMask(), {min:0, max:1, palette: '000000,0000ff'}, 'pixel a Excluir 97', false);
