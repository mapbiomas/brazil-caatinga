#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE PÓS-CLASSIFICAÇÃO (FILTRO TEMPORAL)
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
collections.Callable = collections.abc.Callable # Garante compatibilidade com versões do Python

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

# ---------------------------------------------------------------------------------#
# Bloco 2: Classe Principal do Processo de Filtro Temporal                         #
# Descrição: A classe `processo_filterTemporal` encapsula a lógica para            #
# aplicar um filtro de janela deslizante em uma série temporal de mapas. O         #
# objetivo é corrigir classificações temporalmente inconsistentes, como um         #
# pixel classificado como vegetação nativa em apenas um ano, cercado por           #
# anos de uso antrópico.                                                           #
# ---------------------------------------------------------------------------------#
class processo_filterTemporal(object):
    """
    Classe para orquestrar a aplicação de um filtro temporal em uma série
    de imagens de classificação para uma bacia hidrográfica específica.
    """
    # Dicionário de parâmetros que centraliza os caminhos de assets e configurações
    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Temporal',
        'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalA',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew': [4, 4, 4, 4, 4, 4, 4, 4, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33, 4, 33, 21, 21, 21, 21, 21, 21, 21, 21, 4, 4, 21],
        'classNat': [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        'last_year': 2024, 'first_year': 1985,
        'janela_input': 4, 'janela_output': 5, 'step': 1
    }

    def __init__(self, name_bacia):
        """
        Inicializador da classe de filtro temporal.

        Args:
            name_bacia (str): O ID da bacia hidrográfica a ser processada.
        """
        self.id_bacias = name_bacia
        self.versoutput = 10
        self.versionInput = 10
        # Carrega a geometria da bacia e a converte para uma máscara raster
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer'])\
            .filter(ee.Filter.eq('nunivotto4', name_bacia))
        self.bacia_raster = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))\
            .reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia = self.geom_bacia.geometry()

        # Define listas de anos e nomes de bandas para iteração (normal e inversa)
        self.years = list(range(self.options['first_year'], self.options['last_year'] + 1))
        self.lstbandNames = ['classification_' + str(yy) for yy in self.years]
        self.yearsInv = list(range(self.options['last_year'], self.options['first_year'] - 1, -1))
        self.lstbandsInv = ['classification_' + str(yy) for yy in self.yearsInv]

        # Carrega a imagem de classificação de entrada (série temporal)
        self.imgClass = ee.ImageCollection(self.options['input_asset'])\
            .filter(ee.Filter.eq('version', self.versionInput))\
            .filter(ee.Filter.eq('id_bacias', name_bacia))\
            .first()

        # Cria uma versão reclassificada da imagem (Natural=1, Antrópico=0) para análise
        self.imgReclass = ee.Image().byte()
        for yband in self.lstbandNames:
            img_tmp = self.imgClass.select(yband).remap(self.options['classMapB'], self.options['classNat'])
            self.imgReclass = self.imgReclass.addBands(img_tmp.rename(yband))
        self.imgReclass = self.imgReclass.select(self.lstbandNames)
        
        # Gera a lista de janelas de anos para a iteração do filtro
        self.colectAnos = [self.mapeiaAnos(ano, self.options['janela_output'], self.yearsInv) for ano in self.yearsInv]

    # --- Funções de Regra para Construção da Janela Deslizante ---
    def regra_ultima(self, jan, delt, lstYears):
        """Constrói a janela para o último ano da série temporal."""
        return [lstYears[-3], lstYears[-1], lstYears[-2]]

    # --- (Outras funções de regra para casos de borda foram omitidas para brevidade) ---

    def mapeiaAnos(self, ano, janela, anos):
        """
        Gera a lista de bandas para a janela deslizante de um ano específico.

        Esta função determina quais anos (e, consequentemente, quais bandas)
        compõem a janela de análise para um `ano` central, lidando com os
        casos de borda no início e no fim da série temporal.

        Args:
            ano (int): O ano central da janela.
            janela (int): O tamanho da janela (ex: 3, 4, 5 anos).
            anos (list[int]): A lista completa de anos da série.

        Returns:
            list[str]: Uma lista com os nomes das bandas que compõem a janela.
        """
        lsBandAnos = ['classification_' + str(item) for item in anos]
        indice = anos.index(ano)
        delta = int(janela / 2)
        resto = int(janela % 2)
        
        # Lógica para diferentes tamanhos de janela e casos de borda
        if janela == 3:
            if ano == anos[-1]:
                return self.regra_ultima(janela, delta, lsBandAnos)
            else:
                return lsBandAnos[indice - delta: indice + delta + resto]
        # --- (Lógica para outras janelas omitida para brevidade) ---
        else:
            return lsBandAnos[indice - 1: indice + 2 * delta]

    # --- Funções de Máscara para Detecção de Padrões Temporais ---
    def mask_3_years(self, valor, imagem):
        """
        Detecta e mascara o padrão [A, não A, A] em uma janela de 3 anos.

        Args:
            valor (int): O valor da classe a ser procurada (ex: 1 para vegetação natural).
            imagem (ee.Image): Uma imagem de 3 bandas representando a janela temporal.

        Returns:
            ee.Image: Uma máscara binária onde 1 indica pixels que seguem o padrão.
        """
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
            imagem.select([1]).neq(valor)).And(
            imagem.select([2]).eq(valor)).unmask(0)
        return mmask.eq(1)

    # --- (Funções mask_4_years, mask_5_years, etc., omitidas para brevidade) ---

    def reclass_natural_Antropic(self, raster_maps, listYYbnd):
        """
        Converte uma imagem de classificação em uma imagem binária (Natural vs. Antrópico).

        Args:
            raster_maps (ee.Image): A imagem de entrada com múltiplas classes.
            listYYbnd (list[str]): A lista de bandas a serem reclassificadas.

        Returns:
            ee.Image: A imagem reclassificada com valores 1 (Natural) e 0 (Antrópico).
        """
        # (Implementação omitida, pois a reclassificação já é feita no __init__)
        pass
    
    def applyTemporalFilter(self, showinterv):
        """
        Aplica o filtro temporal iterativo na série temporal de classificações.

        Este é o método principal que percorre a série temporal, identifica
        padrões inconsistentes usando uma janela deslizante e corrige os pixels
        no mapa de classificação original.

        Args:
            showinterv (bool): Se True, imprime as janelas de anos utilizadas em cada iteração.
        """
        imgOutput = ee.Image().byte()
        id_class = 1  # Foco em corrigir a classe de vegetação natural
        
        if self.options['janela_output'] == 3:
            rasterbefore = ee.Image().byte()
            for cc, lstyear in enumerate(self.colectAnos):
                # O loop começa a partir da segunda iteração para ter um pixel central
                if cc > 0:
                    band_C1 = lstyear[1] # A banda central da janela
                    if cc == 1:
                        # Na primeira janela, usa a imagem reclassificada diretamente
                        imgtmp_mask = self.mask_3_years(id_class, self.imgReclass.select(lstyear))
                    else:
                        # Nas janelas seguintes, usa o resultado da iteração anterior
                        imgComposta = rasterbefore.addBands(self.imgReclass.select(lstyear[1:]))
                        imgtmp_mask = self.mask_3_years(id_class, imgComposta)
                    
                    # Atualiza a imagem reclassificada com a correção
                    rasterbefore = self.imgReclass.select(band_C1).where(imgtmp_mask.eq(1), imgtmp_mask)
                    
                    # Usa a máscara para corrigir a imagem de classificação ORIGINAL
                    map_change_year = self.imgClass.select(band_C1).blend(
                        imgtmp_mask.selfMask().multiply(self.imgClass.select(lstyear[2]))
                    ).rename(band_C1)
                    imgOutput = imgOutput.addBands(map_change_year)
                elif cc == 0:
                    # Adiciona o último ano da série (não filtrado) para iniciar a imagem de saída
                    imgOutput = imgOutput.addBands(self.imgClass.select(self.lstbandNames[-1]))
        
        # --- (Lógica para outras janelas (4, 5, 6) foi omitida para brevidade) ---
        
        # Compila a imagem final com todas as bandas corrigidas
        imClass = ee.Image().byte()
        for bndYY in self.lstbandNames:
            imClass = imClass.addBands(imgOutput.select(bndYY))
        imClass = imClass.select(self.lstbandNames[:])

        # Define os metadados e exporta o resultado
        imClass = imClass.updateMask(self.bacia_raster).set({
            'version': self.versoutput, 'id_bacias': self.id_bacias, 'biome': 'CAATINGA',
            'type_filter': 'temporal', 'collection': '10.0', 'janela': self.options['janela_output'],
            'sensor': 'Landsat', 'system:footprint': self.geom_bacia
        })
        name_toexport = f"filterTP_BACIA_{self.id_bacias}_GTB_J{self.options['janela_output']}_V{self.versoutput}"
        self.processoExportar(imClass, name_toexport, self.geom_bacia)

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
    # (Implementação da função omitida para brevidade)
    return cont

# Lista de bacias a serem processadas
listaNameBacias = ["7591"]
cont = 16
knowMapSaved = False
show_interval = True

# --- Loop Principal de Execução ---
for cc, idbacia in enumerate(listaNameBacias[:]):
    if knowMapSaved:
        # Lógica para verificar se o mapa já foi salvo (desativada)
        pass
    else:
        print("-----------------------------------------")
        print(f"----- PROCESSING BACIA {idbacia} -------")
        # Instancia a classe de processamento para a bacia atual
        aplicando_TemporalFilter = processo_filterTemporal(idbacia)
        # Executa o método principal do filtro temporal
        aplicando_TemporalFilter.applyTemporalFilter(show_interval)
        # Desativa a impressão de intervalos após a primeira bacia
        if cc == 0:
            show_interval = False