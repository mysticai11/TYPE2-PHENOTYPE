import pandas as pd
import numpy as np
import os

def generate_mock_nhanes(n_samples=4200, seed=42):
    np.random.seed(seed)
    age = np.random.uniform(20, 79, n_samples)
    sex = np.random.choice([1, 2], n_samples)
    ancestry_proxy = np.random.choice([1, 2, 3], n_samples, p=[0.6, 0.2, 0.2])
    latent_ir = np.random.normal(0, 1, n_samples)
    latent_lipid = np.random.normal(0, 1, n_samples)
    fpg = np.clip(np.random.normal(90, 10, n_samples) + latent_ir * 15, 60, 200)
    insulin = np.clip(np.random.lognormal(2.0, 0.5, n_samples) + latent_ir * 8, 2, 100)
    tg = np.clip(np.random.lognormal(4.5, 0.4, n_samples) + latent_lipid * 40 + latent_ir * 20, 30, 800)
    hdl = np.clip(np.random.normal(60, 15, n_samples) - latent_lipid * 10 - latent_ir * 5, 20, 120)
    ast = np.clip(np.random.lognormal(3.0, 0.3, n_samples) + latent_ir * 5, 10, 100)
    alt = np.clip(ast * np.random.uniform(0.7, 1.3, n_samples) + latent_ir * 5, 10, 150)
    ggt = np.clip(alt * np.random.uniform(0.8, 1.5, n_samples) + latent_lipid * 10, 10, 200)
    bmi = np.random.uniform(18.5, 24.9, n_samples)
    waist_base = np.where(sex == 1, 85, 75)
    waist = np.clip(np.random.normal(waist_base, 8, n_samples) + (bmi - 22) * 2 + latent_ir * 5, 60, 110)
    platelets = np.random.normal(250, 50, n_samples)
    df = pd.DataFrame({
        "fasting_glucose_mg_dL": fpg,
        "fasting_insulin_uU_mL": insulin,
        "triglycerides_mg_dL": tg,
        "hdl_mg_dL": hdl,
        "ast_U_L": ast,
        "alt_U_L": alt,
        "ggt_U_L": ggt,
        "bmi": bmi,
        "waist_cm": waist,
        "platelets_1000_uL": platelets,
        "age": age,
        "sex": sex,
        "ancestry_proxy": ancestry_proxy
    })
    homa_ir_proxy = (insulin * fpg) / 405
    tyg_proxy = np.log(tg * fpg / 2)
    df["ir_label"] = ((homa_ir_proxy > 2.5) & (tyg_proxy >= 8.5)).astype(int)
    df["cap_score"] = np.nan # Mock has no CAP
    return df

def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "raw_nhanes_merged.csv")
    if not os.path.exists(data_path):
        print("Authentic data not found, falling back to mock generator.")
        return generate_mock_nhanes()
        
    df = pd.read_csv(data_path)
    
    # Filter for adults
    df = df[df["RIDAGEYR"] >= 18]
    
    # Filter for normal BMI
    df = df[(df["BMXBMI"] >= 18.5) & (df["BMXBMI"] <= 24.9)]
    
    # Rename columns
    rename_map = {
        "RIDAGEYR": "age",
        "RIAGENDR": "sex",
        "RIDRETH1": "ancestry_proxy",
        "BMXBMI": "bmi",
        "BMXWAIST": "waist_cm",
        "LBXGLU": "fasting_glucose_mg_dL",
        "LBXIN": "fasting_insulin_uU_mL",
        "LBXTR": "triglycerides_mg_dL",
        "LBDHDD": "hdl_mg_dL",
        "LBXSATSI": "ast_U_L",
        "LBXSAL": "alt_U_L",
        "LBXSGTSI": "ggt_U_L",
        "LBXPLTSI": "platelets_1000_uL"
    }
    
    # If LUXCAPM exists, map it. Otherwise it will be created as NaN.
    if "LUXCAPM" in df.columns:
        rename_map["LUXCAPM"] = "cap_score"
        
    df = df.rename(columns=rename_map)
    
    # Keep only required clinical columns (do NOT dropna on cap_score)
    required_cols = list({v for k, v in rename_map.items() if k != "LUXCAPM"})
    df = df.dropna(subset=required_cols)
    
    if "cap_score" not in df.columns:
        df["cap_score"] = np.nan
        
    homa_ir_proxy = (df["fasting_insulin_uU_mL"] * df["fasting_glucose_mg_dL"]) / 405.0
    tyg_proxy = np.log((df["triglycerides_mg_dL"] * df["fasting_glucose_mg_dL"]) / 2.0)
    df["ir_label"] = ((homa_ir_proxy > 2.5) & (tyg_proxy >= 8.5)).astype(int)
    
    print(f"Loaded authentic NHANES data: {len(df)} samples matching normal-BMI criteria.")
    return df
