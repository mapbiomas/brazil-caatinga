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

# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/CLASS/ClassCol8V5'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/merge'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Gap-fill'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Spatial'
asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Temporal'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/POS-CLASS/Frequency'

listBacias = ['777','778']

imgCol = ee.ImageCollection(asset).filter(
                        #   ee.Filter.inList('id_bacia',listBacias)).filter(
                            ee.Filter.eq('version', 10))# .filter(
                                    # ee.Filter.eq('id_bacia', '7422'))
lst_id = imgCol.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
for cc, idss in enumerate(lst_id):    
    # id_bacia = idss.split("_")[2]
    path_ = str(asset + '/' + idss)       
    print ("... eliminando ❌ ... item 📍{} : {}  ▶️ ".format(cc + 1, idss))
    
    try:
        # ee.data.deleteAsset(path_)
        print(path_)
    except:
        print(" NAO EXISTE!")
