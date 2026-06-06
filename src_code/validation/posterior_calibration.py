import torch
import numpy as np
from sklearn.metrics import roc_auc_score

def posterior_uncertainty_calibration(model, X_val, u_val, ir_label_val) -> dict:
    model.eval()
    with torch.no_grad():
        x_t = torch.tensor(X_val, dtype=torch.float32)
        u_t = torch.tensor(u_val, dtype=torch.float32)
        mu_q, logvar_q = model.encoder(x_t, u_t)
    sigma_z1 = logvar_q[:, 0].exp().numpy()
    mu_q_np = mu_q.numpy()
    lo_unc = np.percentile(sigma_z1, 25)
    hi_unc = np.percentile(sigma_z1, 75)
    low_mask = sigma_z1 <= lo_unc
    high_mask = sigma_z1 >= hi_unc
    if len(np.unique(ir_label_val[low_mask])) > 1:
        auroc_low = roc_auc_score(ir_label_val[low_mask], mu_q_np[low_mask, 0])
    else:
        auroc_low = 0.5
    if len(np.unique(ir_label_val[high_mask])) > 1:
        auroc_high = roc_auc_score(ir_label_val[high_mask], mu_q_np[high_mask, 0])
    else:
        auroc_high = 0.5
    return {"auroc_low_uncertainty_patients": round(float(auroc_low), 4), "auroc_high_uncertainty_patients": round(float(auroc_high), 4), "difference": round(float(auroc_low - auroc_high), 4), "interpretation": "positive difference = uncertainty is meaningful"}
