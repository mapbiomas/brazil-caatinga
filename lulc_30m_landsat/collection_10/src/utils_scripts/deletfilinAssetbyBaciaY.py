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

def Get_Remove_Array_from_ImgCol(asset_imgcol, vers= None, janele= None, lsBacias= [], nyears= [],play_eliminar= False):
    
    imgCol = ee.ImageCollection(asset_imgcol)
    
    if vers:
        imgCol = imgCol.filter(ee.Filter.eq('version', vers))
    if janele:
        imgCol = imgCol.filter(ee.Filter.eq('janela', janele))    
    if lsBacias:
        imgCol = imgCol.filter(ee.Filter.inList('id_bacia', lsBacias))
    if nyears:
        imgCol = imgCol.filter(ee.Filter.inList('year', nyears))
    
    
    lst_id = imgCol.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
    print(f'we will eliminate {len(lst_id)} file image from {asset_imgcol} ')
    
    for cc, idss in enumerate(lst_id):    
        path_ = str(asset_imgcol + '/' + idss)    
        print (f"... eliminando ❌ ... item 📍{cc}/{len(lst_id)} : {idss}  ▶️ ")    
        try:
            if play_eliminar:
                ee.data.deleteAsset(path_)
                print(" > " , path_)
        except:
            print(f" {path_} -- > NAO EXISTE!")



def Get_Remove_Array_from_ImgCol_byDict(asset_imgcol, vers= None, janele= None, dictBaciasYears= {}, play_eliminar= False):
    
    imgCol = ee.ImageCollection(asset_imgcol)

    if vers:
        imgCol = imgCol.filter(ee.Filter.eq('version', vers))
    if janele:
        imgCol = imgCol.filter(ee.Filter.eq('janela', janele))   

    lstBacias = list(dictBaciasYears.keys())
    if len(lstBacias) > 0:
        lst_id = []
        for nbasin in lstBacias[:]:
            lstYY = dictBaciasYears[nbasin]
            imgColtmp = imgCol.filter(
                                    ee.Filter.And(
                                        ee.Filter.eq('id_bacia', nbasin),
                                        ee.Filter.inList('year', lstYY)
                                    ))
            lst_id_tmp = imgColtmp.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
            lst_id = lst_id + lst_id_tmp    
  
    else:
        lst_id = imgCol.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()
        print(f'we will eliminate {len(lst_id)} file image from {asset_imgcol} ')
    
    for cc, idss in enumerate(lst_id):    
        path_ = str(asset_imgcol + '/' + idss)    
        print (f"... eliminando ❌ ... item 📍{cc}/{len(lst_id)} : {idss}  ▶️ ")    
        try:
            if play_eliminar:
                ee.data.deleteAsset(path_)
                print(" > " , path_)
        except:
            print(f" {path_} -- > NAO EXISTE!")


# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_estaveis_v2'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_coinciden'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/maks_fire_w5'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVY'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/toExport' #
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/ilumination'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/grass_aflor'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Temporal'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/Gap-fill'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/POS-CLASS/clean_water'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Validation/aggrements'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassV1'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/ClassVP'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/mosaics-CAATINGA-4'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col7/CAATINGA/classAfloramento'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/aggrements'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col8/CAATINGA/estabilidade_colecoes'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/Classify_fromMMBV2YY'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YY'
# asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YY'
asset = 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/Classifier/ClassifyV2YX'
eliminar_byList = True

if eliminar_byList:
    lsBacias = [7622]
    lstBasin = [str(kk) for kk in lsBacias]
    print(lstBasin)
    lstyear = [2010]
    eliminar_files = False
    Get_Remove_Array_from_ImgCol(asset, lsBacias= lstBasin, nyears= lstyear, play_eliminar= eliminar_files)  
else:
    dictBaciaYY = {
        '7422': [1990, 2006, 2007, 2023], 
        '7424': [1989, 2024],
        '7438': [2010],
        '7443': [1986, 1987, 1995, 1997, 2001, 2021], #
        '745': [1986, 1988, 1994],
        '746': [1985, 1986, 1987, 1991, 1992, 1993, 1995, 1996,2002, 2003, 2011, 2015, 2019,2022],
        '751': [1994, 1995, 1996],
        '752': [2017, 2020, 2023],
        '753': [2017, 2019],        
        '7617': [1997],
        '7618': [1998, 2007],
        '7619': [1986, 1996, 2001, 2009, 2016, 2023],
        '7622': [1985, 1992, 1993, 1999, 2004, 2009, 2010, 2017, 2020],
        '7625': [2007],
        '765': [1991, 1993],
        '766': [2004, 2009],
        '7671': [1986],
        '772': [1986],
        '7721': [1991, 1999, 2016],
        '7741': [1993, 1999],
        '7746': [1997],
        '7754': [1996]
    }
    eliminar_files = False
    Get_Remove_Array_from_ImgCol_byDict(asset, dictBaciasYears= dictBaciaYY, play_eliminar= eliminar_files)