// https://code.earthengine.google.com/48383fd92e965c5a6e62e9ded38bc47f
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
};

var assetStast = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/stats_mosaics/all_statisticsL81985';
var featColStast = ee.FeatureCollection(assetStast);
print(featColStast.first());
var asset_bacias = 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga'
var limitCaat = ee.FeatureCollection(asset_bacias);
var bandMos = [
    'blue_median', 'blue_median_wet', 'blue_median_dry', 
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
                                        
                                        return imgNormal.select(bandMos).toFloat();
                                    });
                                    
                    return newImgCol;
                  };

var imgMos = ee.ImageCollection('projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2').filter(
                                            ee.Filter.eq('version', '1')).filterBounds(limitCaat
                                                ).filter(ee.Filter.eq('year', 1985)).select(bandMos);
                             
print("loading Image Collection ", imgMos)
var imgColNorm = normalizeImg_porBanda(imgMos, featColStast)
print("vendo os resultados de la normalização ", imgColNorm);
var mosaic = imgMos.filter(ee.Filter.eq('system:index', 'CAATINGA-SA-24-Y-A-1985-L5-1')).first();
var idI = mosaic.id();
var featN = featColStast.filter(ee.Filter.eq('id_img', idI));
print("feat filtered ", featN);

var mosaicNorm = imgColNorm.filter(ee.Filter.eq('system:index', 'CAATINGA-SA-24-Y-A-1985-L5-1')).first();

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