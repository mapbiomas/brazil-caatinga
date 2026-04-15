''''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee
import os 
import sys
from pathlib import Path
import collections
collections.Callable = collections.abc.Callable

pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
print("parents ", pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
from gee_tools import *
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


def processoExportar(mapaRF,  nomeDesc, geom_bacia, asset_output):

    idasset =  os.path.join(asset_output, nomeDesc)
    optExp = {
        'image': mapaRF, 
        'description': nomeDesc, 
        'assetId': idasset, 
        'region': geom_bacia,  # .getInfo()['coordinates']
        'scale': 10, 
        'maxPixels': 1e13,
        "pyramidingPolicy":{".default": "mode"}
    }
    task = ee.batch.Export.image.toAsset(**optExp)
    task.start() 
    print("salvando ... " + nomeDesc + "..!")
    # print(task.status())
    for keys, vals in dict(task.status()).items():
        print ( "  {} : {}".format(keys, vals))

assetPath_mosaic = 'projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3'
asset_input = 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/GENERAL/CAATINGA/POS-CLASS/Spatials_all'
asset_output = 'projects/mapbiomas-arida/energias'
asset_outputMB = 'projects/mapbiomas-brazil/assets/LAND-COVER-10M/COLLECTION-3/SOLAR-PANELS/classification'
asset_fv = 'projects/mapbiomas-arida/energias/solar-panel-br'
# asset_fv_30 = 'projects/mapbiomas-arida/energias/raster-solar-panel-br-30m'
year_inic = 2016
year_end = 2024
version = 1

imgFV = ee.Image(asset_fv)
mosaic = (ee.ImageCollection(assetPath_mosaic)
                .filter(ee.Filter.eq('year', 2024))
                .mosaic()
                .select('blue_median')
                .gt(100000000)
)

listCoord = [
      [-74.10257255534734,-33.991737087461075], 
      [-34.55179130534736,-33.991737087461075],
      [-34.55179130534736,5.470447918275946],
      [-74.10257255534734,5.470447918275946],
      [-74.10257255534734,-33.991737087461075]
]
limite_Br = ee.Geometry.Polygon(listCoord)

print('show metadados FV ', imgFV.bandNames().getInfo())
lst_bands = []
camada_fotoVoltaica = ee.Image().byte()
for cc, yyear in enumerate(range(year_inic, year_end + 1)):
    print(f'# {cc} processing <>> year {yyear}')
    imgClass = imgFV.select(f"Panel_{yyear}").unmask(0)
    raster_FV_year = mosaic.where(imgClass.eq(1), 75)

    raster_FV_year = (raster_FV_year
                            .selfMask()
                            .rename('classification')
                            .set(
                                'collection_id', 3,
                                'version', version, 
                                'theme', 'FOTOVOLTAICA',
                                'source', 'geodatin',
                                'territory', 'BRAZIL',
                                'system:footprint', limite_Br
                        ))
    name_export = f"SOLAR-PANELS-{yyear}-{version}"
    
    processoExportar(raster_FV_year, name_export, limite_Br, asset_outputMB)
    band_act = f'classification_{yyear}'
    camada_fotoVoltaica = camada_fotoVoltaica.addBands(raster_FV_year.rename(band_act))
    lst_bands.append(band_act)

name_export = 'raster-solar-panel-br-10m'
camada_fotoVoltaica = (camada_fotoVoltaica
                            .select(lst_bands)
                            .set(
                                'collection_id', 3,
                                'version', version, 
                                'theme', 'FOTOVOLTAICA',
                                'source', 'geodatin',
                                'territory', 'BRAZIL',
                                'system:footprint', limite_Br
                            ))
processoExportar(camada_fotoVoltaica, name_export, limite_Br, asset_outputMB)