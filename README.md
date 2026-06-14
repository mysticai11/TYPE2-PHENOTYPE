<div align="center">

# 🧬 LMSIS
### Latent Metabolic State Inference System

*A Clinical Machine Learning Pipeline for Detecting Silent Concurrent Metabolic Dysfunction in Normal-BMI Adults*

<br/>

[![Integration Tests](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions)
[![Python Version](https://img.shields.io/badge/Python-3.12%20%7C%203.13-0A1628?style=flat&logo=python&logoColor=4A9FE0)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-0A1628?style=flat&logo=fastapi&logoColor=4A9FE0)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite-0A1628?style=flat&logo=react&logoColor=4A9FE0)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-0A1628?style=flat)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-15%20passed-1A6FBF?style=flat)](test_integration.py)

</div>

---

## 🧬 Silent metabolic risk, made visible.

> Millions of adults worldwide receive a clean bill of health simply because their Body Mass Index falls within the normal range (18.5 ≤ BMI ≤ 24.9 kg/m²). However, BMI is blind to fat distribution and ectopic tissue accumulation. Underneath a healthy-looking exterior, a patient may carry a silent, severe dual metabolic burden — simultaneous insulin resistance and hepatic steatosis — invisible to traditional screening.

**LMSIS** recovers a continuous 2D latent metabolic geometry from 14 routine blood biomarkers, validated against gold-standard FibroScan ultrasound elastography. It deploys a **Dual-Anchored Semi-Supervised Identifiable Variational Autoencoder (DA-SS-iVAE)** to identify the four phenotypic quadrants of metabolic health in normal-weight individuals.

> [!IMPORTANT]
> **Full Documentation**: For the complete dissertation, mathematical formulation (ELBO, Monotone Anchors), experimental validation metrics, conformal calibration guarantees, symbolic interpretability proofs, and system blueprints, please refer directly to the [LMSIS Master Project Report](LMSIS_Master_Report.md).

---

## 🗺️ System Architecture & Visualizations

The core model mapping routine features to biological pathways is illustrated in the animated diagram below:

<div align="center">
  <img src="results/figures/model_pipeline_animated.svg" alt="LMSIS Model Pipeline" width="100%" />
</div>

### The 2D Latent Metabolic Space
LMSIS projects every patient onto a two-axis plane, where each axis corresponds to a distinct, anchored biological process. The coordinate system divides the population into four clinically actionable quadrants:

<div align="center">
  <img src="results/figures/metabolic_atlas_animated.svg" alt="LMSIS Metabolic Atlas" width="100%" />
</div>

| Quadrant | Phenotype | Clinical Context |
| :--- | :--- | :--- |
| **Metabolically Healthy (MHNW)** | Neither axis elevated | Baseline healthy cohort. Low risk of cardiovascular progression. |
| **IR-Dominant** | Z₁ elevated, Z₂ normal | Isolated tissue insulin resistance. Responds to sensitizers (Metformin). |
| **Steatosis-Dominant** | Z₂ elevated, Z₁ normal | Isolated hepatic lipid accumulation. Responds to Statins/Fibrates. |
| **Dual-Burden (High-Risk)** | Both axes elevated | **Highest risk clinical subpopulation.** Severe silent burden. |

---

## 🚀 Getting Started

### 1 — Installation

Clone the repository and install the strictly version-locked core dependencies:

```bash
git clone https://github.com/mysticai11/TYPE2-PHENOTYPE.git
cd TYPE2-PHENOTYPE
pip install -r requirements.txt
```

### 2 — Verify System Integrity

Assert system safety, run integration tests, check monotonicity bounds, and verify VAE weight alignments:

```bash
python -m pytest test_integration.py -v
```

### 3 — Launch API and Dashboard

Open two separate terminals:

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn main:app --app-dir backend
# API docs available at http://127.0.0.1:8000/docs
```

**Terminal 2 — React Dashboard:**
```bash
cd frontend
cmd /c npm run dev
# Dashboard available at http://localhost:5173
```

---

<div align="center">

**LMSIS** — Built for the intersection of clinical insight and computational rigor.

[GitHub](https://github.com/mysticai11/TYPE2-PHENOTYPE) · [CI/CD](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions) · MIT License

</div>
