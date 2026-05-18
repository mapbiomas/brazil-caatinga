#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import json
import csv
import sys

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
# sys.setrecursionlimit(1000000000)


param = {    
    'assetROIs': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv4N4/',
    'anoInicial': 1985,
    'anoFinal': 2022,
    'numeroTask': 6,
    'numeroLimit': 4,
    'conta' : {
        '0': 'caatinga04'              
    },
    'pmtGTB': {
        'numberOfTrees': 72, 
        'shrinkage': 0.005, 
        'samplingRate': 0.8, 
        'loss': 'Huber',#'LeastAbsoluteDeviation', 
        'seed': 0
    },
    'pmtRF': {
        'numberOfTrees': 265, 
        'variablesPerSplit': 25,
        'minLeafPopulation': 40,
        'bagFraction': 0.8,
        'seed': 0
    },
}

#lista de anos
list_anos = [k for k in range(param['anoInicial'],param['anoFinal'] + 1)]
print('lista de anos', list_anos)

#nome das bacias que fazem parte do bioma (38 bacias)
nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]
a_file = open("registroBacia_Year_FeatsSel.json", "r")
dictFeatureImp = json.load(a_file)


def process_classification(nameROis, lstBND):
    featRois = ee.FeatureCollection(param['assetROIs'] + nameROis)
    print(f"Laoding featCol with {featRois.size().getInfo()} features")
    classifierGTB = ee.Classifier.smileGradientTreeBoost(**param['pmtGTB'])\
                                    .train(featRois, 'class', lstBND)

    # classifierRF = ee.Classifier.smileRandomForest(**param['pmtRF'])\
    #                                 .train(featRois, 'class', lstBND)
    print('show befoire ' )
    explainClass = classifierGTB.explain()
    # explainClass = classifierRF.explain()
    metadados = explainClass.importance.getInfo()
    print('show ')
    print("show importance ", metadados)






arqFaltante = open("registros/lstBaciasYearROIsversion4.txt", 'w+')
list_baciaYearFaltan = []
cont = 0
# cont = gerenciador(cont, param)
for _nbacia in nameBacias[:1]:

    print("loading bacia " + _nbacia)     
    for yyear in list_anos[: 2]:
        nameFeat = _nbacia + '_' + str(yyear) + '_c1'
        print("loading FeatureCollection => ", nameFeat)
        bandas_imports = dictFeatureImp[_nbacia][str(yyear)]
        print("bandass \n", bandas_imports)
        try: 
            process_classification(nameFeat, 
                                bandas_imports)

         
        except:
            list_baciaYearFaltan.append(nameFeat)
            arqFaltante.write(nameFeat + '\n')

arqFaltante.close()