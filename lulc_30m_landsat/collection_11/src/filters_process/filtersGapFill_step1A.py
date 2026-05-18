#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
# SCRIPT DE FFIOL POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

class processo_gapfill(object):

    options = {
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Gap-fill',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1joined',
            'inputAsset10': 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
            'asset_gedi': 'users/potapovpeter/GEDI_V27',
            'classMapB':     [3, 4, 5, 9, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75],
            'classNew':      [3, 4, 3, 3, 12, 12, 15, 19, 19, 19, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 36, 19, 19, 19, 36, 36, 36,  4, 12, 19, 25],
            # 'classNew':      [3, 4, 3, 3, 12, 12, 21, 21, 21, 21, 21, 25, 25, 25, 25, 33, 29, 25, 33, 12, 33, 21, 21, 21, 21, 21, 21, 21,  4, 12, 21, 25],
            'year_col10_max': 2023,   # último ano disponível na col10
            'version_input': 1,
            'version_output': 1
            
        }


    def __init__(self, nameBacia, conectarPixels):
        self.id_bacias = nameBacia
        self.geom_bacia = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                                        .filter(ee.Filter.eq('nunivotto4', nameBacia))
                        )
        self.geom_bacia = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster =  self.geom_bacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)                     
        self.geom_bacia = self.geom_bacia.geometry()   
        # print("geometria ", len(self.geom_bacia.getInfo()['coordinates']))
        self.lstbandNames = ['classification_' + str(yy) for yy in range(1985, 2026)]
        self.years = [yy for yy in range(1985, 2026)]
        # print("lista de years \n ", self.years)
        self.conectarPixels = conectarPixels
        self.version = self.options['version_input']
        # self.model = modelo
        self.name_imgClass = f"BACIA_{nameBacia}_joined_GTB_col11_fm-v_{self.options['version_input']}"
        self.num_clases = len(set(self.options['classNew']))
        
        
        # https://code.earthengine.google.com/4f5c6af0912ce360a5adf69e4e6989e7
        self.imgMap10 = ee.Image(self.options['inputAsset10']).updateMask(self.bacia_raster)
        # .remap(self.options['classMapB'], 
        
        print("carregando imagens a serem processadas com Gap Fill")  
        print("from >> ", self.options['input_asset'])        
        self.imgClass = ee.Image(os.path.join(self.options['input_asset'],self.name_imgClass))

        # self.imgClass = self.imgClass.select(self.lstbandNames)
        # print("todas as bandas \n === > ", self.imgClass.bandNames().getInfo())
        # sys.exit()
   
       
    def dictionary_bands(self, key, value):
        imgT = ee.Algorithms.If(
                        ee.Number(value).eq(2),
                        self.imgClass.select([key]).byte(),
                        ee.Image().rename([key]).byte().updateMask(self.imgClass.select(0))
                    )
        return ee.Image(imgT)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _remap_col10(self, band_name, rename_to):
        """Seleciona e remapeia uma banda do mapa col10."""
        return (self.imgMap10
                    .select(band_name)
                    .remap(self.options['classMapB'], self.options['classNew'])
                    .rename(rename_to))

    def _class_corrections(self, img, col10_ref):
        """
        Aplica regras de correção de classe usando col10 como referência.
          - Classe 33 permanece se col10 remapeado é 33 ou 3
          - Classe 19 permanece se col10 remapeado é 19, 21 ou 15
          - Classe 36 permanece se col10 remapeado é 36, 21 ou 15
        Caso contrário o pixel recebe o valor do col10 remapeado.
        """
        cond33 = img.eq(33).And(col10_ref.eq(33).Or(col10_ref.eq(3)).Not())
        img = img.where(cond33, col10_ref)

        cond19 = img.eq(19).And(col10_ref.eq(19).Or(col10_ref.eq(21)).Or(col10_ref.eq(15)).Not())
        img = img.where(cond19, col10_ref)

        cond36 = img.eq(36).And(col10_ref.eq(36).Or(col10_ref.eq(21)).Or(col10_ref.eq(15)).Not())
        img = img.where(cond36, col10_ref)

        return img

    # ── Correção de pixels 0 que deveriam ser 33 ─────────────────────────────

    def _fix_zero_as_33(self, img, band, col10_yr, ref_img=None):
        """
        Pixels com valor 0 que deveriam ser classe 33:
          1. Se col10 remapeado == 33 no mesmo pixel → substitui por 33
          2. Se ref_img (ex: filled[2024]) == 33 → substitui por 33 (para 2025)
        col10_yr: ano de referência do col10 (int), limitado ao year_col10_max.
        """
        yr10_band = f'classification_{min(col10_yr, self.options["year_col10_max"])}'
        col10r    = self._remap_col10(yr10_band, band)
        zero_px   = img.eq(0)

        # correção principal via col10
        img = img.where(zero_px.And(col10r.eq(33)), ee.Image.constant(33).rename(band))

        # correção adicional via ano de referência (ex: 2024 preenchido → 2025)
        if ref_img is not None:
            zero_px = img.eq(0)   # reavalia após primeira correção
            img = img.where(zero_px.And(ref_img.eq(33)), ee.Image.constant(33).rename(band))

        return img

    # ── Gap fill ─────────────────────────────────────────────────────────────

    def applyGapFill(self):
        yr_max10 = self.options['year_col10_max']

        # ── Passo 1: série corrigida (remap col11 + correções por col10) ─────
        # Garante que as classes 33/19/36 só permanecem onde o col10 confirma.
        corrected = {}
        for yy in self.years:
            band  = f'classification_{yy}'
            yr10  = f'classification_{min(yy, yr_max10)}'

            col11r = (self.imgClass
                          .select(band)
                          .remap(self.options['classMapB'], self.options['classNew'])
                          .rename(band))
            col10r = self._remap_col10(yr10, band)

            corrected[yy] = self._class_corrections(col11r, col10r)
            print(f"  [corr] {band}")

        # Imagem multi-banda para o reducer firstNonNull (série completa corrigida)
        corrected_stack = ee.Image.cat([corrected[yy] for yy in self.years])

        # ── Passo 2: gap fill ao contrário (2025 → 1986) ─────────────────────
        # Para cada gap, usa o primeiro pixel não-nulo dos anos FUTUROS (mais
        # recente primeiro). Isso mantém o valor do último ano observado.
        filled = {}

        # 2025: sem referência futura → gaps preenchidos pelo col10
        # (correção 0→33 via 2024 será aplicada depois, quando filled[2024] existir)
        b25    = 'classification_2025'
        c10_25 = self._remap_col10(f'classification_{yr_max10}', b25)
        mg25   = corrected[2025].mask().Not()
        f25    = corrected[2025].unmask(0).blend(c10_25.updateMask(mg25))
        f25    = self._fix_zero_as_33(f25, b25, 2025)   # fix via col10 (2023)
        filled[2025] = f25
        print("  [fill] classification_2025 (col10 para gaps)")

        for yy in range(2024, 1985, -1):
            band    = f'classification_{yy}'
            corrImg = corrected[yy]
            maskGap = corrImg.mask().Not()

            # Banda futura em ordem decrescente (mais recente primeiro)
            future_bands = [f'classification_{y}' for y in range(2025, yy, -1)]
            first_future = (corrected_stack
                                .select(future_bands)
                                .reduce(ee.Reducer.firstNonNull())
                                .rename(band))

            # Pixels com gap mas sem nenhum futuro disponível
            no_future = maskGap.And(first_future.mask().Not())

            filledImg = corrImg.unmask(0).blend(first_future.updateMask(maskGap))

            # Anos ≤ 1995: gaps restantes (sem futuro) → fallback col10
            if yy <= 1995:
                yr10  = f'classification_{min(yy, yr_max10)}'
                c10r  = self._remap_col10(yr10, band)
                filledImg = filledImg.where(no_future, c10r)

            # corrige pixels 0 que deveriam ser 33 (via col10)
            filledImg    = self._fix_zero_as_33(filledImg, band, yy)
            filled[yy]   = filledImg
            print(f"  [fill] {band}")

        # 2025: correção adicional usando 2024 já preenchido como referência
        filled[2025] = self._fix_zero_as_33(filled[2025], b25, 2025, ref_img=filled[2024])
        print("  [fix33] classification_2025 corrigido com ref 2024")

        # 1985: 1º col10, 2º usar 1986 já preenchido para gaps restantes
        b85    = 'classification_1985'
        corr85 = corrected[1985]
        c10_85 = self._remap_col10('classification_1985', b85)
        mg85   = corr85.mask().Not()

        f85        = corr85.unmask(0).blend(c10_85.updateMask(mg85))
        no_c10_85  = mg85.And(c10_85.mask().Not())
        f85        = f85.where(no_c10_85, filled[1986])
        f85        = self._fix_zero_as_33(f85, b85, 1985)
        filled[1985] = f85
        print("  [fill] classification_1985 (col10 + 1986)")

        # ── Passo 3: monta imagem final ───────────────────────────────────────
        baseImgMap = ee.Image().toByte()
        for yy in self.years:
            baseImgMap = baseImgMap.addBands(filled[yy])

        imageFilledTn = ee.Image.cat(baseImgMap).select(self.lstbandNames)
        return imageFilledTn.updateMask(self.bacia_raster)

    def processing_gapfill(self):

        # apply the gap fill
        imageFilled = self.applyGapFill()
        print(" 🚨🚨🚨  Applying filter Gap Fill 🚨🚨🚨 ")
        print(imageFilled.bandNames().getInfo())
        # sys.exit()
        name_toexport = f'filterGF_BACIA_{self.id_bacias}_GTB_V{self.options['version_output']}_{self.num_clases}cc'
        imageFilled = (ee.Image(imageFilled)
                        .updateMask(self.bacia_raster)
                        .set(
                            'version', self.options['version_output'], 
                            'biome', 'CAATINGA',
                            'source', 'geodatin',
                            'model', "GTB",
                            'type_filter', 'gap_fill',
                            'num_class', self.num_clases,
                            'collection', '11.0',
                            'id_bacias', self.id_bacias,
                            'sensor', 'Landsat',
                            'system:footprint' , self.geom_bacia.coordinates()
                        )
        )
        
        self.processoExportar(imageFilled, name_toexport)

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc):
        
        idasset =  os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId':idasset, 
            'region':self.geom_bacia,#.getInfo()['coordinates'],
            'scale': 30, 
            'maxPixels': 1e13,
            "pyramidingPolicy":{".default": "mode"}
        }
        task = ee.batch.Export.image.toAsset(**optExp)
        task.start() 
        print("salvando ... " + nomeDesc + "..!")
        # print(task.status())
        for keys, vals in dict(task.status()).items():
            print ( "  {} : {}".format(keys, vals))


param = {    
    'bioma': "CAATINGA", #nome do bioma setado nos metadados  
    'numeroTask': 6,
    'numeroLimit': 50,
    'conta' : {
        '0': 'caatinga01',
        '7': 'caatinga02',
        '14': 'caatinga03',
        '21': 'caatinga04',
        '28': 'caatinga05',        
        '35': 'solkan1201',   
        '42': 'superconta', 
    }
}
relatorios = open("relatorioTaskXContas.txt", 'a+')
#============================================================
#========================METODOS=============================
#============================================================
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
            ee.Initialize(project= projAccount) # project='ee-cartas775sol'
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


listaNameBacias = [
    '765', '7544', '7541', '7411', '746', '7591','7746',
    '7592', '761111', '761112', '7612', '7613', '7614',
    '7615', '771', '7712', '772', '7721', '773', '7741',
    '7754', '7761', '7764', '7691', '7581', '7625', '7584',
    '751', '752', '7616', '745', '7424', '7618', '7561',
    '755', '7617', '7564', '7422', '76116', '7671', '757',
    '766', '753', '764', '7619', '7443', '7438', '763',
    '7622'
]

cont = 49
cont = gerenciador(cont)
# applyGdfilter = False
for idbacia in listaNameBacias[:]:
    print("-----------------------------------------")
    print("----- PROCESSING BACIA {} -------".format(idbacia))    
    aplicando_gapfill = processo_gapfill(idbacia, False) # added band connected is True
    aplicando_gapfill.processing_gapfill()
    