#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
# SCRIPT DE PÓS-CLASSIFICAÇÃO (GAP-FILL)
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
import copy
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

# --------------------------------------------------------------------------------#
# Bloco 2: Classe Principal do Processo de Gap-Fill                                #
# Descrição: A classe `processo_gapfill` encapsula toda a lógica para              #
# preencher falhas (gaps) em uma série temporal de mapas de classificação.         #
# Ela utiliza uma estratégia temporal para preencher pixels sem dados em um ano    #
# com informações de anos adjacentes ou de uma coleção de referência.              #
# --------------------------------------------------------------------------------#
class processo_gapfill(object):
    """
    Classe para orquestrar o processo de preenchimento de falhas (gap-fill)
    em uma série temporal de imagens de classificação para uma bacia específica.
    """
    # Dicionário de parâmetros que centraliza os caminhos de assets e configurações
    options = {
        'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill',
        'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyVA',
        'inputAsset9': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_gedi': 'users/potapovpeter/GEDI_V27',
        'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew': [3, 4, 3, 3, 3, 12, 12, 12, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21, 21, 4, 12, 21],
        'version_input': 10,
        'version_output': 10
    }

    def __init__(self, nameBacia, conectarPixels):
        """
        Inicializador da classe de processamento de gap-fill.

        Args:
            nameBacia (str): O ID da bacia hidrográfica a ser processada.
            conectarPixels (bool): Flag para um processo futuro de conexão de pixels (não utilizado atualmente).
        """
        self.id_bacias = nameBacia
        # Carrega a geometria da bacia e a converte para uma máscara raster
        self.geom_bacia = ee.FeatureCollection(self.options['asset_bacias_buffer'])\
            .filter(ee.Filter.eq('nunivotto4', nameBacia))
        self.bacia_raster = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))\
            .reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        self.geom_bacia = self.geom_bacia.geometry()
        
        # Define a lista de anos e nomes de bandas a serem processados
        self.years = list(range(1985, 2025))
        self.lstbandNames = ['classification_' + str(yy) for yy in self.years]
        self.conectarPixels = conectarPixels
        
        # Constrói o nome do asset de entrada e carrega a imagem de classificação
        self.name_imgClass = f"BACIA_{nameBacia}_GTB_col10-v_{self.options['version_input']}"
        self.imgClass = ee.Image(os.path.join(self.options['input_asset'], self.name_imgClass))
        
        # Carrega a imagem de referência (MapBiomas Coleção 9)
        self.imgMap9 = ee.Image(self.options['inputAsset9']).updateMask(self.bacia_raster)
        print("carregando imagens a serem processadas com Gap Fill")
        print("from >> ", self.options['input_asset'])

    def dictionary_bands(self, key, value):
        """
        Cria uma imagem condicionalmente, com ou sem máscara.
        Nota: Esta função não parece ser utilizada no fluxo principal do script.

        Args:
            key (str): O nome da banda a ser selecionada ou criada.
            value (ee.Number): Um número que define a condição. Se for 2, a banda é
                               retornada; caso contrário, uma imagem vazia é retornada.

        Returns:
            ee.Image: A imagem resultante da condição.
        """
        imgT = ee.Algorithms.If(
            ee.Number(value).eq(2),
            self.imgClass.select([key]).byte(),
            ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
        )
        return ee.Image(imgT)

    def applyGapFill(self):
        """
        Aplica o algoritmo de preenchimento de falhas (gap-fill) na série temporal.

        A estratégia varia com o ano:
        - 1985: Falhas são preenchidas com dados da Coleção 9 do MapBiomas.
        - 1986-2023: Falhas são preenchidas com o primeiro pixel válido de anos futuros.
        - 2024: Falhas são preenchidas com os dados do ano anterior (2023).

        Returns:
            ee.Image: Uma única imagem multibanda com a série temporal completa e sem falhas.
        """
        baseImgMap = ee.Image().toByte()
        previousImage = None
        lstBandas = [f'classification_{yy}' for yy in self.years]
        
        for cc, yyear in enumerate(self.years):
            bandActive = f'classification_{yyear}'
            # Remapeia as classes da imagem do ano atual
            currentImage = self.imgClass.select(bandActive)\
                .remap(self.options['classMapB'], self.options['classNew'])\
                .rename(bandActive)
            print("adding >> ", bandActive)
            
            # --- Lógica para o primeiro ano (1985): preenche com MapBiomas Col. 9 ---
            if yyear == 1985:
                currentMap9 = self.imgMap9.select(bandActive)\
                    .remap(self.options['classMapB'], self.options['classNew'])\
                    .updateMask(self.bacia_raster)
                maskGap = currentImage.mask().Not()
                bandBlend = currentMap9.updateMask(maskGap)
                newBandActive = currentImage.unmask(0).blend(bandBlend)

            # --- Lógica para anos intermediários: preenche com o próximo pixel válido no tempo ---
            elif 1985 < yyear < 2024:
                maskGap = currentImage.mask().Not()
                # Encontra o primeiro pixel não nulo nos anos seguintes
                rasterFirst = self.imgClass.select(lstBandas[cc + 1:])\
                    .reduce(ee.Reducer.firstNonNull())\
                    .updateMask(self.bacia_raster)\
                    .updateMask(maskGap)
                newBandActive = currentImage.unmask(0).blend(rasterFirst)
                
                # Salva a imagem de 2023 para preencher o último ano
                if yyear == 2023:
                    previousImage = copy.deepcopy(newBandActive)
                    print("addiding 2023 em imagem previa ")
            
            # --- Lógica para o último ano (2024): preenche com o ano anterior (2023) ---
            else:
                print("finalizando  >> ", bandActive)
                maskGap = currentImage.mask().Not()
                newBandActive = currentImage.unmask(0).where(maskGap.eq(1), previousImage)
            
            # Adiciona a banda processada à imagem final
            baseImgMap = baseImgMap.addBands(newBandActive)

        imageFilledTn = ee.Image.cat(baseImgMap).select(self.lstbandNames)
        return imageFilledTn.updateMask(self.bacia_raster)

    def processing_gapfill(self):
        """
        Orquestra o processo de gap-fill e exportação do resultado final.
        """
        # Aplica o algoritmo de preenchimento de falhas
        imageFilled = self.applyGapFill()
        print(" 🚨🚨🚨  Applying filter Gap Fill 🚨🚨🚨 ")
        
        # Define o nome e os metadados da imagem de saída
        name_toexport = f'filterGF_BACIA_{self.id_bacias}_GTB_V{self.options["version_output"]}'
        imageFilled = imageFilled.updateMask(self.bacia_raster).set({
            'version': self.options['version_output'], 'biome': 'CAATINGA',
            'source': 'geodatin', 'model': "GTB", 'type_filter': 'gap_fill',
            'collection': '10.0', 'id_bacias': self.id_bacias, 'sensor': 'Landsat',
            'system:footprint': self.geom_bacia.coordinates()
        })
        
        # Inicia a exportação do resultado
        self.processoExportar(imageFilled, name_toexport)

    def processoExportar(self, mapaRF, nomeDesc):
        """
        Exporta uma imagem como um asset no Google Earth Engine.

        Args:
            mapaRF (ee.Image): A imagem a ser exportada.
            nomeDesc (str): A descrição da tarefa e o nome base do asset.
        """
        idasset = os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 'description': nomeDesc, 'assetId': idasset,
            'region': self.geom_bacia, 'scale': 30, 'maxPixels': 1e13,
            "pyramidingPolicy": {".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start()
        print("salvando ... " + nomeDesc + "..!")
        for keys, vals in dict(task.status()).items():
            print(f"  {keys} : {vals}")

# --------------------------------------------------------------------------------#
# Bloco 3: Função de Gerenciamento de Contas e Execução Principal                  #
# Descrição: Contém a função para gerenciar as contas do GEE e o loop principal    #
# que instancia e executa o processo de gap-fill para cada bacia hidrográfica.    #
# --------------------------------------------------------------------------------#
param = {
    'numeroTask': 6, 'numeroLimit': 50,
    'conta': {
        '0': 'caatinga01', '7': 'caatinga02', '14': 'caatinga03',
        '21': 'caatinga04', '28': 'caatinga05', '35': 'solkan1201',
        '42': 'solkanGeodatin', '49': 'superconta',
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
    numberofChange = [kk for kk in param['conta'].keys()]
    if str(cont) in numberofChange:
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project=projAccount)
            print('The Earth Engine package initialized successfully!')
        except ee.EEException:
            print('The Earth Engine package failed to initialize!')
        
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')
        tarefas = tasks(n=param['numeroTask'], return_list=True)
        for lin in tarefas:
            relatorios.write(str(lin) + '\n')
            
    elif cont > param['numeroLimit']:
        return 0
    cont += 1
    return cont

# Lista de bacias a serem processadas
listaNameBacias = ["7591"]
cont = 49

# --- Loop Principal de Execução ---
for idbacia in listaNameBacias[:]:
    print("-----------------------------------------")
    print(f"----- PROCESSING BACIA {idbacia} -------")
    # Instancia a classe de processamento para a bacia atual
    aplicando_gapfill = processo_gapfill(idbacia, False)
    # Executa o método principal de gap-fill e exportação
    aplicando_gapfill.processing_gapfill()