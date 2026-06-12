import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, OneHotEncoder
import joblib
import os

from src_code.data.schema import FeatureSchema

RAW_INPUTS = FeatureSchema.RAW_INPUTS
DERIVED_INDICES = FeatureSchema.DERIVED_INDICES
FEATURE_COLS = FeatureSchema.FEATURE_COLS

def derive_features(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out["homa_ir"] = (df_out["fasting_insulin_uU_mL"] * df_out["fasting_glucose_mg_dL"]) / 405.0
    df_out["tyg"] = np.log((df_out["triglycerides_mg_dL"] * df_out["fasting_glucose_mg_dL"]) / 2.0)
    df_out["tg_hdl"] = df_out["triglycerides_mg_dL"] / df_out["hdl_mg_dL"]
    df_out["aip"] = np.log10(df_out["tg_hdl"])
    df_out["ast_alt"] = df_out["ast_U_L"] / df_out["alt_U_L"]
    y = (0.953 * np.log(df_out["triglycerides_mg_dL"]) + 0.139 * df_out["bmi"] +
         0.718 * np.log(df_out["ggt_U_L"]) + 0.053 * df_out["waist_cm"] - 15.745)
    df_out["fli"] = (np.exp(y) / (1 + np.exp(y))) * 100
    return df_out

def encode_demographics(df: pd.DataFrame, encoder=None, is_train=False):
    age = df[["age"]].values
    sex = (df["sex"] == 2).astype(float).values.reshape(-1, 1)
    ancestry = df[["ancestry_proxy"]]
    if is_train:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        anc_encoded = encoder.fit_transform(ancestry)
    else:
        anc_encoded = encoder.transform(ancestry)
    u_encoded = np.hstack([age / 100.0, sex, anc_encoded[:, 1:]])
    return u_encoded, encoder

def preprocess_data(df: pd.DataFrame, scaler=None, u_encoder=None, is_train=False):
    df_derived = derive_features(df)
    X_raw = df_derived[FEATURE_COLS]
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    os.makedirs(models_dir, exist_ok=True)
    if is_train:
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X_raw)
        joblib.dump(scaler, os.path.join(models_dir, "scaler.pkl"))
    else:
        X_scaled = scaler.transform(X_raw)
    u_encoded, u_encoder = encode_demographics(df_derived, u_encoder, is_train)
    if is_train:
        joblib.dump(u_encoder, os.path.join(models_dir, "u_encoder.pkl"))
        
    homa_ir = df_derived["homa_ir"].values
    cap = df_derived["cap_score"].values
    
    # Standardize targets for stable training
    h_homa = (homa_ir - np.nanmean(homa_ir)) / (np.nanstd(homa_ir) + 1e-8)
    h_cap = (cap - np.nanmean(cap)) / (np.nanstd(cap) + 1e-8)
    
    h_target = np.column_stack([h_homa, np.nan_to_num(h_cap, 0)])
    h_mask = np.column_stack([np.ones_like(homa_ir), ~np.isnan(cap)])
    
    return X_scaled, u_encoded, h_target, h_mask, df_derived["ir_label"].values, df_derived, scaler, u_encoder
