from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
import os
import sys
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.data.nhanes_loader import load_data
from src_code.data.preprocess import preprocess_data

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")

def nonconformity_scores(z, y, model):
    probs = model.predict_proba(z)
    scores = np.zeros(len(y))
    for i, label in enumerate(y):
        scores[i] = 1.0 - probs[i, int(label)]
    return scores

def compute_coverage(z, y, q, model):
    probs = model.predict_proba(z)
    coverage_count = 0
    for i, label in enumerate(y):
        threshold = 1.0 - q
        if probs[i, int(label)] >= threshold:
            coverage_count += 1
        else:
            # check if default prediction includes it
            pred_sets = np.zeros(2, dtype=bool)
            pred_sets[0] = probs[i, 0] >= threshold
            pred_sets[1] = probs[i, 1] >= threshold
            if not pred_sets[0] and not pred_sets[1]:
                pred_sets[np.argmax(probs[i])] = True
            if pred_sets[int(label)]:
                coverage_count += 1
    return coverage_count / len(y) if len(y) > 0 else 0.0

def ancestry_conformal_stratification(z_cal, ir_label_cal, ancestry_cal, z_test, ir_label_test, ancestry_test, alpha=0.10) -> dict:
    results = {}
    base_model = LogisticRegression(C=1.0, random_state=99)
    base_model.fit(z_cal, ir_label_cal)

    # Marginal conformal
    scores_cal = nonconformity_scores(z_cal, ir_label_cal, base_model)
    q_marginal = np.quantile(scores_cal, np.clip(np.ceil((len(scores_cal) + 1) * (1 - alpha)) / len(scores_cal), 0.0, 1.0))

    ancestries = np.unique(ancestry_cal)
    
    for anc in ancestries:
        mask_test = ancestry_test == anc
        cov = compute_coverage(z_test[mask_test], ir_label_test[mask_test], q_marginal, base_model)
        results[f"marginal_coverage_ancestry_{anc}"] = round(float(cov), 4)

    # Mondrian by ancestry
    q_ancestry = {}
    for anc in ancestries:
        mask_cal = ancestry_cal == anc
        if mask_cal.sum() > 0:
            scores_anc = nonconformity_scores(z_cal[mask_cal], ir_label_cal[mask_cal], base_model)
            n_anc = mask_cal.sum()
            q_ancestry[anc] = np.quantile(scores_anc, np.clip(np.ceil((n_anc + 1) * (1 - alpha)) / n_anc, 0, 1))
        else:
            q_ancestry[anc] = q_marginal

    for anc in ancestries:
        mask_test = ancestry_test == anc
        cov = compute_coverage(z_test[mask_test], ir_label_test[mask_test], q_ancestry[anc], base_model)
        results[f"mondrian_coverage_ancestry_{anc}"] = round(float(cov), 4)

    # TV distance per ancestry group
    for anc in ancestries:
        p = np.histogram(z_cal[ancestry_cal == anc, 0], bins=20, density=True, range=(-3, 3))[0]
        q_dist = np.histogram(z_cal[ancestry_cal != anc, 0], bins=20, density=True, range=(-3, 3))[0]
        tv_distance = 0.5 * np.sum(np.abs(p - q_dist)) * (6.0 / 20.0) # Multiply by bin width
        results[f"tv_distance_ancestry_{anc}"] = round(float(tv_distance), 4)

        # Barber et al. lower bound
        pi_G = (ancestry_cal == anc).mean()
        if pi_G > 0:
            lower_bound = (1 - alpha) - tv_distance * (1 - pi_G) / pi_G
            results[f"barber_lower_bound_ancestry_{anc}"] = round(float(lower_bound), 4)
        else:
            results[f"barber_lower_bound_ancestry_{anc}"] = 0.0

    return results

def main():
    print("Loading data for Ancestry Conformal Stratification...")
    df = load_data()
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    scaler = joblib.load(os.path.join(models_dir, "scaler.pkl"))
    u_encoder = joblib.load(os.path.join(models_dir, "u_encoder.pkl"))
    
    import torch
    from src_code.model.ivae import iVAE_MetabolicStateModel
    model = iVAE_MetabolicStateModel(beta=4.0, lambda_anchor=0.5)
    model.load_state_dict(torch.load(os.path.join(models_dir, "ivae_best.pt")))
    model.eval()

    X_all, u_all, _, _, ir_all, _, _, _ = preprocess_data(df, scaler=scaler, u_encoder=u_encoder, is_train=False)
    
    with torch.no_grad():
        mu_q, _ = model.encoder(torch.tensor(X_all, dtype=torch.float32), torch.tensor(u_all, dtype=torch.float32))
        z_all = mu_q.numpy()

    ancestry_all = df['ancestry_proxy'].values

    # Split into cal and test
    z_cal, z_test, ir_cal, ir_test, anc_cal, anc_test = train_test_split(
        z_all, ir_all, ancestry_all, test_size=0.3, random_state=42
    )

    res = ancestry_conformal_stratification(z_cal, ir_cal, anc_cal, z_test, ir_test, anc_test, alpha=0.10)
    
    # Map ancestries
    anc_map = {1.0: "NHW", 2.0: "NHB", 3.0: "NHA"}
    
    print("\nAncestry-Stratified Conformal Results:")
    for anc_code, name in anc_map.items():
        if f"marginal_coverage_ancestry_{anc_code}" in res:
            print(f"\n{name}:")
            print(f"  Marginal Coverage: {res[f'marginal_coverage_ancestry_{anc_code}']*100:.1f}%")
            print(f"  Mondrian Coverage: {res[f'mondrian_coverage_ancestry_{anc_code}']*100:.1f}%")
            print(f"  TV Distance:       {res[f'tv_distance_ancestry_{anc_code}']:.4f}")
            print(f"  Barber Lower Bound:{res[f'barber_lower_bound_ancestry_{anc_code}']*100:.1f}%")

    res_df = pd.DataFrame([res])
    res_df.to_csv(os.path.join(RESULTS_DIR, "conformal_ancestry.csv"), index=False)
    
if __name__ == "__main__":
    main()
