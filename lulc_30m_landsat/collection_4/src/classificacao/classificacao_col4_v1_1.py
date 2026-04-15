import ee
ee.Initialize()

def rescale(img, exp, thresholds):
    return img.expression(exp, {img: img}).subtract(thresholds[0]).divide(thresholds[1] - thresholds[0])

def cloudScore(img):
    score = ee.Image(1.0)
    score = score.min(rescale(img, 'img.blue', [0.1, 0.3]))
    score = score.min(rescale(img, 'img.red + img.green + img.blue', [0.2, 0.8]))
  
    score = score.min(rescale(img, 'img.nir + img.swir1 + img.swir2', [0.3, 0.8]))
    score = score.min(rescale(img, 'img.temp', [300, 290]));
    ndsi = img.normalizedDifference(['green', 'swir1'])
    return score.min(rescale(ndsi, 'img', [0.8, 0.6]))

def processoExportar(mapaRF, nameB, ano, regionB):  #
    assetoutRF = 'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/ver1/'  
    mapaRF = mapaRF.set('biome', 'CAATINGA')
    mapaRF = mapaRF.set('id_bacia', nameB)
    mapaRF = mapaRF.set('year', ano)
    nomeDesc = nameB + '_' + str(ano) + '_RF_v1'
    #optExp = {'image': mapaRF, 
    #    'description': nomeDesc, 
    #    'assetId':assetoutRF + nomeDesc, 
    #    'pyramidingPolicy': {'.default': 'mode'},
    #    'region': regionB.getInfo()['coordinates'], 
    #    'scale': 30, 
    #    'maxPixels': 1e13}
    #gride.getInfo()['coordinates']
    #ee.batch.Export.image.toAsset(**optExp)
    task = ee.batch.Export.image.toAsset(image= mapaRF, description= nomeDesc, assetId=assetoutRF + nomeDesc, 
               scale= 30, maxPixels= 1e13)
    task.start()
    
    print('enviando task de descricao %s ' %(nomeDesc))

def func_bacias(namB, training, ano):
    baciaTemp = ee.Feature(baciasB.filterMetadata('ID_NIVEL2', 'equals', namB).first())      
    ptosXbacia = training.filterBounds(baciaTemp)
    classifier = ee.Classifier.randomForest(pmtRF).train(ptosXbacia, 'class', bandNames);
    mosaicTemp = mosaicoTotal.filterMetadata('year', 'equals', ano).filterBounds(baciaTemp).mosaic()
    mosaicTemp = ee.Image(mosaicTemp).clip(baciaTemp)
    resl = 'RF_'+ namB + '_' + ano
    classified = mosaicTemp.classify(classifier, resl)
    print(classified.getInfo())
    processoExportar(classified, namB, ano, baciaTemp.geometry())
    
def evaluate_bacias(lsBacias, training, ano):
    #lsImcRFxBacia = ee.List([])
    lsBacias.forEach(lambda namB: func_bacias(namB, training, ano))
    
def func_anos(ano):
    training = ROIg.filterMetadata('ano', 'equals', ano);
    ee.List(nameBacias).evaluate(lambda bacias: evaluate_bacias(bacias, training, ano))
     
def evaluate(variosAnos, item):
    print(variosAnos.getInfo())
    variosAnos.forEach(lambda ano: func_anos(ano))

dictBandas = ['amp_evi2','amp_gv','amp_ndfi','amp_ndvi','amp_ndwi','amp_npv','amp_sefi','amp_soil'
        ,'amp_wefi','ano','carta','class','median_blue','median_blue_dry','median_blue_wet'
        ,'median_cai','median_cai_dry','median_cai_wet','median_cloud','median_evi2'
        ,'median_evi2_dry','median_evi2_wet','median_fns','median_fns_dry','median_fns_wet'
        ,'median_gcvi','median_gcvi_dry','median_gcvi_wet','median_green','median_green_dry'
        ,'median_green_wet','median_gv','median_gvs','median_gvs_dry','median_gvs_wet','median_hallcover'
        ,'median_ndfi','median_ndfi_dry','median_ndfi_wet','median_ndvi','median_ndvi_dry','median_ndvi_wet'
        ,'median_ndwi','median_ndwi_dry','median_ndwi_wet','median_nir','median_nir_dry','median_nir_wet'
        ,'median_npv','median_pri','median_pri_dry','median_pri_wet','median_red','median_red_dry'
        ,'median_red_wet','median_savi','median_savi_dry','median_savi_wet','median_sefi'
        ,'median_sefi_dry','median_sefi_wet','median_shade','median_soil','median_swir1'
        ,'median_swir1_dry','median_swir1_wet','median_swir2','median_swir2_dry','median_swir2_wet'
        ,'median_temp','median_wefi','median_wefi_dry','median_wefi_wet','min_blue','min_green'
        ,'min_nir','min_red','min_swir1','min_swir2','min_temp','stdDev_blue','stdDev_cai','stdDev_cloud'
        ,'stdDev_evi2','stdDev_fns','stdDev_gcvi','stdDev_green','stdDev_gv','stdDev_gvs'
        ,'stdDev_hallcover','stdDev_ndfi','stdDev_ndvi','stdDev_ndwi','stdDev_nir','stdDev_npv','stdDev_pri'
        ,'stdDev_red','stdDev_savi','stdDev_sefi','stdDev_shade','stdDev_soil','stdDev_swir1'
        ,'stdDev_swir2','stdDev_temp','stdDev_wefi']

    
dictPtos = ['amp_ev2','amp_gv','amp_ndf','amp_ndv','amp_ndw','amp_npv','amp_sef','amp_sol','amp_wef'
        ,'ano','carta','class','mdn_bl_d','mdn_bl_w','mdn_c_d','mdn_c_w','mdn_cld','mdn_fns'
        ,'mdn_fns_d','mdn_fns_w','mdn_gcv','mdn_gcv_d','mdn_gcv_w','mdn_grn','mdn_grn_d','mdn_grn_w'
        ,'mdn_gvs','mdn_gvs_d','mdn_gvs_w','mdn_hll','mdn_ndf','mdn_ndf_d','mdn_ndf_w','mdn_ndv'
        ,'mdn_ndv_d','mdn_ndv_w','mdn_ndw','mdn_ndw_d','mdn_ndw_w','mdn_npv','mdn_nr_d'
        ,'mdn_nr_w','mdn_pr_d','mdn_pr_w','mdn_rd_d','mdn_rd_w','mdn_sf_d','mdn_sf_w','mdn_shd'
        ,'mdn_sv_d','mdn_sv_w','mdn_sw1','mdn_sw2','mdn_swr1_d','mdn_swr1_w','mdn_swr2_d'
        ,'mdn_swr2_w','mdn_tmp','mdn_v2_d','mdn_v2_w','mdn_wf_d','mdn_wf_w','medin_c','medn_bl'
        ,'medn_gv','medn_nr','medn_pr','medn_rd','medn_sf','medn_sl','medn_sv','medn_v2','medn_wf'
        ,'min_blu','min_grn','min_nir','min_red','min_tmp','mn_swr1','mn_swr2','stdDev_c'
        ,'stdDev_gv','stdDv_1','stdDv_b','stdDv_cl','stdDv_f','stdDv_gc','stdDv_gr','stdDv_gvs'
        ,'stdDv_h','stdDv_ndf','stdDv_ndv','stdDv_ndw','stdDv_np','stdDv_nr','stdDv_p'
        ,'stdDv_r','stdDv_s2','stdDv_sf','stdDv_sh','stdDv_sl','stdDv_sv','stdDv_t','stdDv_v2','stdDv_w']



    
LC8_BANDS = ['B2',   'B3',    'B4',  'B5',  'B6',    'B7',    'B10']
STD_NAMES = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'temp']


bioma = "CAATINGA"
anos = [2017]

ndfi_color = 'FFFFFF,FFFCFF,FFF9FF,FFF7FF,FFF4FF,FFF2FF,FFEFFF,FFECFF,FFEAFF,FFE7FF,FFE5FF,FFE2FF,FFE0FF,FFDDFF,FFDAFF,FFD8FF,FFD5FF,FFD3FF,FFD0FF,FFCEFF,'+'FFCBFF,FFC8FF,FFC6FF,FFC3FF,FFC1FF,FFBEFF,FFBCFF,FFB9FF,FFB6FF,FFB4FF,FFB1FF,FFAFFF,FFACFF,FFAAFF,FFA7FF,FFA4FF,FFA2FF,FF9FFF,FF9DFF,FF9AFF,'+'FF97FF,FF95FF,FF92FF,FF90FF,FF8DFF,FF8BFF,FF88FF,FF85FF,FF83FF,FF80FF,FF7EFF,FF7BFF,FF79FF,FF76FF,FF73FF,FF71FF,FF6EFF,FF6CFF,FF69FF,FF67FF,'+'FF64FF,FF61FF,FF5FFF,FF5CFF,FF5AFF,FF57FF,FF55FF,FF52FF,FF4FFF,FF4DFF,FF4AFF,FF48FF,FF45FF,FF42FF,FF40FF,FF3DFF,FF3BFF,FF38FF,FF36FF,FF33FF,'+'FF30FF,FF2EFF,FF2BFF,FF29FF,FF26FF,FF24FF,FF21FF,FF1EFF,FF1CFF,FF19FF,FF17FF,FF14FF,FF12FF,FF0FFF,FF0CFF,FF0AFF,FF07FF,FF05FF,FF02FF,FF00FF,'+'FF00FF,FF0AF4,FF15E9,FF1FDF,FF2AD4,FF35C9,FF3FBF,FF4AB4,FF55AA,FF5F9F,FF6A94,FF748A,FF7F7F,FF8A74,FF946A,FF9F5F,FFAA55,FFB44A,FFBF3F,FFC935,'+'FFD42A,FFDF1F,FFE915,FFF40A,FFFF00,FFFF00,FFFB00,FFF700,FFF300,FFF000,FFEC00,FFE800,FFE400,FFE100,FFDD00,FFD900,FFD500,FFD200,FFCE00,FFCA00,'+'FFC600,FFC300,FFBF00,FFBB00,FFB700,FFB400,FFB000,FFAC00,FFA800,FFA500,FFA500,F7A400,F0A300,E8A200,E1A200,D9A100,D2A000,CA9F00,C39F00,BB9E00,'+'B49D00,AC9C00,A59C00,9D9B00,969A00,8E9900,879900,7F9800,789700,709700,699600,619500,5A9400,529400,4B9300,439200,349100,2D9000,258F00,1E8E00,'+'168E00,0F8D00,078C00,008C00,008C00,008700,008300,007F00,007A00,007600,007200,006E00,006900,006500,006100,005C00,005800,005400,005000,004C00'
visNDFI = {'min':0, 'max':200, 'palette':ndfi_color}
visNDFI100 = {'min':0, 'max':100, 'palette':ndfi_color}


visNDFI = {'min':0, 'max':200, 'palette':ndfi_color}
visNDFI100 = {'min':0, 'max':100, 'palette':ndfi_color}

dirasset = 'projects/mapbiomas-workspace/MOSAICOS/workspace-c3'
dirout = 'projects/mapbiomas-workspace/AMOSTRAS/Caatinga_v18_85a17/'
dirout = 'users/diegocosta/col4_final/PEJanela5_Classe'

assetBacia = 'users/CartasSol/shapes/baciasN2CaatingaB25000'

baciasB = ee.FeatureCollection(assetBacia)


square = ee.Kernel.square(radius= 5);

ROIg = ee.FeatureCollection(dirout)

ROIg = ROIg.select(ee.List(dictPtos), ee.List(dictBandas))


gridFeatureCollection = ee.FeatureCollection('ft:1wCmguQD-xQs2gMH3B-hdOdrwy_hZAq4XFw1rU8PN').filterBounds(baciasB)
                                
nameCartas = gridFeatureCollection.reduceColumns(ee.Reducer.toList(), ['name']).get('list');                           
bandNames = ee.List([
            "amp_evi2","amp_ndfi", "amp_ndvi","amp_ndwi", "median_fns","median_fns_dry","median_ndwi","median_nir",
            "amp_soil", "median_cai_dry", "median_cai_wet", "median_evi2","median_evi2_dry", "median_evi2_wet", 
            "median_fns_wet","median_gcvi","median_gv","median_gvs", "median_hallcover", "median_ndfi", "median_ndvi",
            "median_pri","median_pri_dry","median_pri_wet", "median_savi", "median_shade","median_soil","median_swir1",  
            "median_wefi_dry","median_wefi_wet", "min_nir","min_swir1","min_swir2", "stdDev_fns","stdDev_sefi",
            "stdDev_gcvi", "stdDev_gv", "stdDev_gvs","stdDev_ndfi", "stdDev_ndvi", "stdDev_ndwi", "stdDev_soil"
        ]);
  


visParMedian = {'bands':['m_swir1','m_nir','m_red'], 'gain':[0.08, 0.06,0.2],'gamma':0.5 }
collection = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT_TOA')
vizParams = { 'bands': ['B4', 'B3', 'B2'], max: 0.4, 'gamma': 1.6};
mosaicoTotal = ee.ImageCollection(dirasset)
pmtRF = {'numberOfTrees': 500, 'variablesPerSplit': 30, 'minLeafPopulation':1, 'outOfBagMode': True}

optMosaci = {
    'gamma': 1,
    'max': 1960.08,
    'min': 475.92,
    'opacity': 1,
    'bands':["median_red","median_gre","median_blu"]
}
nameBacias = baciasB.reduceColumns(ee.Reducer.toList(), ['ID_NIVEL2']).get('list')

nameBacias = nameBacias.getInfo()
nameBacias = [270]
lista_aux = ee.List(anos)
#lista_aux.iterate(lambda anos, item: evaluate(anos, item))

for namB in nameBacias:
    baciaTemp = ee.Feature(baciasB.filterMetadata('ID_NIVEL2', 'equals', namB).first()).geometry()
    cartasBacias = gridFeatureCollection.filterBounds(baciaTemp)
    baciaTemp = baciaTemp.getInfo()
    cartasTemp = cartasBacias.reduceColumns(ee.Reducer.toList(), ['name']).get('list').getInfo()    
    #===iterando por anos ===========
    for ano in anos:
        print('treinando ano %s da bacia %s' % (str(ano), namB))
        training = ROIg.filterMetadata('ano', 'equals', ano);
        ptosXbacia = training.filterBounds(baciaTemp)
        classifier = ee.Classifier.randomForest(numberOfTrees= 300, variablesPerSplit= 30, minLeafPopulation=1, outOfBagMode= True).train(ptosXbacia, 'class', bandNames);
        for tempCart in cartasTemp:
            print 'carta: ', tempCart
            geoCarta = ee.Feature(gridFeatureCollection.filterMetadata('name', 'equals', tempCart).first()).geometry()
            mosaicTemp = ee.Image(mosaicoTotal.filterMetadata('year', 'equals', ano).filterMetadata('grid_name', 'equals', tempCart).first())
            resl = tempCart + '_' + str(ano) + '_RF_v1'
            classified = mosaicTemp.classify(classifier, resl)
            processoExportar(classified, tempCart, ano, geoCarta)
            #processoExportar(classified, tempCart, ano, geoCarta)
            # try:
            #     baciaJSON = baciaTemp['coordinates'][0]
            #     print("lista de coordenadas", len(baciaJSON))
            #     processoExportar(classified, tempCart, ano, baciaJSON)
            # except:
            #     baciaJSON = baciaTemp['geometries']
            #     print(baciaJSON[0])
            #     processoExportar(classified, namB, ano, baciaJSON)
        
        
    
    
    
    
    