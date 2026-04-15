#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# SCRIPT DE CLASSIFICACAO POR BACIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
'''
import sys
import os
import json
import glob
from icecream import ic 
from pathlib import Path


def get_bacias_year_faltam(ndictHist):
    lstNBacias = [
        '741','7421','7422','744','745','746','7492','751','752','753',
        '754','755','756','757','758','759', '7613', '76111','76116',
        '7612','7614','7615','7616','7617', '7618','7619','7621','7622',
        '763','764','765','766','767','771','772','773', '7741','7742',
        '775','776','777','778',
    ]
    lstYear = [kk for kk in range(1985, 2023)]
    lstKeysdict = [kkey[1:] for kkey in ndictHist.keys()]
    # print("all keys ", lstKeysdict)
    # sys.exit()
    lstFalta = []
    for nbacia in lstNBacias:
        for yyear in lstYear:
            nameKey = str(nbacia) + "_" + str(yyear)
            if nameKey not in lstKeysdict:
                lstFalta.append(nameKey)

    return lstFalta

def getPathCSV():
    # get dir path of script 
    mpath = os.getcwd()
    # get dir folder before to path scripts 
    pathparent = str(Path(mpath).parents[0])
    print("path parents ", pathparent)
    # folder results of CSVs ROIs
    mpath_bndImp = pathparent + '/dados/results'
    print("path of CSVs Rois is \n ==>",  mpath_bndImp)
    return mpath_bndImp

def preencher_dict_historico(tmpDict, nameFiletxt):
    partes = nameFiletxt.split('_')
    nbacia = partes[0]
    yyear = partes[1]
    baciaKeys = [kk for kk in tmpDict.keys()]
    if nbacia not in baciaKeys:
        tmpDict[nbacia] = [yyear]
    else:
        lst_tmp = tmpDict[nbacia]
        lst_tmp.append(yyear)
        tmpDict[nbacia] = lst_tmp

    return tmpDict

buildingJson = True
pathResults = getPathCSV()
pathjson = pathResults.replace("results","regJSON")
pathjsonRF = pathjson + "lst_features_selected_bndC8.json"
jsonHistogram = pathjson + "historico_bacias_processFS.json"
lstbndyearFalta = []

if buildingJson:
    dictHist = {}
    dictFeatures = {}
    lstFilesnames = glob.glob(pathResults + "/*.txt")
    print("list de arquivos ", len(lstFilesnames))
    # sys.exit()
    for cc, pathFile in enumerate(lstFilesnames[:]):
        nameFile = pathFile.replace(pathResults, "")
        ic(cc, nameFile)    
        # update the historic of process
        dictHist = preencher_dict_historico(dictHist, nameFile)
        lst_bnd = []
        filetext = open(pathFile)
        for line in filetext:
            line = line.rstrip()
            if line not in lst_bnd:
                if '_1' not in line or '_2' not in line:
                    lst_bnd.append(line)

        
        nameKey = nameFile.replace("_c1.txt", "")
        print(nameKey)
        print(lst_bnd)
        dictFeatures[nameKey] = lst_bnd

    print("          🍀🍀 TERMINANDO 🍀🍀    ")

    with open(pathjsonRF, 'w') as fp:
        json.dump(dictFeatures, fp)
    ic(" -- lst_features_selected_bndC8.json saved ")

    with open(jsonHistogram, 'w') as fp:
        json.dump(dictHist, fp)
    ic(" -- historico_bacias_processFS.json saved ")

else:
    ic(f"file json readed {pathjsonRF}")
    with open(pathjsonRF) as infile:
        dictFeatures = json.load(infile)

    with open(jsonHistogram) as infile:
        dictHist = json.load(infile)

    lstbndyearFalta = get_bacias_year_faltam(dictFeatures)
    if len(lstbndyearFalta) > 0:
        print("lista de faltantes ", lstbndyearFalta)
        for cc, bndY in enumerate(lstbndyearFalta):
            ic(cc, " falta ",bndY)
    else:
        ic("********************* all features ROIs were analised 🍀🍀 *************")

