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


# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2YY'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YY'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2Y'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyVA'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_all'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials_int'
# asset= 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/transition'
# asset= 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Merger'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatials'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Temporal'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/TemporalCC'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV1'
asset= 'projects/mapbiomas-brazil/assets/WATER/COLLECTION-4/classification-monthly'
lsBacias = [
    '7754', '7691', '7581', '7625', '7584',  '7614', '751',
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111','761112', 
    '7741', '7422', '76116', '7761', '7671','7615','7411', 
    '7764', '757', '771','7712','766','7746','753','764', 
    '7541', '7721', '772', '7619','7443', '765', '7544','7438', 
    '763', '7591', '7592', '7622', '746'
]

eliminar_files = False
# lstyear=[2025], 
Get_Remove_Array_from_ImgCol(asset, play_eliminar= eliminar_files)  