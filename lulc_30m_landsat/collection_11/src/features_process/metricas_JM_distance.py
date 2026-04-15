#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import os  

import json
import sys
import random
import pandas as pd
from tabulate import tabulate

path_filesCSV = '/run/media/superuser/Almacen/mapbiomas/dadosCol10/ROIsv2'
lstFilesCSV = os.listdir(path_filesCSV)

for nameCSV in lstFilesCSV[:1]:
    print(f"name file CSV  == > {nameCSV}" )
    dfStat = pd.read_csv(os.path.join(path_filesCSV, nameCSV))
    dfStat = dfStat.drop(["system:index", ".geo"], axis= 1)

    print("shape ", dfStat.shape)
    print("colunas ", dfStat.columns)
    print(tabulate(dfStat.head(8), headers = 'keys', tablefmt = 'psql'))