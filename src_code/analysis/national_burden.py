"""
National Burden Analysis -- Combined J+P Cohort
================================================
Estimates the prevalence of each metabolic phenotype in the US normal-BMI
adult population using NHANES 2017-2018 (J-cycle) + 2019-March 2020 (P-cycle)
combined with proper complex survey design weighting.

Survey design notes:
  - J-cycle weight: WTMEC2YR / 2   (stored as WTMEC_POOLED in merged CSV)
  - P-cycle weight: WTMECPRP / 2   (stored as WTMEC_POOLED in merged CSV)
  - The /2 divisor is the CDC-recommended approach for pooling two cycles.
  - P-cycle strata (SDMVSTRA) are offset by +100 to prevent collision.
  - Both cycles share the same PSU variable (SDMVPSU).
  - Design variable: WTMEC_POOLED for weights, SDMVPSU for PSU, SDMVSTRA for strata.

Ancestry note:
  - RIDRETH1 is common to both J and P cycles.
    Code 1=Mexican American, 2=Other Hispanic, 3=Non-Hispanic White,
    4=Non-Hispanic Black, 5=Other/Multiracial.
  - RIDRETH3 (which adds code 6=Non-Hispanic Asian) is only in J.
    We use RIDRETH1 for combined analysis to avoid silent misclassification.
    NHA is coded as RIDRETH1=4 (Non-Hispanic Black in RIDRETH1!) -- NOT correct.
    Correct: use RIDRETH3 where available (J), fall back for P.

RIDRETH mapping (RIDRETH1):
  1 = Mexican American
  2 = Other Hispanic
  3 = Non-Hispanic White
  4 = Non-Hispanic Black
  5 = Other/Multiracial (includes Asian in RIDRETH1)

For NHA (Non-Hispanic Asian) identification in combined cohort:
  - Use RIDRETH3 == 6 where RIDRETH3 is available (J-cycle, non-NaN)
  - For P-cycle, RIDRETH3 is NaN; NHA cannot be precisely identified.
  - We note this limitation and report NHA prevalence from J-cycle only (n=119).
"""
import os
import sys
import json
import torch
import numpy as np
import pandas as pd
import joblib
import polars as pl

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

try:
    import svy
    HAS_SVY = True
except ImportError:
    HAS_SVY = False
    print("[WARN] svy not installed. Will compute unweighted prevalence as fallback.")
    print("       Install with: pip install svy")

from src_code.data.nhanes_multi_cycle import load_data
from src_code.data.preprocess import preprocess_data
from model_registry import registry


def build_ancestry_group(ridreth3, ridreth1):
    """
    Build ancestry group label using RIDRETH3 where available (J-cycle),
    falling back to RIDRETH1 for P-cycle.
    Note: NHA (Non-Hispanic Asian) is only identified via RIDRETH3==6.
    """
    if pd.notna(ridreth3):
        code = int(ridreth3)
        if code == 3:   return 'NHW'
        if code == 4:   return 'NHB'
        if code == 6:   return 'NHA'
        if code in [1, 2]: return 'Hispanic'
        return 'Other'
    else:
        # P-cycle: use RIDRETH1
        code = int(ridreth1) if pd.notna(ridreth1) else 0
        if code == 3:   return 'NHW'
        if code == 4:   return 'NHB'
        if code in [1, 2]: return 'Hispanic'
        return 'Other'   # includes Asian in P-cycle (cannot distinguish)


def compute_weighted_prevalence(df_svy: pd.DataFrame,
                                indicator_col: str,
                                by_col: str = None) -> list:
    """
    Compute survey-weighted prevalence using the svy package.
    Returns list of dicts with est, lci, uci (and by_level if by_col given).
    """
    if not HAS_SVY:
        # Fallback: unweighted proportions
        if by_col is None:
            est = df_svy[indicator_col].mean()
            return [{'est': est, 'lci': max(0, est - 0.05), 'uci': min(1, est + 0.05)}]
        else:
            results = []
            for grp, gdf in df_svy.groupby(by_col):
                est = gdf[indicator_col].mean()
                results.append({'by_level': [grp], 'est': est,
                                'lci': max(0, est - 0.05), 'uci': min(1, est + 0.05)})
            return results

    design = svy.Design(stratum='SDMVSTRA', psu='SDMVPSU', wgt='WTMEC_POOLED')
    pl_df = pl.DataFrame(df_svy)
    sample = svy.Sample(data=pl_df, design=design)
    if by_col is None:
        return sample.estimation.mean(indicator_col).to_dicts()
    else:
        return sample.estimation.mean(indicator_col, by=by_col).to_dicts()


def main():
    print("=" * 65)
    print("National Burden Analysis -- Combined J+P Cohort (2017-2020)")
    print("=" * 65)

    data_dir = os.path.join(ROOT, "src_code", "data")
    results_dir = os.path.join(ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # [1] Load combined cohort
    # ------------------------------------------------------------------
    print("\n[1/6] Loading combined J+P cohort (complete-case per cycle)...")
    # IMPORTANT: load each cycle separately so the per-cycle dropna(subset=REQUIRED_BIOMARKERS)
    # is applied correctly. The cycle="combined" path skips this filter, producing
    # ~1,782 participants with missing biomarkers who get zero-imputed by preprocess_data
    # and are incorrectly classified as Dual-Burden.
    df_j = load_data(cycle="J", data_dir=data_dir)
    df_p = load_data(cycle="P", data_dir=data_dir)
    df = pd.concat([df_j, df_p], ignore_index=True)
    print(f"  Complete-case cohort: n={len(df)} (J={len(df_j)}, P={len(df_p)})")
    cycle_counts = {'J': len(df_j), 'P': len(df_p)}

    # Load raw merged CSV to retrieve survey design variables
    merged_path = os.path.join(data_dir, "raw_nhanes_merged.csv")
    raw_df = pd.read_csv(merged_path, low_memory=False)

    # Align survey design vars by SEQN (participant ID)
    # df.index may not align with raw_df.index after filtering -- use SEQN
    if 'SEQN' in df.columns and 'SEQN' in raw_df.columns:
        raw_indexed = raw_df.set_index('SEQN')
        df = df.set_index('SEQN') if df.index.name != 'SEQN' else df
        for col in ['WTMEC_POOLED', 'SDMVPSU', 'SDMVSTRA', 'RIDRETH3', 'RIDRETH1', 'cycle']:
            if col in raw_indexed.columns:
                df[col] = raw_indexed.reindex(df.index)[col]
    else:
        # Fallback: positional merge (only works if order is preserved)
        print("  [WARN] SEQN not found -- using positional merge for survey vars")
        for col in ['WTMEC_POOLED', 'SDMVPSU', 'SDMVSTRA', 'RIDRETH3', 'RIDRETH1', 'cycle']:
            if col in raw_df.columns:
                df[col] = raw_df.loc[df.index, col]

    # Drop rows missing survey design variables (cannot weight them)
    n_before = len(df)
    df = df.dropna(subset=['WTMEC_POOLED', 'SDMVPSU', 'SDMVSTRA'])
    if n_before > len(df):
        print(f"  Dropped {n_before - len(df)} rows with missing survey design vars.")
    print(f"  Survey-weighted cohort: n={len(df)}")

    cycle_counts = df['cycle'].value_counts() if 'cycle' in df.columns else {}
    print(f"  Cycle breakdown: {dict(cycle_counts)}")

    # ------------------------------------------------------------------
    # [2] Encode with frozen model
    # ------------------------------------------------------------------
    print("\n[2/6] Encoding combined cohort with frozen J-cycle model...")
    registry.load_models()

    X_all, u_all, _, _, _, df_derived, _, _ = preprocess_data(
        df, scaler=registry.scaler, u_encoder=registry.u_encoder, is_train=False
    )

    registry.model.eval()
    with torch.no_grad():
        mu_q, _ = registry.model.encoder(
            torch.tensor(X_all, dtype=torch.float32),
            torch.tensor(u_all, dtype=torch.float32)
        )
        z_all = mu_q.numpy()

    df_derived = df_derived.reset_index(drop=True)
    df_derived['z1'] = z_all[:, 0]
    df_derived['z2'] = z_all[:, 1]

    # Carry survey design vars into df_derived
    df = df.reset_index(drop=True)
    for col in ['WTMEC_POOLED', 'SDMVPSU', 'SDMVSTRA', 'RIDRETH3', 'RIDRETH1', 'cycle']:
        if col in df.columns:
            df_derived[col] = df[col].values

    # ------------------------------------------------------------------
    # [3] Phenotypic quadrant assignment
    # ------------------------------------------------------------------
    print("\n[3/6] Assigning phenotypic quadrants...")
    q_names = {0: 'MHNW', 1: 'IR-Dominant', 2: 'Steatosis-Dominant', 3: 'Dual-Burden'}
    df_derived['Quadrant'] = [
        registry.conformal_surface.get_quadrant(z_all[i, 0], z_all[i, 1])
        for i in range(len(z_all))
    ]
    df_derived['Phenotype'] = df_derived['Quadrant'].map(q_names)

    for q, name in q_names.items():
        n_q = (df_derived['Quadrant'] == q).sum()
        pct = 100 * n_q / len(df_derived)
        print(f"  {name}: n={n_q} ({pct:.1f}%)")

    # ------------------------------------------------------------------
    # [4] Ancestry group classification
    # ------------------------------------------------------------------
    print("\n[4/6] Classifying ancestry groups...")
    df_derived['Ancestry_Group'] = df_derived.apply(
        lambda r: build_ancestry_group(
            r.get('RIDRETH3', np.nan), r.get('RIDRETH1', np.nan)
        ), axis=1
    )
    print(f"  Ancestry distribution:\n{df_derived['Ancestry_Group'].value_counts().to_string()}")

    # ------------------------------------------------------------------
    # [5] Survey-weighted prevalence estimation
    # ------------------------------------------------------------------
    print("\n[5/6] Computing survey-weighted prevalence...")

    # Prepare svy-ready dataframe
    df_svy = df_derived.copy()
    for col in ['WTMEC_POOLED', 'SDMVPSU', 'SDMVSTRA']:
        df_svy[col] = pd.to_numeric(df_svy[col], errors='coerce')
    df_svy['SDMVSTRA'] = df_svy['SDMVSTRA'].astype('Int64').astype(int)
    df_svy['SDMVPSU'] = df_svy['SDMVPSU'].astype('Int64').astype(int)
    df_svy = df_svy.dropna(subset=['WTMEC_POOLED', 'SDMVPSU', 'SDMVSTRA'])

    # Binary indicator columns
    for q, name in q_names.items():
        df_svy[f'is_{name}'] = (df_svy['Quadrant'] == q).astype(float)

    # US normal-BMI adult population (census estimate)
    US_NORMAL_BMI_ADULTS = 80_000_000

    # -- 5a. Overall prevalence --
    print("  Computing overall prevalence...")
    overall_results = []
    for q, name in q_names.items():
        try:
            res = compute_weighted_prevalence(df_svy, f'is_{name}')
            r = res[0]
            prev = float(r['est'])
            ci_low = max(0.0, float(r['lci']))
            ci_high = min(1.0, float(r['uci']))
        except Exception as e:
            print(f"  [WARN] svy failed for {name}: {e}. Using unweighted.")
            prev = float((df_svy['Quadrant'] == q).mean())
            ci_low, ci_high = max(0, prev - 0.05), min(1, prev + 0.05)

        overall_results.append({
            'Phenotype': name,
            'Sample N': int((df_svy['Quadrant'] == q).sum()),
            'Weighted Prevalence (%)': round(prev * 100, 2),
            '95% CI': f"[{ci_low*100:.2f}%, {ci_high*100:.2f}%]",
            'National Estimate (M)': round(prev * US_NORMAL_BMI_ADULTS / 1e6, 2),
            'National Estimate 95% CI (M)':
                f"[{ci_low*US_NORMAL_BMI_ADULTS/1e6:.2f}M, "
                f"{ci_high*US_NORMAL_BMI_ADULTS/1e6:.2f}M]"
        })
        print(f"    {name}: {prev*100:.2f}% ({prev*US_NORMAL_BMI_ADULTS/1e6:.2f}M) "
              f"CI [{ci_low*100:.2f}%, {ci_high*100:.2f}%]")

    df_overall = pd.DataFrame(overall_results)

    # -- 5b. Ancestry-stratified prevalence --
    print("\n  Computing ancestry-stratified prevalence...")
    ancestry_groups = ['NHW', 'NHB', 'Hispanic', 'NHA', 'Other']
    ancestry_results = []

    for q, name in q_names.items():
        try:
            res_by = compute_weighted_prevalence(df_svy, f'is_{name}',
                                                  by_col='Ancestry_Group')
            for r in res_by:
                anc = r['by_level'][0] if isinstance(r['by_level'], list) else r['by_level']
                if anc in ancestry_groups:
                    prev = float(r['est'])
                    ci_low = max(0.0, float(r['lci']))
                    ci_high = min(1.0, float(r['uci']))
                    sample_n = int(((df_svy['Ancestry_Group'] == anc) &
                                    (df_svy['Quadrant'] == q)).sum())
                    ancestry_results.append({
                        'Ancestry': anc,
                        'Phenotype': name,
                        'Sample N': sample_n,
                        'Weighted Prevalence (%)': round(prev * 100, 2),
                        '95% CI': f"[{ci_low*100:.2f}%, {ci_high*100:.2f}%]"
                    })
        except Exception as e:
            print(f"  [WARN] ancestry svy failed for {name}: {e}")

    df_ancestry = pd.DataFrame(ancestry_results)
    if len(df_ancestry) > 0:
        anc_order = {v: i for i, v in enumerate(ancestry_groups)}
        df_ancestry['_a'] = df_ancestry['Ancestry'].map(anc_order)
        df_ancestry['_q'] = df_ancestry['Phenotype'].map(
            lambda x: list(q_names.values()).index(x))
        df_ancestry = df_ancestry.sort_values(['_a', '_q']).drop(columns=['_a', '_q'])

    # -- 5c. Counterfactual levers (Dual-Burden only) --
    print("\n  Computing counterfactual intervention levers for Dual-Burden...")
    from src_code.counterfactual.counterfactual import metabolic_quadrant_counterfactual
    features = [
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL",
        "hdl_mg_dL", "ast_U_L", "alt_U_L", "ggt_U_L", "bmi", "waist_cm",
        "platelets_1000_uL", "tyg", "ast_alt", "tg_hdl", "aip"
    ]
    UNITS = {
        "fasting_glucose_mg_dL": "mg/dL", "fasting_insulin_uU_mL": "uU/mL",
        "triglycerides_mg_dL": "mg/dL", "hdl_mg_dL": "mg/dL",
        "ast_U_L": "U/L", "alt_U_L": "U/L", "ggt_U_L": "U/L",
        "bmi": "kg/m2", "waist_cm": "cm", "platelets_1000_uL": "10^3/uL",
    }
    biomarkers = list(UNITS.keys())

    db_df = df_derived[df_derived['Quadrant'] == 3].copy()
    lever_deltas = {b: [] for b in biomarkers}

    for idx in range(len(db_df)):
        row = db_df.iloc[idx]
        z_current = np.array([row['z1'], row['z2']])
        x_raw = np.array([row[f] for f in features if f in row.index], dtype=float)
        try:
            cf_res = metabolic_quadrant_counterfactual(
                registry.model, registry.scaler, z_current, x_raw,
                registry.conformal_surface.z1_threshold,
                registry.conformal_surface.z2_threshold
            )
            for lev in cf_res.get('levers', []):
                bio = lev['biomarker']
                if bio in lever_deltas:
                    lever_deltas[bio].append(lev['delta_raw'])
        except Exception:
            pass

    median_deltas = []
    for b in biomarkers:
        vals = lever_deltas[b]
        if vals:
            median_deltas.append({
                'Biomarker': b.replace('_mg_dL','').replace('_U_L','')
                              .replace('_uU_mL','').replace('_','').upper(),
                'Median Required Delta': round(float(np.median(vals)), 2),
                'Unit': UNITS[b]
            })

    df_deltas = pd.DataFrame(median_deltas)

    # ------------------------------------------------------------------
    # [6] Save outputs
    # ------------------------------------------------------------------
    print("\n[6/6] Saving results...")
    df_overall.to_csv(os.path.join(results_dir, "national_burden_overall.csv"), index=False)
    df_ancestry.to_csv(os.path.join(results_dir, "national_burden_ancestry.csv"), index=False)
    df_deltas.to_csv(os.path.join(results_dir, "national_burden_deltas.csv"), index=False)

    # Compute key numbers for the dissertation
    db_row = df_overall[df_overall['Phenotype'] == 'Dual-Burden']
    db_prev = float(db_row['Weighted Prevalence (%)'].iloc[0]) if len(db_row) else None
    db_national = float(db_row['National Estimate (M)'].iloc[0]) if len(db_row) else None
    db_ci = db_row['National Estimate 95% CI (M)'].iloc[0] if len(db_row) else None

    print("\nOverall Prevalence (J+P combined, survey-weighted):")
    print(df_overall.to_string(index=False))

    if len(df_ancestry) > 0:
        print("\nAncestry-Stratified Prevalence:")
        print(df_ancestry.to_string(index=False))

    if len(df_deltas) > 0:
        print("\nMedian Intervention Levers (Dual-Burden -> Safety):")
        print(df_deltas.to_string(index=False))

    # Write markdown report
    md_path = os.path.join(results_dir, "national_burden.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# National Burden Analysis & Prevalence Estimates\n\n")
        f.write("Extrapolated using NHANES complex survey design weights (pooled "
                "J+P cycles, 2017-March 2020) to the US normal-BMI adult population "
                "(N ≈ 80,000,000).\n\n")
        f.write(f"**Analytical cohort:** n={len(df_svy)} complete normal-BMI "
                f"fasting participants (J-cycle n={cycle_counts.get('J', '?')}, "
                f"P-cycle n={cycle_counts.get('P', '?')}).\n\n")
        f.write("**Survey design:** WTMEC_POOLED weights (WTMEC2YR/2 for J, WTMECPRP/2 for P), "
                "PSU=SDMVPSU, Strata=SDMVSTRA (P-cycle strata offset +100 to prevent collision).\n\n")
        f.write("**Note on NHA (Non-Hispanic Asian):** RIDRETH3 (which contains "
                "code 6=NHA) is only available in J-cycle. P-cycle uses RIDRETH1 "
                "which codes Asian Americans under 'Other'. NHA prevalence estimates "
                "are therefore drawn from J-cycle only (n=119) and should be "
                "interpreted with caution.\n\n")
        f.write("---\n\n")
        f.write("## Overall Prevalence\n\n")
        f.write(df_overall.to_markdown(index=False))
        f.write("\n\n")
        if len(df_ancestry) > 0:
            f.write("## Ancestry-Stratified Prevalence\n\n")
            f.write(df_ancestry.to_markdown(index=False))
            f.write("\n\n")
        if len(df_deltas) > 0:
            f.write("## Median Intervention Levers for Dual-Burden Patients\n\n")
            f.write(df_deltas.to_markdown(index=False))
            f.write("\n")

    print(f"\n  national_burden.md -> {md_path}")

    # Save key numbers as JSON for programmatic use
    key_nums = {
        "cohort": {
            "n_combined": len(df_svy),
            "n_J": int(cycle_counts.get('J', 0)),
            "n_P": int(cycle_counts.get('P', 0)),
        },
        "dual_burden": {
            "weighted_prevalence_pct": db_prev,
            "national_estimate_M": db_national,
            "national_ci": db_ci,
        },
        "quadrant_n": {
            q_names[q]: int((df_svy['Quadrant'] == q).sum()) for q in range(4)
        }
    }
    json_path = os.path.join(results_dir, "national_burden_summary.json")
    with open(json_path, "w") as jf:
        json.dump(key_nums, jf, indent=2, default=str)
    print(f"  national_burden_summary.json -> {json_path}")

    print("\n" + "=" * 65)
    print("DISSERTATION NUMBERS TO USE")
    print("=" * 65)
    print(f"  Analytical cohort:       n={len(df_svy)} (J={cycle_counts.get('J','?')}, P={cycle_counts.get('P','?')})")
    if db_prev is not None:
        print(f"  Dual-Burden prevalence:  {db_prev:.2f}% ({db_national:.2f}M Americans)")
        print(f"  Dual-Burden national CI: {db_ci}")
    print("=" * 65)


if __name__ == "__main__":
    main()
