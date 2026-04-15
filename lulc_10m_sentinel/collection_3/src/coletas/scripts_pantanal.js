var asset_regioes = 'projects/mapbiomas-workspace/AUXILIAR/PANTANAL/regioes_pantanal';
var regioesCollection = ee.FeatureCollection(asset_regioes);
print("regiões de pantanal ", regioesCollection);
Map.addLayer(regioesCollection, {color: '#D2DE2CFF'},'regioes Pant');

// Define the output version
var versao_out = '2';

// Define the version of the points
var versao_pt = '2';

// Define the year
var ano = 2024;

// Define the output directory
var dirout = 'projects/mapbiomas-workspace/AMOSTRAS/S2_EMBEDDING/PANTANAL/SAMPLES/';

// Import the palettes module
var palettes = require('users/mapbiomas/modules:Palettes.js');
// Define the color palette for NDVI amplitude
var ndvi_color = [
        '#0f330f', '#005000', '#4B9300', '#92df42', 
        '#bff0bf', '#FFFFFF', '#eee4c7', '#ecb168', 
        '#f90000'
];
var vis = {
    mapbiomas_L:  {// Define the visualization parameters
        'min': 0,
        'max': 62,
        'palette': palettes.get('classification8')
    },
    mapbiomas_S: { // Define the visualization parameters
        'min': 0,
        'max': 34,
        'palette': palettes.get('classification2')
    },
    embedding: {
      // bands: ["A00","A01","A02"],
      // bands: ['A01', 'A16', 'A09']
      bands: ['A01', 'A25', 'A50'],
      max: 0.21413302575932336,
      min: -0.2364628988850442
    },
    NDFI_amp: {
        'min':0, 
        'max':300, 
        'palette': ndvi_color
    }
  
}

function export_rois(featCol, name_exp){
    var id_asset = dirout + name_exp;
    var pmtro = {
        collection: featCol,
        description: name_exp,
        assetId: id_asset
    };
     Export.table.toAsset(pmtro);
     print("exporting samples ... " + name_exp);

}

// Add the regions collection to the map
// Map.addLayer(regioesCollection);
//Map.addLayer(bioma250mil_MA,{},"biome MA",false)

// Define the asset path for the mosaics
//var asset_mosaicosS2 = 'projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3';

// Define the biome
var bioma = "PANTANAL";
// lista de anos para coleta 
var lista_anos = [ 2017,2018,2019,2020,2021, 2022,2023,2024];
// Define the list of regions
var regioes_lista = [ 'reg1','reg2','reg3','reg4','reg5','reg6','reg0'];
var asset_emb = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL";
// Load the stable samples
var asset_rois = 'projects/mapbiomas-workspace/AMOSTRAS/S2_EMBEDDING/PANTANAL/SAMPLES/samples_stable_v1_S2';
// Load the S2 clusters image
//var S2_cluster = ee.Image('projects/mapbiomas-workspace/AMOSTRAS/S2_2024/MATA_ATLANTICA/mosaicos_MA_S2_clusters_2106_2023')


// Import the function to add indices for the Caatinga biome
//var addIndexCaatinga = require('users/marcosrosaUSP/MapBiomas_col9_MataAtlan:Mata_Atlantica_SENTINEL2/processa_Bandas_Sentinel2_CAATINGA');

lista_anos.forEach(function(ano){
    // Get the current year. 
    var date_inic = ee.Date.fromYMD(ano, 1, 1);
    var training_reg = ee.FeatureCollection([]);
    //mosaico embedding da S2        
    var mosaico_annual = ee.ImageCollection(asset_emb)
                                .filterBounds(regioesCollection)
                                .filterDate(date_inic, date_inic.advance(1, 'year'))
                                .median();

    // Loop over the list of regions
    regioes_lista.forEach(function(regiao){
        // Get the current region information
        print("processing region " + regiao + "in ano " + String(ano)); 
        // Filter the regions collection to get the current region
        var limite_reg = regioesCollection.filterMetadata('id_reg', "equals", regiao);  
        // Filter the stable samples for the current region      
        var pts_reg = ee.FeatureCollection(asset_rois)
                        .filterMetadata('id_reg', 'equals', regiao);   
        print('we load size roins ', pts_reg.size());

        // Sample the mosaic image using the stable samples for the current region
        var training = mosaico_annual.sampleRegions({
            'collection': pts_reg,
            'scale': 10,
            // 'tileScale': 4,// essa escala 4 pode estar atrapalhando a coleta 
            'geometries': true
        });
        training = training.map(function(feat){return feat.set('year', ano, 'region', regiao)});    
        //print('amostras treinadas',training.limit(1));   
         
        // Otherwise, merge the current region's sample into the existing collection
        training_reg = training_reg.merge(training);       
    })    
    
    Map.addLayer(mosaico_annual, vis.embedding, 'Sentinel 2  Emb ' + ano, false);
    // Export the training sample collection to an asset
    var name_exportar = 'pontos_trained_emb_S2_v'+versao_out+'_'+ano;
    export_rois(training_reg, name_exportar);
});
// ====================================================///
//// samples estaveis entre   coleções                 ///
// ===================================================///
print("//=====================================//");
print("=== coletando amostras estaveis ======");
// Define seed values (list or current).
var lista_seeds = [1];
var seed = 1;
var id_asset_samples = 'projects/mapbiomas-workspace/AMOSTRAS/S2_EMBEDDING/PANTANAL/SAMPLES/samples_stable8910_reg_v1_';
// Loop through each year.
lista_anos.forEach(function(ano){
    // Get the current year. 
    var date_inic = ee.Date.fromYMD(ano, 1, 1);
    // Add the cluster, NDFI amplitude, green texture, NDFI median, longitude, latitude, and year bands to the mosaic.
    //mosaico embedding da S2
    var mosaicoTotal = ee.ImageCollection(asset_emb)
                                .filterBounds(regioesCollection)
                                .filterDate(date_inic, date_inic.advance(1, 'year'))
                                .median();

    var pts_reg1 = ee.FeatureCollection(id_asset_samples + ano);
    if (ano >= 2023) {
        pts_reg1 = ee.FeatureCollection(id_asset_samples + '2022');
    }
     // Filter the training points within the current region.
      var pts_reg = pts_reg1;
    // Sample the mosaic image using the points in the current region to create training data.
     var allTraining = ee.FeatureCollection([]); // Initialize outside the loops
      // Loop over the list of regions
    regioes_lista.forEach(function(regiao){
        // Get the current region information
        print("processing region " + regiao + " in ano " + String(ano)); 
        var limite = regioesCollection.filter(ee.Filter.eq('id_reg', regiao));
        var pts_reg_filtered = pts_reg.filter(ee.Filter.eq('id_reg', regiao));

        var training = mosaicoTotal.sampleRegions({
                            'collection': pts_reg_filtered,
                            'scale': 10, // Resolution of the sampling.
                            // 'tileScale': 4, // Improves performance for large regions.
                            'geometries': true // Include geometries in the output.
                        });
        training = training.map(function(feat){return feat.set('year', ano, 'region', regiao)});
        //   Map.addLayer(training);
        allTraining = allTraining.merge(training); // Accumulate training samples
    });

    var name_exportar = 'pts_trained_stable8910_v'+versao_out+'_'+ano+'_seed_'+seed;
    export_rois(allTraining, name_exportar); 

});
    
