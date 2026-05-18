// https://code.earthengine.google.com/abbb80457608d57df2cb94c699b7ed1b
// https://code.earthengine.google.com/f6a9c9b1bf7e1c4548142418edae75cb  // remocao de nuvens 

function maskL8sr(image) {
  // Bits 3 and 5 are cloud shadow and cloud, respectively.
  var cloudShadowBitMask = (1 << 3);
  var cloudsBitMask = (1 << 5);
  // Get the pixel QA band.
  var qa = image.select('pixel_qa');
  // Both flags should be set to zero, indicating clear conditions.
  var mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
                 .and(qa.bitwiseAnd(cloudsBitMask).eq(0));
  return image.updateMask(mask);
}

function getFC(image_, bnd, geom){
    
    var maxBuckets = 16384; // equivale a 2^13  16384
    var optRed = {
                'reducer': ee.Reducer.histogram({'maxBuckets': maxBuckets}), // 
                'geometry': geom,
                'scale': 30,
                'maxPixels': 1e13,
                'tileScale': 4
                };
    
    var histo = image_.reduceRegion(optRed);
    var valsList = ee.List(ee.Dictionary(histo.get(bnd)).get('bucketMeans')); 
    // print(valsList)
    // calculate histogram 
    var freqsList = ee.List(ee.Dictionary(histo.get(bnd)).get('histogram'));
    // print("frequence List ", ee.Array(freqsList))
    
    var cdfArray = ee.Array(freqsList).accum(0);
    // print(" array accum ", cdfArray)
    var total = cdfArray.get([-1]);
    // print("total ", total)
    // calculate cdf of the histogram
    var normalizedCdf = cdfArray.divide(total);
    // print("lista de probabilidades do CDF ", normalizedCdf)
    // mapping, transformation function T(x)
    normalizedCdf = normalizedCdf.multiply(maxBuckets);
    // print("normalizedCdf  List ", normalizedCdf)
    var listONE = freqsList.map(function(element){return 1});

    var lists = ee.List([listONE, valsList, normalizedCdf.toList()]);
    print("analisando a lista ",lists);
    
    var coef =  lists.reduce(ee.Reducer.linearRegression(2, 1))
    print("coeficientes  == ", coef)
    // var  expLists = lists.reduce(ee.Reducer.toCollection(['dn', 'probability']))
    var coefCalc =  ee.Array(ee.Dictionary(coef).get('coefficients'))

    return ee.Image(image_).multiply(coefCalc.get([1, 0])).add(coefCalc.get([0, 0]))
}

function getFC_lineal(image_, bnd, geom){
    
    var maxBuckets = 8000; // equivale a 2^13  16384
    var optRed = {
                'reducer': ee.Reducer.histogram({'maxBuckets': maxBuckets}), // 
                'geometry': geom,
                'scale': 30,
                'maxPixels': 1e13,
                'tileScale': 4
                };
    
    var histo = image_.reduceRegion(optRed);
    var valsList = ee.List(ee.Dictionary(histo.get(bnd)).get('bucketMeans')); 
    print(" Lsit of values bucket ", valsList)
    // calculate histogram 
    var freqsList = ee.List(ee.Dictionary(histo.get(bnd)).get('histogram'));
    print("frequence List ", ee.Array(freqsList))
    
    var X0 = ee.Array(valsList).get([0])
    print("valores de X ")
    var X1 = ee.Array(valsList).get([-1])
    print(X0, X1)
    
    var coef_m =  ee.Number(maxBuckets).divide(ee.Number(X1).subtract(X0))

    return ee.Image(image_).subtract(X0).multiply(coef_m)
}

// Intercalibration
function intercalibrate(image, reference,  bands){
  
  image = image.select(bands);
  reference = reference.select(bands);
  
  var bandsMean = bands.map(function(band){return ee.String(band).cat("_mean")});
  var bandsStdev = bands.map(function(band){return ee.String(band).cat("_stdDev")});
  
  var imageROI = image.geometry();
  
  var reduceMean = function(img, mask, scale) {
    return img
      .updateMask(mask)
      .reduceRegion({
        reducer: ee.Reducer.mean().combine(ee.Reducer.stdDev(), null, true),
        geometry: imageROI, 
        scale: scale,
        maxPixels: 1E13,
        bestEffort: true, 
        tileScale: 4
      });
  };
  
  var mask = imageMask.eq(1).and(referenceMask.eq(1));
  
  var imageStats = reduceMean(image, mask, imageScale);
  var referenceStats = reduceMean(reference, mask, referenceScale);

  var image_means = ee.Image.constant(imageStats.values(bandsMean));
  var image_stdDev = ee.Image.constant(imageStats.values(bandsStdev));
  
  var reference_means = ee.Image.constant(referenceStats.values(bandsMean));
  var reference_stdDev = ee.Image.constant(referenceStats.values(bandsStdev));
  
  var a = reference_stdDev.divide(image_stdDev);
  var b = reference_means.subtract(a.multiply(image_means));
  
  if(debug){
    print(ee.Dictionary({"gain": a, "bias": b}));
  }

  var inter = image.multiply(a).add(b).clip(imageROI);
  
  return ee.Image(inter.copyProperties(image, image.propertyNames()));
}

var bands = ['B2','B3','B4','B5','B10','B11','pixel_qa']

// var path =  'LANDSAT/LC08/C01/T1_SR'
// var imgC = ee.ImageCollection(path).filterDate('2020-01-01', '2020-12-31')
//                                     .filterBounds(limitCaat)
//                                     .filterBounds(point)
//                                     .sort('CLOUD_COVER_LAND')
                                    
// print("lista de imagerns filtradas ", imgC)

// var pathimA = 'LANDSAT/LC08/C01/T1_SR/LC08_216065_20201017'
// var imgA = ee.Image(pathimA).select(bands);
// imgA = maskL8sr(imgA);
// print(imgA)

var pathimB = 'LANDSAT/LC08/C01/T1_SR/LC08_218068_20200117'
var imgB = ee.Image(pathimB).select(bands);
imgB = maskL8sr(imgB);

var bandAnalise = ['B2','B3','B4'];  //,'B5'
var cc = 0;
var matching = null;
bandAnalise.forEach(function(bandss){
    print(ee.String("BANDAS = ").cat(bandss));
    var imgTemp = getFC(imgB.select(bandss), bandss, imgB.geometry());
    
    imgTemp = imgTemp.toUint16().rename(bandss);
    print("imagem temporal ", imgTemp)
     if (cc === 0){
          matching = imgTemp
     }else{
          matching = matching.addBands(imgTemp)            
     }
     cc += 1;
})
// matching = matching.select(bandAnalise)
print("feat histogram ", matching)

// var bandAnalise = ['B2','B3','B4','B5'];

// Define the chart and print it to the console.
var chartB =
    ui.Chart.image.histogram({image: imgB.select(bandAnalise), region: imgB.geometry(), scale: 300})
        .setSeriesNames(bandAnalise)
        .setOptions({
          title: 'IMAGE B Reflectance Histogram',
          hAxis: {
            title: 'Reflectance (x1e4)',
            titleTextStyle: {italic: false, bold: true},
          },
          vAxis:
              {title: 'Count', titleTextStyle: {italic: false, bold: true}},
          colors: ['cf513e', '1d6b99', 'f0af07']
        });
print("imagem B", chartB);

// Define the chart and print it to the console.
var chartMat =
    ui.Chart.image.histogram({image: matching.select(bandAnalise), region: imgB.geometry(), scale: 300})
        .setSeriesNames(bandAnalise)
        .setOptions({
          title: 'IMAGE B Reflectance Histogram',
          hAxis: {
            title: 'Reflectance (x1e4)',
            titleTextStyle: {italic: false, bold: true},
          },
          vAxis:
              {title: 'Count', titleTextStyle: {italic: false, bold: true}},
          colors: ['cf513e', '1d6b99', 'f0af07']
        });
print("imagem chartMat", chartMat);

// Map.addLayer(imgA,  {min: 20, max: 3500, bands: ['B4','B3','B2']}, "imgA")
Map.addLayer(imgB,  {min: 0, max: 3500, bands: ['B4','B3','B2']}, "imgBr5")
Map.addLayer(matching,  {min: 0, max: 3500, bands: ['B4','B3','B2']}, "img Equal")


