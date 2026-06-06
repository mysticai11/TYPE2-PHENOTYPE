import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def calc_hsi(df):
    diabetes = (df['fasting_glucose_mg_dL'] >= 126).astype(int)
    female = (df['sex'] == 2).astype(int)
    return 8 * (df['alt_U_L'] / df['ast_U_L']) + df['bmi'] + (2 * female) + (2 * diabetes)

def calc_nafld_lfs(df):
    elevated_tg = df['triglycerides_mg_dL'] >= 150
    elevated_glu = df['fasting_glucose_mg_dL'] >= 100
    mets = (elevated_tg & elevated_glu).astype(int)
    t2dm = (df['fasting_glucose_mg_dL'] >= 126).astype(int)
    ast_alt_ratio = df['ast_U_L'] / df['alt_U_L']
    
    return (-2.89 
            + 1.18 * mets 
            + 0.45 * t2dm 
            + 0.15 * df['fasting_insulin_uU_mL'] 
            + 0.04 * df['ast_U_L'] 
            - 0.94 * ast_alt_ratio)

def calc_fli(df):
    L = (0.953 * np.log(df['triglycerides_mg_dL']) 
         + 0.139 * df['bmi'] 
         + 0.718 * np.log(df['ggt_U_L']) 
         + 0.053 * df['waist_cm'] 
         - 15.745)
    return (np.exp(L) / (1 + np.exp(L))) * 100

def formal_bmi_degradation_analysis(df_full, df_normal_bmi, outcome_col='cap_score') -> dict:
    """
    Compute the formal BMI variance ratio and its implication for each score.
    """
    var_bmi_full    = df_full['bmi'].var()
    var_bmi_normal  = df_normal_bmi['bmi'].var()
    variance_ratio  = var_bmi_normal / var_bmi_full

    scores = {
        'HSI':       {'formula': calc_hsi, 'c_bmi': 1.0},
        'FLI':       {'formula': calc_fli, 'c_bmi': 0.139},
        'NAFLD-LFS': {'formula': calc_nafld_lfs, 'c_bmi': 0.0},
    }

    results = {}
    for name, spec in scores.items():
        # Compute score on full cohort and normal-BMI cohort
        s_full   = spec['formula'](df_full)
        s_normal = spec['formula'](df_normal_bmi)

        # Theoretical AUROC degradation lower bound
        bmi_var_contribution_full   = (spec['c_bmi']**2) * var_bmi_full
        bmi_var_contribution_normal = (spec['c_bmi']**2) * var_bmi_normal

        # Handle NaNs
        valid_normal = df_normal_bmi[outcome_col].notna() & s_normal.notna()
        if valid_normal.sum() > 2:
            rho_normal = spearmanr(s_normal[valid_normal], df_normal_bmi.loc[valid_normal, outcome_col])[0]
        else:
            rho_normal = np.nan

        results[name] = {
            'c_bmi':                      spec['c_bmi'],
            'bmi_var_contribution_full':  round(bmi_var_contribution_full, 3),
            'bmi_var_contribution_normal': round(bmi_var_contribution_normal, 3),
            'contribution_ratio':         round(variance_ratio, 4),
            'theoretical_signal_loss':    round(1 - variance_ratio, 4) if spec['c_bmi'] > 0 else 0.0,
            'empirical_rho_normal':       round(rho_normal, 4),
        }
    return results

def load_full_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_nhanes_merged.csv")
    df = pd.read_csv(data_path)
    df = df[df["RIDAGEYR"] >= 18]
    rename_map = {
        "RIDAGEYR": "age",
        "RIAGENDR": "sex",
        "RIDRETH1": "ancestry_proxy",
        "BMXBMI": "bmi",
        "BMXWAIST": "waist_cm",
        "LBXGLU": "fasting_glucose_mg_dL",
        "LBXIN": "fasting_insulin_uU_mL",
        "LBXTR": "triglycerides_mg_dL",
        "LBDHDD": "hdl_mg_dL",
        "LBXSATSI": "ast_U_L",
        "LBXSAL": "alt_U_L",
        "LBXSGTSI": "ggt_U_L",
        "LBXPLTSI": "platelets_1000_uL"
    }
    if "LUXCAPM" in df.columns:
        rename_map["LUXCAPM"] = "cap_score"
    df = df.rename(columns=rename_map)
    required_cols = list({v for k, v in rename_map.items() if k != "LUXCAPM"})
    df = df.dropna(subset=required_cols)
    
    if "cap_score" not in df.columns:
        df["cap_score"] = np.nan
        
    homa_ir_proxy = (df["fasting_insulin_uU_mL"] * df["fasting_glucose_mg_dL"]) / 405.0
    tyg_proxy = np.log((df["triglycerides_mg_dL"] * df["fasting_glucose_mg_dL"]) / 2.0)
    df["ir_label"] = ((homa_ir_proxy > 2.5) & (tyg_proxy >= 8.5)).astype(int)
    
    return df

def main():
    print("Loading data for Formal BMI-Invariance Theorem...")
    df_normal = load_data()
    df_mixed = load_full_data()
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    
    # We want to run this analysis on derived features where CAP is present
    _, _, _, m_all_normal, _, df_derived_normal, _, _ = preprocess_data(df_normal, scaler=scaler, u_encoder=u_encoder, is_train=False)
    _, _, _, m_all_mixed, _, df_derived_mixed, _, _ = preprocess_data(df_mixed, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    cap_mask_normal = m_all_normal[:, 1] == 1
    df_normal_bmi = df_derived_normal.iloc[cap_mask_normal].copy()

    cap_mask_mixed = m_all_mixed[:, 1] == 1
    df_mixed_bmi = df_derived_mixed.iloc[cap_mask_mixed].copy()

    print(f"Mixed BMI cohort: n={len(df_mixed_bmi)}")
    print(f"Normal BMI cohort: n={len(df_normal_bmi)}")

    res = formal_bmi_degradation_analysis(df_mixed_bmi, df_normal_bmi, outcome_col='cap_score')
    
    # Output results
    res_df = pd.DataFrame(res).T.reset_index().rename(columns={'index': 'Score'})
    print("\nFormal BMI-Invariance Theorem Results:")
    print(res_df.to_string(index=False))
    
    res_df.to_csv(os.path.join(RESULTS_DIR, "formal_bmi_theorem.csv"), index=False)
    
if __name__ == "__main__":
    main()
