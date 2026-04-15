import ee
import os
import sys
import collections
collections.Callable = collections.abc.Callable

from pathlib import Path
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize(project= projAccount)
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

# asset = {'id': 'projects/nexgenmap/SAMPLES/Caatinga/ROIs'}
# asset = {'id': 'projects/nexgenmap/SAMPLES/caatinga/ROIs/col6'}
# asset = {'id': 'projects/nexgenmap/SAMPLES/caatinga/ROIs/col6_norm'}
# asset = {'id': 'projects/nexgenmap/SAMPLES/caatinga/ROIs/col6_norm_outlier'}
# asset = {'id': 'projects/nexgenmap/SAMPLES/caatinga/ROIs/col6_outlier'}
# asset ={'id' :'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2'}
# asset ={'id' : 'projects/nexgenmap/SAMPLES/Caatinga'}
# asset = {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN245_allBND'}
# asset = {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsGradeallBNDNormal'}
# asset = {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsv1N245'}
# asset = {'id' : 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/ROIsnotWithLabel'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2red'}

GetPolygonsfromFolder(asset, '')  # 

