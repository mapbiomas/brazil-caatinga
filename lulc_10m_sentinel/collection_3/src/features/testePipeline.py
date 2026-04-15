from sklearn.pipeline import Pipeline
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest
iris = load_iris()
pipe = Pipeline(steps=[
            ('select', SelectKBest(k=2)), 
            ('clf', LogisticRegression())
        ])
pipe.fit(iris.data, iris.target)
# Pipeline(steps=[
#         ('select', SelectKBest(...)), 
#         ('clf', LogisticRegression(...))
#     ])
print('lista de nomes ')
print(pipe[:-1].get_feature_names_out())
# array(['x2', 'x3'], ...)