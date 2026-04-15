import ee
import os 
import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise






options = {
        # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/Gap-fill',
        # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/POS-CLASS/merger',
        'input_asset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/joined',
        'output_asset': 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/TemporalCC',
        'inputAsset10': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
        'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_ROIs': 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col4_points_w_edge_and_edited_v1',
        'asset_gedi': 'users/potapovpeter/GEDI_V27',
        'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 3, 12, 12, 12, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21, 21,  4, 12, 21],
        'version_input': 5,
        'version_output': 5,
        'date_inic': 2016,
        'date_end': 2025
        
    }
naturais = [3, 4, 12]
antropicas = [21, 22, 29]
anos = list(range(2016, 2026, 2))
limiares = [0.2, 0.4, 0.6, 0.8]

classeDictNaturais = {
    'FORMAÇÃO FLORESTAL': 3,
    'FORMAÇÃO SAVÂNICA': 4,
    'FORMAÇÃO CAMPESTRE': 12
}

classeDictAntropicas = {
    'PASTAGEM': 21, 'AGRICULTURA': 21, 'LAVOURA TEMPORÁRIA': 21, 'SOJA': 21,
    'CANA': 21, 'ARROZ': 21, 'ALGODÃO': 21, 'OUTRAS LAVOURAS TEMPORÁRIAS': 21,
    'LAVOURA PERENE': 21, 'CAFÉ': 21, 'CITRUS': 21, 'DENDÊ': 21,
    'OUTRAS LAVOURAS PERENES': 21,  'MOSAICO DE USOS': 21,
    'PRAIA, DUNA E AREAL': 22, 'PRAIA E DUNA': 22, 'ÁREA URBANIZADA': 22,
    'VEGETAÇÃO URBANA': 22, 'INFRAESTRUTURA URBANA': 22, 'MINERAÇÃO': 22,
    'OUTRAS ÁREAS NÃO VEGETADAS': 22, 'OUTRA ÁREA NÃO VEGETADA': 22,
    'APICUM': 22, 'AFLORAMENTO ROCHOSO': 29
}


def __init__(nameBacia):
        
    # print("geometria ", len(self.geom_bacia.getInfo()['coordinates']))
    self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['date_inic'], self.options['date_end'] + 1)]
    self.years = [yy for yy in range(self.options['date_inic'], self.options['date_end'] + 1)]

    self.pontos_references = 
    
    # https://code.earthengine.google.com/4f5c6af0912ce360a5adf69e4e6989e7
    self.imgMap10 = ee.Image(self.options['inputAsset10']).updateMask(self.bacia_raster)
    # .remap(self.options['classMapB'], 
    
    print("carregando imagens a serem processadas com Temporal CC")  
    print("from >> ", self.options['input_asset']) 
    print(" >>>>>>>>> read >>> ", self.name_imgClass)       
    self.imgClass = (ee.ImageCollection(self.options['input_asset'])
                            .filter(ee.Filter.eq('version', self.options['version_input']))
    )

    # self.imgClass = self.imgClass.select(self.lstbandNames)
    print("todas as bandas \n === > ", self.imgClass.bandNames().getInfo())
    # sys.exit()
   
        
        
    def dictionary_bands(self, key, value):
        imgT = ee.Algorithms.If(
                        ee.Number(value).eq(2),
                        self.imgClass.select([key]).byte(),
                        ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
                    )
        return ee.Image(imgT)

    def avaliar_bacia(idBacia):
        print(f"🟡 Avaliando bacia {idBacia}...")
        print("carregando imagens a serem processadas com Temporal CC")  
        print("from >> ", options['input_asset']) 
    
        imgClass = (ee.ImageCollection(options['input_asset'])
                                .filter(ee.Filter.eq('version', options['version_input']))
                                .filter(ee.Filter.eq('id_bacias', idBacia))
                                .first()
        )
        print("reading ", imgClass.bandNames().getInfo())
        proj = imgClass.projection()

        geom_bacia = (ee.FeatureCollection(options['asset_bacias_buffer'])
                                        .filter(ee.Filter.eq('nunivotto4', idBacia))
                        )
        geom_bacia = geom_bacia.map(lambda f: f.set('id_codigo', 1))
        bacia_raster =  geom_bacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)                                                    
        geom_bacia = geom_bacia.geometry()  

        pontos = ee.FeatureCollection(options['asset_ROIs']).filterBounds(geom_bacia)

        def avaliar_combo(classes, classe_dict, label, ano):
            classe_keys = list(classe_dict.keys())
            dict_js = ee.Dictionary(classe_dict)

            pontos_valid = (pontos
                            .filter(ee.Filter.inList(f'CLASS_{ano}', classe_keys))
                            .map(lambda f: f.set('ref', dict_js.get(f.get(f'CLASS_{ano}'))))
            )
            # Lista de bandas disponíveis no asset
            bandas_disponiveis = img.bandNames()

            # Gera lista de bandas válidas disponíveis
            bandas = ['classification_' + str(a) for a in range(options['date_inic'], options['date_end'] + 1)]
            bandas_validas = [b for b in bandas if bandas_disponiveis.contains(b).getInfo()]

            stack = ee.ImageCollection([
                img.select(b).updateMask(img.select(b).remap(classes, [1]*len(classes)).eq(1)).rename(b)
                for b in bandas_validas
            ]).toBands()

            freqs = {c: stack.eq(c).reduce(ee.Reducer.sum()) for c in classes}
            freqTot = stack.neq(0).reduce(ee.Reducer.count())

            combinacoes = [[l1, l2, l3] for l1 in limiares for l2 in limiares for l3 in limiares]
            melhores = {'acc': -1, 'l1': None, 'l2': None, 'l3': None}

            for lim in combinacoes:
                l1, l2, l3 = lim
                m1 = freqs[classes[0]].divide(freqTot).gte(l1)
                m2 = freqs[classes[1]].divide(freqTot).gte(l2)
                m3 = freqs[classes[2]].divide(freqTot).gte(l3)

                novaClasse = (ee.Image(0)
                                .where(m1, classes[0])
                                .where(m2.And(m1.Not()), classes[1])
                                .where(m3.And(m1.Not()).And(m2.Not()), classes[2])
                )

                bandaAno = img.select(f'classification_{ano}')
                mascara = bandaAno.remap(classes, [1]*len(classes)).eq(1)

                reclass = (bandaAno.where(mascara, novaClasse.unmask(0))
                            .rename('map_class')
                            .setDefaultProjection(proj)
                )

                pontos_classificados = pontos_valid.map(lambda f: f.set(
                    'map_class',
                    reclass.reduceRegion(
                        reducer=ee.Reducer.first(),
                        geometry= f.geometry(),#.centroid(30),
                        scale=10,
                        maxPixels=1e13
                    ).get('map_class')
                ))

                pontos_validos = pontos_classificados.filter(ee.Filter.notNull(['map_class', 'ref']))


                pontos_acerto = pontos_validos.map(
                                lambda f: f.set(
                                        'acerto',
                                        ee.Number(f.get('ref')).eq(ee.Number(f.get('map_class'))).int()
                                    ))

                total = pontos_acerto.size()
                acertos = pontos_acerto.aggregate_sum('acerto')
                acc = ee.Number(acertos).divide(total).getInfo()

                print(f"   🔍 {label} — ACC: {acc:.2f} | Limiar: {lim}")
                if acc > melhores['acc']:
                    melhores.update({'acc': acc, 'l1': l1, 'l2': l2, 'l3': l3})

            print(f"✅ Melhor {label}: {melhores}")
            return melhores

        melhores_nat = avaliar_combo(naturais, classeDictNaturais, 'Naturais', 2015)
        melhores_ant = avaliar_combo(antropicas, classeDictAntropicas, 'Antrópicas', 2015)
        return {'bacia': idBacia, 'naturais': melhores_nat, 'antropicas': melhores_ant}

    def processing_gapfill(self):

        # apply the gap fill
        imageFilled = self.applyGapFill()
        print(" 🚨🚨🚨  Applying filter Gap Fill 🚨🚨🚨 ")
        print(imageFilled.bandNames().getInfo())
        # sys.exit()
        name_toexport = f'filterGF_BACIA_{self.id_bacias}_GTB_V{self.options['version_output']}'
        imageFilled = (ee.Image(imageFilled)
                        .updateMask(bacia_raster)
                        .set(
                            'version', options['version_output'], 
                            'biome', 'CAATINGA',
                            'source', 'geodatin',
                            'model', "GTB",
                            'type_filter', 'gap_fill',
                            'collection', '2.0',
                            'id_bacias', self.id_bacias,
                            'sensor', 'Sentinel',
                            'system:footprint' , self.geom_bacia.coordinates()
                        )
        )
        
        self.processoExportar(imageFilled, name_toexport)

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':self.geom_bacia,#.getInfo()['coordinates'],
            'scale': 10, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))
















listaNameBacias = [
    '751', '7691', '7754', '7581', '7625', '7584', '7614', 
    '7616', '745', '7424', '773', '7612', '7613', '752', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443','7544', '7438', 
    '763', '7591', '7592', '746','7712', '7622', '765', 
]
# listaNameBacias = ['7746', '7619', '763']
# listaNameBacias = [ "7613","7746","7754","7741","773","761112","7591","7581","757"]
# listaNameBacias = [ "755","7622","746","7591","7544","7443", "766", "757", "7764", "7671", "7422", "7564"]
# listaNameBacias = ["7591"]
cont = 49
start_date = 15
# cont = gerenciador(cont)
# applyGdfilter = False
for cc, idbacia in enumerate(listaNameBacias[start_date:]):
    print("-----------------------------------------")
    print(f"----- #{cc + start_date}/{len(listaNameBacias)} PROCESSING BACIA {idbacia} -------")   
    try: 
        aplicando_gapfill = processo_gapfill(idbacia, False) # added band connected is True
        aplicando_gapfill.processing_gapfill()
    except:
        print(f"basin {idbacia} with erro ")