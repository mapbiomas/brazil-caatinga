var dictCod =  {
    "7411": {"nunivotto4": "7411", "id_codigo": 28}, "7422": {"nunivotto4": "7422", "id_codigo": 23}, "7424": {"nunivotto4": "7424", "id_codigo": 10}, 
    "7438": {"nunivotto4": "7438", "id_codigo": 44}, "7443": {"nunivotto4": "7443", "id_codigo": 41}, "745": {"nunivotto4": "745", "id_codigo": 9}, 
    "746": {"nunivotto4": "746", "id_codigo": 49}, "751": {"nunivotto4": "751", "id_codigo": 6}, "752": {"nunivotto4": "752", "id_codigo": 7}, 
    "753": {"nunivotto4": "753", "id_codigo": 35}, "7541": {"nunivotto4": "7541", "id_codigo": 37}, "7544": {"nunivotto4": "7544", "id_codigo": 43}, 
    "755": {"nunivotto4": "755", "id_codigo": 17}, "7561": {"nunivotto4": "7561", "id_codigo": 16}, "7564": {"nunivotto4": "7564", "id_codigo": 19}, 
    "757": {"nunivotto4": "757", "id_codigo": 30}, "7581": {"nunivotto4": "7581", "id_codigo": 3}, "7584": {"nunivotto4": "7584", "id_codigo": 5}, 
    "7591": {"nunivotto4": "7591", "id_codigo": 46}, "7592": {"nunivotto4": "7592", "id_codigo": 47}, "761111": {"nunivotto4": "761111", "id_codigo": 20}, 
    "761112": {"nunivotto4": "761112", "id_codigo": 21}, "76116": {"nunivotto4": "76116", "id_codigo": 24}, "7612": {"nunivotto4": "7612", "id_codigo": 12}, 
    "7613": {"nunivotto4": "7613", "id_codigo": 13}, "7614": {"nunivotto4": "7614", "id_codigo": 14}, "7615": {"nunivotto4": "7615", "id_codigo": 27}, 
    "7616": {"nunivotto4": "7616", "id_codigo": 8}, "7617": {"nunivotto4": "7617", "id_codigo": 18}, "7618": {"nunivotto4": "7618", "id_codigo": 15}, 
    "7619": {"nunivotto4": "7619", "id_codigo": 40}, "7622": {"nunivotto4": "7622", "id_codigo": 48}, "7625": {"nunivotto4": "7625", "id_codigo": 4}, 
    "763": {"nunivotto4": "763", "id_codigo": 45}, "764": {"nunivotto4": "764", "id_codigo": 36}, "765": {"nunivotto4": "765", "id_codigo": 42}, 
    "766": {"nunivotto4": "766", "id_codigo": 33}, "7671": {"nunivotto4": "7671", "id_codigo": 26}, "7691": {"nunivotto4": "7691", "id_codigo": 2}, 
    "771": {"nunivotto4": "771", "id_codigo": 31}, "7712": {"nunivotto4": "7712", "id_codigo": 32}, "772": {"nunivotto4": "772", "id_codigo": 39}, 
    "7721": {"nunivotto4": "7721", "id_codigo": 38}, "773": {"nunivotto4": "773", "id_codigo": 11}, "7741": {"nunivotto4": "7741", "id_codigo": 22}, 
    "7746": {"nunivotto4": "7746", "id_codigo": 34}, "7754": {"nunivotto4": "7754", "id_codigo": 1}, "7761": {"nunivotto4": "7761", "id_codigo": 25}, 
    "7764": {"nunivotto4": "7764", "id_codigo": 29}
};
var listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753','764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', 
    '7438', '763', '7591', '7592', '7622', '746'
];

function processoExportarImage(rasterExp, nametoExp, assetOutput, myGeo){
    
    var optExp = {
        'image': rasterExp,
        'description': nametoExp,
        'assetId': assetOutput + "/" + nametoExp,
        'scale': 10,
        'pyramidingPolicy': {'.default': 'mode'},
        'maxPixels': 1e13,
        'region': myGeo
      }
    Export.image.toAsset(optExp); 
}

var param = {
    'asset_raster_biomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    'asset_bacias_raster' : 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',
    'limit_basin': {
        'asset_bacias_shp' : 'projects/ee-solkancengine17/assets/shape/bacias_caatinga_div_49_regions',
    },
    'limit_basin_buffer': {
        'asset_bacias_shp' : 'projects/ee-solkancengine17/assets/shape/bacias_hidrografica_caatinga_49_regions',
    },
    'asset_output': 'projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions',
}
var idBasin = '7754';
var regSel, imgReg, nameExport ;
var isBuffer = false;
// var buildingBuffer = false;
var wantExport = true;
var assetExp = param.asset_output;

var biomaraster = ee.Image(param.asset_raster_biomas).eq(5);
if (isBuffer){
    var baciaRegions = ee.FeatureCollection(param.limit_basin_buffer.asset_bacias_shp);
    print("show data bacias Regions buffer ", baciaRegions);
    var rasterRegions = ee.ImageCollection(param.asset_bacias_raster).filter(ee.Filter.eq('isBuffer', 1));
    print("Metadata raster Regions buffer ", rasterRegions);
}else{
    var baciaRegions = ee.FeatureCollection(param.limit_basin.asset_bacias_shp);
    print("show data bacias Regions ", baciaRegions);
    var rasterRegions = ee.ImageCollection(param.asset_bacias_raster).filter(ee.Filter.eq('isBuffer', 0));
    print("Metadata raster Regions ", rasterRegions);
}
// projects/ee-solkancengine17/assets/bacias_raster_Caatinga_49_regions/raster_bacias_buf_7754
var sizeRaster = rasterRegions.size().getInfo();
var basin_select = rasterRegions.filter(ee.Filter.eq('nunivotto4', idBasin)).first();
print("basin selected ", basin_select);
Map.addLayer(biomaraster.selfMask(), {min:0, max: 1, palette: 'green'}, 'caatinga');
Map.addLayer(baciaRegions, {color: 'yellow'}, 'baciaReg');
Map.addLayer(basin_select, {min:0, max: 1, palette: 'green'}, 'basin ' + idBasin);


listaNameBacias.forEach(function(nbacia){
    var idcod = dictCod[nbacia]["id_codigo"];
    print("Codigo selecionado " + idcod);
    regSel = baciaRegions.filter(ee.Filter.eq('nunivotto4', nbacia));
    print(regSel)
    if (isBuffer)
    {
        imgReg = regSel.reduceToImage(['id_codigo'], ee.Reducer.first());
        imgReg = imgReg.set('id_codigo', idcod, 'nunivotto4', String(nbacia), 'isBuffer', 1);
        // print("setando os parametros ", )
        nameExport = 'raster_bacias_buf_' + nbacia;
    }
    else 
    {
        if (sizeRaster < 49)
        {
            imgReg = regSel.reduceToImage(['id_codigo'], ee.Reducer.first());
            imgReg = imgReg.set('id_codigo', idcod, 'nunivotto4', String(nbacia), 'isBuffer', 0);
            nameExport = 'raster_bacias_' + nbacia;
        }
        else
        {
            imgReg = rasterRegions.filter(ee.Filter.eq("id_codigo", idcod)).first();
        }
    }
    print("inspeccionando " + nbacia, imgReg);
    if (wantExport)
    {
        processoExportarImage(imgReg, nameExport, assetExp, regSel.geometry());
    }
    if(nbacia === idBasin)
    {
        Map.addLayer(imgReg.selfMask(), {min: 0, max: 1, palette: 'red'}, 'regImg');
        Map.addLayer(regSel, {color: 'blue'}, 'reg vetor');
    }
})