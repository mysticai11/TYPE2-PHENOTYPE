import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
import joblib
import torch

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.validation.benchmark import calc_hsi, calc_fli

def calculate_net_benefit(y_true, y_pred_prob, p_t):
    if p_t == 1.0:
        return 0.0
    
    # Binary predictions based on threshold
    y_pred = (y_pred_prob >= p_t).astype(int)
    
    # Calculate TP and FP
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    N = len(y_true)
    
    net_benefit = (tp / N) - (fp / N) * (p_t / (1 - p_t))
    return net_benefit

def compute_dca_curves():
    """Computes DCA curves for LMSIS (Z2), FLI, and HSI."""
    print("Loading data for DCA computation...")
    df = load_data()
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    
    X_all, u_all, _, m_all, _, df_derived_all, _, _ = preprocess_data(df, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    model = iVAE_MetabolicStateModel()
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt"), map_location="cpu"))
    model.eval()
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_all, dtype=torch.float32), torch.tensor(u_all, dtype=torch.float32))
        z_all = mu_q.numpy()

    # Filter only samples with valid CAP ground truth and Normal-BMI for the specific claim
    cap_mask = (m_all[:, 1] == 1) & (df_derived_all['bmi'] >= 18.5) & (df_derived_all['bmi'] < 25.0)
    df_eval = df_derived_all[cap_mask].copy()
    z2_labeled = z_all[cap_mask, 1]
    cap_actual = df_eval['cap_score'].values

    y_true = (cap_actual >= 248).astype(int) # Liver fat ground truth

    # Calculate scores
    scores = {
        'HSI': calc_hsi(df_eval).values,
        'FLI': calc_fli(df_eval).values,
        'LMSIS': z2_labeled
    }

    # Normalize scores to pseudo-probabilities [0, 1] using min-max scaling for DCA comparison
    # In real clinical DCA, scores are often converted to probabilities via logistic regression.
    # Here we use Min-Max scaling as a proxy to map them into the [0, 1] threshold space.
    probs = {}
    for name, s in scores.items():
        s_clean = np.nan_to_num(s, nan=np.nanmin(s))
        s_min, s_max = np.min(s_clean), np.max(s_clean)
        if s_max > s_min:
            probs[name] = (s_clean - s_min) / (s_max - s_min)
        else:
            probs[name] = np.zeros_like(s_clean)

    thresholds = np.arange(0.01, 0.41, 0.01) # 1% to 40%
    dca_results = []

    prevalence = np.mean(y_true)

    for p_t in thresholds:
        treat_all_nb = prevalence - (1 - prevalence) * (p_t / (1 - p_t))
        treat_none_nb = 0.0

        pt_results = {
            "threshold": f"{int(p_t * 100)}%",
            "Treat All": round(float(treat_all_nb), 4),
            "Treat None": round(float(treat_none_nb), 4)
        }

        for name, prob in probs.items():
            nb = calculate_net_benefit(y_true, prob, p_t)
            pt_results[name] = round(float(nb), 4)

        dca_results.append(pt_results)

    # Filter for frontend UI to match 10, 15, 20, 25, 30, 35% specifically
    ui_thresholds = ["10%", "15%", "20%", "25%", "30%", "35%"]
    filtered_results = [r for r in dca_results if r["threshold"] in ui_thresholds]

    return filtered_results

if __name__ == "__main__":
    res = compute_dca_curves()
    print("DCA Results:")
    for r in res:
        print(r)
