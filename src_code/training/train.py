import os
import sys
import torch
import numpy as np
from torch.utils.data import TensorDataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.utils.seeds import set_all_seeds

def evaluate_validation(model, val_loader):
    model.eval()
    val_loss = 0.0
    with torch.no_grad():
        for x_b, u_b, h_b, m_b in val_loader:
            x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z = model(x_b, u_b)
            loss, _, _, _ = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat)
            val_loss += loss.item() * x_b.size(0)
    return - (val_loss / len(val_loader.dataset))

def train_model(best_params=None):
    set_all_seeds(42, 1234)
    if best_params is None: best_params = {"beta": 4.0, "lambda_anchor": 0.5, "k": 2}
    best_lr = best_params.pop("lr", 1e-3)
    df = load_data()
    df_train, df_temp = train_test_split(df, test_size=0.30, random_state=42)
    df_val, df_test = train_test_split(df_temp, test_size=0.50, random_state=42)
    X_train, u_train, h_train, m_train, y_train, df_derived_train, scaler, u_encoder = preprocess_data(df_train, is_train=True)
    X_val, u_val, h_val, m_val, y_val, df_derived_val, _, _ = preprocess_data(df_val, scaler=scaler, u_encoder=u_encoder, is_train=False)
    X_test, u_test, h_test, m_test, y_test, df_derived_test, _, _ = preprocess_data(df_test, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(u_train, dtype=torch.float32), torch.tensor(h_train, dtype=torch.float32), torch.tensor(m_train, dtype=torch.float32))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(u_val, dtype=torch.float32), torch.tensor(h_val, dtype=torch.float32), torch.tensor(m_val, dtype=torch.float32))
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    model = iVAE_MetabolicStateModel(**best_params)
    optim = AdamW(model.parameters(), lr=best_lr, weight_decay=1e-4)
    sched = CosineAnnealingLR(optim, T_max=150, eta_min=1e-5)
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    os.makedirs(models_dir, exist_ok=True)
    best_val_score, patience_counter = -np.inf, 0
    PATIENCE = 20
    
    print("Starting training...")
    for epoch in range(150):
        model.train()
        epoch_loss = 0
        for x_b, u_b, h_b, m_b in train_loader:
            x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z = model(x_b, u_b)
            loss, recon, kl, anchor = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat)
            optim.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optim.step()
            epoch_loss += loss.item()
        sched.step()
        val_score = evaluate_validation(model, val_loader)
        if val_score > best_val_score:
            best_val_score = val_score
            torch.save(model.state_dict(), os.path.join(models_dir, "ivae_best.pt"))
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"Early stopping at epoch {epoch}")
                break
        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d} | Train Loss: {epoch_loss/len(train_loader):.4f} | Val Score: {val_score:.4f}")
    
    print("Training complete.")
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    assert model.anchor.verify_monotonicity(), "Anchor monotonicity check FAILED"
    print("Anchor monotonicity check passed.")

    # Generate Conformal Surface
    try:
        from src_code.validation.conformal_surface import fit_conformal_risk_surface
        print("Generating conformal surface...")
        model.eval()
        with torch.no_grad():
            mu_q_val, _ = model.encoder(torch.tensor(X_val, dtype=torch.float32), torch.tensor(u_val, dtype=torch.float32))
            z_cal = mu_q_val.numpy()
            mu_q_test, _ = model.encoder(torch.tensor(X_test, dtype=torch.float32), torch.tensor(u_test, dtype=torch.float32))
            z_test = mu_q_test.numpy()
        fit_conformal_risk_surface(z_cal, y_val, z_test, y_test)
        print("Conformal surface generated and saved.")
    except Exception as e:
        print(f"Failed to generate conformal surface: {e}")
    
if __name__ == "__main__":
    train_model()
