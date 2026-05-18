"""
    Ajuste automático a través de GridSearchCV en Scikit-learn
    Lleva mucho tiempo y no se usa comúnmente en muchos casos
    https://programmerclick.com/article/2965240309/
"""
from keras.models import Sequential
from keras.layers import Dense
import numpy as np
from sklearn.model_selection import GridSearchCV
from keras.wrappers.scikit_learn import KerasClassifier
 
 # Construyendo el modelo
 # ¡Los parámetros aquí deben tener init! !! !! De lo contrario, se informará un error.
def create_model(optimizer='rmsprop', init='glorot_uniform'):
         # Construyendo el modelo
    model = Sequential()
    model.add(Dense(12, input_dim=8, kernel_initializer=init, activation='relu'))
    model.add(Dense(8, kernel_initializer=init, activation='relu'))
    model.add(Dense(1, kernel_initializer=init, activation='sigmoid'))
         # Modelo de compilación
    model.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    return model
 
semilla = 7 # Establecer semilla aleatoria
np.random.seed(seed)
 
 # Importar datos
dataset = np.loadtxt(r'F:\Python\pycharm\keras_deeplearning\datasets\PimaIndiansdiabetes.csv', delimiter=',', skiprows=1)
 #Dividir la variable de entrada xy la variable de salida Y
x = dataset[:, 0:8]
Y = dataset[:, 8]
 
 # Crear modelo, los parámetros de iteración son (modelo, período, tamaño de lote, papel detallado = 0: desactivar la salida detallada de fit () y evaluar () del modelo)
model = KerasClassifier(build_fn=create_model, verbose=0)
 
 # Crear parámetros que necesitan ajuste
param_grid = {}
param_grid['optimizer'] = ['rmsprop', 'adam']
param_grid['init'] = ['glorot_uniform', 'normal', 'uniform']
param_grid['epochs'] = [50,100,150,200]
param_grid['batch_size'] = [5,10,20]
 
 #    
grid = GridSearchCV(estimator=model, param_grid=param_grid)
results = grid.fit(x,Y)
 
 # Resultado de salida
print('Best: %f using %s' % (results.best_score_, results.best_params_))
means = results.cv_results_['mean_test_score']
stds = results.cv_results_['std_test_score']
params = results.cv_results_['params']
 
for mean, std, param in zip(means,stds,params):
    print('%f (%f) with: %r' % (mean, std, param))