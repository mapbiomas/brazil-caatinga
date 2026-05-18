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

def GetPolygonsfromFolder(assetFolder, sufixo):
  
    getlistPtos = ee.data.getList(assetFolder)
    lstBacias = []
    for cc, idAsset in enumerate(getlistPtos): 
        path_ = idAsset.get('id') 
        lsFile =  path_.split("/")
        name = lsFile[-1]
        idBacia = name.split('_')[0]
        if idBacia not in lstBacias:
            lstBacias.append(idBacia)
        # print(name)
        # if str(name).startswith(sufixo): AMOSTRAS/col7/CAATINGA/classificationV
        if sufixo in str(name): 
            print("eliminando {}:  {}".format(cc, name))
            print(path_)
            # ee.data.deleteAsset(path_) 
    
    print(lstBacias)

asset ={'id' :'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/ROIsAflor'}
# asset = {'id':"projects/nexgenmap/SAD_MapBiomas/Caatinga/tiles_grides/x_tiles"}

GetPolygonsfromFolder(asset, 'cAfl')  # 

