
import sys
import os 
import glob
import pandas as pd
import numpy as np
import holoviews as hv
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
# import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
# from plotly.validators.scatter.marker import SymbolValidator
# raw_symbols = SymbolValidator().values
# print("lista de markers ", raw_symbols)

classMapB = [3, 4, 5, 9,11,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,62]
classNew =  [3, 4, 3, 3,12,12,12,15,18,18,18,21,22,22,22,22,33,29,22,33,12,33,18,33,33,18,18,18,18,18,18,18,18,18,18, 4,12,21]
dict_ClassesNum = {}
for ccDe,  ccPara in zip(classMapB, classNew):
    dict_ClassesNum[str(ccDe)] = ccPara


def plot_Sankey_map_classCober(dfAreaTrans, lstClasses, lstColors, nameArea):
    # dfAreaTrans = dfAreaTrans.apply(OrdenaNumerico, axis= 1)
    print(dfAreaTrans.head(10))
    print(dfAreaTrans.tail(10))
    lstclassNum = [kk for kk, jj in enumerate(lstClasses)]
    print(lstclassNum)
    figSank = go.Figure(
                    data=[
                        go.Sankey(
                                
                                node = dict(
                                    pad = 15,
                                    thickness=20,
                                    line = dict(color = "black", width = 0.5),
                                    label =  lstclassNum,
                                    color =  'green'
                                ),
                            link = dict(
                                    source =  dfAreaTrans['source'],
                                    target =  dfAreaTrans['target'],
                                    value =  dfAreaTrans['value'],
                                    # label =  data['data'][0]['link']['label']
                            )
                    )])

    # figSank.update_layout(
    #         hovermode = 'x',
    #         title="Energy forecast for 2050<br>Source: Department of Energy & Climate Change, Tom Counsell via <a href='https://bost.ocks.org/mike/sankey/'>Mike Bostock</a>",
    #         font=dict(size = 10, color = 'white'),
    #         plot_bgcolor='black',
    #         paper_bgcolor='black'
    # )
    # figSank.write_image("graficosAreasPrior/{}.png".format("SankeyMap_Areas_" + nameArea))
    figSank.show()

def set_columncobertura(nrow):
    nclasse = nrow['classe']
    nrow['cobertura'] = dict_class[str(nclasse)]
    return nrow

def returnStringClass(valor):
    if valor < 10:
        return '0' + str(valor)
    return str(valor)

def convert_valorTransicao_Cobert(nrow):
    # dict_ClassesNum
    nclasse = str(nrow['classe'])
    print("== > ", nrow['classe'], " ", nclasse[:-2], " ",nclasse[-2:] )
    classDe = dict_ClassesNum[str(int(nclasse[:-2]))]
    classPara = dict_ClassesNum[str(int(nclasse[-2:]))]

    nrow['De'] = classDe
    nrow['Para'] = classPara

    nrow['remap'] = returnStringClass(classDe) + returnStringClass(classPara)
    return nrow

def OrdenaNumerico(mrow):
    dictnumer = {
        '3' : 0,
        '4': 1,
        '12': 2,
        '15': 3,
        '18': 4,
        '21': 5,
        '22': 6,
        '29': 7,
        '33': 8
    }

    mrow['DeN'] = dictnumer[str(mrow['De'])]
    mrow['ParaN'] = dictnumer[str(mrow['Para'])]

    return mrow

# 100 arvores
nameVetors = []

 # "#fff3bf",,"#45C2A5"
filesAreaCSV = glob.glob('areasPrioritCSVJoin/*.csv')
classes = [3,4,12,15,18,21,22,29,33]
columnsInt = [
    'Forest Formation', 'Savanna Formation', 'Grassland', 'Pasture',
    'Agriculture', 'Mosaic of Uses', 'Non vegetated area', 'Rocky Outcrop', 
    'Water'
]
colors = [ 
    "#006400", "#32CD32", "#B8AF4F", "#FFD966", "#E974ED", 
    "#FFFFB2", "#EA9999", "#FF8C00", "#0000FF"
]

dict_class = {
    '3': 'Forest Formation', 
    '4': 'Savanna Formation', 
    '12': 'Grassland', 
    '15': 'Pasture', 
    '18': 'Agriculture', 
    '21': 'Mosaic of Uses', 
    '22': 'Non vegetated area', 
    '29': 'Rocky Outcrop', 
    '33': 'Water'
}
years = ['1985_2022', '1985_1990']
dict_colors = {}
for ii, cclass in enumerate(classes):
    dict_colors[dict_class[str(cclass)]] = colors[ii]
lst_df_conse = []
lst_df_semi = []
groupConserva = False
groupSemiarido = False
hv.extension('bokeh')
# for kk, vv in dict_color.items():
#     print(kk, " ", vv)
# sys.exit()
for cc, nfile in enumerate(filesAreaCSV):

    
    if cc < 1:
        print(f"*** Loading {nfile} ****")
        # if 'prioridade-conservacao' in nfile:
        #     tmp_df_Area = pd.read_csv(nfile)
        #     tmp_df_Area = tmp_df_Area.drop(['system:index', '.geo'], axis='columns')
        #     # tmp_df_Area = tmp_df_Area.apply(set_columncobertura, axis= 1)
        #     print(tmp_df_Area.head(2))
        #     lst_df_conse.append(tmp_df_Area)
        #     if len(lst_df_conse) > 1:
        #         groupConserva = True

        # elif 'class_semiarido' in nfile:
        #     tmp_df_Area = pd.read_csv(nfile)
        #     tmp_df_Area = tmp_df_Area.drop(['system:index', '.geo'], axis='columns')
        #     # tmp_df_Area = tmp_df_Area.apply(set_columncobertura, axis= 1)
        #     print(tmp_df_Area.head(2))
        #     lst_df_semi.append(tmp_df_Area)
        #     if len(lst_df_semi) > 1:
        #         groupSemiarido = True

        df_Area = pd.read_csv(nfile)
        print(df_Area.shape)        
        df_Area = df_Area.drop(['system:index', '.geo'], axis='columns')
        df_Area = df_Area.apply(convert_valorTransicao_Cobert, axis= 1)
        print(df_Area.head())
        df_Area = df_Area.apply(OrdenaNumerico, axis= 1)
        print(df_Area.columns)
        print("show the table ", df_Area.head())
        print("years ", df_Area['year'].unique())
        print("size table ", df_Area.shape)
        
        # print(groupDF.shape)
        for yyear in years:
            df_AreaYY = df_Area[df_Area['year'] == yyear]

            lstInt = ['remap', 'DeN', 'ParaN']  # 'area', 
            lstAll = ['remap', 'DeN', 'ParaN', 'area']  # 
            groupDF = df_AreaYY[lstAll].groupby(lstInt).agg('sum').reset_index();
            groupDF.columns = ['remap', 'source', 'target', 'value']
            print(groupDF.head(2))
            print("new size table grouped ", groupDF.shape)

            name_export = nfile.replace("class_", "").replace(".csv", "").replace('areasPrioritCSV/', '')
            name_export = name_export + "_" + yyear

            ## Providing column names to use as Source, Destination and Flow Value.
            sankey1 = hv.Sankey(continent_wise_migration, kdims=["Measure", "Country"], vdims=["Value"])
            ## Modifying Default Chart Options
            sankey1.opts(cmap='Colorblind',
                        label_position='left',
                        edge_color='Country', edge_line_width=0,
                        node_alpha=1.0, node_width=40, node_sort=True,
                        width=800, height=600, bgcolor="snow",
                        title="Population Migration between New Zealand and Other Continents")

            plt.show()
            # plot_Sankey_map_classCober(groupDF, classes, colors, name_export)



# if groupConserva:
#     print()
#     ndfAcc = pd.concat(lst_df_conse, ignore_index= True)
#     print("columna ", ndfAcc.columns)
#     # print(ndfAcc.head(1))
#     print(" SMUDANDO ")
#     lstInt = ['classe', 'cobertura', 'year']  # 'area', 
#     lstAll = ['classe', 'cobertura', 'year', 'area']  # 
#     groupDF = ndfAcc[lstAll].groupby(lstInt).agg('sum').reset_index();
#     print(groupDF.head(2))
#     groupDF = groupDF.sort_values(by='year')
#     print(groupDF.shape)
#     buildingPlots_x_Class(groupDF, classes,  nfile.replace("class_", ""))
#     buildingPlots_Cruzando_Class(groupDF, [3,4,12,15,18,21],  nfile.replace("class_", ""))

#     plotPie_extremosSerie(df_Area, 1985, 'areasPrioritCSV/prioridade-conservacao' , dict_colors)
#     plotPie_extremosSerie(df_Area, 2022, 'areasPrioritCSV/prioridade-conservacao', dict_colors)


# if groupSemiarido:
#     print()
#     ndfAcc = pd.concat(lst_df_semi, ignore_index= True)
#     print("columna ", ndfAcc.columns)
#     print(ndfAcc.head(1))
#     print(" SMUDANDO ")
#     lstInt = ['classe', 'cobertura', 'year']  # 'area', 
#     lstAll = ['classe', 'cobertura', 'year', 'area']  # 
#     groupDF = ndfAcc[lstAll].groupby(lstInt).agg('sum').reset_index();
#     print(groupDF.head(2))
#     print(groupDF.shape)
#     groupDF = groupDF.sort_values(by='year')
#     buildingPlots_x_Class(groupDF, classes,  nfile.replace("class_", ""))
#     buildingPlots_Cruzando_Class(groupDF, [3,4,12,15,18,21],  nfile.replace("class_", ""))

#     plotPie_extremosSerie(df_Area, 1985, 'areasPrioritCSV/Semiarido' , dict_colors)
#     plotPie_extremosSerie(df_Area, 2022, 'areasPrioritCSV/Semiarido', dict_colors)