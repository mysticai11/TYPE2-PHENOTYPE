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

from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

def calc_tyg(df):
    return np.log(df['triglycerides_mg_dL'] * df['fasting_glucose_mg_dL'] / 2)

def main():
    print("Loading data and model for Benchmark Demolition...")
    df = load_data()
    
    # Train/Val/Test split (identical to train.py)
    df_train, df_temp = train_test_split(df, test_size=0.30, random_state=42)
    df_val, df_test = train_test_split(df_temp, test_size=0.50, random_state=42)
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    
    # Preprocess train and test splits using the frozen scaler and encoder
    X_train, u_train, _, m_train, _, df_derived_train, _, _ = preprocess_data(
        df_train, scaler=scaler, u_encoder=u_encoder, is_train=False
    )
    X_test, u_test, _, m_test, _, df_derived_test, _, _ = preprocess_data(
        df_test, scaler=scaler, u_encoder=u_encoder, is_train=False
    )
    
    # Train supervised baselines on the training split (where CAP is available)
    train_cap_mask = df_derived_train['cap_score'].notna()
    X_train_baselines = X_train[train_cap_mask]
    y_train_baselines = df_derived_train['cap_score'].values[train_cap_mask]
    
    print(f"Training supervised baseline models on {len(X_train_baselines)} samples...")
    
    # 1. Elastic Net
    en = ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42)
    en.fit(X_train_baselines, y_train_baselines)
    
    # 2. Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train_baselines, y_train_baselines)
    
    # 3. XGBoost
    xgb_model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
    xgb_model.fit(X_train_baselines, y_train_baselines)
    
    # Load iVAE model to run evaluation
    model = iVAE_MetabolicStateModel()
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()
    
    # Filter only test samples with valid CAP ground truth
    test_cap_mask = df_derived_test['cap_score'].notna()
    X_test_baselines = X_test[test_cap_mask]
    cap_actual = df_derived_test['cap_score'].values[test_cap_mask]
    
    print(f"Evaluating on {len(X_test_baselines)} test samples with valid CAP.")
    
    # Run iVAE encoder on the test subset
    with torch.no_grad():
        mu_q, _ = model.encoder(
            torch.tensor(X_test_baselines, dtype=torch.float32),
            torch.tensor(u_test[test_cap_mask], dtype=torch.float32)
        )
        z2_test = mu_q.numpy()[:, 1]
        
    df_eval = df_derived_test.loc[test_cap_mask].copy()
    
    # Calculate scores
    scores = {
        'HSI': calc_hsi(df_eval),
        'NAFLD-LFS': calc_nafld_lfs(df_eval),
        'FLI': calc_fli(df_eval),
        'TyG Index': calc_tyg(df_eval),
        'Elastic Net': en.predict(X_test_baselines),
        'Random Forest': rf.predict(X_test_baselines),
        'XGBoost': xgb_model.predict(X_test_baselines),
        'DA-SS-iVAE (Z2)': z2_test
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
    print("\nBenchmark Demolition Results (Test Set):")
    print(res_df.to_string(index=False))
    
    res_df.to_csv(os.path.join(RESULTS_DIR, "benchmark_demolition_results.csv"), index=False)
    
    with open(os.path.join(RESULTS_DIR, "benchmark_summary.md"), "w") as f:
        f.write("# Benchmark Demolition Results\n\n")
        f.write(res_df.to_markdown(index=False))
        
if __name__ == "__main__":
    main()
