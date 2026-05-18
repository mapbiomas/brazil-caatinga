# !/usr/bin/env python
# --------------------------------------------------------------------------
# Bloco 1: Importação de Módulos
# Descrição: Este bloco importa todas as bibliotecas e módulos necessários
# para a execução do script. Inclui manipulação de arquivos (os, glob),
# processamento de dados (pandas, numpy), visualização (matplotlib) e,
# principalmente, ferramentas de Machine Learning do scikit-learn para
# seleção de features e modelagem.
# --------------------------------------------------------------------------
import glob
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import starmap
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import RFECV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from multiprocessing import Pool

# --------------------------------------------------------------------------
# Bloco 2: Definição de Constantes e Funções de Modelagem
# Descrição: Esta seção define variáveis globais, como a lista de colunas
# a serem usadas, e contém as funções principais para construir, avaliar e
# comparar diferentes modelos de Machine Learning.
# --------------------------------------------------------------------------

# Lista de todas as colunas (features) disponíveis nos dados de entrada.
colunas = [
    'afvi_median', 'afvi_median_dry', 'afvi_median_wet', 'avi_median', 'avi_median_dry',
    # ... (lista completa de colunas) ...
    'wetness_median', 'wetness_median_dry', 'wetness_median_wet'
]
# Flag para controlar se múltiplos modelos devem ser avaliados.
multiModels = False

def get_models():
    """Constrói um dicionário de modelos de Machine Learning para avaliação.

    Cada modelo é encapsulado em um `Pipeline` que primeiro aplica a
    Seleção Recursiva de Features (RFECV) e depois treina o classificador final.

    Returns:
        dict: Um dicionário onde as chaves são os nomes dos modelos (ex: 'rf')
              e os valores são os objetos de Pipeline do scikit-learn.
    """
    models = dict()
    # Modelo 'rf': RFECV com RandomForest para selecionar features, seguido por um DecisionTree.
    rfe = RFECV(estimator=RandomForestClassifier())
    model = DecisionTreeClassifier()
    models['rf'] = Pipeline(steps=[('s', rfe), ('m', model)])

    # Modelo 'gbm': RFECV com GradientBoosting para selecionar features, seguido por um RandomForest.
    rfe = RFECV(estimator=GradientBoostingClassifier())
    model = RandomForestClassifier()
    models['gbm'] = Pipeline(steps=[('s', rfe), ('m', model)])

    return models

def evaluate_model(nmodel, X, y):
    """Avalia um determinado modelo usando validação cruzada estratificada.

    Args:
        nmodel (sklearn.pipeline.Pipeline): O pipeline do modelo a ser avaliado.
        X (pd.DataFrame): O DataFrame contendo as features de treinamento.
        y (pd.Series): A Series contendo os rótulos (classes) de treinamento.

    Returns:
        np.ndarray: Um array com os scores de acurácia de cada fold da validação cruzada.
    """
    skf = StratifiedKFold(n_splits=5)
    scores = cross_val_score(nmodel, X, y, scoring='accuracy', cv=skf, n_jobs=2)
    return scores

def building_process_Model(X_train, y_train):
    """Orquestra a avaliação de múltiplos modelos e plota os resultados.

    Obtém a lista de modelos da função `get_models`, avalia cada um usando
    `evaluate_model` e, ao final, gera um boxplot para comparar a performance.

    Args:
        X_train (pd.DataFrame): As features de treinamento.
        y_train (pd.Series): Os rótulos de treinamento.
    """
    models = get_models()
    results = []
    names = []
    # Avalia cada modelo e armazena os resultados
    for name, model in models.items():
        scores = evaluate_model(model, X_train, y_train)
        results.append(scores)
        names.append(name)
        print('>%s %.3f (%.3f)' % (name, np.mean(scores), np.std(scores)))
    # Plota o boxplot comparativo
    plt.boxplot(results, labels=names, showmeans=True)
    plt.show()

# --------------------------------------------------------------------------
# Bloco 3: Funções de Carga e Processamento de Dados
# Descrição: Contém funções para carregar os dados das amostras (ROIs) a
# partir de arquivos CSV, concatená-los e prepará-los para o processo de
# seleção de features.
# --------------------------------------------------------------------------

def load_table_to_processing(cc, dir_fileCSV):
    """(Depreciada) Carrega e processa tabelas de ROIs para seleção de features.

    Nota: Esta função parece ter sido substituída por `load_table_to_process`.
    Ela carrega múltiplos arquivos CSV, concatena-os e aplica a seleção
    recursiva de features (RFECV) para identificar as variáveis mais importantes.

    Args:
        cc (int): Um contador ou identificador do processo.
        dir_fileCSV (list): Uma lista de tuplas contendo o caminho para os arquivos CSV.

    Returns:
        tuple: Uma tupla contendo a lista de bandas selecionadas e o limiar usado.
    """
    lstDF = []
    for dirCSV in dir_fileCSV:
        df_tmp = pd.read_csv(dirCSV[1])
        df_tmp = df_tmp.drop(['system:index', '.geo'], axis=1)
        lstDF.append(df_tmp)

    conDF = pd.concat(lstDF, axis=0, ignore_index=True)
    print("temos {} filas ".format(conDF.shape))

    colunas = [kk for kk in df_tmp.columns if kk not in ['year', 'class', 'newclass', 'random']]

    print(f"# {cc} loading train DF {df_tmp[colunas].shape} and ref {df_tmp['class'].shape}")

    # Lógica para seleção de features
    min_features_to_select = 2
    skf = StratifiedKFold(n_splits=3)
    model = RandomForestClassifier()
    rfecv = RFECV(
        estimator=model,
        step=1,
        cv=skf,
        scoring='accuracy',
        min_features_to_select=min_features_to_select,
        n_jobs=2
    )
    rfecv.fit(conDF[colunas], conDF['class'])
    print(f"Optimal number of features: {rfecv.n_features_}")

    # Filtra as features com base no ranking do RFECV
    lstBandSelect = []
    limear = 30
    if rfecv.n_features_ < 30:
        limear = 30 - int(rfecv.n_features_)
    for i, bndFeat in enumerate(colunas):
        if rfecv.ranking_[i] < limear if limear < 30 else rfecv.ranking_[i] < 4:
            lstBandSelect.append(bndFeat)

    return lstBandSelect, limear

def load_table_to_process(cc, dir_fileCSV):
    """Carrega, concatena e processa tabelas de ROIs para seleção de features.

    Esta é a função principal para a análise. Ela lê múltiplos arquivos CSV
    de uma bacia/ano, os une, e aplica o `RFECV` com um classificador
    `RandomForest` para encontrar o conjunto ótimo de features.

    Args:
        cc (int): Um contador ou identificador do processo.
        dir_fileCSV (list): Uma lista de tuplas, onde cada tupla contém o
                          caminho para um arquivo CSV de amostras.

    Returns:
        tuple: Uma tupla contendo:
               - (list): A lista de nomes das features selecionadas.
               - (int): O limiar de ranking utilizado para a seleção.
    """
    lstDF = []
    for dirCSV in dir_fileCSV:
        df_tmp = pd.read_csv(dirCSV[1])
        df_tmp = df_tmp.drop(['system:index', '.geo'], axis=1)
        lstDF.append(df_tmp)

    conDF = pd.concat(lstDF, axis=0, ignore_index=True)
    print("temos {} filas ".format(conDF.shape))

    colunas = [kk for kk in conDF.columns if kk not in ['year', 'class', 'newclass', 'random']]

    print(f"# {cc} loading train DF {conDF[colunas].shape} and ref {conDF['class'].shape}")

    # Configura e executa a Seleção Recursiva de Features
    min_features_to_select = 1
    skf = StratifiedKFold(n_splits=3)
    model = RandomForestClassifier()
    rfecv = RFECV(
        estimator=model,
        step=1,
        cv=skf,
        scoring='accuracy',
        min_features_to_select=min_features_to_select,
        n_jobs=2
    )
    rfecv.fit(conDF[colunas], conDF['class'])
    print(f"Optimal number of features: {rfecv.n_features_}")

    # Filtra as features com base no ranking gerado pelo RFECV
    lstBandSelect = []
    limear = 30
    if rfecv.n_features_ < 30:
        limear = 30 - int(rfecv.n_features_)

    for i, bndFeat in enumerate(colunas):
        # A condição seleciona as features com melhor ranking
        if rfecv.ranking_[i] < limear if limear < 30 else rfecv.ranking_[i] < 4:
            lstBandSelect.append(bndFeat)

    return lstBandSelect, limear

# --------------------------------------------------------------------------
# Bloco 4: Funções Utilitárias
# Descrição: Funções auxiliares para manipulação de caminhos de arquivos e
# filtragem de listas com base em critérios específicos como bacia e ano.
# --------------------------------------------------------------------------

def filterLSTbyBacia_Year(lstDir, mbasin, nYear, prefix):
    """Filtra uma lista de caminhos de arquivo por bacia e ano.

    Args:
        lstDir (list): A lista de caminhos de arquivo para filtrar.
        mbasin (str): O código da bacia a ser procurado no nome do arquivo.
        nYear (str): O ano a ser procurado no nome do arquivo.
        prefix (str): Um prefixo adicional a ser considerado na busca.

    Returns:
        list: Uma sublista contendo apenas os caminhos que correspondem aos critérios.
    """
    lst_tmp = []
    for ndir in lstDir:
        if prefix + mbasin in ndir[1] and str(nYear) in ndir[1]:
            lst_tmp.append(ndir)
    return lst_tmp

def filterLSTbyBacia_YearTupla(lstDir, mbasin, nYear):
    """(Depreciada) Filtra uma lista de caminhos e retorna tuplas.

    Similar à função anterior, mas formata a saída como uma lista de tuplas.
    """
    lst_tmp = []
    cc = 0
    for ndir in lstDir:
        if "/" + mbasin in ndir[1] and str(nYear) in ndir[1]:
            lst_tmp.append((cc, ndir[1]))
    return lst_tmp

def getPathCSV(lstfolders):
    """Constrói os caminhos absolutos para as pastas de dados CSV.

    Args:
        lstfolders (list): Uma lista com os nomes das subpastas dentro de '/dados/'.

    Returns:
        tuple: Uma tupla contendo:
               - (list): Uma lista de caminhos absolutos para cada pasta.
               - (str): O caminho absoluto para a pasta pai '/dados/'.
    """
    pathparent = str(Path(os.getcwd()).parents[0])
    lstpaths = []
    for npath in lstfolders:
        roisPathC = '/dados/' + npath
        mpathCC = pathparent + roisPathC
        lstpaths.append(mpathCC)
        print("add path of CSVs Rois is \n ==>", mpathCC)
    return lstpaths, pathparent + '/dados/'

# --------------------------------------------------------------------------
# Bloco 5: Execução Principal do Script (Main)
# Descrição: Este é o ponto de entrada do script. Ele define as listas de
# bacias e anos a serem processados, encontra todos os arquivos CSV de
# entrada e inicia o loop principal que itera sobre cada combinação de
# bacia/ano para realizar a seleção de features.
# --------------------------------------------------------------------------

# Listas de bacias e anos para iterar
lstBacias = [
    '7421', '741', '7422', '744', '745', '746', '7492', '751', '752', '753',
    '754', '755', '756', '757', '758', '759', '7621', '7622', '763', '764',
    '765', '766', '767', '771', '772', '773', '7741', '7742', '775', '776',
    '777', '778', '76111', '76116', '7612', '7614', '7615', '7616', '7617',
    '7618', '7619', '7613'
]
lstYears = [str(kk) for kk in range(1985, 2023)]

# Obtém os caminhos para os dados
lstFolders = ['ROIs_Joins_GrBa/']
pathCSVsCCs, npathParent = getPathCSV(lstFolders)

# Flags de controle
byYear = True
byBacia = True
multiprocess = False

if __name__ == '__main__':
    # Coleta todos os caminhos de arquivos CSV em uma única lista
    lst_pathCSV = []
    for mpath in pathCSVsCCs:
        lst_pathCSV.extend(glob.glob(mpath + "*.csv"))

    dirCSVs = [(cc, kk) for cc, kk in enumerate(lst_pathCSV)]
    print(f"lista de path {len(dirCSVs)}")

    # A opção de multiprocessamento está desativada, executa em modo sequencial.
    if multiprocess:
        pass # Lógica de multiprocessamento omitida.
    else:
        cc = 0
        # Loop principal que itera sobre cada bacia e cada ano.
        for nbacia in ['777']:  # Exemplo: processando apenas a bacia '777'
            for year in lstYears:
                # Filtra os arquivos CSV para a bacia e ano atuais.
                lstmDirs = filterLSTbyBacia_Year(dirCSVs, nbacia, year, "")
                print(f"#  {cc}  processing {nbacia} and {year} == {lstmDirs}")

                if cc > -1 and lstmDirs:
                    print(f"========== executando ============ \n => {lstmDirs}")
                    try:
                        # Carrega os dados e executa a seleção de features.
                        lst_bnd_rank, nlimear = load_table_to_process(cc, lstmDirs)
                        
                        # Salva as features selecionadas em um arquivo de texto.
                        nameFileSaved = lstmDirs[0][1].split("/")[-1][:-4] + '.txt'
                        print(" ✍️ saving ... ", nameFileSaved)
                        newdir = npathParent + "/results/" + nameFileSaved

                        with open(newdir, 'w+') as filesave:
                            for bndrank in lst_bnd_rank:
                                filesave.write(bndrank + '\n')
                            filesave.write("limear_" + str(nlimear))
                    except Exception as e:
                        print(f"=== Dado com Gap ou Erro em {nbacia}/{year} === ")
                        print(f"Detalhe: {e}")
                cc += 1