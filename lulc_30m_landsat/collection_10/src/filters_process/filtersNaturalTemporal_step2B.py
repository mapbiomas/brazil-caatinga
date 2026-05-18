#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
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
class processo_filterTemporal(object):

    options = {
            # 'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
            'output_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Temporal',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/SpatialV3',
            'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalA',
            # 'input_asset': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill',
            'asset_bacias_buffer' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',   
            'classMapB': [3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 35, 36, 39, 40, 41, 46, 47, 48, 49, 50, 62],
            'classNew':  [4, 4, 4, 4, 4,  4,  4,  4, 21, 21, 21, 21, 21, 22, 22, 22, 22, 33, 29, 22, 33,  4, 33, 21, 21, 21, 21, 21, 21, 21, 21,  4,  4, 21], 
            'classNat':  [1, 1, 1, 1, 1,  1,  1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  0],    
            'last_year' : 2024,
            'first_year': 1985,
            'janela_bef' : 3,
            'step': 1
        }

    def __init__(self, name_bacia):
        self.id_bacias = name_bacia
        self.versoutput = 5
        self.versionInput = 5
        self.geom_bacia = (ee.FeatureCollection(self.options['asset_bacias_buffer'])
                    .filter(ee.Filter.eq('nunivotto4', name_bacia))
        )
        geomBacia = self.geom_bacia.map(lambda f: f.set('id_codigo', 1))
        self.bacia_raster = geomBacia.reduceToImage(['id_codigo'], ee.Reducer.first()).gt(0)            
        self.geom_bacia = self.geom_bacia.geometry()            

        self.years = [yy for yy in range(self.options['first_year'], self.options['last_year'] + 1)]  
        # self.years = [kk for kk in years.sort(reverse= False)]
        self.lstbandNames = ['classification_' + str(yy) for yy in range(self.options['first_year'], self.options['last_year'] + 1)]


        self.imgClass = (
                    ee.ImageCollection(self.options['input_asset'])
                        .filter(ee.Filter.eq('version', self.versionInput))
                        # só o Gap-fill tem id_bacia o resto tem id_bacias
                        .filter(ee.Filter.eq('id_bacias', name_bacia ))  
                        # .first()
                )
        # print(" list of bands  loaded \n  ", self.imgClass.size().getInfo())
        # print(self.imgClass.first().getInfo())
        if 'Temporal' in self.options['input_asset']:
            self.imgClass = self.imgClass.filter(ee.Filter.eq('janela', self.options['janela_bef']))

        self.imgClass =self.imgClass.first()
        print(" list of bands  loaded \n  ", self.imgClass.bandNames().getInfo())

        # sys.exit()
    ################### CONJUNTO DE REGRAS PARA CONSTRUIR A LISTA DE BANDAS ##############
    """ 
        Se algum pixels ou mais até o 1990 forem natural, e 1990 e 1991 forem natural
        então todos eles viram natural 
    """
    def regra_primeiraJ6(self, janela, delta, lstYears):
        """Retorna a primeira janela no formato [ano4, ano0, ano1, ano2, ano3, ano5]."""
        if len(lstYears) < 6:
            return lstYears  # Fallback se não houver anos suficientes
        return [lstYears[4], lstYears[0], lstYears[1], lstYears[2], lstYears[3], lstYears[5]]


    def mapeiaAnos(self, ano, janela, anos):
        """Mapeia os anos em uma janela móvel, com regra especial para o primeiro ano."""
        lsBandAnos = ['classification_' + str(item) for item in anos]
        indice = anos.index(ano)
        delta = janela // 2  # Metade da janela para cada lado
        
        # Caso especial: primeiro ano (usa regra_primeiraJ6)
        if ano == self.options['first_year']:
            return self.regra_primeiraJ6(janela, delta, lsBandAnos)
        
        # Caso repetido: primeiro ano (usa regra_primeiraJ6)
        elif ano == self.options['first_year'] + 2 or  ano == self.options['first_year'] + 3 :
            return [] ##self.regra_segundaJ6(janela, delta, lsBandAnos)
        
       
        # Caso especial: últimos anos (não há anos suficientes à frente)
        if indice + delta >= len(anos):
            return []
        
        # Janela normal (centrada no 'ano')
        inicio = max(0, indice - delta)
        fim = inicio + janela
        return lsBandAnos[inicio:fim]

    #### https://code.earthengine.google.com/1f9dd3ab081d243fa9d7962e06348579            

    def mask_of_yearss(self, valor_cc, imagem, listaBND):
        """Creates a binary mask based on band values meeting specific conditions.
        
        Args:
            valor_cc: Target value to match in first/last bands
            imagem: ee.Image or image ID to process
            listaBND: List of band names to use
            
        Returns:
            ee.Image binary mask where:
            - First band == valor_cc
            - Middle bands meet sum condition
            - Last band == valor_cc
        """
        img = ee.Image(imagem)
        num_bands = ee.List(listaBND).size()
        cond = num_bands.gt(1)
        
        # # Input validation
        # if num_bands < 3:
        #     raise ValueError("listaBND must contain at least 3 bands")
        
        # Create base masks
        first_band_mask = img.select(ee.List(listaBND).get(0)).eq(valor_cc)
        last_band_mask = img.select(ee.List(listaBND).get(-1)).eq(valor_cc)
        
        # Process middle bands
        middle_bands = ee.List(listaBND).slice(1, ee.Number(ee.List(listaBND).length()).subtract(1))
        sum_reducer = ee.Reducer.sum()
        middle_sum = ee.Algorithms.If(
            cond,
            img.select(middle_bands).reduce(sum_reducer),
            # If only one middle band, no need to sum
            img.select(ee.List(middle_bands).get(0))
        )
        
        # Apply different conditions based on valor_cc
        sum_condition = ee.Algorithms.If(
                            valor_cc == 1,
                            ee.Image(middle_sum).gt(0),
                            ee.Image(middle_sum).lt(ee.Number(num_bands).subtract(2))
                        )
        # Combine all conditions
        final_mask = first_band_mask.And(sum_condition).And(last_band_mask)
        
        return final_mask

    def reclass_natural_Antropic(self, raster_maps, listYYbnd):
        mapstemporal = ee.Image().byte()
        lstRemap = []
        for mm, bnd_year in enumerate(listYYbnd):
            tmp_raster = raster_maps.select(bnd_year).remap(self.options['classMapB'], self.options['classNat'])
            mapstemporal = mapstemporal.addBands(tmp_raster)
            if mm == 0:
                lstRemap.append('remapped')
            else:
                lstRemap.append(f'remapped_{mm}')
        
        return mapstemporal.select(lstRemap).rename(listYYbnd)

    def reclass_natural_Antropics(self, raster_maps, listYYbnd):
        """Reclassifica valores de raster conforme mapeamento de classes.
        
        Otimizações:
        - Elimina loop desnecessário
        - Reduz operações de adição de bandas
        - Usa operações vetorizadas do Earth Engine
        - Minimiza conversões de tipo
        
        Args:
            raster_maps: Imagem contendo as bandas a serem reclassificadas
            listYYbnd: Lista de nomes de bandas para processar
            
        Returns:
            Imagem com bandas reclassificadas
        """
        # Cria lista de operações de reclassificação em paralelo
        remapped_bands = ee.List(listYYbnd).map(
            lambda bnd: raster_maps.select(bnd)
                                .remap(self.options['classMapB'], 
                                        self.options['classNat'])
                                .rename(bnd)
        )
        
        # Converte a lista de bandas para uma imagem multicamada
        result_image = ee.ImageCollection(remapped_bands).toBands()
        
        # Renomeia as bandas para manter os nomes originais
        return result_image.rename(listYYbnd)

    def applyTemporalFilter(self, showinterv):
        """
        Aplica filtro temporal em séries de classificação usando janelas móveis.
        
        Otimizações:
        - Processamento vetorizado com Earth Engine
        - Redução de operações redundantes
        - Melhor gestão de memória
        - Cálculos mais eficientes
        
        Args:
            showinterv: Flag para mostrar informações de debug
        """
        id_class = 1
        mjanela = 6
        delta = mjanela // 2
        
        # 1. Pré-processamento: criar lista de janelas
        colectAnos = ee.List([self.mapeiaAnos(ano, mjanela, self.years) for ano in self.years])
        
        # 2. Função para processar cada janela
        def process_window(lstyear, cc, rasterClass):
            lstyear = ee.List(lstyear)
            cc = ee.Number(cc)
            
            # Condição para janelas válidas
            isValid = lstyear.size().gt(6)
            
            # Processamento principal
            def process_valid_window():
                band_C1 = lstyear.get(1)
                
                # Reclassificação
                rasterReclass = self.reclass_natural_Antropics(rasterClass, lstyear)
                
                # Criação da máscara
                imgstmp_masks = ee.Algorithms.If(
                    cc.eq(0),
                    self.mask_of_yearss(id_class, rasterReclass, lstyear),
                    self.mask_of_yearss(
                                id_class, 
                                new_band.select(lstyear.slice(0, 2))
                                    .addBands(rasterReclass.select(lstyear.slice(2, mjanela))),
                                lstyear
                            )
                )
                
                # Atualização do mapa
                new_band = rasterReclass.select(band_C1).blend(imgstmp_masks.selfMask())
                map_change_year = (rasterClass.select(band_C1)
                                        .blend(imgstmp_masks.selfMask().multiply(
                                            rasterClass.select(lstyear.get(-1))))
                ).rename(band_C1)
                
                return {
                    'mapReclass': new_band,
                    'map_change_year': map_change_year,
                    'debug_info': ee.Algorithms.If(showinterv, lstyear, None)
                }
            
            # Processamento para janelas inválidas
            def process_invalid_window():
                prev_lstyear = colectAnos.get(cc.subtract(1))
                last_band = self.imgClass.select(prev_lstyear.get(-1))
                
                def add_bands(bnd, img):
                    bnd = ee.String(bnd)
                    change_band = self.imgClass.select(prev_lstyear.get(1)).blend(
                        imgstmp_masks.selfMask().multiply(last_band)
                    ).rename(bnd)
                    return ee.Image(img).addBands(change_band)
                
                imgOutput = ee.List(prev_lstyear.slice(2, -1)) \
                    .iterate(add_bands, ee.Image().byte())
                
                return {
                    'mapReclass': None,
                    'map_change_year': imgOutput.addBands(last_band),
                    'debug_info': None
                }
            
            result = ee.Algorithms.If(
                        isValid, 
                        process_valid_window(), 
                        # process_invalid_window()
                        ee.Image().byte()
                    )
            return result
        
        # 3. Processamento paralelo das janelas
        initial_state = {
            'mapReclass': ee.Image().byte(),
            'imgOutput': ee.Image().byte(),
            'count': 0
        }
        print(colectAnos)
        jj = 0
        image_resultado = process_window(colectAnos.get(jj), jj, self.imgClass)
        print(image_resultado.getInfo())

        # final_state = (ee.List.sequence(0, colectAnos.size().subtract(1)) 
        #                     .iterate(
        #                         lambda cc, state: self.process_window_iteration(colectAnos, cc, state, showinterv),
        #                         initial_state
        #                     ))
        
        # 4. Preparação da imagem final
        # imgOutput = ee.Image(final_state.get('imgOutput')).select(self.lstbandNames)
        
        sys.exit()
        # 5. Adicionar metadados e exportar
        imgOutput = imgOutput.updateMask(self.bacia_raster).set({
            'version': self.versoutput,
            'id_bacias': self.id_bacias,
            'biome': 'CAATINGA',
            'type_filter': 'temporal',
            'collection': '10.0',
            'janela': 6,
            'sensor': 'Landsat',
            'system:footprint': self.geom_bacia
        })
        
        name_toexport = f"filterTP_BACIA_{self.id_bacias}_GTB_J6_V{self.versoutput}"
        self.processoExportar(imgOutput, name_toexport, self.geom_bacia)

    def process_window_iteration(self, colectAnos, cc, state, showinterv):
        """
        Processa cada janela temporal durante a iteração, com tratamento correto de escopo.
        
        Args:
            colectAnos: Lista de listas de bandas/anos
            cc: Contador de iteração (índice)
            state: Dicionário com estado atual (mapReclass, imgOutput, count, last_mask)
            showinterv: Flag para debug
        
        Returns:
            Estado atualizado com:
            - mapReclass: Bandas reclassificadas acumuladas
            - imgOutput: Resultado final sendo construído
            - count: Contador de iterações
            - last_mask: Última máscara gerada (para uso em janelas inválidas)
        """
        lstyear = ee.List(colectAnos.get(cc))
        isValid = lstyear.size().gt(1)
        
        def valid_window_process():
            band_C1 = ee.String(lstyear.get(1))
            
            # 1. Reclassificação
            rasterReclass = self.reclass_natural_Antropics(self.imgClass, lstyear)
            
            # 2. Geração de máscara
            input_img = ee.Algorithms.If(
                ee.Number(cc).eq(0),
                rasterReclass,
                state.get('mapReclass').select(lstyear.slice(0, 2))
                    .addBands(rasterReclass.select(lstyear.slice(2, 6)))
            )
            
            current_mask = self.mask_of_yearss(1, input_img, lstyear)
            
            # 3. Atualização de bandas
            new_band = rasterReclass.select(band_C1).blend(current_mask.selfMask())
            
            map_change_year = (self.imgClass.select(band_C1)
                                        .blend(current_mask.selfMask().multiply(self.imgClass.select(lstyear.get(-1))))
                                        .rename(band_C1))
            
            return state.update({
                'mapReclass': state.get('mapReclass').addBands(new_band),
                'imgOutput': state.get('imgOutput').addBands(map_change_year),
                'count': state.get('count').add(1),
                'last_mask': current_mask  # Armazena a máscara para uso posterior
            })
        
        def invalid_window_process():
            prev_lstyear = ee.List(colectAnos.get(ee.Number(cc).subtract(1)))
            last_band = self.imgClass.select(prev_lstyear.get(-1))
            
            # Usa a última máscara válida armazenada no estado
            last_valid_mask = ee.Image(state.get('last_mask'))
            
            # Adiciona bandas de mudança para anos intermediários
            imgOutput = ee.List(prev_lstyear.slice(2, 5)).iterate(
                lambda bnd, img: ee.Image(img).addBands(
                    self.imgClass.select(prev_lstyear.get(1)).blend(
                        last_valid_mask.selfMask().multiply(last_band)
                    ).rename(bnd)
                ),
                ee.Image().byte()
            )
            
            return state.update({
                'imgOutput': state.get('imgOutput').addBands(imgOutput).addBands(last_band),
                'count': state.get('count').add(1),
                'last_mask': last_valid_mask  # Mantém a mesma máscara
            })
        
        return ee.Algorithms.If(isValid, valid_window_process(), invalid_window_process())
            

    #exporta a imagem classificada para o asset
    def processoExportar(self, mapaRF,  nomeDesc, geom_bacia):
        
        idasset =  os.path.join(self.options['output_asset'], nomeDesc)
        optExp = {
            'image': mapaRF, 
            'description': nomeDesc, 
            'assetId': idasset, 
            'region': geom_bacia, #.getInfo()['coordinates'],
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
    'numeroTask': 6,
    'numeroLimit': 20,
    'conta' : {
        '0': 'caatinga01',
        '4': 'caatinga02',
        '6': 'caatinga03',
        '8': 'caatinga04',
        '10': 'caatinga05',        
        '12': 'solkan1201',    
        '14': 'solkanGeodatin',
        '16': 'superconta'      
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
            ee.Initialize(project= projAccount) # project='ee-cartassol'
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
    '765', '7544', '7541', '7411', '746', '7591', '7592', 
    '761111', '761112', '7612', '7613', '7614', '7615', 
    '771', '7712', '772', '7721', '773', '7741', '7746', '7754', 
    '7761', '7764',   '7691', '7581', '7625', '7584', '751',     
     '7616', '745', '7424', '7618', '7561', '755', '7617', 
    '7564', '7422', '76116', '7671', '757', '766', '753', 
    '764', '7619', '7443', '7438', '763', '7622', '752'
]

# listaNameBacias = ['7411', '7422', '751', '752', '753', '7541' ]
print("ver quantidad ", len(listaNameBacias))
# sys.exit()

lstBacias = []
changeAcount = False
lstqFalta =  []
cont = 16
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Gap-fillV2'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill'
# input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency'
input_asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Temporal'
if changeAcount:
    cont = gerenciador(cont)
version = 5
janela = 3
modelo = 'GTB'
listBacFalta = []
knowMapSaved = False
show_interval = True
for cc, idbacia in enumerate(listaNameBacias[:]):   
    if knowMapSaved:
        try:
            nameMap = f"filterTP_BACIA_{idbacia}_GTB_J{janela}_V{version}"
            # # nameMap = 'filterSP_BACIA_'+ str(idbacia) + "_V" + str(version)
            # print(nameMap)
            imgtmp = ee.Image(os.path.join(input_asset, nameMap))
            # imgtmp = (ee.ImageCollection(input_asset)
            #                 # .filter(ee.Filter.eq('version', version))
            #                 .filter(ee.Filter.eq('id_bacia', idbacia ))
            #                 .first()
            #     )
            # print("know how many images exist ", imgtmp.size().getInfo())
            print(f" 👀> {cc} loading {imgtmp.get('system:index').getInfo()}", len(imgtmp.bandNames().getInfo()), "bandas ✅ ")
        except:
            listBacFalta.append(idbacia)
    else: 
        if idbacia not in lstBacias:
            # cont = gerenciador(cont)            
            print("----- PROCESSING BACIA {} -------".format(idbacia)) 
            aplicando_TemporalFilter = processo_filterTemporal(idbacia)            
            aplicando_TemporalFilter.applyTemporalFilter(show_interval)
            if cc == 0:
                show_interval = False
