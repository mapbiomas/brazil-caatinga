import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline
from collections import Counter

X = np.load("./data/train_00000000000000000ce1.npy", allow_pickle=True)
y = np.load("./data/test_00000000000000000ce1.npy", allow_pickle=True)

print(X.shape)
print(y.shape)

print()

counter = Counter(y)
print(counter)

# define pipeline
over = SMOTE(sampling_strategy=0.1)
under = RandomUnderSampler(sampling_strategy=0.5)
steps = [('o', over), ('u', under)]
pipeline = Pipeline(steps=steps)
# transform the dataset
X, y = pipeline.fit_resample(X, y)
# summarize the new class distribution
counter = Counter(y)
print(counter)