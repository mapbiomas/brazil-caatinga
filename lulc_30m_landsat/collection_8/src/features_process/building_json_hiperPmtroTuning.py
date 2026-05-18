
import glob
import sys
import pandas as pd
import json

import arqParametros as arqParams 



nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]

# lsNamesBacias = arqParams.dictBaciasViz[_nbacia]
print("lista de Bacias vizinhas", nameBacias)

path_csvs = '/home/superusuario/Dados/mapbiomas/col8/features/hiperparameter/'
lst_files = glob.glob(path_csvs + '*man.csv')

dict_param = {}

for cc, filecsv in enumerate(lst_files):
    if cc > -1:
        name_csv = filecsv.replace(path_csvs, '')
        print("loading ", name_csv)
        df_tmp = pd.read_csv(filecsv)
        df_tmp = df_tmp[df_tmp['n_estimators'] < 100]
        # print(df_tmp.head(5))
        bacia = name_csv.split("_")[1]
        yyear = name_csv.split("_")[2]
        learning_rate = df_tmp['learning_rate'].tolist()[0]
        n_estimator = df_tmp['n_estimators'].tolist()[0]
        lst_key = [kk for kk in dict_param.keys()]
        if bacia not in lst_key:
            dict_param[bacia] = {
                '2016': [0, 0],
                '2021': [0, 0]
            }
            dict_param[bacia][str(yyear)] = [float(learning_rate), int(n_estimator)]
        else:
            if dict_param[bacia][str(yyear)][1] == 0:
                print('enterando aqui')
                dict_param[bacia][str(yyear)] = [float(learning_rate), int(n_estimator)]


for nbacia, mdict in dict_param.items():
    for kkeys, val_lst in mdict.items():
        print(nbacia, " ", kkeys, " ", val_lst)
        if val_lst[1] == 0:
            if kkeys == '2021':
                dict_param[nbacia][kkeys] = dict_param[nbacia]['2016'] 
            else:
                dict_param[nbacia][kkeys] = dict_param[nbacia]['2021'] 
            print("refez ", nbacia, " ", kkeys, " ", dict_param[nbacia][kkeys] )

lst_key = [kk for kk in dict_param.keys()]
for bacia in nameBacias:
    if bacia not in lst_key:
        print(' bacia = ', bacia)
        baciasViz = arqParams.dictBaciasViz[bacia]
        lstWithPmts = False
        for otherBa in baciasViz:
            if otherBa in lst_key and lstWithPmts == False:
                dict_param[bacia] = {
                                    '2016': dict_param[otherBa]['2016'],
                                    '2021': dict_param[otherBa]['2021']
                                }                                        
                
                lstWithPmts = True

cc = 1
for nbacia, mdict in dict_param.items():
    for kkeys, val_lst in mdict.items():
        print(cc, " ", nbacia, " ", kkeys, " ", val_lst)
    cc += 1
yyear

with open('regBacia_Year_hiperPmtrosTuningfromROIs2Y.json', 'w') as fp:
        json.dump(dict_param, fp)