import glob 
import pandas as pd

def get_percent_table(dfArea):
    dfGroup = dfArea[['area', 'year']].groupby('year').sum().reset_index()
    # print(dfGroup.head())
    area_total = dfGroup.iloc[0]['area']
    print("area total ", dfGroup.iloc[0]['area'])
    dfArea['percent'] =  round((dfArea['area'] * 100 ) / area_total, 2)
    return dfArea


def get_percent_tableYY(dfArea):

    area_total = dfArea['area'].sum()
    print("area total ", dfGroup.iloc[0]['area'])
    dfArea['percent'] =  round((dfArea['area'] * 100 ) / area_total, 2)
    return dfArea

path = '/home/superuser/Dados/mapbiomas/dev_collection_sentinel/src/dados/areaBacia'
paths_lst = glob.glob(path + '/*')

for cc, npath in enumerate(paths_lst[:2]):
    print("loading " + npath.replace(path + '/',''))
    dftable = pd.read_csv(npath)
    dftable = dftable.drop(['system:index','.geo'], axis=1)    
    dftable = get_percent_table(dftable)
    print(dftable.columns)
    print(dftable[dftable['year'] == 2023].head())

    dftable23 = dftable[dftable['year'] == 2023]
    area_total = dftable23['area'].sum()
    dftable23['percent'] =  round((dftable23['area'] * 100 ) / area_total, 2)
    print(dftable23.columns)
    print(dftable23.head())