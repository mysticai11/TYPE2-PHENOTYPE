import os
import sys
import torch
import numpy as np
import pandas as pd
from scipy.stats import kruskal
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def find_homa_ir_at_z1_threshold(df_group, model, scaler, u_encoder, tau1, features):
    # We want to find HOMA-IR where Z1 crosses tau1.
    # Since HOMA-IR strongly correlates with Z1, we fit a simple linear model: Z1 = m * HOMA-IR + c
    # Then implied_threshold = (tau1 - c) / m
    from sklearn.linear_model import LinearRegression
    
    # Need to encode this specific group to get Z1
    X_raw = df_group[features]
    X_scaled = scaler.transform(X_raw)
    
    # We use encode_demographics logic manually for this subset
    age = df_group[["age"]].values
    sex = (df_group["sex"] == 2).astype(float).values.reshape(-1, 1)
    ancestry = df_group[["ancestry_proxy"]]
    anc_encoded = u_encoder.transform(ancestry)
    u_encoded = np.hstack([age / 100.0, sex, anc_encoded[:, 1:]])
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_scaled, dtype=torch.float32), torch.tensor(u_encoded, dtype=torch.float32))
        z1_group = mu_q.numpy()[:, 0]
        
    homa_ir_group = df_group["homa_ir"].values
    
    # Linear fit
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
        # Resample with replacement
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
    print("Running Ancestral Threshold Bias Experiment...")
    df = load_data()
    raw_df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_nhanes_merged.csv"))
    
    # Map SEQN to RIDRETH3 for precise Asian ancestry analysis
    seqn_to_reth3 = dict(zip(raw_df['SEQN'], raw_df['RIDRETH3']))
    df['RIDRETH3'] = df.index.map(lambda i: raw_df.loc[i, 'RIDRETH3'] if i in raw_df.index else np.nan) 
    # Wait, the index of df is not SEQN. 
    # Let's map SEQN if it's in df. nhanes_loader doesn't keep SEQN! 
    # That's okay, we can just align by index since nhanes_loader just filters raw_df.
    # Actually, df = df.rename(...) keeps the original index from raw_df!
    df['RIDRETH3'] = raw_df.loc[df.index, 'RIDRETH3']

    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    conformal = joblib.load(os.path.join(models_dir, "conformal_surface.pkl"))
    tau1 = conformal.z1_threshold
    
    X_all, u_all, _, _, _, df_derived, _, _ = preprocess_data(df, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    model = iVAE_MetabolicStateModel(x_dim=14, beta=4.0)
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_all, dtype=torch.float32), torch.tensor(u_all, dtype=torch.float32))
        z1_all = mu_q.numpy()[:, 0]
        
    df_derived['z1'] = z1_all
    df_derived['RIDRETH3'] = df['RIDRETH3']
    
    # Mapping RIDRETH3 to groups
    # 1: Mexican American, 2: Other Hispanic -> 'Hispanic'
    # 3: Non-Hispanic White -> 'NHW'
    # 4: Non-Hispanic Black -> 'NHB'
    # 6: Non-Hispanic Asian -> 'NHA'
    def map_ancestry(val):
        if val in [1, 2]: return 'Hispanic'
        elif val == 3: return 'NHW'
        elif val == 4: return 'NHB'
        elif val == 6: return 'NHA'
        return 'Other'
        
    df_derived['Ancestry_Group'] = df_derived['RIDRETH3'].apply(map_ancestry)
    
    # 1. HOMA-IR Band Analysis
    band_df = df_derived[(df_derived['homa_ir'] >= 2.0) & (df_derived['homa_ir'] <= 3.0)]
    
    ancestry_groups = ['NHW', 'NHB', 'Hispanic', 'NHA']
    z1_by_ancestry = [band_df[band_df['Ancestry_Group'] == g]['z1'].values for g in ancestry_groups]
    
    # Filter out empty groups if any
    valid_groups = [z for z in z1_by_ancestry if len(z) > 0]
    
    print("\nSample sizes in HOMA-IR 2.3-2.7 band:")
    for g in ancestry_groups:
        n_band = len(band_df[band_df['Ancestry_Group'] == g])
        print(f"  {g}: n = {n_band}")
        
    if len(valid_groups) > 1:
        stat, p = kruskal(*valid_groups)
        print(f"\nKruskal-Wallis test across ancestries at HOMA-IR ~ 2.5: p={p:.4e}")
    else:
        print("Not enough data to run Kruskal-Wallis.")
        
    # 2. Implied Fair HOMA-IR Threshold
    results = []
    features = [
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL", "hdl_mg_dL",
        "ast_U_L", "alt_U_L", "ggt_U_L", "bmi", "waist_cm", "platelets_1000_uL",
        "tyg", "ast_alt", "tg_hdl", "aip"   # homa_ir removed — it's the anchor target, not an input
    ]
    
    for g in ancestry_groups:
        group_df = df_derived[df_derived['Ancestry_Group'] == g].copy()
        if len(group_df) < 10:
            continue
        
        implied_threshold = find_homa_ir_at_z1_threshold(group_df, model, scaler, u_encoder, tau1, features)
        ci_lower, ci_upper = bootstrap_implied_threshold(group_df, model, scaler, u_encoder, tau1, features)
        
        n_band = len(band_df[band_df['Ancestry_Group'] == g])
        
        results.append({
            'Ancestry': g,
            'N (Full)': len(group_df),
            'N (HOMA 2.3-2.7)': n_band,
            'Implied Threshold': round(implied_threshold, 2),
            '95% CI': f"[{ci_lower:.2f}, {ci_upper:.2f}]"
        })
        
    res_df = pd.DataFrame(results)
    print("\nImplied Thresholds by Ancestry:")
    print(res_df.to_string(index=False))
    
    # 3. Clinical Impact Calculation for NHA
    nha_patients = df_derived[df_derived['Ancestry_Group'] == 'NHA']
    if len(nha_patients) > 0:
        currently_missed = nha_patients[
            (nha_patients['homa_ir'] < 2.5) & 
            (nha_patients['z1'] >= tau1)
        ]
        pct_missed = len(currently_missed) / len(nha_patients) * 100
        print(f"\nClinical Impact: {pct_missed:.1f}% of Non-Hispanic Asian Americans ({len(currently_missed)} out of {len(nha_patients)})")
        print("in this normal-BMI cohort are currently misclassified as insulin-sensitive")
        print("by the universal NHANES threshold of 2.5.")
    
    res_df.to_csv(os.path.join(RESULTS_DIR, "ancestry_threshold_results.csv"), index=False)
    
    with open(os.path.join(RESULTS_DIR, "ancestry_summary.md"), "w") as f:
        f.write("# Ancestral Threshold Bias Results\n\n")
        f.write(f"Kruskal-Wallis p-value near HOMA-IR 2.5: {p:.4e}\n\n")
        f.write(res_df.to_markdown(index=False))

if __name__ == "__main__":
    main()
