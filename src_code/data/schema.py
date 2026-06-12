class FeatureSchema:
    RAW_INPUTS = [
        "fasting_glucose_mg_dL",
        "fasting_insulin_uU_mL",
        "triglycerides_mg_dL",
        "hdl_mg_dL",
        "ast_U_L",
        "alt_U_L",
        "ggt_U_L",
        "bmi",
        "waist_cm",
        "platelets_1000_uL"
    ]

    DERIVED_INDICES = ["tyg", "ast_alt", "tg_hdl", "aip"]
    FEATURE_COLS = RAW_INPUTS + DERIVED_INDICES
    DEMO_COLS = ["age", "sex", "ancestry_proxy"]
