
import os
from math import floor
import streamlit as st
import numpy as np
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards
import plotly.graph_objects as go
# import altair as alt
import ipywidgets
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go





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
dict_cobertura = {
    'Forest Formation': 3, 
    'Savanna Formation': 4, 
    'Grassland': 12, 
    'Pasture': 15, 
    'Agriculture': 18, 
    'Mosaic of Uses': 21, 
    'Non vegetated area': 22, 
    'Rocky Outcrop': 29, 
    'Water': 33
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
dict_colors = {
    '3':  '#1f8d49', 
    '4':  '#7dc975', 
    '12': '#d6bc74', 
    '15': '#edde8e', 
    '18': '#f5b3c8', 
    '21': '#ffefc3', 
    '22': '#db4d4f', 
    '29': '#FF8C00', 
    '33': '#0000FF',
    'Forest Formation':  '#1f8d49', 
    'Savanna Formation':  '#7dc975', 
    'Grassland': '#d6bc74', 
    'Pasture': '#edde8e', 
    'Agriculture': '#f5b3c8', 
    'Mosaic of Uses': '#ffefc3', 
    'Non vegetated area': '#db4d4f', 
    'Rocky Outcrop': '#FF8C00', 
    'Water': '#0000FF',
}
dict_code_colors = {}
for ii, cclass in enumerate(classes):
    dict_code_colors[str(cclass)] = colors[ii]

dict_colors['Natural'] = '#32a65e'
dict_colors['Antrópico'] = '#FFFFB2'
dict_colors['cobertura'] = '#FFFFFF'
dictModel = {
    'Gradient Tree Boosting': 'GTB',
    'Gap-fill': 'Gap-fill', 
    'Spatial': 'Spatial', 
    'SpatialV2': 'SpatialV2',
    'Temporal': 'Temporal', 
    'toExport': 'toExport',
    'Frequency': 'Frequency',
    'Gap-fillV2': 'Gap-fillV2',
    'SpatialV2St1': 'SpatialV2St1', 
    'FrequencyV2nat': 'FrequencyV2nat', 
    'FrequencyV2natUso': 'FrequencyV2natUso',
    'SpatialV2St3': 'SpatialV2St3',
    'TemporalV2J3': 'TemporalV2J3',
    'SpatialV3St1': 'SpatialV3St1',
    'TemporalV3J3': 'TemporalV3J3',
    'TemporalV3J4': 'TemporalV3J4',
    'TemporalV3J5': 'TemporalV3J5',
    'FrequencyV3St2': 'FrequencyV3St2',
    'FrequencyV3St1': 'FrequencyV3St1',
    'SpatialV3su': 'SpatialV3su'
}

vers = ['1',]
nameBacias = [
    '7754', '7691', '7581', '7625', '7584', '751', '7614', 
    '752', '7616', '745', '7424', '773', '7612', '7613', 
    '7618', '7561', '755', '7617', '7564', '761111', '761112', 
    '7741', '7422', '76116', '7761', '7671', '7615', '7411', 
    '7764', '757', '771', '7712', '766', '7746', '753', '764', 
    '7541', '7721', '772', '7619', '7443', '765', '7544', '7438', 
    '763', '7591', '7592', '7622', '746'
] 


def load_data_Acc(nameBac, xvers, modelo_act):
    base_path = os.getcwd()
    base_path = os.path.join(base_path, 'dbase')
    nameTablesGlob = f"regMetricsAccs_{modelo_act}_vers_{xvers}_Col9.csv"        
    dfAccYY = pd.read_csv(os.path.join(base_path, nameTablesGlob), index_col=False, low_memory=False)
    # print("=================================")
    # print("", dfAccYY.head())
    colInts = [kk for kk in dfAccYY.columns]
    # print("colunas listadas \n   ==> ",colInts)
    colInts.remove('Unnamed: 0')
    dfAccYY = dfAccYY[colInts]
    # lstIndex = ['Accuracy', 'Accuracy_Bal', 'Precision', 'ReCall', 'F1-Score', 'Jaccard']
    # for colInd in lstIndex:
    #     dfAccYY[colInd] = dfAccYY[colInd].apply(lambda x: round(x * 100, 0))

    dfAccYY['Version'] = dfAccYY['Version'].astype(str)
    dfAccYY['Bacia'] = dfAccYY['Bacia'].astype(str)

    # print(dfAccYY.head())
    return dfAccYY





# create year filter drop down
lstSelBa = ['bacia_' + str(kk) for kk in nameBacias]
modeloAct = 'GTB'
posclass = ['GTB']
accCol8 = 75.4
discAloc = 17.0 
discQual = 7.6
st.set_page_config(page_title="Dashboard Maps Validation", page_icon="📈", layout="wide", initial_sidebar_state='collapsed')
dash_1 = st.container()
dash_2 = st.container()
dash_3 = st.container()
dash_4 = st.container()
dash_5 = st.container()

with dash_1:
    st.markdown("<h2 style='text-align: center;'>Dashboard Maps Validation </h2>", unsafe_allow_html=True)
    st.write("")

# components
sidebarApp = st.sidebar
with sidebarApp:
    sidebarApp.header(" Painel de Validação Coleção S2 📈")

optionAnalises = st.sidebar.selectbox(
                    "seleciona o tipo de Analises",
                    ('Accuracy', 'Area by class') # , 'Aggrement'
                )
optionModel = st.sidebar.selectbox(
                    "seleciona modelo ou Filtro pos-classificação",
                    posclass
                )
selected_Basin = st.sidebar.selectbox(
                    "Selecionar Bacia ou Bioma", 
                    ['Caatinga 🌵'] + lstSelBa 
                )
selected_Versions = st.sidebar.selectbox("Selecionar Versão", vers)


if optionAnalises == 'Accuracy':          
    
    modeloAct = dictModel[optionModel]
    baciaAct = selected_Basin.replace('bacia_', '').replace(" 🌵", "")
    versionAct = selected_Versions

    dataAcc = load_data_Acc(baciaAct, versionAct, modeloAct)
    dataAggAc = load_data_Aggrement(baciaAct, versionAct, modeloAct)

    # print(f"tenemos uma analises aqui de  Accuracy para os dados {modeloAct}| {baciaAct} | {versionAct}")
    # st.write(f"tenemos uma analises aqui de  Accuracy para os dados {modeloAct}| {baciaAct} | {versionAct}")
    