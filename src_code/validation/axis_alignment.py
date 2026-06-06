import numpy as np
import pandas as pd
from scipy.stats import pearsonr

def check_axis_alignment(z_val: np.ndarray, features_val: pd.DataFrame) -> dict:
    results = {}
    for i, axis_name in enumerate(["z1", "z2"]):
        for feat in ["homa_ir", "tyg", "tg_hdl", "fli", "aip"]:
            if feat in features_val.columns:
                r, p = pearsonr(z_val[:, i], features_val[feat])
                results[f"{axis_name}_vs_{feat}"] = {"r": round(r, 3), "p": round(p, 4)}
    return results
