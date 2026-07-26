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

def Get_Remove_Array_from_ImgCol(asset_imgcol, vers= 0, janela= 0, lstBacias= [], lstyear= [], play_eliminar= False):

    
    imgCol = ee.ImageCollection(asset_imgcol)
    
    if vers > 0:
        imgCol = imgCol.filter(ee.Filter.eq('version', vers))
    if janela > 0:
        imgCol = imgCol.filter(ee.Filter.eq('janela', janela))    
    if len(lstBacias) > 0:
        imgCol = imgCol.filter(ee.Filter.inList('id_bacias', lstBacias))
    if len(lstyear) > 0:
        imgCol = imgCol.filter(ee.Filter.inList('year', lstyear))
    
    lst_id = imgCol.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
    print(f'we will eliminate {len(lst_id)} file image from {asset_imgcol} ')
    
    for cc, idss in enumerate(lst_id):    
        path_ = str(asset_imgcol + '/' + idss)    
        print (f"... eliminando ❌ ... item 📍{cc + 1}/{len(lst_id)} : {idss}  ▶️ ")    
        try:
            if play_eliminar:
                ee.data.deleteAsset(path_)
                print(" > " , path_)
        except:
            print(f" {path_} -- > NAO EXISTE!")


# asset =  'projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/POS-CLASS/Spatials_sieve'
asset = "projects/mapbiomas-workspace/AMOSTRAS/col11/CAATINGA/Classifier/Classify_fromEEMV1"
lsBacias = []

eliminar_files = False
# lstyear=[2025],  lstBacias=lsBacias, vers= 1,
Get_Remove_Array_from_ImgCol(asset,  play_eliminar= eliminar_files)  