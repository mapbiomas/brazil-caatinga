
var apply_incidence = function(imgActual, imgPrevious){
 
    var imgincidence = ee.Image(imgPrevious).select(["incidence"]);
    
    var classification0 = ee.Image(imgPrevious).select(["classification"]);
    var classification1 = ee.Image(imgActual).select(["classification"]);
    
    imgincidence = imgincidence.where(
                        classification0.neq(classification1), 
                        imgincidence.add(1)
                    );    
    return imgActual.addBands(imgincidence);    
};
var exportMaps= function(imgMaps, namesImExp, geometLimit){
    var assetIdExp = 'users/CartasSol/Mapbiomas/' + namesImExp;
    var myFolder = 'MAPBIOMAS-EXPORT';
    var pmtroExpAsset = {
        'image': imgMaps.toUint8(),
        'description': namesImExp,
        'region': geometLimit.geometry(),
        "pyramidingPolicy":{".default": "mode"},
        'assetId': assetIdExp,
        'maxPixels':1e13, 
        'scale': 30          
    };    
    Export.image.toAsset(pmtroExpAsset);

    var pmtroExpdrive = {
        'image': imgMaps.toUint8(),
        'description': namesImExp,
        'region': geometLimit,
        'folder': myFolder,
        'maxPixels':1e13, 
        'scale': 30
    }
    Export.image.toDrive(pmtroExpdrive);
    
    print("exporting Image Maps  " + namesImExp + " to Folder => " + myFolder);
    print(" and asset  => " + assetIdExp );
}
//======================  Edição Usuario =======================================
var Palettes = require('users/mapbiomas/modules:Palettes.js');
var palette = Palettes.get('classification7');
var vis = {
    mapbiomas: {
        'min': 0,
        'max': 62,
        'palette': palette,
        'format': 'png'
    },
    incidents: {
        min:0, 
        max:8,
        palette:[
            "#C8C8C8","#FED266","#FBA713","#cb701b","#cb701b", 
            "#a95512","#a95512","#662000","#662000","#cb181d"
        ],
        format: 'png'
    },
    states: {
        min:1, 
        max:5,
        palette: "#C8C8C8,#AE78B2,#772D8F,#4C226A,#22053A"
    },
    combination: {
        min: 1, 
        max: 6,
        palette: "#C9C9C9,#F0F076,#782E90,#f4a295,#ff6d56,#ff2200"
    },
    bioma: {
        featureCollection: null,
        color: 'CD_Bioma',
        width: 2
    }
        
};

var classMapB =  [ 3, 4, 5, 6, 9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62];
var classNew =   [ 3, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0];
// var asset_classificacao = "projects/mapbiomas-workspace/COLECAO2_3/classificacao";
//var asset_integracao = "projects/mapbiomas-workspace/COLECAO2_3/classificacao-ft";
//var asset_integracao = "projects/mapbiomas-workspace/COLECAO2_3/integracao";

var param = {
    'asset_integracao' : "projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1",
    'asset_biomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'year_start': 1985,
    'year_end': 2022,
    'expor_img': true
}
var dictCDbiomas = {
    '1': 'Amazônia',
    '2': 'Caatinga',
    '3': 'Cerrado',
    '4': 'Mata Atlântica',
    '5': 'Pampa',
    '6': 'Pantanal'
};
var lstCombinationValues = [1,2,3,4,5,6];
var dictCombination = {
    '1': 'persistence',
    '2': 'One incident',
    '3': 'Toggle',
    '4': 'low states',
    '5': 'medium states',
    '6': 'high states'
}
var dictcombVal = {
    '1': [0,1],
    '2': [1,2],
    '3': [1,2],
    '4': [1,2],
    '5': [5,3],
    '6': [5,5]
}
var bandActual = "classification_2022"

var bbiomas = ee.FeatureCollection(param.asset_biomas);
var mapsMapbiomas = ee.Image(param.asset_integracao);
print("mapas da Coleção 8",mapsMapbiomas); 
var years = ee.List.sequence(param.year_start, param.year_end).getInfo();
print("list of years ", years)
// remap to natural class
var col8mapEst = mapsMapbiomas.select('classification_' + param.year_start).remap(classMapB, classNew).gt(0);

// building stavel class map
var lstBand = ee.List([]);
var lstImgs = ee.List([])
years.forEach(function(year){
    var bandCC = 'classification_' + year.toString();
    lstBand = lstBand.add(bandCC);
    var tmpClass = mapsMapbiomas.select(bandCC);
    lstImgs = lstImgs.add(tmpClass.rename("classification"))
    tmpClass = tmpClass.remap(classMapB, classNew).gt(0);
    col8mapEst = col8mapEst.multiply(tmpClass);
}) 
print("lista de bandass ", lstBand);
print('Lista de images ', lstImgs);
// imc_carta
// var colectionMaps = convertListBandName_to_ImgCollection(lstBand, mapsMapbiomas);
var colectionMaps = ee.ImageCollection.fromImages(lstImgs)
print("coletionm masp ", colectionMaps)
// ************************** states ***********************************
var image_states = colectionMaps.reduce(ee.Reducer.countDistinct());
//**********************************************************************
// ************************ incidence **********************************
var imagefirst = ee.Image(colectionMaps.first()).addBands(
                            ee.Image.constant(0).toByte().rename( "incidence"));

var image_incidence = colectionMaps.iterate(apply_incidence, imagefirst);
image_incidence = ee.Image(image_incidence).select(["incidence"]);
// *********************************************************************

// ********************** processing combination ***********************
var combination = ee.Image.constant(0) //.clip(geometry);
lstCombinationValues.forEach(function(value){
    print("processing " + dictCombination[value.toString()] + " combination");
    var val_inc = dictcombVal[value.toString()][0];
    var val_sta = dictcombVal[value.toString()][1];
    combination = combination.where(image_incidence.eq(val_inc).and(image_states.eq(val_sta)), value);
})
// ******************************************************************** 
// Export incicdnet bioo+'_image_incidence'
if (param.expor_img === true){
    var name_export = 'maps_incidence_br';
    exportMaps(image_incidence, name_export, bbiomas);
    name_export = 'maps_state_br';
    exportMaps(image_states, name_export, bbiomas);
    name_export = 'maps_combination_br';
    exportMaps(combination, name_export, bbiomas);
}

//**************map layout***********************
// var limit = ee.Image().paint(regioe_ft,1,3);
var styles = {
    styleLabel: {
        fontSize: '13px', 
        stretch: 'horizontal',
        position: 'bottom-left', 
        margin:'1px'
    },
}

var mapLeft = ui.Map();
var labelLeft = ui.Label(bandActual, styles.styleLabel);
mapLeft.add(labelLeft);
mapLeft.addLayer(ee.Image.constant(1), {min:0, max: 1}, "base")
vis.bioma.featureCollection = bbiomas;
var LimiteCaat = ee.Image().byte().paint(vis.bioma); 
mapLeft.addLayer(LimiteCaat, {palette: 'FF0000'}, 'Caatinga');
// adding maps 
print(mapsMapbiomas.select(bandActual))
mapLeft.addLayer(mapsMapbiomas.select(bandActual).updateMask(col8mapEst), vis.mapbiomas, bandActual);

var mapRight = ui.Map();
mapRight.addLayer(ee.Image.constant(1), {min:0, max: 1}, "base")
mapRight.addLayer(LimiteCaat, {palette: 'FF0000'}, 'Caatinga');//
mapRight.addLayer(image_incidence.updateMask(col8mapEst), vis.incidents, "incidents", false);
mapRight.addLayer(image_states.clip(bbiomas).updateMask(col8mapEst), vis.states, "States", false);
mapRight.addLayer(combination.clip(bbiomas).updateMask(col8mapEst), vis.combination, "Combination");
var labelRight = ui.Label("Incidents and States", styles.styleLabel);
mapRight.add(labelRight);
var maps = [mapLeft, mapRight]
var linker = ui.Map.Linker([mapLeft, mapRight]);
// Create a grid of maps.
var mapGrid = ui.Panel(
  [
    ui.Panel([mapLeft], null, {stretch: 'both'}),
    ui.Panel([mapRight], null, {stretch: 'both'}),
  ],
  ui.Panel.Layout.Flow('horizontal'), {stretch: 'both'}
);


ui.root.widgets().reset([mapGrid]);
ui.root.setLayout(ui.Panel.Layout.Flow('horizontal'));

// maps[0].centerObject(img1, 10);


//***************************************************

//*******************Panel***************************


var panel = ui.Panel();
panel.style().set('width', '300px');
var intro = ui.Panel([
    ui.Label('Click a point on the map to inspect.')
]);
panel.add(intro);


var lon = ui.Label();
var lat = ui.Label();
panel.add(ui.Panel([lon, lat], ui.Panel.Layout.flow('horizontal')));


var legendas = ee.FeatureCollection("users/dyedenm/legendas");
legendas = legendas.getInfo()['features'].map(function(item){return item['properties']});

var clickmap = function (maps, i){
    maps[i].onClick(function(coords) {
        lon.setValue('lon: ' + coords.lon.toFixed(2)),
        lat.setValue('lat: ' + coords.lat.toFixed(2));    

        var point = ee.Geometry.Point(coords.lon, coords.lat);
        point = ee.FeatureCollection(point);
        var dot1 = ui.Map.Layer(point.draw({
                            color: 'FF0000',
                            pointRadius:5,
                            strokeWidth:2,
                        }),null, "point");
        
        var dot2 = ui.Map.Layer(point.draw({
                            color: 'FF0000',
                            pointRadius:5,
                            strokeWidth:2,
                        }),null, "point");

        maps[0].layers().set(3, dot2);
        maps[1].layers().set(5, dot1);

    
        var pixelseries = colectionMaps.getRegion(point, 30).getInfo().map(
                                function(item){return item[4]});      
        pixelseries = pixelseries.filter(function(item){return item !== "classification"});

        var data = {
                cols: [
                    {label: 'Year', type: 'string'},
                    {label: 'Classe', type: 'number'},
                ],                
                rows: []
        };

        pixelseries.forEach(function(item, index){
            var name = null;
            
            legendas.forEach(function(itemb, index){
                if (item === itemb.value){
                    name = itemb.class;
                }
            });
            
            var year = String(2016 + index);
            data.rows.push({c:[{v: year}, {v: item,  f: item + " " + name}]});
        
        });
    
        var options = {
            title: 'Classification Over Time',
            vAxis: {title: 'values'},
            hAxis: {title: 'date', format: '0', gridlines: {count: 7}},
            legend: 'none'
        };
        var chart = new ui.Chart(data, 'LineChart', options);


        panel.widgets().set(2, chart);
    
        addLegend();
    });
};

clickmap(maps, 0);
clickmap(maps, 1);

maps[1].style().set('cursor', 'crosshair');
maps[0].style().set('cursor', 'crosshair');


//************Adicionar legenda****************************
var makeRow = function(color, name) {
    var colorBox = ui.Label({
        style: {
        backgroundColor: color,

        padding: '8px',
        margin: '0 0 4px 0'
        }
    });

    var description = ui.Label({
        value: name,
        style: {margin: '0 0 4px 6px'}
    });

    return ui.Panel({
        widgets: [colorBox, description],
        layout: ui.Panel.Layout.Flow('horizontal')
    });
};



var addLegend = function(){
    var legend = ui.Panel({
        style: {
        position: 'bottom-left',
        padding: '8px 15px'
        }
    });

    var legendTitle = ui.Label({
        value: 'Combination',
        style: {
        fontWeight: 'bold',
        fontSize: '15px',
        margin: '0 0 4px 0',
        padding: '0'
        }
    });
  
    legend.add(legendTitle);
    var palette = ["#C9C9C9","#F0F076","#782E90","#f4a295","#ff6d56","#ff2200"];
    var names = ["Persistence", "One incident", "Toggle", "(n>2) states", "(n>3) states", "(n>5) states"];
    
    for (var i = 0; i < names.length; i++) {
        legend.add(makeRow(palette[i], names[i]));
    }
    panel.widgets().set(3, legend);    
    legend = ui.Panel({ style: {position: 'bottom-left',padding: '8px 15px'} });    

    legendTitle = ui.Label({
        value: 'States',
        style: {
            fontWeight: 'bold',
            fontSize: '15px',
            margin: '0 0 4px 0',
            padding: '0'
        }
    });
  
    legend.add(legendTitle);
    palette = ["#C8C8C8","#AE78B2","#772D8F","#4C226A","#22053A"];
    names = ["1 state", "2 states", "3 states", "4 states", "n>4 states"];
    
    for (var i = 0; i < names.length; i++) {
        legend.add(makeRow(palette[i], names[i]));
    }

    panel.widgets().set(4, legend); 
  
    legend = ui.Panel({ style: {position: 'bottom-left',padding: '8px 15px'} });
    

    legendTitle = ui.Label({
        value: 'Incidents',
        style: {
            fontWeight: 'bold',
            fontSize: '15px',
            margin: '0 0 4px 0',
            padding: '0'
        }
    });  
    legend.add(legendTitle);
    palette = ["#C8C8C8","#FED266","#FBA713","#cb701b", "#a95512", "#662000", "#cb181d"];
    names = ["0 incidents", "1 incident", "2 incidents", "3 incidents", "n>3 incidents", "n>5 incidents", "n>7 incidents"];    
    for (var i = 0; i < names.length; i++) {
        legend.add(makeRow(palette[i], names[i]));
    }

    panel.widgets().set(5, legend);
};
addLegend();

//***********************************************************

ui.root.add(panel);

