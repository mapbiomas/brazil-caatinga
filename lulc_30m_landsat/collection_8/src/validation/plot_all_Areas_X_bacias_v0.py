

import os 
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
# from plotly.validators.scatter.marker import SymbolValidator
# raw_symbols = SymbolValidator().values
# print("lista de markers ", raw_symbols)
dict_class = {
    '3': 'Forest Formation', 
    '4': 'Savanna Formation', 
    '12': 'Grassland', 
    '21': 'Mosaic of Uses', 
    '22': 'Non vegetated area', 
    '29': 'Rocky Outcrop', 
    '33': 'Water'
}
dictMarker = {   
    'Cv7.1': 'diamond-open',   
    'Cv2':   'diamond-open', 
    'Cv3':   'triangle-up-open', 
    'Cv4':   'star-open',
    'Cv5':   'diamond-open', 
    'Cv6':   'diamond-open',
    'Cv9':   'diamond-open', 
    'Cv10':  'diamond-open',
    'Gfv3':  'star-open',
    'Spv3':   'star-open',
    'Spv4':  'star-open',
    'Fqv2':   'star-open',
    'Tpv2':   'star-open',
    'Fqv3':   'star-open',
    'Tpvv1':   'star-open',
    'Tpvv2':   'star-open',
    'Tpv3':   'star-open',
    'Tpv4':   'star-open',
    'Spv2':   'star-open',
    'Spvv3':   'star-open',
    'Mov1': 'star-open',
    'Mist1':   'star-open',
    'Mist2':   'star-open',
    'ext':  'star-open',
    'int':  'star-open',
    'Cv6.0': 'star-open'
}
dictCol= {    
    'Cv7.1': '#4D0B4D', 
    'Cv2':   '#4D0B4D', 
    'Cv3':   '#D53604', 
    'Cv4':   '#D10074',
    'Cv5':   '#FF6347',
    'Cv6':   '#FF8C00',
    'Cv7':   '#D10074',
    'Cv9':   '#FF6347',
    'Cv10':  '#FF8C00',
    'Gfv3':  '#4D0B4D',
    'Spv3':  '#D10074',
    'Spv4':  '#7FFF00',
    'Fqv2':  '#FF6347',
    'Tpv2':  '#4B0082',
    'Fqv3':  '#FF6347',
    'Tpvv1':  '#4B0082',
    'Tpvv2':  '#D10074',
    'Tpv3':  '#4B0082',
    'Tpv4':  '#FF6347',
    'Spv2':  '#000000',
    'Spvv3':  '#00FFFF',
    'Mov1':  '#FF8C00',
    'Mist1': '#D53604', 
    'Mist2': '#FF8C00',
    'ext':  '#00FFFF',
    'int':  '#FF0000',
    'Cv6.0': '#9EBCDA'    
} 

def buildingPlots_x_Class(df_class, lstclass, lstVersion, mbacia):
    coluna = 3
    nRowplot = int(len(lstclass) / coluna) + 1
    fig = make_subplots(rows= nRowplot, cols= coluna)

    for cc, clase in enumerate(lstclass): 
        kcol = cc % coluna
        krow = int(cc / coluna)
        print(cc, krow, kcol)
        print(colors[cc], clase)

        for vers in lstVersion:
            mcolor = dictCol[vers]
            if vers == 'Cv7.1':
                mcolor = colors[cc]
            fig.add_trace(
                    go.Scatter(
                        x= df_class[(df_class['classe'] == clase) & (df_class['version'] == vers)]['year'], 
                        y= df_class[(df_class['classe'] == clase) & (df_class['version'] == vers)]['area'], 
                        marker_color= mcolor,
                        marker_symbol= dictMarker[vers],
                        name= dict_class[str(clase)] + "-" + vers
                    ),
                    row=krow + 1, col= kcol + 1
                )
        fig.update_xaxes(title_text=dict_class[str(clase)], row= krow + 1, col= kcol + 1)
    
    fig.update_layout(height=800, width=1600, title_text="bacia " + mbacia, showlegend=False)
    fig.update_layout(showlegend= True)
    # fig.show()
    fig.write_image(f"graficosV8/{mbacia}.png")
    # export as static image
    # pio.write_image(fig, "op.pdf")

# 100 arvores
nameBacias = [
    '741','7421','7422','744','745','746','7492','751','752','753',
    '754','755','756','757','758','759','7621','7622','763','764',
    '765','766','767','771','772','773', '7741','7742','775','776',
    '777','778','76111','76116','7612','7614','7615','7616','7617',
    '7618','7619', '7613'
]
classes = [ 3, 4,12,21,22,29,33] 
colors = ["#006400","#32CD32","#B8AF4F","#FFEFC3","#EA9999","#FF8C00","#0000FF"] # "#fff3bf",,"#45C2A5"
filesAreaCSV = glob.glob('AREA-EXPORT-V7/*.csv')
# bacia_sel = '741'

for bacia_sel in nameBacias[:]:
    lst_df = []
    print(bacia_sel)
    for nfile in filesAreaCSV:
        
        if '_' + bacia_sel + '_' in nfile :  #  and 'Col7.1' in nfile
            print(nfile)
            if 'Col7.1' in nfile:
                version = 'Cv7.1'
            elif 'Col6' in nfile:
                version = 'Cv6.0'
            else:
                version = nfile.split("_")[-1].replace('.csv', "")
            
            df_tmp = pd.read_csv(nfile)
            print(df_tmp.shape)
            df_tmp['classe'] = df_tmp['classe'].replace([15], 21)
            df_tmp['classe'] = df_tmp['classe'].replace([18], 21)
            df_tmp["version"] = [version] * df_tmp.shape[0]        
            # print(df_tmp.head(4))

            df_tmp = df_tmp.drop(['system:index', '.geo'], axis='columns')
            print(df_tmp.head(4))
            
            lst_df.append(df_tmp)

    concat_df  = pd.concat(lst_df, axis=0, ignore_index=True)
    # concat_df = df_tmp
    print("temos {} filas ".format(concat_df.shape))
    lst_vers = [kk for kk in concat_df.version.unique()]
    print("versoes = ", lst_vers)
    buildingPlots_x_Class(concat_df, classes, lst_vers, bacia_sel)


