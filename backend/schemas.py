import math
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class BiomarkerInput(BaseModel):
    fasting_glucose_mg_dL:  float = Field(..., ge=30,  le=600)
    fasting_insulin_uU_mL:  float = Field(..., ge=1,   le=300)
    triglycerides_mg_dL:    float = Field(..., ge=20,  le=2000)
    hdl_mg_dL:              float = Field(..., ge=10,  le=150)
    ast_U_L:                float = Field(..., ge=5,   le=2000)
    alt_U_L:                float = Field(..., ge=1,   le=2000)
    ggt_U_L:                Optional[float] = Field(None, ge=5, le=2000)
    bmi:                    float = Field(..., ge=10,  le=24.9)
    waist_cm:               float = Field(..., ge=30,  le=200)
    platelets_1000_uL:      Optional[float] = Field(None, ge=50, le=1000)
    age:                    float = Field(..., ge=18,  le=120)
    sex:                    int   = Field(..., ge=1,   le=2)
    # NHANES RIDRETH1 codes: 1=Mex-Am/Hispanic, 2=OtherHisp, 3=NHW, 4=NHB, 6=NHA
    ancestry_proxy:         int   = Field(1, ge=1, le=6)

    @field_validator(
        "fasting_glucose_mg_dL", "fasting_insulin_uU_mL", "triglycerides_mg_dL",
        "hdl_mg_dL", "ast_U_L", "alt_U_L", "ggt_U_L", "bmi", "waist_cm",
        "platelets_1000_uL", "age"
    )
    @classmethod
    def reject_inf_nan(cls, v):
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("NaN or Infinity values are not permitted.")
        return v

class FeatureContribution(BaseModel):
    feature: str
    contribution: float

class InferenceOutput(BaseModel):
    # Latent coordinates
    z1: float
    z2: float
    z1_sigma: float
    z2_sigma: float
    # Conformal risk
    ir_risk: float
    ir_risk_lower: float
    ir_risk_upper: float
    # Clinical flags
    thin_fat_flag: bool
    homa_ir: float          # computed input-space HOMA-IR
    tyg: float
    quadrant: int
    quadrant_name: str
    # Anchor network predictions (clinical units, un-standardized)
    pred_homa_ir: float     # g1(z1) converted to HOMA-IR units
    pred_cap_score: float   # g2(z2) converted to FibroScan CAP dB/m
    # Research mode fields
    recon_mse: float        # per-sample reconstruction MSE from decoder
    # Percentile ranks against training cohort
    ir_percentile: int      # 1–99, patient's rank on IR axis vs. 618 training participants
    cap_percentile: int     # 1–99, patient's rank on steatosis axis
    # Distribution shift
    in_distribution: bool   # True if within 97.5th percentile Mahalanobis of training set
    # Stratum-specific achieved coverage (not a guarantee — the measured result)
    achieved_coverage: float
    # Explainability layer contributions
    z1_contributions: list[FeatureContribution] = Field(default_factory=list)
    z2_contributions: list[FeatureContribution] = Field(default_factory=list)

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

class CohortPoint(BaseModel):
    """Single training participant's latent position, for the /cohort endpoint."""
    z1: float
    z2: float
    quadrant: int

class DCAResult(BaseModel):
    threshold: str
    LMSIS: float
    FLI: float
    HSI: float
    Treat_All: float = Field(alias="Treat All")
    Treat_None: float = Field(alias="Treat None")
    
    class Config:
        populate_by_name = True

class BenchmarkData(BaseModel):
    name: str
    rho: float

class DrugData(BaseModel):
    name: str
    effect: float
    axis: str
    pval: str

class ValidationDataOutput(BaseModel):
    benchmark: list[BenchmarkData]
    drugs: list[DrugData]

class CompareInput(BaseModel):
    patient_a: BiomarkerInput
    patient_b: BiomarkerInput

class CompareOutput(BaseModel):
    inference_a: InferenceOutput
    inference_b: InferenceOutput
    euclidean_distance: float
    geodesic_distance: float

class ExportPdfInput(BaseModel):
    patient_data: dict
    interventions: list


