import os
import sys
import torch
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def calc_hsi(df):
    # HSI = 8 * (ALT / AST) + BMI + (2 if female else 0) + (2 if diabetes else 0)
    # Proxy diabetes as fasting glucose >= 126
    diabetes = (df['fasting_glucose_mg_dL'] >= 126).astype(int)
    female = (df['sex'] == 2).astype(int)
    return 8 * (df['alt_U_L'] / df['ast_U_L']) + df['bmi'] + (2 * female) + (2 * diabetes)

def calc_nafld_lfs(df):
    # NAFLD-LFS requires Metabolic Syndrome. Proxy with available data:
    # TG >= 150, Glucose >= 100, waist criteria
    elevated_tg = df['triglycerides_mg_dL'] >= 150
    elevated_glu = df['fasting_glucose_mg_dL'] >= 100
    mets = (elevated_tg & elevated_glu).astype(int) # Simplified proxy
    t2dm = (df['fasting_glucose_mg_dL'] >= 126).astype(int)
    ast_alt_ratio = df['ast_U_L'] / df['alt_U_L']
    
    return (-2.89 
            + 1.18 * mets 
            + 0.45 * t2dm 
            + 0.15 * df['fasting_insulin_uU_mL'] 
            + 0.04 * df['ast_U_L'] 
            - 0.94 * ast_alt_ratio)

def calc_fli(df):
    # FLI
    L = (0.953 * np.log(df['triglycerides_mg_dL']) 
         + 0.139 * df['bmi'] 
         + 0.718 * np.log(df['ggt_U_L']) 
         + 0.053 * df['waist_cm'] 
         - 15.745)
    return (np.exp(L) / (1 + np.exp(L))) * 100

def calc_tyg(df):
    return np.log(df['triglycerides_mg_dL'] * df['fasting_glucose_mg_dL'] / 2)

def main():
    print("Loading data and model for Benchmark Demolition...")
    df = load_data()
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    
    X_all, u_all, _, m_all, _, df_derived_all, _, _ = preprocess_data(df, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    model = iVAE_MetabolicStateModel()
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_all, dtype=torch.float32), torch.tensor(u_all, dtype=torch.float32))
        z_all = mu_q.numpy()

    # Filter only samples with valid CAP ground truth
    cap_mask = m_all[:, 1] == 1
    df_eval = df_derived_all.iloc[cap_mask].copy()
    z2_labeled = z_all[cap_mask, 1]
    cap_actual = df_eval['cap_score'].values

    print(f"\nEvaluating on {len(df_eval)} samples with valid CAP.")

    # Calculate scores
    scores = {
        'HSI': calc_hsi(df_eval),
        'NAFLD-LFS': calc_nafld_lfs(df_eval),
        'FLI': calc_fli(df_eval),
        'TyG Index': calc_tyg(df_eval),
        'DA-SS-iVAE (Z2)': z2_labeled
    }

    results = []

    # Binarize CAP
    y_248 = (cap_actual >= 248).astype(int)
    y_268 = (cap_actual >= 268).astype(int)

    for name, score_vals in scores.items():
        rho, _ = spearmanr(score_vals, cap_actual)
        
        # Handle NA in scores if any
        mask = ~np.isnan(score_vals)
        s_clean = score_vals[mask]
        y_248_clean = y_248[mask]
        y_268_clean = y_268[mask]

        if len(np.unique(y_248_clean)) > 1:
            auc_248 = roc_auc_score(y_248_clean, s_clean)
            if auc_248 < 0.5: auc_248 = 1.0 - auc_248 # Handle inverse direction
        else:
            auc_248 = np.nan
            
        if len(np.unique(y_268_clean)) > 1:
            auc_268 = roc_auc_score(y_268_clean, s_clean)
            if auc_268 < 0.5: auc_268 = 1.0 - auc_268
        else:
            auc_268 = np.nan
            
        results.append({
            'Model': name,
            'Spearman_Rho': round(rho, 3),
            'AUROC_CAP>=248': round(auc_248, 3),
            'AUROC_CAP>=268': round(auc_268, 3)
        })

    res_df = pd.DataFrame(results)
    print("\nBenchmark Demolition Results:")
    print(res_df.to_string(index=False))
    
    res_df.to_csv(os.path.join(RESULTS_DIR, "benchmark_demolition_results.csv"), index=False)
    
    with open(os.path.join(RESULTS_DIR, "benchmark_summary.md"), "w") as f:
        f.write("# Benchmark Demolition Results\n\n")
        f.write(res_df.to_markdown(index=False))

if __name__ == "__main__":
    main()
