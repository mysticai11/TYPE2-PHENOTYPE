"""
temporal_robustness_check.py
============================
Four-check robustness audit for the temporal OOD result (ρ=0.5793).

Checks:
  1. SEQN-level zero-overlap assertion (no participant appears in both J-train and P-eval)
  2. Multi-seed stability: 5 random seeds for J-cycle 70/15/15 split
     → reports mean and SD of P-cycle ρ across seeds
  3. CAP + HOMA-IR distribution comparison (J-train vs P-cycle)
     → checks if range expansion in P-cycle artificially inflates ρ
  4. Verdict: are both the direction and magnitude of ρ=0.5793 trustworthy?

Output: results/temporal_robustness.json
"""

import os, sys, json
import torch
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src_code.data.nhanes_multi_cycle import load_data as load_cycle
from src_code.data.preprocess import preprocess_data, derive_features, FEATURE_COLS
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.utils.seeds import set_all_seeds

RESULTS_DIR = os.path.join(ROOT, "results")
DATA_DIR    = os.path.join(ROOT, "src_code", "data")

SEEDS   = [42, 7, 123, 999, 2024]
PARAMS  = {"beta": 4.0, "lam1": 0.8, "lam2": 1.2, "lam_ortho": 0.1}
LR      = 1e-3
PATIENCE = 20
MAX_EPOCHS = 150


# ── helpers ────────────────────────────────────────────────────────────────────

def train_and_eval(df_train, df_val, df_p, seed):
    """Train on df_train, validate on df_val, evaluate frozen model on df_p."""
    set_all_seeds(seed, seed * 29)

    X_tr, u_tr, h_tr, m_tr, _, _, scaler, u_enc = preprocess_data(df_train, is_train=True)
    X_va, u_va, h_va, m_va, _, _, _, _ = preprocess_data(df_val,   scaler=scaler, u_encoder=u_enc, is_train=False)

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
            model.loss(x_b, u_b, h_b, m_b,
                       *model(x_b, u_b)[:6],
                       model(x_b, u_b)[6])[0].item() * len(x_b)
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

    # Encode P-cycle with frozen scaler + frozen model
    def encode(df_input):
        df_d = derive_features(df_input)
        X = scaler.transform(df_d[FEATURE_COLS])
        age = df_d[["age"]].values
        sex = (df_d["sex"] == 2).astype(float).values.reshape(-1, 1)
        anc = u_enc.transform(df_d[["ancestry_proxy"]])
        u   = np.hstack([age / 100.0, sex, anc[:, 1:]])
        model.eval()
        with torch.no_grad():
            mu_q, _ = model.encoder(torch.tensor(X, dtype=torch.float32),
                                    torch.tensor(u, dtype=torch.float32))
        return mu_q[:, 1].numpy()   # z2 = steatosis axis

    z2_p = encode(df_p)
    df_p_r = df_p.copy().reset_index(drop=True)
    df_p_cap = df_p_r.dropna(subset=["cap_score"])
    idx = df_p_cap.index.tolist()
    rho, pval = stats.spearmanr(z2_p[idx], df_p_cap["cap_score"].values)
    return float(rho), float(pval), len(idx), stop_epoch


# ── main ────────────────────────────────────────────────────────────────────────

def run_robustness_checks():
    results = {}

    # ── Load data once ─────────────────────────────────────────────────────────
    print("Loading J-cycle and P-cycle...")
    df_j = load_cycle(cycle="J", data_dir=DATA_DIR)
    df_p = load_cycle(cycle="P", data_dir=DATA_DIR)
    assert df_j is not None and df_p is not None, "Data load failed"
    print(f"  J: n={len(df_j)},  P: n={len(df_p)}")

    # ── CHECK 2: SEQN-level zero-overlap assertion ─────────────────────────────
    print("\n[CHECK 2] SEQN-level participant overlap...")
    raw_j_path = os.path.join(DATA_DIR, "raw_nhanes_j.csv")
    raw_p_path = os.path.join(DATA_DIR, "raw_nhanes_p.csv")

    seqn_overlap_result = {}
    if os.path.exists(raw_j_path) and os.path.exists(raw_p_path):
        raw_j = pd.read_csv(raw_j_path, usecols=["SEQN"], low_memory=False)
        raw_p = pd.read_csv(raw_p_path, usecols=["SEQN"], low_memory=False)
        j_seqns = set(raw_j["SEQN"].dropna().astype(int).tolist())
        p_seqns = set(raw_p["SEQN"].dropna().astype(int).tolist())
        overlap  = j_seqns & p_seqns
        seqn_overlap_result = {
            "j_unique_seqns": len(j_seqns),
            "p_unique_seqns": len(p_seqns),
            "overlap_count": len(overlap),
            "verdict": "PASS — zero participant overlap" if len(overlap) == 0
                       else f"FAIL — {len(overlap)} SEQNs appear in both cycles"
        }
        print(f"  {seqn_overlap_result['verdict']}")
        assert len(overlap) == 0, seqn_overlap_result["verdict"]
    else:
        seqn_overlap_result = {"verdict": "SKIP — per-cycle raw CSVs not found"}
        print("  SKIP — raw_nhanes_j.csv / raw_nhanes_p.csv not found")

    results["check2_seqn_overlap"] = seqn_overlap_result

    # ── CHECK 3: Distribution comparison J-train vs P ─────────────────────────
    print("\n[CHECK 3] Biomarker distribution comparison (J vs P)...")
    df_j_d = derive_features(df_j)
    df_p_d = derive_features(df_p)

    # HOMA-IR
    df_j_d["homa_ir"] = (df_j_d["fasting_insulin_uU_mL"] * df_j_d["fasting_glucose_mg_dL"]) / 405.0
    df_p_d["homa_ir"] = (df_p_d["fasting_insulin_uU_mL"] * df_p_d["fasting_glucose_mg_dL"]) / 405.0

    def dist_stats(series, label):
        s = series.dropna()
        return {
            "label": label, "n": len(s),
            "mean": round(float(s.mean()), 4),
            "sd":   round(float(s.std()),  4),
            "iqr":  round(float(s.quantile(0.75) - s.quantile(0.25)), 4),
            "min":  round(float(s.min()), 4),
            "max":  round(float(s.max()), 4),
        }

    dist_check = {
        "cap_J":    dist_stats(df_j["cap_score"].dropna(),  "J-cycle CAP (dB/m)"),
        "cap_P":    dist_stats(df_p["cap_score"].dropna(),  "P-cycle CAP (dB/m)"),
        "homa_J":   dist_stats(df_j_d["homa_ir"], "J-cycle HOMA-IR"),
        "homa_P":   dist_stats(df_p_d["homa_ir"], "P-cycle HOMA-IR"),
    }
    cap_iqr_ratio = dist_check["cap_P"]["iqr"] / max(dist_check["cap_J"]["iqr"], 1e-6)
    dist_check["cap_iqr_ratio_P_over_J"] = round(cap_iqr_ratio, 4)
    dist_check["range_expansion_warning"] = (
        "WARN — P-cycle CAP IQR > 20% wider than J. Wider range may inflate Spearman rho."
        if cap_iqr_ratio > 1.20 else
        "OK — CAP IQR similar between cycles (<20% difference)."
    )
    for k in ["cap_J", "cap_P", "homa_J", "homa_P"]:
        d = dist_check[k]
        print(f"  {d['label']}: n={d['n']}, mean={d['mean']}, sd={d['sd']}, IQR={d['iqr']}, range=[{d['min']}, {d['max']}]")
    print(f"  CAP IQR ratio (P/J): {cap_iqr_ratio:.4f}  -> {dist_check['range_expansion_warning']}")

    results["check3_distributions"] = dist_check

    # ── CHECK 1: Multi-seed stability ─────────────────────────────────────────
    print(f"\n[CHECK 1] Multi-seed stability ({len(SEEDS)} seeds)...")
    seed_results = []
    for seed in SEEDS:
        df_train, df_temp = train_test_split(df_j, test_size=0.30, random_state=seed)
        df_val, _         = train_test_split(df_temp, test_size=0.50, random_state=seed)
        rho, pval, n_cap, stop = train_and_eval(df_train, df_val, df_p, seed)
        entry = {"seed": seed, "train_n": len(df_train), "rho_p_cycle": round(rho, 4),
                 "p_value": pval, "n_cap": n_cap, "stopped_at_epoch": stop}
        seed_results.append(entry)
        print(f"  seed={seed}: rho={rho:.4f}  (n={n_cap}, stopped epoch {stop})")

    rhos = [r["rho_p_cycle"] for r in seed_results]
    mean_rho = round(float(np.mean(rhos)), 4)
    std_rho  = round(float(np.std(rhos)),  4)
    seed42_rho = next(r["rho_p_cycle"] for r in seed_results if r["seed"] == 42)

    stability_verdict = (
        "STABLE — SD < 0.03; single-seed result is representative."
        if std_rho < 0.03 else
        "UNSTABLE — SD >= 0.03; single-seed result is NOT representative; use mean."
        if std_rho < 0.07 else
        "HIGH VARIANCE — SD >= 0.07; treat all results with caution."
    )

    results["check1_multi_seed"] = {
        "seeds": seed_results,
        "mean_rho": mean_rho,
        "std_rho":  std_rho,
        "seed42_rho": seed42_rho,
        "original_random_split_rho": 0.5009,
        "verdict": stability_verdict,
    }

    print(f"\n  Multi-seed summary: mean rho = {mean_rho} +/- {std_rho}")
    print(f"  Stability verdict: {stability_verdict}")

    # ── CHECK 4: Verdict logic review ─────────────────────────────────────────
    results["check4_verdict_logic"] = {
        "original_script_bug": "Script used abs(rho - baseline) > 0.05 as threshold; fired for direction=UP as well as DOWN.",
        "corrected_logic": "Temporal OOD is confirmed if temporal_rho >= baseline_rho - 0.05 (one-sided tolerance).",
        "seed42_vs_baseline": f"seed42 rho={seed42_rho} vs baseline={0.5009}; delta={round(seed42_rho - 0.5009, 4)}",
        "mean_vs_baseline":   f"mean rho={mean_rho} vs baseline={0.5009}; delta={round(mean_rho - 0.5009, 4)}",
        "verdict": (
            "CONFIRMED — mean rho exceeds baseline by >0"
            if mean_rho > 0.5009 else
            "NEUTRAL — mean rho within ±0.05 of baseline"
            if abs(mean_rho - 0.5009) <= 0.05 else
            "DEGRADED — mean rho more than 0.05 below baseline"
        )
    }

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = os.path.join(RESULTS_DIR, "temporal_robustness.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*65)
    print("ROBUSTNESS AUDIT SUMMARY")
    print("="*65)
    print(f"  SEQN overlap:       {seqn_overlap_result['verdict']}")
    print(f"  CAP range:          {dist_check['range_expansion_warning']}")
    print(f"  Multi-seed rho:     {mean_rho} +/- {std_rho}  (seed42: {seed42_rho})")
    print(f"  Stability:          {stability_verdict}")
    print(f"  Saved -> {out_path}")
    print("="*65)

    return results


if __name__ == "__main__":
    run_robustness_checks()
