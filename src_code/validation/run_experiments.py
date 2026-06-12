import os
import sys
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split
import joblib
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_exp3_z2_vs_cap(df_derived, z_all, m_all):
    print("\n--- Running Experiment 3: Z2 vs CAP ---")
    cap_mask = m_all[:, 1] == 1
    z2_labeled = z_all[cap_mask, 1]
    cap_labeled = df_derived['cap_score'].values[cap_mask]
    
    rho, pval = spearmanr(z2_labeled, cap_labeled)
    print(f"Spearman correlation between Z2 and CAP: {rho:.4f} (p={pval:.4e})")
    
    df_exp3 = pd.DataFrame({'Z2': z2_labeled, 'CAP': cap_labeled})
    df_exp3['Z2_Quintile'] = pd.qcut(df_exp3['Z2'], 5, labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (Highest)'])
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Z2_Quintile', y='CAP', data=df_exp3, palette='Blues')
    plt.title(f"Hepatic Steatosis Recovery: CAP Score by Z2 Quintile\nSpearman ρ = {rho:.3f}")
    plt.ylabel("CAP Score (dB/m)")
    plt.xlabel("Z2 Coordinate Quintile")
    plt.axhline(y=248, color='r', linestyle='--', label='Steatosis Threshold (248 dB/m)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "exp3_z2_vs_cap.png"), dpi=300)
    plt.close()

def run_exp4_quadrant_stats(df_derived, z_all, conformal):
    print("\n--- Running Experiment 4: Phenotypic Quadrant Characterization ---")
    z1_thresh = conformal.z1_threshold
    z2_thresh = conformal.z2_threshold
    
    quadrants = []
    for i in range(len(z_all)):
        q = conformal.get_quadrant(z_all[i, 0], z_all[i, 1])
        quadrants.append(q)
    
    df_derived['Quadrant'] = quadrants
    q_names = {0: 'MHNW', 1: 'IR-Dominant', 2: 'Steatosis-Dominant', 3: 'Dual-Burden'}
    df_derived['Phenotype'] = df_derived['Quadrant'].map(q_names)
    
    freq = df_derived['Phenotype'].value_counts(normalize=True) * 100
    print("Population Frequencies (%):")
    print(freq)
    
    stats = df_derived.groupby('Phenotype')[['homa_ir', 'triglycerides_mg_dL', 'alt_U_L', 'waist_cm', 'bmi']].mean().round(2)
    stats.to_csv(os.path.join(RESULTS_DIR, "exp4_quadrant_stats.csv"))
    print("Quadrant Stats:")
    print(stats)
    
    plt.figure(figsize=(10, 8))
    colors = {0: '#00c47d', 1: '#f5a623', 2: '#3d8ef8', 3: '#e8394a'}
    sns.scatterplot(x=z_all[:, 0], y=z_all[:, 1], hue=df_derived['Quadrant'], palette=colors, alpha=0.6)
    plt.axvline(x=z1_thresh, color='k', linestyle='--', alpha=0.5)
    plt.axhline(y=z2_thresh, color='k', linestyle='--', alpha=0.5)
    plt.xlabel('Z1 (Insulin Resistance Axis)')
    plt.ylabel('Z2 (Hepatic Steatosis Axis)')
    plt.title('Latent Metabolic Coordinate Space by Phenotype')
    
    handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i], markersize=10, label=q_names[i]) for i in range(4)]
    plt.legend(handles=handles, title='Phenotype')
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "exp4_latent_scatter.png"), dpi=300)
    plt.close()

def run_exp5_conformal_coverage(df_derived, z_all, y_all, conformal):
    print("\n--- Running Experiment 5: Conformal Impossibility Proof ---")
    from sklearn.linear_model import LogisticRegression
    alpha = 0.10
    
    base = LogisticRegression(C=1.0, random_state=99)
    base.fit(z_all, y_all)
    probs = base.predict_proba(z_all)
    scores = np.array([1.0 - probs[i, int(y_all[i])] for i in range(len(y_all))])
    n = len(y_all)
    q_marginal = np.quantile(scores, np.clip(np.ceil((n + 1) * (1 - alpha)) / n, 0.0, 1.0))
    
    marginal_pred_sets = np.zeros((len(z_all), 2), dtype=bool)
    marginal_pred_sets[:, 0] = probs[:, 0] >= (1.0 - q_marginal)
    marginal_pred_sets[:, 1] = probs[:, 1] >= (1.0 - q_marginal)
    empty = ~marginal_pred_sets[:, 0] & ~marginal_pred_sets[:, 1]
    marginal_pred_sets[empty, np.argmax(probs[empty], axis=1)] = True
    
    _, mondrian_pred_sets = conformal.predict(z_all, alpha=alpha)
    
    results = []
    q_names = {0: 'MHNW', 1: 'IR-Dominant', 2: 'Steatosis-Dominant', 3: 'Dual-Burden'}
    
    for q in range(4):
        idx = np.where(df_derived['Quadrant'] == q)[0]
        y_q = y_all[idx]
        if len(y_q) == 0: continue
        
        marg_cov = np.mean([marginal_pred_sets[i, int(y_all[i])] for i in idx])
        mond_cov = np.mean([mondrian_pred_sets[i, int(y_all[i])] for i in idx])
        
        results.append({
            'Phenotype': q_names[q],
            'N': len(idx),
            'Marginal_Coverage': round(marg_cov, 4),
            'Mondrian_Coverage': round(mond_cov, 4),
            'Nominal_Target': 1.0 - alpha
        })
        
    df_res = pd.DataFrame(results)
    df_res.to_csv(os.path.join(RESULTS_DIR, "exp5_coverage_comparison.csv"), index=False)
    print(df_res.to_string())

def run_exp6_counterfactuals(df_derived, z_all, scaler, model, conformal):
    print("\n--- Running Experiment 6: Counterfactual Intervention Pathways ---")
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src_code.counterfactual.counterfactual import metabolic_quadrant_counterfactual
    
    pathways = {}
    q_names = {1: 'IR-Dominant', 2: 'Steatosis-Dominant', 3: 'Dual-Burden'}
    
    features = [
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL", "hdl_mg_dL",
        "ast_U_L", "alt_U_L", "ggt_U_L", "bmi", "waist_cm", "platelets_1000_uL",
        "tyg", "ast_alt", "tg_hdl", "aip"
    ]
    
    for q in [1, 2, 3]:
        idx = np.where(df_derived['Quadrant'] == q)[0]
        if len(idx) == 0: continue
        
        z_q = z_all[idx]
        dists = np.sqrt(z_q[:, 0]**2 + z_q[:, 1]**2)
        rep_idx = idx[np.argmax(dists)]
        
        z_current = z_all[rep_idx]
        x_raw = df_derived.iloc[rep_idx][features].values.astype(float)
        
        res = metabolic_quadrant_counterfactual(model, scaler, z_current, x_raw, conformal.z1_threshold, conformal.z2_threshold)
        pathways[q_names[q]] = res
        
    with open(os.path.join(RESULTS_DIR, "exp6_intervention_pathways.json"), "w") as f:
        json.dump(pathways, f, indent=4)
    print("Counterfactual pathways saved to JSON.")

def main():
    print("Loading data and models...")
    df = load_data()
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    conformal = joblib.load(os.path.join(models_dir, "conformal_surface.pkl"))
    
    X_all, u_all, h_all, m_all, y_all, df_derived_all, _, _ = preprocess_data(df, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    model = iVAE_MetabolicStateModel()
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_all, dtype=torch.float32), torch.tensor(u_all, dtype=torch.float32))
        z_all = mu_q.numpy()

    run_exp3_z2_vs_cap(df_derived_all, z_all, m_all)
    run_exp4_quadrant_stats(df_derived_all, z_all, conformal)
    run_exp5_conformal_coverage(df_derived_all, z_all, y_all, conformal)
    run_exp6_counterfactuals(df_derived_all, z_all, scaler, model, conformal)
    
    print("\nAll experiments completed successfully. Results saved in /results/")

if __name__ == "__main__":
    main()
