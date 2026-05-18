
from osgeo import gdal
import os
 
# os.system() accepts command arguments as a string
os.system("ogr2ogr -f 'ESRI Shapefile' ./dest_shp/destination_data.shp example.geojson")


# Open the GeoJSON
src = gdal.OpenEx('example.geojson')
# Translate the vector data into Shapefile
dest = gdal.VectorTranslate('./test_shp/test.shp', src, format='ESRI Shapefile')