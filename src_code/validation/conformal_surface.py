import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib
import os

class PhenotypicMondrianConformalPredictor:
    def __init__(self, z1_threshold=0.0, z2_threshold=0.0):
        self.z1_threshold = z1_threshold
        self.z2_threshold = z2_threshold
        self.base_model = LogisticRegression(C=1.0, random_state=99)
        self.q_alphas = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}

    def get_quadrant(self, z1, z2):
        if z1 < self.z1_threshold and z2 < self.z2_threshold: return 0
        if z1 >= self.z1_threshold and z2 < self.z2_threshold: return 1
        if z1 < self.z1_threshold and z2 >= self.z2_threshold: return 2
        return 3

    def fit(self, z_cal, y_cal, alpha=0.10):
        self.base_model.fit(z_cal, y_cal)
        probs = self.base_model.predict_proba(z_cal)
        scores = np.zeros(len(y_cal))
        for i, y in enumerate(y_cal):
            scores[i] = 1.0 - probs[i, int(y)]
            
        for q in range(4):
            idx = [i for i in range(len(z_cal)) if self.get_quadrant(z_cal[i, 0], z_cal[i, 1]) == q]
            if len(idx) > 0:
                q_scores = scores[idx]
                n = len(q_scores)
                val = np.quantile(q_scores, np.clip(np.ceil((n + 1) * (1 - alpha)) / n, 0.0, 1.0))
                self.q_alphas[q] = val
            else:
                self.q_alphas[q] = 1.0 - alpha

    def predict(self, z_test, alpha=0.10):
        probs = self.base_model.predict_proba(z_test)
        pred_sets = np.zeros((len(z_test), 2), dtype=bool)
        for i in range(len(z_test)):
            q = self.get_quadrant(z_test[i, 0], z_test[i, 1])
            q_alpha = self.q_alphas.get(q, 1.0 - alpha)
            threshold = 1.0 - q_alpha
            pred_sets[i, 0] = probs[i, 0] >= threshold
            pred_sets[i, 1] = probs[i, 1] >= threshold
            if not pred_sets[i, 0] and not pred_sets[i, 1]:
                pred_sets[i, np.argmax(probs[i])] = True
        return probs[:, 1], pred_sets

def fit_conformal_risk_surface(z_cal, ir_label_cal, z_test, ir_label_test, alpha=0.10):
    mapie = PhenotypicMondrianConformalPredictor(z1_threshold=np.median(z_cal[:, 0]), z2_threshold=np.median(z_cal[:, 1]))
    mapie.fit(z_cal, ir_label_cal, alpha=alpha)
    _, pred_sets = mapie.predict(z_test, alpha=alpha)
    coverage = np.mean([pred_sets[i, int(ir_label_test[i])] for i in range(len(z_test))])
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(mapie, os.path.join(models_dir, "conformal_surface.pkl"))
    return {"nominal_coverage": 1 - alpha, "empirical_coverage": round(float(coverage), 4), "coverage_gap": round(float(coverage - (1 - alpha)), 4)}, mapie
