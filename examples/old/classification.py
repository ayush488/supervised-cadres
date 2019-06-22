## classification-example.py
## author: alexander new

'''In this example, we train a binary classification cadre model on the breast cancer dataset.
Information about the breast cancer dataset may be found (e.g.)
here: https://archive.ics.uci.edu/ml/datasets/Breast+Cancer+Wisconsin+(Diagnostic)
The goal is to predict whether a cell nucleus is benign or malignant.
We also compare with a linear SVM. This classification task is quite easy, so
we do not expect the cadre model to be significantly better than the linear model.
'''

from __future__ import division, print_function, absolute_import

import numpy as np
import scipy.stats as ss
import pandas as pd
import cadreModels.classification as sc
from sklearn.datasets import load_breast_cancer
from sklearn.svm import LinearSVC
import matplotlib.pyplot as plt

#######################
## construct dataset ##
#######################

breastCancer = load_breast_cancer()
D = pd.DataFrame(breastCancer['data']).assign(target=breastCancer['target']).sample(frac=1, random_state=662352).values

## train and test set sizes
Ntr = int(np.ceil(0.75*D.shape[0]))
Nte = D.shape[0] - Ntr
P = D.shape[1]-1

### train and test splits
Xtr, Ytr = D[:Ntr,:-1], D[:Ntr,-1]
Xva, Yva = D[Ntr:,:-1], D[Ntr:,-1]
Xva, Xtr = ss.zmap(Xva, Xtr), ss.zscore(Xtr)   

Tmax = 1001
M = 2                # number of cadres
alpha_d, alpha_W = 0.95, 0.05 # d is more l1, W is more l2
lambda_d, lambda_W = 0.01, 0.05   # regularization strength

##################
## learn models ##
##################

cadreModel = sc.kClassCadreModel(M=M, alpha_d=alpha_d, alpha_W=alpha_W, 
                                 lambda_d=lambda_d, lambda_W=lambda_W, Tmax=Tmax)
cadreModel.fit(Xtr=Xtr, Ytr=Ytr, Xva=Xva, Yva=Yva, seed=1512)
## calculate classification score, label, membership probabilities, and cadre for validation data
fVa, lVa, Gva, mVa = cadreModel.predictFull(Xva)

## learn svm
lsvc = LinearSVC(loss='hinge', C=0.1)
lsvc.fit(Xtr, Ytr)

######################
## evaluate results ##
######################

## plot class label vs. predicted margin for the test set,
## colored by cadre membership. we introduce a slight jitter on the x-axis to
## avoid overlaps. true negative points above the horizontal line are misclassified.
## true positive points below the horizontal line are misclassified.
colors = {(0,0): 'blue', (0,1): 'red', (1,0): 'green', (1,1): 'orange'}
for m in range(M):
    plt.scatter(Yva[np.where(mVa==m)]+m/10,
                fVa[np.where(mVa==m),0],
                facecolors='none', edgecolors=colors[m,m], label='cadre_'+str(m))
plt.scatter(Yva-1/10, lsvc.decision_function(Xva), facecolors='none', edgecolors=colors[0,1], label='svm')
plt.axhline()
plt.legend(loc='center')
plt.xlabel('true label')
plt.ylabel('predicted margin')
plt.show()

## plot distribution of cadre assignment weights
plt.plot(np.arange(P), np.abs(cadreModel.d))
plt.xlabel('feature index')
plt.ylabel('cadre assignment weight')
plt.show()

## find out what features are used for cadre assignment
threshold = 0.01
print('features used for cadre assignment')
print(breastCancer.feature_names[np.where(np.abs(cadreModel.d) > threshold)])
print('only', np.sum(np.abs(cadreModel.d) > threshold), 'out of', P, 'features are used for',
      'cadre assignment at a threshold of', threshold)

## plot distribution of cadre centers
for m in range(M):
    plt.plot(np.arange(P), cadreModel.C[:,m], c=colors[m,m], label='cadre_'+str(m))
plt.axhline(y=0, xmin=0, xmax=P, color='black', label='reference')
plt.legend(loc='upper left')
plt.xlabel('feature index')
plt.ylabel('cadre center')
plt.show()

## plot distribution of softmax regression weights
## colored by cadre and target
## include linear svm for comparison
for m in range(M):
    for k in range(np.unique(Ytr).shape[0]):
        plt.plot(np.arange(P), cadreModel.W[k,:,m], c=colors[m,k], label='label-'+str(k)+'_cadre-'+str(m))
plt.plot(np.arange(P), np.squeeze(lsvc.coef_), c='green', label='lsvm')
plt.axhline(color='black', label='reference')
plt.legend(loc='upper left')
plt.xlabel('feature index')
plt.ylabel('linear model weight')
plt.show()

## calculate train set and test set classification rate for each model
print('supervised cadre model training error, generalization error')
print(cadreModel.accs[-1], cadreModel.accsVa[-1])
print('linear SVM training error, generalization error')
print(np.sum(lsvc.predict(Xtr)==Ytr)/Xtr.shape[0],
      np.sum(lsvc.predict(Xva)==Yva)/Xva.shape[0])
