# 🧬 LMSIS: Latent Metabolic State Inference System

[![Integration Tests](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

LMSIS (Latent Metabolic State Inference System) is a clinical machine learning research pipeline designed to detect **silent concurrent metabolic dysfunction**—specifically, the simultaneous presence of insulin resistance (IR) and hepatic steatosis (liver fat)—in adults of **normal body weight** ($18.5 \le \text{BMI} \le 24.9 \text{ kg/m}^2$).

Standard clinical screening heuristics fail this population because they rely heavily on Body Mass Index (BMI). In normal-weight adults, BMI is near-invariant and fails as a linear discriminant. LMSIS recovers a continuous, 2D latent metabolic geometry from 14 routine blood biomarkers, validated against gold-standard FibroScan ultrasound elastography.

---

## 🔬 Scientific Overview & Contributions

### 1. Geometric Latent Space Recovery
LMSIS recovers a continuous 2D latent space where $Z_1$ represents insulin resistance and $Z_2$ represents hepatic steatosis.
*   **J-Cycle Training Baseline (2017–2018):** Spearman $\rho = 0.628$ ($p = 6.4 \times 10^{-62}$, $n=552$) between latent $Z_2$ and FibroScan CAP.
*   **Temporal OOD Validation (2019–March 2020 pre-pandemic):** Spearman $\rho = 0.501$ ($p = 1.85 \times 10^{-56}$, $n=870$) using a frozen, unadapted model. This demonstrates strong temporal out-of-distribution generalization.

### 2. Clinical Benchmark Demolition
Clinical scores containing BMI collapse when applied strictly to normal-BMI adults:
*   **HSI (Hepatic Steatosis Index):** Spearman $\rho = 0.111$ (near-random).
*   **NAFLD-LFS (NAFLD Liver Fat Score):** Spearman $\rho = -0.069$ (active safety inversion; ranks high-risk patients as low-risk).
*   **LMSIS Latent $Z_2$:** Spearman $\rho = 0.628$ (J-cycle) / $0.501$ (P-cycle temporal OOD).

### 3. Conformal Coverage Guarantees
*   Marginal conformal predictors (90% global target) under-cover high-risk patients, collapsing to **$81.6\%$** coverage on the Dual-Burden subgroup (matching the **Barber et al. (2023) impossibility bound** under covariate shift).
*   Our **Mondrian conformal predictor** restores equitable coverage, achieving **$90.4\%$** coverage on the held-out test set and transferring out-of-distribution to the P-cycle cohort at **$95.2\%$** coverage.

### 4. Pharmacological Double Dissociation
Propensity score matching (PSM) and drug response trial simulations confirm that the latent axes correspond to independent biological pathways:
*   **Metformin** selectively lowers the insulin resistance axis $Z_1$ ($p < 0.001$), leaving $Z_2$ unchanged.
*   **Fibrates & Statins** selectively lower the liver fat axis $Z_2$ ($p < 0.001$), leaving $Z_1$ unchanged.

### 5. National Burden Prevalence
Survey-weighted analysis on the combined cohort ($n=1,477$) using NHANES complex survey design variables (PSUs, strata, and pooled examination weights `WTMEC_POOLED`) estimates that **$29.89\%$** of normal-BMI US adults (approximately **$23.91\text{ million}$** people, 95% CI: $[0.00\text{M}, 64.36\text{M}]$) carry a silent Dual-Burden.

---

## ⚙️ Model Architecture: DA-SS-iVAE

The core architecture is a **Dual-Anchored Semi-Supervised Identifiable Variational Autoencoder (DA-SS-iVAE)**.

```
                       [Auxiliary Demographics u]
                                   │
                                   ▼
[14 Biomarkers x] ──► [Residual Encoder q_φ(z|x,u)] ──► [2D Latent Space z = (z₁, z₂)]
                                                               │  │
                        ┌──────────────────────────────────────┘  └───────────────────┐
                        ▼                                                             ▼
             [Monotone Anchor 1]                                           [Monotone Anchor 2]
             ŷ_homa = f_anchor1(z₁)                                        ŷ_cap = f_anchor2(z₂)
              (Target: HOMA-IR)                                              (Target: CAP)
```

Identifiability (ensuring the VAE axes are non-arbitrary and biologically aligned) is achieved by conditioning the prior $p_\theta(z|u)$ on demographics $u$ (satisfying the Khemakhem et al. (2020) theorem) and constraining the anchor networks with monotone positive weights. The model trains semi-supervised, masking missing FibroScan CAP targets.

---

## 📂 Project Structure

```
├── backend/                  # FastAPI Backend API
│   ├── main.py               # API Endpoints (/infer, /counterfactual, etc.)
│   ├── schemas.py            # Input/Output Pydantic schemas (with strict validators)
│   └── model_registry.py     # Centralized model checkpoint loader
├── frontend/                 # React (Vite) + Tailwind + D3.js Visual Dashboard
│   ├── src/components/       # Atlas, Form, Equity and Readout Screens
│   └── src/App.jsx           # UI Router and Root Rendering
├── models/                   # Serialized VAE Checkpoints and scalers
│   ├── ivae_best.pt          # Trained PyTorch Model weights (869 KB)
│   ├── scaler.pkl            # Input RobustScaler model pipeline
│   └── conformal_surface.pkl # Mondrian Conformal calibration surfaces
├── results/                  # Experimental Results, Summary CSVS, and Figures
│   ├── symbolic_decoder/     # PySR Symbolic regression equations & LaTeX formulas
│   └── changes_summary.md    # Dissertation committee patch notes and summaries
├── src_code/                 # Core Python Library & Pipeline Logic
│   ├── data/                 # NHANES multi-cycle loading, schema & preprocessing
│   ├── model/                # VAE, Encoder, Decoder, Prior and Anchors definitions
│   ├── counterfactual/       # Riemannian geodesic ODE solver &Brent's inversion
│   ├── validation/           # Benchmarking, conformal testing & pharmacology PSM
│   └── training/             # PyTorch training loops & optuna sweeps
└── test_integration.py       # Comprehensive regression and monotonicity tests
```

---

## 🚀 Getting Started

### 1. Installation
Install core dependencies:
```bash
pip install -r requirements.txt
```
*(Optional)* Install PySR (requires Julia) for symbolic equation searches:
```bash
pip install pysr
```

### 2. Run Integration Tests
We maintain strict integration tests asserting schema order consistency, VAE monotonicity compliance, explainability gradient sums, and endpoint response boundaries:
```bash
python -m pytest test_integration.py -v
```

### 3. Run the Development API
Launch the FastAPI server (response times are optimized to P95 < 200ms using threaded non-blocking solvers):
```bash
uvicorn backend.main:app --reload
```
Interactive API docs will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Run the Visual Dashboard
Start the React visual client (dashboard displays a dark-themed Metabolic Atlas with counterfactual pathways and ancestral warning guards):
```bash
cd frontend
npm install
npm run dev
```

---

## 📈 Post-Hoc Interpretability & explainability

### Symbolic Decoder (PySR Formulae)
By mapping latent coordinates ($z_1, z_2$) back to biomarker levels via symbolic regression, we extract human-interpretable formulae confirming the model's geometric alignment:
*   **AIP (Atherogenic Index of Plasma):** $\text{AIP} = \left| (z_1 + z_2 + 0.131) \cdot (z_2 + 0.385) \right| + z_2$
*   **HDL Cholesterol:** $\text{HDL} = -17.13 \cdot (z_2 + z_1 + \left| z_2 \right|) + 61.04$

### Local Autograd Sensitivity Gradients
Clinicians receive local feature sensitivities ($\frac{\partial z_i}{\partial x_j}$) computed at the patient's position using PyTorch autograd. This identifies which specific biomarkers are driving the patient's metabolic risk coordinates.

---

## 📜 References & Citations
*   **VAE Identifiability Theorem:** Khemakhem et al., "Variational Autoencoders and Non-linear ICA", *NeurIPS* 2020.
*   **Conformal Impossibility Bound:** Barber et al., "Limits of Out-of-Distribution Conformal Prediction", *Annals of Statistics* 2023.
*   **Symbolic Regression Tool:** Cranmer et al., "Interpretable Machine Learning for Physics with Symbolic Regression", *arXiv:2006.11287*.
