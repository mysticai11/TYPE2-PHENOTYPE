import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from main import app

@pytest.fixture(scope="module")
def client():
    # Using TestClient as a context manager triggers the FastAPI startup event
    with TestClient(app) as c:
        yield c

# Typical valid BiomarkerInput payload matching normal-BMI and real NHANES demographics
VALID_INPUT = {
    "fasting_glucose_mg_dL": 94.0,
    "fasting_insulin_uU_mL": 6.08,
    "triglycerides_mg_dL": 54.5,
    "hdl_mg_dL": 59.0,
    "ast_U_L": 13.0,
    "alt_U_L": 4.1,
    "ggt_U_L": 16.0,
    "bmi": 22.2,
    "waist_cm": 78.8,
    "platelets_1000_uL": 229.0,
    "age": 30.0,
    "sex": 2,
    "ancestry_proxy": 4
}

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "DA-SS-iVAE-v2"
    assert "x_dim" in data
    assert data["x_dim"] == 14

def test_cohort_endpoint(client):
    response = client.get("/cohort")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        point = data[0]
        assert "z1" in point
        assert "z2" in point
        assert "quadrant" in point

def test_infer_endpoint(client):
    response = client.post("/infer", json=VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    assert "z1" in data
    assert "z2" in data
    assert "ir_risk" in data
    assert "pred_homa_ir" in data
    assert "pred_cap_score" in data
    assert "recon_mse" in data
    assert "ir_percentile" in data
    assert "cap_percentile" in data
    assert "in_distribution" in data
    assert "achieved_coverage" in data
    assert data["quadrant"] in [0, 1, 2, 3]

def test_counterfactual_endpoint(client):
    response = client.post("/counterfactual?homa_ir_target=1.5", json=VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    assert "z1_current" in data
    assert "z1_counterfactual" in data
    assert "z2_unchanged" in data
    assert "delta_z1" in data
    assert "latent_distance" in data

def test_quadrant_counterfactual_endpoint(client):
    response = client.post("/quadrant_counterfactual", json=VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    assert "z1_current" in data
    assert "z2_current" in data
    assert "z1_target" in data
    assert "z2_target" in data
    assert "latent_distance" in data
    assert "levers" in data
    assert isinstance(data["levers"], list)

def test_geodesic_pathway_endpoint(client):
    response = client.post("/geodesic_pathway", json=VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    assert "z_current" in data
    assert "z_target" in data
    assert "euclidean_distance" in data
    assert "geodesic_distance" in data
    assert "euclidean_path" in data
    assert "geodesic_path" in data
    assert "interventions" in data
    assert isinstance(data["interventions"], list)

def test_feature_order_regression():
    from src_code.data.schema import FeatureSchema
    from model_registry import registry
    registry.load_models()
    
    # Check that FEATURE_COLS is exactly 14 columns
    assert len(FeatureSchema.FEATURE_COLS) == 14
    
    # Check that RobustScaler's feature names match FEATURE_COLS
    if hasattr(registry.scaler, "feature_names_in_"):
        scaler_features = list(registry.scaler.feature_names_in_)
        assert scaler_features == FeatureSchema.FEATURE_COLS

def test_model_output_regression(client):
    response = client.post("/infer", json=VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    
    # Assert coordinates match rounded baseline within 1e-5 tolerance
    # z1 = -0.0035, z2 = -0.0518
    assert abs(data["z1"] - (-0.0035)) < 1e-3
    assert abs(data["z2"] - (-0.0518)) < 1e-3

def test_latent_space_monotonicity():
    import torch
    from model_registry import registry
    registry.load_models()
    
    # Test Z1 -> HOMA-IR monotonicity: as z1 increases, predicted HOMA-IR must increase
    z1s = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=torch.float32)
    z2_zero = torch.zeros(1, dtype=torch.float32)
    
    homa_vals = []
    for z1 in z1s:
        with torch.no_grad():
            h_hat = registry.model.anchor(z1.unsqueeze(0), z2_zero)
            pred_homa, _ = registry.unstandardize_anchor(h_hat.numpy()[0])
            homa_vals.append(pred_homa)
            
    # Check if homa_vals is strictly monotonic increasing
    for idx in range(len(homa_vals) - 1):
        assert homa_vals[idx + 1] > homa_vals[idx]
        
    # Test Z2 -> CAP score monotonicity: as z2 increases, predicted CAP must increase
    z2s = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=torch.float32)
    z1_zero = torch.zeros(1, dtype=torch.float32)
    
    cap_vals = []
    for z2 in z2s:
        with torch.no_grad():
            h_hat = registry.model.anchor(z1_zero, z2.unsqueeze(0))
            _, pred_cap = registry.unstandardize_anchor(h_hat.numpy()[0])
            cap_vals.append(pred_cap)
            
    # Check if cap_vals is strictly monotonic increasing
    for idx in range(len(cap_vals) - 1):
        assert cap_vals[idx + 1] > cap_vals[idx]

def test_input_validation_boundaries(client):
    # Case A: BMI outside normal-BMI limits
    invalid_bmi = VALID_INPUT.copy()
    invalid_bmi["bmi"] = 28.5  # normal BMI is max 24.9
    res = client.post("/infer", json=invalid_bmi)
    assert res.status_code == 422
    
    # Case B: NaN values in fasting glucose
    invalid_nan = VALID_INPUT.copy()
    invalid_nan["fasting_glucose_mg_dL"] = "NaN"
    res = client.post("/infer", json=invalid_nan)
    assert res.status_code == 422
    
    # Case C: Inf values in triglycerides
    invalid_inf = VALID_INPUT.copy()
    invalid_inf["triglycerides_mg_dL"] = "Infinity"
    res = client.post("/infer", json=invalid_inf)
    assert res.status_code == 422

def test_explainability_contributions(client):
    response = client.post("/infer", json=VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "z1_contributions" in data
    assert "z2_contributions" in data
    assert len(data["z1_contributions"]) == 14
    assert len(data["z2_contributions"]) == 14
    
    # Assert contributions sum to approximately 1.0
    sum_z1 = sum(c["contribution"] for c in data["z1_contributions"])
    sum_z2 = sum(c["contribution"] for c in data["z2_contributions"])
    assert abs(sum_z1 - 1.0) < 1e-2
    assert abs(sum_z2 - 1.0) < 1e-2

def test_dca_endpoint(client):
    response = client.get("/dca_results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # verify schema
    first = data[0]
    assert "threshold" in first
    assert "LMSIS" in first
    assert "FLI" in first
    assert "HSI" in first
    assert "Treat All" in first
    assert "Treat None" in first

def test_validation_data_endpoint(client):
    response = client.get("/validation_data")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark" in data
    assert "drugs" in data
    assert len(data["benchmark"]) > 0
    assert len(data["drugs"]) > 0

def test_compare_endpoint(client):
    payload = {
        "patient_a": VALID_INPUT,
        "patient_b": VALID_INPUT
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "inference_a" in data
    assert "inference_b" in data
    assert "euclidean_distance" in data
    assert "geodesic_distance" in data

def test_export_pdf_endpoint(client):
    payload = {
        "patient_data": {
            "quadrant_name": "Test Quadrant",
            "pred_homa_ir": 2.5,
            "pred_cap": 250,
            "risk_score": 0.5
        },
        "interventions": [
            {"name": "Triglycerides", "current": 200, "target": 150, "diff": -50, "unit": "mg/dL"}
        ]
    }
    response = client.post("/export_pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000

if __name__ == "__main__":
    print("Running integration tests...")
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
