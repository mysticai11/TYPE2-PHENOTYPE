import numpy as np
from sklearn.metrics import roc_auc_score, r2_score

def reconstruction_mse(x, x_hat):
    return np.mean((x - x_hat) ** 2)

def compute_r2(y_true, y_pred):
    return r2_score(y_true, y_pred)
