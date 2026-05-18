// https://code.earthengine.google.com/68e5117ac0ce5721d4e0706b94bd2477
var vis = {
    mosaic: {
            bands: ['red_median', 'green_median', 'blue_median'],
            min: 20, 
            max: 3500
    },
    mosaicNorm: {
            bands: ['red_median', 'green_median', 'blue_median'],
            min: 0.02, 
            max: 0.8
    },
    indexRock: {
        min: 0,
        max: 1,
        palette: [
            "41ab5d","78c679","addd8e","d9f0a3","f7fcb9","ffffe5","ffffe5",
            "fff7bc","fee391","fec44f","fe9929","ec7014","cc4c02","8c2d04"
        ]
    },
    indexVeg: {
        min: 0,
        max: 1,
        palette: [
            "ffffe5","f7fcb9","d9f0a3","addd8e","78c679","41ab5d","238443","005a32"
        ]
    },
    indexSlope: {
        min: 0,
        max: 1,
        palette: [
            "252525","525252","737373","969696","bdbdbd","d9d9d9","f0f0f0","ffffff"
        ]
    } 
};

var assetStast = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/stats_mosaics/all_statisticsL81985';
var featColStast = ee.FeatureCollection(assetStast);
print(featColStast.first());
var asset_bacias = 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga'
var limitCaat = ee.FeatureCollection(asset_bacias);
var bandMos = [
    'slope','blue_median', 'blue_median_wet', 'blue_median_dry', 
    'green_median', 'green_median_dry', 'green_median_wet',
    'red_median', 'red_median_dry', 'red_median_wet',  
    'nir_median', 'nir_median_dry', 'nir_median_wet',  
    'swir1_median', 'swir1_median_dry', 'swir1_median_wet', 
    'swir2_median', 'swir2_median_wet', 'swir2_median_dry'
];
// def calculing_zcore_modifing(arrX, xmean, xstd):
//     calcZ = (arrX - xmean) / xstd
//     expBandAft =  np.exp(-1 * calcZ)
//     return 1 / (1 + expBandAft)

// Bare Soil Index 
var agregateBandsIndexBSI = function(img){  
     
    var bsiImgY = img.expression(
        "float(((b('swir1_median') - b('red_median')) - (b('nir_median') + b('blue_median'))) / ((b('swir1_median') + b('red_median')) + (b('nir_median') + b('blue_median'))))")
            .add(1).divide(2).rename(['bsi_median']).toFloat()
    var bsiImgwet = img.expression(
        "float(((b('swir1_median_wet') - b('red_median_wet')) - (b('nir_median_wet') + b('blue_median_wet'))) / ((b('swir1_median_wet') + b('red_median_wet')) + (b('nir_median_wet') + b('blue_median_wet'))))")
            .add(1).divide(2).rename(['bsi_median_wet']).toFloat()

    var bsiImgdry = img.expression(
        "float(((b('swir1_median_dry') - b('red_median_dry')) - (b('nir_median_dry') + b('blue_median_dry'))) / ((b('swir1_median_dry') + b('red_median_dry')) + (b('nir_median_dry') + b('blue_median_dry'))))")
            .add(1).divide(2).rename(['bsi_median_dry']).toFloat()
            
    
    return img.addBands(bsiImgY).addBands(bsiImgwet).addBands(bsiImgdry)

}


// SAVI OSAVI	Optimized Soil-Adjusted Vegetation Index	vegetation	(N - R) / (N + R + 0.16)
var agregateBandsIndexSAVI =  function(img){
    var saviImgY = img.expression(
        "float((b('nir_median') - b('red_median')) / (b('nir_median') + b('red_median') + 0.16))")
           .add(1).divide(2).rename(['savi_median']).toFloat() 
    var saviImgWet = img.expression(
        "float((b('nir_median_wet') - b('red_median_wet')) / (b('nir_median_wet') + b('red_median_wet') + 0.16))")
           .add(1).divide(2).rename(['savi_median_wet']).toFloat() 

    var saviImgDry = img.expression(
        "float((b('nir_median_dry') - b('red_median_dry')) / (b('nir_median_dry') + b('red_median_dry') + 0.16))")
           .add(1).divide(2).rename(['savi_median_dry']).toFloat()         
    
    return img.addBands(saviImgY).addBands(saviImgWet).addBands(saviImgDry)

    }

// Host Rocks - SWIR1/SWIR2
var agregateBandsIndexhostyocks = function(img){    
    var hostRockImgY = img.expression(
        "float(b('swir1_median')  / b('swir2_median'))")
           .rename(['HR_median']).toFloat() 
    var hostRockImgWet = img.expression(
        "float(b('swir1_median_wet')  / b('swir2_median_wet'))")
           .rename(['HR_median_wet']).toFloat()

    var hostRockImgDry = img.expression(
        "float(b('swir1_median_dry')  / b('swir2_median_dry'))")
           .rename(['HR_median_dry']).toFloat()         
    
    return img.addBands(hostRockImgY).addBands(hostRockImgWet).addBands(hostRockImgDry)
}

// Ferrous Rocks - SWIR1/NIR
var agregateBandsIndexFerrRocks = function(img){
    var ferrRockImgY = img.expression(
        "float(b('swir1_median')  / b('nir_median'))")
           .rename(['FR_median']).toFloat() 

    var ferrRockImgWet = img.expression(
        "float(b('swir1_median_wet')  / b('nir_median_wet'))")
           .rename(['FR_median_wet']).toFloat() 
             
    var ferrRockImgDry = img.expression(
        "float(b('swir1_median_dry')  / b('nir_median_dry'))")
           .rename(['FR_median_dry']).toFloat() 
    
    return img.addBands(ferrRockImgY).addBands(ferrRockImgWet).addBands(ferrRockImgDry)
};

// Eisenhydroxid-Index - SWIR2/RED
var agregateBandsIndexEisenIndex = function(img){
    
    var eisenIndexImgY = img.expression(
        "float(b('swir2_median')  / b('red_median'))")
           .rename(['EI_median']).toFloat()        

    var eisenIndexImgWet = img.expression(
        "float(b('swir2_median_wet')  / b('red_median_wet'))")
           .rename(['EI_median_wet']).toFloat()  
    
    var eisenIndexImgDry = img.expression(
        "float(b('swir2_median_dry')  / b('red_median_dry'))")
           .rename(['EI_median_dry']).toFloat()  
    
    return img.addBands(eisenIndexImgY).addBands(eisenIndexImgWet).addBands(eisenIndexImgDry)
}

// 
var CalculateIndiceAllinOne = function(imageW){
    
    imageW = agregateBandsIndexSAVI(imageW)
    imageW = agregateBandsIndexBSI(imageW)
    imageW = agregateBandsIndexhostyocks(imageW)
    imageW = agregateBandsIndexFerrRocks(imageW)
    imageW = agregateBandsIndexEisenIndex(imageW)
    
    return imageW
};

var normalizeImg_porBanda = function(imCol, featCoSt){
                    var newImgCol = imCol.map(function(img){
                                        var idIm = img.id();
                                        var featSt = featCoSt.filter(ee.Filter.eq('id_img', idIm)).first();
                                        var imgNormal = img.addBands(ee.Image.constant(1));
                                        imgNormal = imgNormal.select(['constant']);
                                        var bandMos = [
                                              'blue_median', 'blue_median_wet', 'blue_median_dry', 
                                              'green_median', 'green_median_dry', 'green_median_wet',
                                              'red_median', 'red_median_dry', 'red_median_wet',  
                                              'nir_median', 'nir_median_dry', 'nir_median_wet',  
                                              'swir1_median', 'swir1_median_dry', 'swir1_median_wet', 
                                              'swir2_median', 'swir2_median_wet', 'swir2_median_dry'
                                          ];

                                        bandMos.forEach(function(bnd){
                                            var bndMed = bnd + '_mean';
                                            var bndStd = bnd + '_stdDev';
                                            var band_tmp = img.select(bnd);
                                            //  calcZ = (arrX - xmean) / xstd;
                                            var calcZ = band_tmp.subtract(ee.Image.constant(featSt.get(bndMed)))
                                                              .divide(ee.Image.constant(featSt.get(bndStd)));
                                            //     expBandAft =  np.exp(-1 * calcZ)
                                            var expBandAft = calcZ.multiply(ee.Image.constant(-1)).exp();
                                            //     return 1 / (1 + expBandAft)
                                            var bndend = expBandAft.add(ee.Image.constant(1)).pow(ee.Image.constant(-1));
                                            imgNormal = imgNormal.addBands(bndend.rename(bnd));
                                        });
                                        imgNormal = imgNormal.select(bandMos).toFloat();
                                        imgNormal = CalculateIndiceAllinOne(imgNormal);

                                        return imgNormal;
                                    });
                                    
                    return newImgCol;
                  };

var imgMos = ee.ImageCollection('projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2').filter(
                                            ee.Filter.eq('version', '1')).filter(
                                                ee.Filter.eq('biome', 'CAATINGA')).filter(
                                                    ee.Filter.eq('year', 1985)).select(bandMos);
                             
print("loading Image Collection ", imgMos)
var imgColNorm = normalizeImg_porBanda(imgMos, featColStast)
print("vendo os resultados de la normalização ", imgColNorm);
var mosaic = imgMos.filterBounds(localizador).first();
var idI = mosaic.id();
var featN = featColStast.filter(ee.Filter.eq('id_img', idI));
print("feat filtered ", featN);

var mosaicNorm = imgColNorm.filterBounds(localizador).first();
print("bandas do mosaico normalizado ",mosaicNorm.bandNames());
// Reduce the region. The region parameter is the Feature geometry.
var minMaxDict = mosaicNorm.reduceRegion({
  reducer: ee.Reducer.minMax(),
  geometry: mosaicNorm.geometry(),
  scale: 30,
  maxPixels: 1e9
});

// The result is a Dictionary.  Print it.
print("dict min max ", minMaxDict);

Map.addLayer(mosaic, vis.mosaic, 'mosaic');
Map.addLayer(mosaicNorm, vis.mosaicNorm, 'mosaicNorma');
var coord = [-41.24991919607103, -2.5001446905018065];
var PointCentro = ee.Geometry.Point(coord);
Map.addLayer(PointCentro, {color: 'red'}, 'PointCentro');
// Map.centerObject(PointCentro, 9);



var allindexBands   = [
    'slope','blue_median','green_median','red_median',
    'savi_median','savi_median_wet','savi_median_dry',
    'bsi_median','bsi_median_wet','bsi_median_dry',      
    'HR_median','HR_median_wet','HR_median_dry',
    'FR_median','FR_median_wet','FR_median_dry',
    'EI_median','EI_median_wet','EI_median_dry',
]
var selectIndexBnd = [
    'slopeA','savi_median','HR_median','FR_median','EI_median'
]

Map.addLayer(mosaic.select('slope').divide(1500), vis.indexSlope, 'slope');
Map.addLayer(mosaicNorm.select('savi_median'), vis.indexVeg, 'SAVI');
Map.addLayer(mosaicNorm.select('HR_median'), vis.indexRock, 'HR_m');
Map.addLayer(mosaicNorm.select('FR_median'), vis.indexRock, 'FR_m');
Map.addLayer(mosaicNorm.select('EI_median'), vis.indexRock, 'EI_m');