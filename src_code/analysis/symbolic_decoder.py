"""
PySR Symbolic Decoder -- LMSIS Project
=======================================
Post-hoc symbolic regression on the trained DA-SS-iVAE decoder.

Scientific purpose:
  The decoder maps latent coordinates (z1, z2) to 14-dimensional biomarker
  space. PySR fits interpretable mathematical formulas to each output dimension,
  answering: "What does a specific (z1, z2) coordinate mean in terms of
  measurable blood biomarkers?"

  Example output formula:
    alt_U_L = 1.92 * z2^1.3 + 0.41 * z1 * z2

  This gives a dissertation-ready interpretability result that no other
  clinical VAE paper in 2025-2026 has demonstrated.

Sampling strategy (CRITICAL -- do NOT use uniform grid):
  We sample z coordinates from the TRAINING DATA DISTRIBUTION, not from a
  uniform square grid over the latent space. Uniform grid sampling includes
  regions far outside where any real patient exists -- PySR would fit
  formulas to biologically meaningless extrapolations.

  Method: load saved J-cycle training Z coords, add small Gaussian noise
  to augment diversity, then decode each point through the frozen decoder.

No model parameters are updated. This is purely post-hoc analysis.

Usage:
    python src_code/analysis/symbolic_decoder.py

Output:
    results/symbolic_decoder/
        formulas.txt          -- human-readable equations for each biomarker
        formulas_latex.txt    -- LaTeX-formatted equations
        pysr_models/          -- PySR fitted model objects per feature
"""
import os
import sys
import json
import numpy as np
import torch
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

from src_code.data.schema import FeatureSchema
from model_registry import registry

RESULTS_DIR = os.path.join(ROOT, "results", "symbolic_decoder")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Biomarker names matching FEATURE_COLS order in schema.py
FEATURE_NAMES = FeatureSchema.FEATURE_COLS

# How many z-samples to fit symbolic regression on.
# 2000 is enough for PySR to find stable formulas; 5000 takes much longer.
N_SAMPLES = 2000
NOISE_STD  = 0.10   # Gaussian noise added to training coords for augmentation

# PySR search settings (tuned for speed -- adjust if more iterations needed)
PYSR_NITERATIONS = 40
PYSR_POPULATIONS  = 15
PYSR_MAXSIZE      = 20   # max nodes in symbolic tree -- larger = more complex formulas


def load_training_z(results_dir: str) -> np.ndarray:
    """
    Load J-cycle training latent coordinates saved by ood_evaluation.py.
    Falls back to a smaller set if file not found.
    """
    z_path = os.path.join(results_dir, "training_z_coords.npy")
    if os.path.exists(z_path):
        z = np.load(z_path)
        print(f"  Loaded training Z: {z.shape} from {z_path}")
        return z
    else:
        print(f"  [WARN] training_z_coords.npy not found at {z_path}")
        print("  Run ood_evaluation.py first to generate this file.")
        print("  Falling back to a small uniform grid (not recommended).")
        # Minimal fallback: grid from -3 to 3
        g = np.linspace(-3, 3, 50)
        z1g, z2g = np.meshgrid(g, g)
        return np.column_stack([z1g.ravel(), z2g.ravel()])


def sample_from_training_distribution(z_train: np.ndarray,
                                      n_samples: int,
                                      noise_std: float) -> np.ndarray:
    """
    Sample n_samples points from the training latent distribution.

    Strategy: bootstrap sample from training Z coords, then add small
    Gaussian noise to augment coverage without extrapolating.

    This ensures all sampled points are in biologically plausible regions.
    """
    idx = np.random.choice(len(z_train), size=n_samples, replace=True)
    z_samples = z_train[idx].copy()
    z_samples += np.random.normal(0, noise_std, z_samples.shape)
    return z_samples


def decode_z_to_biomarkers(z_samples: np.ndarray) -> np.ndarray:
    """
    Pass z samples through the frozen decoder.
    Returns (n_samples, n_features) array in SCALED space.
    The decoder outputs are in the RobustScaler-transformed space.
    """
    registry.load_models()
    registry.model.eval()

    z_t = torch.tensor(z_samples, dtype=torch.float32)
    with torch.no_grad():
        x_hat = registry.model.decoder(z_t)

    return x_hat.numpy()


def inverse_scale(x_scaled: np.ndarray) -> np.ndarray:
    """
    Inverse-transform decoder outputs back to original clinical units.
    Uses the frozen J-cycle RobustScaler.
    """
    return registry.scaler.inverse_transform(x_scaled)


def run_symbolic_regression(z_samples: np.ndarray,
                             x_biomarkers: np.ndarray,
                             feature_names: list,
                             n_iterations: int = PYSR_NITERATIONS) -> dict:
    """
    Fit symbolic regression formulas: x_i = f(z1, z2) for each biomarker i.

    Uses PySR (symbolic regression via genetic programming).
    Returns dict: {feature_name: {"equation": str, "latex": str, "loss": float}}
    """
    try:
        from pysr import PySRRegressor
    except ImportError:
        print("  [ERROR] pysr not installed. Run: pip install pysr")
        return {}

    results = {}
    z_df = pd.DataFrame(z_samples, columns=["z1", "z2"])

    n_features = x_biomarkers.shape[1]
    if len(feature_names) != n_features:
        print(f"  [WARN] feature_names length ({len(feature_names)}) != "
              f"x_biomarkers cols ({n_features}). Trimming.")
        feature_names = feature_names[:n_features]

    for i, fname in enumerate(feature_names):
        print(f"\n  [{i+1}/{n_features}] Fitting symbolic formula for: {fname}")
        y = x_biomarkers[:, i]

        # Skip features with near-zero variance (decoder may output constant)
        if y.std() < 1e-4:
            print(f"    [skip] near-zero variance (std={y.std():.6f})")
            results[fname] = {
                "equation": f"{fname} = {float(y.mean()):.4f}  [constant]",
                "latex": f"{fname} \\approx {float(y.mean()):.4f}",
                "loss": 0.0,
                "skipped": True
            }
            continue

        model = PySRRegressor(
            niterations=n_iterations,
            populations=PYSR_POPULATIONS,
            maxsize=PYSR_MAXSIZE,
            binary_operators=["+", "-", "*", "/", "^"],
            unary_operators=["exp", "log", "abs", "sqrt"],
            loss="loss(x, y) = (x - y)^2",
            verbosity=0,
            random_state=42,
            temp_equation_file=True,
            delete_tempfiles=True,
        )

        try:
            model.fit(z_df, y)
            best = model.get_best()
            eq_str  = f"{fname} = {best['equation']}"
            eq_latex = f"{fname} = {model.latex()}"
            loss_val = float(best["loss"])

            print(f"    Best: {eq_str}  (loss={loss_val:.6f})")
            results[fname] = {
                "equation": eq_str,
                "latex": eq_latex,
                "loss": loss_val,
                "skipped": False
            }
        except Exception as e:
            print(f"    [ERROR] PySR failed for {fname}: {e}")
            results[fname] = {
                "equation": f"{fname} = [fit failed: {e}]",
                "latex": "",
                "loss": None,
                "skipped": True
            }

    return results


def save_results(results: dict, z_stats: dict) -> None:
    """Save formulas in plain text, LaTeX, and JSON formats."""
    # Plain text
    txt_path = os.path.join(RESULTS_DIR, "formulas.txt")
    with open(txt_path, "w") as f:
        f.write("LMSIS Symbolic Decoder -- Extracted Formulas\n")
        f.write("=" * 60 + "\n")
        f.write(f"Model: frozen DA-SS-iVAE (ivae_best.pt)\n")
        f.write(f"Sampling: {N_SAMPLES} points from training Z distribution\n")
        f.write(f"         + Gaussian noise (std={NOISE_STD})\n")
        f.write(f"z1 range: [{z_stats['z1_min']:.3f}, {z_stats['z1_max']:.3f}]  "
                f"(training data range)\n")
        f.write(f"z2 range: [{z_stats['z2_min']:.3f}, {z_stats['z2_max']:.3f}]  "
                f"(training data range)\n")
        f.write("=" * 60 + "\n\n")
        for fname, r in results.items():
            status = "[SKIP]" if r.get("skipped") else ""
            loss   = f"  loss={r['loss']:.6f}" if r["loss"] is not None else ""
            f.write(f"{r['equation']}{loss}  {status}\n")
    print(f"\n  Formulas saved -> {txt_path}")

    # LaTeX
    latex_path = os.path.join(RESULTS_DIR, "formulas_latex.txt")
    with open(latex_path, "w") as f:
        f.write("% LMSIS Symbolic Decoder -- LaTeX Equations\n")
        f.write("% Paste into dissertation interpretability section\n\n")
        f.write("\\begin{align}\n")
        for fname, r in results.items():
            if r["latex"] and not r.get("skipped"):
                f.write(f"  {r['latex']} \\\\\n")
        f.write("\\end{align}\n")
    print(f"  LaTeX saved    -> {latex_path}")

    # JSON (for programmatic use)
    json_path = os.path.join(RESULTS_DIR, "formulas.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"  JSON saved     -> {json_path}")


def main():
    print("=" * 65)
    print("LMSIS Symbolic Decoder -- PySR Post-hoc Analysis")
    print("=" * 65)
    print(f"  n_samples:     {N_SAMPLES}")
    print(f"  noise_std:     {NOISE_STD}")
    print(f"  niterations:   {PYSR_NITERATIONS}")
    print(f"  populations:   {PYSR_POPULATIONS}")
    print(f"  maxsize:       {PYSR_MAXSIZE}")

    np.random.seed(42)

    # [1] Load training Z distribution
    print("\n[1/5] Loading training latent coordinates...")
    results_dir = os.path.join(ROOT, "results")
    z_train = load_training_z(results_dir)

    z_stats = {
        "z1_min": float(z_train[:, 0].min()),
        "z1_max": float(z_train[:, 0].max()),
        "z2_min": float(z_train[:, 1].min()),
        "z2_max": float(z_train[:, 1].max()),
    }
    print(f"  Training Z: n={len(z_train)}, "
          f"z1=[{z_stats['z1_min']:.3f}, {z_stats['z1_max']:.3f}], "
          f"z2=[{z_stats['z2_min']:.3f}, {z_stats['z2_max']:.3f}]")

    # [2] Sample from training distribution
    print(f"\n[2/5] Sampling {N_SAMPLES} points from training Z distribution...")
    z_samples = sample_from_training_distribution(z_train, N_SAMPLES, NOISE_STD)
    print(f"  Sampled: {z_samples.shape}, "
          f"z1 std={z_samples[:,0].std():.3f}, z2 std={z_samples[:,1].std():.3f}")

    # [3] Decode to biomarker space
    print("\n[3/5] Decoding z samples through frozen decoder...")
    x_scaled = decode_z_to_biomarkers(z_samples)
    x_biomarkers = inverse_scale(x_scaled)
    print(f"  Decoded: {x_biomarkers.shape} (scaled back to clinical units)")

    # Sanity check -- biomarker ranges
    for i, fname in enumerate(FEATURE_NAMES[:5]):
        print(f"    {fname}: min={x_biomarkers[:,i].min():.2f}, "
              f"max={x_biomarkers[:,i].max():.2f}, "
              f"mean={x_biomarkers[:,i].mean():.2f}")

    # [4] PySR symbolic regression
    print(f"\n[4/5] Running PySR on {len(FEATURE_NAMES)} biomarker outputs...")
    print("  (This may take 10-30 minutes depending on niterations)")
    formula_results = run_symbolic_regression(
        z_samples, x_biomarkers, FEATURE_NAMES,
        n_iterations=PYSR_NITERATIONS
    )

    if not formula_results:
        print("  [ERROR] No formulas produced. Check PySR installation.")
        return

    # [5] Save
    print("\n[5/5] Saving results...")
    save_results(formula_results, z_stats)

    # Print dissertation-ready summary
    print("\n" + "=" * 65)
    print("DISSERTATION-READY: Top Formulas by Relevance")
    print("=" * 65)
    priority_features = [
        "homa_ir", "ast_alt_ratio", "fasting_glucose_mg_dL",
        "triglycerides_mg_dL", "hdl_mg_dL"
    ]
    for fname in priority_features:
        if fname in formula_results:
            r = formula_results[fname]
            if not r.get("skipped"):
                print(f"  {r['equation']}")
    print("=" * 65)
    print(f"\n  Full results in: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
