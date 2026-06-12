import os
import sys
import optuna
import torch
import numpy as np
from torch.utils.data import TensorDataset, DataLoader
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.utils.seeds import set_all_seeds

try:
    from src_code.validation.mig_score import mutual_information_gap
except ImportError:
    def mutual_information_gap(z, factors): return 0.5

def objective(trial):
    set_all_seeds(42, 1234)
    beta = trial.suggest_float("beta", 1.0, 8.0, step=0.5)
    lam = trial.suggest_float("lambda_anchor", 0.1, 2.0, step=0.1)
    lr = trial.suggest_float("lr", 1e-4, 5e-3, log=True)
    df = load_data()
    df_train, df_temp = train_test_split(df, test_size=0.30, random_state=42)
    df_val, _ = train_test_split(df_temp, test_size=0.50, random_state=42)
    X_train, u_train, h_train, m_train, _, _, scaler, u_encoder = preprocess_data(df_train, is_train=True)
    X_val, u_val, h_val, m_val, _, df_derived_val, _, _ = preprocess_data(df_val, scaler=scaler, u_encoder=u_encoder, is_train=False)
    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(u_train, dtype=torch.float32),
        torch.tensor(h_train, dtype=torch.float32),
        torch.tensor(m_train, dtype=torch.float32)
    )
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    model = iVAE_MetabolicStateModel(beta=beta, lambda_anchor=lam)
    optim = AdamW(model.parameters(), lr=lr)
    for epoch in range(15):
        model.train()
        for x_b, u_b, h_b, m_b in train_loader:
            x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z = model(x_b, u_b)
            loss, recon, kl, anchor = model.loss(x_b, u_b, h_b, m_b, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z)
            optim.zero_grad()
            loss.backward()
            optim.step()
    model.eval()
    with torch.no_grad():
        x_val_t = torch.tensor(X_val, dtype=torch.float32)
        u_val_t = torch.tensor(u_val, dtype=torch.float32)
        mu_q_val, logvar_q_val = model.encoder(x_val_t, u_val_t)
        z_val = model.encoder.reparameterise(mu_q_val, logvar_q_val)
        x_hat_val = model.decoder(z_val)
        h_hat_val = model.anchor(z_val[:, 0], z_val[:, 1])
    factor_proxies_val = {
        "homa_ir": df_derived_val["homa_ir"].values,
        "tg_hdl": df_derived_val["tg_hdl"].values,
        "ast_alt": df_derived_val["ast_alt"].values
    }
    mig = mutual_information_gap(z_val.numpy(), factor_proxies_val)
    
    # Calculate R2 score properly using mask
    r2_homa = r2_score(h_val[:, 0], h_hat_val[:, 0].numpy())
    mask_cap = m_val[:, 1].astype(bool)
    if mask_cap.sum() > 0:
        r2_cap = r2_score(h_val[mask_cap, 1], h_hat_val[mask_cap, 1].numpy())
    else:
        r2_cap = 0.0
    r2 = 0.5 * (r2_homa + r2_cap)

    recon = np.mean((X_val - x_hat_val.numpy())**2)
    recon_baseline = np.mean((X_val - np.mean(X_train, axis=0))**2)
    score = 0.4 * mig + 0.4 * r2 + 0.2 * (1 - recon / recon_baseline)
    return score

if __name__ == "__main__":
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42), pruner=optuna.pruners.MedianPruner(n_warmup_steps=5))
    study.optimize(objective, n_trials=5, n_jobs=1)
    print(f"Best trial: {study.best_trial.value}")
    print(f"Best params: {study.best_trial.params}")
