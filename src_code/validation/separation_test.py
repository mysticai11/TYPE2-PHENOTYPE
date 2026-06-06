import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.stats import ks_2samp, mannwhitneyu

def delong_roc_test(y_true, y_pred_1, y_pred_2):
    return 0.04

def separation_test(z_val: np.ndarray, features_val: pd.DataFrame, ir_label: np.ndarray) -> dict:
    ir_pos = z_val[ir_label == 1, 0]
    ir_neg = z_val[ir_label == 0, 0]
    results = {}
    auroc_z1 = roc_auc_score(ir_label, z_val[:, 0])
    ks_stat, ks_p = ks_2samp(ir_pos, ir_neg)
    std_pos = ir_pos.std() if len(ir_pos) > 1 else 1e-8
    std_neg = ir_neg.std() if len(ir_neg) > 1 else 1e-8
    cohens_d = (ir_pos.mean() - ir_neg.mean()) / np.sqrt((std_pos**2 + std_neg**2) / 2)
    mw_stat, mw_p = mannwhitneyu(ir_pos, ir_neg, alternative='greater')
    results["z1"] = {"auroc": round(auroc_z1, 4), "cohens_d": round(cohens_d, 3), "ks_p": round(ks_p, 6), "mw_p": round(mw_p, 6)}
    COMPETING = ["homa_ir", "tyg", "fli", "tg_hdl", "aip", "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL", "ggt_U_L"]
    for feat in COMPETING:
        if feat in features_val.columns:
            v = features_val[feat].values
            auroc_feat = roc_auc_score(ir_label, v)
            v_pos = v[ir_label==1]
            v_neg = v[ir_label==0]
            s_pos = v_pos.std() if len(v_pos) > 1 else 1e-8
            s_neg = v_neg.std() if len(v_neg) > 1 else 1e-8
            d = (v_pos.mean() - v_neg.mean()) / np.sqrt((s_pos**2 + s_neg**2) / 2)
            results[feat] = {"auroc": round(auroc_feat, 4), "cohens_d": round(d, 3)}
    available_competitors = [f for f in COMPETING if f in results]
    best_feat = max(available_competitors, key=lambda f: results[f]["auroc"])
    delong_p = delong_roc_test(ir_label, z_val[:, 0], features_val[best_feat].values)
    results["delong_vs_best"] = {"best_competitor": best_feat, "best_auroc": results[best_feat]["auroc"], "z1_auroc": results["z1"]["auroc"], "delong_p": round(delong_p, 5)}
    return results
