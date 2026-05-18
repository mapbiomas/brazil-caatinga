import ee
import os
import sys
from pathlib import Path
import collections.abc

# Ensure collections.Callable is available for older Python versions if needed,
# though GEE environments typically use Python 3 where it's in collections.abc
collections.Callable = collections.abc.Callable

# --- Configurações Iniciais ---
# Assegura que o módulo gee_tools está acessível.
# Se gee_tools for um módulo personalizado, você pode precisar ajustar este caminho.
# Para este exemplo, vou presumir que gee_tools está no mesmo diretório ou em um diretório acessível via PYTHONPATH.
try:
    from gee_tools import get_current_account, get_project_from_account, switch_user, tasks
except ImportError:
    print("Erro: O módulo 'gee_tools' não foi encontrado. Certifique-se de que está no PYTHONPATH ou no mesmo diretório.")
    print("Você pode precisar adicionar o diretório pai ao sys.path, se 'gee_tools' estiver lá.")
    # Exemplo: sys.path.append(str(Path(os.getcwd()).parents[1]))
    sys.exit(1)

# --- Gerenciamento da Conta GEE ---
def initialize_ee_account(account_name=None):
    """
    Inicializa a API do Earth Engine para a conta especificada ou a conta atual.
    """
    try:
        if account_name:
            switch_user(account_name)
            project_id = get_project_from_account(account_name)
            print(f"Conta selecionada: {account_name}, Projeto: {project_id}")
        else:
            project_id = get_current_account()
            print(f"Projeto selecionado: {project_id} (conta atual)")

        ee.Initialize(project=project_id)
        print('O pacote Earth Engine foi inicializado com sucesso!')
    except ee.EEException as e:
        print(f'Falha na inicialização do pacote Earth Engine: {e}')
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado durante a inicialização do Earth Engine: {e}")
        sys.exit(1)

# --- Definição de Parâmetros ---
# Centralize todos os parâmetros em um dicionário para fácil configuração.
# Use nomes de variáveis claros e consistentes.
PARAMETERS = {
    'input_asset_collection': 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification',
    'input_transition_collection': 'projects/mapbiomas-workspace/COLECAO8/transicao', # Não usado no script fornecido
    'assets': {
        "Assentamento_Brasil": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
        "BR_ESTADOS_2022": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
        "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
        "br_estados_shp": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
        "BR_Municipios_2022": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
        "BR_Pais_2022": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
        "Im_bioma_250": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
        'vetor_biomas_250': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
        'biomas_250_rasters': 'projects/mapbiomas-workspace/AUXILIAR/RASTER/Bioma250mil',
        "Sigef_Brasil": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sigef_Brasil",
        "Sistema_Costeiro_Marinho": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sistema_Costeiro_Marinho",
        "aapd": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/aapd",
        "areas_Quilombolas": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/areas_Quilombolas",
        "buffer_pts_energias": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/buffer_pts_energias",
        "energias-dissolve-aneel": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/energias-dissolve-aneel",
        "florestaspublicas": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/florestaspublicas",
        "imovel_certificado_SNCI_br": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/imovel_certificado_SNCI_br",
        "macro_RH": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
        "meso_RH": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/meso_RH",
        "micro_RH": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/micro_RH",
        "pnrh_asd": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_asd",
        "prioridade-conservacao": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/prioridade-conservacao-caatinga-ibama",
        "prioridade-conservacao-V1": "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V1",
        "prioridade-conservacao-V2": "users/solkancengine17/shps_public/prioridade-conservacao-semiarido_V2",
        "tis_poligonais_portarias": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/tis_poligonais_portarias",
        "transposicao-cbhsf": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/transposicao-cbhsf",
        "nucleos_desertificacao": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
        "UnidadesConservacao_S": "projects/mapbiomas-workspace/AUXILIAR/areas-protegidas",
        "unidade_gerenc_RH_SNIRH_2020": "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
        "reserva_biosfera": "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
        "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
        'semiarido': 'users/mapbiomascaatinga04/semiarido_rec',
        "irrigacao": 'projects/ee-mapbiomascaatinga04/assets/polos_irrigaaco_atlas',
        "energiasE": 'projects/ee-mapbiomascaatinga04/assets/energias_renovaveis',
        "bacia_sao_francisco": 'users/solkancengine17/shps_public/bacia_sao_francisco',
        "matopiba": 'projects/mapbiomas-fogo/assets/territories/matopiba'
    },
    'asset_vector_input': 'users/data_sets_solkan/SHPs/APA_R_Capivara_limite',
    'mapbiomas_collection_version': '10.0',
    'output_version': '0-7',
    'biome_filter': 'CAATINGA',
    'source_name': 'geodatin',
    'scale_meters': 30,
    'end_year': 2024,
    'drive_folder': 'AREA-CAATINGA-CORR',
    'mapbiomas_classes_to_consider': [3, 4, 12, 15, 18, 21, 22, 33, 29], # Não usado no script fornecido
    'max_tasks_per_account': 6,
    'account_rotation_limit': 40, # Limite de chamadas do gerenciador de contas
    'accounts': {
        '0': 'caatinga01',
    },
}

# Variáveis globais para o relatório e controle de conta
RELATORIO_FILE = "relatorio_tarefas_gee.txt"
CURRENT_ACCOUNT_INDEX = 0

# --- Mapeamentos e Dicionários ---
# Consolidar mapeamentos para evitar repetição.
NAME_MAPPING = {
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
    "semiarido2024": "limite-Semiarido-2024",
    "transposicao-cbhsf": "transposicao-cbhsf",
}

IRRIGATION_AREAS = {
    "Jaíba": "Jaiba",
    "Petrolina / Juazeiro": "PetroJuazei",
    "Jaguaribe": "Jaguaribe",
    "Mucugê-Ibicoara": "MucuIbico",
    "Oeste Baiano": "OestBaiano"
}

SAO_FRANCISCO_BASIN_IDS = {
    '196': "Submedio-Sao-Francisco",
    '197': "Medio-Sao-Francisco",
    '205': "Alto-Sao-Francisco",
    '219': "Baixo-Sao-Francisco"
}

MACRO_RH_LIST = [
    "PARNAÍBA", "ATLÂNTICO NORDESTE ORIENTAL",
    "SÃO FRANCISCO", "ATLÂNTICO LESTE"
]

MESO_RH_MAPPING = {
    "PARNAÍBA": ["Alto Parnaíba", "Médio Parnaíba", "Baixo Parnaíba"],
    "ATLÂNTICO NORDESTE ORIENTAL": [
        "Jaguaribe", "Litoral do Ceará", "Litoral do Rio Grande do Norte e Paraíba",
        "Piancó-Piranhas-Açu", "Litoral de Pernambuco e Alagoas"],
    "SÃO FRANCISCO": ["Médio São Francisco", "Submédio São Francisco", "Baixo São Francisco"],
    "ATLÂNTICO LESTE": ["Contas", "Itapicuru/Paraguaçu", "Jequitinhonha/Pardo", "Vaza-Barris"]
}

MESO_RH_SIGLA_MAPPING = {
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

BIOME_CODE_MAPPING = {
    '1': '', # Amazônia
    '2': '_Caatinga',
    '3': '', # Cerrado
    '4': '', # Mata Atlântica
    '5': '', # Pampa
    '6': '', # Pantanal
}

STATE_CODE_MAPPING = {
    '21': 'MARANHÃO', '22': 'PIAUÍ', '23': 'CEARÁ', '24': 'RIO GRANDE DO NORTE',
    '25': 'PARAÍBA', '26': 'PERNAMBUCO', '27': 'ALAGOAS', '28': 'SERGIPE',
    '29': 'BAHIA', '31': 'MINAS GERAIS', '32': 'ESPÍRITO SANTO'
}

# Lista de ativos para processar (deve ser configurável)
ASSETS_TO_PROCESS = [
    # 'Assentamento_Brasil',
    # "nucleos_desertificacao",
    # "UnidadesConservacao_S", #"unidade_gerenc_RH_SNIRH_2020",
    # 'areas_Quilombolas',
    # "macro_RH", "meso_RH", #'micro_RH',
    # 'prioridade-conservacao-V1',
    # 'prioridade-conservacao-V2',
    # 'tis_poligonais_portarias',
    # "reserva_biosfera",
    # "energiasE",
    # "irrigacao",
    # "bacia_sao_francisco",
    "matopiba",
    "micro_RH",
    "transposicao-cbhsf"
]

# --- Funções Auxiliares ---
def get_unique_elements(input_list):
    """Retorna elementos únicos de uma lista, mantendo a ordem de primeira ocorrência."""
    seen = set()
    result = []
    for item in input_list:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def convert_to_feature_collection(item):
    """
    Converte um item de dicionário (resultante de reduceRegion) para uma Feature.
    Usado no mapeamento de resultados do GEE.
    """
    item = ee.Dictionary(item)
    # Certifique-se de que 'classe' e 'sum' existem antes de tentar acessá-los
    return ee.Feature(None).set({
        'classe': item.get('classe'),
        'area': item.get('sum')
    })

def calculate_area(image, pixel_area_image, geom_fc):
    """
    Calcula a área de classes dentro de uma FeatureCollection.
    Otimizado para usar reduceRegion com agrupamento.
    """
    # Adiciona a banda de classificação à imagem de área de pixel
    image_with_class = pixel_area_image.addBands(image.rename('classe'))

    # Configura o redutor para somar e agrupar por classe
    reducer = ee.Reducer.sum().group(1, 'classe') # 1 indica o índice da banda 'classe'

    # Opções para reduceRegion
    reduce_region_options = {
        'reducer': reducer,
        'geometry': geom_fc,
        'scale': PARAMETERS['scale_meters'],
        'bestEffort': True,
        'maxPixels': 1e13
    }

    # Aplica reduceRegion
    areas = image_with_class.reduceRegion(**reduce_region_options)

    # Converte a lista de grupos para uma FeatureCollection
    areas_list = ee.List(areas.get('groups'))
    feature_collection = ee.FeatureCollection(
        areas_list.map(convert_to_feature_collection)
    )
    return feature_collection

def export_to_drive(feature_collection, task_name):
    """
    Exporta uma FeatureCollection para o Google Drive.
    """
    export_options = {
        'collection': feature_collection,
        'description': task_name,
        'folder': PARAMETERS['drive_folder']
    }
    task = ee.batch.Export.table.toDrive(**export_options)
    task.start()
    print(f"Exportando tarefa '{task_name}' para o Drive...")

def manage_tasks_and_accounts():
    """
    Gerencia a alternância de contas GEE e verifica o status das tarefas.
    Retorna True se puder continuar, False se atingir o limite.
    """
    global CURRENT_ACCOUNT_INDEX
    accounts_list = list(PARAMETERS['accounts'].keys())

    if CURRENT_ACCOUNT_INDEX >= PARAMETERS['account_rotation_limit']:
        print("Limite de rotação de contas atingido. Encerrando script.")
        return False

    if str(CURRENT_ACCOUNT_INDEX) in accounts_list:
        account_name = PARAMETERS['accounts'][str(CURRENT_ACCOUNT_INDEX)]
        initialize_ee_account(account_name)
        with open(RELATORIO_FILE, 'a') as f:
            f.write(f"\n--- Conta de: {account_name} ---\n")
            current_tasks = tasks(n=PARAMETERS['max_tasks_per_account'], return_list=True)
            for task_info in current_tasks:
                f.write(f"{task_info}\n")
    else:
        # Se a conta atual não estiver na lista, apenas avança para a próxima
        # ou mantém a conta atual se não houver mais para alternar.
        print(f"Conta no índice {CURRENT_ACCOUNT_INDEX} não definida nos parâmetros. Mantendo conta atual.")

    CURRENT_ACCOUNT_INDEX += 1
    return True

# --- Lógica Principal de Processamento ---
def process_mapbiomas_data(limit_feature_collection, sub_region_name, macro_region_name,
                          is_coverage_analysis, process_by_year, apply_remap):
    """
    Processa os dados do MapBiomas para a geometria fornecida,
    calculando áreas e exportando os resultados.
    """
    # Remapeamento de classes (se necessário)
    class_map_biomas = [3, 4, 5, 6, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 62]
    new_classes = [3, 4, 3, 3, 3, 12, 12, 15, 18, 18, 18, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 18, 33, 33, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 4, 12, 18]
    remap_suffix = '_sinRM' if not apply_remap else '_remap'

    # Carrega as geometrias auxiliares
    caatinga_biome_geometry = (ee.FeatureCollection(PARAMETERS['assets']["vetor_biomas_250"])
                               .filter(ee.Filter.eq('CD_Bioma', 2)).geometry())
    brazilian_states_shp = ee.FeatureCollection(PARAMETERS['assets']["br_estados_shp"])
    brazilian_states_raster = ee.Image(PARAMETERS['assets']["br_estados_raster"])

    # Máscara do bioma Caatinga
    mask_biome = ee.Image(PARAMETERS['assets']["biomas_250_rasters"]).eq(2)

    # Máscara da geometria de entrada
    raster_mask_polygon = limit_feature_collection.reduceToImage(['id_codigo'], ee.Reducer.first())

    if is_coverage_analysis:
        print("Carregando imagem de Cobertura da Coleção 10.0...")
        # Carrega a coleção de imagens e aplica as máscaras globais
        map_image_collection = (ee.ImageCollection(PARAMETERS['input_asset_collection'])
                                .filter(ee.Filter.eq('version', PARAMETERS['output_version']))
                                .mosaic()
                                .updateMask(mask_biome)
                                .updateMask(raster_mask_polygon))

        pixel_area_image_base = (ee.Image.pixelArea().divide(10000) # Converter para hectares/km²
                                 .updateMask(mask_biome)
                                 .updateMask(raster_mask_polygon))

        # Estados brasileiros na Caatinga (ou próximos)
        relevant_state_codes = [21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32]

        for state_code in relevant_state_codes:
            print(f"Processando Estado: {STATE_CODE_MAPPING.get(str(state_code), 'Desconhecido')} (Código: {state_code})")

            # Máscara raster para o estado atual
            state_raster_mask = brazilian_states_raster.eq(state_code)

            # Geometria do estado (vetor)
            state_shp_geometry = (brazilian_states_shp
                                  .filter(ee.Filter.eq('CD_GEOCUF', str(state_code)))
                                  .geometry())

            # Interseção da geometria de entrada com o bioma e o estado
            processing_geometry = (caatinga_biome_geometry
                                   .intersection(state_shp_geometry)
                                   .intersection(limit_feature_collection.geometry()))

            # Certifica-se de que a geometria resultante tem uma área válida antes de prosseguir
            # Essa verificação pode ser custosa, então considere se é realmente necessária.
            # Se for, descomente e ajuste o threshold (0.01) conforme sua necessidade.
            # area_geom = processing_geometry.area(PARAMETERS['scale_meters']).getInfo()
            # if area_geom == 0:
            #     print(f"Área de interseção para o estado {STATE_CODE_MAPPING.get(str(state_code))} é zero. Pulando.")
            #     continue

            # Aplica máscara do estado às imagens
            map_image_state = map_image_collection.updateMask(state_raster_mask)
            pixel_area_image_state = pixel_area_image_base.updateMask(state_raster_mask)

            # FeatureCollection para acumular resultados se não for por ano
            all_years_areas = ee.FeatureCollection([])

            for year in range(1985, PARAMETERS['end_year'] + 1):
                band_name = f"classification_{year}"
                current_year_image = map_image_state.select(band_name)

                if apply_remap:
                    current_year_image = current_year_image.remap(class_map_biomas, new_classes)
                    print(f"    << Remapeando para o ano {year} >>")

                # Calcula a área
                area_results = calculate_area(current_year_image, pixel_area_image_state, processing_geometry)

                # Adiciona propriedades aos resultados
                area_results = area_results.map(lambda feat: feat.set({
                    'year': year,
                    'nomeVetor': PARAMETERS['asset_vector_input'].split('/')[-1].replace('_limite', ''), # Nome do vetor principal
                    'region': sub_region_name,
                    'sub_region': macro_region_name,
                    'estado_name': STATE_CODE_MAPPING.get(str(state_code), 'Desconhecido'),
                    'estado_codigo': state_code
                }))

                if process_by_year:
                    # Exporta por ano e por estado
                    task_file_name = (f"area_class_{sub_region_name}_{macro_region_name}_"
                                      f"codEst_{state_code}_{year}{remap_suffix}")
                    export_to_drive(area_results, task_file_name)
                    # Gerenciar contas e tarefas após cada exportação
                    if not manage_tasks_and_accounts():
                        return ee.FeatureCollection([]), False
                else:
                    # Acumula os resultados para exportação única por estado
                    all_years_areas = all_years_areas.merge(area_results)

            if not process_by_year:
                # Exporta todos os anos para o estado de uma vez
                task_file_name = (f"area_class_{sub_region_name}_{macro_region_name}_"
                                  f"codEst_{state_code}{remap_suffix}")
                export_to_drive(all_years_areas, task_file_name)
                # Gerenciar contas e tarefas após cada exportação de estado
                if not manage_tasks_and_accounts():
                    return ee.FeatureCollection([]), False

    return ee.FeatureCollection([]), False # Indica que a exportação já foi iniciada internamente

# --- Execução Principal do Script ---
if __name__ == "__main__":
    # Inicializa a conta GEE antes de qualquer operação GEE
    initialize_ee_account()

    # Prepara o arquivo de relatório
    with open(RELATORIO_FILE, 'w') as f:
        f.write("Relatório de Tarefas do Google Earth Engine\n")
        f.write("-----------------------------------------\n")

    # Define o nome base para os arquivos de saída
    base_vector_name = PARAMETERS['asset_vector_input'].split('/')[-1].replace('_limite', '')
    suffix = '_cob' if True else '_trans' # 'paraCobertura' do script original, aqui fixado para cobertura

    # Carrega a geometria limite da Caatinga ou Semiárido
    select_caatinga = True # Pode ser um parâmetro
    if select_caatinga:
        limit_geometry_fc = ee.FeatureCollection(PARAMETERS['assets']["vetor_biomas_250"]).filter(ee.Filter.eq("CD_Bioma", 2))
        biome_suffix = BIOME_CODE_MAPPING.get('2', '_Caatinga')
    else:
        limit_geometry_fc = ee.FeatureCollection(PARAMETERS['assets']["semiarido2024"])
        biome_suffix = '_SemiArido2024' # Ou um nome mais genérico

    # Adiciona uma propriedade 'id_codigo' para reduceToImage
    limit_geometry_fc = limit_geometry_fc.map(lambda feat: feat.set('id_codigo', 1))
    print(f"Limite selecionado: {limit_geometry_fc.size().getInfo()} features.")

    # Processamento de cada ativo na lista ASSETS_TO_PROCESS
    for asset_name in ASSETS_TO_PROCESS:
        print(f"\n--- PROCESSANDO ATIVO: {asset_name} ---")

        asset_fc = ee.FeatureCollection(PARAMETERS['assets'][asset_name])
        print(f"Total de features em {asset_name}: {asset_fc.size().getInfo()}")
        asset_fc = asset_fc.map(lambda feat: feat.set('id_codigo', 1))

        # Filtra o asset pela geometria limite da Caatinga/Semiárido
        filtered_asset_fc = asset_fc.filterBounds(limit_geometry_fc.geometry())
        print(f"Features de {asset_name} dentro do limite: {filtered_asset_fc.size().getInfo()}")

        if filtered_asset_fc.size().getInfo() == 0:
            print(f"Nenhuma feature de {asset_name} encontrada dentro do limite. Pulando.")
            continue

        # Lógica condicional para diferentes tipos de ativos
        if asset_name in ['prioridade-conservacao-V1', 'prioridade-conservacao-V2']:
            shp_filtered = filtered_asset_fc.filter(ee.Filter.eq('import_bio', 'Extremamente Alta'))
            print(f"Prioridade de conservação (Extremamente Alta): {shp_filtered.size().getInfo()} features.")
            process_mapbiomas_data(shp_filtered, NAME_MAPPING[asset_name], 'ext-alta', True, False, False)

        elif asset_name == 'reserva_biosfera':
            # Coleta as zonas únicas
            unique_zones = filtered_asset_fc.reduceColumns(ee.Reducer.toList(), ['zona']).get('list').getInfo()
            unique_zones = get_unique_elements(unique_zones)
            print(f"Zonas de Reserva da Biosfera: {unique_zones}")
            for zone in unique_zones:
                shp_zone = filtered_asset_fc.filter(ee.Filter.eq('zona', zone))
                print(f"Processando zona '{zone}': {shp_zone.size().getInfo()} features.")
                process_mapbiomas_data(shp_zone, NAME_MAPPING[asset_name], zone, True, False, False)

        elif asset_name == 'UnidadesConservacao_S':
            # Tipos de uso (Proteção Integral e Uso Sustentável)
            usage_types = [["Proteção Integral", "Proteção integral"], ["Uso Sustentável"]]
            for types in usage_types:
                shp_usage = filtered_asset_fc.filter(ee.Filter.inList('TipoUso', types))
                # Usa o primeiro tipo como nome para o arquivo, se existir
                type_name = NAME_MAPPING.get(types[0], types[0]) if types else "UnknownType"
                print(f"Processando Tipo de Uso '{type_name}': {shp_usage.size().getInfo()} features.")
                process_mapbiomas_data(shp_usage, NAME_MAPPING[asset_name], type_name, True, False, False)

        elif asset_name == 'macro_RH':
            for macro_rh_name in MACRO_RH_LIST:
                shp_macro_rh = filtered_asset_fc.filter(ee.Filter.eq('nm_macroRH', macro_rh_name))
                print(f"Processando Macro Região Hidrográfica '{macro_rh_name}': {shp_macro_rh.size().getInfo()} features.")
                process_mapbiomas_data(shp_macro_rh, NAME_MAPPING[asset_name], NAME_MAPPING[macro_rh_name], True, False, False)

        elif asset_name == 'meso_RH':
            for macro_rh_name, meso_list in MESO_RH_MAPPING.items():
                if macro_rh_name in MACRO_RH_LIST: # Garante que estamos nos focando nas macros relevantes
                    for meso_rh_name in meso_list:
                        shp_meso_rh = filtered_asset_fc.filter(ee.Filter.eq('nm_mesoRH', meso_rh_name))
                        meso_sigla = MESO_RH_SIGLA_MAPPING[macro_rh_name][meso_rh_name]
                        print(f"Processando Meso Região Hidrográfica '{meso_rh_name}' ({meso_sigla}): {shp_meso_rh.size().getInfo()} features.")
                        process_mapbiomas_data(shp_meso_rh, NAME_MAPPING[asset_name], meso_sigla, True, False, False)

        elif asset_name == "irrigacao":
            for irrig_name, irrig_code in IRRIGATION_AREAS.items():
                shp_irrigation = filtered_asset_fc.filter(ee.Filter.eq('Polo_irrig', irrig_name))
                print(f"Processando Área de Irrigação '{irrig_name}': {shp_irrigation.size().getInfo()} features.")
                process_mapbiomas_data(shp_irrigation, asset_name, irrig_code, True, False, False)

        elif asset_name == "bacia_sao_francisco":
            for sf_id, sf_name in SAO_FRANCISCO_BASIN_IDS.items():
                shp_sf_basin = filtered_asset_fc.filter(ee.Filter.eq('id', int(sf_id)))
                print(f"Processando Bacia do São Francisco '{sf_name}': {shp_sf_basin.size().getInfo()} features.")
                process_mapbiomas_data(shp_sf_basin, asset_name, sf_name, True, False, False)

        else:
            # Caso geral para outros ativos
            print(f"Processando ativo geral '{asset_name}'.")
            process_mapbiomas_data(filtered_asset_fc, NAME_MAPPING.get(asset_name, asset_name),
                                   'Caatinga', True, False, False)

    print("\nProcessamento de todas as áreas concluído!")