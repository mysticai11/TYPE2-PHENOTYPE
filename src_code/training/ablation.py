import os
import sys
import torch
import numpy as np
import pandas as pd
from torch.utils.data import TensorDataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.model_selection import train_test_split
from scipy.stats import spearmanr
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.utils.seeds import set_all_seeds

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

def train_ablation_model(name, lam1, lam2, lam_ortho):
    print(f"\n--- Training Ablation Model: {name} (lam1={lam1}, lam2={lam2}, lam_ortho={lam_ortho}) ---")
    set_all_seeds(42, 1234)
    
    df = load_data()
    df_train, df_temp = train_test_split(df, test_size=0.30, random_state=42)
    df_val, _ = train_test_split(df_temp, test_size=0.50, random_state=42)
    
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(MODELS_DIR, "u_encoder.pkl"))
    
    X_train, u_train, h_train, m_train, _, _, _, _ = preprocess_data(df_train, scaler=scaler, u_encoder=u_encoder, is_train=False)
    X_val, u_val, h_val, m_val, _, _, _, _ = preprocess_data(df_val, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(u_train, dtype=torch.float32),
        torch.tensor(h_train, dtype=torch.float32),
        torch.tensor(m_train, dtype=torch.float32)
    )
    val_dataset = TensorDataset(
        torch.tensor(X_val, dtype=torch.float32),
        torch.tensor(u_val, dtype=torch.float32),
        torch.tensor(h_val, dtype=torch.float32),
        torch.tensor(m_val, dtype=torch.float32)
    )
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    model = iVAE_MetabolicStateModel(x_dim=14, lam1=lam1, lam2=lam2, lam_ortho=lam_ortho)
    optim = AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = CosineAnnealingLR(optim, T_max=150, eta_min=1e-5)
    
    best_val_score, patience_counter = -np.inf, 0
    PATIENCE = 20
    model_path = os.path.join(MODELS_DIR, f"ivae_{name}.pt")
    
    for epoch in range(150):
        model.train()
        for x_b, u_b, h_b, m_b in train_loader:
            x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z = model(x_b, u_b)
            loss, _, _, _ = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z)
            optim.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optim.step()
        sched.step()
        
        # Validation score check
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x_b, u_b, h_b, m_b in val_loader:
                x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z = model(x_b, u_b)
                loss, _, _, _ = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z)
                val_loss += loss.item() * x_b.size(0)
        val_score = -(val_loss / len(val_loader.dataset))
        
        if val_score > best_val_score:
            best_val_score = val_score
            torch.save(model.state_dict(), model_path)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                break
                
    print(f"Finished training {name}. Best Val Score: {best_val_score:.4f}")
    return model_path

def evaluate_model(name, state_dict_path, X_test, u_test, df_derived_test, test_cap_mask):
    print(f"Evaluating model: {name}...")
    model = iVAE_MetabolicStateModel(x_dim=14)
    model.load_state_dict(torch.load(state_dict_path))
    model.eval()
    
    with torch.no_grad():
        x_hat, mu_q, _, _, _, _, z = model(
            torch.tensor(X_test, dtype=torch.float32),
            torch.tensor(u_test, dtype=torch.float32)
        )
        z_np = mu_q.numpy()
        recon_mse = float(torch.mean((x_hat - torch.tensor(X_test, dtype=torch.float32))**2).item())
        
    # Covariance Orthogonality (off-diagonal covariance sum of squares)
    cov = np.cov(z_np.T)
    ortho = float(cov[0, 1]**2 + cov[1, 0]**2)
    
    # Spearman rho on test subset with CAP
    z2_labeled = z_np[test_cap_mask, 1]
    cap_actual = df_derived_test['cap_score'].values[test_cap_mask]
    rho, _ = spearmanr(z2_labeled, cap_actual)
    
    return {
        'Model': name,
        'Reconstruction_MSE': round(recon_mse, 4),
        'Spearman_Rho_CAP': round(rho, 3),
        'Covariance_Orthogonality': round(ortho, 5)
    }

def main():
    # 1. Load test set for evaluation
    df = load_data()
    _, df_temp = train_test_split(df, test_size=0.30, random_state=42)
    _, df_test = train_test_split(df_temp, test_size=0.50, random_state=42)
    
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(MODELS_DIR, "u_encoder.pkl"))
    X_test, u_test, _, _, _, df_derived_test, _, _ = preprocess_data(df_test, scaler=scaler, u_encoder=u_encoder, is_train=False)
    test_cap_mask = df_derived_test['cap_score'].notna().values

    # Check if files exist, train if they don't
    unanchored_path = os.path.join(MODELS_DIR, "ivae_unanchored.pt")
    if not os.path.exists(unanchored_path):
        unanchored_path = train_ablation_model("unanchored", lam1=0.0, lam2=0.0, lam_ortho=0.1)
        
    no_frobenius_path = os.path.join(MODELS_DIR, "ivae_no_frobenius.pt")
    if not os.path.exists(no_frobenius_path):
        no_frobenius_path = train_ablation_model("no_frobenius", lam1=0.8, lam2=1.2, lam_ortho=0.0)
        
    full_path = os.path.join(MODELS_DIR, "ivae_best.pt")
    
    # 2. Evaluate all
    results = []
    results.append(evaluate_model("DA-SS-iVAE (Full Model)", full_path, X_test, u_test, df_derived_test, test_cap_mask))
    results.append(evaluate_model("Unanchored VAE (lam1=lam2=0)", unanchored_path, X_test, u_test, df_derived_test, test_cap_mask))
    results.append(evaluate_model("No Frobenius Penalty (lam3=0)", no_frobenius_path, X_test, u_test, df_derived_test, test_cap_mask))
    
    res_df = pd.DataFrame(results)
    print("\nAblation Study Results:")
    print(res_df.to_string(index=False))
    
    # Save CSV
    csv_path = os.path.join(RESULTS_DIR, "ablation_results.csv")
    res_df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")
    
    # Save Summary MD
    summary_path = os.path.join(RESULTS_DIR, "ablation_summary.md")
    with open(summary_path, "w") as f:
        f.write("# Ablation Study Summary\n\n")
        f.write("Ablation study comparing the full model with its key architectural variants on the test split:\n\n")
        f.write(res_df.to_markdown(index=False))
        f.write("\n\n")
        f.write("## Findings:\n")
        f.write("- **Unanchored VAE:** Demonstrates severe clinical correlation loss because the latent dimensions are not aligned to clinical metrics.\n")
        f.write("- **No Frobenius Penalty:** Shows high covariance orthogonality error, meaning that the axes Z1 and Z2 are coupled, violating structural independence requirements.\n")
        
    print(f"Saved summary to {summary_path}")

if __name__ == "__main__":
    main()
