#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import sys
import os 
import glob
import pandas as pd
import numpy as np
import openpyxl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.express as px
# import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
# from plotly.validators.scatter.marker import SymbolValidator
# raw_symbols = SymbolValidator().values
# print("lista de markers ", raw_symbols)
# def getPathCSV ():
#     # get dir path of script 
#     mpath = os.getcwd()
#     # get dir folder before to path scripts 
#     pathparent = str(Path(mpath).parents[0])
#     return pathparent + '/dados/'

# pathBaseDados = getPathCSV()

def get_interval_to_plot(df_Cobert, lstColunas):
    pmtroDict = {}

    for cobert in lstColunas:
        # print("classe ", cobert)
        maxVal = df_Cobert[df_Cobert["classe"] == cobert]['area'].max()
        minVal = df_Cobert[df_Cobert["classe"] == cobert]['area'].min()
        if maxVal > minVal:
            amp = maxVal - minVal
            intervalo = int(amp / 5)
            ampDown = minVal * 0.3
            ampUp = maxVal * 0.20

            # print("cobertura=> ", cobert, " | Min ", minVal ,  ' | max ', maxVal, ' | Amp ', amp, " | interval ", intervalo)
            maxVal += ampUp
            if ampDown > 0:
                minVal -= ampDown
            else:
                minVal += ampDown
            amp = maxVal - minVal
            intervalo = int(amp / 5)
            # print(" ----> cobertura=> ", cobert, " | Min ", minVal ,  ' | max ', maxVal, ' | Amp ', amp, " | interval ", intervalo)
            dict_temp = {'range': [minVal, maxVal], 'dtick': intervalo,}
            pmtroDict[str(cobert)] = dict_temp
        else:
            dict_temp = {'range': [minVal, maxVal], 'dtick': 0,}
            pmtroDict[str(cobert)] = dict_temp

    return pmtroDict


def get_interval_geral_plot(df_Cobert, lstColunas):
    pmtroDict = {}
    
    maxVal = df_Cobert[df_Cobert["classe"].isin(lstColunas)]['area'].max()
    minVal = df_Cobert[df_Cobert["classe"].isin(lstColunas)]['area'].min()
    if maxVal > minVal:
        amp = maxVal - minVal
        intervalo = int(amp / 5)
        ampDown = minVal * 0.3
        ampUp = maxVal * 0.20

        # print("cobertura=> ", cobert, " | Min ", minVal ,  ' | max ', maxVal, ' | Amp ', amp, " | interval ", intervalo)
        maxVal += ampUp
        if ampDown > 0:
            minVal -= ampDown
        else:
            minVal += ampDown
        amp = maxVal - minVal
        intervalo = int(amp / 5)
        # print(" ----> cobertura=> ", cobert, " | Min ", minVal ,  ' | max ', maxVal, ' | Amp ', amp, " | interval ", intervalo)
        pmtroDict = {'range': [minVal, maxVal + intervalo], 'dtick': intervalo,}
        
    else:
        pmtroDict = {'range': [minVal, maxVal], 'dtick': 0,}
        

    return pmtroDict


def buildingPlots_x_Class(df_class, lstclass, nameArea):
    coluna = 3
    nameArea = nameArea.replace('areasPrioritCSV/', '')
    # print("lista de classes ", lstclass)
    dictPmtrosPlot = get_interval_to_plot(df_class, lstclass)
    # print("dictionario classe ")
    # for kk, val in dictPmtrosPlot.items():
    #     print(kk, " ", val)
    dictPmtros = {
            'height': 800,
            'width': 800,
            'template':'plotly_white'
        }
    # sys.exit()
    nRowplot = int(len(lstclass) / coluna) + 1
    figPlotC = make_subplots(rows= nRowplot, cols= coluna)

    for cc, nclase in enumerate(lstclass): 
        kcol = cc % coluna
        krow = int(cc / coluna)
        # print(cc, krow, kcol)
        # print(colors[cc], nclase)
          
        figPlotC.add_trace(
                go.Scatter(
                    x= df_class[df_class['classe'] == nclase]['year'], 
                    y= df_class[df_class['classe'] == nclase]['area'], 
                    marker_color= dict_colors[dict_class[str(nclase)]],
                    marker_symbol= 'star-open',
                    fill='tonexty',
                    name= dict_class[str(nclase)] 
                ),
                row=krow + 1, col= kcol + 1
            )
        figPlotC.update_xaxes(title_text=dict_class[str(nclase)], row= krow + 1, col= kcol + 1)
        if cc < 1:
            mkey = 'yaxis'
        else:
            mkey = 'yaxis' + str(cc + 1)
        dictPmtros[mkey] = dictPmtrosPlot[str(nclase)]

    figPlotC.update_layout(dictPmtros)
    figPlotC.update_layout(
            height=800, 
            width=1600, 
            title_text= nameArea, 
            showlegend= True,
            legend= dict(
                        orientation="h", 
                        x= 0.01,  
                        y= 0.11, 
                        font=dict(
                            family="Courier",
                            size=24,
                            color="black"
                        ),                    
                    ),
    )
    # figPlot.show()
    print(f" saving plot Class {nameArea}.png ")
    figPlotC.write_image(pathBaseDados + f"/graficosAreasPrior/{nameArea}.png")
    plt.clf()
    # export as static image
    # pio.write_image(fig, "op.pdf")


def buildingPlots_Cruzando_Class(df_class, lstclass, nameArea):

    nameArea = nameArea.replace('areasPrioritCSV/', '')
    # print("lista de classes ", lstclass)
    # dictPmtrosPlot = get_interval_geral_plot(df_class, lstclass)
    # print("dictionario classe ", dictPmtrosPlot)    
    dictPmtros = {
            'height': 600,
            'width': 800,
            'template':'plotly_white'
        }
    # sys.exit()
    
    figPlotCr = make_subplots(rows= 1, cols= 1)
    for cc, nclase in enumerate(lstclass):        
        # print(colors[cc], nclase)          
        figPlotCr.add_trace(
                go.Scatter(
                    x= df_class[df_class['classe'] == nclase]['year'], 
                    y= df_class[df_class['classe'] == nclase]['area'], 
                    marker_color= dict_colors[dict_class[str(nclase)]],
                    marker_symbol= 'star-open',
                    stackgroup='one',
                    name= dict_class[str(nclase)] 
                ),
                row= 1, col= 1
            )
        figPlotCr.update_xaxes(title_text= dict_class[str(nclase)], row= 1, col= 1)

        # dictPmtros['yaxis'] = dictPmtrosPlot

    # figPlotCr.update_layout(dictPmtros)
    figPlotCr.update_layout(
            height= 600, 
            width= 900, 
            title_text="cruzandoAreas_" , 
            showlegend=True,
            legend= dict(
                        orientation="h", 
                        x= 0.01,  
                        y= -0.15, 
                        font=dict(
                            family="Courier",
                            size=24,
                            color="black"
                        ),
                    ),
    )
    # figPlot.show()
    print(" ", "cruzandoAreas_" + nameArea)
    figPlotCr.write_image("graficosAreasPrior/{}.png".format("cruzandoAreas_" + nameArea))
    # export as static image
    # pio.write_image(fig, "op.pdf")
    plt.clf()


def plotPie_extremosSerie(dfArea, nyear, nameArea, dict_colors):
    nameArea = nameArea.replace('areasPrioritCSV/', '')

    fig_pie = px.pie(
                values = dfArea[dfArea['year'] == nyear]['area'],
                names = dfArea[dfArea['year'] == nyear]['cobertura'],
                color = dfArea[dfArea['year'] == nyear]['cobertura'],
                color_discrete_map = dict_colors,
                hole= 0.45,
                width=1200,
                height=650
               )
    fig_pie.update_traces(
                textfont_size=18,
                textinfo=' percent'  # value +
                )
    fig_pie.update_layout(
                    title={
                        'text': '<i><b>Distribuição {} Caatinga {} <br />'.format(nameArea, nyear),
    #                             'y':0.7,
                                'x':0.45,
                                'xanchor': 'center',
                                'yanchor': 'top',
                                'font': dict(color= "black",size=25, family='Verdana')
                        },
    #                 margin = dict(l=350, r=200, pad=100),
    #                 title_pad_t = 380,
                )

    # fig_1985.show()
    print("plot areas plot pie ", nameArea)
    fig_pie.write_image("graficosAreasPrior/{}_{}.png".format("Pie_Areas_" + nameArea, str(nyear)))
    plt.clf()

def plot2Pie_extremosSerie(dfArea, nyear, nameArea):
    nameArea = nameArea.replace('areasPrioritCSV/', '')

    nwidth= 1600
    nheight= 1450
    dfAreaFtr = dfArea[dfArea['year'] == nyear]
    dfAreaFtr.sort_values(by=['cob_level1'])

    # trace1 = go.Pie(
    #             values = dfAreaFtr['area'],
    #             labels = dfAreaFtr['cob_level1'],
    #             hole= 0.6,
    #             # sort= False,
    #             direction='clockwise',
    #             domain={'x':[0.5,0.5], 'y':[0.1,0.9]},
    #             textinfo= 'label + percent',
    #             textposition='inside',
    #             marker=dict(colors=dfAreaFtr["nat_color"],
    #                           line=dict(color='#FFFFFF', width=1)),
    #             showlegend= False
    #            )

    trace1 = go.Pie(
                values = dfAreaFtr['area'],
                labels = dfAreaFtr['cobertura'],
                hole= 0.6,
                # sort= False,
                direction='clockwise',
                textinfo= 'percent',
                textposition='outside',
                marker=dict(colors=dfAreaFtr["cob_color"],
                              line=dict(color='#FFFFFF', width=1)),

                showlegend= True
               )

    fig_2pie = go.FigureWidget(data=[trace1])          
    fig_2pie.update_traces(
                textfont_size=38,
                # textinfo=' percent'  # value +
                )
    fig_2pie.update_layout(
    #                 title={
    #                     'text': '<i><b>Distribuição {} Caatinga {} <br />'.format(nameArea, nyear),
    # #                             'y':0.7,
    #                             'x':0.45,
    #                             'xanchor': 'center',
    #                             'yanchor': 'top',
    #                             'font': dict(color= "black",size=25, family='Verdana')
    #                     },
    #                 margin = dict(l=350, r=200, pad=100),
    #                 title_pad_t = 380,
                    autosize=False,
                    width=nwidth ,
                    height=nheight,
                    legend= dict(
                        orientation="h", 
                        x= 0.01,  
                        y= -0.05, 
                        font=dict(
                            family="Courier",
                            size=32,
                            color="black"
                        ),
                        # yanchor="bottom"
                    ),
                    # legend_title_text='Cobertura\n'
                )

    # fig_1985.show()
    print("plot areas plot pie ", nameArea)
    namePlot = "graficosAreasPrior/{}_{}.png".format("Pie_Areas_" + nameArea, str(nyear))
    fig_2pie.write_image(namePlot, width= nwidth, height= nheight, scale=1)
    plt.clf()

def plotSunburstClasse(dfArea, nyear, nameArea, dict_colors_map):
    nameArea = nameArea.replace('areasPrioritCSV/', '')

    nwidth= 1400
    nheight= 1250
    dfAreaFtr = dfArea[dfArea['year'] == nyear]
    # dfAreaFtr.sort_values(by=['cob_level1'])
    figMap = px.sunburst(
                    dfAreaFtr,
                    path= ['total','cob_level1', 'cobertura'],
                    values='area',
                    color= 'cobertura',
                    branchvalues="total",
                    color_discrete_map= dict_colors_map,
                    width=500 ,
                    height=800,    
                )
    figMap.update_traces(
            textinfo="percent parent",
            # textposition='outside',
            insidetextorientation='horizontal',
            marker_colors=[dict_colors_map[cat] for cat in figMap.data[-1].labels],
            hoverlabel= dict(align= "auto",),
            insidetextfont= dict(size= 30),
    )    

    figMap.update_layout(          
            # autosize=False,
            font=dict(size=30),       
            margin = dict(t=0, l=0, r=0, b=0),
            uniformtext=dict(minsize=30, mode='show')
    )

    # fig_1985.show()
    print("plot areas plot pie ", nameArea)
    namePlot = "graficosAreasPrior/{}_{}.png".format("Sunburst_Areas_" + nameArea, str(nyear))
    figMap.write_image(namePlot, width= nwidth, height= nheight, scale=1)
    plt.clf()

def plot_Sankey_map_classCober(dfArea, nyearF, nyearS, nameArea, dict_colors):
    figSank = go.Figure(
                    data=[go.Sankey(
                            valueformat = ".0f",
                            valuesuffix = "TWh",
                            node = dict(
                            pad = 15,
                            thickness = 15,
                            line = dict(color = "black", width = 0.5),
                            label =  data['data'][0]['node']['label'],
                            color =  data['data'][0]['node']['color']
                            ),
                            link = dict(
                            source =  data['data'][0]['link']['source'],
                            target =  data['data'][0]['link']['target'],
                            value =  data['data'][0]['link']['value'],
                            label =  data['data'][0]['link']['label']
                        ))])

    figSank.update_layout(
            hovermode = 'x',
            title="Energy forecast for 2050<br>Source: Department of Energy & Climate Change, Tom Counsell via <a href='https://bost.ocks.org/mike/sankey/'>Mike Bostock</a>",
            font=dict(size = 10, color = 'white'),
            plot_bgcolor='black',
            paper_bgcolor='black'
    )

    mpath = os.getcwd()
    figSank.write_image(mpath + "/graficosAreasPrior/{}_{}_{}.png".format("SankeyMap_Areas_" + nameArea, str(nyear)))
    figSank.show()

def set_columncobertura(nrow):
    nclasse = nrow['classe']
    nrow['cobertura'] = dict_class[str(nclasse)]
    nrow['cob_level1'] = dict_classNat[str(nclasse)]
    nrow['cob_color'] = dict_colors[dict_class[str(nclasse)]]
    nrow['nat_color'] = dict_ColorNat[dict_classNat[str(nclasse)]]
    nrow['total'] = 'cobertura'
    return nrow

def calculoPerdas_ganho_byClass(dfAnalises, nameCSVexp):
    nameCSVexp = nameCSVexp.replace('areasPrioritCSV/', '')
    dfArea85 = dfAnalises[dfAnalises['year'] == 1985][['cobertura','classe', 'area']]
    dfArea22 = dfAnalises[dfAnalises['year'] == 2022][['cobertura','classe', 'area']]
    def calc_statisticsLoss(row):
        classe = row['classe']
        area85 = row['area']
        area22 = dfArea22[dfArea22['classe'] == classe]['area'].tolist()[0]
        percent = round(((area22 - area85)/area85) * 100, 2)
        row['area_85'] = area85
        row['area_22'] = area22
        row['diference'] = abs(area85 - area22)
        row['percent'] = percent

        return row

    dfArea85 = dfArea85.apply(calc_statisticsLoss, axis= 1)
    print("========= Areas diferencias  ☕ =========\n ", dfArea85.head(10))
    # get dir path of script 
    mpath = os.getcwd()
    newnameCSVexp = "perdaGanho_Areas_" + nameCSVexp
    namePlot = mpath + f"/graficosAreasPrior/{newnameCSVexp}.csv"
    print("plot in = ", namePlot)
    dfArea85.to_csv(namePlot)
    dfArea85.to_excel(namePlot.replace('.csv', '.xlsx'), sheet_name='Employee', index=False)


# 100 arvores
nameVetors = []

 # "#fff3bf",,"#45C2A5"
filesAreaCSV = glob.glob('areasPrioritCSV/*.csv')
print("==================================================================================")
print("========== LISTA DE CSVs  NO FOLDER areasPrioritCSV ==============================")
for cc, namFile in enumerate(filesAreaCSV):
    print(f" #{cc}  >>  {namFile}")

print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
print("==================================================================================")
print("")
classes = [3,4,12,15,18,21,22,29,33] # 
columnsInt = [
    'Forest Formation', 'Savanna Formation', 'Grassland', 'Pasture',
    'Agriculture', 'Mosaic of Uses', 'Non vegetated area', 'Rocky Outcrop', 'Water'
] # 
colors = [ 
    "#1f8d49", "#7dc975", "#d6bc74", "#edde8e", "#f5b3c8", 
    "#ffefc3", "#db4d4f",  "#FF8C00", "#0000FF"
] # 
# bacia_sel = '741'

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

dict_classNat = {
    '3': 'Natural', 
    '4': 'Natural', 
    '12': 'Natural', 
    '15': 'Antrópico', 
    '18': 'Antrópico', 
    '21': 'Antrópico', 
    '22': 'Antrópico', 
    '29': 'Natural', 
    '33': 'Natural'
}
dict_ColorNat = {
    'Natural': '#32a65e',
    'Antrópico': '#FFFFB2',
}
dict_colors = {}
for ii, cclass in enumerate(classes):
    dict_colors[dict_class[str(cclass)]] = colors[ii]
dict_colors['Natural'] = '#32a65e'
dict_colors['Antrópico'] = '#FFFFB2'
dict_colors['cobertura'] = '#FFFFFF'

for kk, vals in dict_colors.items():
    print(f" {kk} >> {vals}")

lstclass_part1 = [3,4,12]
lstclass_part2 = [15,21,18,22,33]
savePlot = False
lst_df_SF = []
lst_df_macro = []
lst_df_biosf = []
groupSaoFrancisco = False
groupmacroRH = False
groupBiosfer = False

# for kk, vv in dict_color.items():
#     print(kk, " ", vv)
# sys.exit()
for cc, nfile in enumerate(filesAreaCSV):

    print(f"*** Loading... {nfile} ****")
    if cc > -1:
        if 'sao_francisco' in nfile:
            tmp_df_Area = pd.read_csv(nfile)
            tmp_df_Area = tmp_df_Area[(tmp_df_Area['classe'] != 0) & (tmp_df_Area['classe'] != 29)]
            tmp_df_Area = tmp_df_Area.drop(['system:index', '.geo'], axis='columns')
            tmp_df_Area = tmp_df_Area.apply(set_columncobertura, axis= 1)
            print(tmp_df_Area.head(2))
            lst_df_SF.append(tmp_df_Area)
            if len(lst_df_SF) > 1:
                groupSaoFrancisco = True

        elif 'macro_RH' in nfile:
            tmp_df_Area = pd.read_csv(nfile)
            tmp_df_Area = tmp_df_Area[(tmp_df_Area['classe'] != 0) & (tmp_df_Area['classe'] != 29)]
            tmp_df_Area = tmp_df_Area.drop(['system:index', '.geo'], axis='columns')
            tmp_df_Area = tmp_df_Area.apply(set_columncobertura, axis= 1)
            print(tmp_df_Area.head(2))
            lst_df_macro.append(tmp_df_Area)
            if len(lst_df_macro) > 1:
                groupmacroRH = True

        elif 'res_biosf' in nfile:
            tmp_df_Area = pd.read_csv(nfile)
            tmp_df_Area = tmp_df_Area[(tmp_df_Area['classe'] != 0) & (tmp_df_Area['classe'] != 29)]
            tmp_df_Area = tmp_df_Area.drop(['system:index', '.geo'], axis='columns')
            tmp_df_Area = tmp_df_Area.apply(set_columncobertura, axis= 1)
            print(tmp_df_Area.head(2))
            lst_df_biosf.append(tmp_df_Area)
            if len(lst_df_biosf) > 1:
                groupBiosfer = True

        else:
            # pass
            print("===== dataframe não será agrupado to process ====")
            df_Area = pd.read_csv(nfile)
            df_Area = df_Area[(df_Area['classe'] != 0) & (df_Area['classe'] != 29)]
            print("tamanho da tabela => ", df_Area.shape)
            # print(df_Area.columns)
            df_Area = df_Area.drop(['system:index', '.geo'], axis='columns')
            df_Area = df_Area.apply(set_columncobertura, axis= 1)
            print(df_Area.head(2))
            print(df_Area['classe'].unique())
            # print(df_tmp['year'].value_counts())
            df_Area = df_Area.sort_values(by='year')
            
            nameFileExp = nfile.replace("class_", "").replace(".csv", "")
            calculoPerdas_ganho_byClass(df_Area, nameFileExp)

            if savePlot:
                buildingPlots_x_Class(df_Area, classes,  nameFileExp)          

                plotSunburstClasse(df_Area, 1985, nameFileExp, dict_colors)
                plot2Pie_extremosSerie(df_Area, 1985, nameFileExp)
                plot2Pie_extremosSerie(df_Area, 2022, nameFileExp)

                buildingPlots_Cruzando_Class(df_Area, lstclass_part1,  nameFileExp +  "_p1_")
                buildingPlots_Cruzando_Class(df_Area, lstclass_part2,  nameFileExp + "_p2_")

    # sys.exit() 


lstInt = ['classe', 'cobertura', 'year', 'total','cob_level1','cob_color']  # 'area', 
lstAll = ['classe', 'cobertura', 'year', 'total','cob_level1', 'cob_color', 'area']  # 

if groupSaoFrancisco:
    print()
    ndfAcc = pd.concat(lst_df_SF, ignore_index= True)
    print("columna ", ndfAcc.columns)
    # print(ndfAcc.head(1))
    print("== AGRUPANDO PELA SUMA == ")
    groupDF = ndfAcc[lstAll].groupby(lstInt).agg('sum').reset_index();
    print(groupDF.head(2))
    groupDF = groupDF.sort_values(by='year')
    print(groupDF.shape)
    calculoPerdas_ganho_byClass(df_Area, "areasPrioritCSV/sao-francisco")
    if savePlot:
        buildingPlots_x_Class(groupDF, classes,  "areasPrioritCSV/sao-francisco")    
        plotSunburstClasse(groupDF, 1985, "areasPrioritCSV/sao-francisco", dict_colors)
        plot2Pie_extremosSerie(groupDF, 1985, 'areasPrioritCSV/sao-francisco')
        plot2Pie_extremosSerie(groupDF, 2022, 'areasPrioritCSV/sao-francisco')

        buildingPlots_Cruzando_Class(groupDF, lstclass_part1,  "areasPrioritCSV/sao-francisco_p1_")
        buildingPlots_Cruzando_Class(groupDF, lstclass_part2,  "areasPrioritCSV/sao-francisco_p2_")


if groupmacroRH:
    print()
    ndfAcc = pd.concat(lst_df_macro, ignore_index= True)
    print("columna ", ndfAcc.columns)
    # print(ndfAcc.head(1))
    print("== AGRUPANDO PELA SUMA == ")    
    groupDF = ndfAcc[lstAll].groupby(lstInt).agg('sum').reset_index();
    print(groupDF.head(2))
    groupDF = groupDF.sort_values(by='year')
    print(groupDF.shape)
    calculoPerdas_ganho_byClass(df_Area, "areasPrioritCSV/macro_RH_SF")
    if savePlot:
        buildingPlots_x_Class(groupDF, classes,  'areasPrioritCSV/macro_RH_SF')    
        plotSunburstClasse(groupDF, 1985, 'areasPrioritCSV/macro_RH_SF', dict_colors)
        plot2Pie_extremosSerie(groupDF, 1985, 'areasPrioritCSV/macro_RH_SF')
        plot2Pie_extremosSerie(groupDF, 2022, 'areasPrioritCSV/macro_RH_SF')

        buildingPlots_Cruzando_Class(groupDF, lstclass_part1,  'areasPrioritCSV/macro_RH_SF_p1_')
        buildingPlots_Cruzando_Class(groupDF, lstclass_part2,  'areasPrioritCSV/macro_RH_SF_p2_')

if groupBiosfer:
    print()
    ndfAcc = pd.concat(lst_df_biosf, ignore_index= True)
    print("columna ", ndfAcc.columns)
    print(ndfAcc.head(1))
    print("== AGRUPANDO PELA SUMA == ")
    groupDF = ndfAcc[lstAll].groupby(lstInt).agg('sum').reset_index();
    print(groupDF.head(2))
    print(groupDF.shape)
    groupDF = groupDF.sort_values(by='year')
    calculoPerdas_ganho_byClass(df_Area, "areasPrioritCSV/reserva_biosfera")
    
    if savePlot:
        buildingPlots_x_Class(groupDF, classes,  'areasPrioritCSV/reserva_biosfera')    
        plotSunburstClasse(groupDF, 1985, 'areasPrioritCSV/reserva_biosfera', dict_colors)
        plot2Pie_extremosSerie(groupDF, 1985, 'areasPrioritCSV/reserva_biosfera')
        plot2Pie_extremosSerie(groupDF, 2022, 'areasPrioritCSV/reserva_biosfera')

        buildingPlots_Cruzando_Class(groupDF, lstclass_part1,  'areasPrioritCSV/reserva_biosfera_P1_')
        buildingPlots_Cruzando_Class(groupDF, lstclass_part2,  'areasPrioritCSV/reserva_biosfera_P2_')
    