import ee
import sys
from tqdm import tqdm
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
    outAssetROIs = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA'
    optExp = {
        'collection': collection,
        'description': name,
        'assetId': outAssetROIs + "/" + name
    }

    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()

    print(f"⚡️⚡ exportando ROIs da bacia << {name} >> ...! ⚡️⚡")

def GetPolygonsfromFolder(dictAsset):   

    getlistPtos = ee.data.getList(dictAsset)
    ColectionPtos = ee.FeatureCollection([])
    
    for idAsset in tqdm(getlistPtos):         
        print("join asset ", idAsset.get('id').replace(dictAsset['id'], "..."))
        feattmp = ee.FeatureCollection(idAsset.get('id'))    
        ColectionPtos = ColectionPtos.merge(feattmp)
        
    return ee.FeatureCollection(ColectionPtos)


inputAssetROIs = {'id':'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/region'}
featRegions = GetPolygonsfromFolder(inputAssetROIs)

namexp = 'bacias_hidrografica_caatinga_49_regions'
save_ROIs_toAsset(ee.FeatureCollection(featRegions), namexp)