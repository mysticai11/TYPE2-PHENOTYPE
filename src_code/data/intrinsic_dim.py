import sys
import os
from skdim.id import TwoNN, MLE

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import derive_features, FEATURE_COLS

def estimate_intrinsic_dimensionality(X):
    try:
        twonn = TwoNN()
        id_twonn = twonn.fit(X).dimension_
        print(f"TwoNN estimator ID: {id_twonn:.2f}")
    except Exception as e:
        pass
    try:
        mle = MLE()
        id_mle = mle.fit(X).dimension_
        print(f"MLE estimator ID: {id_mle:.2f}")
    except Exception as e:
        pass

if __name__ == "__main__":
    df = load_data()
    df_derived = derive_features(df)
    from sklearn.preprocessing import RobustScaler
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(df_derived[FEATURE_COLS].values)
    estimate_intrinsic_dimensionality(X_scaled)
