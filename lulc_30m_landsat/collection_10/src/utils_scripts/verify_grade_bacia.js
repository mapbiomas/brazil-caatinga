
// se pode verifica diretamente aqui 
//# https://code.earthengine.google.com/02cf5ba3b0731d51f0b6246472614c7b
var asset_bacias = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions'
var shp_bacias = ee.FeatureCollection(asset_bacias)
var asset_grid = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga'
var shp_grid = ee.FeatureCollection(asset_grid)

// var bacia_select = '7691'
// var lstGrades = [6218, 6219, 6220, 6221, 6222, 6010, 6325, 6326, 6327, 6114, 6115, 6116, 6117]

// var bacia_select = '7411'
// var lstGrades = [ 
//     2328, 2329, 2431, 2432, 2433, 2434, 2223, 2224, 2852, 2853, 2854, 2855, 2856, 
//     2641, 2642, 2643, 2644, 2645, 2646, 2958, 2959, 2960, 2746, 2747, 2748, 2749, 
//     2750, 2751, 2536, 2537, 2538, 2539, 2540
// ]

// var bacia_select = '7754'
// var lstGrades = [
//     5155, 5156, 5157, 5158, 5159, 5160, 5261, 5262, 5263, 5264, 5265, 5052, 5053, 
//     5054, 5368]


var bacia_select = '763'
var lstGrades = [4641, 4642, 4643, 4954, 4955, 4956, 4957, 4958, 4959, 4745, 4746, 4747, 4748, 4749, 4849, 4850, 4851, 4852, 4853, 4854, 5376, 5163, 5164, 5165, 5166, 5167, 5168, 5169, 5170, 5480, 5268, 5269, 5270, 5271, 5272, 5273, 5058, 5059, 5060, 5061, 5062, 5063, 5064, 5065, 5374, 5375]

lstGrades.forEach(function(idCod){
    var featGrade = shp_grid.filter(ee.Filter.eq('indice', parseInt(idCod)));
    Map.addLayer(featGrade, {}, ''+idCod);
})

Map.addLayer(shp_bacias.filter(ee.Filter.eq('nunivotto4', bacia_select)), {}, bacia_select)
