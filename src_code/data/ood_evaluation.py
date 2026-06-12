"""
OOD Temporal Evaluation -- LMSIS Project
=========================================
Evaluates the trained DA-SS-iVAE model on NHANES 2019-March 2020 (P-cycle)
as a temporal out-of-distribution (OOD) test.

Scientific claim being tested:
  "A model trained on NHANES 2017-2018 generalises to NHANES 2019-March 2020
   without retraining, demonstrating temporal robustness of the learned
   latent metabolic phenotypes."

Key outputs:
  1. CAP correlation (rho) on P-cycle -- does it hold near 0.607?
  2. Latent space quadrant distribution -- is Q0 still dominant?
  3. NHA subgroup n -- does combined cohort fix the n=11 problem?
  4. HOMA-IR threshold decision -- can we promote [2.3, 2.7] to primary result?
  5. Reconstruction MSE on P-cycle -- OOD distribution shift diagnostic.
  6. Conformal coverage on P-cycle -- does the J-calibrated guarantee transfer?

Run AFTER download_nhanes.py has completed all P-cycle files.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import torch

# -- Path setup --------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

from src_code.data.nhanes_multi_cycle import (
    load_data, get_ood_cohort_stats, validate_cycle_schema, assert_weights_valid
)
from src_code.data.preprocess import preprocess_data, derive_features, FEATURE_COLS
from model_registry import registry

RESULTS_DIR = os.path.join(ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def encode_cohort(df: pd.DataFrame) -> tuple:
    """
    Run the trained model's encoder on a cohort DataFrame.
    Uses the FROZEN J-cycle scaler and u_encoder. No retraining.

    Returns:
        z1: np.array, z2: np.array, recon_mse: float, ir_labels: np.array
    """
    registry.load_models()

    df_derived = derive_features(df)
    X_raw = df_derived[FEATURE_COLS]
    X_scaled = registry.scaler.transform(X_raw)

    age = df_derived[["age"]].values
    sex = (df_derived["sex"] == 2).astype(float).values.reshape(-1, 1)
    ancestry = df_derived[["ancestry_proxy"]]
    anc_encoded = registry.u_encoder.transform(ancestry)
    u_encoded = np.hstack([age / 100.0, sex, anc_encoded[:, 1:]])

    x_t = torch.tensor(X_scaled, dtype=torch.float32)
    u_t = torch.tensor(u_encoded, dtype=torch.float32)

    registry.model.eval()
    with torch.no_grad():
        mu_q, _ = registry.model.encoder(x_t, u_t)
        x_recon = registry.model.decoder(mu_q)   # Decoder returns single tensor, not tuple

    z1 = mu_q[:, 0].numpy()
    z2 = mu_q[:, 1].numpy()
    recon_mse = float(torch.mean((x_recon - x_t) ** 2).item())
    ir_labels = df_derived["ir_label"].values if "ir_label" in df_derived.columns else None

    return z1, z2, recon_mse, ir_labels


def quadrant_label(z1: float, z2: float,
                   tau1: float = 0.0, tau2: float = 0.0) -> int:
    """Q0=healthy, Q1=IR-only, Q2=steatosis-only, Q3=dual-burden."""
    if z1 < tau1 and z2 < tau2:  return 0
    if z1 >= tau1 and z2 < tau2: return 1
    if z1 < tau1 and z2 >= tau2: return 2
    return 3


def check_conformal_coverage_ood(z_p: np.ndarray, ir_labels_p: np.ndarray,
                                  conformal_surface) -> dict:
    """
    Compute empirical conformal coverage on P-cycle participants using the
    J-cycle calibrated conformal surface (no recalibration).

    This tests whether the coverage guarantee (target: 0.90) transfers
    out-of-distribution to the P-cycle population.

    Target interpretation:
      >= 0.85: Coverage transfers. Conformal guarantee generalises OOD.
      0.80-0.85: Marginal. Note in dissertation, do not promote as a guarantee.
      < 0.80: Coverage gap. Calibration set must include P-cycle before
              clinical deployment on this population.
    """
    if ir_labels_p is None or np.isnan(ir_labels_p).any():
        return {"error": "ir_labels not available for P-cycle"}

    try:
        z_tensor = torch.tensor(z_p, dtype=torch.float32)
        _, pred_sets = conformal_surface.predict(z_p, alpha=0.10)

        covered = []
        for i, label in enumerate(ir_labels_p.astype(int)):
            if label in [0, 1] and label < pred_sets.shape[1]:
                covered.append(bool(pred_sets[i, label]))

        if not covered:
            return {"error": "No valid labels for coverage check"}

        emp_coverage = float(np.mean(covered))
        return {
            "empirical_coverage": round(emp_coverage, 4),
            "nominal_coverage": 0.90,
            "coverage_gap": round(emp_coverage - 0.90, 4),
            "n_evaluated": len(covered),
            "verdict": (
                "TRANSFERS (>= 0.85)" if emp_coverage >= 0.85
                else "MARGINAL (0.80-0.85)" if emp_coverage >= 0.80
                else "GAP (< 0.80) -- recalibrate before clinical use"
            )
        }
    except Exception as e:
        return {"error": str(e)}


def run_ood_evaluation():
    print("=" * 65)
    print("LMSIS Temporal OOD Evaluation -- NHANES 2019-March 2020 (P)")
    print("=" * 65)

    data_dir = os.path.join(ROOT, "src_code", "data")

    # -- [1] Load both cohorts ------------------------------------------------
    print("\n[1/7] Loading J-cycle (2017-2018, training cohort)...")
    df_j = load_data(cycle="J", data_dir=data_dir)
    if df_j is None or len(df_j) == 0:
        print("  [ERROR] J-cycle data unavailable. Abort.")
        return

    print("\n[2/7] Loading P-cycle (2019-March 2020, OOD cohort)...")
    df_p = load_data(cycle="P", data_dir=data_dir)
    if df_p is None or len(df_p) == 0:
        print("  [ERROR] P-cycle data unavailable. Run download_nhanes.py first.")
        return

    # -- [2] Cohort comparison stats ------------------------------------------
    print("\n[3/7] Computing cohort comparison statistics...")
    ood_stats = get_ood_cohort_stats(df_j, df_p)

    print(f"\n  n (J, training):          {ood_stats['n_J']}")
    print(f"  n (P, OOD):               {ood_stats['n_P']}")
    print(f"  n (combined):             {ood_stats['n_combined']}")
    print(f"  NHA n (J):                {ood_stats.get('n_NHA_J', 'N/A')}")
    print(f"  NHA n (P):                {ood_stats.get('n_NHA_P', 'N/A')}")
    print(f"  NHA n (combined):         {ood_stats.get('n_NHA_combined', 'N/A')}")
    print(f"  CAP available (J):        {ood_stats['cap_J']}")
    print(f"  CAP available (P):        {ood_stats['cap_P']}")

    # -- [3] NHA threshold decision gate --------------------------------------
    # Check combined NHA in HOMA-IR [2.3, 2.7] band
    nha_code = 4
    df_combined = pd.concat([df_j, df_p], ignore_index=True)
    df_combined_derived = derive_features(df_combined)
    df_combined_derived["homa_ir"] = (
        df_combined_derived["fasting_insulin_uU_mL"] *
        df_combined_derived["fasting_glucose_mg_dL"]
    ) / 405.0

    nha_combined = df_combined_derived[df_combined_derived["ancestry_proxy"] == nha_code]
    nha_homa_band = nha_combined[
        (nha_combined["homa_ir"] >= 2.3) & (nha_combined["homa_ir"] <= 2.7)
    ]
    n_nha_band = len(nha_homa_band)

    print(f"\n  NHA in HOMA-IR [2.3, 2.7] band (combined): {n_nha_band}")
    if n_nha_band >= 40:
        threshold_verdict = "PROMOTE: n >= 40 -- promote threshold analysis to primary result"
    elif n_nha_band >= 30:
        threshold_verdict = "BORDERLINE: n in [30, 40) -- keep supplementary, note in text"
    else:
        threshold_verdict = "DEMOTE: n < 30 -- keep in limitations, do not promote"
    print(f"  Decision: {threshold_verdict}")

    # -- [4] Encode J-cycle (baseline sanity check) ---------------------------
    print("\n[4/7] Encoding J-cycle (sanity check on frozen baseline)...")
    registry.load_models()
    try:
        z1_j, z2_j, mse_j, ir_j = encode_cohort(df_j)
        print(f"  J-cycle: n={len(z1_j)}, z1 mean={z1_j.mean():.4f}, "
              f"z2 mean={z2_j.mean():.4f}, recon_mse={mse_j:.5f}")
    except Exception as e:
        print(f"  [ERROR] J-cycle encoding failed: {e}")
        z1_j = z2_j = ir_j = None
        mse_j = None

    # -- [5] Encode P-cycle (OOD inference, no retraining) --------------------
    print("\n[5/7] Encoding P-cycle (OOD inference -- frozen J model)...")
    try:
        z1_p, z2_p, mse_p, ir_p = encode_cohort(df_p)
        print(f"  P-cycle: n={len(z1_p)}, z1 mean={z1_p.mean():.4f}, "
              f"z2 mean={z2_p.mean():.4f}, recon_mse={mse_p:.5f}")

        if mse_j is not None and mse_p > mse_j * 2.0:
            print(f"  [WARN] OOD MSE ({mse_p:.5f}) > 2x J MSE ({mse_j:.5f}). "
                  "Investigate potential distribution shift before promoting P results.")
        elif mse_j is not None:
            print(f"  OOD MSE within acceptable range (< 2x J MSE). Good generalisation.")
    except Exception as e:
        print(f"  [ERROR] P-cycle encoding failed: {e}")
        return

    # -- [6] CAP correlation on P-cycle ---------------------------------------
    print("\n[6/7] CAP correlation analysis...")
    results_data = {
        "cohort_stats": ood_stats,
        "nha_homa_band": {"n": n_nha_band, "verdict": threshold_verdict},
        "recon_mse": {
            "J_cycle": float(mse_j) if mse_j is not None else None,
            "P_cycle": float(mse_p),
        },
    }

    df_p_eval = df_p.copy().reset_index(drop=True)
    df_p_eval["z1"] = z1_p
    df_p_eval["z2"] = z2_p

    df_p_cap = df_p_eval.dropna(subset=["cap_score"])
    if len(df_p_cap) >= 30:
        rho_p, pval_p = stats.spearmanr(df_p_cap["z2"], df_p_cap["cap_score"])
        print(f"  z2 vs CAP (P-cycle OOD): rho={rho_p:.3f}, p={pval_p:.2e}, "
              f"n={len(df_p_cap)}")
        results_data["cap_correlation_P"] = {
            "rho": float(rho_p), "p": float(pval_p), "n": len(df_p_cap)
        }

        if z1_j is not None:
            df_j_eval = df_j.copy().reset_index(drop=True)
            df_j_eval["z2"] = z2_j
            df_j_cap = df_j_eval.dropna(subset=["cap_score"])
            if len(df_j_cap) >= 10:
                rho_j, pval_j = stats.spearmanr(df_j_cap["z2"], df_j_cap["cap_score"])
                print(f"  z2 vs CAP (J-cycle ref): rho={rho_j:.3f}, p={pval_j:.2e}, "
                      f"n={len(df_j_cap)}")
                results_data["cap_correlation_J"] = {
                    "rho": float(rho_j), "p": float(pval_j), "n": len(df_j_cap)
                }
    else:
        print(f"  Insufficient CAP data in P-cycle (n={len(df_p_cap)}). "
              "Check P_LUX.xpt download.")

    # Quadrant distribution on P-cycle
    tau1 = getattr(registry.conformal_surface, "z1_threshold", 0.0)
    tau2 = getattr(registry.conformal_surface, "z2_threshold", 0.0)
    quads_p = [quadrant_label(z1, z2, tau1, tau2)
               for z1, z2 in zip(z1_p, z2_p)]
    quad_counts_p = {q: quads_p.count(q) for q in range(4)}
    quad_labels   = {0: "Q0 Healthy", 1: "Q1 IR-only",
                     2: "Q2 Steatosis", 3: "Q3 Dual-Burden"}
    print(f"\n  P-cycle quadrant distribution:")
    for q, label in quad_labels.items():
        pct = 100 * quad_counts_p[q] / len(quads_p)
        print(f"    {label}: n={quad_counts_p[q]} ({pct:.1f}%)")
    results_data["quadrant_distribution_P"] = {
        str(q): {"n": quad_counts_p[q],
                 "pct": round(100 * quad_counts_p[q] / len(quads_p), 2)}
        for q in range(4)
    }

    # -- [7] Conformal coverage on P-cycle ------------------------------------
    print("\n[7/7] Conformal coverage check (J-calibrated quantiles on P-cycle)...")
    ir_p_clean = ir_p
    if ir_p is not None and not np.isnan(ir_p).any():
        z_p_array = np.column_stack([z1_p, z2_p])
        conf_result = check_conformal_coverage_ood(
            z_p_array, ir_p_clean, registry.conformal_surface
        )
        results_data["conformal_coverage_OOD"] = conf_result
        if "error" not in conf_result:
            print(f"  P-cycle empirical coverage: {conf_result['empirical_coverage']:.3f} "
                  f"(target >= 0.85)")
            print(f"  Verdict: {conf_result['verdict']}")
        else:
            print(f"  [warn] {conf_result['error']}")
    else:
        print("  [warn] ir_labels not available -- skipping coverage check")

    # -- Save results ---------------------------------------------------------
    out_path = os.path.join(RESULTS_DIR, "ood_evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump(results_data, f, indent=2, default=str)
    print(f"\n  Results saved -> {out_path}")

    # -- Dissertation-ready summary -------------------------------------------
    print("\n" + "=" * 65)
    print("DISSERTATION OOD SECTION -- NUMBERS TO USE")
    print("=" * 65)
    print(f"  Training cohort (J, 2017-2018):        n = {ood_stats['n_J']}")
    print(f"  OOD cohort (P, 2019-Mar2020):          n = {ood_stats['n_P']}")
    print(f"  Combined for subgroup analysis:         n = {ood_stats['n_combined']}")
    print(f"  NHA (ancestry=4) combined:              n = {ood_stats.get('n_NHA_combined', 'N/A')}")
    if "cap_correlation_J" in results_data:
        print(f"  CAP rho (J, training):    {results_data['cap_correlation_J']['rho']:.3f}")
    if "cap_correlation_P" in results_data:
        print(f"  CAP rho (P, OOD):         {results_data['cap_correlation_P']['rho']:.3f}")
    print(f"  Recon MSE (J training):   {mse_j:.5f}")
    print(f"  Recon MSE (P OOD):        {mse_p:.5f}")
    print(f"  NHA threshold verdict:    {threshold_verdict.split(':')[0]}")
    if "conformal_coverage_OOD" in results_data and "error" not in results_data["conformal_coverage_OOD"]:
        cov = results_data["conformal_coverage_OOD"]
        print(f"  Conformal coverage OOD:   {cov['empirical_coverage']:.3f} -- {cov['verdict']}")
    print("=" * 65)

    # -- Training Z for PySR sampling (save for Phase 3) ---------------------
    # Save the J-cycle latent coordinates so PySR can sample from the
    # training distribution rather than a uniform grid.
    # See Phase 3 notes: sample from training Z + small Gaussian noise,
    # not from a uniform square -- avoids extrapolating to biologically
    # implausible latent regions.
    if z1_j is not None:
        z_train_path = os.path.join(RESULTS_DIR, "training_z_coords.npy")
        np.save(z_train_path, np.column_stack([z1_j, z2_j]))
        print(f"\n  Training Z saved for PySR Phase 3 -> {z_train_path}")

    return results_data


if __name__ == "__main__":
    run_ood_evaluation()
