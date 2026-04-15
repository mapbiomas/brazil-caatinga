import os
import numpy as np
import pandas as pd



nameTable = 'areaXclasse_CAATINGA_Col90_red.csv'
dfStat = pd.read_csv(nameTable)

print("shape of table ", dfStat.shape)
# print(dfStat.head(10))


lstRegionsStat = [    
    '7754', '7691', '7581', '7625', '7584', '751', '752', 
    '7616', '745', '7424', '773', '7612', '7613', '7614',
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]
colunasInt = ['area', 'classe', 'year', 'Bacia']
lstDF = []
for reg in lstRegionsStat:
    print("Region = ", reg)
    dfStatReg = dfStat[dfStat['Bacia'] == reg][colunasInt]
    print("shape of table ", dfStatReg.shape)
    totalYY = np.sum(dfStatReg[dfStatReg['year'] == 2016]['area'].tolist())
    dfStatReg['percent'] =  round((dfStatReg['area'] * 100 ) / totalYY, 2)
    print(dfStatReg.head(10))
    print(totalYY, " <> ", dfStatReg.columns)
    print("=================================================")
    lstDF.append(dfStatReg)


concat_df  = pd.concat(lstDF, ignore_index=True) #
print("temos {} filas ".format(concat_df.shape))
concat_df.head()

concat_df.to_csv('areaXclasse_CAATINGA_Col90_percent.csv', index= False)