import os
import joblib
import torch
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src_code.model.ivae import iVAE_MetabolicStateModel

class DummyConformal:
    def __init__(self):
        self.q_alphas = {0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1}
        
    def get_quadrant(self, z1, z2):
        if z1 < 0 and z2 < 0: return 0
        if z1 >= 0 and z2 < 0: return 1
        if z1 < 0 and z2 >= 0: return 2
        return 3

    def predict(self, z, alpha=0.1):
        import numpy as np
        risk = 1 / (1 + np.exp(-z[0, 0]))
        return np.array([risk]), np.zeros((1, 2), dtype=bool)

class ModelRegistry:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.u_encoder = None
        self.conformal_surface = None

    def load_models(self):
        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        self.model = iVAE_MetabolicStateModel(beta=4.0, lambda_anchor=0.5)
        try:
            self.model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
            self.scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
            self.u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
            self.conformal_surface = DummyConformal()
            print("Models loaded successfully.")
        except Exception as e:
            print(f"Warning: Could not load all models: {e}. You may need to run training first.")
            from sklearn.preprocessing import RobustScaler, OneHotEncoder
            from sklearn.linear_model import LogisticRegression
            self.scaler = RobustScaler().fit([[0]*15])
            self.u_encoder = OneHotEncoder().fit([[1]])
            self.conformal_surface = DummyConformal()

registry = ModelRegistry()
