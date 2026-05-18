#-*- coding utf-8 -*-
import ee
import sys
import numpy as np
from tqdm import tqdm

try:
  ee.Initialize()
  print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
  print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
sys.setrecursionlimit(1000000000)

params = {
    'year': 1994,
    'class': 'class',
    'categorical': 'bacia'
}

FeatColAl = ee.FeatureCollection("projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/PtosXBaciasBalanCluster/777")
features = list(FeatColAl.first().propertyNames().getInfo())
features.remove(params["class"])
features.remove('system:index')
features.remove(params['categorical'])

lsNome = FeatColAl.reduceColumns(ee.Reducer.toList(), ['system:index']).get('list').getInfo()

row = []
y = []
for namIndex in tqdm(lsNome):  
    FeatTemp = ee.Feature(FeatColAl.filter(ee.Filter.eq('system:index', namIndex)).first())
    if FeatTemp.get("year").getInfo() == params['year']:
        
        y.append(FeatTemp.get(params['class']))
        columns = FeatTemp.toArray(ee.List(features)).getInfo()
        columns.append(FeatTemp.get(params['categorical']))
        row.append(columns)
        

X = np.array(row)
print(X.shape)
np.save("./data/train_" + lsNome[0], X)
y = np.array(y).reshape(-1,1)
print(y.shape)
np.save("./data/test_" + lsNome[0], y)


