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
        idBacia = name.split('_')[0]
        nyear = int(name.split('_')[1])
        
        if len(lstBacias) > 0 and len(lstYear) > 0:            
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
        print(f"eliminando {cc}/{sizeFiles}:  {name}")
        print(path_)
        if play_eliminar:
            ee.data.deleteAsset(npath) 

        cc += 1
    
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
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsNormN2cluster'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsNormN2manual'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv6N2cluster'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/ROIs/coletaROIsv7N2manual'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGrades_info'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_IndAll'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesAgrWat'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesIndV2'}  # 
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesIndExt'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_Merges_info'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_Ind'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_IndAll'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_byGradesIndV3'}
# asset = {'id': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_merged_IndAllv3'}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN245red_allBND"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2clusterNN"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN5allBND"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsN2cluster"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/cROIsN2manualNN"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsN2man6bnd"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/coletaROIsN2manual"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisGradesgroupBuf"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisGradesgroupedBuf"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisJoinedBaGrNN"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisJoinsbyBaciaNN"}
# asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/ROIs/roisredDJoinsbyBaciaNN"}
asset = {'id': "projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/ROIs/ROIs_cleaned_downsamplesv4C"}
lstbacias = ['763']  # 7764
lst_years = [1991, 1999, 2005, 2014, 2021, 2022, 2023]
eliminar_files = False
GetPolygonsfromFolder(asset, '', lstBacias= lstbacias, lstYear= lst_years, play_eliminar= eliminar_files)  # 

