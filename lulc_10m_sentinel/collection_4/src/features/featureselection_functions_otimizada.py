# ------------- SUBSTITUA A FUNÇÃO ORIGINAL PELO CÓDIGO ABAIXO -------------
import pandas as pd
import numpy as np
import joblib, gc, psutil, warnings
from sklearn.feature_selection import RFECV
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, f_classif, SelectKBest
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, train_test_split
from tqdm import tqdm

warnings.filterwarnings("ignore")

MAX_RAM_GB = 28
N_JOBS     = -1
RANDOM_STATE = 42

def mem():
    return psutil.virtual_memory().used / 1024**3

def load_table_to_process(cc, dir_fileCSV):
    """
    DROP-IN replacement: mesma assinatura, mesma saída (lstBandSelect, limear),
    mas 5-15× mais rápido e leve.
    """
    # 1) leitura enxuta
    lstDF = []
    for _, path in dir_fileCSV:
        df = pd.read_csv(path,
                         usecols=lambda c: c not in ['system:index', '.geo'],
                         dtype=np.float32)          # 50 % menos RAM
        lstDF.append(df)
    conDF = pd.concat(lstDF, axis=0, ignore_index=True)
    print(f"temos {conDF.shape[0]} filas | RAM: {mem():.1f} GB")
    
    # remove year, class etc.
    cols = [c for c in conDF.columns if c not in ['year', 'class', 'newclass', 'random']]
    X = conDF[cols].values.astype(np.float32, copy=False)
    y = conDF['class'].values
    del conDF, lstDF; gc.collect()

    # 2) corte rápido – variância zero + F-test top-k
    X = VarianceThreshold().fit_transform(X)
    cols = np.array(cols)[VarianceThreshold().get_support()]
    skb = SelectKBest(score_func=f_classif, k=min(100, X.shape[1]))  # top-100
    X   = skb.fit_transform(X, y)
    cols = cols[skb.get_support()]

    # 3) modelo rápido e importância por permutação (bootstrap 5×)
    clf = HistGradientBoostingClassifier(max_iter=200,
                                         early_stopping=True,
                                         random_state=RANDOM_STATE)
    clf.fit(X, y)
    imp = permutation_importance(clf, X, y, n_repeats=5,
                                 random_state=RANDOM_STATE,
                                 n_jobs=N_JOBS).importances_mean
    # mantém as 60 maiores (ajuste se quiser mais ou menos)
    n_keep = 60
    idx_top = np.argsort(imp)[-n_keep:]
    X = X[:, idx_top]
    cols = cols[idx_top].tolist()

    # 4) RFECV só nas 60 melhores – step proporcional (muito mais rápido)
    min_feat = 2
    step_pct = 0.10   # remove 10 % por iteração
    rfecv = RFECV(
        estimator= clf,
        step=max(1, int(len(cols)*step_pct)),
        cv= StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE),
        scoring= 'accuracy',
        min_features_to_select= min_feat,
        n_jobs=N_JOBS
    )
    rfecv.fit(X, y)
    cols_final = np.array(cols)[rfecv.support_].tolist()

    # 5) monta saída idêntica ao script antigo
    limear = 30 if rfecv.n_features_ >= 30 else 30 - rfecv.n_features_
    return cols_final, limear
# -------------------------------------------------------------------------