import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import xgboost as xgb
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import RobustScaler, OneHotEncoder

# --- 1. Load Data ---
raw_path = os.path.join(os.path.dirname(__file__), "raw_nhanes_merged.csv")
print(f"Loading merged dataset from {raw_path}...")
df_raw = pd.read_csv(raw_path)

# Ensure required target columns exist
cap_col = "LUXCAPM"
dexa_col = "DXDVFAT" # Visceral Fat
bmi_col = "BMXBMI"
age_col = "RIDAGEYR"

# Base filters (Adults >= 20)
if age_col in df_raw.columns:
    df_adults = df_raw[df_raw[age_col] >= 20]
else:
    df_adults = df_raw.copy()

total_adults = len(df_adults)

# Normal BMI Filter
if bmi_col in df_adults.columns:
    df_normal_bmi = df_adults[(df_adults[bmi_col] >= 18.5) & (df_adults[bmi_col] < 25.0)]
else:
    df_normal_bmi = df_adults.copy()

normal_bmi_count = len(df_normal_bmi)

# CAP labeled cohort
if cap_col in df_normal_bmi.columns:
    df_cap = df_normal_bmi.dropna(subset=[cap_col])
else:
    df_cap = pd.DataFrame()

cap_count = len(df_cap)

# DEXA labeled cohort
if dexa_col in df_normal_bmi.columns:
    df_dexa = df_normal_bmi.dropna(subset=[dexa_col])
else:
    df_dexa = pd.DataFrame()

dexa_count = len(df_dexa)

# Both labeled cohort
if not df_cap.empty and not df_dexa.empty:
    df_both = df_normal_bmi.dropna(subset=[cap_col, dexa_col])
else:
    df_both = pd.DataFrame()

both_count = len(df_both)

print("\n--- Cohort Sizes ---")
print(f"Total Adults (>=20): {total_adults}")
print(f"Normal-BMI Adults: {normal_bmi_count}")
print(f"Normal-BMI with CAP: {cap_count}")
print(f"Normal-BMI with DEXA VAT: {dexa_count}")
print(f"Normal-BMI with BOTH: {both_count}")

# We need CAP prediction. So we continue with df_cap.
if cap_count < 50:
    print("\n[!] Not enough CAP data to proceed with prediction experiments.")
    exit(0)

# --- 2. Variable Extraction and Mapping ---
# Let's map the variables needed for prediction, mirroring nhanes_loader.py logic.
mapping = {
    'RIDAGEYR': 'age',
    'RIAGENDR': 'sex',
    'RIDRETH1': 'ancestry_proxy',
    'BMXBMI': 'bmi',
    'BMXWAIST': 'waist_cm',
    'LBXTR': 'triglycerides_mg_dL',     # TRIGLY file (LBXSTR is wrong)
    'LBDHDD': 'hdl_mg_dL',
    'LBXSATSI': 'ast_U_L',               # BIOPRO SI units
    'LBXSAL': 'alt_U_L',                 # BIOPRO (LBXSAT is wrong)
    'LBXSGTSI': 'ggt_U_L',
    'LBXGLU': 'fasting_glucose_mg_dL',
    'LBXIN': 'fasting_insulin_uU_mL',    # Align with nhanes_loader convention
    'LBXPLTSI': 'platelets_1000_uL',
    'LUXCAPM': 'cap_score'
}

df_features = pd.DataFrame()
for old, new in mapping.items():
    if old in df_cap.columns:
        df_features[new] = df_cap[old]

# Drop rows missing critical features for the experiment
df_features = df_features.dropna()
final_cap_count = len(df_features)
print(f"\nFinal CAP cohort (no missing biomarkers): {final_cap_count}")

# Compute HOMA-IR
df_features['homa_ir'] = (df_features['fasting_glucose_mg_dL'] * df_features['fasting_insulin_uU_mL']) / 405.0

# --- 3. Correlation Analysis ---
print("\n--- Spearman Correlations with CAP ---")
cols_to_check = ['triglycerides_mg_dL', 'ggt_U_L', 'alt_U_L', 'homa_ir', 'bmi', 'waist_cm']
for col in cols_to_check:
    if col in df_features.columns:
        rho, p = stats.spearmanr(df_features['cap_score'], df_features[col])
        print(f"CAP vs {col.ljust(22)}: rho = {rho:.3f} (p={p:.1e})")

# --- 4. Predictive Modeling Baseline ---
# Prepare X and y
y = df_features['cap_score'].values

# Encode categorical variables (ancestry_proxy)
df_model = df_features.copy()
if 'ancestry_proxy' in df_model.columns:
    encoder = OneHotEncoder(sparse_output=False, drop='first')
    anc_encoded = encoder.fit_transform(df_model[['ancestry_proxy']])
    anc_cols = [f"anc_{i}" for i in range(anc_encoded.shape[1])]
    df_model[anc_cols] = anc_encoded
    df_model = df_model.drop(columns=['ancestry_proxy', 'cap_score'])
else:
    df_model = df_model.drop(columns=['cap_score'])

X = df_model.values

# Train / Test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale X for linear models
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\n--- Baseline Model Evaluation ---")

# 1. Linear Regression
lr = LinearRegression()
lr.fit(X_train_scaled, y_train)
lr_preds = lr.predict(X_test_scaled)
lr_r2 = r2_score(y_test, lr_preds)
lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))
print(f"Linear Regression: R^2 = {lr_r2:.3f}, RMSE = {lr_rmse:.3f}")

# 2. Elastic Net
en = ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42)
en.fit(X_train_scaled, y_train)
en_preds = en.predict(X_test_scaled)
en_r2 = r2_score(y_test, en_preds)
en_rmse = np.sqrt(mean_squared_error(y_test, en_preds))
print(f"Elastic Net:       R^2 = {en_r2:.3f}, RMSE = {en_rmse:.3f}")

# 3. XGBoost
xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
xgb_model.fit(X_train, y_train)
xgb_preds = xgb_model.predict(X_test)
xgb_r2 = r2_score(y_test, xgb_preds)
xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_preds))
print(f"XGBoost:           R^2 = {xgb_r2:.3f}, RMSE = {xgb_rmse:.3f}")

# Simple mean baseline
mean_pred = np.full_like(y_test, np.mean(y_train))
mean_r2 = r2_score(y_test, mean_pred)
mean_rmse = np.sqrt(mean_squared_error(y_test, mean_pred))
print(f"Baseline (Mean):   R^2 = {mean_r2:.3f}, RMSE = {mean_rmse:.3f}")

print("\nExperiment script completed.")
