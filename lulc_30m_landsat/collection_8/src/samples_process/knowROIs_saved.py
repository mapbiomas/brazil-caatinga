#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import gee

import collections
collections.Callable = collections.abc.Callable
try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


assetROIs = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster/'


nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]
lst_faltantes = open("lista_ROIsv6N2cluster_faltantes.txt", 'w+')
for _nbacia in nameBacias[:]:
    for yyear in range(1985, 2023):
        name = _nbacia + "_" + str(yyear) + "_c1"
        try:
            feat_tmp = ee.FeatureCollection(assetROIs + name)
            print(f"size {_nbacia} in {yyear} = {feat_tmp.size().getInfo()}")
        except:
            lst_faltantes.write(name + '\n')

