




# https://medium.com/turo-engineering/how-not-to-use-random-forest-265a19a68576
from collections import default
dictX = X.as_matrix()
scores = defaultdict(list)## Pseudo code:
# For 100 random draw of train / test (70%/30%):
    # fit a random forest 
    # compute the accuracy (acc) 
    # For each feature: 
        # randomly permute the observations of the feature
        # compute the accuracy with random permutation (shuff_acc)
        # compute the decrease in accuracy between acc and shuff_acc
        # store this value
# compute the mean decrease accuracy over the 100 draws for each feature

for train_idx, test_idx in ShuffleSplit(len(X), 100, .3):
    X_train, X_test = X[train_idx], X[test_idx]
    Y_train, Y_test = Y[train_idx], Y[test_idx]
    rf = reg.fit(X_train, Y_train)
    acc = r2_score(Y_test, rf.predict(X_test))
    for i in range(X.shape[1]):
        X_t = X_test.copy()
        np.random.shuffle(X_t[:, i])
        shuff_acc = r2_score(Y_test, rf.predict(X_t))
        scores[features[i]].append((acc-shuff_acc)/acc)

mda_features = [f for f in scores.keys()]
mda_importance = [(np.mean(score)) for score in scores.values()]
mda_indices = np.argsort(mda_importance)

plt.title('Feature Importances')
plt.barh(range(len(mda_indices)), [mda_importance[i] for i in mda_indices], color='#8f63f4', align='center')
plt.yticks(range(len(mda_indices)), [mda_features[i] for i in mda_indices])
plt.xlabel('Mean decrease accuracy')
plt.show()
# Original code come from http://blog.datadive.net/selecting-good-features-part-iii-random-forests/