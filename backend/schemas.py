from pydantic import BaseModel, Field
from typing import Optional

class BiomarkerInput(BaseModel):
    fasting_glucose_mg_dL:  float = Field(..., ge=50,  le=600)
    fasting_insulin_uU_mL:  float = Field(..., ge=1,   le=300)
    triglycerides_mg_dL:    float = Field(..., ge=20,  le=2000)
    hdl_mg_dL:              float = Field(..., ge=10,  le=150)
    ast_U_L:                float = Field(..., ge=5,   le=2000)
    alt_U_L:                float = Field(..., ge=5,   le=2000)
    ggt_U_L:                Optional[float] = Field(None, ge=5, le=2000)
    bmi:                    float = Field(..., ge=10,  le=24.9)
    waist_cm:               float = Field(..., ge=50,  le=180)
    platelets_1000_uL:      Optional[float] = Field(None)
    age:                    float = Field(..., ge=18,  le=80)
    sex:                    int   = Field(..., ge=1,   le=2)
    ancestry_proxy:         int   = Field(1, ge=1, le=3)

class InferenceOutput(BaseModel):
    z1: float
    z2: float
    z1_sigma: float
    z2_sigma: float
    ir_risk: float
    ir_risk_lower: float
    ir_risk_upper: float
    thin_fat_flag: bool
    homa_ir: float
    tyg: float
    quadrant: int
    quadrant_name: str

class CounterfactualOutput(BaseModel):
    z1_current: float
    z1_counterfactual: float
    z2_unchanged: float
    delta_z1: float
    latent_distance: float

class Lever(BaseModel):
    biomarker: str
    delta_raw: float
    delta_scaled: float
    unit: str

class QuadrantCounterfactualOutput(BaseModel):
    z1_current: float
    z2_current: float
    z1_target: float
    z2_target: float
    latent_distance: float
    levers: list[Lever]

class GeodesicWaypoint(BaseModel):
    step: int
    z: list[float]
    progress: float
    biomarker_deltas: dict[str, float]

class GeodesicPathwayOutput(BaseModel):
    z_current: list[float]
    z_target: list[float]
    euclidean_distance: float
    geodesic_distance: float
    euclidean_path: list[list[float]]
    geodesic_path: list[list[float]]
    interventions: list[GeodesicWaypoint]
