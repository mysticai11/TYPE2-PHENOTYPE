"""
NHANES 2021-2023 (L-Cycle) Loader -- LMSIS Project
==================================================
Dedicated module for loading the post-pandemic L-cycle data directly from the CDC.
This script ensures the strict pipeline application:
1. Download 9 `.xpt` files via requests (no local storage required).
2. Merge on SEQN.
3. Apply filters: Age >= 20 -> Normal BMI (18.5-24.9) -> Complete 14 biomarkers.
4. Rename columns to canonical names used by the DA-SS-iVAE model.
"""

import pandas as pd
import requests
import io
import urllib3
import warnings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/"

URLS = {
    "DEMO_L": BASE_URL + "DEMO_L.xpt",
    "LUX_L": BASE_URL + "LUX_L.xpt",
    "GLU_L": BASE_URL + "GLU_L.xpt",
    "INS_L": BASE_URL + "INS_L.xpt",
    "BIOPRO_L": BASE_URL + "BIOPRO_L.xpt",
    "TCHOL_L": BASE_URL + "TCHOL_L.xpt",
    "TRIGLY_L": BASE_URL + "TRIGLY_L.xpt",
    "HDL_L": BASE_URL + "HDL_L.xpt",
    "CBC_L": BASE_URL + "CBC_L.xpt",
    "BMX_L": BASE_URL + "BMX_L.xpt",
}

# Mapping CDC L-cycle variables to LMSIS canonical model names
# Note the change: LBXTLG instead of LBXTR for Triglycerides
NHANES_TO_MODEL = {
    "RIDAGEYR":  "age",
    "RIAGENDR":  "sex",
    "RIDRETH1":  "ancestry_proxy",
    "BMXBMI":    "bmi",
    "BMXWAIST":  "waist_cm",
    "LBXGLU":    "fasting_glucose_mg_dL",
    "LBXIN":     "fasting_insulin_uU_mL",
    "LBXTLG":    "triglycerides_mg_dL",    # NEW for L-cycle (was LBXTR)
    "LBDHDD":    "hdl_mg_dL",
    "LBXSATSI":  "ast_U_L",
    "LBXSAL":    "alt_U_L",
    "LBXSGTSI":  "ggt_U_L",
    "LBXPLTSI":  "platelets_1000_uL",
    "LUXCAPM":   "cap_score",              # Target (FibroScan)
}

REQUIRED_NHANES_COLS = list(NHANES_TO_MODEL.keys())
BIOMARKER_COLS = [k for k in REQUIRED_NHANES_COLS if k not in ("RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "LUXCAPM")]

def load_l_cycle_data() -> pd.DataFrame:
    """
    Downloads, merges, and perfectly filters the NHANES 2021-2023 dataset.
    Returns a DataFrame with renamed, canonical columns ready for inference.
    """
    print("[L-Cycle] Downloading 10 datasets from CDC...")
    dfs = []
    for name, url in URLS.items():
        try:
            r = requests.get(url, verify=False)
            r.raise_for_status()
            df = pd.read_sas(io.BytesIO(r.content), format='xport')
            df = df.set_index('SEQN')
            dfs.append(df)
        except Exception as e:
            print(f"  [ERROR] Failed to download {name}: {e}")
            raise

    # 1. Merge
    merged = pd.concat(dfs, axis=1)
    
    # 2. Filter Age >= 20
    if 'RIDAGEYR' in merged.columns:
        merged = merged[merged['RIDAGEYR'] >= 20]
    
    # 3. Filter Normal BMI
    if 'BMXBMI' in merged.columns:
        merged = merged[(merged['BMXBMI'] >= 18.5) & (merged['BMXBMI'] < 25.0)]
        
    # 4. Filter Complete Biomarkers
    available_req = [c for c in BIOMARKER_COLS if c in merged.columns]
    merged = merged.dropna(subset=available_req)
    
    # 5. We also drop rows where CAP score is missing since we need it for zero-shot OOD eval
    if 'LUXCAPM' in merged.columns:
        merged = merged.dropna(subset=['LUXCAPM'])
        
    # 6. Keep only required columns and rename
    missing = [c for c in REQUIRED_NHANES_COLS if c not in merged.columns]
    if missing:
        raise ValueError(f"Missing required L-cycle columns: {missing}")
        
    merged = merged[REQUIRED_NHANES_COLS].copy()
    merged = merged.rename(columns=NHANES_TO_MODEL)
    
    # Add cycle indicator for reference
    merged['cycle'] = 'L_2021_2023'
    
    print(f"[L-Cycle] Successfully loaded and filtered {len(merged)} OOD cases.")
    return merged

if __name__ == "__main__":
    df = load_l_cycle_data()
    print(df.head())
