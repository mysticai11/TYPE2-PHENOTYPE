import torch
import numpy as np
from scipy.optimize import brentq

def metabolic_counterfactual(model, z_current: np.ndarray, homa_ir_target: float) -> dict:
    model.eval()
    with torch.no_grad():
        def g(z1_val):
            z1_tensor = torch.tensor([[z1_val]], dtype=torch.float32)
            h_pred = model.anchor(z1_tensor).numpy()[0]
            return h_pred - homa_ir_target
        a, b = -5.0, 5.0
        fa, fb = g(a), g(b)
        if fa * fb > 0:
            a, b = -10.0, 10.0
            fa, fb = g(a), g(b)
            if fa * fb > 0:
                raise ValueError(f"Target HOMA-IR {homa_ir_target} unreachable within latent bounds [-10, 10].")
        z1_cf = brentq(g, a=a, b=b, xtol=1e-6)
    delta_z1 = z1_cf - z_current[0]
    distance = abs(delta_z1)
    return {"z1_current": round(float(z_current[0]), 4), "z1_counterfactual": round(float(z1_cf), 4), "z2_unchanged": round(float(z_current[1]), 4), "delta_z1": round(float(delta_z1), 4), "latent_distance": round(float(distance), 4)}

def metabolic_quadrant_counterfactual(model, scaler, z_current: np.ndarray, x_current_raw: np.ndarray, z1_threshold: float, z2_threshold: float) -> dict:
    model.eval()
    epsilon = 0.05
    z1_cf = min(z_current[0], z1_threshold - epsilon)
    z2_cf = min(z_current[1], z2_threshold - epsilon)
    
    distance = np.sqrt((z1_cf - z_current[0])**2 + (z2_cf - z_current[1])**2)
    
    with torch.no_grad():
        x_hat_scaled = model.decoder(torch.tensor([[z1_cf, z2_cf]], dtype=torch.float32)).numpy()[0]
        x_current_scaled = model.decoder(torch.tensor([[z_current[0], z_current[1]]], dtype=torch.float32)).numpy()[0]
        
    x_cf_raw = scaler.inverse_transform([x_hat_scaled])[0]
    x_recon_raw = scaler.inverse_transform([x_current_scaled])[0]
    
    # Calculate deltas between the reconstructions to isolate the effect of Z movement
    delta_raw = x_cf_raw - x_recon_raw
    delta_scaled = x_hat_scaled - x_current_scaled
    
    FEATURE_COLS = [
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL", "hdl_mg_dL",
        "ast_U_L", "alt_U_L", "ggt_U_L", "bmi", "waist_cm", "platelets_1000_uL",
        "tyg", "homa_ir", "fli", "tg_hdl", "aip"
    ]
    
    UNITS = {
        "fasting_glucose_mg_dL": "mg/dL", "fasting_insulin_uU_mL": "uU/mL",
        "triglycerides_mg_dL": "mg/dL", "hdl_mg_dL": "mg/dL",
        "ast_U_L": "U/L", "alt_U_L": "U/L", "ggt_U_L": "U/L",
        "bmi": "kg/m2", "waist_cm": "cm", "platelets_1000_uL": "10^3/uL",
        "tyg": "", "homa_ir": "", "fli": "", "tg_hdl": "", "aip": ""
    }
    
    levers = []
    # We only care about the raw inputs (first 10 features) for interventions
    for i in range(10):
        # We look for features that DECREASED significantly, except HDL which we want to INCREASE
        # Wait, if z1 and z2 decreased, delta_raw is negative. So we take abs(delta_scaled) for ranking magnitude
        # But we only suggest changes > 1%
        if abs(delta_raw[i]) / max(abs(x_recon_raw[i]), 1e-5) > 0.01:
            levers.append({
                "biomarker": FEATURE_COLS[i],
                "delta_raw": round(float(delta_raw[i]), 2),
                "delta_scaled": round(float(delta_scaled[i]), 4),
                "unit": UNITS[FEATURE_COLS[i]]
            })
            
    # Sort by absolute magnitude of scaled change to find the "primary levers"
    levers.sort(key=lambda x: abs(x["delta_scaled"]), reverse=True)
    
    return {
        "z1_current": round(float(z_current[0]), 4),
        "z2_current": round(float(z_current[1]), 4),
        "z1_target": round(float(z1_cf), 4),
        "z2_target": round(float(z2_cf), 4),
        "latent_distance": round(float(distance), 4),
        "levers": levers[:3]  # Top 3 levers
    }
