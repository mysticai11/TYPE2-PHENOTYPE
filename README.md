<div align="center">

# Predictive Risk Intelligence for Metabolic Screening in Diabetes
### LMSIS: Latent Metabolic State Inference System

*A Semi-Supervised Deep Learning Framework for Early Detection of Metabolic Dysfunction in Normal-BMI Adults*

<br/>

[![Integration Tests](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions)
[![Python Version](https://img.shields.io/badge/Python-3.12%20%7C%203.13-0A1628?style=flat&logo=python&logoColor=4A9FE0)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-0A1628?style=flat&logo=fastapi&logoColor=4A9FE0)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite-0A1628?style=flat&logo=react&logoColor=4A9FE0)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-0A1628?style=flat)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-15%20passed-1A6FBF?style=flat)](test_integration.py)

</div>

---

## 📑 Table of Contents
- [Silent metabolic risk, made visible](#-silent-metabolic-risk-made-visible)
- [Quick Guide for Examiners](#-quick-guide-for-examiners)
- [System Architecture & Visualizations](#-system-architecture--visualizations)
- [Key Findings at a Glance](#-key-findings-at-a-glance)
- [Getting Started](#-getting-started)

---

## 🔬 Silent metabolic risk, made visible.

Millions of adults worldwide receive a clean bill of health simply because their Body Mass Index falls within the normal range (18.5 ≤ BMI ≤ 24.9 kg/m²). However, BMI is strictly a measure of mass, completely blind to fat distribution and ectopic tissue accumulation. Underneath a healthy-looking exterior, a patient may carry a silent, severe dual metabolic burden — simultaneous insulin resistance and hepatic steatosis — invisible to traditional screening.

**LMSIS** deploys a **Dual-Anchored Semi-Supervised Identifiable Variational Autoencoder (DA-SS-iVAE)** to recover a continuous 2D latent metabolic geometry from 14 routine blood biomarkers. Validated against gold-standard FibroScan ultrasound elastography, the system successfully identifies high-risk metabolic phenotypes without requiring imaging or specialist referral.

> [!IMPORTANT]
> **Full Dissertation & Results**: For the complete findings, including mathematical proofs, exact threshold derivations (e.g., the 24.2% NHA misclassification rate), ablation studies (ρ: 0.18 → 0.54 with anchors), temporal OOD validation (ρ = 0.583 ± 0.027 five-seed mean), and post-pandemic L-cycle stress test (Z₁ stable at 0.773; Z₂ fractured at 0.332; Mondrian CP preserved ≥90% coverage), please read the comprehensive **[dissertation.md](dissertation.md)** summary or the full LaTeX source [dissertation.tex](dissertation.tex).

---

## 👨‍🏫 Quick Guide for Examiners

If you are reviewing this repository for the viva defense, please note the following structure:
- **Core Results & Scripts**: All scripts that generate the final numbers (prevalence, ancestry bias, etc.) are located in `src_code/validation/`.
- **System Safety Tests**: You can verify the integrity of the full pipeline (including monotonicity proofs) by running the automated test suite: `python -m pytest test_integration.py -v`.
- **Reproducible Dissertation**: The final `dissertation.docx` and `dissertation_abstract.docx` are generated dynamically from the model's outputs via `generate_dissertation.py`.

---

## 🗺️ System Architecture & Visualizations

The core model mapping routine features to biological pathways is illustrated in the animated diagram below:


### The 2D Latent Metabolic Space
LMSIS projects every patient onto a two-axis plane, where each axis corresponds to a distinct, anchored biological process. The coordinate system divides the population into four clinically actionable quadrants:


| Quadrant | Phenotype | Clinical Context |
| :--- | :--- | :--- |
| **Metabolically Healthy (MHNW)** | Neither axis elevated | Baseline healthy cohort. Low risk of cardiovascular progression. |
| **IR-Dominant** | Z₁ elevated, Z₂ normal | Isolated tissue insulin resistance. Responds to sensitizers (Metformin). |
| **Steatosis-Dominant** | Z₂ elevated, Z₁ normal | Isolated hepatic lipid accumulation. Responds to Statins/Fibrates. |
| **Dual-Burden (High-Risk)** | Both axes elevated | **Highest risk subpopulation.** Severe silent burden (29.89% prevalence). |

---

## 📊 Key Findings at a Glance

- **29.89% National Prevalence:** An estimated 23.9 million normal-BMI U.S. adults (95% CI: [0.00M, 64.36M]) carry dual-burden metabolic dysfunction.
- **Ancestry Inequality:** The universal HOMA-IR cutoff of 2.5 misclassifies 24.2% of Asian-American patients as healthy. LMSIS discovers statistically significant, lower ancestry-specific thresholds (p = 3.65×10⁻⁵).
- **Fair Uncertainty:** Mondrian Conformal Prediction restores 90.4% coverage for the high-risk Dual-Burden subgroup, which standard CP fails to protect (81.6%).
- **Temporal Robustness (Pre/Post-Pandemic):** Surpassed standard baselines on the P-cycle holdout ($\rho=0.583$). On the severe post-pandemic L-cycle holdout, the latent steatosis representation ($Z_2$) fractured, but the Mondrian Conformal layer successfully trapped the uncertainty, preserving $\ge 90\%$ clinical coverage across all phenotypes.

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
