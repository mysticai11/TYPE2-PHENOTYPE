import logging
import time
import uuid
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import torch
import torch.nn.functional as F
import numpy as np
import sys
import os

from schemas import (
    BiomarkerInput, InferenceOutput, CounterfactualOutput,
    QuadrantCounterfactualOutput, GeodesicPathwayOutput, CohortPoint,
    FeatureContribution
)
from feature_derivation import get_derived_features, get_demographics
from model_registry import registry, ACHIEVED_COVERAGE

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src_code.counterfactual.counterfactual import metabolic_counterfactual, metabolic_quadrant_counterfactual
from src_code.counterfactual.geodesic import compute_geodesic, geodesic_to_clinical_interventions
from src_code.data.preprocess import FEATURE_COLS

# Structured Logging Setup
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True

logger = logging.getLogger("LMSIS")
logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if re-imported
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addFilter(RequestIdFilter())

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load_models()
    yield

app = FastAPI(title="Latent Metabolic State Inference API — LMSIS", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000.0
    
    logger.info(
        f"{request.method} {request.url.path} status={response.status_code} latency={duration:.2f}ms",
        extra={"request_id": request_id}
    )
    response.headers["X-Request-ID"] = request_id
    return response



# ---------------------------------------------------------------------------
# /health — liveness check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "DA-SS-iVAE-v2",
        "x_dim": 14,
        "n_training": len(registry.training_z) if registry.training_z is not None else 0,
    }


# ---------------------------------------------------------------------------
# /cohort — return encoded Z-coordinates of full training cohort
# ---------------------------------------------------------------------------
@app.get("/cohort", response_model=list[CohortPoint])
async def cohort():
    if registry.training_z is None:
        raise HTTPException(status_code=503, detail="Training embeddings not yet computed.")
    points = []
    for i in range(len(registry.training_z)):
        points.append(CohortPoint(
            z1=round(float(registry.training_z[i, 0]), 4),
            z2=round(float(registry.training_z[i, 1]), 4),
            quadrant=int(registry.training_quadrants[i])
        ))
    return points


# ---------------------------------------------------------------------------
# /infer — core inference
# ---------------------------------------------------------------------------
@app.post("/infer", response_model=InferenceOutput)
async def infer(biomarkers: BiomarkerInput):
    try:
        x_dict = get_derived_features(biomarkers.model_dump())
        x_scaled = registry.scaler.transform(x_dict["df_derived"][FEATURE_COLS])
        u_encoded = get_demographics(biomarkers.model_dump(), registry.u_encoder)
        x_t = torch.tensor(x_scaled, dtype=torch.float32)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        z_tensor = torch.tensor(x_scaled, dtype=torch.float32)   # kept for recon

        registry.model.eval()
        with torch.no_grad():
            mu_q, logvar_q = registry.model.encoder(x_t, u_t)
            z_np = mu_q.numpy()[0]
            sigma_np = np.exp(0.5 * logvar_q.numpy()[0])

            # Anchor predictions → clinical units
            h_hat = registry.model.anchor(
                torch.tensor([z_np[0]], dtype=torch.float32),
                torch.tensor([z_np[1]], dtype=torch.float32)
            ).numpy()[0]
            pred_homa_ir, pred_cap_score = registry.unstandardize_anchor(h_hat)

            # Reconstruction MSE for research mode
            x_hat = registry.model.decoder(mu_q)
            recon_mse = float(F.mse_loss(x_hat, x_t).item())

        # Explainability Layer: Autograd to calculate gradients of Z1/Z2 w.r.t input features
        x_scaled_tensor = torch.tensor(x_scaled, dtype=torch.float32, requires_grad=True)
        mu_explain, _ = registry.model.encoder(x_scaled_tensor, u_t)
        
        # Z1 Explainability
        z1_explain = mu_explain[0, 0]
        z1_explain.backward(retain_graph=True)
        grad_z1 = x_scaled_tensor.grad.data.numpy()[0]
        
        # Reset gradients
        x_scaled_tensor.grad.zero_()
        
        # Z2 Explainability
        z2_explain = mu_explain[0, 1]
        z2_explain.backward()
        grad_z2 = x_scaled_tensor.grad.data.numpy()[0]
        
        # Normalize and map back to FEATURE_COLS
        total_z1_grad = np.sum(np.abs(grad_z1))
        total_z2_grad = np.sum(np.abs(grad_z2))
        
        z1_contribs = []
        z2_contribs = []
        for i, col in enumerate(FEATURE_COLS):
            z1_contribs.append(FeatureContribution(
                feature=col,
                contribution=round(float(np.abs(grad_z1[i]) / total_z1_grad) if total_z1_grad > 0 else 0.0, 4)
            ))
            z2_contribs.append(FeatureContribution(
                feature=col,
                contribution=round(float(np.abs(grad_z2[i]) / total_z2_grad) if total_z2_grad > 0 else 0.0, 4)
            ))
            
        z1_contribs.sort(key=lambda x: x.contribution, reverse=True)
        z2_contribs.sort(key=lambda x: x.contribution, reverse=True)

        # Conformal risk score + interval
        risk_pt, pred_sets = registry.conformal_surface.predict(z_np.reshape(1, -1), alpha=0.10)
        risk_pt = float(risk_pt[0]) if risk_pt.ndim == 1 else float(risk_pt[0, 1])

        # Quadrant assignment
        if hasattr(registry.conformal_surface, 'get_quadrant'):
            quadrant_idx = registry.conformal_surface.get_quadrant(z_np[0], z_np[1])
            q_alpha = registry.conformal_surface.q_alphas.get(quadrant_idx, 0.10)
        else:
            quadrant_idx = 0
            q_alpha = 0.10

        risk_lo = max(0.0, risk_pt - q_alpha)
        risk_hi = min(1.0, risk_pt + q_alpha)

        # Thin-fat flag
        thin_fat = (
            biomarkers.bmi < 23.5
            and x_dict["homa_ir"] > 2.5
            and (biomarkers.waist_cm > 90 if biomarkers.sex == 1 else biomarkers.waist_cm > 80)
        )

        # Percentile ranks against training cohort
        ir_percentile, cap_percentile = registry.get_percentile(z_np[0], z_np[1])

        # Distribution shift detection
        in_distribution = registry.is_in_distribution(z_np)

        # Achieved coverage for this patient's stratum
        achieved_coverage = ACHIEVED_COVERAGE.get(quadrant_idx, 0.90)

        quadrant_names = [
            "Metabolically Healthy Normal Weight (MHNW)",
            "Insulin-Resistant (IR-dominant)",
            "Steatotic (Steatosis-dominant)",
            "Dual-Burden (Thin-Fat Phenotype)"
        ]

        return InferenceOutput(
            z1=round(float(z_np[0]), 4),
            z2=round(float(z_np[1]), 4),
            z1_sigma=round(float(sigma_np[0]), 4),
            z2_sigma=round(float(sigma_np[1]), 4),
            ir_risk=round(risk_pt, 4),
            ir_risk_lower=round(risk_lo, 4),
            ir_risk_upper=round(risk_hi, 4),
            thin_fat_flag=thin_fat,
            homa_ir=round(x_dict["homa_ir"], 3),
            tyg=round(x_dict["tyg"], 3),
            quadrant=quadrant_idx,
            quadrant_name=quadrant_names[quadrant_idx],
            pred_homa_ir=pred_homa_ir,
            pred_cap_score=pred_cap_score,
            recon_mse=round(recon_mse, 5),
            ir_percentile=ir_percentile,
            cap_percentile=cap_percentile,
            in_distribution=in_distribution,
            achieved_coverage=achieved_coverage,
            z1_contributions=z1_contribs,
            z2_contributions=z2_contribs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /counterfactual — single-axis HOMA-IR target
# ---------------------------------------------------------------------------
@app.post("/counterfactual", response_model=CounterfactualOutput)
async def counterfactual(biomarkers: BiomarkerInput, homa_ir_target: float):
    try:
        x_dict = get_derived_features(biomarkers.model_dump())
        x_scaled = registry.scaler.transform(x_dict["df_derived"][FEATURE_COLS])
        u_encoded = get_demographics(biomarkers.model_dump(), registry.u_encoder)
        x_t = torch.tensor(x_scaled, dtype=torch.float32)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        registry.model.eval()
        with torch.no_grad():
            mu_q, _ = registry.model.encoder(x_t, u_t)
        z_current = mu_q.numpy()[0]
        result = await asyncio.to_thread(
            metabolic_counterfactual, registry.model, z_current, homa_ir_target
        )
        return CounterfactualOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /quadrant_counterfactual — move to safe quadrant
# ---------------------------------------------------------------------------
@app.post("/quadrant_counterfactual", response_model=QuadrantCounterfactualOutput)
async def quadrant_counterfactual(biomarkers: BiomarkerInput):
    try:
        x_dict = get_derived_features(biomarkers.model_dump())
        x_scaled = registry.scaler.transform(x_dict["df_derived"][FEATURE_COLS])[0]
        u_encoded = get_demographics(biomarkers.model_dump(), registry.u_encoder)
        x_t = torch.tensor(x_scaled, dtype=torch.float32).unsqueeze(0)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)
        registry.model.eval()
        with torch.no_grad():
            mu_q, _ = registry.model.encoder(x_t, u_t)
        z_current = mu_q.numpy()[0]

        z1_threshold = getattr(registry.conformal_surface, 'z1_threshold', 0.0)
        z2_threshold = getattr(registry.conformal_surface, 'z2_threshold', 0.0)

        result = await asyncio.to_thread(
            metabolic_quadrant_counterfactual,
            registry.model, registry.scaler, z_current,
            np.array(x_dict["features"]), z1_threshold, z2_threshold
        )
        return QuadrantCounterfactualOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /geodesic_pathway — Riemannian pathway to safe zone
# ---------------------------------------------------------------------------
@app.post("/geodesic_pathway", response_model=GeodesicPathwayOutput)
async def geodesic_pathway(biomarkers: BiomarkerInput):
    try:
        x_dict = get_derived_features(biomarkers.model_dump())
        x_scaled = registry.scaler.transform(x_dict["df_derived"][FEATURE_COLS])[0]
        u_encoded = get_demographics(biomarkers.model_dump(), registry.u_encoder)
        x_t = torch.tensor(x_scaled, dtype=torch.float32).unsqueeze(0)
        u_t = torch.tensor([u_encoded], dtype=torch.float32)

        registry.model.eval()
        with torch.no_grad():
            mu_q, _ = registry.model.encoder(x_t, u_t)
        z_current = mu_q.numpy()[0]

        z1_target = getattr(registry.conformal_surface, 'z1_threshold', 0.0)
        z2_target = getattr(registry.conformal_surface, 'z2_threshold', 0.0)
        z_target = np.array([z1_target, z2_target])

        euclidean_path = np.linspace(z_current, z_target, 50)
        euclidean_distance = float(np.linalg.norm(z_current - z_target))

        geodesic_path_arr = await asyncio.to_thread(
            compute_geodesic, registry.model, z_current, z_target, n_steps=50
        )
        if geodesic_path_arr is None:
            geodesic_path_arr = euclidean_path

        diffs = np.diff(geodesic_path_arr, axis=0)
        geodesic_dist = float(np.sum(np.linalg.norm(diffs, axis=1)))

        interventions = await asyncio.to_thread(
            geodesic_to_clinical_interventions,
            registry.model, geodesic_path_arr, registry.scaler, FEATURE_COLS
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
