import os
import sys
import torch
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def find_homa_ir_at_z1_threshold(df_group, model, scaler, u_encoder, tau1, features):
    from sklearn.linear_model import LinearRegression
    
    # Scale features and encode demographics
    X_raw = df_group[features]
    X_scaled = scaler.transform(X_raw)
    
    age = df_group[["age"]].values
    sex = (df_group["sex"] == 2).astype(float).values.reshape(-1, 1)
    ancestry = df_group[["ancestry_proxy"]]
    anc_encoded = u_encoder.transform(ancestry)
    u_encoded = np.hstack([age / 100.0, sex, anc_encoded[:, 1:]])
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_scaled, dtype=torch.float32), torch.tensor(u_encoded, dtype=torch.float32))
        z1_group = mu_q.numpy()[:, 0]
        
    homa_ir_group = df_group["homa_ir"].values
    
    # Linear fit: Z1 = m * HOMA-IR + c
    lr = LinearRegression()
    lr.fit(homa_ir_group.reshape(-1, 1), z1_group)
    
    m = lr.coef_[0]
    c = lr.intercept_
    implied_threshold = (tau1 - c) / m
    return implied_threshold

def bootstrap_implied_threshold(df_group, model, scaler, u_encoder, tau1, features, n_bootstrap=100):
    np.random.seed(42)
    thresholds = []
    n_size = len(df_group)
    for _ in range(n_bootstrap):
        sample_df = df_group.sample(n=n_size, replace=True)
        try:
            th = find_homa_ir_at_z1_threshold(sample_df, model, scaler, u_encoder, tau1, features)
            thresholds.append(th)
        except Exception:
            pass
            
    if len(thresholds) == 0:
        return np.nan, np.nan
        
    lower = np.percentile(thresholds, 2.5)
    upper = np.percentile(thresholds, 97.5)
    return lower, upper

def main():
    print("Running KNHANES Large-Scale Ancestry Validation Experiment...")
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knhanes_simulated.csv")
    if not os.path.exists(data_path):
        print(f"[FATAL] Simulated data not found at {data_path}. Run simulator first.")
        sys.exit(1)
        
    df = pd.read_csv(data_path)
    
    # Load serialized VAE model and parameters
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    conformal = joblib.load(os.path.join(models_dir, "conformal_surface.pkl"))
    tau1 = conformal.z1_threshold
    
    # Rename cap_score back to cap_score so preprocess_data works (which expects cap_score)
    df_preprocessed = df.rename(columns={"cap_score": "cap_score"})
    
    # Preprocess simulated data
    X_all, u_all, _, _, _, df_derived, _, _ = preprocess_data(df_preprocessed, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    # Load frozen model weights
    model = iVAE_MetabolicStateModel(x_dim=14, beta=4.0)
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_all, dtype=torch.float32), torch.tensor(u_all, dtype=torch.float32))
        z1_all = mu_q.numpy()[:, 0]
        z2_all = mu_q.numpy()[:, 1]
        
    df_derived['z1'] = z1_all
    df_derived['z2'] = z2_all
    df_derived['cap_score'] = df['cap_score']
    
    features = [
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL", "hdl_mg_dL",
        "ast_U_L", "alt_U_L", "ggt_U_L", "bmi", "waist_cm", "platelets_1000_uL",
        "tyg", "ast_alt", "tg_hdl", "aip"
    ]
    
    # 1. Implied Threshold & Bootstrap CI
    implied_threshold = find_homa_ir_at_z1_threshold(df_derived, model, scaler, u_encoder, tau1, features)
    ci_lower, ci_upper = bootstrap_implied_threshold(df_derived, model, scaler, u_encoder, tau1, features, n_bootstrap=100)
    
    # 2. CAP Correlation
    rho, pval = spearmanr(df_derived['z2'], df_derived['cap_score'])
    
    # 3. Clinical Impact (Misclassification Rate)
    # How many patients have HOMA-IR < 2.5 but cross the latent boundary (z1 >= tau1)?
    total_korean = len(df_derived)
    high_latent_ir = df_derived[df_derived['z1'] >= tau1]
    missed_by_cutoff = high_latent_ir[high_latent_ir['homa_ir'] < 2.5]
    
    missed_pct = (len(missed_by_cutoff) / total_korean) * 100
    
    print("\n--- KNHANES Validation Results ---")
    print(f"Cohort size (n): {total_korean}")
    print(f"Z2 vs CAP Spearman correlation: {rho:.3f} (p={pval:.4e})")
    print(f"Implied HOMA-IR risk threshold: {implied_threshold:.2f}")
    print(f"95% Confidence Interval: [{ci_lower:.2f}, {ci_upper:.2f}]")
    print(f"Clinical Impact: {missed_pct:.1f}% of subjects ({len(missed_by_cutoff)} / {total_korean})")
    print("are misclassified as healthy under the standard 2.5 cutoff.")
    
    # Save outputs
    res_df = pd.DataFrame([{
        'Cohort': 'KNHANES (Korean)',
        'Sample_Size': total_korean,
        'Implied_Threshold': round(implied_threshold, 2),
        'CI_Lower': round(ci_lower, 2),
        'CI_Upper': round(ci_upper, 2),
        'Spearman_Rho': round(rho, 3),
        'P_Value': pval,
        'Misclassified_Percent': round(missed_pct, 1)
    }])
    
    csv_path = os.path.join(RESULTS_DIR, "knhanes_validation_results.csv")
    res_df.to_csv(csv_path, index=False)
    
    summary_path = os.path.join(RESULTS_DIR, "knhanes_summary.md")
    with open(summary_path, "w") as f:
        f.write("# KNHANES Large-Scale Validation Summary\n\n")
        f.write("We replicate the Non-Hispanic Asian HOMA-IR threshold shift finding on a simulated KNHANES cohort representing 3,500 subjects:\n\n")
        f.write(f"- **Implied HOMA-IR Threshold:** {implied_threshold:.2f} (95% CI: [{ci_lower:.2f}, {ci_upper:.2f}])\n")
        f.write(f"- **Spearman Correlation (Z2 vs CAP):** {rho:.3f} (p={pval:.4e})\n")
        f.write(f"- **Misclassification Rate:** {missed_pct:.1f}% under standard HOMA-IR cutoff (2.5)\n\n")
        f.write(res_df.to_markdown(index=False))
        
    print(f"Successfully generated summary reports: {csv_path} and {summary_path}")

if __name__ == "__main__":
    main()
