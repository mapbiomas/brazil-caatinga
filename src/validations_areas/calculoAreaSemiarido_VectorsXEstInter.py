#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CÁLCULO DE ÁREA POR CAMADAS TEMÁTICAS
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''
# --------------------------------------------------------------------------------#
# Bloco 1: Importação de Módulos e Inicialização do Earth Engine                   #
# Descrição: Este bloco importa as bibliotecas necessárias, configura o            #
# ambiente para encontrar módulos locais e inicializa a conexão com a API          #
# do Google Earth Engine usando uma conta pré-configurada.                         #
# --------------------------------------------------------------------------------#
import ee
import os
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões

# Adiciona diretórios pais ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[1])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

# Define e inicializa o projeto GEE a ser utilizado
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project=projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

# --------------------------------------------------------------------------------#
# Bloco 2: Parâmetros Globais e Configuração da Análise                            #
# Descrição: Esta seção centraliza todos os parâmetros de configuração do script.  #
# Inclui os caminhos para os assets de entrada (mapas e vetores), listas de        #
# camadas a serem processadas, dicionários para renomear arquivos e filtros       #
# específicos para cada camada temática.                                          #
# --------------------------------------------------------------------------------#

# --- Parâmetros Principais ---
param = {
    'inputAssetCol': 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification',
    'assets': {
        "Assentamento_Brasil": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
        "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
        "br_estados_shp": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
        'vetor_biomas_250': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
        "nucleos_desertificacao": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
        "UnidadesConservacao_S": "projects/mapbiomas-workspace/AUXILIAR/areas-protegidas",
        "macro_RH": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
        # (Outros assets omitidos para brevidade)
        "matopiba": 'projects/mapbiomas-fogo/assets/territories/matopiba'
    },
    'collection': '10.0', 'outputVersion': '0-7', 'biome': 'CAATINGA',
    'scale': 30, 'date_end': 2024,
    'driverFolder': 'AREA-SEMIARIDO-CORR',
    'conta': {'0': 'caatinga01'}
}

# --- Listas e Dicionários de Controle ---
# Lista de assets vetoriais a serem processados nesta execução

dict_name = {
    "prioridade-conservacao": 'prior-cons',
    "reserva_biosfera": 'res-biosf',
    "Assentamento_Brasil": 'Assent-Br', 
    "nucleos_desertificacao": "nucleos-desert",
    "UnidadesConservacao_S": "UnidCons-S", 
    "unidade_gerenc_RH_SNIRH_2020": "unid-ger-RH",
    "areas_Quilombolas": "areaQuil", 
    "macro_RH": "macro-RH", 
    "meso_RH": "meso-RH", 
    "micro_RH": "micro_RH",
    "matopiba": "matopiba",
    "tis_poligonais_portarias": "tis-port",
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
    "semiarido2024": "Semiarido-2024",
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
        "Jaguaribe": "AtlaNO-Jag", 
        "Litoral do Ceará": "AtlaNO-LC", 
        "Litoral do Rio Grande do Norte e Paraíba": "AtlaNO-LRGNP", 
        "Piancó-Piranhas-Açu": "AtlaNO-PPA", 
        "Litoral de Pernambuco e Alagoas": "AtlaNO-LPA"
    },
    "SÃO FRANCISCO": {
        "Médio São Francisco": "MedioSF", 
        "Submédio São Francisco": "SubmedSF", 
        "Baixo São Francisco": "BaixoSF"
    },
    "ATLÂNTICO LESTE": {
        "Contas": "AtlaL-C", 
        "Itapicuru/Paraguaçu": "AtlaL-IP", 
        "Jequitinhonha/Pardo": "AtlaL-JP", 
        "Vaza-Barris": "AtlaL-VB"
    }
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

# --------------------------------------------------------------------------------#
# Bloco 3: Funções Principais de Cálculo de Área                                   #
# Descrição: Este bloco contém as funções centrais que executam o cálculo de      #
# área. A função `calculateArea` realiza a operação de baixo nível no GEE,         #
# enquanto `iterandoXanoImCruda` orquestra o processo, iterando sobre a série      #
# temporal e estratificando os resultados por estado.                              #
# --------------------------------------------------------------------------------#

def convert2featCollection(item):
    """
    Função auxiliar para formatar a saída do redutor `sum().group()`.

    Args:
        item (ee.Dictionary): Dicionário do redutor (ex: {'classe': 3, 'sum': 1234.5}).

    Returns:
        ee.Feature: Feature com as propriedades 'classe' e 'area'.
    """
    item = ee.Dictionary(item)
    return ee.Feature(None, {'classe': item.get('classe'), "area": item.get('sum')})

def calculateArea(image, pixelArea, geomFC):
    """
    Calcula a área total para cada classe em uma imagem dentro de uma geometria.

    Args:
        image (ee.Image): Imagem de banda única contendo as classes.
        pixelArea (ee.Image): Imagem onde cada pixel tem o valor de sua área.
        geomFC (ee.Geometry): A região de interesse para o cálculo.

    Returns:
        ee.FeatureCollection: Coleção onde cada feature representa uma classe e sua área total.
    """
    pixelArea = pixelArea.addBands(image.rename('classe'))
    areas = pixelArea.reduceRegion(
        reducer=ee.Reducer.sum().group(1, 'classe'),
        geometry=geomFC, scale=30, bestEffort=True, maxPixels=1e13
    )
    areas = ee.List(areas.get('groups')).map(convert2featCollection)
    return ee.FeatureCollection(areas)

def iterandoXanoImCruda(limite_feat_col, namesubVector, namemacroVect, isCobert, porAno, remap):
    """
    Calcula a área de cobertura do solo, estratificada por estado e por ano.

    Para uma dada camada temática (`limite_feat_col`), esta função itera sobre
    os estados brasileiros e, para cada um, calcula a área de cada classe de
    cobertura para todos os anos da série temporal.

    Args:
        limite_feat_col (ee.FeatureCollection): A camada temática a ser analisada.
        namesubVector (str): Nome da camada temática para metadados.
        namemacroVect (str): Nome da subcategoria (se houver) para metadados.
        isCobert (bool): Flag indicando que o cálculo é de cobertura.
        porAno (bool): Se True, exporta um arquivo por ano; senão, um arquivo consolidado.
        remap (bool): Se True, aplica um remapeamento de classes.

    Returns:
        tuple: (ee.FeatureCollection com áreas, bool indicando se deve exportar).
    """
    classMapB = [3, 4, 5, ...]
    classNew = [3, 4, 3, ...]
    # Carrega camadas de referência (Semiárido, Estados)
    shpSemiArGeom = ee.FeatureCollection(param['assets']["semiarido2024"]).geometry()
    shpStateGeom = ee.FeatureCollection(param['assets']["br_estados_shp"])
    estados_raster = ee.Image(param['assets']["br_estados_raster"])
    
    # Carrega o mapa de cobertura do solo
    imgMapp = ee.ImageCollection(param['inputAssetCol'])\
        .filter(ee.Filter.eq('version', param['outputVersion']))\
        .mosaic().updateMask(ee.Image(1).clip(shpSemiArGeom))
    
    imgAreaRef = ee.Image.pixelArea().divide(10000).updateMask(ee.Image(1).clip(shpSemiArGeom))
    
    lstEstCruz = [21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32] # Códigos IBGE dos estados
    
    # Itera sobre cada estado para estratificar o resultado
    for estadoCod in lstEstCruz:
        areaGeral = ee.FeatureCollection([])
        print(f"processing Estado {dictEst[str(estadoCod)]} with code {estadoCod}")
        
        # Cria as geometrias e máscaras para o estado atual
        maskRasterEstado = estados_raster.eq(estadoCod)
        shpStateGeomS = shpStateGeom.filter(ee.Filter.eq('CD_GEOCUF', str(estadoCod))).geometry()
        geom_polygon_state = shpSemiArGeom.intersection(shpStateGeomS).intersection(limite_feat_col.geometry())
        
        # Itera sobre cada ano da série temporal
        for year in range(1985, param['date_end'] + 1):
            bandAct = "classification_" + str(year)
            mapToCalc = imgMapp.select(bandAct).updateMask(maskRasterEstado)
            
            # Calcula a área e adiciona metadados
            areaTemp = calculateArea(mapToCalc, imgAreaRef.updateMask(maskRasterEstado), geom_polygon_state)
            areaTemp = areaTemp.map(lambda feat: feat.set(
                'year', year, 'nomeVetor', nomeVetor, 'region', namesubVector,
                'sub_region', namemacroVect, 'estado_name', dictEst[str(estadoCod)],
                'estado_codigo', estadoCod
            ))
            
            # Exporta anualmente ou consolida
            if porAno:
                nameCSV = f"area_class_SA_{namesubVector}_{namemacroVect}_codEst_{estadoCod}_{year}"
                processoExportar(areaTemp, nameCSV)
            else:
                areaGeral = areaGeral.merge(areaTemp)

        if not porAno:
            nameCSV = f"area_class_SA_{namesubVector}_{namemacroVect}_codEst_{estadoCod}"
            processoExportar(areaGeral, nameCSV)
            
    return ee.FeatureCollection([]), False

# --------------------------------------------------------------------------------#
# Bloco 4: Funções Auxiliares e de Gerenciamento                                   #
# Descrição: Funções de suporte para exportar dados e gerenciar contas GEE.        #
# --------------------------------------------------------------------------------#
def processoExportar(areaFeat, nameT):
    """Exporta uma FeatureCollection (tabela de áreas) para o Google Drive."""
    optExp = {'collection': areaFeat, 'description': nameT, 'folder': param["driverFolder"]}
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start()
    print("salvando ... " + nameT + "..!")

def gerenciador(cont):
    """Gerencia a troca de contas do GEE para balancear a fila de tarefas."""
    # (Implementação omitida para brevidade)
    return cont

# --------------------------------------------------------------------------------#
# Bloco 5: Execução Principal do Script                                            #
# Descrição: Este bloco define a lista de camadas temáticas a serem processadas    #
# e inicia o loop principal. A lógica condicional (`if/elif/else`) dentro do loop  #
# aplica regras de filtragem e nomenclatura específicas para cada camada.          #
# --------------------------------------------------------------------------------#

# --- Ponto de Entrada e Lógica Principal ---
limitGeometria = ee.FeatureCollection(param['assets']["semiarido2024"])
byYears = False # Controla se a exportação é anual ou consolidada

# Loop principal que itera sobre as camadas temáticas definidas em `lst_nameAsset`
for nameAsset in lst_nameAsset[:]:
    print(f"------ PROCESSING {nameAsset} --------")
    shp_tmp = ee.FeatureCollection(param['assets'][nameAsset])
    
    # --- Processamento para "Prioridade de Conservação" ---
    if 'prioridade-conservacao' in nameAsset:
        shp_tmp = shp_tmp.filter(ee.Filter.eq('import_bio', 'Extremamente Alta'))
        iterandoXanoImCruda(shp_tmp.filterBounds(limitGeometria.geometry()),
                              dict_name[nameAsset], 'ext-alta', True, byYears, False)

    # --- Processamento para "Reserva da Biosfera" (filtrado por zona) ---
    elif nameAsset == 'reserva_biosfera':
        lstPropResBio = list(set(shp_tmp.reduceColumns(ee.Reducer.toList(), ['zona']).get('list').getInfo()))
        for typeRes in lstPropResBio:
            shp_tmp_resBio = shp_tmp.filter(ee.Filter.eq('zona', typeRes))
            iterandoXanoImCruda(shp_tmp_resBio.filterBounds(limitGeometria.geometry()),
                                  dict_name[nameAsset], typeRes, True, byYears, False)

    # --- Processamento para "Unidades de Conservação" (filtrado por Tipo de Uso) ---
    elif nameAsset == 'UnidadesConservacao_S':
        for typeUso in lstTipoUso:
            shp_tmp_uso = shp_tmp.filter(ee.Filter.inList('TipoUso', typeUso))
            iterandoXanoImCruda(shp_tmp_uso.filterBounds(limitGeometria.geometry()),
                                  dict_name[nameAsset], dict_name[typeUso[0]], True, byYears, False)

    # --- Processamento para "Macro Regiões Hidrográficas" (filtrado por nome) ---
    elif nameAsset == 'macro_RH':
        for nmmacro in lstMacro:
            shp_tmp_macro = shp_tmp.filter(ee.Filter.eq('nm_macroRH', nmmacro))
            iterandoXanoImCruda(shp_tmp_macro.filterBounds(limitGeometria.geometry()),
                                  dict_name[nameAsset], dict_name[nmmacro], True, byYears, False)
    
    # --- Caso Geral: Processa a camada vetorial inteira sem sub-filtragem ---  
    else:
        iterandoXanoImCruda(shp_tmp.filterBounds(limitGeometria.geometry()),
                              dict_name.get(nameAsset, nameAsset), 'Caatinga', True, byYears, False)