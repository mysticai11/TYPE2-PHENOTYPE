# 🧬 LMSIS: Latent Metabolic State Inference System
> **A Clinical Machine Learning Pipeline for Detecting Silent Concurrent Metabolic Dysfunction in Normal-BMI Adults**

[![Integration Tests](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/frontend-React%20%7C%20Vite%20%7C%20Tailwind-61dafb.svg)](https://vitejs.dev/)

---

## 🎨 Latent Space & Geodesic Pathway Visualizer

![LMSIS Metabolic Atlas Geodesic Solver](results/figures/metabolic_atlas_animated.svg)

---

## 🔬 The Clinical Paradox

> *"Millions of adults worldwide receive a clean bill of health at their annual physical simply because their Body Mass Index (BMI) falls within the normal range ($18.5 \le \text{BMI} \le 24.9 \text{ kg/m}^2$). However, BMI is blind to fat distribution and ectopic tissue accumulation. Underneath a healthy-looking exterior, a patient may carry a silent, severe dual metabolic burden—simultaneous insulin resistance and hepatic steatosis—invisible to traditional screening and standard clinical markers."*

**LMSIS** addresses this gap by training a **Dual-Anchored Semi-Supervised Identifiable Variational Autoencoder (DA-SS-iVAE)**. It recovers a continuous 2D latent metabolic geometry from 14 routine blood biomarkers, validated against gold-standard FibroScan ultrasound elastography.

```mermaid
flowchart TD
    subgraph Input ["📋 Patient Inputs (Routine Profile)"]
        B1["14 Blood Biomarkers (x)"]
        B2["6 Demographic Conditioners (u)"]
    end

    subgraph Core ["🧠 DA-SS-iVAE Pipeline"]
        Enc["Conditional Encoder q_φ(z | x, u)"]
        Lat["2D Latent Space z = (z₁, z₂)"]
        Dec["Biomarker Decoder p_θ(x | z)"]
    end

    subgraph Grounding ["🔗 Monotone Biological Anchors"]
        A1["Monotone Anchor 1: g_1(z₁)"]
        A2["Monotone Anchor 2: g_2(z₂)"]
        T1["Target: HOMA-IR (Insulin Resistance)"]
        T2["Target: FibroScan CAP (Liver Fat)"]
    end

    B1 --> Enc
    B2 --> Enc
    Enc --> Lat
    Lat --> Dec
    Dec -->|"Reconstructs"| B1
    
    Lat -->|z₁| A1
    Lat -->|z₂| A2
    A1 -->|"Monotone Fit"| T1
    A2 -->|"Masked (Semi-Supervised)"| T2
```

---

## 📊 Benchmarking & Performance Comparison

We evaluate our model against standard clinical indicators on the normal-BMI cohort, ensuring complete empirical transparency:

### 1. Temporal Out-of-Distribution (OOD) Validation
> [!NOTE]
> **Takeaway:** Generalization is tested on an independent pre-pandemic cohort (P-Cycle). The drop in CAP correlation ($\sim 0.13$) represents a standard, honest cohort shift, but retains extreme statistical significance ($p < 10^{-55}$).

| Metric | J-Cycle (Train / 2017-2018) | P-Cycle (OOD / 2019-2020) | Status |
| :--- | :---: | :---: | :---: |
| **Fasting Cohort Size ($n$)** | 574 | 903 | — |
| **CAP-Labeled Size ($n$)** | 552 | 870 | — |
| **$Z_2$ vs. CAP Spearman $\rho$** | **$0.628$** | **$0.501$** | **✅ Generalises** |
| **P-value** | $6.43 \times 10^{-62}$ | $1.85 \times 10^{-56}$ | **✅ Significant** |
| **Reconstruction MSE** | $2.221$ | $2.734$ | **✅ Stable** |
| **Conformal Coverage** | $90.4\%$ | **$95.2\%$** | **✅ Safe Transfer** |

---

### 2. Clinical Benchmarks Comparison
> [!IMPORTANT]
> **Takeaway:** Existing clinical indices degrade because they are linearly dependent on BMI. Constraining the population to normal BMI (18.5–24.9) strips their discriminative signal.

| Model / Index | Spearman $\rho$ vs. CAP | AUROC ($\text{CAP} \ge 248$) | AUROC ($\text{CAP} \ge 268$) | Clinical Verdict |
| :--- | :---: | :---: | :---: | :--- |
| **HSI (Hepatic Steatosis Index)** | $0.111$ | $0.587$ | $0.557$ | **Degraded** (Near-Random) |
| **NAFLD-LFS (Liver Fat Score)** | $-0.069$ | $0.509$ | $0.512$ | **🚨 Inverse Association** (Ranks backwards) |
| **FLI (Fatty Liver Index)** | $0.447$ | $0.740$ | $0.766$ | **Suboptimal** (High variance) |
| **TyG (Triglyceride-Glucose)** | $0.358$ | $0.710$ | $0.736$ | **Moderate** (Insulin-only proxy) |
| **LMSIS VAE Axis $Z_2$** | **$0.607$** | **$0.841$** | **$0.833$** | **🏆 Imaging Grade** (Robust) |

---

### 3. Conformal Safety Calibration
> [!CAUTION]
> **Takeaway:** Under covariate shift, standard marginal calibration fails to cover the highest-risk Dual-Burden subgroup ($81.62\%$). Mondrian calibration guarantees safe subgroup coverage ($\ge 90\%$).

| Phenotypic Quadrant | Subgroup Size ($n$) | Marginal Coverage | Mondrian Coverage | Nominal Target | Patient Safety |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **MHNW (Healthy)** | 168 | $98.21\%$ | $98.21\%$ | $90.0\%$ | **Safe** |
| **IR-Dominant** | 129 | $93.80\%$ | $100.00\%$ | $90.0\%$ | **Safe** |
| **Steatosis-Dominant** | 185 | $87.03\%$ | $98.92\%$ | $90.0\%$ | **Safe** |
| **Dual-Burden (High-Risk)** | 136 | **$81.62\%$** ⚠️ | **$90.44\%$** | $90.0\%$ | **Restored by Mondrian** |

---

### 🔍 Important Scientific Disclosures
* **Temporal Correlation Drop ($0.628 \rightarrow 0.501$):** A drop of $\sim0.13$ is expected when evaluating a frozen, unadapted model on a temporally separate cohort (pre-pandemic 2019-2020). The fact that the correlation remains highly significant ($p = 1.85 \times 10^{-56}$ on $n=870$) confirms the pipeline's robustness.
* **The HSI / NAFLD-LFS Collapse:** HSI fails because it relies heavily on BMI, which is invariant in this cohort. NAFLD-LFS exhibits a negative correlation because metabolic syndrome criteria correlate positively with liver fat in mixed-BMI cohorts but negatively in normal-BMI cohorts.
* **Asian American HOMA-IR Cutoff (0.96):** While clinical literature supports lower metabolic thresholds for Asian ancestry, our calculated threshold of $0.96$ is derived from a small subpopulation ($n=12$ in the critical HOMA-IR reference band $[2.3, 2.7]$). We treat this finding strictly as *hypothesis-generating* and have demoted it from our main results.

---

## ⚙️ Model Architecture: DA-SS-iVAE

Standard VAEs fail metabolic phenotyping because their latent spaces are **non-identifiable** (arbitrary rotations achieve identical reconstruction error). LMSIS resolves this through:
1. **iVAE Identifiability (Khemakhem et al., 2020):** Conditioning the prior $p_\theta(z|u)$ on demographics $u$ (age, sex, ancestry).
2. **Dual Monotone Anchoring:** Constraining anchor networks using a Softplus activation on weights, forcing $z_1 \rightarrow \text{HOMA-IR}$ and $z_2 \rightarrow \text{CAP}$ to be strictly monotonic.
3. **Semi-Supervised Masking:** Leveraging all $1,477$ cohort participants for the $Z_1$ anchor, while masking the $Z_2$ anchor for the $55$ participants missing FibroScan records.

---

## 📂 Repository Structure

```
├── backend/                  # FastAPI Backend API
│   ├── main.py               # API Endpoints (/infer, /counterfactual, /geodesic_pathway)
│   ├── schemas.py            # Input/Output Pydantic schemas (with strict validators)
│   └── model_registry.py     # Centralized model checkpoint loader
├── frontend/                 # React (Vite) + Tailwind + D3.js Visual Dashboard
│   ├── src/components/       # Atlas, Form, Equity and Readout Screens
│   └── src/App.jsx           # UI Router and Root Rendering
├── models/                   # Serialized VAE Checkpoints and scalers
│   ├── ivae_best.pt          # Trained PyTorch Model weights (869 KB)
│   ├── scaler.pkl            # Input RobustScaler model pipeline
│   └── conformal_surface.pkl # Mondrian Conformal calibration surfaces
├── results/                  # Experimental Results, Summary CSVs, and Figures
│   └── symbolic_decoder/     # PySR Symbolic regression equations & LaTeX formulas
├── src_code/                 # Core Python Library & Pipeline Logic
│   ├── data/                 # NHANES multi-cycle loading, schema & preprocessing
│   ├── model/                # VAE, Encoder, Decoder, Prior and Anchors definitions
│   ├── counterfactual/       # Riemannian geodesic ODE solver & Brent's inversion
│   └── validation/           # Benchmarking, conformal testing & pharmacology PSM
└── test_integration.py       # Comprehensive regression and monotonicity tests
```

---

## 🚀 Getting Started

### 1. Installation
Clone the repository and install core dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run Integration Tests
Assert system safety, FastAPI endpoints, monotonicity bounds, and VAE weight alignments:
```bash
python -m pytest test_integration.py -v
```

### 3. Launch FastAPI Development Server
```bash
uvicorn backend.main:app --reload
```
Interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Launch visual Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser to interact with the **Metabolic Atlas**.

---

## 📈 Explainability & Interpretability

### 🧬 Symbolic Decoder Discoveries (PySR)
By fitting symbolic formulas to the frozen VAE decoder using symbolic regression (PySR), we map the latent axes ($z_1$: Insulin Resistance, $z_2$: Liver Fat) back to physical laws:

| Target Biomarker | Discovered Symbolic Formula | Loss | Biological Pathway |
| :--- | :--- | :---: | :--- |
| **HDL Cholesterol** | $hdl = -17.13 \cdot (z_1 + z_2 + \|z_2\|) + 61.04$ | $0.721$ | **HDL Suppression:** Both axes suppress HDL. |
| **AIP (Atherogenic Index)** | $aip = \|(z_1 + z_2 + 0.131) \cdot (z_2 + 0.385)\| + z_2$ | $0.0005$ | **Atherogenesis:** Risk peaks at Dual-Burden. |
| **AST:ALT Ratio** | $ast\_alt = 11.59^{z_2} \cdot (4.64 - \|z_1 - z_2\|)$ | $0.018$ | **Hepatic Injury:** Exponential steatosis drive. |
| **Triglycerides** | $triglycerides = (z_2 + 2.00)^{z_1 + 6.36}$ | $31.95$ | **Lipid Synthesis:** Power law IR scaling. |
| **TyG Index** | $tyg = 0.696 \cdot \|z_1 + z_2\| + 4.66 + e^{z_2 + 1.26} + z_1 z_2 + z_1$ | $0.002$ | **Insulin-Lipid Loop:** Joint representation. |

### 🧮 Local Autograd Sensitivity Gradients
Rather than relying on global feature importance, the FastAPI backend uses PyTorch Autograd to calculate patient-specific local gradients:
$$\text{Sensitivity} = \frac{\partial z_i}{\partial x_j}$$
This provides clinicians with real-time feedback on which biomarkers are driving a patient's position on the metabolic map at that exact moment.

---

## ⚠️ Limitations & Future Directions

While LMSIS represents a major step forward, its deployment in clinical workflows is subject to several active research limitations:
1. **Ancestral Sample Constraints:** The Non-Hispanic Asian HOMA-IR shift is highly significant ($p = 2.67 \times 10^{-3}$) but based on a small cohort ($n=12$ in reference band).
2. **Cross-Sectional Snapshots:** NHANES data provides cross-sectional slices. We cannot infer longitudinal trajectories without cohort follow-up.
3. **Validation Strategy:** Immediate next steps involve validating the frozen model on **KNHANES** (Korea National Health and Nutrition Examination Survey) to replicate the Asian threshold finding on thousands of subjects, and **UK Biobank** to test cross-modal generalization (CAP to MRI-PDFF).

---

## 📜 References & Citations
*   **iVAE Identifiability:** Khemakhem et al., "Variational Autoencoders and Non-linear ICA", *NeurIPS* 2020.
*   **Conformal Impossibility Bound:** Barber et al., "Limits of Out-of-Distribution Conformal Prediction", *Annals of Statistics* 2023.
*   **Symbolic Regression Tool:** Cranmer et al., "Interpretable Machine Learning for Physics with Symbolic Regression", *arXiv:2006.11287*.
*   **Lean MASLD Review:** Dey et al., "The Pathogenesis and Management of Lean NAFLD", *Frontiers in Endocrinology* 2025.
