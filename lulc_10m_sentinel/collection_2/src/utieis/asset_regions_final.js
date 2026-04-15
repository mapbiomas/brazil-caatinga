var asset_buffer = 'projects/ee-solkancengine17/assets/shape/bacias_hidrografica_caatinga_49_regions'
var asset_reg = 'projects/ee-solkancengine17/assets/shape/bacias_caatinga_div_49_regions';
var featShpBuffer = ee.FeatureCollection(asset_buffer);
var featShpreg = ee.FeatureCollection(asset_reg);
print("regiões com buffers ", featShpBuffer);
print("divisões 49 regiões  Caatinga ", featShpreg);

Map.addLayer(featShpreg, {}, 'bacias');
Map.addLayer(featShpBuffer, {color: 'yellow'}, 'bacias buffer');

