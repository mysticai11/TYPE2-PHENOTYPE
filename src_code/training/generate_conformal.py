import os
import sys
import torch
import numpy as np
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data
from src_code.model.ivae import iVAE_MetabolicStateModel
from src_code.validation.conformal_surface import fit_conformal_risk_surface
import joblib

def generate():
    df = load_data()
    df_train, df_temp = train_test_split(df, test_size=0.30, random_state=42)
    df_val, df_test = train_test_split(df_temp, test_size=0.50, random_state=42)
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    
    X_val, u_val, h_val, m_val, y_val, df_derived_val, _, _ = preprocess_data(df_val, scaler=scaler, u_encoder=u_encoder, is_train=False)
    X_test, u_test, h_test, m_test, y_test, df_derived_test, _, _ = preprocess_data(df_test, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    model = iVAE_MetabolicStateModel(beta=4.0, lambda_anchor=0.5)
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()
    
    with torch.no_grad():
        mu_q_val, _ = model.encoder(torch.tensor(X_val, dtype=torch.float32), torch.tensor(u_val, dtype=torch.float32))
        z_cal = mu_q_val.numpy()
        mu_q_test, _ = model.encoder(torch.tensor(X_test, dtype=torch.float32), torch.tensor(u_test, dtype=torch.float32))
        z_test = mu_q_test.numpy()
        
    res, _ = fit_conformal_risk_surface(z_cal, y_val, z_test, y_test)
    print("Conformal surface generated:", res)

if __name__ == "__main__":
    generate()
