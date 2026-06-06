import numpy as np
from sklearn.feature_selection import mutual_info_regression

def mutual_information_gap(z_samples: np.ndarray, factor_values: dict) -> float:
    mig_scores = []
    for factor_name, v in factor_values.items():
        mi_per_dim = [mutual_info_regression(z_samples[:, i].reshape(-1, 1), v, random_state=42)[0] for i in range(z_samples.shape[1])]
        mi_sorted = sorted(mi_per_dim, reverse=True)
        h_v = np.log(np.std(v) * np.sqrt(2 * np.pi * np.e) + 1e-8)
        mig_scores.append((mi_sorted[0] - mi_sorted[1]) / (h_v + 1e-8))
    return float(np.mean(mig_scores))
