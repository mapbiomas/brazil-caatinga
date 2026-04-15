import pandas as pd 
import numpy as np 
import os 
import glob

dir_csv = '/home/gabriel//Downloads/cartas_1k-/'
dir_saida = '/home/gabriel/Dados/Mapbiomas/out_poucas_bandas/'
extension='csv'

bandas = ['median_gcvi','median_gcvi_wet','median_hallcover','median_swir1','median_swir1_dry','median_swir2_dry','median_swir2_wet','median_gvs_wet',
 'median_ndvi','median_ndvi_wet','median_savi','median_swir1_wet','min_swir1','median_savi_wet','median_fns_dry','median_gcvi_dry','median_ndfi','median_ndvi_dry','median_savi_dry','median_swir2',
 'median_gvs','median_nir_dry','median_evi2','median_ndwi_dry','median_nir','median_ndfi_wet','min_nir','min_swir2','median_ndfi_dry','median_evi2_dry', 'median_sefi_dry',
 'median_gvs_dry','median_ndwi','median_nir_wet','median_red','median_red_dry','median_wefi_wet','min_red','median_ndwi_wet','median_pri', 'class', 'latitude', 'longitude', 'ano', 'carta']

df_main = pd.DataFrame([])
os.chdir(dir_csv)
nome_arquivos = glob.glob('*.{}'.format(extension))

for nome in nome_arquivos:
    df = pd.read_csv(dir_csv+nome, index_col='system:index')
    
    #df = df.drop(columns=['.geo'])
    #df = df.drop(columns=[df.columns[108] , df.columns[109]])
    df = df[bandas]
    carta = nome.split('.')[0]
    print(carta)
    df['carta'] = carta
    
    #if df_main.empty:
        #df_main = df
    #else:
        #df_main = pd.concat([df_main, df])
    
    #print (df_main.head())
    df.to_csv(dir_saida+nome, header=True);
    
    