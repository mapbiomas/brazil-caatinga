#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
import ee 
import json

ee.Initialize()

#============================================================
#========================METODOS=============================
#exporta a imagem classificada para o asset
def processoExportar(mapaRF, regionB, nameB):
    print(regionB)
    assetoutRF = 'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/ver3bacia/'  
    nomeDesc = 'RF_BACIA_'+ str(nameB)
    optExp = {'image': mapaRF, 
                 'description': nomeDesc, 
                 'assetId':assetoutRF + nomeDesc, 
                 'region':regionB, 
                 'scale': 30, 
                 'maxPixels': 1e13
             }
    ee.batch.Export.image.toAsset(**optExp).start()
    print("salvando ... !")

#map do col anos
def map_col_pontos(table):
	mylist = table.get('id').split('/')
	FeatCPtos = ee.FeatureCollection(table.get('id')).map(lambda f: f.set('id', int(mylist[len(mylist) - 1])))
	return FeatCPtos

#============================================================
    
    
bioma = "CAATINGA";

assetCaat = 'users/CartasSol/shapes/Caatinga';
assetGridCartas = 'ft:1wCmguQD-xQs2gMH3B-hdOdrwy_hZAq4XFw1rU8PN';
dirasset = 'projects/mapbiomas-workspace/MOSAICOS/workspace-c3';
assetBacia = 'users/diegocosta/baciasRecticadaCaatinga';

limiteCaatinga = ee.FeatureCollection(assetCaat);
FeatColbacia = ee.FeatureCollection(assetBacia);

#nome das bacias que fazem parte do bioma
nameBacias = ['732','741','742', '743','744', '745','746','747',
'751', '752','753', '754', '755','756', '757', '758','759', '762',
'763','765','766', '767', '773',  '771', '772', '777','774', '775','776',
'7611','7612','7613','7614','7615','7616','7617','7618','7619']

#nome das bandas 
bandNames = ee.List([
     'median_gcvi','median_gcvi_dry','median_gcvi_wet','median_gvs','median_gvs_dry','median_gvs_wet',
     'median_hallcover','median_ndfi','median_ndfi_dry','median_ndfi_wet', 'median_ndvi','median_ndvi_dry',
     'median_ndvi_wet','median_nir_dry','median_nir_wet','median_savi_dry','median_savi_wet','median_swir1',
     'median_swir2','median_swir1_dry','median_swir1_wet','median_swir2_dry', 'median_swir2_wet','median_nir',
     'median_pri','median_red','median_savi','median_evi2','min_nir','min_red','min_swir1','min_swir2', 
     'median_fns_dry','median_ndwi_dry','median_evi2_dry','median_sefi_dry','median_ndwi','median_red_dry',
     'median_wefi_wet','median_ndwi_wet'      
     ])

#opcoes de visualizacao 
visclass = {"min": 0, "max": 29,
"palette": "d5d5e5,129912,1f4423,006400,00ff00," +
   "687537,76a5af,29eee4,77a605,935132,ff9966,45c2a5," +
   "b8af4f,f1c232,ffffb2,f6b26b,f6b26b,a0d0de," +
   "e974ed,d5a6bd,c27ba0,FBF3C7,d0670f," +
   "dd7e6b,b7b7b7,ff99ff," +
   "0000ff,d5d5e5,afafaf,f76262",
"format": "png"
}

#opcoes do random forest 
pmtRF = {'numberOfTrees': 60, 'variablesPerSplit': 6}

primeiroAno = 1985;

#lista de anos
anos =['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994','1995','1996',
  '1997','1998','1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
  '2011','2012','2013','2014','2015','2016','2017', '2018']

#pasta contendo as bacias
foldersROI = {'id':'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/PtosBacias2_1000'}

getlistPtos = ee.data.getList(foldersROI)
ColectionPtos = map(lambda t: map_col_pontos(t), getlistPtos)
ROIs = ee.FeatureCollection(ColectionPtos).flatten();
mosaicoTotal = ee.ImageCollection(dirasset)
nameBacias = ['752']
for _nbacia in nameBacias:
    #pega o poligono da bacia
    PoligonoBacia = FeatColbacia.filterMetadata('nunivotto3', 'equals', _nbacia);
    print('classificando bacia '+_nbacia)
    #adiciona um buffer de 25km ao poligono da bacia 
    PoligonoBaciaB = PoligonoBacia.geometry().buffer(25000);
    #pega os dados de treinamento utilizando a geometria da bacia com buffer
    training = ROIs.filterBounds(PoligonoBaciaB);
    
    imglsClasxanos = None
    mydict = None
    primerAno = anos[0]
    
    i = 1
    for ano in anos:
        #se o ano for 2018 utilizamos os dados de 2017 para fazer a classificacao
        if ano == anos[-1]:
            temptraining = training.filterMetadata('year', 'equals', int(ano) - 1)
        else:
            #pega os dados do ano em questao
            temptraining = training.filterMetadata('year', 'equals', int(ano))
            #cria o mosaico a partir do mosaico total, cortando pelo poligono da bacia
            mosaicMapbiomas = ee.Image(mosaicoTotal.filterMetadata('year', 'equals', int(ano)).filterBounds(PoligonoBacia).mosaic()).clip(PoligonoBacia)
            #cria o classificador com as especificacoes definidas acima 
            classifier = ee.Classifier.randomForest(**pmtRF).train(temptraining, 'class', bandNames)
            #para que na imagem classificada e agrupada cada banda corresponda a um ano
            #criamos essa variavel e passamos ela na classificacao
            resl = 'classification_'+ano
            
            #classifica
            classified = mosaicMapbiomas.classify(classifier, resl)
            #verifica se o ano em questao eh o primeiro ano 
            condition = ee.Algorithms.IsEqual(ano, primerAno)
            
            #se for o primeiro ano cria o dicionario e seta a variavel como
            #o resultado da primeira imagem classificada
            if condition.getInfo() == True:
                print ('entrou em 1985')
                imglsClasxanos = classified
                mydict = {'id_bacia': _nbacia,'version': '2','biome': bioma,'collection': '4','sensor': 'Landsat','ver':2}
            #se nao, adiciona a imagem como uma banda a imagem que ja existia
            else:
                imglsClasxanos = imglsClasxanos.addBands(classified)
    i+=1
    #seta as propriedades na imagem classificada            
    for pmt in mydict:
        imglsClasxanos = imglsClasxanos.set(pmt, mydict[pmt])
        imglsClasxanos = imglsClasxanos.set("system:footprint", PoligonoBacia.geometry())
    
    nomec = _nbacia + '_' + 'RF-v2_bacia';
    #exporta bacia
    processoExportar(imglsClasxanos, PoligonoBacia.geometry().coordinates().getInfo(), nomec);        
                 
            
            
    
    
    


