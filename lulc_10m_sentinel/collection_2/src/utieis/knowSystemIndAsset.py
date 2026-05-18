import ee
import sys
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

# salva ftcol para um assetindexIni
def save_ROIs_toAsset(collection, name):
    outAssetROIs = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/region'
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': outAssetROIs + "/" + name
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()

    print(f"⚡️⚡ exportando ROIs da bacia << {name} >> ...! ⚡️⚡")


listaNameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
]

dictCode = {
    '7754': '775',
    '7581': '758',
    '7584': '758',
    '7561': '756',
    '7564': '756',
    '761111': '76111',
    '761112': '76111', 
    '7761': '776',
    '7764': '776',
    '7671': '767', 
    '7411': '741',
    '7541': '754',
    '7544': '754',
    '7591': '759',
    '7592': '759',
}
lstChange = [kk for kk in dictCode.keys() ]
# asset_cruzN245 = 'projects/mapbiomas-arida/ALERTAS/auxiliar/bacias_hidrografica_caatinga_BdivN245'
asset_cruzN245 = 'users/mapbiomascaatinga04/bacias_final_caatingaa'
featrtRegcruzN245 = ee.FeatureCollection(asset_cruzN245)
exportFeat = False
print("size ", featrtRegcruzN245.size().getInfo())
# print("show the first ", featrtRegcruzN245.first().getInfo())

lstCod = featrtRegcruzN245.reduceColumns(ee.Reducer.toList(),['nunivotto4']).get('list').getInfo()

print("know the list code ", lstCod)
print(len(lstCod))

for cc, code in enumerate(lstCod):
    print(f"# {cc} com code nunivotto4 {code}")
    feattmp = featrtRegcruzN245.filter(ee.Filter.eq('nunivotto4', code)).first()
    feattmp = ee.Feature(feattmp).buffer(5000)
    if code in lstChange:
        feattmp = feattmp.set('nunivotto3', dictCode[code])
        print("    change by ==> ", dictCode[code])
    else:
        feattmp = feattmp.set('nunivotto3', code)
    
    if exportFeat:
        nameExp = 'region_' + str(code)
        save_ROIs_toAsset(ee.FeatureCollection([feattmp]), nameExp)