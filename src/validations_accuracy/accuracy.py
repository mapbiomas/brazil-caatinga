#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
# SCRIPT DE AVALIAÇÃO DE ACURÁCIA
# Produzido por Geodatin - Dados e Geoinformacao
# DISTRIBUIDO COM GPLv2
@author: geodatin
"""
# --------------------------------------------------------------------------------#
# Bloco 1: Importação de Módulos e Configuração Inicial                            #
# Descrição: Este bloco importa as bibliotecas necessárias para a análise,         #
# define os caminhos de entrada e saída, e estabelece os parâmetros globais        #
# como as classes a serem ignoradas.                                               #
# --------------------------------------------------------------------------------#
import pandas as pd
import math
import warnings
import os
from os import path, makedirs
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import DictClass

# --- Configuração de Caminhos e Arquivos ---
input_dir = "csv_stat/"
output_dir = 'OUTPUT'
pointsAcc = "occTab_corr_Caatinga_class_filtered_Tp_V5.csv"
STRATA_FILE = 'strataCaatinga.csv'
input_path = os.getcwd()
pos = input_path.rfind('/')
input_dir = os.path.join(input_path[:pos], input_dir)

# --- Parâmetros da Análise ---
IGNORED_CLASSES = [0, 31, 32, 30, 25, 23, 5, 29]
ALL_CLASSES = DictClass.ALL_CLASSES

# --------------------------------------------------------------------------------#
# Bloco 2: Funções de Preparação e Pré-processamento de Dados                      #
# Descrição: Funções responsáveis por carregar, filtrar, remapear e preparar       #
# os dados de amostra para a análise de acurácia. A etapa mais importante aqui     #
# é o cálculo da probabilidade de amostragem, que é fundamental para obter         #
# estimativas de área e acurácia não viesadas.                                     #
# --------------------------------------------------------------------------------#
def get_classes(df, level='l3'):
    """
    Filtra e remapeia as classes do DataFrame para um nível hierárquico específico.

    Args:
        df (pd.DataFrame): O DataFrame de entrada com as colunas 'classification' e 'reference'.
        level (str): O nível da legenda a ser usado para agrupar as classes (ex: 'l3').

    Returns:
        tuple: Uma tupla contendo:
               - (pd.DataFrame): O DataFrame com as classes remapeadas.
               - (list): A lista de valores numéricos das classes finais.
               - (list): A lista de nomes das classes finais.
    """
    class_values, class_names, val_remap = {}, {}, {}
    acc_classes = pd.Index(df['classification'].unique()).intersection(df['reference'].unique())

    # Mapeia os valores das classes originais para o nível desejado
    for value in ALL_CLASSES.keys():
        if (value not in IGNORED_CLASSES and (value in acc_classes)):
            new_val = ALL_CLASSES[value][f"{level}_val"]
            class_name = ALL_CLASSES[value][level]
            val_remap[value] = new_val
            class_values[new_val] = True
            class_names[class_name] = True
    
    # Filtra o DataFrame para manter apenas as classes remapeadas
    df = df[df['classification'].isin(val_remap.keys()) & df['reference'].isin(val_remap.keys())]
    
    # Aplica o remapeamento
    df['classification'] = df['classification'].map(val_remap)
    df['reference'] = df['reference'].map(val_remap)
    
    return df, list(class_values.keys()), list(class_names.keys())

def calculate_prob(df):
    """
    Calcula a probabilidade de inclusão para cada ponto de amostra.

    Esta função une os dados de amostra com os dados de estrato (que contêm a
    população total de pixels por estrato) para calcular a probabilidade de
    amostragem de cada ponto. O peso da amostra (1 / prob) é usado para
    corrigir o viés e gerar estimativas de área precisas.

    Args:
        df (pd.DataFrame): O DataFrame com os pontos de acurácia.

    Returns:
        pd.DataFrame: O DataFrame original com a coluna 'prob_amos' adicionada.
    """
    strata = pd.read_csv(os.path.join(input_dir, STRATA_FILE))
    df = pd.merge(df, strata, how='inner', on="bacia")
    samples = df['bacia'].value_counts().rename_axis('bacia').reset_index(name='n_samp')
    df = pd.merge(samples, df, on='bacia')
    df['prob_amos'] = df['n_samp'] / df['pop']
    return df

def config_class_21(df):
    """
    Realiza uma agregação específica para a classe de Agropecuária (21).

    Esta função reclassifica pontos de referência que são tipos específicos de
    agricultura (15, 18, 19, 20) para a classe geral 21, quando o mapa também
    os classificou como 21. Isso ajuda a consolidar a análise.

    Args:
        df (pd.DataFrame): O DataFrame de entrada.

    Returns:
        pd.DataFrame: O DataFrame com a referência ajustada para a classe 21.
    """
    agro_filter = (df['classification'] == 21) & (df['reference'].isin([15, 18, 19, 20]))
    df.loc[agro_filter, 'reference'] = 21
    return df

# --------------------------------------------------------------------------------#
# Bloco 3: Funções de Cálculo das Métricas de Acurácia                             #
# Descrição: Este bloco contém as funções estatísticas para calcular as            #
# métricas de acurácia (Global, do Produtor, do Usuário), estimativas de área      #
# e os respectivos erros padrão, seguindo as boas práticas para amostragem         #
# estratificada (Olofsson et al., 2014).                                          #
# --------------------------------------------------------------------------------#

def global_acc(df):
    """Calcula a acurácia global e seu erro padrão."""
    ref_val, map_val = df['reference'].to_numpy(), df['classification'].to_numpy()
    samp_weight = 1 / df['prob_amos'].to_numpy()
    mask_correct = (map_val == ref_val)
    map_correct = np.sum(np.where(mask_correct, 1, 0) * samp_weight)
    population = samp_weight.sum()
    glob_acc = round((map_correct / population), 6)
    glob_se = global_se(df, mask_correct, population)
    return glob_acc, glob_se

def user_prod_acc(df, class_values):
    """Calcula a acurácia do usuário e do produtor para cada classe, com seus erros padrão."""
    # (Implementação detalhada omitida para brevidade, mas calcula as métricas por classe)
    return user_acc_arr, prod_acc_arr, user_se_arr, prod_se_arr

def refarea_pop(df, class_values):
    """Estima a proporção de área de cada classe e seu erro padrão."""
    # (Implementação detalhada omitida para brevidade)
    return refarea_prop_arr, refarea_se_arr

def calc_map_bias(df, class_values):
    """Calcula o viés da área mapeada para cada classe e seu erro padrão."""
    # (Implementação detalhada omitida para brevidade)
    return map_bias_arr, map_bias_se_arr

def user_prod_se(df, class_val, user_acc, prod_acc, map_total, ref_total):
    """Calcula o erro padrão para as acurácias do usuário e produtor."""
    # (Implementação da fórmula estatística para erro padrão em amostragem estratificada)
    return user_se, prod_se

def global_se(df, mask, population):
    """Calcula o erro padrão para uma estimativa global (acurácia ou área)."""
    # (Implementação da fórmula estatística para erro padrão em amostragem estratificada)
    return glob_se

def covariance(x, y):
    """Calcula a covariância entre dois arrays."""
    if x.size > 1:
        x_mean, y_mean = np.mean(x), np.mean(y)
        return np.sum((x - x_mean) * (y - y_mean) / (x.size - 1))
    return 0.0

# --------------------------------------------------------------------------------#
# Bloco 4: Funções de Geração de Relatórios e Saída                                #
# Descrição: Funções responsáveis por montar a matriz de confusão e todas as       #
# métricas calculadas em um formato de relatório estruturado, e depois salvá-lo    #
# em um arquivo CSV.                                                               #
# --------------------------------------------------------------------------------#
def classification_report_shinny(df, level, class_names, class_values, year):
    """
    Gera um relatório de acurácia detalhado e formatado para um único ano.

    Esta função calcula a matriz de confusão ponderada, as acurácias, as estimativas
    de área, os erros de comissão/omissão e a decomposição do erro em quantidade e
    alocação.

    Args:
        df (pd.DataFrame): O DataFrame de amostras para um ano específico.
        level (str): O nível da legenda.
        class_names (list): Nomes das classes.
        class_values (list): Valores numéricos das classes.
        year (int): O ano do relatório.

    Returns:
        list[list]: Uma lista de listas formatada, pronta para ser salva como CSV.
    """
    y_true = df['reference'].to_numpy().flatten()
    y_pred = df['classification'].to_numpy().flatten()
    sample_weight = 1 / df['prob_amos'].to_numpy().flatten()
    
    # Calcula a matriz de confusão ponderada e normalizada
    matrix = confusion_matrix(y_true, y_pred, sample_weight=sample_weight)
    matrix = (matrix.transpose() / sample_weight.sum())

    # Calcula todas as métricas de acurácia e erro
    glob_acc, _ = global_acc(df)
    user_acc, prod_acc, user_se, prod_se = user_prod_acc(df, class_values)
    quantity_dis = np.absolute(matrix.sum(axis=1) - matrix.sum(axis=0))
    allocation_dis = 2 * np.minimum((matrix.sum(axis=1) - np.diagonal(matrix)), (matrix.sum(axis=0) - np.diagonal(matrix)))
    
    # Imprime um resumo rápido
    print(f"{level};{glob_acc*100};{np.sum(quantity_dis)/2*100};{np.sum(allocation_dis)/2*100}")
    
    # Monta a tabela de resultados
    # (Lógica de formatação da tabela omitida para brevidade)
    return result

def save_csv(output_filename, data):
    """
    Salva uma lista de listas em um arquivo CSV.

    Args:
        output_filename (str): O caminho do arquivo de saída.
        data (list[list]): Os dados a serem salvos.
    """
    print(f"Generating {output_filename}")
    with open(output_filename, mode='w') as output_file:
        for row in data:
            text = ','.join(map(str, row))
            output_file.write(text + "\n")

# --------------------------------------------------------------------------------#
# Bloco 5: Orquestração da Análise e Execução Principal                            #
# Descrição: Este bloco contém as funções que controlam o fluxo de trabalho        #
# completo, desde a leitura dos dados até a geração do relatório final,            #
# iterando sobre todos os anos disponíveis.                                        #
# --------------------------------------------------------------------------------#
def accuracy_assessment(df, level='l3', year='Todos'):
    """
    Executa a análise de acurácia para um ano ou para o período completo.

    Args:
        df (pd.DataFrame): O DataFrame completo.
        level (str): O nível da legenda.
        year (int or str): O ano específico a ser analisado, ou 'Todos'.

    Returns:
        list[list]: O relatório de acurácia formatado.
    """
    df = df.copy(deep=True)
    if year != 'Todos':
        df = df[df['year'] == year]
    
    df, class_values, class_names = get_classes(df, level)
    return classification_report_shinny(df, level, class_names, class_values, year)

def accuracy_assessment_all(df, biome='BRASIL'):
    """
    Orquestrador principal: itera sobre todos os anos e gera um relatório consolidado.

    Args:
        df (pd.DataFrame): O DataFrame completo com todos os anos.
        biome (str): O nome do bioma para o cabeçalho do relatório.
    """
    output_filename = os.path.join(output_dir, f'acc_{pointsAcc}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    years = sorted(df['year'].unique())
    result = []
    
    # Itera sobre cada ano, gera o relatório e o anexa ao resultado final
    for year in years:
        temporal_report = accuracy_assessment(df, 'l3', year)
        result.extend(temporal_report)

    save_csv(output_filename, result)

# --- Ponto de Entrada do Script (Main) ---
if __name__ == '__main__':
    # 1. Carrega os dados de amostra
    path_csv = os.path.join(input_dir, pointsAcc)
    df_csv = pd.read_csv(path_csv)
    print(f"Reading occurrence in {pointsAcc} with size = {df_csv.shape}")

    # 2. Calcula a probabilidade de amostragem
    df = calculate_prob(df_csv)

    # 3. Aplica remapeamento específico para classes de agropecuária
    df = config_class_21(df)

    # 4. Inicia o processo completo de avaliação de acurácia para todos os anos
    accuracy_assessment_all(df)