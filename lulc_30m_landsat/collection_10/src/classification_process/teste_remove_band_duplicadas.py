lstBNDs = [
    'swir1_stdDev_1', 'nir_stdDev_1', 'green_stdDev_1', 'ratio_median_dry', 
    'gli_median_wet', 'dswi5_median_dry', 'ri_median', 'osavi_median', 
    'shape_median', 'mbi_median_dry', 'wetness_median_dry', 'green_median_texture_1',
    'iia_median_wet', 'brba_median_dry', 'lswi_median_wet', 'rvi_median', 
    'gcvi_median_dry', 'shape_median_dry', 'cvi_median_dry', 'mbi_median', 
    'ui_median_wet', 'avi_median', 'gemi_median', 'osavi_median_dry', 
    'blue_median_dry_1', 'swir2_median_dry_1', 'brba_median', 'ratio_median', 
    'gli_median_dry', 'blue_min_1', 'wetness_median', 'blue_median_wet_1', 
    'brightness_median_wet', 'swir1_min_1', 'blue_stdDev_1', 'lswi_median_dry', 
    'cvi_median', 'red_stdDev_1', 'shape_median_wet', 'red_median_dry_1', 
    'swir2_median_wet_1', 'dswi5_median_wet', 'red_median_wet_1', 'afvi_median', 
    'ndwi_median', 'avi_median_wet', 'gli_median', 'cvi_median_wet', 'swir2_min_1', 
    'iia_median', 'ndwi_median_dry', 'green_min_1', 'ri_median_dry', 'osavi_median_wet',
    'ui_median_dry', 'nir_median_wet_1', 'swir1_median_dry_1', 'red_median_1', 
    'nir_median_dry_1', 'bsi_median', 'gemi_median_wet', 'lswi_median', 
    'brightness_median_dry', 'awei_median_wet', 'afvi_median_wet', 'swir2_median_1', 
    'ndwi_median_wet', 'ratio_median_wet', 'gcvi_median', 'ui_median', 
    'rvi_median_wet', 'green_median_wet_1', 'ri_median_wet', 'nir_min_1', 
    'blue_median_1', 'green_median_1', 'avi_median_dry', 'wetness_median_wet', 
    'swir1_median_1', 'dswi5_median', 'swir2_stdDev_1', 'awei_median', 'red_min_1', 
    'mbi_median_wet', 'brba_median_wet', 'awei_median_dry', 'swir1_median_wet_1', 
    'gemi_median_dry', 'nir_median_1', 'green_median_dry_1', 'afvi_median_dry', 
    'gcvi_median_wet', 'iia_median_dry', 'brightness_median'
]


print(f"we have {len(lstBNDs)} bandas ")
def clean_lstBandas(tmplstBNDs):
    lstbndsRed = []
    for bnd in tmplstBNDs:
        bnd = bnd.replace('_1','')
        bnd = bnd.replace('_2','')
        bnd = bnd.replace('_3','')
        if bnd not in lstbndsRed:
            lstbndsRed.append(bnd)
    return lstbndsRed

nlstbndsRed = clean_lstBandas(lstBNDs)
print(f"we have {len(nlstbndsRed)} bandas REDUCED ")

