// =============================================================
// SCRIPT: Gerar grade com solape de 300m (10 pixels Landsat)
// Entrada : basegrade30KMCaatinga
// Saída   : basegrade30KMBufferCaatinga
// Rode no GEE Code Editor antes de usar o VC5
// =============================================================

var ASSET_IN  = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga';
var ASSET_OUT = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMBufferCaatinga';
var BUFFER_M  = 300; // 10 pixels Landsat 30m

var grade = ee.FeatureCollection(ASSET_IN);
print('Total de grades:', grade.size());
print('Primeira grade (props):', grade.first().propertyNames());
print('Primeira grade (valores):', grade.first().toDictionary()); // confirma o nome do campo de ID

// Aplica buffer preservando todas as propriedades originais
var gradeBuffer = grade.map(function(feat) {
  return feat.buffer(BUFFER_M);
});

// Visualização rápida para conferir
Map.centerObject(grade, 6);
Map.addLayer(grade,       {color: 'blue'},  'Grade original');
Map.addLayer(gradeBuffer, {color: 'red'},   'Grade +300m buffer');

print('Exemplo grade original:',  grade.first().geometry().area().divide(1e6).round(), 'km²');
print('Exemplo grade buffered:',  gradeBuffer.first().geometry().area().divide(1e6).round(), 'km²');
print('ID da primeira grade (indice):', grade.first().get('indice'));

// Export
Export.table.toAsset({
  collection:  gradeBuffer,
  description: 'basegrade30KMBufferCaatinga',
  assetId:     ASSET_OUT,
});
