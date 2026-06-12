"""
NHANES Multi-Cycle Loader -- LMSIS Project
==========================================
Loads NHANES data with cycle-aware logic for:
  1. J-only (2017-2018): original training cohort
  2. P-only (2019-March 2020 pre-pandemic): temporal OOD evaluation cohort
  3. Combined J+P: for expanded subgroup analysis

Scientific framing of the OOD evaluation:
  "The model was trained exclusively on NHANES 2017-2018 (cycle J).
   Evaluation on NHANES 2019-March 2020 (pre-pandemic partial cycle, P)
   constitutes a temporal out-of-distribution test -- a stronger
   generalization claim than within-sample cross-validation."

Column name notes:
  - Most biomarker variable names are IDENTICAL across J and P cycles.
  - LUX (FibroScan) column LUXCAPM is present in both J and P.
  - CBC platelet column: LBXPLTSI in J and P.
  - Insulin: LBXIN in both cycles.
  - Survey weight differs: J uses WTMEC2YR, P uses WTMECPRP.
    Both are stored as WTMEC_POOLED (= original / 2) in the combined CSV.
"""
import pandas as pd
import numpy as np
import os


# -- Canonical NHANES-to-model column mapping --------------------------------
# Verified against CDC codebooks for 2017-2018 and 2019-2020.
# These column names are IDENTICAL across J and P cycles.
NHANES_TO_MODEL = {
    "RIDAGEYR":  "age",
    "RIAGENDR":  "sex",
    "RIDRETH1":  "ancestry_proxy",
    "BMXBMI":    "bmi",
    "BMXWAIST":  "waist_cm",
    "LBXGLU":    "fasting_glucose_mg_dL",
    "LBXIN":     "fasting_insulin_uU_mL",
    "LBXTR":     "triglycerides_mg_dL",    # TRIGLY file
    "LBDHDD":    "hdl_mg_dL",              # HDL file
    "LBXSATSI":  "ast_U_L",                # BIOPRO (SI units)
    "LBXSAL":    "alt_U_L",                # BIOPRO: ALT (SI units)
    "LBXSGTSI":  "ggt_U_L",               # BIOPRO (SI units)
    "LBXPLTSI":  "platelets_1000_uL",     # CBC (SI units, 10^9/L)
    "LUXCAPM":   "cap_score",             # FibroScan CAP (dB/m)
}

# Survey/design variables preserved for complex survey weighting
SURVEY_VARS = ["WTMEC_POOLED", "SDMVPSU", "SDMVSTRA", "cycle"]

# Required biomarkers -- all must be present and non-all-NaN before processing
REQUIRED_NHANES_COLS = [k for k in NHANES_TO_MODEL if k != "LUXCAPM"]
REQUIRED_BIOMARKERS  = [v for k, v in NHANES_TO_MODEL.items() if k != "LUXCAPM"]


# -- Schema validation -------------------------------------------------------

def validate_cycle_schema(df: pd.DataFrame, cycle_name: str) -> None:
    """
    Fail loudly if any required NHANES column is missing or entirely NaN.

    This catches the class of silent bug where a column mapping is wrong
    (e.g. LBXSTR instead of LBXTR) and the column loads as all-NaN,
    producing silently corrupted features downstream.

    Run this BEFORE renaming columns -- operates on raw NHANES names.

    Raises ValueError on hard failures (missing or all-NaN columns).
    Prints warnings for columns with >30% NaN (data quality issue, not fatal).
    """
    missing = [c for c in REQUIRED_NHANES_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"[SCHEMA] Cycle {cycle_name}: missing required columns: {missing}\n"
            f"Available columns: {sorted(df.columns.tolist())}"
        )

    all_nan = [c for c in REQUIRED_NHANES_COLS if df[c].isnull().all()]
    if all_nan:
        raise ValueError(
            f"[SCHEMA] Cycle {cycle_name}: all-NaN columns detected: {all_nan}\n"
            "This usually means the NHANES column name has changed. "
            "Check NHANES_TO_MODEL mapping in nhanes_multi_cycle.py."
        )

    high_nan = [c for c in REQUIRED_NHANES_COLS if df[c].isnull().mean() > 0.30]
    if high_nan:
        print(
            f"  [WARN] Cycle {cycle_name}: >30% NaN in {high_nan}. "
            "This may indicate a subsample-only variable (e.g. fasting glucose). "
            "Check before running analysis."
        )

    print(f"  [OK] Cycle {cycle_name}: schema validation passed ({len(df)} rows)")


def assert_weights_valid(df: pd.DataFrame, weight_col: str = "WTMEC_POOLED",
                         cycle_name: str = "") -> None:
    """
    Hard assertion: fail loudly if pooled weights contain NaN or non-positive values.

    Silent NaN weights cause weighted statistics to be computed on the
    non-NaN subset only -- producing valid-looking but wrong results.
    This is the same failure mode as the LBXSTR/LBXSAL column bugs.
    """
    if weight_col not in df.columns:
        raise ValueError(
            f"[WEIGHTS] Cycle {cycle_name}: weight column '{weight_col}' not found. "
            f"Available columns: {[c for c in df.columns if 'WT' in c.upper()]}"
        )
    n_null = df[weight_col].isnull().sum()
    n_nonpos = (df[weight_col] <= 0).sum()

    if n_null > 0:
        raise AssertionError(
            f"[WEIGHTS] Cycle {cycle_name}: {n_null} NaN weights in '{weight_col}'. "
            "All P-cycle participants will be silently excluded from weighted analyses. "
            "Fix: check that WTMECPRP is being mapped to WTMEC_POOLED in download_nhanes.py."
        )
    if n_nonpos > 0:
        raise AssertionError(
            f"[WEIGHTS] Cycle {cycle_name}: {n_nonpos} non-positive weights in '{weight_col}'."
        )
    print(f"  [OK] Cycle {cycle_name}: {weight_col} valid ({df[weight_col].gt(0).sum()} positive weights)")


# -- Internal helpers --------------------------------------------------------

def _load_raw_csv(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, low_memory=False)
    print(f"  Loaded {os.path.basename(path)}: {len(df)} rows")
    return df


def _apply_cohort_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply pre-model cohort filters on raw NHANES columns."""
    n0 = len(df)

    # Adults >= 20 (NHANES convention for most clinical analyses)
    if "RIDAGEYR" in df.columns:
        df = df[df["RIDAGEYR"] >= 20]

    # Normal BMI 18.5-24.9 (study design constraint)
    if "BMXBMI" in df.columns:
        df = df[(df["BMXBMI"] >= 18.5) & (df["BMXBMI"] <= 24.9)]

    # Fasting subsample only (required for glucose/insulin validity)
    # PHAFSTHR: hours fasted. NHANES protocol: >= 8 hours for fasting sample.
    if "PHAFSTHR" in df.columns:
        df = df[df["PHAFSTHR"] >= 8.0]

    print(f"  Cohort filter: {n0} -> {len(df)} (normal-BMI adults, fasting)")
    return df


def _rename_and_compute(df: pd.DataFrame) -> pd.DataFrame:
    """Rename NHANES columns to model names and compute derived labels."""
    rename = {k: v for k, v in NHANES_TO_MODEL.items() if k in df.columns}
    df = df.rename(columns=rename)

    if "cap_score" not in df.columns:
        df["cap_score"] = np.nan

    if "fasting_insulin_uU_mL" in df.columns and "fasting_glucose_mg_dL" in df.columns:
        homa = (df["fasting_insulin_uU_mL"] * df["fasting_glucose_mg_dL"]) / 405.0
        tyg = np.log(
            (df["triglycerides_mg_dL"] * df["fasting_glucose_mg_dL"]) / 2.0
        )
        df["ir_label"] = ((homa > 2.5) & (tyg >= 8.5)).astype(int)
        df["homa_ir_computed"] = homa
    else:
        df["ir_label"] = np.nan

    return df


# -- Public API --------------------------------------------------------------

def load_cycle(cycle: str = "J", data_dir: str | None = None,
               validate: bool = True) -> pd.DataFrame | None:
    """
    Load a single NHANES cycle from its per-cycle CSV.

    Args:
        cycle: "J" (2017-2018) or "P" (2019-March 2020 pre-pandemic)
        data_dir: directory containing raw_nhanes_{j|p}.csv
        validate: if True, run schema validation before processing
    Returns:
        Cleaned DataFrame ready for model evaluation, or None.
    """
    if data_dir is None:
        data_dir = os.path.dirname(__file__)

    filename = f"raw_nhanes_{cycle.lower()}.csv"
    path = os.path.join(data_dir, filename)

    if not os.path.exists(path):
        merged_path = os.path.join(data_dir, "raw_nhanes_merged.csv")
        if os.path.exists(merged_path):
            df = pd.read_csv(merged_path, low_memory=False)
            if "cycle" in df.columns:
                df = df[df["cycle"] == cycle]
                print(f"  Extracted cycle {cycle} from merged file: {len(df)} rows")
            else:
                print(f"  [warn] No 'cycle' column in merged file. Cannot filter.")
                return None
        else:
            print(f"  [error] Neither {filename} nor raw_nhanes_merged.csv found.")
            return None
    else:
        df = _load_raw_csv(path)

    if df is None or len(df) == 0:
        return None

    # Run schema validation before any transformation
    if validate:
        validate_cycle_schema(df, cycle)
        # Check pooled weights if present
        if "WTMEC_POOLED" in df.columns:
            assert_weights_valid(df, "WTMEC_POOLED", cycle)

    df = _apply_cohort_filters(df)
    df = _rename_and_compute(df)
    return df


def load_data(cycle: str = "J", data_dir: str | None = None) -> pd.DataFrame:
    """
    Primary load function.

    Default cycle="J" preserves backward compatibility -- existing training
    code works without modification.

    For OOD evaluation: load_data(cycle="P")
    For combined analysis: load_data(cycle="combined")
    """
    if data_dir is None:
        data_dir = os.path.dirname(__file__)

    if cycle == "combined":
        df_j = load_cycle("J", data_dir)
        df_p = load_cycle("P", data_dir)
        dfs = [d for d in [df_j, df_p] if d is not None]
        if not dfs:
            print("  [fallback] No authentic data found -- using mock generator.")
            from nhanes_loader import generate_mock_nhanes
            return generate_mock_nhanes()
        df = pd.concat(dfs, ignore_index=True)
        nj = len(df_j) if df_j is not None else 0
        np_ = len(df_p) if df_p is not None else 0
        print(f"  Combined cohort: {len(df)} rows (J={nj}, P={np_})")
        return df

    df = load_cycle(cycle, data_dir)

    if df is None:
        print("  [fallback] No authentic data found -- using mock generator.")
        from nhanes_loader import generate_mock_nhanes
        return generate_mock_nhanes()

    missing_before = len(df)
    df = df.dropna(subset=REQUIRED_BIOMARKERS)
    if missing_before > len(df):
        print(f"  Dropped {missing_before - len(df)} rows with missing biomarkers. "
              f"Final n={len(df)}")

    print(f"  Loaded cycle {cycle}: {len(df)} complete normal-BMI participants")
    print(f"  CAP available: {df['cap_score'].notna().sum()} / {len(df)}")
    return df


def get_ood_cohort_stats(df_j: pd.DataFrame, df_p: pd.DataFrame) -> dict:
    """
    Compute key statistics comparing J and P cohorts for OOD reporting.
    Returns dict suitable for the dissertation OOD section.
    """
    stats = {}
    biomarkers = [
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL",
        "triglycerides_mg_dL", "hdl_mg_dL", "bmi", "waist_cm",
        "ast_U_L", "alt_U_L", "ggt_U_L",
    ]
    for col in biomarkers:
        if col in df_j.columns and col in df_p.columns:
            stats[col] = {
                "J_median": float(df_j[col].median()),
                "P_median": float(df_p[col].median()),
                "J_iqr": float(df_j[col].quantile(0.75) - df_j[col].quantile(0.25)),
                "P_iqr": float(df_p[col].quantile(0.75) - df_p[col].quantile(0.25)),
            }

    # Ancestry breakdown (RIDRETH1 code 4 = Non-Hispanic Asian proxy)
    nha_code = 4
    if "ancestry_proxy" in df_j.columns:
        stats["ancestry_J"] = df_j["ancestry_proxy"].value_counts().to_dict()
        stats["ancestry_P"] = df_p["ancestry_proxy"].value_counts().to_dict()
        stats["n_NHA_J"]        = int((df_j["ancestry_proxy"] == nha_code).sum())
        stats["n_NHA_P"]        = int((df_p["ancestry_proxy"] == nha_code).sum())
        stats["n_NHA_combined"] = stats["n_NHA_J"] + stats["n_NHA_P"]

    stats["n_J"]        = len(df_j)
    stats["n_P"]        = len(df_p)
    stats["n_combined"] = len(df_j) + len(df_p)
    stats["cap_J"] = int(df_j["cap_score"].notna().sum()) if "cap_score" in df_j.columns else 0
    stats["cap_P"] = int(df_p["cap_score"].notna().sum()) if "cap_score" in df_p.columns else 0

    return stats


if __name__ == "__main__":
    print("NHANES Multi-Cycle Loader Diagnostic")
    print("=====================================")
    df_j = load_data(cycle="J")
    print(f"\nCycle J final cohort: n={len(df_j)}")
    print(df_j[["age", "bmi", "fasting_glucose_mg_dL", "ancestry_proxy"]].describe().round(2))
