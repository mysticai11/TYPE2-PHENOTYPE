"""
audit_l_cycle.py
================
Rigorous mechanical audit of the NHANES 2021-2023 (L-cycle) holdout.

Checks:
1. Baseline N-size consistency
2. 5-Seed stability of DA-SS-iVAE (L vs P cycle)
3. CAP Distribution Shift (L vs P vs J)
4. Conformal Interval Width expansion
"""

import os, sys, json
import numpy as np
import pandas as pd
import scipy.stats as stats
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import joblib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src_code.data.nhanes_multi_cycle import load_data as load_cycle
from src_code.data.nhanes_l_cycle import load_l_cycle_data
from src_code.data.preprocess import preprocess_data, derive_features, FEATURE_COLS
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.utils.seeds import set_all_seeds
from src_code.validation.benchmark import calc_hsi, calc_nafld_lfs, calc_fli, calc_tyg
from src_code.validation.conformal_surface import PhenotypicMondrianConformalPredictor

RESULTS_DIR = os.path.join(ROOT, "results")
DATA_DIR    = os.path.join(ROOT, "src_code", "data")
SEEDS   = [42, 7, 123, 999, 2024]
PARAMS  = {"beta": 4.0, "lam1": 0.8, "lam2": 1.2, "lam_ortho": 0.1}
LR      = 1e-3
PATIENCE = 20
MAX_EPOCHS = 150

def get_baselines(df):
    return {
        "HSI": calc_hsi(df),
        "NAFLD-LFS": calc_nafld_lfs(df),
        "FLI": calc_fli(df),
        "TyG": calc_tyg(df)
    }

def train_and_eval_multi(df_train, df_val, df_p, df_l, seed):
    set_all_seeds(seed, seed * 29)
    X_tr, u_tr, h_tr, m_tr, _, _, scaler, u_enc = preprocess_data(df_train, is_train=True)
    X_va, u_va, h_va, m_va, _, _, _, _ = preprocess_data(df_val, scaler=scaler, u_encoder=u_enc, is_train=False)

    def make_loader(X, u, h, m, shuffle=True):
        return DataLoader(
            TensorDataset(torch.tensor(X, dtype=torch.float32),
                          torch.tensor(u, dtype=torch.float32),
                          torch.tensor(h, dtype=torch.float32),
                          torch.tensor(m, dtype=torch.float32)),
            batch_size=64, shuffle=shuffle)

    tr_loader = make_loader(X_tr, u_tr, h_tr, m_tr, shuffle=True)
    va_loader = make_loader(X_va, u_va, h_va, m_va, shuffle=False)

    model = iVAE_MetabolicStateModel(**PARAMS)
    optim = AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = CosineAnnealingLR(optim, T_max=MAX_EPOCHS, eta_min=1e-5)

    best_val, patience_ctr, stop_epoch = -np.inf, 0, MAX_EPOCHS
    for epoch in range(MAX_EPOCHS):
        model.train()
        for x_b, u_b, h_b, m_b in tr_loader:
            x_hat, mu_q, lv_q, mu_p, lv_p, h_hat, z = model(x_b, u_b)
            loss, *_ = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, lv_q, mu_p, lv_p, h_hat, z)
            optim.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
        sched.step()

        model.eval()
        val_loss = sum(
            model.loss(x_b, u_b, h_b, m_b, *model(x_b, u_b)[:6], model(x_b, u_b)[6])[0].item() * len(x_b)
            for x_b, u_b, h_b, m_b in va_loader
        )
        val_score = -(val_loss / len(va_loader.dataset))
        if val_score > best_val:
            best_val = val_score
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_ctr = 0
        else:
            patience_ctr += 1
            if patience_ctr >= PATIENCE:
                stop_epoch = epoch
                break
    model.load_state_dict(best_state)
    
    # Eval helper
    def encode(df_input):
        df_d = derive_features(df_input)
        X = scaler.transform(df_d[FEATURE_COLS])
        age = df_d[["age"]].values
        sex = (df_d["sex"] == 2).astype(float).values.reshape(-1, 1)
        anc = u_enc.transform(df_d[["ancestry_proxy"]])
        u   = np.hstack([age / 100.0, sex, anc[:, 1:]])
        model.eval()
        with torch.no_grad():
            mu_q, _ = model.encoder(torch.tensor(X, dtype=torch.float32), torch.tensor(u, dtype=torch.float32))
        return mu_q.numpy(), df_d

    # Encode P
    z_p, df_p_d = encode(df_p)
    valid_p = df_p_d['cap_score'].notna()
    rho_p_z2, _ = stats.spearmanr(z_p[valid_p, 1], df_p_d['cap_score'].values[valid_p])
    homa_p = (df_p_d['fasting_insulin_uU_mL'].values * df_p_d['fasting_glucose_mg_dL'].values) / 405.0
    rho_p_z1, _ = stats.spearmanr(z_p[:, 0], homa_p)
    
    # Encode L
    z_l, df_l_d = encode(df_l)
    valid_l = df_l_d['cap_score'].notna()
    rho_l_z2, _ = stats.spearmanr(z_l[valid_l, 1], df_l_d['cap_score'].values[valid_l])
    homa_l = (df_l_d['fasting_insulin_uU_mL'].values * df_l_d['fasting_glucose_mg_dL'].values) / 405.0
    rho_l_z1, _ = stats.spearmanr(z_l[:, 0], homa_l)
    
    return float(rho_p_z1), float(rho_p_z2), float(rho_l_z1), float(rho_l_z2), scaler, u_enc, model

def main():
    print("Loading data...")
    df_j = load_cycle(cycle="J", data_dir=DATA_DIR)
    df_p = load_cycle(cycle="P", data_dir=DATA_DIR)
    df_l = load_l_cycle_data()
    
    # Filter J for training
    df_j_train, df_j_temp = train_test_split(df_j, test_size=0.30, random_state=42)
    df_j_val, df_j_calib = train_test_split(df_j_temp, test_size=0.50, random_state=42)
    
    audit_results = {}
    
    # ── CHECK 1: N-Size Consistency ──
    print("\n[CHECK 1] N-Size Consistency on L-cycle")
    df_l_d = derive_features(df_l)
    valid_cap_l = df_l_d['cap_score'].notna()
    base_scores = get_baselines(df_l_d[valid_cap_l])
    
    n_counts = {}
    for name, scores in base_scores.items():
        missing = pd.Series(scores).isna().sum()
        n_counts[name] = len(scores) - int(missing)
        print(f"  {name}: N = {n_counts[name]}")
    audit_results['baseline_n_counts'] = n_counts

    # ── CHECK 2: CAP Distribution Shift ──
    print("\n[CHECK 2] CAP Distribution Shift")
    cap_j = df_j['cap_score'].dropna().values
    cap_p = df_p['cap_score'].dropna().values
    cap_l = df_l['cap_score'].dropna().values
    
    dist_stats = {}
    for name, arr in zip(['J-cycle', 'P-cycle', 'L-cycle'], [cap_j, cap_p, cap_l]):
        iqr = stats.iqr(arr)
        dist_stats[name] = {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'iqr': float(iqr)
        }
        print(f"  {name}: Mean={np.mean(arr):.1f} | Std={np.std(arr):.1f} | IQR={iqr:.1f}")
        
    iqr_ratio = dist_stats['L-cycle']['iqr'] / dist_stats['J-cycle']['iqr']
    print(f"  IQR Ratio (L / J): {iqr_ratio:.3f}")
    audit_results['cap_distribution'] = dist_stats
    audit_results['cap_distribution']['iqr_ratio_L_to_J'] = float(iqr_ratio)
    
    # ── CHECK 3: 5-Seed Stability ──
    print("\n[CHECK 3] 5-Seed Stability & Z1/Z2 Breakdown...")
    seed_rhos_p_z1 = []
    seed_rhos_p_z2 = []
    seed_rhos_l_z1 = []
    seed_rhos_l_z2 = []
    
    last_scaler, last_u_enc, last_model = None, None, None
    for s in SEEDS:
        rp_1, rp_2, rl_1, rl_2, sc, uenc, mod = train_and_eval_multi(df_j_train, df_j_val, df_p, df_l, s)
        seed_rhos_p_z1.append(rp_1); seed_rhos_p_z2.append(rp_2)
        seed_rhos_l_z1.append(rl_1); seed_rhos_l_z2.append(rl_2)
        print(f"  Seed {s}: P-cycle (Z1={rp_1:.3f}, Z2={rp_2:.3f}) | L-cycle (Z1={rl_1:.3f}, Z2={rl_2:.3f})")
        last_scaler, last_u_enc, last_model = sc, uenc, mod
        
    print(f"  P-cycle Z1 Mean: {np.mean(seed_rhos_p_z1):.3f} +/- {np.std(seed_rhos_p_z1):.3f}")
    print(f"  P-cycle Z2 Mean: {np.mean(seed_rhos_p_z2):.3f} +/- {np.std(seed_rhos_p_z2):.3f}")
    print(f"  L-cycle Z1 Mean: {np.mean(seed_rhos_l_z1):.3f} +/- {np.std(seed_rhos_l_z1):.3f}")
    print(f"  L-cycle Z2 Mean: {np.mean(seed_rhos_l_z2):.3f} +/- {np.std(seed_rhos_l_z2):.3f}")
    
    audit_results['5_seed_stability'] = {
        'P-cycle': {
            'Z1': {'mean': float(np.mean(seed_rhos_p_z1)), 'std': float(np.std(seed_rhos_p_z1))},
            'Z2': {'mean': float(np.mean(seed_rhos_p_z2)), 'std': float(np.std(seed_rhos_p_z2))}
        },
        'L-cycle': {
            'Z1': {'mean': float(np.mean(seed_rhos_l_z1)), 'std': float(np.std(seed_rhos_l_z1))},
            'Z2': {'mean': float(np.mean(seed_rhos_l_z2)), 'std': float(np.std(seed_rhos_l_z2))}
        }
    }
    
    # ── CHECK 4: Conformal Interval Width ──
    print("\n[CHECK 4] Conformal Interval Width (Using last seed model)")
    # Encode Calib and L with last model
    def encode_final(df_input):
        df_d = derive_features(df_input)
        X = last_scaler.transform(df_d[FEATURE_COLS])
        age = df_d[["age"]].values
        sex = (df_d["sex"] == 2).astype(float).values.reshape(-1, 1)
        anc = last_u_enc.transform(df_d[["ancestry_proxy"]])
        u = np.hstack([age / 100.0, sex, anc[:, 1:]])
        last_model.eval()
        with torch.no_grad():
            mu_q, _ = last_model.encoder(torch.tensor(X, dtype=torch.float32), torch.tensor(u, dtype=torch.float32))
        return mu_q.numpy(), df_d
        
    z_calib, df_calib_d = encode_final(df_j_calib)
    valid_calib = df_calib_d['cap_score'].notna()
    y_calib = (df_calib_d['cap_score'].values[valid_calib] > 274).astype(int)
    z_calib_clean = z_calib[valid_calib]
    
    z_p, df_p_d = encode_final(df_p)
    valid_p = df_p_d['cap_score'].notna()
    
    z_l, df_l_d = encode_final(df_l)
    valid_l = df_l_d['cap_score'].notna()
    
    conformal = PhenotypicMondrianConformalPredictor(z1_threshold=0.0, z2_threshold=0.0)
    conformal.fit(z_calib_clean, y_calib, alpha=0.1)
    
    # Get P-values and prediction sets for P and L
    _, p_sets = conformal.predict(z_p[valid_p])
    _, l_sets = conformal.predict(z_l[valid_l])
    
    p_set_sizes = np.sum(p_sets, axis=1)
    l_set_sizes = np.sum(l_sets, axis=1)
    
    print(f"  P-cycle Average Set Size: {np.mean(p_set_sizes):.2f} (Median: {np.median(p_set_sizes)})")
    print(f"  L-cycle Average Set Size: {np.mean(l_set_sizes):.2f} (Median: {np.median(l_set_sizes)})")
    
    # What % of people get a maximally uninformative set size of 2?
    p_uninformative = np.mean(p_set_sizes == 2)
    l_uninformative = np.mean(l_set_sizes == 2)
    print(f"  P-cycle % Uninformative Sets (Size 2): {p_uninformative:.1%}")
    print(f"  L-cycle % Uninformative Sets (Size 2): {l_uninformative:.1%}")
    
    audit_results['conformal_width'] = {
        'P-cycle': {
            'mean_set_size': float(np.mean(p_set_sizes)),
            'median_set_size': float(np.median(p_set_sizes)),
            'pct_uninformative': float(p_uninformative)
        },
        'L-cycle': {
            'mean_set_size': float(np.mean(l_set_sizes)),
            'median_set_size': float(np.median(l_set_sizes)),
            'pct_uninformative': float(l_uninformative)
        }
    }
    
    out_path = os.path.join(RESULTS_DIR, "l_cycle_audit.json")
    with open(out_path, "w") as f:
        json.dump(audit_results, f, indent=2)
    print(f"\nAudit saved to {out_path}")

if __name__ == "__main__":
    main()
