import sys
import glob
import pandas as pd
from sklearn import ensemble 
from sklearn.pipeline import Pipeline
import seaborn as sns
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# https://inria.github.io/scikit-learn-mooc/python_scripts/parameter_tuning_grid_search.html

pathROIsman = "/home/superusuario/Dados/mapbiomas/col8/features/ROIsCSV/ROIsV7Col8man/"
listCSVsRoi = glob.glob(pathROIsman + "*csv")

for featFile in listCSVsRoi:
    # featFirst = listCSVsRoi[0]
    nameTableCSV = featFile.replace(pathROIsman, '')
    print("processing features ", nameTableCSV)
    df_rois = pd.read_csv(featFile)
    lst_col = [kk for kk in df_rois.columns]
    lst_col.remove('system:index')
    lst_col.remove('.geo')
    lst_col.remove('class')
    # print("lista de coluna \n ==> ", lst_col)
    print("número de colunas ", len(lst_col))

    data_train, data_test, target_train, target_test = train_test_split(
                                                            df_rois[lst_col], df_rois["class"], 
                                                            test_size=0.2, random_state=42
                                                        )
    # n_estimators=n_estimators,
    # validation_fraction=0.2,
    # n_iter_no_change=5,
    # tol=0.01,
    # random_state=0,
    model = Pipeline([            
                ("classifier", ensemble.GradientBoostingClassifier(
                                    n_estimators= 150, 
                                    learning_rate= 0.01,
                                    subsample= 0.8,
                                    min_samples_leaf= 3,
                                    validation_fraction= 0.2,
                                    min_samples_split= 30,
                                    max_features= "sqrt"
                                ))
            ])
    print("Modelo Pipeline ", model)

    param_grid = {
        'classifier__learning_rate': (0.1, 0.125, 0.15, 0.175, 0.2),
        'classifier__n_estimators': (35,40, 50, 55, 60, 65, 70)
    }
    model_grid_search = GridSearchCV(
                                model, 
                                param_grid=param_grid,
                                n_jobs=2, 
                                cv=2
                            )
    model_grid_search.fit(data_train, target_train)

    accuracy = model_grid_search.score(data_test, target_test)
    print(
        f"The test accuracy score of the grid-searched pipeline is: {accuracy:.2f}")

    model_grid_search.predict(data_test)

    print(f"The best set of parameters is: "
        f"{model_grid_search.best_params_}")

    cv_results = pd.DataFrame(model_grid_search.cv_results_).sort_values(
        "mean_test_score", ascending=False)
    cv_results.head(6)

    # get the parameter names
    column_results = [f"param_{name}" for name in param_grid.keys()]
    column_results += [
        "mean_test_score", "std_test_score", "rank_test_score"]
    cv_results = cv_results[column_results]

    def shorten_param(param_name):
        if "__" in param_name:
            return param_name.rsplit("__", 1)[1]
        return param_name


    cv_results = cv_results.rename(shorten_param, axis=1)
    print("======== CV_resultado ========== \n", cv_results)

    pathSave = "hiperparameter/HPmtTuningV2_" + nameTableCSV
    cv_results.to_csv(pathSave, index=False)

    pivoted_cv_results = cv_results.pivot_table(
        values="mean_test_score", index=["learning_rate"],
        columns=["n_estimators"])

    print(pivoted_cv_results)

    ax = sns.heatmap(pivoted_cv_results, annot=True, cmap="YlGnBu", vmin=0.7,
                    vmax=0.9)
    ax.invert_yaxis()
    # plt.show()
    pathGraph = "imgGraficos/plotMat_HPt_" + nameTableCSV.replace('.csv', 'V2.png')
    plt.savefig(pathGraph)
    plt.clf()
    