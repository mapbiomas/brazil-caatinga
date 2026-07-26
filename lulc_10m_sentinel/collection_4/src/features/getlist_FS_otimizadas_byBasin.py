import os
import glob
import copy
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path

pathparent = str(Path(os.getcwd()).parents[0])
# sys.path.append(pathparent)
print(pathparent)
pathData = os.path.join(pathparent, 'dados')
pathData = os.path.join(pathData, 'feature_select_col10')
print('we load CSVs from \n >>> ', pathData)

lstFilesFS = glob.glob(pathData + '/*.csv' )
# get first list of basin
lstBasin = []
dictBasinYY = {}

for cc, nfile in enumerate(lstFilesFS):
    print(f" #{cc} >> {nfile.split('/')[-1]}")
    nameBasin =  nfile.split('/')[-1].split("_")[1]
    yyear = nfile.split('/')[-1].split("_")[-1].replace(".csv", "")  

    if nameBasin not in lstBasin:
        lstBasin.append(nameBasin)
        dictBasinYY[nameBasin] = [yyear]
        # print(f'iniciando >> {dictBasinYY[nameBasin]}')
    else:  
        lsttmp = dictBasinYY[nameBasin]
        lsttmp.append(str(yyear))
        dictBasinYY[nameBasin] = copy.deepcopy(lsttmp)
        # print(dictBasinYY[nameBasin])
        
# sys.exit()
dictFSBasin = {}
lstRamking = [f"(1, {kk})" for kk in range(0, 40)]
print("lista de Basin feitas ", lstBasin)
print(f" {len(lstBasin)} feitas")
# sys.exit()
for nbasin in lstBasin[:]:
    print(f"  processing  {nbasin}")
    lstFeat = []
    for cc, yyear in enumerate(dictBasinYY[nameBasin]):
        pathCSV = os.path.join(pathData, f'featuresSelectS2_{nbasin}_{yyear}.csv')
        dftmp = pd.read_csv(pathCSV)
        print(f"#{cc}:",dftmp.head(3))
        dftmp = dftmp[dftmp['ranking'].isin(lstRamking)]
        print(" >>> ", dftmp.shape)
        lsttmp = list(dftmp['features'].tolist())
        for featname in lsttmp:
            if featname not in lstFeat: 
                lstFeat.append(featname)

    print("lista de features selecionadas \n ", lstFeat)
    print(len(lstFeat))
    dictFSBasin[nbasin] = lstFeat


# convert and write JSON object to file 
with open("dict_lst_features_by_basin.json", "w") as outfile:
    json.dump(dictFSBasin, outfile)

for nkey, lstF in dictFSBasin.items():
    print(f" {nkey} : size> {len(lstF)} >>  {lstF}")
    