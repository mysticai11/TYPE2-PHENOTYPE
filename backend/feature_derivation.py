import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src_code.data.preprocess import derive_features, encode_demographics
from src_code.data.schema import FeatureSchema

FEATURE_COLS = FeatureSchema.FEATURE_COLS

def get_derived_features(input_data: dict) -> dict:
    if input_data.get("ggt_U_L") is None:
        input_data["ggt_U_L"] = input_data["alt_U_L"] * 1.2
    if input_data.get("platelets_1000_uL") is None:
        input_data["platelets_1000_uL"] = 250.0
    df = pd.DataFrame([input_data])
    df_derived = derive_features(df)
    features = df_derived[FEATURE_COLS].iloc[0].values.tolist()
    return {"features": features, "homa_ir": float(df_derived["homa_ir"].iloc[0]), "tyg": float(df_derived["tyg"].iloc[0]), "df_derived": df_derived}

def get_demographics(input_data: dict, u_encoder) -> list:
    df = pd.DataFrame([input_data])
    u_encoded, _ = encode_demographics(df, u_encoder, is_train=False)
    return u_encoded[0].tolist()
