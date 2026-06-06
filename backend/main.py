from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch
import numpy as np
import sys
import os

from schemas import BiomarkerInput, InferenceOutput, CounterfactualOutput, QuadrantCounterfactualOutput, GeodesicPathwayOutput
from feature_derivation import get_derived_features, get_demographics
from model_registry import registry

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src_code.counterfactual.counterfactual import metabolic_counterfactual, metabolic_quadrant_counterfactual
from src_code.counterfactual.geodesic import compute_geodesic, geodesic_to_clinical_interventions
from src_code.data.preprocess import FEATURE_COLS

app = FastAPI(title="Latent Metabolic State Inference API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    registry.load_models()

@app.post("/infer", response_model=InferenceOutput)
async def infer(biomarkers: BiomarkerInput):
    try:
        x_dict = get_derived_features(biomarkers.dict())
        x_scaled = registry.scaler.transform([x_dict["features"]])
        u_encoded = get_demographics(biomarkers.dict(), registry.u_encoder)
        x_t = torch.tensor(x_scaled, dtype=torch.float32)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        registry.model.eval()
        with torch.no_grad():
            mu_q, logvar_q = registry.model.encoder(x_t, u_t)
        z = mu_q.numpy()[0]
        sigma = np.exp(0.5 * logvar_q.numpy()[0])
        risk_pt, pred_sets = registry.conformal_surface.predict(z.reshape(1, -1), alpha=0.10)
        risk_pt = float(risk_pt[0]) if risk_pt.ndim == 1 else float(risk_pt[0, 1])
        
        if hasattr(registry.conformal_surface, 'get_quadrant'):
            quadrant_idx = registry.conformal_surface.get_quadrant(z[0], z[1])
            q_alpha = registry.conformal_surface.q_alphas.get(quadrant_idx, 0.10)
        else:
            quadrant_idx = 0
            q_alpha = 0.10
            
        quadrant_names = [
            "Metabolically Healthy Normal Weight (MHNW)",
            "Insulin-Resistant (IR-dominant)",
            "Steatotic (Steatosis-dominant)",
            "Dual-Burden (Thin-Fat Phenotype)"
        ]
            
        risk_lo = max(0.0, risk_pt - q_alpha)
        risk_hi = min(1.0, risk_pt + q_alpha)
        thin_fat = (biomarkers.bmi < 23.5 and x_dict["homa_ir"] > 2.5 and (biomarkers.waist_cm > 90 if biomarkers.sex == 1 else biomarkers.waist_cm > 80))
        return InferenceOutput(z1=round(float(z[0]), 4), z2=round(float(z[1]), 4), z1_sigma=round(float(sigma[0]), 4), z2_sigma=round(float(sigma[1]), 4), ir_risk=round(risk_pt, 4), ir_risk_lower=round(risk_lo, 4), ir_risk_upper=round(risk_hi, 4), thin_fat_flag=thin_fat, homa_ir=round(x_dict["homa_ir"], 3), tyg=round(x_dict["tyg"], 3), quadrant=quadrant_idx, quadrant_name=quadrant_names[quadrant_idx])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/counterfactual", response_model=CounterfactualOutput)
async def counterfactual(biomarkers: BiomarkerInput, homa_ir_target: float):
    try:
        x_dict = get_derived_features(biomarkers.dict())
        x_scaled = registry.scaler.transform([x_dict["features"]])
        u_encoded = get_demographics(biomarkers.dict(), registry.u_encoder)
        x_t = torch.tensor(x_scaled, dtype=torch.float32)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        registry.model.eval()
        with torch.no_grad():
            mu_q, _ = registry.model.encoder(x_t, u_t)
        z_current = mu_q.numpy()[0]
        result = metabolic_counterfactual(registry.model, z_current, homa_ir_target)
        return CounterfactualOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quadrant_counterfactual", response_model=QuadrantCounterfactualOutput)
async def quadrant_counterfactual(biomarkers: BiomarkerInput):
    try:
        x_dict = get_derived_features(biomarkers.dict())
        x_scaled = registry.scaler.transform([x_dict["features"]])[0]
        u_encoded = get_demographics(biomarkers.dict(), registry.u_encoder)
        x_t = torch.tensor([x_scaled], dtype=torch.float32)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        registry.model.eval()
        with torch.no_grad():
            mu_q, _ = registry.model.encoder(x_t, u_t)
        z_current = mu_q.numpy()[0]
        
        if hasattr(registry.conformal_surface, 'z1_threshold'):
            z1_threshold = registry.conformal_surface.z1_threshold
            z2_threshold = registry.conformal_surface.z2_threshold
        else:
            z1_threshold = 0.0
            z2_threshold = 0.0
            
        result = metabolic_quadrant_counterfactual(
            registry.model, 
            registry.scaler, 
            z_current, 
            np.array(x_dict["features"]), 
            z1_threshold, 
            z2_threshold
        )
        return QuadrantCounterfactualOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/geodesic_pathway", response_model=GeodesicPathwayOutput)
async def geodesic_pathway(biomarkers: BiomarkerInput):
    try:
        x_dict = get_derived_features(biomarkers.dict())
        x_scaled = registry.scaler.transform([x_dict["features"]])[0]
        u_encoded = get_demographics(biomarkers.dict(), registry.u_encoder)
        x_t = torch.tensor([x_scaled], dtype=torch.float32)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        
        registry.model.eval()
        with torch.no_grad():
            mu_q, _ = registry.model.encoder(x_t, u_t)
        z_current = mu_q.numpy()[0]
        
        if hasattr(registry.conformal_surface, 'z1_threshold'):
            z1_target = registry.conformal_surface.z1_threshold
            z2_target = registry.conformal_surface.z2_threshold
        else:
            z1_target = 0.0
            z2_target = 0.0
            
        z_target = np.array([z1_target, z2_target])
        
        # Euclidean path
        euclidean_path = np.linspace(z_current, z_target, 50)
        euclidean_distance = float(np.linalg.norm(z_current - z_target))
        
        # Geodesic path
        geodesic_path_arr = compute_geodesic(registry.model, z_current, z_target, n_steps=50)
        if geodesic_path_arr is None:
            # Fallback
            geodesic_path_arr = euclidean_path
            
        # Riemannian length approx
        diffs = np.diff(geodesic_path_arr, axis=0)
        geodesic_dist = float(np.sum(np.linalg.norm(diffs, axis=1)))
        
        interventions = geodesic_to_clinical_interventions(
            registry.model, 
            geodesic_path_arr, 
            registry.scaler, 
            FEATURE_COLS
        )
        
        return GeodesicPathwayOutput(
            z_current=z_current.tolist(),
            z_target=z_target.tolist(),
            euclidean_distance=euclidean_distance,
            geodesic_distance=geodesic_dist,
            euclidean_path=euclidean_path.tolist(),
            geodesic_path=geodesic_path_arr.tolist(),
            interventions=interventions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
