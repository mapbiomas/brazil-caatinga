#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#  SCRIPT DE CALCULO DE AREA POR AREAS PRIORITARIAS DA CAATINGA
#  Produzido por Geodatin - Dados e Geoinformacao
#  DISTRIBUIDO COM GPLv2

#  Relação de camadas para destaques:
#  Assentamento_Brasil - Asentamentos 
#  nucleos_desertificacao - Nucleos de desertificação,
#  UnidadesConservacao - Unidades de conservação  -> 'TipoUso' -> ["Proteção Integral", "Proteção integral",  "Uso Sustentável"]
#  unidade_gerenc_RH_SNIRH_2020- Unidade de gerenciamento de recursos Hidricos 
#  tis_poligonais_portarias -  Terras indígenas
#  prioridade-conservacao - Prioridade de conservação (usar apenas Extremamente alta)
#  florestaspublicas - Unidades de conservação
#  areas_Quilombolas - áreas quilombolas
#  macro_RH - Bacias hidrográficas 
#  reserva da biosfera - 'zona' ->  ["nucleo","transicao","amortecimento"]
#  Novo limite do semiarido 2024


'''
import ee
import os 
# import copy
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount) #
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

nomeVetor = 'APA_R_Capivara'
sufixo = nomeVetor + '_cob'

paraCobertura = True
if paraCobertura:
    sufixo = '_cob'
else:
    sufixo = '_tans'

#testes do dado
# https://code.earthengine.google.com/8e5ba331665f0a395a226c410a04704d
# https://code.earthengine.google.com/306a03ce0c9cb39c4db33265ac0d3ead
# get raster with area km2


param = {
    # 'inputAssetCol': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',  
    # 'inputAssetCol': 'projects/mapbiomas-workspace/COLECAO9/integracao',
    'inputAssetCol': 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification',
    'inputTransicao': 'projects/mapbiomas-workspace/COLECAO8/transicao',
    'assets' : {
        "Assentamento-Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
        "BR_ESTADOS_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
        "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
        "br_estados_shp": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
        "BR_Municipios_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
        "BR_Pais_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
        "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
        'vetor_biomas_250': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
        'biomas_250_rasters': 'projects/mapbiomas-workspace/AUXILIAR/RASTER/Bioma250mil',
        "Sigef_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sigef_Brasil",
        "Sistema_Costeiro_Marinho" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sistema_Costeiro_Marinho",
        "aapd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/aapd",
        "areas-Quilombolas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/areas_Quilombolas",
        "buffer_pts_energias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/buffer_pts_energias",
        "energias-dissolve-aneel" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/energias-dissolve-aneel",
        "florestaspublicas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/florestaspublicas",
        "imovel_certificado_SNCI_br" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/imovel_certificado_SNCI_br",
        "macro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
        "meso-RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/meso_RH",
        "pnrh_asd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_asd",
        "prioridade-conservacao" : "projects/ee-solkancengine17/assets/shp_publicos/areas_prioridade_conservacao",
        "tis-poligonais-portarias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/tis_poligonais_portarias",
        "transposicao-cbhsf" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/transposicao-cbhsf",
        "nucleos-desertificacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
        "UnidadesConservacao" : "projects/ee-solkancengine17/assets/shp_publicos/Unidades_consevacao_CNUC",
        "unidade_gerenc_RH_SNIRH_2020" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
        "reserva-biosfera" : "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
        "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
        'semiarido' : 'users/mapbiomascaatinga04/semiarido_rec',
        "irrigacao": 'projects/ee-mapbiomascaatinga04/assets/polos_irrigaaco_atlas',
        "energiasE": 'projects/ee-mapbiomascaatinga04/assets/energias_renovaveis',        
        "matopiba": 'projects/mapbiomas-fogo/assets/territories/matopiba'
    },
    'collection': '10.0', # 
    'outputVersion': '0-7',
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'date_end': 2024,
    'driverFolder': 'AREA-CAATINGA-CORR', 
    'lsClasses': [3,4,12,15,18,21,22,33,29],
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta' : {
        '0': 'caatinga01',         
    },
}

lst_nameAsset = [
    'ALL',
    # 'Assentamento-Brasil', 
    # "nucleos-desertificacao",
    # "UnidadesConservacao", 
    # 'areas-Quilombolas', 
    # "meso-RH", 
    # 'prioridade-conservacao', 
    # 'tis-poligonais-portarias', 
    # "reserva-biosfera",
    # 'matopiba',
    # "energiasE"
    # "transposicao-cbhsf"
];                          

dict_name = {
    "prioridade-conservacao": 'prior-cons',
    "reserva-biosfera": 'res-biosf',
    "Assentamento-Brasil": 'Assent-Br', 
    "nucleos-desertificacao": "nucleos-desert",
    "UnidadesConservacao": "UnidCons-S", 
    "unidade_gerenc_RH_SNIRH_2020": "unid-ger-RH",
    "areas_Quilombolas": "areaQuil", 
    "macro_RH": "macro-RH", 
    "meso-RH": "meso-RH", 
    "micro_RH": "micro_RH",
    "matopiba": "matopiba",
    "tis-poligonais-portarias": "tis-port",
    "PARNAÍBA": "PARN", 
    "ATLÂNTICO NORDESTE ORIENTAL": "AtlTO", 
    "SÃO FRANCISCO": "SF", 
    "ATLÂNTICO LESTE": "AtlL",
    "Proteção Integral": "prot-Int", 
    "Proteção integral": "prot-Int2",  
    "Uso Sustentável": "Uso-sustt",
    'semiarido': 'semiarido',
    "energiasE": 'energias-renovaveis',
    'prioridade-conservacao-V1': 'prioridade-conservacao-V1',
    'prioridade-conservacao-V2': 'prioridade-conservacao-V2',
    "bacia_sao_francisco": "bacia-sao-francisco",
    "semiarido2024": "limite-Semiarido-2024",
    "transposicao-cbhsf": "transposicao-cbhsf",
}
camadasIrrig = [
    "Jaíba", "Petrolina / Juazeiro", "Jaguaribe",
    "Mucugê-Ibicoara", "Oeste Baiano"
]
dict_Irrig = {
    "Jaíba": "Jaiba", 
    "Petrolina / Juazeiro": "PetroJuazei", 
    "Jaguaribe": "Jaguaribe",
    "Mucugê-Ibicoara": "MucuIbico", 
    "Oeste Baiano": "OestBaiano"
}
dict_baciaSF = {
    '196': "Submedio-Sao-Francisco",
    '197': "Medio-Sao-Francisco",
    '205':"Alto-Sao-Francisco",
    '219':"Baixo-Sao-Francisco"
}
camadasAtenc = [
    'prioridade-conservacao', 'reserva-biosfera',
    'UnidadesConservacao-S', 'macro-RH','meso-RH'
];
nameCamada = '';
dictTipoUso = {
    "Proteção Integral" : "protecao-integral",
    "Uso Sustentável": "uso-sustentavel"
}
lstMacro = [
    "PARNAÍBA", "ATLÂNTICO NORDESTE ORIENTAL", 
    "SÃO FRANCISCO", "ATLÂNTICO LESTE"
];
lstIdsbaciaSF = ['196','197','205','219']
dict_Macro = {
    "102": "TOCANTINS-ARAGUAIA",
    "103": "ATLÂNTICO NORDESTE OCIDENTAL",
    "104": "PARNAÍBA",
    "105": "ATLÂNTICO NORDESTE ORIENTAL",
    "106": "SÃO FRANCISCO",
    "107": "ATLÂNTICO LESTE",
    "108": "ATLÂNTICO SUDESTE"
}
dict_Meso = {
    "10213": " Alto Tocantins",
    "10317": " Itapecuru",
    "10420": " Alto Parnaíba",
    "10419": " Médio Parnaíba",
    "10418": " Baixo Parnaíba",
    "10522": " Jaguaribe",
    "10521": " Litoral do Ceará",
    "10524": "Litoral do Rio Grande do Norte e Paraíba",
    "10523": " Piancó-Piranhas-Açu",
    "10525": " Litoral de Pernambuco e Alagoas",
    "10628": " Médio São Francisco",
    "10627": " Submédio São Francisco",
    "10629": " Alto São Francisco",
    "10626": " Baixo São Francisco",
    "10732": " Contas",
    "10731": " Itapicuru/Paraguaçu",
    "10734": " Itanhém/Mucuri/São Mateus",
    "10733": " Jequitinhonha/Pardo",
    "10730": " Vaza-Barris",
    "10836": " Jucu/Itapemirim/Itabapoana",
    "10835": " Doce"
}
dict_CD_Bioma = {
    '1': '',
    '2': '_Caatinga',
    '3': '',
    '4': '',
    '5': '',
    '6': '',
}
dictEst = {
    '21': 'MARANHÃO',
    '22': 'PIAUÍ',
    '23': 'CEARÁ',
    '24': 'RIO GRANDE DO NORTE',
    '25': 'PARAÍBA',
    '26': 'PERNAMBUCO',
    '27': 'ALAGOAS',
    '28': 'SERGIPE',
    '29': 'BAHIA',
    '31': 'MINAS GERAIS',
    '32': 'ESPÍRITO SANTO'
}


def gerenciador(cont):
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)
    
    if str(cont) in numberofChange:
        
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 

        # tasks(n= param['numeroTask'], return_list= True) 
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:            
            relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        return 0
    cont += 1    
    return cont

##############################################
###    Helper function                    ####
###    @param item                        ####  
##############################################
def convert2featCollection (item):
    item = ee.Dictionary(item)
    feature = ee.Feature(ee.Geometry.Point([0, 0])).set(
        'classe', item.get('classe'),"area", item.get('sum'))
        
    return feature

#########################################################################
####     Calculate area crossing a cover map (deforestation, mapbiomas)
####     and a region map (states, biomes, municipalites)
####      @param image 
####      @param geometry
#########################################################################
# https://code.earthengine.google.com/5a7c4eaa2e44f77e79f286e030e94695
def calculateArea (image, pixelArea, geomFC):
    # limite_shp = ee.FeatureCollection(geomFC).geometry()
    # maskGeom_raster = ee.FeatureCollection(geomFC).reduceToImage(['id_codigo'], ee.Reducer.first())
    pixelArea = pixelArea.addBands(image.rename('classe')).selfMask()

    reducer = ee.Reducer.sum().group(1, 'classe')
    optRed = {
        'reducer': reducer,
        'geometry': geomFC,
        'scale': 30,
        'bestEffort': True, 
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)
    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

# pixelArea, imgMapa, bioma250mil
# shp_tmpdiv, limitGeometria, nameCSV
def iterandoXanoImCruda(limite_feat_col, shpBiomeGeom, name_export):
    shpLimitGeom = ee.FeatureCollection(shpBiomeGeom)                       
    mask_Geometry = shpLimitGeom.reduceToImage(['id_codigo'], ee.Reducer.first())  
    shpLimitGeom = shpLimitGeom.geometry() 
    # mascara do vector de interesse
    raster_mask_polygon = ee.FeatureCollection(limite_feat_col).reduceToImage(['id_codigo'], ee.Reducer.first())
    limite_feat_col = ee.FeatureCollection(limite_feat_col).geometry()
    # raster e vetores de estados 
    estados_raster = ee.Image(param['assets']["br_estados_raster"])
    shpStateGeom = ee.FeatureCollection(param['assets']["br_estados_shp"]) 
    lstEstCruz = [21,22,23,24,25,26,27,28,29,31,32]

    imgMapp = (ee.ImageCollection(param['inputAssetCol'])
                    .filter(ee.Filter.eq('version', param['outputVersion']))
                    .mosaic()
                    .updateMask(mask_Geometry)   # todo o vetor externo ou limite maior
                    .updateMask(raster_mask_polygon)  # limit dos vetores de interesse listados
                    # .selfMask()
            )
    imgAreaRef =  (ee.Image.pixelArea().divide(10000)
                    .updateMask(mask_Geometry)
                    .updateMask(raster_mask_polygon)
                    # .selfMask()
                )
        
    for estadoCod in lstEstCruz:
        areaGeral = ee.FeatureCollection([]) 
        print(f"processing Estado {dictEst[str(estadoCod)]} with code {estadoCod}")
        maskRasterEstado = estados_raster.eq(estadoCod)
        shpStateGeomS = shpStateGeom.filter(ee.Filter.eq('CD_GEOCUF', str(estadoCod))).geometry()

        rasterMapEstado = imgMapp.updateMask(maskRasterEstado)
        imgAreaRefEstado = imgAreaRef.updateMask(maskRasterEstado)

        geom_polygon_state = shpLimitGeom.intersection(shpStateGeomS).intersection(limite_feat_col)

        for year in range(1985, param['date_end'] + 1):
            # print(f" ======== processing year {year} for mapbiomas map =====")
            bandAct = "classification_" + str(year)
            newimgMap = rasterMapEstado.select(bandAct)
            areaTemp = calculateArea (newimgMap, imgAreaRefEstado, geom_polygon_state) 
            # print(" area temporal ", areaTemp.first().getInfo())
            # sys.exit()       
            areaTemp = areaTemp.map( lambda feat: feat.set(
                                                'year', year,                                               
                                                'estado_name', dictEst[str(estadoCod)], # colocar o nome do estado
                                                'estado_codigo', estadoCod
                                            ))

            areaGeral = areaGeral.merge(areaTemp)              

        nameCSV =  name_export + "_" + str(estadoCod) + "_lulc"
        processoExportar(areaGeral, nameCSV)

        
#exporta a imagem classificada para o asset
def processoExportar(areaFeat, nameT):      
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': param["driverFolder"]        
        }    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")    


def unique(list1): 
    # insert the list to the set
    list_set = set(list1)
    # convert the set to the list
    unique_list = (list(list_set))
    for x in unique_list:
        print (" >>> ", x)

    return unique_list
 
def uniques(list1): 
    # insert the list to the set
    list_set = []
    
    for x in list1:
        if x not in list_set:
            list_set.append(x)

    return list_set

sobreNomeGeom = "_Caatinga"
lst_limit = ['Caatinga', 'Semiarido'] # 'estados','Caatinga', 'Semiarido'
print(' limite caatinga carregado ')

select_Caatinga = True
for name_lim in lst_limit[:]: 

    if name_lim == 'Caatinga':
        limitGeometria = ee.FeatureCollection(param['assets']["vetor_biomas_250"])
        limitGeometria = limitGeometria.filter(ee.Filter.eq("CD_Bioma", 2))

    elif name_lim == 'Semiarido':
        limitGeometria = ee.FeatureCollection(param['assets']["semiarido2024"])
    else:
        limitGeometria = ee.FeatureCollection(param['assets']["br_estados_shp"])

    print("=============== limite a Macro Selecionado ========== ", limitGeometria.size().getInfo())
    # limitGeometria = limitGeometria.geometry()
    limitGeometria = limitGeometria.map(lambda feat: feat.set('id_codigo', 1))

    for cc, nameAsset in enumerate(lst_nameAsset[:]):

        print(f"------ <{cc}> PROCESSING {nameAsset} --------")
        if nameAsset == 'ALL': 
            shp_tmp = ee.FeatureCollection(param['assets']["br_estados_shp"])
        else:
            shp_tmp = ee.FeatureCollection(param['assets'][nameAsset]).filterBounds(limitGeometria)    
        # print(" => " + nameAsset, " with = ", shp_tmp.size().getInfo())
        shp_tmp = shp_tmp.map(lambda feat: feat.set('id_codigo', 1))
        
        if nameAsset == 'prioridade-conservacao':
            lst_prop = ee.Dictionary(shp_tmp.aggregate_histogram('prioridade')).keys().getInfo()
            for name_prop in lst_prop:
                shp_tmpdiv = shp_tmp.filter(ee.Filter.eq('prioridade', name_prop))
                name_prop = name_prop.replace(" ", "-")
                print(f"filtrado por prioridade {name_prop}   >> ", shp_tmpdiv.size().getInfo())
                nameCSV = f"area_class_{name_lim}_{nameAsset}_{name_prop}"
                # imgAreaRef, limite, namesubVector, namemacroVect, isCobert, porAno, remap
                iterandoXanoImCruda(shp_tmpdiv, limitGeometria, nameCSV)

        elif nameAsset == 'reserva-biosfera':
            lst_prop = ee.Dictionary(shp_tmp.aggregate_histogram('zona')).keys().getInfo()
            for name_prop in lst_prop:
                shp_tmpdiv = shp_tmp.filter(ee.Filter.eq('zona', name_prop))
                print("filtrado por prioridade ", shp_tmpdiv.size().getInfo())
                nameCSV = f"area_class_{name_lim}_{nameAsset}_{name_prop.replace(" ", "-")}"
                iterandoXanoImCruda(shp_tmpdiv, limitGeometria, nameCSV)
        
        elif nameAsset == 'UnidadesConservacao':
            # lst_prop = ee.Dictionary(shp_tmp.aggregate_histogram('grupo')).keys().getInfo()
            for name_prop in list(dictTipoUso.keys()):
                shp_tmpdiv = shp_tmp.filter(ee.Filter.inList('grupo', name_prop))     
                name_prop = dictTipoUso[name_prop]
                print(" export ", name_prop) 
                nameCSV = f"area_class_{name_lim}_{nameAsset}_{name_prop}"      
                iterandoXanoImCruda(shp_tmpdiv, limitGeometria, nameCSV)

        elif nameAsset == 'meso-RH':
            lst_prop = ee.Dictionary(shp_tmp.aggregate_histogram('cd_mesoRH')).keys().getInfo()
            for name_prop in lst_prop:
                shp_tmpdiv = shp_tmp.filter(ee.Filter.inList('cd_mesoRH', name_prop))      
                nameCSV = f"area_class_{name_lim}_{nameAsset}_{name_prop}"      
                iterandoXanoImCruda(shp_tmpdiv, limitGeometria, nameCSV)

        else:
            nameCSV = f"area_class_{name_lim}_{nameAsset}_semProp" 
            iterandoXanoImCruda(shp_tmp, limitGeometria, nameCSV)

        # cont = gerenciador(cont) 
        # sys.exit()    

