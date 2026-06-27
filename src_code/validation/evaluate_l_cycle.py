"""
L-Cycle (2021-2023) Evaluation Script
=====================================
Evaluates the pre-trained DA-SS-iVAE model and established clinical baselines
on the newly released NHANES 2021-2023 temporal holdout cohort.
"""

import os
import sys
import torch
import joblib
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src_code.data.nhanes_multi_cycle import load_data as load_j_cycle
from src_code.data.nhanes_l_cycle import load_l_cycle_data
from src_code.data.preprocess import preprocess_data, derive_features, FEATURE_COLS
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.validation.benchmark import calc_hsi, calc_nafld_lfs, calc_fli, calc_tyg
from src_code.validation.conformal_surface import PhenotypicMondrianConformalPredictor

RESULTS_DIR = os.path.join(ROOT, "results")
MODELS_DIR = os.path.join(ROOT, "models")

def get_baselines(df):
    """Compute baselines on the raw dataframe."""
    return {
        "HSI": calc_hsi(df),
        "NAFLD-LFS": calc_nafld_lfs(df),
        "FLI": calc_fli(df),
        "TyG": calc_tyg(df)
    }

def main():
    print("--- NHANES 2021-2023 (L-CYCLE) DOUBLE TEMPORAL EVALUATION ---")
    
    # 1. Load L-Cycle Data
    df_l = load_l_cycle_data()
    
    # 2. Load J-Cycle Data (for CP Calibration bounds)
    df_j = load_j_cycle(cycle="J", data_dir=os.path.join(ROOT, "src_code", "data"))
    df_j_train, df_j_temp = train_test_split(df_j, test_size=0.30, random_state=42)
    df_j_val, df_j_calib = train_test_split(df_j_temp, test_size=0.50, random_state=42)
    
    # 3. Load Frozen Model & Preprocessors
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(MODELS_DIR, "u_encoder.pkl"))
    
    model = iVAE_MetabolicStateModel()
    model.load_state_dict(torch.load(os.path.join(MODELS_DIR, "ivae_best.pt")))
    model.eval()
    
    # 4. Preprocess Data
    def encode_df(df_input):
        df_d = derive_features(df_input)
        X = scaler.transform(df_d[FEATURE_COLS])
        age = df_d[["age"]].values
        sex = (df_d["sex"] == 2).astype(float).values.reshape(-1, 1)
        anc = u_encoder.transform(df_d[["ancestry_proxy"]])
        u = np.hstack([age / 100.0, sex, anc[:, 1:]])
        with torch.no_grad():
            mu_q, _ = model.encoder(torch.tensor(X, dtype=torch.float32),
                                    torch.tensor(u, dtype=torch.float32))
        return mu_q.numpy(), df_d

    print("Encoding L-cycle data through frozen DA-SS-iVAE...")
    z_l, df_l_derived = encode_df(df_l)
    
    z_calib, df_calib_derived = encode_df(df_j_calib)
    
    # Evaluate Spearman rho against FibroScan CAP
    # Drop rows missing CAP in L-cycle (should be handled in loader, but safety check)
    valid_mask = df_l_derived['cap_score'].notna()
    z2_preds = z_l[valid_mask, 1]
    cap_true = df_l_derived['cap_score'].values[valid_mask]
    
    ivae_rho, pval = spearmanr(z2_preds, cap_true)
    
    print("\n--- PHASE 2: Zero-Shot Spearman Correlation (Z2 vs CAP) ---")
    print(f"DA-SS-iVAE (L-cycle): rho = {ivae_rho:.4f} (p={pval:.2e})")
    
    results = {"DA-SS-iVAE": float(ivae_rho)}
    
    # Compute Baselines
    baselines = get_baselines(df_l_derived[valid_mask])
    for name, scores in baselines.items():
        rho, _ = spearmanr(scores, cap_true)
        results[name] = float(rho)
        print(f"{name:<15}: rho = {rho:.4f}")
        
    # --- PHASE 3: Conformal Coverage Check ---
    print("\n--- PHASE 3: Mondrian Conformal Coverage Transfer ---")
    # Calibrate on J-cycle
    calib_mask = df_calib_derived['cap_score'].notna()
    y_calib = (df_calib_derived['cap_score'].values[calib_mask] > 274).astype(int)
    z_calib_clean = z_calib[calib_mask]
    
    # Quadrant assignment
    def get_quadrants(z):
        q = np.zeros(len(z))
        q[(z[:,0] > 0) & (z[:,1] <= 0)] = 1
        q[(z[:,0] <= 0) & (z[:,1] > 0)] = 2
        q[(z[:,0] > 0) & (z[:,1] > 0)] = 3
        return q

    q_calib = get_quadrants(z_calib_clean)
    
    conformal = PhenotypicMondrianConformalPredictor(z1_threshold=0.0, z2_threshold=0.0)
    conformal.fit(z_calib_clean, y_calib, alpha=0.1)
    
    # Predict on L-cycle
    y_l = (cap_true > 274).astype(int)
    q_l = get_quadrants(z_l[valid_mask])
    
    p_values_1, prediction_sets = conformal.predict(z_l[valid_mask])
    
    q_names = {0: 'MHNW', 1: 'IR-Dominant', 2: 'Steatosis-Dominant', 3: 'Dual-Burden'}
    coverage_results = {}
    
    for q in range(4):
        idx = np.where(q_l == q)[0]
        if len(idx) == 0: continue
        cov = np.mean([prediction_sets[i, y_l[i]] for i in idx])
        coverage_results[q_names[q]] = float(cov)
        print(f"Quadrant {q} ({q_names[q]:<20}) L-Cycle Coverage: {cov:.2%}")
        
    # Save results
    out_dict = {
        "n_samples": int(len(cap_true)),
        "spearman_rhos": results,
        "mondrian_coverage_alpha_0.1": coverage_results
    }
    
    out_path = os.path.join(RESULTS_DIR, "temporal_ood_2023.json")
    with open(out_path, "w") as f:
        json.dump(out_dict, f, indent=2)
    print(f"\nResults saved to {out_path}")

if __name__ == "__main__":
    main()
