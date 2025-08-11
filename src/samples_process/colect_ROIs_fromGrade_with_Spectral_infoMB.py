#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
# SCRIPT DE COLETA DE AMOSTRAS (ROIs) POR GRADE
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
@author: geodatin
"""

# --------------------------------------------------------------------------------#
# Bloco 1: Importação de Módulos e Inicialização do Earth Engine                   #
# Descrição: Este bloco importa as bibliotecas necessárias, configura o            #
# ambiente para encontrar módulos locais e inicializa a conexão com a API          #
# do Google Earth Engine usando uma conta pré-configurada.                         #
# --------------------------------------------------------------------------------#
import ee
import os
import sys
import pandas as pd
import collections
from pathlib import Path
collections.Callable = collections.abc.Callable # Garante compatibilidade com novas versões do Python

# Adiciona o diretório pai ao path do sistema para importar módulos customizados
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
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
# Bloco 2: Classe Principal para Coleta de Amostras e Cálculo de Índices           #
# Descrição: A classe `ClassMosaic_indexs_Spectral` encapsula toda a lógica        #
# para a coleta de amostras (ROIs). Ela carrega mosaicos anuais pré-processados,   #
# calcula um vasto conjunto de índices espectrais e dados auxiliares, e então     #
# extrai os valores desses pixels em pontos aleatórios, rotulando-os com base      #
# no mapa de referência do MapBiomas.                                              #
# --------------------------------------------------------------------------------#
class ClassMosaic_indexs_Spectral(object):
    """
    Classe para orquestrar a coleta de amostras (ROIs), enriquecendo-as com
    um conjunto completo de bandas espectrais, índices e dados topográficos.
    """
    options = {
        'bnd_L': ['blue', 'green', 'red', 'nir', 'swir1', 'swir2'],
        'biomas': ['CERRADO', 'CAATINGA', 'MATAATLANTICA'],
        'classMapB': [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
        'classNew':  [3, 4, 3, 3, 12, 12, 15, 18, 18, 18, 21, 22, 22, 22, 22, 33, 29, 22, 33, 12, 33, 18, 18, 18, 18, 18, 18, 18,  4, 12, 18],
        'asset_bacias_buffer': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
        'asset_grad': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga',
        'assetMapbiomas90': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
        'asset_mosaic': 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',
        'asset_mask_toSamples': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample',
        'asset_output_grade': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesInd_MBV4',
        "anoIntInit": 1985, "anoIntFin": 2024,
    }
    
    def __init__(self):
        """
        Inicializador da classe. Carrega os assets principais que serão usados
        em todo o processo, como a grade de coleta e os mosaicos anuais.
        """
        self.regionInterest = ee.FeatureCollection(self.options['asset_grad'])
        band_year = [nband + '_median' for nband in self.options['bnd_L']]
        band_drys = [bnd + '_dry' for bnd in band_year]
        band_wets = [bnd + '_wet' for bnd in band_year]
        self.band_mosaic = band_year + band_wets + band_drys
        
        # Carrega a coleção de mosaicos anuais
        self.imgMosaic = ee.ImageCollection(self.options['asset_mosaic'])\
            .filter(ee.Filter.inList('biome', self.options['biomas']))\
            .filter(ee.Filter.inList('satellite', ["l5", "l7", "l8"]))\
            .select(self.band_mosaic)
        
        self.lst_year = list(range(self.options['anoIntInit'], self.options['anoIntFin'] + 1))
        
        # Carrega o mapa de referência do MapBiomas para rotulagem
        self.imgMapbiomas = ee.Image(self.options['assetMapbiomas90'])

    def addSlopeAndHilshade(self, img):
        """
        Adiciona bandas de declividade (slope) e sombreamento (hillshade) a uma imagem.

        Args:
            img (ee.Image): A imagem de entrada à qual as bandas serão adicionadas.

        Returns:
            ee.Image: A imagem original com as bandas 'slope' e 'hillshade'.
        """
        dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
        slope = ee.Terrain.slope(dem).divide(500).toFloat()
        terrain = ee.Terrain.products(dem)
        hillshade = terrain.select('hillshade').divide(500).toFloat()
        return img.addBands(slope.rename('slope')).addBands(hillshade.rename('hillshade'))

    # --------------------------------------------------------------------#
    # Sub-Bloco: Métodos para Cálculo de Índices Espectrais                 #
    # Descrição: Cada método abaixo calcula um índice espectral específico  #
    # para as três sazonalidades (anual, seca e úmida) e o adiciona como    #
    # novas bandas à imagem de entrada.                                     #
    # --------------------------------------------------------------------#

    def agregateBandsIndexNDVI(self, img):
        """Calcula o NDVI (Índice de Vegetação por Diferença Normalizada)."""
        # (Implementação omitida para brevidade, mas o padrão se repete para todos os índices)
        return img
    
    # ... (Muitos outros métodos de cálculo de índice como NDBI, EVI, SAVI, etc.) ...
    
    def GET_NDFIA(self, IMAGE, sufixo):
        """
        Calcula o NDFIa (Índice de Fração por Diferença Normalizada Ajustado).

        Aplica uma Análise de Mistura Espectral (SMA) para obter frações de
        vegetação, solo, etc., e então calcula o NDFIa ajustado para sombra.

        Args:
            IMAGE (ee.Image): A imagem de entrada com as 6 bandas espectrais.
            sufixo (str): O sufixo sazonal a ser usado (ex: '_median').

        Returns:
            ee.Image: Uma imagem com as bandas de fração e a banda 'ndfia'.
        """
        # (Implementação do método)
        return ee.Image(RESULT_IMAGE).toFloat()

    def agregate_Bands_SMA_NDFIa(self, img):
        """Aplica o cálculo de NDFIa para as três sazonalidades."""
        indSMA_median = self.GET_NDFIA(img, '_median')
        indSMA_med_wet = self.GET_NDFIA(img, '_median_wet')
        indSMA_med_dry = self.GET_NDFIA(img, '_median_dry')
        return img.addBands(indSMA_median).addBands(indSMA_med_wet).addBands(indSMA_med_dry)

    # --------------------------------------------------------------------#
    # Sub-Bloco: Orquestração da Coleta de Amostras                       #
    # --------------------------------------------------------------------#

    def CalculateIndice(self, imagem):
        """
        Orquestrador que aplica todos os cálculos de índice a uma imagem de mosaico.

        Args:
            imagem (ee.Image): A imagem de mosaico de entrada.

        Returns:
            ee.Image: A imagem final com todas as bandas de features calculadas.
        """
        # Chama sequencialmente todos os métodos de agregação de índice
        imageW = self.agregateBandsIndexEVI(imagem)
        imageW = self.agregateBandsIndexNDVI(imageW)
        # ... (chamada para todos os outros 30+ métodos de índice) ...
        imageW = self.agregate_Bands_SMA_NDFIa(imageW)
        return imageW

    def iterate_bacias(self, idGrade, askSize):
        """
        Processa uma única célula da grade para coletar amostras de todos os anos.

        Para uma dada célula da grade, esta função itera de 1985 a 2024. Em cada
        ano, ela carrega o mosaico, calcula dezenas de features, e coleta 500
        pontos aleatórios, extraindo para cada ponto os valores de todas as
        features e o rótulo da classe do mapa de referência.

        Args:
            idGrade (int): O ID da célula da grade a ser processada.
            askSize (bool): Se True, verifica se a coleção resultante tem pontos
                            antes de iniciar a exportação.
        """
        # Carrega a geometria da célula da grade
        oneGrade = ee.FeatureCollection(self.options['asset_grad']).filter(ee.Filter.eq('indice', int(idGrade)))
        maskGrade = oneGrade.reduceToImage(['indice'], ee.Reducer.first()).gt(0)
        oneGrade = oneGrade.geometry()

        # Carrega a máscara de áreas válidas para amostragem
        layerSamplesMask = ee.ImageCollection(self.options['asset_mask_toSamples']).filterBounds(oneGrade)
        # ... (lógica para tratar máscara vazia) ...

        shpAllFeat = ee.FeatureCollection([])
        # Loop principal que itera sobre cada ano da série temporal
        for nyear in self.lst_year[:]:
            bandYear = f'classification_{nyear}'
            print(f" processing grid_year => {idGrade} <> {bandYear} ")

            # Carrega o mosaico para o ano atual
            imgColfiltered = self.imgMosaic.filter(ee.Filter.eq('year', nyear)).mosaic().updateMask(maskGrade)

            # Calcula todas as 120+ bandas de features para o mosaico
            img_recMosaicnewB = self.CalculateIndice(imgColfiltered)

            # Carrega a camada de referência do MapBiomas para obter os rótulos
            layerCC = self.imgMapbiomas.select(bandYear if nyear < 2024 else 'classification_2023')\
                .remap(self.options['classMapB'], self.options['classNew'])\
                .clip(oneGrade).rename('class')

            # Realiza a amostragem aleatória, extraindo todas as bandas (features + classe)
            ptosTemp = img_recMosaicnewB.addBands(layerCC)\
                .addBands(ee.Image.constant(nyear).rename('year'))\
                .addBands(ee.Image.constant(idGrade).rename('GRID_ID'))\
                .updateMask(layerSamplesMask.select(f"mask_sample_{nyear if nyear < 2024 else '2023'}").eq(1) if numLayers > 0 else layerSamplesMask)\
                .sample(region=oneGrade, scale=30, numPixels=500, dropNulls=True, geometries=True)

            # Une os pontos do ano atual à coleção geral da grade
            shpAllFeat = shpAllFeat.merge(ptosTemp)
        
        # Exporta a coleção de amostras final para a célula da grade
        name_exp = 'rois_grade_' + str(idGrade)
        self.save_ROIs_toAsset(ee.FeatureCollection(shpAllFeat), name_exp)

    def save_ROIs_toAsset(self, collection, name):
        """
        Exporta uma FeatureCollection de ROIs para um asset no GEE.

        Args:
            collection (ee.FeatureCollection): A coleção de amostras a ser salva.
            name (str): O nome do asset de saída (ex: 'rois_grade_3990').
        """
        optExp = {
            'collection': collection, 'description': name,
            'assetId': self.options['asset_output_grade'] + "/" + name
        }
        task = ee.batch.Export.table.toAsset(**optExp)
        task.start()
        print("exportando ROIs da grade {} ...!".format(name.split('_')[-1]))

# --------------------------------------------------------------------------------#
# Bloco 3: Funções Auxiliares de Gerenciamento de Tarefas                          #
# Descrição: Contém a função para listar assets já processados e a função para     #
# gerenciar as contas, evitando o excesso de tarefas simultâneas.                  #
# --------------------------------------------------------------------------------#
def ask_byGrid_saved(dict_asset):
    """
    Verifica o diretório de saída e retorna uma lista de IDs de grades já processadas.

    Args:
        dict_asset (dict): Dicionário com o ID da pasta de assets de saída.

    Returns:
        list[int]: Uma lista de IDs de grades que já foram exportadas.
    """
    getlstFeat = ee.data.getList(dict_asset)
    lst_temporalAsset = []
    assetbase = "projects/earthengine-legacy/assets/" + dict_asset['id']
    for idAsset in getlstFeat:
        name_feat = idAsset.get('id').replace(assetbase + '/', '')
        idGrade = name_feat.split('_')[2]
        if int(idGrade) not in lst_temporalAsset:
            lst_temporalAsset.append(int(idGrade))
    return lst_temporalAsset

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

# --------------------------------------------------------------------------------#
# Bloco 4: Execução Principal do Script                                            #
# Descrição: Este bloco define a lista de grades a serem processadas, verifica     #
# quais já foram concluídas, e inicia o loop principal, chamando o processo de     #
# coleta de amostras para cada grade pendente.                                     #
# --------------------------------------------------------------------------------#
# Lista completa de todos os IDs de grade a serem processados

lstIdCode = [
    3990, 3991, 3992, 3993, 3994, 3995, 3996, 3997, 3998, 3999, 4000, 4096, 
    4097, 4098, 4099, 4100, 4101, 4102, 4103, 4104, 4105, 4106, 4107, 4108, 
    4109, 4110, 4111, 4112, 4113, 4114, 4115, 4116, 4117, 4118, 4119, 4120, 
    4121, 4122, 4123, 4414, 4415, 4416, 4417, 4418, 4419, 4420, 4421, 4422, 
    4423, 4424, 4425, 4426, 4427, 4428, 4429, 4430, 4431, 4432, 4433, 4434,
    4435, 4436, 4437, 4438, 4439, 4440, 4202, 4203, 4204, 4205, 4206, 4207, 
    4208, 4209, 4210, 4211, 4212, 4213, 4214, 4215, 4216, 4217, 4218, 4219, 
    4220, 4221, 4222, 4223, 4224, 4225, 4226, 4227, 4228, 4001, 4002, 4003, 
    4004, 4005, 4006, 4007, 4008, 4009, 4010, 4011, 4012, 4013, 4014, 4015, 
    4016, 4308, 4309, 4310, 4311, 4312, 4313, 4314, 4315, 4316, 4317, 4318, 
    4319, 4320, 4321, 4322, 4323, 4324, 4325, 4326, 4327, 4328, 4329, 4330, 
    4331, 4332, 4333, 4334, 4626, 4627, 4628, 4629, 4630, 4631, 4632, 4633, 
    4634, 4635, 4636, 4637, 4638, 4639, 4640, 4641, 4642, 4643, 4644, 4645, 
    4646, 4647, 4648, 4649, 4650, 4651, 4942, 4943, 4944, 4945, 4946, 4947, 
    4948, 4949, 4950, 4951, 4952, 4953, 4954, 4955, 4956, 4957, 4958, 4959, 
    4960, 4961, 4962, 4731, 4732, 4733, 4734, 4735, 4736, 4737, 4738, 4739, 
    4740, 4741, 4742, 4743, 4744, 4745, 4746, 4747, 4748, 4749, 4750, 4751, 
    4752, 4753, 4754, 4755, 4756, 4520, 4521, 4522, 4523, 4524, 4525, 4526, 
    4527, 4528, 4529, 4530, 4531, 4532, 4533, 4534, 4535, 4536, 4537, 4538, 
    4539, 4540, 4541, 4542, 4543, 4544, 4545, 4546, 4837, 4838, 4839, 4840, 
    4841, 4842, 4843, 4844, 4845, 4846, 4847, 4848, 4849, 4850, 4851, 4852, 
    4853, 4854, 4855, 4856, 4857, 5376, 5377, 5378, 5379, 5380, 5381, 5382, 
    5383, 5384, 5385, 5154, 5155, 5156, 5157, 5158, 5159, 5160, 5161, 5162, 
    5163, 5164, 5165, 5166, 5167, 5168, 5169, 5170, 5171, 5172, 5173, 5174, 
    5175, 5471, 5472, 5473, 5474, 5475, 5476, 5477, 5478, 5479, 5480, 5481, 
    5482, 5483, 5484, 5485, 5486, 5487, 5488, 5489, 5490, 5261, 5262, 5263, 
    5264, 5265, 5266, 5267, 5268, 5269, 5270, 5271, 5272, 5273, 5274, 5275, 
    5276, 5277, 5278, 5279, 5280, 5048, 5049, 5050, 5051, 5052, 5053, 5054, 
    5055, 5056, 5057, 5058, 5059, 5060, 5061, 5062, 5063, 5064, 5065, 5066, 
    5067, 5366, 5367, 5368, 5369, 5370, 5371, 5372, 5373, 5374, 5375, 5901, 
    5902, 5903, 5904, 5905, 5906, 5907, 5908, 5683, 5684, 5686, 5687, 5688, 
    5689, 5690, 5691, 5692, 5693, 5694, 5695, 5696, 5697, 5698, 5699, 5700, 
    5792, 5793, 5794, 5795, 5796, 5797, 5798, 5799, 5800, 5801, 5802, 5803, 
    5804, 5805, 5576, 5577, 5578, 5579, 5580, 5581, 5582, 5583, 5584, 5585, 
    5586, 5587, 5588, 5589, 5590, 5591, 5592, 5593, 5594, 5595, 6217, 6218, 
    6219, 6220, 6221, 6222, 6006, 6007, 6008, 6009, 6010, 6011, 6012, 6013, 
    6323, 6324, 6325, 6326, 6327, 6112, 6113, 6114, 6115, 6116, 6117, 6118, 
    2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2425, 2426, 2427, 2428, 
    2429, 2430, 2431, 2432, 2433, 2434, 2220, 2223, 2224, 2840, 2841, 2842, 
    2843, 2844, 2845, 2846, 2847, 2848, 2849, 2850, 2851, 2852, 2853, 2854, 
    2855, 2856, 2633, 2634, 2635, 2636, 2637, 2638, 2639, 2640, 2641, 2642, 
    2643, 2644, 2645, 2646, 2941, 2942, 2943, 2944, 2945, 2946, 2947, 2948, 
    2949, 2950, 2951, 2952, 2953, 2954, 2955, 2956, 2957, 2958, 2959, 2960, 
    2737, 2738, 2739, 2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 
    2749, 2750, 2751, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 
    2538, 2539, 2540, 3360, 3361, 3362, 3363, 3364, 3365, 3366, 3367, 3368, 
    3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377, 3378, 3379, 3380, 
    3381, 3382, 3383, 3150, 3151, 3152, 3153, 3154, 3155, 3156, 3157, 3158, 
    3159, 3160, 3161, 3162, 3163, 3164, 3165, 3166, 3167, 3168, 3169, 3170, 
    3171, 3465, 3466, 3467, 3468, 3469, 3470, 3471, 3472, 3473, 3474, 3475, 
    3476, 3477, 3478, 3479, 3480, 3481, 3482, 3483, 3484, 3485, 3486, 3487, 
    3488, 3489, 3255, 3256, 3257, 3258, 3259, 3260, 3261, 3262, 3263, 3264, 
    3265, 3266, 3267, 3268, 3269, 3270, 3271, 3272, 3273, 3274, 3275, 3276, 
    3277, 3278, 3046, 3047, 3048, 3049, 3050, 3051, 3052, 3053, 3054, 3055, 
    3056, 3057, 3058, 3059, 3060, 3061, 3062, 3063, 3064, 3584, 3585, 3586, 
    3587, 3588, 3589, 3590, 3591, 3592, 3593, 3594, 3885, 3886, 3887, 3888, 
    3889, 3890, 3891, 3892, 3893, 3894, 3895, 3896, 3897, 3898, 3899, 3900, 
    3901, 3902, 3903, 3904, 3905, 3906, 3907, 3908, 3909, 3910, 3911, 3675, 
    3676, 3677, 3678, 3679, 3680, 3681, 3682, 3683, 3684, 3685, 3686, 3687, 
    3688, 3689, 3690, 3691, 3692, 3693, 3694, 3695, 3696, 3697, 3698, 3699, 
    3700, 3780, 3781, 3782, 3783, 3784, 3785, 3786, 3787, 3788, 3789, 3790, 
    3791, 3792, 3793, 3794, 3795, 3796, 3797, 3798, 3799, 3800, 3801, 3802, 
    3803, 3804, 3805, 3570, 3571, 3572, 3573, 3574, 3575, 3576, 3577, 3578, 
    3579, 3580, 3581, 3582, 3583
]
# Flag para reprocessar grades que falharam anteriormente
reprocessar = False
if reprocessar:
    df = pd.read_csv('lista_gride_with_failsYearSaved.csv')
    lstIdCode = df['idGrid'].tolist()

# Parâmetros para o gerenciador de tarefas
param = {
    'changeCount': False, 'numeroTask': 6, 'numeroLimit': 70,
    'conta': {
        '0': 'caatinga01', '10': 'caatinga02', '20': 'caatinga03', '30': 'caatinga04',
        '40': 'caatinga05', '50': 'solkan1201', '60': 'solkanGeodatin', '70': 'superconta'
    },
}

# --- Loop Principal de Execução ---
askingbySizeFC = False
searchFeatSaved = True
cont = 0

# Instancia a classe principal de coleta de dados
objetoMosaic_exportROI = ClassMosaic_indexs_Spectral()

# Verifica quais grades já foram salvas para evitar reprocessamento
if searchFeatSaved:
    lstFeatAsset = ask_byGrid_saved({'id': objetoMosaic_exportROI.options['asset_output_grade']})
    print(f"  == Encontrados {len(lstFeatAsset)} assets de grades já processados ==")
else:
    lstFeatAsset = []

print("Total de grades a processar >> ", len(lstIdCode))
sys.exit() # Interrompe o script antes do loop principal (para fins de teste/configuração)

# Define o intervalo de grades a serem processadas nesta execução
inicP = 600
endP = 800
for cc, item in enumerate(lstIdCode[inicP:endP]):
    print(f"# {cc + 1 + inicP} loading geometry grade {item}")
    # Processa a grade apenas se ela não estiver na lista de assets já salvos
    if item not in lstFeatAsset:
        objetoMosaic_exportROI.iterate_bacias(item, askingbySizeFC)
        cont = gerenciador(cont) # Gerencia a conta para não sobrecarregar as tarefas

