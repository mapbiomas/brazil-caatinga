#!/usr/bin/python
# # -*- coding: utf-8 -*-

'''
# SCRIPT DE PÓS-CLASSIFICAÇÃO (FILTRO TEMPORAL ITERATIVO)
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
# Bloco 2: Classe Principal do Processo de Filtro Temporal                         #
# Descrição: A classe `processo_filterTemporal` encapsula a lógica para            #
# aplicar um filtro de janela deslizante em uma série temporal de mapas. O         #
# objetivo é corrigir classificações temporalmente inconsistentes, como um         #
# pixel classificado como vegetação nativa em apenas um ano, cercado por           #
# anos de uso antrópico. Esta versão é iterativa, onde a correção de um ano       #
# influencia a análise dos anos seguintes.                                        #
# --------------------------------------------------------------------------------#
class processo_filterTemporal(object):
    """
    Classe para orquestrar a aplicação de um filtro temporal em uma série
    de imagens de classificação para uma bacia hidrográfica específica.
    """
    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalCC',
        'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalCC',
        'input_asset25': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew': [4, 4, 4, 4, 4, 4, 4, 4, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33, 4, 33, 21, 21, 21, 21, 21, 21, 21, 21, 4, 4, 21],
        'classNat': [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        'last_year': 2024, 'first_year': 1985,
        'janela_input': 6, 'janela_output': 6, 'step': 1
    }

    def __init__(self, name_bacia):
        """
        Inicializador da classe de filtro temporal.

        Args:
            name_bacia (str): O ID da bacia hidrográfica a ser processada.
        """
        self.id_bacias = name_bacia
        self.versoutput = 7
        self.versionInput = 6
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer'])\
            .filter(ee.Filter.eq('nunivotto4', name_bacia))
        self.bacia_raster = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))\
            .reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia = self.geom_bacia.geometry()

        # Define a lista de anos, incluindo 2025 para auxiliar no tratamento de borda
        self.years = list(range(self.options['first_year'], self.options['last_year'] + 2))
        self.lstbandNames = ['classification_' + str(yy) for yy in self.years]
        
        # Carrega a imagem de classificação principal (até 2024)
        self.imgClass = ee.ImageCollection(self.options['input_asset'])\
            .filter(ee.Filter.eq('version', self.versionInput))\
            .filter(ee.Filter.eq('id_bacias', name_bacia))\
            .first()

        # Carrega a imagem de 2025 de outra fonte e a adiciona à série temporal
        imgClass25 = ee.ImageCollection(self.options['input_asset25'])\
            .filter(ee.Filter.eq('version', self.versionInput + 1))\
            .filter(ee.Filter.eq('id_bacias', name_bacia))\
            .first()
        self.imgClass = self.imgClass.addBands(imgClass25.select(['classification_2025']))
        
        # Cria uma versão reclassificada (binária) da série temporal para análise de padrões
        self.imgReclass = ee.Image().byte()
        for yband in self.lstbandNames:
            img_tmp = self.imgClass.select(yband).remap(self.options['classMapB'], self.options['classNat'])
            self.imgReclass = self.imgReclass.addBands(img_tmp.rename(yband))
        self.imgReclass = self.imgReclass.select(self.lstbandNames)
        
        # Gera a lista de janelas de anos para a iteração do filtro
        self.colectAnos = [self.mapeiaAnos(ano, self.options['janela_output'], self.years) for ano in self.years]

    # --- Funções de Regra para Construção da Janela Deslizante (Casos de Borda) ---
    def regra_primeira(self, jan, delt, lstYears):
        """Constrói a janela para o primeiro ano da série temporal."""
        return lstYears[1: delt + 1] + [lstYears[0]] + lstYears[delt + 1: jan]

    # --- (Outras funções de regra para casos de borda foram omitidas para brevidade) ---

    def mapeiaAnos(self, ano, janela, anos):
        """
        Gera a lista de bandas para a janela deslizante de um ano específico.

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
        # --- (Lógica de seleção da janela omitida para brevidade) ---
        return lsBandAnos[indice - 1: indice + 2 * delta - 1]

    # --- Funções de Máscara para Detecção de Padrões Temporais ---
    def mask_3_years(self, valor, imagem):
        """Detecta o padrão [A, não A, A] em uma janela de 3 anos."""
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
            imagem.select([1]).neq(valor)).And(
            imagem.select([2]).eq(valor)).unmask(0)
        return mmask.eq(1)

    def mask_6_years(self, valor, imagem):
        """Detecta o padrão [A, A, A, A, não A, A] em uma janela de 6 anos."""
        imagem = ee.Image(imagem)
        mmask = imagem.select([0]).eq(valor).And(
            imagem.select([1]).eq(valor)).And(
            imagem.select([2]).eq(valor)).And(
            imagem.select([3]).eq(valor)).And(
            imagem.select([4]).neq(valor)).And(
            imagem.select([5]).eq(valor))
        return mmask.eq(1)

    # --- (Outras funções de máscara omitidas para brevidade) ---
    
    def applyTemporalFilter(self, showinterv):
        """
        Aplica o filtro temporal iterativo na série temporal de classificações.

        Este método percorre a série temporal, identifica padrões inconsistentes
        usando uma janela deslizante na imagem binária (Natural/Antrópico) e, em
        seguida, usa a máscara resultante para corrigir o mapa de classificação original.
        A correção é iterativa: a alteração em um ano afeta a análise do próximo.

        Args:
            showinterv (bool): Se True, imprime as janelas de anos utilizadas.
        """
        imgOutput = ee.Image().byte()
        id_class = 1  # Foco em corrigir a classe de vegetação natural (valor 1)
        
        if self.options['janela_output'] == 3:
            # --- Lógica para janela de 3 anos ---
            rasterbefore = ee.Image().byte()
            for cc, lstyear in enumerate(self.colectAnos[:-1]): # Itera até o penúltimo ano
                band_C1 = lstyear[1] # Banda central da janela
                if showinterv:
                    print(f"> {band_C1} intervalos <==> ", lstyear)
                
                # Na primeira iteração, usa a imagem reclassificada original
                if cc == 0:
                    imgtmp_mask = self.mask_3_years(id_class, self.imgReclass.select(lstyear))
                # Nas seguintes, usa a versão já corrigida da iteração anterior
                else:
                    imgComposta = rasterbefore.addBands(self.imgReclass.select(lstyear[1:]))
                    imgtmp_mask = self.mask_3_years(id_class, imgComposta)

                # Atualiza a imagem binária com a correção para a próxima iteração
                rasterbefore = self.imgReclass.select(band_C1).where(imgtmp_mask.eq(1), id_class)
                
                # Usa a máscara para corrigir a imagem de classificação ORIGINAL
                map_change_year = self.imgClass.select(band_C1).blend(
                    self.imgClass.select(lstyear[2]).updateMask(imgtmp_mask)
                ).rename(band_C1)
                imgOutput = imgOutput.addBands(map_change_year)
            
            # Adiciona a última banda, que não foi filtrada
            imgOutput = imgOutput.addBands(self.imgClass.select(self.colectAnos[-1][1]))
            
        # --- (Lógica para outras janelas (4, 5, 6) foi omitida para brevidade) ---

        # Define os metadados finais e exporta a imagem resultante
        imgOutput = imgOutput.updateMask(self.bacia_raster).set({
            'version': self.versoutput, 'id_bacias': self.id_bacias, 'biome': 'CAATINGA',
            'type_filter': 'temporal', 'collection': '10.0', 'janela': self.options['janela_output'],
            'sensor': 'Landsat', 'system:footprint': self.geom_bacia
        })
        name_toexport = f"filterTP_BACIA_{self.id_bacias}_GTB_J{self.options['janela_output']}_V{self.versoutput}"
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
# Bloco 3: Função de Gerenciamento de Contas e Execução Principal                  #
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
listaNameBacias = [
    '765', '7544', '7541', '7411', '746', '7591', '7592',
    '761111', '761112', '7612', '7613', '7614', '7615',
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754',
    '7761', '7764', '7691', '7581', '7625', '7584', '751',
    '7616', '745', '7424', '7618', '7561', '755', '7617',
    '7564', '7422', '76116', '7671', '757', '766', '753', '764',
    '7619', '7443', '7438', '763', '7622', '752'
]

# --- Loop Principal de Execução ---
knowMapSaved = False
show_interval = True
for cc, idbacia in enumerate(listaNameBacias[:]):
    if knowMapSaved:
        # Lógica para verificar se o mapa já foi salvo (desativada)
        pass
    else:
        print("----- PROCESSING BACIA {} -------".format(idbacia))
        # Instancia a classe de processamento para a bacia atual
        aplicando_TemporalFilter = processo_filterTemporal(idbacia)
        # Executa o método principal do filtro temporal
        aplicando_TemporalFilter.applyTemporalFilter(show_interval)
        # Desativa a impressão de intervalos após a primeira bacia
        if cc == 0:
            show_interval = False