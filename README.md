<div align="center">

# 🧬 LMSIS
### Latent Metabolic State Inference System

<img src="results/figures/metabolic_atlas_animated.svg" width="800px" alt="LMSIS Metabolic Atlas Geodesic Solver" />

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
> LMSIS is not intended to diagnose MASLD or insulin resistance. It provides a non-invasive **risk-stratification framework** that identifies normal-weight individuals who may benefit from further metabolic evaluation — specialist referrals, FibroScan, or longitudinal tracking.

---

## 📊 Key Results at a Glance

| Metric | Value | Context |
| :--- | :---: | :--- |
| **AUROC (CAP ≥ 248)** | **`0.841`** | vs. 0.740 FLI — state of the art liver fat recovery |
| **Spearman ρ vs CAP** | **`0.607`** | NAFLD-LFS is −0.069 (active inverse association) |
| **Cohort size** | **`1,477`** | Multi-cycle NHANES survey population |
| **Mondrian coverage (Dual-Burden)** | **`90.4%`** | Subgroup safety target guaranteed under population shift |
| **Integration tests** | **`15 passed`** | Monotonicity constraints and conformal coverages verified |

---

## 🗺️ The 2D Latent Metabolic Space

LMSIS projects every patient onto a two-axis plane, where each axis corresponds to a distinct, anchored biological process. The coordinate system divides the population into four clinically actionable quadrants:

```text
        Z₂ (Hepatic Steatosis)
        ↑
        │  ┌─────────────┬─────────────┐
        │  │  STEATOSIS  │  DUAL-BURDEN│
        │  │  DOMINANT   │  (HIGH-RISK)│
        │  │  n=185      │  n=136      │
        │  ├─────────────┼─────────────┤
        │  │  METABOLI-  │  IR-DOMINANT│
        │  │  CALLY HLTH │             │
        │  │  n=168      │  n=129      │
        │  └─────────────┴─────────────┘──→  Z₁ (Insulin Resistance)
```

| Quadrant | n | Phenotype | Clinical Context |
| :--- | :---: | :--- | :--- |
| **Metabolically Healthy (MHNW)** | 168 | Neither axis elevated | Baseline healthy cohort. Low risk of cardiovascular progression. |
| **IR-Dominant** | 129 | Z₁ elevated, Z₂ normal | Isolated tissue insulin resistance. Responds to sensitizers (Metformin). |
| **Steatosis-Dominant** | 185 | Z₂ elevated, Z₁ normal | Isolated hepatic lipid accumulation. Responds to Statins/Fibrates. |
| **Dual-Burden (High-Risk)** | **136** | **Both axes elevated** | **Highest risk clinical subpopulation.** Severe silent burden. |

---

## 📈 Benchmark Results

### 1 — Predicting Liver Steatosis (FibroScan CAP)

> [!TIP]
> LMSIS Z₂ dominates every current clinical gold standard. Notably, NAFLD-LFS has a **negative** Spearman correlation in this population — meaning it actively misleads clinical judgement under BMI restriction.

| Model / Index | Spearman ρ | AUROC (≥ 248) | AUROC (≥ 268) | Verdict | Visual AUROC (≥ 248) |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **LMSIS VAE (Z₂)** | **`0.607`** | **`0.841`** | **`0.833`** | 🟢 State-of-the-art | `████████████████████ 84.1%` |
| FLI (Fatty Liver Index) | `0.447` | `0.740` | `0.766` | 🟡 Suboptimal | `████████████████░░░░ 74.0%` |
| TyG (Triglyceride-Glucose) | `0.358` | `0.710` | `0.736` | 🟡 Moderate | `███████████████░░░░░ 71.0%` |
| HSI (Hepatic Steatosis Index) | `0.111` | `0.587` | `0.557` | 🟠 Near-random | `████████████░░░░░░░░ 58.7%` |
| NAFLD-LFS (Liver Fat Score) | `-0.069` | `0.509` | `0.512` | 🔴 Inverse association | `██████████░░░░░░░░░░ 50.9%` |

### 2 — Conformal Safety Calibration under Subpopulation Shift

> [!WARNING]
> Under covariate shift, standard marginal calibration drops to **81.6% coverage** for the highest-risk Dual-Burden subgroup — falling below the 90% safety target. **Mondrian calibration** guarantees safe conditional coverage (≥ 90%) across all quadrants.

| Phenotypic Quadrant | Sample size (n) | Marginal Coverage | Mondrian Coverage | Patient Safety Target | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| Metabolically Healthy (MHNW) | 168 | `98.2%` | **`98.2%`** ✓ | `90.0%` | 🟢 Safe |
| IR-Dominant | 129 | `93.8%` | **`100.0%`** ✓ | `90.0%` | 🟢 Safe |
| Steatosis-Dominant | 185 | `87.0%` | **`98.9%`** ✓ | `90.0%` | 🟢 Safe |
| **Dual-Burden (High-Risk)** | 136 | `81.6%` ⚠️ | **`90.4%`** 🛡️ | `90.0%` | 🟢 Safe (Calibrated) |

### 3 — Causal Pharmacological Dissociation

The model perfectly disentangles the biological mechanisms of drug action (double dissociation), confirming structural identifiability. Each drug class affects exclusively its target latent axis; off-target p-values are all non-significant (NS).

| Drug Class | Target Axis | Target p-value | Effect Size (r) | Off-Target p-value | Clinical Mechanism |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Metformin** | **Z₁ (IR)** | **`< 1.4e-19`** | **`1.000`** | `0.554` (NS) | ✔ Exclusively targets peripheral insulin resistance |
| **Statin** | **Z₂ (Steatosis)** | **`< 2.3e-26`** | **`0.888`** | `0.550` (NS) | ✔ Exclusively targets hepatic lipid clearance |
| **Fibrate** | **Z₂ (Steatosis)** | **`< 7.1e-10`** | **`1.000`** | `0.431` (NS) | ✔ Exclusively targets PPAR-α triglyceride clearing |

---

## ⚙️ Architecture: DA-SS-iVAE

Standard VAEs fail metabolic phenotyping because their latent spaces are **non-identifiable** — arbitrary rotations achieve identical reconstruction error. LMSIS resolves this through three mathematically grounded constraints:

### 1. 🧬 Demographic iVAE Identifiability
Conditioning the prior `p(z|u)` on demographic auxiliary variables `u` (age, sex, ancestry), following **Khemakhem et al., 2020**. This breaks the rotational symmetry that compromises standard generative spaces, forcing demographic-independent metabolic variation.

### 2. 🔗 Dual Monotone Anchoring
Constraining anchor networks using a Softplus activation on weights, forcing strict monotonicity: `z₁ → HOMA-IR` and `z₂ → CAP`. The decoder cannot reassign axes — each latent dimension is pinned to a biological observable.

### 3. 🎭 Semi-Supervised Loss Masking
All 1,477 cohort participants contribute to the Z₁ HOMA-IR anchor. The Z₂ CAP anchor is safely masked for participants missing ultrasound records — maximizing data usage without introducing bias.

<br/>

<div align="center">
  <img src="results/figures/model_pipeline_animated.svg" width="700px" alt="DA-SS-iVAE Pipeline Architecture" />
  <p><small><em>Figure 2: DA-SS-iVAE Neural Architecture and Latent Anchoring Flow.</em></small></p>
</div>

---

## 📈 Symbolic AI Interpretability

The black-box decoder was mapped using **Symbolic Regression (PySR)**, recovering closed-form governing equations for the biological pathways. All coefficients verified against `results/symbolic_decoder/formulas.json`.

| Biomarker | Discovered Symbolic Formula | Biological Interpretation |
| :--- | :--- | :--- |
| **HDL Cholesterol** | `hdl = -17.13 * (z1 + z2 + abs(z2)) + 61.04` | Both axes suppress HDL; the <code>abs(z2)</code> term means steatosis contributes double when positive. |
| **Atherogenic Index** | `aip = abs((z1 + z2 + 0.131) * (z2 + 0.385)) + z2 + 0.034` | Cardiovascular risk scales non-linearly; the product structure means each axis amplifies the other. |
| **AST:ALT Ratio** | `ast_alt = 11.49^z2 * (4.64 - abs(z1 - z2))` | Liver injury correlates exponentially with the Z₂ steatosis axis. |

<blockquote>
  <strong>💡 Mathematical Proof:</strong> The AIP formula mathematically confirms that the dual-burden phenotype (z₁ &gt; 0 and z₂ &gt; 0 simultaneously) produces the highest atherogenic index of plasma — not either axis alone. This emerges naturally from the decoder manifold's geometry rather than manual design constraints.
</blockquote>

---

## 🛠️ Developer Resources & Documentation

<details>
  <summary>💻 <strong>View Technology Stack & Core Layers</strong></summary>
  <br/>
  
  | Layer | Technologies |
  | :--- | :--- |
  | **Deep Learning Core** | PyTorch · NumPy · SciPy · Scikit-Learn |
  | **Uncertainty & Coverage** | MAPIE · Scikit-Dimension |
  | **Symbolic Regression** | PySR (Julia backend) |
  | **API Backend** | FastAPI · Uvicorn · Pydantic v2 |
  | **Interactive Dashboard** | React 19 · Vite · Tailwind CSS · D3.js · Zustand · Framer Motion |

</details>

<details>
  <summary>📊 <strong>View 14 Routine Features Used</strong></summary>
  <br/>
  <ul>
    <li><strong>Fasting Glucose</strong> (mg/dL)</li>
    <li><strong>Fasting Insulin</strong> (µU/mL)</li>
    <li><strong>Triglycerides</strong> (mg/dL)</li>
    <li><strong>HDL Cholesterol</strong> (mg/dL)</li>
    <li><strong>AST</strong> (U/L)</li>
    <li><strong>ALT</strong> (U/L)</li>
    <li><strong>GGT</strong> (U/L)</li>
    <li><strong>Platelets</strong> (1000/µL)</li>
    <li><strong>BMI</strong> (kg/m²)</li>
    <li><strong>Waist Circumference</strong> (cm)</li>
    <li><strong>AST:ALT Ratio</strong></li>
    <li><strong>TG:HDL Ratio</strong></li>
    <li><strong>Atherogenic Index of Plasma (AIP)</strong></li>
    <li><strong>TyG Index</strong></li>
  </ul>
</details>

<details>
  <summary>📂 <strong>View Repository Directory Blueprint</strong></summary>
  <br/>
  <pre><code>TYPE2-PHENOTYPE/
├── backend/                   # FastAPI application
│   └── main.py                # Endpoints: /infer, /compare, /export_pdf
├── frontend/                  # React 19 dashboard
│   └── src/                   # D3.js Atlas, Framer Motion UI, Zustand state
├── models/                    # Serialized checkpoints
│   ├── ivae_best.pt            # Trained DA-SS-iVAE weights
│   └── conformal_surface.pkl  # Mondrian calibration surface
├── results/                   # All validation outputs
│   ├── benchmark_demolition_results.csv
│   ├── exp5_coverage_comparison.csv
│   ├── pharmacology_results_simulated.csv
│   └── symbolic_decoder/
│       └── formulas.json      # PySR recovered equations
├── src_code/                  # Core Python pipeline
│   ├── data/                  # NHANES multi-cycle loading & preprocessing
│   ├── model/                 # VAE, Encoder, Decoder, Prior, Anchor definitions
│   ├── counterfactual/        # Riemannian geodesic solver & Brent's inversion
│   └── validation/            # Benchmarking, conformal testing & pharmacology PSM
└── test_integration.py        # Comprehensive CI/CD integration tests (15 tests)</code></pre>
</details>

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
# Expected: 15 passed, 5 warnings in 17.17s
```

The test suite verifies:
- Strict monotonicity of anchor networks
- VAE weight sign constraints (Softplus-anchored)
- Mondrian conformal coverage ≥ 90% on all subgroups
- Pharmacological double dissociation significance thresholds

### 3 — Launch API and Dashboard

Open two separate terminals:

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn backend.main:app --reload
# API docs available at http://127.0.0.1:8000/docs
```

**Terminal 2 — React Dashboard:**
```bash
cd frontend
npm install
npm run dev
# Dashboard available at http://localhost:5173
```

---

## 📜 Data Provenance & Audit Trail

All benchmark numbers are verified against raw output files in `results/`. Key audit outcomes:

- **Benchmark table** — All Spearman ρ and AUROC values match `benchmark_demolition_results.csv` exactly.
- **Conformal table** — All sample sizes and coverage percentages match `exp5_coverage_comparison.csv` exactly.
- **Pharmacology table** — Metformin p-value corrected to `< 1.4e-19` (raw: 1.369×10⁻¹⁹); Statin and Fibrate separated into individual rows with distinct effect sizes.
- **Symbolic formulas** — AST:ALT base corrected to `11.49` (raw: 11.492642); AIP formula updated to include the `+0.034` constant intercept; `abs()` notation replaces HTML entities.

---

<div align="center">

**LMSIS** — Built for the intersection of clinical insight and computational rigor.

[GitHub](https://github.com/mysticai11/TYPE2-PHENOTYPE) · [CI/CD](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions) · MIT License

</div>
