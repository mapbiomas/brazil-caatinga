#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#  SCRIPT DE CALCULO DE AREA POR AREAS PRIORITARIAS DA CAATINGA
#  Produzido por Geodatin - Dados e Geoinformacao
#  DISTRIBUIDO COM GPLv2

#  Relação de camadas para destaques:
#  Assentamento_Brasil - Asentamentos 
#  nucleos_desertificacao - Nucleos de desertificação,
#  UnidadesConservacao_S - Unidades de conservação  -> 'TipoUso' -> ["Proteção Integral", "Proteção integral",  "Uso Sustentável"]
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
import gee
import sys
import arqParametros as arqParamet
import collections
collections.Callable = collections.abc.Callable

try:
    ee.Initialize()
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

param = {
    'inputAssetCol': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1',  
    'inputTransicao': 'projects/mapbiomas-workspace/COLECAO8/transicao',
    'assets' : {
        "Assentamento_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
        "BR_ESTADOS_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
        "BR_Municipios_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
        "BR_Pais_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
        "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
        "Sigef_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sigef_Brasil",
        "Sistema_Costeiro_Marinho" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sistema_Costeiro_Marinho",
        "aapd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/aapd",
        "areas_Quilombolas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/areas_Quilombolas",
        "buffer_pts_energias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/buffer_pts_energias",
        "energias-dissolve-aneel" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/energias-dissolve-aneel",
        "florestaspublicas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/florestaspublicas",
        "imovel_certificado_SNCI_br" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/imovel_certificado_SNCI_br",
        "macro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
        "meso_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/meso_RH",
        "micro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/micro_RH",
        "pnrh_asd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_asd",
        "prioridade-conservacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/prioridade-conservacao-caatinga-ibama",
        "prioridade-conservacao-V1" : "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V1",
        "prioridade-conservacao-V2" : "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V2",
        "tis_poligonais_portarias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/tis_poligonais_portarias",
        "transposicao-cbhsf" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/transposicao-cbhsf",
        "nucleos_desertificacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
        # "UnidadesConservacao_S" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/UnidadesConservacao_S",
        "UnidadesConservacao_S" : "projects/mapbiomas-workspace/AUXILIAR/areas-protegidas",
        "unidade_gerenc_RH_SNIRH_2020" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
        "reserva_biosfera" : "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
        "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
        'semiarido' : 'users/mapbiomascaatinga04/semiarido_rec',
        "irrigacao": 'projects/ee-mapbiomascaatinga04/assets/polos_irrigaaco_atlas',
        "energiasE": 'projects/ee-mapbiomascaatinga04/assets/energias_renovaveis',
        "bacia_sao_francisco" : 'users/solkancengine17/shps_public/bacia_sao_francisco' 
    },   
    # 'assetVetor': 'users/data_sets_solkan/SHPs/APA_Guarajuba_limite',
    'assetVetor': 'users/data_sets_solkan/SHPs/APA_R_Capivara_limite',
    'collection': '7.1', # 
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXP-SEMIARIDO-24', 
    'lsClasses': [3,4,12,15,18,21,22,33,29],
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '29': 'caatinga05',        
        # '35': 'solkan1201',
        # '36': 'rodrigo',
        # '35': 'diegoGmail',    
    },
}

lst_nameAsset = [
    # 'Assentamento_Brasil', 
    # "nucleos_desertificacao",
    # "UnidadesConservacao_S", #"unidade_gerenc_RH_SNIRH_2020", 
    # 'areas_Quilombolas', 
    # "macro_RH", "meso_RH", #'micro_RH', 
    # 'prioridade-conservacao-V1', 
    # 'prioridade-conservacao-V2', 
    # 'tis_poligonais_portarias', 
    # "reserva_biosfera",
    # 'semiarido',
    # "energiasE",
    ##"irrigacao",
    # "bacia_sao_francisco",
    "semiarido2024"
];

dict_name = {
    "prioridade-conservacao": 'prior_cons',
    "reserva_biosfera": 'res_biosf',
    "Assentamento_Brasil": 'Assent_Br', 
    "nucleos_desertificacao": "nucleos_desert",
    "UnidadesConservacao_S": "UnidCons_S", 
    "unidade_gerenc_RH_SNIRH_2020": "unid_ger_RH",
    "areas_Quilombolas": "areaQuil", 
    "macro_RH": "macro_RH", 
    "meso_RH": "meso_RH", 
    "tis_poligonais_portarias": "tis_port",
    "PARNAÍBA": "PARN", 
    "ATLÂNTICO NORDESTE ORIENTAL": "AtlTO", 
    "SÃO FRANCISCO": "SF", 
    "ATLÂNTICO LESTE": "AtlL",
    "Proteção Integral": "prot_Int", 
    "Proteção integral": "prot_Int2",  
    "Uso Sustentável": "Uso_sustt",
    'semiarido': 'semiarido',
    "energiasE": 'energias_renovaveis',
    'prioridade-conservacao-V1': 'prioridade-conservacao-V1',
    'prioridade-conservacao-V2': 'prioridade-conservacao-V2',
    "bacia_sao_francisco": "bacia_sao_francisco",
    "semiarido2024": "limite_Semiarido_2024"
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
    '196': "Submedio_Sao_Francisco",
    '197': "Medio_Sao_Francisco",
    '205':"Alto_Sao_Francisco",
    '219':"Baixo_Sao_Francisco"
}
camadasAtenc = [
    'prioridade-conservacao', 'reserva_biosfera',
    'UnidadesConservacao_S', 'macro_RH','meso_RH'
];
lstSemiarido = ["08012100154","08012200053","08012900108"]
nameCamada = '';
lstTipoUso = [
    ["Proteção Integral", "Proteção integral"],  ["Uso Sustentável"]
];
lstMacro = [
    "PARNAÍBA", "ATLÂNTICO NORDESTE ORIENTAL", 
    "SÃO FRANCISCO", "ATLÂNTICO LESTE"
];
lstIdsbaciaSF = ['196','197','205','219']
dictMeso ={
    "PARNAÍBA": ["Alto Parnaíba", "Médio Parnaíba", "Baixo Parnaíba"],
    "ATLÂNTICO NORDESTE ORIENTAL": [
        "Jaguaribe", "Litoral do Ceará", "Litoral do Rio Grande do Norte e Paraíba", 
        "Piancó-Piranhas-Açu", "Litoral de Pernambuco e Alagoas"],
    "SÃO FRANCISCO": ["Médio São Francisco", "Submédio São Francisco", "Baixo São Francisco"],
    "ATLÂNTICO LESTE": ["Contas", "Itapicuru/Paraguaçu", "Jequitinhonha/Pardo", "Vaza-Barris"]
}
dictMesoSigla ={
    "PARNAÍBA": {
        "Alto Parnaíba": "AltoP", 
        "Médio Parnaíba": "MedioP", 
        "Baixo Parnaíba": "BaixoP"
    },
    "ATLÂNTICO NORDESTE ORIENTAL": {
        "Jaguaribe": "AtlaNO_Jag", 
        "Litoral do Ceará": "AtlaNO_LC", 
        "Litoral do Rio Grande do Norte e Paraíba": "AtlaNO_LRGNP", 
        "Piancó-Piranhas-Açu": "AtlaNO_PPA", 
        "Litoral de Pernambuco e Alagoas": "AtlaNO_LPA"
    },
    "SÃO FRANCISCO": {
        "Médio São Francisco": "MedioSF", 
        "Submédio São Francisco": "SubmedSF", 
        "Baixo São Francisco": "BaixoSF"
    },
    "ATLÂNTICO LESTE": {
        "Contas": "AtlaL_C", 
        "Itapicuru/Paraguaçu": "AtlaL_IP", 
        "Jequitinhonha/Pardo": "AtlaL_JP", 
        "Vaza-Barris": "AtlaL_VB"
    }
}
dict_CD_Bioma = {
    '1': '',
    '2': '_Caatinga',
    '3': '',
    '4': '',
    '5': '',
    '6': '',
}

def gerenciador(cont):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in param['conta'].keys()]    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(param['conta'][str(cont)]))        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

##############################################
###     Helper function
###    @param item 
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
def calculateArea (image, pixelArea, geometry):

    pixelArea = pixelArea.addBands(image.rename('classe')).clip(geometry)#.addBands(
                                # ee.Image.constant(yyear).rename('year'))
    reducer = ee.Reducer.sum().group(1, 'classe')
    optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': param['scale'],
        'bestEffort': True, 
        'maxPixels': 1e13
    }    
    areas = pixelArea.reduceRegion(**optRed)

    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)    
    return areas

# pixelArea, imgMapa, bioma250mil

def iterandoXanoImCruda(imgAreaRef, limite, namesubVector, namemacroVect, isCobert, porAno, remap):
    
    classMapB = [3, 4, 5, 6, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
    classNew =  [3, 4, 3, 3, 3,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,33,33,18,18,18,18,18,18,18,18,18,18, 4,12,18]
    sufRemap = '_sinRM'
    imgAreaRef = imgAreaRef.clip(limite)
    areaGeral = ee.FeatureCollection([])  
    cont = 0
    if isCobert:
        print("Loadding image Cobertura Coleção 8 " )
        imgMapp = ee.Image(param['inputAssetCol']).clip(limite)  # para a 7.1
        # print("---- SHOW ALL BANDS FROM MAPBIOKMAS MAPS -------\n ", imgMapp.bandNames().getInfo())

        for year in range(1985, 2023):
            # print(f" ======== processing year {year} for mapbiomas map =====")
            bandAct = "classification_" + str(year)
            if remap:
                newimgMap = imgMapp.select(bandAct).remap(classMapB, classNew)
                sufRemap = '_remap'
                # print("    << remaping >>   ")
            else:
                newimgMap = imgMapp.select(bandAct)
            areaTemp = calculateArea (newimgMap, imgAreaRef, limite)        
            areaTemp = areaTemp.map( lambda feat: feat.set(
                                                'year', year, 
                                                'nomeVetor', nomeVetor,
                                                'region', namesubVector, 
                                                'sub_region', namemacroVect
                                            ))
            if porAno:                
                nameCSV = "area_class_" + namesubVector + namemacroVect + "_" + str(year) + sufRemap
                processoExportar(areaTemp, nameCSV)
                cont = gerenciador(cont) 
            else:
                areaGeral = areaGeral.merge(areaTemp)              

    else:
        print("Loadding image Transição Coleção 8 " )
        imgColMapp = ee.ImageCollection(param['inputTransicao'])
      
        bandsTransica = ['mapbiomas_brazil_1985_2022_0-16', 'mapbiomas_brazil_1985_1990_0-16']
        years = ['1985_2022', '1985_1990']
        for cc, banda in enumerate(bandsTransica):
            imgMapp = ee.Image(imgColMapp.filter(
                            ee.Filter.eq("system:index", banda)
                                    ).first()).clip(limite)

            areaTemp = calculateArea (imgMapp, imgAreaRef, limite)        
            areaTemp = areaTemp.map( lambda feat: feat.set(
                                                    'year', years[cc], 
                                                    'nomeVetor', nomeVetor,
                                                    'region', namesubVector, 
                                                    'sub_region', namemacroVect
                                                ))

            areaGeral = areaGeral.merge(areaTemp)  
    nExport = True
    if porAno:
        nExport = False    

    return areaGeral, nExport

        
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

print('         limite caatinga carregado ')
select_Caatinga = False
sobreNomeGeom = "_Semiarido"
CD_Bioma = None
if select_Caatinga:
    limitGeometria = ee.FeatureCollection(param['assets']["Im_bioma_250"])
    if CD_Bioma == None:
        sobreNomeGeom = '_Brasil'
    else:
        limitGeometria = limitGeometria.filter(ee.Filter.eq("CD_Bioma", str(CD_Bioma)))
        sobreNomeGeom = dict_CD_Bioma[str(CD_Bioma)]
else:
    limitGeometria = ee.FeatureCollection(param['assets']["semiarido2024"])

print("=============== limite a Macro Selecionado ========== ", limitGeometria.size().getInfo())
# limitGeometria = limitGeometria.geometry()
# for assetshp in lst_nameAsset:
#     shp_tmp = ee.FeatureCollection(param['assets'][assetshp]).filterBounds(limitCaat.geometry())


#testes do dado
# https://code.earthengine.google.com/8e5ba331665f0a395a226c410a04704d
# https://code.earthengine.google.com/306a03ce0c9cb39c4db33265ac0d3ead
# get raster with area km2
lstBands = ['classification_' + str(yy) for yy in range(1985, 2022)]
shpLimit = ee.FeatureCollection(param['assetVetor'])
pixelArea = ee.Image.pixelArea().divide(10000)
# imgMapa = ee.ImageCollection(param['inputAsset']).select(lstBands)

# nameCSV = "area_class_" + sufixo
# print("Calculando a area ", nameCSV)
# areaM = iterandoXanoImCruda(pixelArea, shpLimit)  
# processoExportar(areaM, nameCSV)
sufRemap = '_sinRM'
cont = 0
byYears = False
lstProp = []
for nameAsset in lst_nameAsset[:]:

    print(f"------ PROCESSING {nameAsset} --------")
    shp_tmp = ee.FeatureCollection(param['assets'][nameAsset]
                            ).filterBounds(limitGeometria.geometry());
    # print(" => " + nameAsset, shp_tmp.first().propertyNames().getInfo());
    # print(" => " + nameAsset, " with = ", shp_tmp.size().getInfo());
    
    if nameAsset == 'prioridade-conservacao-V1' or nameAsset == 'prioridade-conservacao-V2':
        shp_tmp = shp_tmp.filter(ee.Filter.eq('import_bio', 'Extremamente Alta'))
        print("filtrado por prioridade ", shp_tmp.size().getInfo());
        nameCSV = "area_class_" + dict_name[nameAsset] + "_" + 'ext_alta' + sobreNomeGeom + sufixo
        # imgAreaRef, limite, namesubVector, namemacroVect, isCobert, porAno, remap
        csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp.geometry().intersection(limitGeometria.geometry()), 
                                dict_name[nameAsset], 'ext_alta', paraCobertura, byYears, True)
        
        if exportar:
            processoExportar(csv_table, nameCSV)

    elif nameAsset == 'reserva_biosfera':
        lstPropResBio = shp_tmp.reduceColumns(ee.Reducer.toList(), ['zona']).get('list').getInfo();
        lstPropResBio = unique(lstPropResBio)
        print("reserva da biosfera ", lstPropResBio);
        for typeRes in lstPropResBio:
            shp_tmp_resBio = shp_tmp.filter(ee.Filter.eq('zona', typeRes))
            nameCSV = "area_class_" + dict_name[nameAsset] + "_" + typeRes + sobreNomeGeom + sufixo
            csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_resBio.geometry().intersection(limitGeometria.geometry()), 
                                    dict_name[nameAsset], typeRes, paraCobertura, byYears, True)
            
            if exportar:
                processoExportar(csv_table, nameCSV)
    
    elif nameAsset == 'UnidadesConservacao_S':
        lstTipoUso = shp_tmp.reduceColumns(ee.Reducer.toList(), ['TipoUso']).get('list').getInfo();
        print("Unidades de conservação ", unique(lstTipoUso));
        lstTipoUso = [["Proteção Integral", "Proteção integral"],  ["Uso Sustentável"]]
        for typeUso in lstTipoUso:
            shp_tmp_uso = shp_tmp.filter(ee.Filter.inList('TipoUso', typeUso))      
            nameCSV = "area_class_" + dict_name[nameAsset] + "_" + dict_name[typeUso[0]] + sobreNomeGeom + sufixo      
            csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_uso.geometry().intersection(limitGeometria.geometry()), 
                            dict_name[nameAsset], dict_name[typeUso[0]], paraCobertura, byYears,  True)
            
            if exportar:
                processoExportar(csv_table, nameCSV)


    elif nameAsset == 'macro_RH':
        lstProp = shp_tmp.reduceColumns(ee.Reducer.toList(), ['nm_macroRH']).get('list').getInfo();
        print("Macro Região Hidrografica ", unique(lstProp));
        for nmmacro in lstMacro:
            shp_tmp_macro = shp_tmp.filter(ee.Filter.eq('nm_macroRH', nmmacro))
            # nameCamada = nameAsset + "_" + nmmacro
            # Map.addLayer(shp_tmp_macro, {}, nameCamada, false);
            nameCSV = "area_class_" + dict_name[nameAsset] + "_" + dict_name[nmmacro] + sobreNomeGeom + sufixo
            csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_macro.geometry().intersection(limitGeometria.geometry()), 
                            dict_name[nameAsset], 'Caat', paraCobertura, byYears, True)
            
            if exportar:
                processoExportar(csv_table, nameCSV)

    elif nameAsset == 'meso_RH':
        lstProp = shp_tmp.reduceColumns(ee.Reducer.toList(2),  
                            ['nm_macroRH', 'nm_mesoRH']).get('list').getInfo();
        print("Meso Região Hidrografica ", uniques(lstProp));
        for nmmacro in lstMacro:
            lstMesoRH = dictMeso[nmmacro]
            print("Macro => ", nmmacro, " with ", lstMesoRH)
            for nmmeso in lstMesoRH:
                print("loading ", nmmeso)
                shp_tmp_meso = shp_tmp.filter(ee.Filter.eq('nm_mesoRH', nmmeso))
                # nameCamada = nameAsset + "_" + dictMesoSigla[nmmacro][nmmeso]
                nameCSV = "area_class_" + dict_name[nameAsset] + dictMesoSigla[nmmacro][nmmeso] + sobreNomeGeom + sufixo
                csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_meso.geometry().intersection(limitGeometria.geometry()), 
                            dict_name[nameAsset], dictMesoSigla[nmmacro][nmmeso], paraCobertura, byYears, True)
                
                if exportar:
                    processoExportar(csv_table, nameCSV)

    elif nameAsset == 'semiarido':
        for semiA in lstSemiarido:
            shp_tmp_semi = shp_tmp.filter(ee.Filter.eq('cd_recorte', semiA))
            nameCSV = "area_class_" + nameAsset + semiA + sufixo
            csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_semi.geometry().intersection(limitGeometria.geometry()), 
                            nameAsset, semiA, paraCobertura, False, True)
            
            if exportar:
                processoExportar(csv_table, nameCSV)

    elif nameAsset == "irrigacao":
        for irrig in camadasIrrig:
            shp_tmp_irr = shp_tmp.filter(ee.Filter.eq('Polo_irrig', irrig))
            nameCSV = "area_class_" + nameAsset + "_" + dict_Irrig[irrig] + sobreNomeGeom + sufixo
            csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_irr.geometry().intersection(limitGeometria.geometry()), 
                            nameAsset, dict_Irrig[irrig], paraCobertura, byYears, nameCSV, True)
            
            if exportar:
                processoExportar(csv_table, nameCSV)

    elif nameAsset == "bacia_sao_francisco":

        for idBaciaSF in lstIdsbaciaSF:
            nameCSV = "area_class_" + nameAsset + "_" + dict_baciaSF[idBaciaSF] +sobreNomeGeom + sufixo
            shp_tmp_bSF = shp_tmp.filter(ee.Filter.eq('id', int(idBaciaSF))) #'id','nm_mesoRH'
            print("size shp São Francisco ", shp_tmp_bSF.size().getInfo())
            csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp_bSF.geometry().intersection(limitGeometria.geometry()), 
                            nameAsset, dict_baciaSF[idBaciaSF], paraCobertura, byYears, False) # remap = False
            
            if exportar:
                processoExportar(csv_table, nameCSV)
            # sys.exit()
    else:
        nameCSV = "area_class_" + dict_name[nameAsset] + sobreNomeGeom + sufixo + sufRemap 
        csv_table, exportar = iterandoXanoImCruda(pixelArea,  shp_tmp.geometry().intersection(limitGeometria.geometry()), 
                            dict_name[nameAsset], 'Semiarido_2024', paraCobertura, True, False) # remap = False
        
        if exportar:
            processoExportar(csv_table, nameCSV)

    # cont = gerenciador(cont) 
    # sys.exit()

