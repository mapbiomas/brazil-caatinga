#!/usr/bin/python
# # -*- coding: utf-8 -*-

'''
# SCRIPT DE PÓS-CLASSIFICAÇÃO (FILTRO TEMPORAL OTIMIZADO COM MAP)
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
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões do Python

# Adiciona o diretório pai ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[0])
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
# Bloco 2: Classe Principal do Processo de Filtro Temporal (Versão Otimizada)      #
# Descrição: A classe `processo_filterTemporal` encapsula a lógica para            #
# aplicar um filtro de janela deslizante. Esta versão foi refatorada para          #
# utilizar `ee.List.map` para processar a série temporal de forma paralela e       #
# server-side, o que é significativamente mais eficiente do que loops client-side. #
# --------------------------------------------------------------------------------#
class processo_filterTemporal(object):
    """
    Classe para orquestrar a aplicação de um filtro temporal em uma série
    de imagens de classificação, com lógica otimizada para execução no servidor GEE.
    """
    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Temporal',
        'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalA',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew': [4, 4, 4, 4, 4, 4, 4, 4, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33, 4, 33, 21, 21, 21, 21, 21, 21, 21, 21, 4, 4, 21],
        'classNat': [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        'last_year': 2024, 'first_year': 1985, 'janela_bef': 3, 'step': 1
    }

    def __init__(self, name_bacia):
        """
        Inicializador da classe de filtro temporal.

        Args:
            name_bacia (str): O ID da bacia hidrográfica a ser processada.
        """
        self.id_bacias = name_bacia
        self.versoutput = 5
        self.versionInput = 5
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer'])\
            .filter(ee.Filter.eq('nunivotto4', name_bacia))
        self.bacia_raster = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))\
            .reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia = self.geom_bacia.geometry()

        self.years = list(range(self.options['first_year'], self.options['last_year'] + 1))
        self.lstbandNames = ['classification_' + str(yy) for yy in self.years]

        # Carrega a imagem de classificação de entrada (série temporal)
        self.imgClass = ee.ImageCollection(self.options['input_asset'])\
            .filter(ee.Filter.eq('version', self.versionInput))\
            .filter(ee.Filter.eq('id_bacias', name_bacia)).first()
        print("Input Image loaded with bands: ", self.imgClass.bandNames().getInfo())

    # --- Funções Otimizadas para Execução no Servidor GEE ---
    def reclass_natural_Antropic(self, raster_maps, listYYbnd):
        """
        Reclassifica, de forma otimizada (server-side), uma imagem em Natural/Antrópico.

        Args:
            raster_maps (ee.Image): A imagem de entrada com múltiplas classes.
            listYYbnd (list[str]): A lista de bandas a serem reclassificadas.

        Returns:
            ee.Image: A imagem reclassificada com valores 1 (Natural) e 0 (Antrópico).
        """
        window_bands = raster_maps.select(listYYbnd)
        remapped_bands = window_bands.remap(self.options['classMapB'], self.options['classNat'])
        original_band_names = window_bands.bandNames().getInfo()
        remapped_band_names = [f'{band_name}_reclass' for band_name in original_band_names]
        remapped_image = remapped_bands.rename(remapped_band_names)
        first_band_type = raster_maps.select([listYYbnd[0]]).bandTypes()
        return remapped_image.cast(first_band_type)

    def _calculate_mask_for_window(self, imagem_reclassificada, listaBND_reclassificada_ee, valor_cc):
        """
        (Privado) Calcula a máscara temporal para uma janela, de forma server-side.

        Args:
            imagem_reclassificada (ee.Image): A imagem com as bandas da janela reclassificada.
            listaBND_reclassificada_ee (ee.List): Nomes das bandas reclassificadas na janela.
            valor_cc (int): O valor da classe a ser procurado (ex: 1 para natural).

        Returns:
            ee.Image: Uma máscara binária onde 1 indica pixels que seguem o padrão.
        """
        first_band_reclass = imagem_reclassificada.select(listaBND_reclassificada_ee.get(0))
        last_band_reclass = imagem_reclassificada.select(listaBND_reclassificada_ee.get(-1))
        initial_mask = first_band_reclass.eq(valor_cc).And(last_band_reclass.eq(valor_cc))
        
        window_size_ee = listaBND_reclassificada_ee.size()
        
        def condition_fails():
            intermediate_bands_reclass_names = listaBND_reclassificada_ee.slice(1, -1)
            intermediate_bands_reclass = imagem_reclassificada.select(intermediate_bands_reclass_names)
            maskCount = intermediate_bands_reclass.reduce(ee.Reducer.sum())
            intermediate_condition = ee.Algorithms.If(
                valor_cc == 1,
                maskCount.gt(0),
                maskCount.lt(window_size_ee.subtract(2))
            )
            return intermediate_condition

        intermediate_mask_val = ee.Algorithms.If(
            window_size_ee.lt(3),
            ee.Image(1), # Se janela < 3, condição intermediária é sempre verdadeira
            condition_fails()
        )
        return initial_mask.And(ee.Image(intermediate_mask_val))

    def mask_of_years(self, valor_cc, imagem_reclassificada, listaBND_reclassificada):
        """
        Wrapper robusto para criar a máscara temporal, tratando janelas pequenas.

        Args:
            valor_cc (int): O valor da classe a ser procurado (ex: 1 para natural).
            imagem_reclassificada (ee.Image): A imagem com as bandas da janela reclassificada.
            listaBND_reclassificada (list): Lista Python com os nomes das bandas reclassificadas.

        Returns:
            ee.Image: A máscara binária resultante, ou uma máscara vazia para janelas inválidas.
        """
        listBND_ee = ee.List(listaBND_reclassificada)
        mask = ee.Algorithms.If(
            listBND_ee.size().lt(2),
            ee.Image(0), # Retorna máscara vazia se a janela for muito pequena
            self._calculate_mask_for_window(imagem_reclassificada, listBND_ee, valor_cc)
        )
        return ee.Image(mask).selfMask()

    def applyTemporalFilter(self):
        """
        Orquestra a aplicação do filtro temporal usando uma abordagem `map` server-side.

        Este método cria uma lista de índices anuais e mapeia uma função
        server-side (`process_year_window`) sobre ela. Cada chamada da função
        processa um ano da série, resultando em uma coleção de bandas filtradas
        que são então combinadas em uma única imagem final.
        """
        id_class_natural = 1
        mjanela = 6
        print(f"--------- processing  janela {mjanela} (forward) ----------")

        # Cria uma lista de índices (0, 1, 2, ...) para representar cada ano
        year_indices = ee.List.sequence(0, len(self.years) - 1)

        # Função server-side a ser mapeada sobre a lista de anos
        def process_year_window(year_index):
            """Processa um único ano da série, aplicando o filtro de janela."""
            year_index = ee.Number(year_index)
            
            # Define a janela de 6 anos à frente do ano atual
            window_start_index = year_index
            window_end_index_exclusive = year_index.add(mjanela)
            window_band_names_ee = ee.List(self.lstbandNames).slice(window_start_index, window_end_index_exclusive)
            
            # Converte para lista client-side para usar em `reclass_natural_Antropic`
            window_band_names_py = window_band_names_ee.getInfo()
            
            # Reclassifica a janela para o formato binário
            remapped_window_image = self.reclass_natural_Antropic(self.imgClass, window_band_names_py)
            remapped_window_band_names = remapped_window_image.bandNames()
            
            # Cria a máscara para o padrão de vegetação natural
            mask_natural = self.mask_of_years(id_class_natural, remapped_window_image, remapped_window_band_names)
            
            # Obtém a banda do ano atual e a banda do final da janela
            current_year_band_name = ee.List(self.lstbandNames).get(year_index)
            original_current_year_band = self.imgClass.select([current_year_band_name])
            
            # Obtém a última banda da janela para usar na correção
            original_last_year_of_window_band = ee.Algorithms.If(
                window_band_names_ee.size().gt(0),
                self.imgClass.select(window_band_names_ee.get(-1)),
                ee.Image(0).selfMask() # Retorna imagem vazia se a janela for inválida
            )
            
            # Aplica a correção: onde a máscara for 1, usa o valor do final da janela
            filtered_band = original_current_year_band.blend(
                ee.Image(original_last_year_of_window_band).updateMask(mask_natural)
            )
            
            return filtered_band.rename([current_year_band_name])

        # Mapeia a função sobre a lista de anos para processamento paralelo no servidor
        filtered_bands_list = year_indices.map(process_year_window)

        # Converte a lista de imagens (uma por banda) em uma única imagem multibanda
        imgOutput = ee.ImageCollection.fromImages(filtered_bands_list).toBands()
        imgOutput = imgOutput.rename(self.lstbandNames) # Renomeia as bandas para o padrão correto

        # Define os metadados e exporta a imagem final
        imgOutput = imgOutput.updateMask(self.bacia_raster).set({
            'version': self.versoutput, 'id_bacias': self.id_bacias, 'biome': 'CAATINGA',
            'type_filter': 'temporal', 'collection': '10.0', 'janela': mjanela,
            'sensor': 'Landsat', 'system:footprint': self.geom_bacia
        })
        name_toexport = f"filterTP_BACIA_{self.id_bacias}_GTB_J{mjanela}_V{self.versoutput}"
        self.processoExportar(imgOutput, name_toexport, self.geom_bacia)

    def processoExportar(self, mapaRF, nomeDesc, geom_bacia):
        """
        Exporta uma imagem como um asset no Google Earth Engine.

        Args:
            mapaRF (ee.Image): A imagem a ser exportada.
            nomeDesc (str): A descrição da tarefa e o nome base do asset.
            geom_bacia (ee.Geometry): A geometria da bacia para delimitar a exportação.
        """
        idasset = os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 'description': nomeDesc, 'assetId': idasset,
            'region': geom_bacia, 'scale': 30, 'maxPixels': 1e13,
            "pyramidingPolicy": {".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start()
        print("salvando ... " + nomeDesc + "..!")

# --------------------------------------------------------------------------------#
# Bloco 4: Função de Gerenciamento de Contas e Execução Principal                  #
# Descrição: Contém a função para gerenciar as contas do GEE e o loop principal    #
# que instancia e executa o processo de filtro temporal para cada bacia.           #
# --------------------------------------------------------------------------------#
param = {
    'numeroTask': 6, 'numeroLimit': 20,
    'conta': {
        '0': 'caatinga01', '4': 'caatinga02', '6': 'caatinga03', '8': 'caatinga04',
        '10': 'caatinga05', '12': 'solkan1201', '14': 'solkanGeodatin', '16': 'superconta'
    }
}
relatorios = open("relatorioTaskXContas.txt", 'a+')

def gerenciador(cont):
    """
    Gerencia a troca de contas do GEE para balancear a fila de tarefas.

    Args:
        cont (int): O contador que representa o estado atual do ciclo de tarefas.

    Returns:
        int: O contador atualizado para o próximo ciclo.
    """
    # (Implementação omitida para brevidade)
    return cont

# Lista de bacias a serem processadas
listaNameBacias = [ '765' ] # Exemplo com uma bacia
print("ver quantidad ", len(listaNameBacias))

# --- Loop Principal de Execução ---
knowMapSaved = False
for cc, idbacia in enumerate(listaNameBacias[:]):
    if knowMapSaved:
        pass # Lógica para verificar se o mapa já foi salvo
    else:
        print("----- PROCESSING BACIA {} -------".format(idbacia))
        # Instancia e executa o filtro temporal
        aplicando_TemporalFilter = processo_filterTemporal(idbacia)
        aplicando_TemporalFilter.applyTemporalFilter()