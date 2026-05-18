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

# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_estaveis_v2'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_coinciden'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVY'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/toExport' #
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/ilumination'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/grass_aflor'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Temporal'
asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/clean_water'
# lsBacias = [
    # '741','7421','7422','744','745','746','7492','751','752','753',
    # '754','755','756','757','758','759','7621','7622', '763','764',
    # '765','766', '767','771','772','773', '7741','7742','775','776',
    # '777','778','76111','76116', '7614','7616','7618','7619','7613','7612',
    # '7422','744','7492','751','752','757','7622','763',
    # '765','766','767','772','773','7741','7742','776',
    # '778','7612','7613','7615','7617'
# ]


lsBacias = ['7721', '761111']
imgCol = (ee.ImageCollection(asset)
                # .filter(ee.Filter.eq('version', 4)) 
                # .filter(ee.Filter.eq('janela', 4))
                # .filter(ee.Filter.inList('bacia', lsBacias))
)
lst_id = imgCol.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
print(imgCol.aggregate_histogram('name_country').getInfo())
for cc, idss in enumerate(lst_id):    
    # id_bacia = idss.split("_")[2]
    path_ = str(asset + '/' + idss)    
    print ("... eliminando ❌ ... item 📍{} : {}  ▶️ ".format(cc, idss))    
    try:
        ee.data.deleteAsset(path_)
        print(path_)
    except:
        print(" NAO EXISTE!")
