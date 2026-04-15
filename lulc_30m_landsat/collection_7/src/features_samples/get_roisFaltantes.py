#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

import ee
import gee
import json
import csv
import sys
import arqParametros as arqParam
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

def getAllFeatsfromFolder(mpath, listaIds):

    getParam = ee.data.getList(mpath)  
    feats_faltantes = []
    ls_presentes = []
    
    for item in getParam:
        # print(item)
        path_feat = item['id']
        # print(path_feat)
        namebacia = path_feat.split('/')[-1][:-4]
        print(namebacia)
        ls_presentes.append(namebacia)

        # if namebacia not in listaIds:
        #     print("====   {} =====".format(namebacia))
        #     feats_faltantes.append(namebacia)
    print("faltantes ")
    for cc, namebacia in enumerate(listaIds):
        print("{} ==> {} contra ".format(cc, namebacia, ))  #ls_presentes[cc]
        if namebacia not in ls_presentes:
            print("====   {} =====".format(namebacia))
            feats_faltantes.append(namebacia)
    print(feats_faltantes)
    text = ''
    for cc, name in enumerate(feats_faltantes):

        if cc > 0 and (cc + 1) % 10 == 0:
            print (text)

            text = ''
        
        else:
            text += '"' + str(name) + '",'


    # print("total CC = ", cc)  

    # print("carregou {} features".format(len(getParam)))
    # return featTotal

lsBacias = [
        '741','7421','7422','744','745','746','7492','751','752','753',
        '754','755','756','757','758','759','7621','7622', '763','764',
        '765','766', '767','771','772','773', '7741','7742','775','776',
        '777','778','76111','76116','7612','7613','7614','7615','7616',
        '7617','7618','7619'
]

# list_bacias = arqParam.listaNameBacias
path = {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsXBaciasBalv13'}
# pathBacias = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/bacias_hidrografica_caatingaN4'
# col_bacias = ee.FeatureCollection(pathBacias)
# lst_names = col_bacias.reduceColumns(ee.Reducer.toList(), ['fid']).get('list').getInfo()

print("lista de names de bacias \n", lsBacias)

getAllFeatsfromFolder(path, lsBacias)
