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

def GetPolygonsfromFolder(assetFolder, sufixo, lstBacias= [], lstYear= [], play_eliminar= False):
    getlistPtos = ee.data.getList(assetFolder)
    lst_path = []
    sizeFiles = len(getlistPtos)

    for cc, idAsset in enumerate(getlistPtos): 
        path_ = idAsset.get('id') 
        name =  path_.split("/")[-1]
        
        
        if len(lstBacias) > 0 and len(lstYear) > 0:    
            idBacia = name.split('_')[0]
            nyear = int(name.split('_')[1])        
            if idBacia in lstBacias and nyear in lstYear:
                print(" --- passo nas condicionais --- ")
                print(f' {idBacia}    {nyear}    {name}'   )
                # print(path_)
                lst_path.append(path_)
        else:
            if sufixo in str(name): 
                lst_path.append(path_)        
     
        # print(name)
        # if str(name).startswith(sufixo): AMOSTRAS/col7/CAATINGA/classificationV
    cc = 0
    sizeFiles = len(lst_path)
    for npath in lst_path:
        name = npath.split("/")[-1]
        print(f"eliminando {cc + 1}/{sizeFiles}:  {name}")
        print(path_)
        if play_eliminar:
            ee.data.deleteAsset(npath) 

        cc += 1
    
    print(lstBacias)


# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_byGrades'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_byGrades_emb'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_IndAll'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_byGrades_emb'}
asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_cleaned'}
lstbacias = []  # 7764
lst_years = []
eliminar_files = False
GetPolygonsfromFolder(asset, '', lstBacias= lstbacias, lstYear= lst_years, play_eliminar= eliminar_files)  # 

