
#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICAÇÃO POR BACIA
# Produzido por Geodatin - Dados e Geoinformação
# DISTRIBUIDO COM GPLv2
'''
# --------------------------------------------------------------------------
# Bloco 1: Importação de Módulos e Configuração Inicial do Ambiente
# Descrição: Este bloco importa as bibliotecas necessárias, configura os
# caminhos de sistema para acessar módulos customizados, seleciona a conta
# do GEE a ser utilizada e inicializa a API do Earth Engine.
# --------------------------------------------------------------------------
import ee
import os
import json
import copy
import sys
from pathlib import Path
import arqParametros as arqParams
import collections
collections.Callable = collections.abc.Callable # Compatibilidade com versões do Python

# Adiciona o diretório pai ao path para importar módulos locais
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)

# Importa funções customizadas para gerenciamento de contas e ferramentas do GEE
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *

# Define o projeto GEE a ser utilizado
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

# Tenta inicializar a API do Google Earth Engine
try:
    ee.Initialize(project=projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

# --------------------------------------------------------------------------
# Bloco 2: Definição da Classe Principal de Classificação
# Descrição: A classe `ClassMosaic_indexs_Spectral` encapsula toda a lógica
# para o processo de classificação, desde a definição de parâmetros e
# cálculo de índices espectrais até a execução do classificador e
# exportação dos resultados.
# --------------------------------------------------------------------------
class ClassMosaic_indexs_Spectral(object):
    """
    Classe principal para orquestrar o processo de classificação de imagens
    de satélite por bacia hidrográfica no Google Earth Engine.
    """

    # ----------------------------------------------------------------------
    # Seção de Parâmetros e Configurações Globais da Classe
    # Este dicionário 'options' centraliza todos os parâmetros de entrada,
    # como bandas, biomas, versões, caminhos de assets e hiperparâmetros
    # do classificador.
    # ----------------------------------------------------------------------
    options = {
        'bnd_L': ['blue', 'green', 'red', 'nir', 'swir1', 'swir2'],
        'bnd_fraction': ['gv', 'npv', 'soil'],
        'biomas': ['CERRADO', 'CAATINGA', 'MATAATLANTICA'],
        'bioma': "CAATINGA",
        'version': 10,
        'lsBandasMap': [],
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'asset_collectionId': 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
        'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_joinsGrBa': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C',
        'asset_joinsGrBaMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_MB_DS_v4corrCC',
        'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2',
        'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX',
        'lsClasse': [4, 3, 12, 15, 18, 21, 22, 33],
        'lsPtos': [300, 500, 300, 350, 150, 100, 150, 300],
        "anoIntInit": 1985,
        "anoIntFin": 2024,
        'dict_classChangeBa': arqParams.dictClassRepre,
        # Hiperparâmetros para o classificador Gradient Tree Boost
        'pmtGTB': {
            'numberOfTrees': 25,
            'shrinkage': 0.1,
            'samplingRate': 0.65,
            'loss': "LeastSquares",
            'seed': 0
        },
    }
    # Lista de bacias para pós-processamento específico
    lstbasin_posp = ["7613", "7746", "7754", "7741", "773", "761112", "7591", "7581", "757"]
    # Dicionário para definir o tamanho máximo das amostras (ROIs) por classe e por bacia
    dictSizeROIs = {
        "7613": {'3': 600, '4': 2500, '12': 450, '15': 650, '18': 100, '21': 450, '22': 400, '29': 200, '33': 100},
        "7746": {'3': 600, '4': 800, '12': 350, '15': 1150, '18': 100, '21': 550, '22': 400, '29': 200, '33': 50},
        "7754": {'3': 600, '4': 800, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        "7741": {'3': 600, '4': 800, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        "773": {'3': 600, '4': 800, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        "761112": {'3': 600, '4': 800, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        "7591": {'3': 600, '4': 1100, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        "7581": {'3': 600, '4': 800, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        "757": {'3': 600, '4': 1000, '12': 300, '15': 1250, '18': 100, '21': 550, '22': 400, '29': 200, '33': 100},
        'outros': {'3': 600, '4': 1800, '12': 300, '15': 1200, '18': 100, '21': 750, '22': 400, '29': 200, '33': 100},
    }

    def __init__(self):
        """
        Inicializador da classe.

        Configura o ambiente da classe, verifica mapas já processados,
        define a lista de anos a serem processados, carrega hiperparâmetros
        de arquivos JSON e define as bandas a serem utilizadas.
        """
        # Verifica mapas já existentes no asset de saída para evitar reprocessamento
        imgMapSaved = ee.ImageCollection(self.options['assetOut'])
        self.lstIDassetS = imgMapSaved.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
        print(f" ====== we have {len(self.lstIDassetS)} maps saved ====")
        print("==================================================")

        # Gera a lista de anos com base nos parâmetros de início e fim
        self.lst_year = [k for k in range(self.options['anoIntInit'], self.options['anoIntFin'] + 1)]
        print("lista de anos ", self.lst_year)
        self.options['lsBandasMap'] = ['classification_' + str(kk) for kk in self.lst_year]

        # Carrega dicionário de hiperparâmetros otimizados de um arquivo JSON
        pathHiperpmtros = os.path.join(pathparent, 'dados', 'dictBetterModelpmtCol10v1.json')
        with open(pathHiperpmtros, 'r') as b_file:
            self.dictHiperPmtTuning = json.load(b_file)

        # Define o caminho para os arquivos JSON com as features selecionadas
        self.pathFSJson = getPathCSV("FS_col10_json/")
        print("==== path of CSVs of Features Selections ==== \n >>> ", self.pathFSJson)
        self.lstBandMB = self.get_bands_mosaicos()
        print("bandas mapbiomas ", self.lstBandMB)
    
    # --------------------------------------------------------------------------
    # Bloco 3: Funções para Cálculo de Índices e Adição de Bandas
    # Descrição: Este bloco contém métodos para enriquecer uma imagem `ee.Image`
    # com informações adicionais, como índices espectrais (NDVI, EVI, etc.),
    # frações de SMA, dados de relevo (declividade e sombreamento) e textura.
    # --------------------------------------------------------------------------

    def addSlopeAndHilshade(self, img):
        """Adiciona bandas de declividade (slope) e sombreamento (hillshade) a uma imagem.

        Utiliza o modelo digital de elevação NASADEM para calcular as métricas
        de terreno e as anexa como novas bandas na imagem de entrada.

        Args:
            img (ee.Image): A imagem de entrada à qual as bandas serão adicionadas.

        Returns:
            ee.Image: A imagem original com as bandas 'slope' e 'hillshade' adicionadas.
        """
        dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
        slope = ee.Terrain.slope(dem).divide(500).toFloat()
        terrain = ee.Terrain.products(dem)
        hillshade = terrain.select('hillshade').divide(500).toFloat()

        return img.addBands(slope.rename('slope')).addBands(hillshade.rename('hillshade'))

    def agregateBandswithSpectralIndex(self, img):
        """Calcula e adiciona um conjunto extenso de índices espectrais a uma imagem.

        A função calcula diversos índices para as composições de mediana anual,
        estação seca ('dry') e estação chuvosa ('wet'). Também calcula a textura (contraste)
        das bandas NIR e RED.

        Args:
            img (ee.Image): A imagem de entrada, que deve conter as bandas espectrais
                            com sufixos '_median', '_median_wet' e '_median_dry'.

        Returns:
            ee.Image: A imagem original com todas as bandas de índices espectrais e textura adicionadas.
        """
        # --- Cálculo dos Índices ---
        # A implementação de cada índice (NDVI, EVI, NBR, etc.) segue um padrão:
        # 1. Usa ee.Image.expression() para aplicar a fórmula do índice.
        # 2. Renomeia a banda resultante com um nome descritivo.
        # 3. Converte o resultado para o tipo float.
        # Este padrão se repete para as três sazonalidades (anual, seca e chuvosa).

        ratioImgY = (img.expression("float(b('nir_median') / b('red_median'))").rename(['ratio_median']).toFloat())
        ratioImgwet = (img.expression("float(b('nir_median_wet') / b('red_median_wet'))").rename(['ratio_median_wet']).toFloat())
        ratioImgdry = (img.expression("float(b('nir_median_dry') / b('red_median_dry'))").rename(['ratio_median_dry']).toFloat())

        rviImgY = (img.expression("float(b('red_median') / b('nir_median'))").rename(['rvi_median']).toFloat())
        rviImgWet = (img.expression("float(b('red_median_wet') / b('nir_median_wet'))").rename(['rvi_median_wet']).toFloat())
        rviImgDry = (img.expression("float(b('red_median_dry') / b('nir_median_dry'))").rename(['rvi_median_dry']).toFloat())

        ndviImgY = (img.expression("float(b('nir_median') - b('red_median')) / (b('nir_median') + b('red_median'))").rename(['ndvi_median']).toFloat())
        ndviImgWet = (img.expression("float(b('nir_median_wet') - b('red_median_wet')) / (b('nir_median_wet') + b('red_median_wet'))").rename(['ndvi_median_wet']).toFloat())
        ndviImgDry = (img.expression("float(b('nir_median_dry') - b('red_median_dry')) / (b('nir_median_dry') + b('red_median_dry'))").rename(['ndvi_median_dry']).toFloat())

        # ... (continuação do cálculo para todos os outros índices como NDWI, NDBI, EVI, etc.) ...
        # (O código para os outros índices foi omitido aqui para brevidade, mas o padrão é o mesmo)
        # ...

        nddiImg = (ndviImgY.addBands(ndwiImgY).expression("float((b('ndvi_median') - b('ndwi_median')) / (b('ndvi_median') + b('ndwi_median')))").rename(['nddi_median']).toFloat())
        nddiImgWet = (ndviImgWet.addBands(ndwiImgWet).expression("float((b('ndvi_median_wet') - b('ndwi_median_wet')) / (b('ndvi_median_wet') + b('ndwi_median_wet')))").rename(['nddi_median_wet']).toFloat())
        nddiImgDry = (ndviImgDry.addBands(ndwiImgDry).expression("float((b('ndvi_median_dry') - b('ndwi_median_dry')) / (b('ndvi_median_dry') + b('ndwi_median_dry')))").rename(['nddi_median_dry']).toFloat())

        # ... (continuação do cálculo para todos os outros índices) ...
        
        # --- Cálculo de Textura (GLCM Contrast) ---
        textura2 = img.select('nir_median').multiply(10000).toUint16().glcmTexture(3)
        contrastnir = textura2.select('nir_median_contrast').divide(10000).toFloat()
        textura2Dry = img.select('nir_median_dry').multiply(10000).toUint16().glcmTexture(3)
        contrastnirDry = textura2Dry.select('nir_median_dry_contrast').divide(10000).toFloat()
        
        textura2R = img.select('red_median').multiply(10000).toUint16().glcmTexture(3)
        contrastred = textura2R.select('red_median_contrast').divide(10000).toFloat()
        textura2RDry = img.select('red_median_dry').multiply(10000).toUint16().glcmTexture(3)
        contrastredDry = textura2RDry.select('red_median_dry_contrast').divide(10000).toFloat()

        # --- Agregação de todas as novas bandas ---
        return (
            img.addBands(ratioImgY).addBands(ratioImgwet).addBands(ratioImgdry)
                .addBands(rviImgY).addBands(rviImgWet).addBands(rviImgDry)
                # ... (todas as outras bandas de índice) ...
                .addBands(contrastnir).addBands(contrastred).addBands(contrastnirDry).addBands(contrastredDry)
        )

    def calculateBandsIndexEVI(self, img):
        """Calcula e adiciona a banda de EVI a uma imagem.

        Args:
            img (ee.Image): Imagem de entrada com as bandas 'nir' e 'red'.

        Returns:
            ee.Image: A imagem original com a banda 'evi' adicionada.
        """
        eviImgY = img.expression("float(2.4 * (b('nir') - b('red')) / (1 + b('nir') + b('red')))")\
            .rename(['evi']).toFloat()
        return img.addBands(eviImgY)

    def agregateBandsIndexLAI(self, img):
        """Calcula e adiciona o Índice de Área Foliar (LAI) a uma imagem.

        Args:
            img (ee.Image): Imagem de entrada com a banda 'evi_median'.

        Returns:
            ee.Image: A imagem original com a banda 'lai_median' adicionada.
        """
        laiImgY = img.expression("float(3.618 * (b('evi_median') - 0.118))")\
            .rename(['lai_median']).toFloat()
        return img.addBands(laiImgY)
    
    def GET_NDFIA(self, IMAGE, sufixo):
        """Calcula o NDFIa (Normalized Difference Fraction Index - Adjusted) para uma imagem.

        Este método aplica uma análise de mistura espectral (SMA) para obter as frações
        de vegetação verde (GV), vegetação não fotossintética (NPV), solo e sombra.
        Em seguida, calcula o NDFIa ajustado para a sombra.

        Args:
            IMAGE (ee.Image): A imagem de entrada com as 6 bandas espectrais (blue a swir2).
            sufixo (str): Um sufixo a ser adicionado aos nomes das bandas ('_median', etc.).

        Returns:
            ee.Image: Uma imagem contendo as frações SMA e a banda 'ndfia'.
        """
        lstBands = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
        lstBandsSuf = [bnd + sufixo for bnd in lstBands]
        lstFractions = ['gv', 'shade', 'npv', 'soil', 'cloud']
        lstFractionsSuf = [frac + sufixo for frac in lstFractions]

        endmembers = [
            [0.05, 0.09, 0.04, 0.61, 0.30, 0.10],  # gv
            [0.14, 0.17, 0.22, 0.30, 0.55, 0.30],  # npv
            [0.20, 0.30, 0.34, 0.58, 0.60, 0.58],  # soil
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],     # Shade
            [0.90, 0.96, 0.80, 0.78, 0.72, 0.65]   # cloud
        ]

        fractions = ee.Image(IMAGE).select(lstBandsSuf)\
            .unmix(endmembers=endmembers, sumToOne=True, nonNegative=True).float().rename(lstFractions)

        NDFI_ADJUSTED = fractions.expression(
            "float(((b('gv') / (1 - b('shade'))) - b('soil')) / ((b('gv') / (1 - b('shade'))) + b('npv') + b('soil')))"
        ).rename('ndfia')
        
        fractions = fractions.rename(lstFractionsSuf)
        RESULT_IMAGE = (fractions.toFloat().addBands(NDFI_ADJUSTED))

        return ee.Image(RESULT_IMAGE).toFloat()

    def agregate_Bands_SMA_NDFIa(self, img):
        """Aplica o cálculo de frações SMA e NDFIa para as três sazonalidades.

        Args:
            img (ee.Image): A imagem de entrada com as bandas espectrais e seus sufixos.

        Returns:
            ee.Image: A imagem original com todas as bandas de fração e NDFIa adicionadas.
        """
        indSMA_median = self.GET_NDFIA(img, '_median')
        indSMA_med_wet = self.GET_NDFIA(img, '_median_wet')
        indSMA_med_dry = self.GET_NDFIA(img, '_median_dry')

        return img.addBands(indSMA_median).addBands(indSMA_med_wet).addBands(indSMA_med_dry)

    def CalculateIndice(self, imagem):
        """Função orquestradora para o cálculo de todos os índices e bandas auxiliares.

        Args:
            imagem (ee.Image): A imagem de mosaico de entrada.

        Returns:
            ee.Image: A imagem final com todas as bandas calculadas, pronta para a classificação.
        """
        imageW = self.agregateBandswithSpectralIndex(imagem)
        imageW = self.agregate_Bands_SMA_NDFIa(imageW)
        imageW = self.addSlopeAndHilshade(imageW)
        return imageW
    
    # --------------------------------------------------------------------------
    # Bloco 4: Funções para Criação de Mosaicos e Manipulação de Amostras (ROIs)
    # Descrição: Este bloco contém métodos para gerar mosaicos sazonais a partir
    # de coleções de imagens e para processar as amostras de treinamento, como
    # subamostragem (downsampling) e coleta de amostras de bacias vizinhas.
    # --------------------------------------------------------------------------
    
    def make_mosaicofromReducer(self, colMosaic):
        """Cria um mosaico sazonal usando redutores de percentil baseados em EVI.

        Args:
            colMosaic (ee.ImageCollection): A coleção de imagens de entrada para o ano.

        Returns:
            ee.Image: Um mosaico contendo as bandas da mediana anual, mediana da estação seca,
                      mediana da estação chuvosa e desvio padrão.
        """
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]
        band_wets = [bnd + '_wet' for bnd in band_year]
        
        percentilelowDry, percentileDry, percentileWet = 5, 35, 65

        # Define os limiares de EVI para as estações seca e chuvosa
        evilowDry = colMosaic.select(['evi']).reduce(ee.Reducer.percentile([percentilelowDry]))
        eviDry = colMosaic.select(['evi']).reduce(ee.Reducer.percentile([percentileDry]))
        eviWet = colMosaic.select(['evi']).reduce(ee.Reducer.percentile([percentileWet]))

        # Filtra as coleções para obter as imagens de cada estação
        collectionDry = colMosaic.map(lambda img: img.mask(img.select(['evi']).gte(evilowDry)).mask(img.select(['evi']).lte(eviDry)))
        collectionWet = colMosaic.map(lambda img: img.mask(img.select(['evi']).gte(eviWet)))

        # Gera os mosaicos por redução (mediana e desvio padrão)
        mosaic = colMosaic.select(self.options['bnd_L']).reduce(ee.Reducer.median()).rename(band_year)
        mosaicDry = collectionDry.select(self.options['bnd_L']).reduce(ee.Reducer.median()).rename(band_drys)
        mosaicWet = collectionWet.select(self.options['bnd_L']).reduce(ee.Reducer.median()).rename(band_wets)
        mosaicStdDev = colMosaic.select(self.options['bnd_L']).reduce(ee.Reducer.stdDev())

        # Combina todos os mosaicos em uma única imagem
        mosaic = mosaic.addBands(mosaicDry).addBands(mosaicWet).addBands(mosaicStdDev)
        return mosaic

    def make_mosaicofromIntervalo(self, colMosaic, year_courrent, semetral=False):
        """Cria um mosaico sazonal usando intervalos de datas fixos.

        Args:
            colMosaic (ee.ImageCollection): A coleção de imagens de entrada.
            year_courrent (int): O ano de referência para criar os intervalos.
            semetral (bool): Se True, processa apenas os períodos anual e chuvoso.

        Returns:
            ee.Image: Um mosaico contendo as bandas dos períodos selecionados.
        """
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_wets = [bnd + '_wet' for bnd in band_year]
        band_drys = [bnd + '_dry' for bnd in band_year]
        dictPer = {
            'year': {'start': f'{year_courrent}-01-01', 'end': f'{year_courrent}-12-31', 'bnds': band_year},
            'dry': {'start': f'{year_courrent}-08-01', 'end': f'{year_courrent}-12-31', 'bnds': band_drys},
            'wet': {'start': f'{year_courrent}-01-01', 'end': f'{year_courrent}-07-31', 'bnds': band_wets}
        }
        
        mosaico = None
        lstPeriodo = ['year', 'wet'] if semetral else ['year', 'dry', 'wet']
        
        for periodo in lstPeriodo:
            mosaictmp = colMosaic.select(self.options['bnd_L'])\
                .filter(ee.Filter.date(dictPer[periodo]['start'], dictPer[periodo]['end']))\
                .max().rename(dictPer[periodo]['bnds'])
            
            if periodo == 'year':
                mosaico = copy.deepcopy(mosaictmp)
            else:
                mosaico = mosaico.addBands(mosaictmp)

        # Preenche com bandas vazias se o modo semestral for ativado
        if semetral:
            imgUnos = ee.Image.constant([1] * len(band_year)).rename(dictPer['dry']['bnds'])
            mosaico = mosaico.addBands(imgUnos)

        return mosaico

    def get_bands_mosaicos(self):
        """Retorna uma lista consolidada com os nomes de todas as bandas do mosaico.

        Returns:
            list[str]: Uma lista de strings com os nomes das bandas para as três sazonalidades.
        """
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]
        band_wets = [bnd + '_wet' for bnd in band_year]
        return band_year + band_wets + band_drys

    def down_samples_ROIs(self, rois_train, nome_bacia):
        """Realiza a subamostragem (downsampling) das amostras de treinamento.

        Limita o número de amostras por classe para evitar desbalanceamento,
        com base em limiares pré-definidos para cada bacia.

        Args:
            rois_train (ee.FeatureCollection): A coleção de amostras de entrada.
            nome_bacia (str): O código da bacia para buscar os limiares corretos.

        Returns:
            ee.FeatureCollection: A coleção de amostras após a subamostragem.
        """
        dictQtLimit = self.dictSizeROIs.get(nome_bacia, self.dictSizeROIs['outros'])
        lstFeats = ee.FeatureCollection([])

        def make_random_select(featCC, limiar):
            featCC = featCC.randomColumn()
            return featCC.filter(ee.Filter.lt('random', ee.Number(limiar).toFloat()))

        for cclass in [3, 4, 12, 15, 21, 22, 33]:
            feattmp = rois_train.filter(ee.Filter.eq('class', int(cclass)))
            sizeFC = feattmp.size()
            
            # Aplica a seleção aleatória apenas se o número de amostras exceder o limiar
            feattmp = ee.Algorithms.If(
                sizeFC.gt(ee.Number(dictQtLimit[str(cclass)])),
                make_random_select(feattmp, ee.Number(dictQtLimit[str(cclass)]).divide(sizeFC)),
                feattmp
            )
            lstFeats = lstFeats.merge(feattmp)
        
        # Mantém todas as amostras das classes minoritárias
        feattmp = rois_train.filter(ee.Filter.inList('class', [18, 29]))
        lstFeats = lstFeats.merge(feattmp)
        return ee.FeatureCollection(lstFeats)

    def get_ROIs_from_neighbor(self, lst_bacias, asset_root, yyear):
        """Coleta amostras de treinamento de bacias vizinhas.

        Args:
            lst_bacias (list[str]): Lista de códigos das bacias vizinhas.
            asset_root (str): O caminho do asset onde as amostras estão armazenadas.
            yyear (int): O ano das amostras a serem coletadas.

        Returns:
            ee.FeatureCollection: Uma coleção com todas as amostras das bacias vizinhas.
        """
        featGeral = ee.FeatureCollection([])
        for jbasin in lst_bacias:
            nameFeatROIs = f"{jbasin}_{yyear}_cd"
            dir_asset_rois = os.path.join(asset_root, nameFeatROIs)
            feat_tmp = ee.FeatureCollection(dir_asset_rois)
            feat_tmp = feat_tmp.map(lambda f: f.set('class', ee.Number.parse(f.get('class')).toFloat().toInt8()))
            featGeral = featGeral.merge(feat_tmp)
        return featGeral
    
    # --------------------------------------------------------------------------
    # Bloco 5: Orquestração do Processo de Classificação e Exportação
    # Descrição: Este bloco contém o método principal `iterate_bacias`, que
    # executa o fluxo completo para uma única bacia e ano, e o método
    # `processoExportar` para salvar os resultados como assets no GEE.
    # --------------------------------------------------------------------------

    def iterate_bacias(self, _nbacia, myModel, makeProb, process_mosaic_EE):
        """Executa o fluxo completo de classificação para uma bacia específica.

        Este é o método orquestrador principal. Ele carrega a geometria da bacia,
        as amostras de treinamento, o mosaico de imagens, treina o classificador
        e exporta o mapa classificado.

        Args:
            _nbacia (str): O código da bacia a ser processada.
            myModel (str): O nome do modelo (não utilizado atualmente).
            makeProb (bool): Se deve gerar um mapa de probabilidade (não utilizado).
            process_mosaic_EE (bool): Flag para decidir qual fluxo de mosaico e amostras usar.
        """
        # Carrega a geometria da bacia e a converte para uma máscara raster
        baciabuffer_fc = ee.FeatureCollection(self.options['asset_bacias_buffer'])\
            .filter(ee.Filter.eq('nunivotto4', _nbacia))
        print(f"know about the geometry 'nunivotto4' >>  {_nbacia} loaded < {baciabuffer_fc.size().getInfo()} > geometry")
        bacia_raster = baciabuffer_fc.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)
        baciabuffer = baciabuffer_fc.geometry()

        # Carrega as coleções de mosaicos do GEE e do MapBiomas
        imagens_mosaicoEE = ee.ImageCollection(self.options['asset_collectionId']).select(self.options['bnd_L'])
        imagens_mosaico = ee.ImageCollection(self.options['asset_mosaic'])\
            .filter(ee.Filter.inList('biome', self.options['biomas']))\
            .filter(ee.Filter.inList('satellite', ["l5", "l7", "l8"]))\
            .select(self.lstBandMB)

        # Carrega as features selecionadas para a bacia a partir de um arquivo JSON
        path_ptrosFS = os.path.join(self.pathFSJson, f"feat_sel_{_nbacia}.json")
        print("load features json ", path_ptrosFS)
        with open(path_ptrosFS, 'r') as file:
            bandas_fromFS = json.load(file)

        # Itera sobre cada ano definido nos parâmetros da classe
        for nyear in self.lst_year[:]:
            bandActiva = f'classification_{nyear}'
            print("banda activa: " + bandActiva)
            nomec = f"{_nbacia}_{nyear}_GTB_col10-v_{self.options['version']}"

            # Pula o ano se o mapa já foi processado e salvo
            if 'BACIA_' + nomec not in self.lstIDassetS:
                try:
                    # Seleciona as bandas mais importantes para o ano e bacia atuais
                    lstbandas_import = bandas_fromFS[f"{_nbacia}_{nyear}"]['features']
                    bandas_imports = [b for b in lstbandas_import if '_1' not in b and '_2' not in b][:35]
                    print(f" numero de bandas selecionadas {len(bandas_imports)} ")

                    # Carrega as amostras de treinamento (ROIs)
                    nameFeatROIs = f"{_nbacia}_{nyear}_cd"
                    asset_rois = self.options['asset_joinsGrBaMB'] if not process_mosaic_EE else self.options['asset_joinsGrBa']
                    dir_asset_rois = os.path.join(asset_rois, nameFeatROIs)
                    ROIs_toTrain = ee.FeatureCollection(dir_asset_rois)
                    
                    # Realiza a subamostragem dos ROIs para balanceamento
                    ROIs_toTrain = self.down_samples_ROIs(ROIs_toTrain, _nbacia)
                    print(" fez down samples nos ROIs ")

                    # Constrói o mosaico para o ano, preenchendo falhas entre fontes de dados
                    if process_mosaic_EE:
                        # Lógica para preencher falhas no mosaico GEE com dados MapBiomas
                        # (código omitido para brevidade)
                        mosaicoBuilded = ...
                    else:
                        # Lógica para preencher falhas no mosaico MapBiomas com dados GEE
                        # (código omitido para brevidade)
                        mosaicoBuilded = ...

                    # Calcula todos os índices espectrais e bandas auxiliares
                    mosaicProcess = self.CalculateIndice(mosaicoBuilded.updateMask(bacia_raster))
                    print("calculou todas as bandas necesarias ")

                    # Configura e treina o classificador Gradient Tree Boost
                    pmtroClass = copy.deepcopy(self.options['pmtGTB'])
                    pmtroClass['shrinkage'] = self.dictHiperPmtTuning[_nbacia]['learning_rate']
                    pmtroClass['numberOfTrees'] = self.dictHiperPmtTuning[_nbacia]["n_estimators"]
                    print("pmtros Classifier ==> ", pmtroClass)

                    classifierGTB = ee.Classifier.smileGradientTreeBoost(**pmtroClass)\
                        .train(ROIs_toTrain, 'class', bandas_imports)

                    # Classifica a imagem e define os metadados
                    classifiedGTB = mosaicProcess.classify(classifierGTB, bandActiva)
                    mydict = {
                        'id_bacia': _nbacia, 'version': self.options['version'],
                        'biome': self.options['bioma'], 'classifier': 'GTB',
                        'collection': '10.0', 'sensor': 'Landsat',
                        'source': 'geodatin', 'year': nyear
                    }
                    classifiedGTB = classifiedGTB.set(mydict)
                    classifiedGTB = classifiedGTB.set("system:footprint", baciabuffer.coordinates())

                    # Inicia a exportação do resultado
                    self.processoExportar(classifiedGTB, baciabuffer, nomec, process_mosaic_EE)

                except Exception as e:
                    print(f"----------- ERRO AO PROCESSAR {_nbacia} para o ano {nyear} ----------------")
                    print(f"Detalhe do erro: {e}")

            else:
                print(f' bacia >>> {nomec}   <<<  foi FEITA ')

    def processoExportar(self, mapaRF, regionB, nameB, proc_mosaicEE):
        """Exporta uma imagem classificada como um asset no Google Earth Engine.

        Args:
            mapaRF (ee.Image): A imagem classificada a ser exportada.
            regionB (ee.Geometry): A geometria da região para definir a extensão da exportação.
            nameB (str): O nome base para o asset a ser criado.
            proc_mosaicEE (bool): Flag para determinar o diretório de saída do asset.
        """
        nomeDesc = 'BACIA_' + str(nameB)
        idasset = os.path.join(self.options['assetOutMB'] if not proc_mosaicEE else self.options['assetOut'], nomeDesc)
        
        optExp = {
            'image': mapaRF,
            'description': nomeDesc,
            'assetId': idasset,
            'region': ee.Geometry(regionB),
            'scale': 30,
            'maxPixels': 1e13,
            "pyramidingPolicy": {".default": "mode"},
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start()
        print("salvando ... " + nomeDesc + "..!")
        for keys, vals in dict(task.status()).items():
            print(f"   {keys} : {vals}")

# --------------------------------------------------------------------------
# Bloco 6: Funções Utilitárias e de Gerenciamento
# Descrição: Este bloco contém funções auxiliares para gerenciar tarefas de
# exportação no GEE, manipular arquivos e caminhos no sistema local, e
# limpar listas de bandas.
# --------------------------------------------------------------------------

def gerenciador(cont):
    """Gerencia a troca de contas do GEE para distribuir as tarefas de exportação.

    Verifica o número de tarefas ativas e, se necessário, troca para a próxima
    conta da lista para evitar o bloqueio por excesso de tarefas simultâneas.

    Args:
        cont (int): O índice da conta atual a ser utilizada.

    Returns:
        int or 0: O índice da próxima conta a ser usada, ou 0 se o limite foi atingido.
    """
    numberofChange = [kk for kk in param['conta'].keys()]
    print(numberofChange)

    if str(cont) in numberofChange:
        print(f"inicialize in account #{cont} <> {param['conta'][str(cont)]}")
        switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project=projAccount)
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!')

        tarefas = tasks(n=param['numeroTask'], return_list=True)
        for lin in tarefas:
            print(str(lin))
    elif cont > param['numeroLimit']:
        return 0
    cont += 1
    return cont

def save_ROIs_toAsset(collection, name):
    """Exporta uma FeatureCollection de ROIs para um asset no GEE.

    Args:
        collection (ee.FeatureCollection): A coleção de amostras a ser salva.
        name (str): O nome do asset de saída.
    """
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': os.path.join(param['outAssetROIs'], name)
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print(f"exportando ROIs da bacia {name} ...!")

def check_dir(file_name):
    """Verifica se um arquivo existe e, caso não, o cria.

    Args:
        file_name (str): O caminho completo do arquivo a ser verificado/criado.
    """
    if not os.path.exists(file_name):
        with open(file_name, 'w+') as arq:
            pass

def getPathCSV(nfolder):
    """Constrói o caminho absoluto para um diretório de dados.

    Args:
        nfolder (str): O nome da subpasta dentro do diretório 'dados'.

    Returns:
        str: O caminho absoluto para a pasta especificada.
    """
    pathparent = str(Path(os.getcwd()).parents[0])
    roisPath = f'/dados/{nfolder}'
    mpath = pathparent + roisPath
    print("path of CSVs Rois is \n ==>", mpath)
    return mpath

def clean_lstBandas(tmplstBNDs):
    """Limpa e padroniza uma lista de nomes de bandas.

    Remove sufixos numéricos (ex: '_1') e nomes de bandas indesejados.

    Args:
        tmplstBNDs (list[str]): A lista de nomes de bandas a ser limpa.

    Returns:
        list[str]: A lista de bandas limpa e sem duplicatas.
    """
    lstFails = ['green_median_texture']
    lstbndsRed = []
    for bnd in tmplstBNDs:
        bnd = bnd.replace('_1', '').replace('_2', '').replace('_3', '')
        if bnd not in lstbndsRed and 'min' not in bnd and bnd not in lstFails and 'stdDev' not in bnd:
            lstbndsRed.append(bnd)
    return lstbndsRed

# --------------------------------------------------------------------------
# Bloco 7: Execução Principal do Script (Main)
# Descrição: Este é o ponto de entrada do script. Ele define os parâmetros de
# execução, lê os registros de bacias já processadas, e inicia o loop
# principal para processar cada bacia da lista.
# --------------------------------------------------------------------------

# Define os parâmetros de execução para este script
param = {
    'bioma': "CAATINGA",
    'biomas': ["CAATINGA", "CERRADO", "MATAATLANTICA"],
    'asset_bacias': "projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga49div",
    'asset_bacias_buffer': 'projects/ee-solkancengine17/assets/shape/bacias_buffer_caatinga_49_regions',
    'assetOutMB': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2',
    'assetOut': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX',
    'version': 4,
    'numeroTask': 6,
    'numeroLimit': 10,
    'conta': {'0': 'caatinga01', '1': 'caatinga02', '2': 'caatinga03', '3': 'caatinga04', '4': 'caatinga05', '5': 'solkan1201', '6': 'solkanGeodatin', '7': 'superconta'},
}
tesauroBasin = arqParams.tesauroBasin
pathJson = getPathCSV("regJSON/")
print("==================================================")

# Lê o arquivo de registro para saber quais bacias já foram concluídas
registros_proc = "registros/lsBaciasClassifyfeitasv_1.txt"
path_MGRS = os.path.join(os.getcwd(), registros_proc)
baciasFeitas = []
check_dir(path_MGRS)
with open(path_MGRS, 'r') as arqFeitos:
    for ii in arqFeitos.readlines():
        baciasFeitas.append(ii.strip())

# Abre o arquivo de registro no modo de adição para gravar novos processamentos
arqFeitos = open(path_MGRS, 'a+')

# Lista de bacias a serem processadas nesta execução
nameBacias = ["7591"]
print(f"we have {len(nameBacias)} bacias")

# Flags de controle de execução
modelo = "GTB"
knowMapSaved = False
procMosaicEE = True

# Gerencia a conta do GEE a ser utilizada
cont = 7
cont = gerenciador(cont)

# Loop principal que itera sobre cada bacia da lista
for _nbacia in nameBacias[:]:
    print("---------------------------------------------------------------------")
    print(f"--------   classificando bacia nova {_nbacia} and seus properties da antinga {tesauroBasin.get(_nbacia, 'N/A')}-----------------")
    print("---------------------------------------------------------------------")
    
    # Cria uma instância da classe de classificação e inicia o processo
    process_classification = ClassMosaic_indexs_Spectral()
    process_classification.iterate_bacias(_nbacia, modelo, False, procMosaicEE)
    
    # Grava o ID da bacia no arquivo de registro após iniciar o processo
    arqFeitos.write(_nbacia + '\n')
    arqFeitos.flush() # Garante que a escrita seja salva no disco imediatamente

# Fecha o arquivo de registro ao final da execução
arqFeitos.close()