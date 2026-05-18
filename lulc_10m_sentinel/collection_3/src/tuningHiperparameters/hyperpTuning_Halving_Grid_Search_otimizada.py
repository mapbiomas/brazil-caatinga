#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hyper-tuning otimizado para i9 + 32 GB
Autor: Kimi (upgrade via GPT-4)
"""
import os, gc, glob, joblib, warnings, psutil
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.model_selection import HalvingGridSearchCV, train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------- CONFIGURAÇÕES ----------
PATH_ROIS = "/home/superusuario/Dados/mapbiomas/col8/features/ROIsCSV/ROIsV5Col8man/"
N_JOBS = -1                 # uso total da CPU
MAX_RAM_GB = 28             # limite para não travar o PC
CV_FOLDS = 3                # reduzir se ainda estiver lento
RANDOM_STATE = 42
SUB_SAMPLE_FRAC = 0.20      # 20 % só para tuning rápido (estratificado)
# ------------------------------------

def memory_usage():
    return psutil.virtual_memory().used / 1024**3  # GB

def load_sample(csv_file, frac=1.0):
    """Carrega só as colunas úteis e faz amostragem se pedido."""
    cols2drop = ['system:index', '.geo', 'class']
    df = pd.read_csv(csv_file, usecols=lambda c: c not in cols2drop)
    if frac < 1.0:
        df, _ = train_test_split(df, train_size=frac,
                                   stratify=df['class'],
                                   random_state=RANDOM_STATE)
    return df

def best_model_pipeline():
    """Pipeline + modelo rápido em C."""
    model = Pipeline([
        ('scaler', StandardScaler(with_mean=False)),  # esparsas ficam ok
        ('clf', HistGradientBoostingClassifier(
                    random_state=RANDOM_STATE,
                    max_iter=300,
                    early_stopping=True,
                    n_iter_no_change=10,
                    validation_fraction=0.1))
    ])
    return model

def param_grid():
    """Grid enxuto mas eficaz para HistGradientBoosting."""
    return {
        'clf__learning_rate': [0.01, 0.05, 0.1],
        'clf__max_depth': [None, 8, 16],
        'clf__max_leaf_nodes': [15, 31, 63]
    }

def halving_search(X, y):
    """Busca sucressiva com budget de amostras."""
    search = HalvingGridSearchCV(
        best_model_pipeline(),
        param_grid(),
        factor=2,               # dobra amostras a cada round
        resource='n_samples',
        max_resources=len(y),
        cv=CV_FOLDS,
        n_jobs=N_JOBS,
        random_state=RANDOM_STATE,
        verbose=2
    )
    search.fit(X, y)
    return search

def main():
    csvs = glob.glob(PATH_ROIS + "*.csv")
    if not csvs:
        print("Nenhum CSV encontrado!")
        return

    # 1) carrega e amostra
    print("Carregando CSV...")
    df = load_sample(csvs[0], frac=SUB_SAMPLE_FRAC)
    print("Shape após amostragem:", df.shape,
          "| RAM:", f"{memory_usage():.1f} GB")

    y = df.pop('class').values
    X = df.values
    del df; gc.collect()

    # 2) split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    # 3) busca
    print("\nIniciando HalvingGridSearchCV...")
    search = halving_search(X_train, y_train)

    # 4) avalia
    preds = search.best_estimator_.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"\nMelhor acurácia: {acc:.3f}")
    print("Melhores parâmetros:", search.best_params_)

    # 5) heatmap
    cv_results = pd.DataFrame(search.cv_results_)
    heat_df = (cv_results
               .rename(columns=lambda c: c.replace('param_clf__', ''))
               .pivot_table(values='mean_test_score',
                            index='learning_rate',
                            columns='max_leaf_nodes'))
    plt.figure(figsize=(4, 3))
    sns.heatmap(heat_df, annot=True, fmt=".3f", cmap="YlGnBu")
    plt.title("HistGradientBoosting – Grid reduzido")
    plt.tight_layout()
    plt.savefig("heatmap_otimizado.png", dpi=150)
    print("Heatmap salvo em heatmap_otimizado.png")

    # 6) salva modelo
    joblib.dump(search.best_estimator_, "best_model.gz")
    print("Modelo salvo em best_model.gz")

if __name__ == "__main__":
    main()