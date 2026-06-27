"""
train_temporal.py — Strict Temporal Split Training
====================================================
REPLACES train.py for the dissertation's primary DA-SS-iVAE training.

Key difference from train.py:
  train.py:        df = load_data()                 # loads J+P merged → random 70/30
  train_temporal:  df = load_data(cycle="J")        # loads J-cycle ONLY → random 70/30
                   df_p = load_data(cycle="P")      # NEVER used in training

This means the P-cycle (n=903) is a genuine temporal holdout: no P-cycle
participant was present in the training or validation set in any form.
The resulting rho on P-cycle is a true temporal OOD result.

Output:
  models/ivae_temporal.pt      — strictly J-trained checkpoint
  results/temporal_ood_comparison.json — comparison table for dissertation
"""

import os
import sys
import json
import torch
import numpy as np
from torch.utils.data import TensorDataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.model_selection import train_test_split
import scipy.stats as stats

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src_code.data.nhanes_multi_cycle import load_data as load_cycle
from src_code.data.preprocess import preprocess_data, derive_features, FEATURE_COLS
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.utils.seeds import set_all_seeds

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
MODELS_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


def evaluate_validation(model, val_loader):
    model.eval()
    val_loss = 0.0
    with torch.no_grad():
        for x_b, u_b, h_b, m_b in val_loader:
            x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z = model(x_b, u_b)
            loss, _, _, _ = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z)
            val_loss += loss.item() * x_b.size(0)
    return -(val_loss / len(val_loader.dataset))


def encode_with_model(model, scaler, u_encoder, df):
    """Encode a DataFrame using a trained model and frozen scalers."""
    df_derived = derive_features(df)
    X_raw = df_derived[FEATURE_COLS]
    X_scaled = scaler.transform(X_raw)

    age = df_derived[["age"]].values
    sex = (df_derived["sex"] == 2).astype(float).values.reshape(-1, 1)
    ancestry = df_derived[["ancestry_proxy"]]
    anc_encoded = u_encoder.transform(ancestry)
    u_encoded = np.hstack([age / 100.0, sex, anc_encoded[:, 1:]])

    x_t = torch.tensor(X_scaled, dtype=torch.float32)
    u_t = torch.tensor(u_encoded, dtype=torch.float32)

    model.eval()
    with torch.no_grad():
        mu_q, _ = model.encoder(x_t, u_t)

    return mu_q[:, 0].numpy(), mu_q[:, 1].numpy()


def train_temporal():
    set_all_seeds(42, 1234)
    best_params = {"beta": 4.0, "lam1": 0.8, "lam2": 1.2, "lam_ortho": 0.1}
    best_lr = 1e-3

    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # --- Load J-cycle ONLY for training ---
    print("\n[TEMPORAL SPLIT] Loading J-cycle (2017-2018) for training only...")
    df_j = load_cycle(cycle="J", data_dir=data_dir)
    if df_j is None or len(df_j) == 0:
        print("[ERROR] J-cycle data not available. Cannot run temporal experiment.")
        return None

    print(f"  J-cycle cohort: n={len(df_j)}")
    print(f"  J CAP available: {df_j['cap_score'].notna().sum()}")

    # --- Load P-cycle — NEVER seen during training ---
    print("\n[TEMPORAL SPLIT] Loading P-cycle (2019-2020) — HELD OUT, never in training...")
    df_p = load_cycle(cycle="P", data_dir=data_dir)
    if df_p is None or len(df_p) == 0:
        print("[ERROR] P-cycle data not available.")
        return None

    print(f"  P-cycle cohort: n={len(df_p)}")
    print(f"  P CAP available: {df_p['cap_score'].notna().sum()}")

    # --- Random 70/30 split within J-cycle only ---
    df_train, df_temp = train_test_split(df_j, test_size=0.30, random_state=42)
    df_val, df_test   = train_test_split(df_temp, test_size=0.50, random_state=42)
    print(f"\n  Train (70% of J): n={len(df_train)}")
    print(f"  Val   (15% of J): n={len(df_val)}")
    print(f"  Test  (15% of J): n={len(df_test)}")

    # --- Preprocess (fit scaler on J-train only) ---
    X_train, u_train, h_train, m_train, y_train, _, scaler, u_encoder = preprocess_data(df_train, is_train=True)
    X_val,   u_val,   h_val,   m_val,   y_val,   _, _, _ = preprocess_data(df_val,   scaler=scaler, u_encoder=u_encoder, is_train=False)
    X_test,  u_test,  h_test,  m_test,  y_test,  _, _, _ = preprocess_data(df_test,  scaler=scaler, u_encoder=u_encoder, is_train=False)

    # --- DataLoaders ---
    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train, dtype=torch.float32),
                      torch.tensor(u_train, dtype=torch.float32),
                      torch.tensor(h_train, dtype=torch.float32),
                      torch.tensor(m_train, dtype=torch.float32)),
        batch_size=64, shuffle=True
    )
    val_loader = DataLoader(
        TensorDataset(torch.tensor(X_val, dtype=torch.float32),
                      torch.tensor(u_val, dtype=torch.float32),
                      torch.tensor(h_val, dtype=torch.float32),
                      torch.tensor(m_val, dtype=torch.float32)),
        batch_size=64, shuffle=False
    )

    # --- Train ---
    model = iVAE_MetabolicStateModel(**best_params)
    optim = AdamW(model.parameters(), lr=best_lr, weight_decay=1e-4)
    sched = CosineAnnealingLR(optim, T_max=150, eta_min=1e-5)

    ckpt_path = os.path.join(MODELS_DIR, "ivae_temporal.pt")
    best_val_score, patience_counter = -np.inf, 0
    PATIENCE = 20
    stopped_epoch = 150

    print("\n[TEMPORAL] Training DA-SS-iVAE on J-cycle only (max 150 epochs)...")
    for epoch in range(150):
        model.train()
        for x_b, u_b, h_b, m_b in train_loader:
            x_hat, mu_q, logvar_q, mu_p_prior, logvar_p_prior, h_hat, z = model(x_b, u_b)
            loss, _, _, _ = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p_prior, logvar_p_prior, h_hat, z)
            optim.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optim.step()
        sched.step()

        val_score = evaluate_validation(model, val_loader)
        if val_score > best_val_score:
            best_val_score = val_score
            torch.save(model.state_dict(), ckpt_path)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                stopped_epoch = epoch
                print(f"  Early stopping at epoch {epoch}")
                break

        if epoch % 10 == 0:
            print(f"  Epoch {epoch:03d} | Val Score: {val_score:.4f}")

    print(f"\n  Training complete. Best checkpoint: {ckpt_path}")
    model.load_state_dict(torch.load(ckpt_path))

    # --- Evaluate on J-cycle internal test (in-distribution) ---
    print("\n[EVAL] Internal J-cycle test (in-distribution)...")
    z1_jtest, z2_jtest = encode_with_model(model, scaler, u_encoder, df_test)
    df_test_eval = df_test.copy().reset_index(drop=True)
    df_test_cap = df_test_eval.dropna(subset=["cap_score"])
    j_internal_results = {}
    if len(df_test_cap) >= 10:
        df_test_cap = df_test_cap.copy()
        idx = df_test_cap.index
        z2_cap = z2_jtest[idx] if len(z2_jtest) > max(idx) else None
        if z2_cap is not None:
            rho_j_int, p_j_int = stats.spearmanr(z2_cap, df_test_cap["cap_score"].values)
            j_internal_results = {"rho": round(float(rho_j_int), 4), "p": float(p_j_int), "n": len(df_test_cap)}
            print(f"  J-cycle internal test: rho={rho_j_int:.4f}, n={len(df_test_cap)}")

    # --- Evaluate on P-cycle (genuine temporal OOD) ---
    print("\n[EVAL] P-cycle temporal OOD (genuine — zero P-cycle data in training)...")
    z1_p, z2_p = encode_with_model(model, scaler, u_encoder, df_p)
    df_p_eval = df_p.copy().reset_index(drop=True)
    df_p_cap = df_p_eval.dropna(subset=["cap_score"])
    p_ood_results = {}
    if len(df_p_cap) >= 30:
        z2_pcap = z2_p[df_p_cap.index]
        rho_p, p_p = stats.spearmanr(z2_pcap, df_p_cap["cap_score"].values)
        p_ood_results = {"rho": round(float(rho_p), 4), "p": float(p_p), "n": len(df_p_cap)}
        print(f"  P-cycle OOD: rho={rho_p:.4f}, p={p_p:.2e}, n={len(df_p_cap)}")

    # --- Compare with original random-split result ---
    original_rho = 0.5009  # from ood_evaluation_results.json cap_correlation_P.rho

    results = {
        "experiment": "Strict Temporal OOD vs Random Cross-Cycle Split",
        "training_cohort": "J-cycle only (2017-2018)",
        "training_n": len(df_train),
        "val_n": len(df_val),
        "test_n_j_internal": len(df_test),
        "p_cycle_n": len(df_p),
        "stopped_at_epoch": stopped_epoch,
        "j_internal_test": j_internal_results,
        "p_cycle_temporal_ood": p_ood_results,
        "original_random_split_rho_p": original_rho,
        "verdict": (
            "TEMPORAL OOD HOLDS — rho within 0.05 of random-split result"
            if p_ood_results and abs(p_ood_results.get("rho", 0) - original_rho) <= 0.05
            else "TEMPORAL OOD DROPS — rho more than 0.05 below random-split result"
        )
    }

    out_path = os.path.join(RESULTS_DIR, "temporal_ood_comparison.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*65)
    print("TEMPORAL SPLIT EXPERIMENT RESULTS")
    print("="*65)
    print(f"  J-only training n:           {len(df_train)}")
    print(f"  J internal test rho (CAP):   {j_internal_results.get('rho', 'N/A')}")
    print(f"  P-cycle TRUE OOD rho (CAP):  {p_ood_results.get('rho', 'N/A')}")
    print(f"  Original random-split rho:   {original_rho}")
    print(f"  Verdict: {results['verdict']}")
    print(f"  Results saved -> {out_path}")
    print("="*65)

    return results


if __name__ == "__main__":
    train_temporal()
