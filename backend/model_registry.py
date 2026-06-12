import os
import sys
import json
import joblib
import torch
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src_code.model.ivae import iVAE_MetabolicStateModel

# Per-quadrant achieved coverage from validation experiments (Mondrian)
ACHIEVED_COVERAGE = {
    0: 0.981,   # MHNW
    1: 0.923,   # IR-Dominant
    2: 0.954,   # Steatosis-Dominant
    3: 0.854,   # Dual-Burden
}

class DummyConformal:
    """Fallback when conformal_surface.pkl is not yet generated."""
    def __init__(self):
        self.q_alphas = {0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1}
        self.z1_threshold = 0.0
        self.z2_threshold = 0.0

    def get_quadrant(self, z1, z2):
        if z1 < 0 and z2 < 0: return 0
        if z1 >= 0 and z2 < 0: return 1
        if z1 < 0 and z2 >= 0: return 2
        return 3

    def predict(self, z, alpha=0.1):
        risk = float(1 / (1 + np.exp(-z[0, 0])))
        return np.array([risk]), np.zeros((1, 2), dtype=bool)


class ModelRegistry:
    def __init__(self):
        self.models = {}
        self.model = None
        self.scaler = None
        self.u_encoder = None
        self.conformal_surface = None
        self.anchor_stats = None
        # Precomputed training data for percentile ranks and /cohort endpoint
        self.training_z = None          # (N, 2) latent coordinates of training set
        self.training_quadrants = None  # (N,) quadrant assignments
        self.z1_sorted = None           # sorted for percentile lookup
        self.z2_sorted = None
        # MinCovDet for distribution shift detection
        self.mcd = None

    def load_models(self):
        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        self.load_model_variant(models_dir, "default")
        
        # Support legcy direct accesses
        default_variant = self.models.get("default", {})
        self.model = default_variant.get("model")
        self.scaler = default_variant.get("scaler")
        self.u_encoder = default_variant.get("u_encoder")
        self.conformal_surface = default_variant.get("conformal_surface")
        self.anchor_stats = default_variant.get("anchor_stats")

    def load_model_variant(self, models_dir, model_id):
        # --- Load core model artifacts ---
        model = iVAE_MetabolicStateModel(x_dim=14, beta=4.0)
        try:
            model.load_state_dict(
                torch.load(os.path.join(models_dir, "ivae_best.pt"), map_location="cpu")
            )
            model.eval()
            scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
            u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))

            # Conformal surface
            conformal_path = os.path.join(models_dir, "conformal_surface.pkl")
            if os.path.exists(conformal_path):
                conformal_surface = joblib.load(conformal_path)
            else:
                print("Warning: conformal_surface.pkl not found — using dummy conformal predictor.")
                conformal_surface = DummyConformal()

            # Anchor normalization stats
            stats_path = os.path.join(models_dir, "anchor_stats.json")
            if os.path.exists(stats_path):
                with open(stats_path) as f:
                    anchor_stats = json.load(f)
            else:
                anchor_stats = {
                    "homa_mean": 0.0, "homa_std": 1.0,
                    "cap_mean": 0.0, "cap_std": 1.0,
                }

            self.models[model_id] = {
                "model": model,
                "scaler": scaler,
                "u_encoder": u_encoder,
                "conformal_surface": conformal_surface,
                "anchor_stats": anchor_stats
            }

            # Precompute training Z-coordinates using loaded scaler and model
            # To allow _precompute_training_embeddings to run, temporarily set legacy properties
            self.model = model
            self.scaler = scaler
            self.u_encoder = u_encoder
            self.conformal_surface = conformal_surface
            self._precompute_training_embeddings(models_dir)

            print(f"Model variant '{model_id}' loaded successfully (x_dim=14).")
        except Exception as e:
            print(f"Warning: Could not load model variant '{model_id}': {e}. Using fallback defaults.")
            from sklearn.preprocessing import RobustScaler, OneHotEncoder
            fallback_scaler = RobustScaler().fit([[0] * 14])
            fallback_u_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore').fit([[1]])
            fallback_conformal = DummyConformal()
            fallback_stats = {"homa_mean": 0.0, "homa_std": 1.0, "cap_mean": 0.0, "cap_std": 1.0}
            
            self.models[model_id] = {
                "model": model,
                "scaler": fallback_scaler,
                "u_encoder": fallback_u_encoder,
                "conformal_surface": fallback_conformal,
                "anchor_stats": fallback_stats
            }
            self.model = model
            self.scaler = fallback_scaler
            self.u_encoder = fallback_u_encoder
            self.conformal_surface = fallback_conformal
            self.anchor_stats = fallback_stats

    def _precompute_training_embeddings(self, models_dir):
        """Encode the full training set to get Z coordinates for percentiles and /cohort."""
        try:
            import pandas as pd
            from sklearn.model_selection import train_test_split
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from src_code.data.nhanes_loader import load_data
            from src_code.data.preprocess import preprocess_data

            df = load_data()
            X_all, u_all, _, _, _, _, _, _ = preprocess_data(
                df, scaler=self.scaler, u_encoder=self.u_encoder, is_train=False
            )
            with torch.no_grad():
                mu_q, _ = self.model.encoder(
                    torch.tensor(X_all, dtype=torch.float32),
                    torch.tensor(u_all, dtype=torch.float32)
                )
                z_all = mu_q.numpy()

            self.training_z = z_all
            self.z1_sorted = np.sort(z_all[:, 0])
            self.z2_sorted = np.sort(z_all[:, 1])

            # Assign quadrants
            tau1 = getattr(self.conformal_surface, 'z1_threshold', 0.0)
            tau2 = getattr(self.conformal_surface, 'z2_threshold', 0.0)
            q = np.zeros(len(z_all), dtype=int)
            ir = z_all[:, 0] >= tau1
            hep = z_all[:, 1] >= tau2
            q[ir & ~hep] = 1
            q[~ir & hep] = 2
            q[ir & hep] = 3
            self.training_quadrants = q

            # Fit MinCovDet for Mahalanobis distance (distribution shift detection)
            from sklearn.covariance import MinCovDet
            mcd = MinCovDet(random_state=42, support_fraction=0.9)
            mcd.fit(z_all)
            # Store the 97.5th percentile of training Mahalanobis distances as threshold
            train_distances = mcd.mahalanobis(z_all)
            self.mcd_threshold = float(np.percentile(train_distances, 97.5))
            self.mcd = mcd

        except Exception as e:
            print(f"Warning: Could not precompute training embeddings: {e}")

    def get_percentile(self, z1_val: float, z2_val: float) -> tuple:
        """Return (ir_percentile, cap_percentile) as integers 1–99."""
        if self.z1_sorted is None:
            return 50, 50
        ir_pct = int(np.searchsorted(self.z1_sorted, z1_val) / len(self.z1_sorted) * 100)
        cap_pct = int(np.searchsorted(self.z2_sorted, z2_val) / len(self.z2_sorted) * 100)
        return max(1, min(99, ir_pct)), max(1, min(99, cap_pct))

    def is_in_distribution(self, z: np.ndarray) -> bool:
        """Return True if the point is within the 97.5th percentile of training Mahalanobis distances."""
        if self.mcd is None:
            return True
        dist = float(self.mcd.mahalanobis(z.reshape(1, -1))[0])
        return dist <= self.mcd_threshold

    def unstandardize_anchor(self, h_hat: np.ndarray) -> tuple:
        """Convert standardized anchor predictions back to clinical units."""
        s = self.anchor_stats
        pred_homa_ir = float(h_hat[0]) * s["homa_std"] + s["homa_mean"]
        pred_cap = float(h_hat[1]) * s["cap_std"] + s["cap_mean"]
        return round(pred_homa_ir, 3), round(pred_cap, 1)


registry = ModelRegistry()
