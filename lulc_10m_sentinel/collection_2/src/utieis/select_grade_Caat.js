
//exporta a imagem classificada para o asset
function processoExportar(areaFeat, nameT, asset_expo){      
    var optExp = {
          'collection': ee.FeatureCollection(areaFeat), 
          'description': nameT, 
          'assetId': asset_expo + "/" + nameT     
        };    
    Export.table.toAsset(optExp) ;
    print(" salvando ... " + nameT + "..!")      ;
}
var asset_gradeGeral = 'projects/nexgenmap/SAD_MapBiomas/DL/SHP_grades_BR_35pathces_AllBrV3';
var featGradesBr = ee.FeatureCollection(asset_gradeGeral);

var asset_OutputshpGrade = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA';
var nameExp = 'basegrade30KMCaatinga'

print("know size of feature Collection ",featGradesBr.size())



var asset_cruzN245 = 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga_49_regions';
var featReg = ee.FeatureCollection(asset_cruzN245);

var newgrade = featGradesBr.filterBounds(featReg)
print("as que faltam ", newgrade.size())

Map.addLayer(featReg, {color: 'red'}, 'regions');
Map.addLayer(featGradesBr, {color: 'green'}, 'grade')
Map.addLayer(newgrade, {color: 'yellow'}, 'region');
processoExportar(newgrade, nameExp, asset_OutputshpGrade);