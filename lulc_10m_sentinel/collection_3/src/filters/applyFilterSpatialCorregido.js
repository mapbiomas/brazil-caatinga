// https://code.earthengine.google.com/f7fa08ed1f4f1e3c9c3771336a8077b2
var palettes = require('users/mapbiomas/modules:Palettes.js');
var text = require('users/gena/packages:text')

var visualizar = {
    visclassCC: {
            "min": 0, 
            "max": 69,
            "palette":  palettes.get('classification9'),
            "format": "png"
    },
    visMosaic: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },
    visFreq : {
        max: 5,
        min: 0,
        palette: ['#000000','#faf3dd','#c8d5b9','#f19c79','#fec601','#013a63']
    },
    mask: {
        max: 1,
        min: 0,
        palette: ['000000'],    
    }
} 


var asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill/filterGF_BACIA_7721_GTB_V4'
            // projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyVA/BACIA_7691_2024_GTB_col10-v_4
var rasterMap = ee.Image(asset).select('classification_2024');
var maxNumbPixels = 20;
var rasterConnect = rasterMap.connectedPixelCount({
                                            maxSize: maxNumbPixels, 
                                            eightConnected: true
                                        })

// var rasterConnect = ee.Image(asset).select('classification_2024_conn');
print("metadatos ", rasterMap);
var maskConn = rasterConnect.lt(maxNumbPixels).selfMask()
// Define o tamanho da janela do filtro (3x3 neste caso)
// var kernel = ee.Kernel.square(1); // Raio de 1 pixel (janela 3x3)
var kernel = ee.Kernel.square(4); // Raio de 2 pixels (janela 5x5)
// Aplica o filtro da maioria
var maskSavUso = rasterMap.eq(4).or(rasterMap.eq(21))
var maskSavFlorest = rasterMap.eq(4).or(rasterMap.eq(3))
var maskUsoSolo = rasterMap.eq(21).or(rasterMap.eq(22))

// a savana dentro dos pixels conectados será classe Uso
var filterImageSavUs = rasterMap.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: kernel
});
var filterImageSavFo = rasterMap.reduceNeighborhood({
    reducer: ee.Reducer.mode(),
    kernel: kernel
});
var filterImageUsoSol = rasterMap.reduceNeighborhood({
    reducer: ee.Reducer.min(),
    kernel: kernel
});
filterImageSavUs = filterImageSavUs.updateMask(maskSavUso).updateMask(maskConn)
filterImageSavFo = filterImageSavFo.updateMask(maskSavFlorest).updateMask(maskConn)
filterImageUsoSol = filterImageUsoSol.updateMask(maskUsoSolo).updateMask(maskConn)
var newMap = rasterMap.blend(filterImageSavUs).blend(filterImageSavFo).blend(filterImageUsoSol);

Map.addLayer(rasterMap, visualizar.visclassCC, 'map_2024');
Map.addLayer(rasterConnect, visualizar.visFreq, 'conn_2024', false);
Map.addLayer(maskConn, visualizar.mask, 'maskconn_2024');
Map.addLayer(filterImageSavUs, visualizar.visclassCC, 'mask_2024');
Map.addLayer(newMap, visualizar.visclassCC, 'new map_2024');




