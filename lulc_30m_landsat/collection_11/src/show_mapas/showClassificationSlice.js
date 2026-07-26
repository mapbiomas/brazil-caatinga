var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text')

var visualizar = {
    visclassCC: {
            "min": 0, 
            "max": 48,
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


var list_year = function(year_ini, year_last){
                                var list_ano = ee.List.sequence(year_ini, year_last)
                                list_ano = list_ano.map(function(year){
                                                            return ee.Algorithms.String(ee.Number(year).toInt())
                                                        })
                                
                                return list_ano
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
    //'743','732','747',
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
var visMosaic = false;
var translate = function (pt, x, y) {
    var x1 = ee.Number(pt.get(0)).subtract(x);
    var y1 = ee.Number(pt.get(1)).subtract(y);    
    return ee.Geometry.Point(ee.List([x1, y1]));
}
  
var yearcourrent = 2019;

// select images
var bounds = Map.getBounds(true);
var scale = Map.getScale();
print("scala ", scale)
scale = ee.Number(scale).subtract(7703)

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



var MapLayerCol6 = ui.Map({
    style: {
        border: '2px solid black'
    }
});
var MapProcess = ui.Map({
    style: {
        stretch: 'both',
        border: '2px solid black'
    }
});

MapProcess.setCenter(-38.1325, -8.3078, 12);
var Mapeando = function(ano){

    MapLayerCol6.clear()
    print("Mapeando ano " + ano.toString());
    var bandaActiva  = 'classification_' + ano.toString();
    var mosaicoTemp = Mosaicos.filter(ee.Filter.eq('year', parseInt(ano))).median();

    MapMosaic = ui.Map.Layer({
                    "eeObject": mosaicoTemp,
                    'visParams': visualizar.visMosaic,
                    'name': 'Mosaic'+ ano,
                    'shown': true,
                    'opacity': 1
                })
    
    var MapMosaicesq = ui.Map.Layer({
                "eeObject": mosaicoTemp,
                'visParams': visualizar.visMosaic,
                'name': 'Mosaic'+ ano,
                'shown': true,
                'opacity': 1
            })

    if (visMosaic === true){
      
        print(MapProcess.layers())
        MapProcess.remove(MapMosaic);
        MapProcess.remove(MapCol7);        
        MapLayerCol6.remove(MapMosaicesq);
        MapLayerCol6.remove(MapCol6);
        
    }
    MapProcess.add(MapMosaic);
    MapLayerCol6.add(MapMosaicesq)
    var imgMapCol6tmp = imgMapCol6.select(bandaActiva).remap(param.classMapB, param.classNew);
    var imgMapCol7tmp = imgMapCol7.select(bandaActiva);
        
    MapCol6 = ui.Map.Layer({
                    "eeObject": imgMapCol6tmp,
                    'visParams': visualizar.visclassCC,
                    'name': 'Col6_pub_' + String(ano),
                    'shown': false,
                    'opacity': 1
                })

    MapLayerCol6.add(MapCol6);
    
    MapCol7= ui.Map.Layer({
                "eeObject": imgMapCol7tmp,
                'visParams': visualizar.visclassCC,
                'name': 'Col7_v1_' + String(ano),
                'shown': true,
                'opacity': 1
            })
    

    MapProcess.add(MapCol7);
       
    if (visMosaic === false){
        var bioma250mil = ee.FeatureCollection('projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil')
                                        .filter(ee.Filter.eq('Bioma', 'Caatinga'))
        MapProcess.addLayer(bioma250mil, {}, "lCaatinga", false)
        visMosaic = true;
    }
    
    // MapTeste.setCenter(-39.7857, -8.888, 12)
    print(MapProcess.layers())
}




print('Iniciando Rotina...🔥🔥' )
var slider=  ui.Slider({
      min:1985,
      max:2021,
      value:2019,
      step:1,
      direction: 'vertical',
      onChange:function(value){
        Mapeando(value)
      },
      style:{
        width:'50px',
        height: '200px',
        margin: 0,
        position: 'middle-right'
      }
});


Mapeando(2019)

MapProcess.add(slider)
// MapTeste.setCenter(-39.7857, -8.888, 12)
var Maplincados = ui.Map.Linker([MapLayerCol6, MapProcess]);


var compPanel = ui.SplitPanel({
    firstPanel: Maplincados.get(0),
    secondPanel: Maplincados.get(1),
    orientation: 'horizontal',
    wipe: true,
    style: {
        stretch: 'both'
    }
});



ui.root.clear()
ui.root.add(compPanel)