import glob 
import pandas as pd
import ee 

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

# salva ftcol para um assetindexIni
def save_ROIs_toAsset(collection, name_exp):
    asset_output = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs'
    optExp = {
        'collection': collection,
        'description': name_exp,
        'assetId': asset_output + "/" + name_exp
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando a estadistica  $s ...!", name_exp)


pathStat = '/home/superusuario/Dados/mapbiomas/col8/stats/'
file_list = glob.glob(pathStat + '*.csv')
lst_bnd = [
        "blue_median","green_median","red_median","nir_median",
        "swir1_median","swir2_median",         
        "blue_median_wet","green_median_wet","red_median_wet",
        "nir_median_wet","swir1_median_wet","swir2_median_wet",
        "blue_median_dry","green_median_dry","red_median_dry",
        "nir_median_dry","swir1_median_dry","swir2_median_dry", 
    ];
featColStat = ee.FeatureCollection([])
lst_coord = [-37.986, -8.395]
for cc, year in enumerate(range(1985, 2023)):
    nameTable = 'all_statisticsL8' + str(year) + '.csv'    
    pathfile = pathStat + nameTable
    
    if cc > -1:   
        print("loading csv from ", pathfile) 
        df_tmp = pd.read_csv(pathfile)
        print("columns ", df_tmp.columns)
        # print(df_tmp.head(6))
        newdf = df_tmp.describe()
        newdf = newdf.transpose()
        # print(newdf.head())
        # print(newdf.index)
        lst_bnd = [kk for kk in newdf.index]
        # print(newdf.columns)
        colSelect = [ 'mean', 'std', 'min','50%','max']
        colSelRename = [ 'mean', 'std', 'min','median','max']
        newdf = newdf[colSelect]
        newdf.columns = colSelRename
        # print(newdf.columns)
        # print(newdf.head())
        dictFeat = {
            'year': year
            }
        print("valor teste ", newdf['mean']["blue_median_mean"])
        for stat in colSelRename:
            for bnd in lst_bnd:
                dKey = bnd + "_" + stat
                dictFeat[dKey] = newdf[stat][bnd]

        # for kk, val in dictFeat.items():
        #     print(kk, " = ", val)

        point = ee.Geometry.Point(lst_coord)
        featStat = ee.Feature(point, dictFeat)
        featColStat = featColStat.merge(ee.FeatureCollection([featStat]))

print("Feat Collection Statistic have ", featColStat.size().getInfo())
name_export = "all_statistics_landsatCaat"
save_ROIs_toAsset(featColStat, name_export)
