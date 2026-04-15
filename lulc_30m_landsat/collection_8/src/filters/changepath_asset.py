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
import json
import csv
import copy
import sys
import math
import arqParametros as arqParams 
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


listaNameBacias = [
        '741','7421','7422','744','745','746','7492','751','752','753',
        '754','755','756','757','758','759','7621','7622','763','764',
        '765','766','767','771','772','773', '7741','7742','775','776',
        '777','778','76111','76116','7612','7613','7614','7615','7616',
        '7617','7618','7619'
        # "7615","7616","7617","7618","7619"
]
assetout = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial/'
assetInp = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/class_filtered_Sp/'

for nbacia in listaNameBacias:
    nameExp = 'filterSP_BACIA_' + nbacia + '_V1'
    print(f"change file {nbacia} asset from assetInp to assetOut")
    sourceId = assetInp + nameExp
    destinationId = assetout + nameExp
    ee.data.renameAsset(sourceId = sourceId, destinationId= destinationId)