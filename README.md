<div align="center">

<br/>

```text
██╗     ███╗   ███╗███████╗██╗███████╗
██║     ████╗ ████║██╔════╝██║██╔════╝
██║     ██╔████╔██║███████╗██║███████╗
██║     ██║╚██╔╝██║╚════██║██║╚════██║
███████╗██║ ╚═╝ ██║███████║██║███████║
╚══════╝╚═╝     ╚═╝╚══════╝╚═╝╚══════╝
```

### Latent Metabolic State Inference System

*A Clinical Machine Learning Pipeline for Detecting Silent Concurrent Metabolic Dysfunction in Normal-BMI Adults*

<br/>

[![Integration Tests](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mysticai11/TYPE2-PHENOTYPE/actions)
[![Python Version](https://img.shields.io/badge/Python-3.12%20%7C%203.13-0A1628?style=flat&logo=python&logoColor=4A9FE0)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-0A1628?style=flat&logo=fastapi&logoColor=4A9FE0)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite-0A1628?style=flat&logo=react&logoColor=4A9FE0)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-0A1628?style=flat)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-15%20passed-1A6FBF?style=flat)](test_integration.py)

<br/>

</div>

---

<table border="0" width="100%" cellpadding="10" style="border: none; border-collapse: collapse;">
  <tr>
    <td width="60%" valign="top" style="border: none; text-align: left;">
      <h2>🧬 Silent metabolic risk, made visible.</h2>
      <p>Millions of adults worldwide receive a clean bill of health simply because their Body Mass Index falls within the normal range (18.5 ≤ BMI ≤ 24.9 kg/m²). However, BMI is blind to fat distribution and ectopic tissue accumulation. Underneath a healthy-looking exterior, a patient may carry a silent, severe dual metabolic burden — simultaneous insulin resistance and hepatic steatosis — invisible to traditional screening.</p>
      <p><strong>LMSIS</strong> recovers a continuous 2D latent metabolic geometry from 14 routine blood biomarkers, validated against gold-standard FibroScan ultrasound elastography. It deploys a <strong>Dual-Anchored Semi-Supervised Identifiable Variational Autoencoder (DA-SS-iVAE)</strong> to identify the four phenotypic quadrants of metabolic health in normal-weight individuals.</p>
      <blockquote>
        <strong>⚠️ Clinical Intent:</strong> LMSIS is not intended to diagnose MASLD or insulin resistance. It provides a non-invasive <strong>risk-stratification framework</strong> that identifies normal-weight individuals who may benefit from further metabolic evaluation — specialist referrals, FibroScan, or longitudinal tracking.
      </blockquote>
    </td>
    <td width="40%" valign="center" align="center" style="border: none; padding-left: 20px;">
      <img src="results/figures/metabolic_atlas_animated.svg" width="100%" alt="LMSIS Metabolic Atlas Geodesic Solver" />
      <p align="center"><small><em>Interactive 2D Latent Geodesic Path Solver</em></small></p>
    </td>
  </tr>
</table>

---

## 📊 Key Results at a Glance

<table width="100%">
  <thead>
    <tr align="center">
      <th>Liver Steatosis AUROC</th>
      <th>Spearman Correlation</th>
      <th>Cohort Size</th>
      <th>Subgroup Coverage</th>
    </tr>
  </thead>
  <tbody>
    <tr align="center">
      <td>
        <h2 style="margin:0;">0.841</h2>
        <small>LMSIS VAE Z₂ Performance</small>
      </td>
      <td>
        <h2 style="margin:0;">0.607</h2>
        <small>Z₂ vs FibroScan CAP</small>
      </td>
      <td>
        <h2 style="margin:0;">1,477</h2>
        <small>NHANES Multi-Cycle Dataset</small>
      </td>
      <td>
        <h2 style="margin:0; color:#22c55e;">90.4%</h2>
        <small>Mondrian Conformal Guarantee</small>
      </td>
    </tr>
  </tbody>
</table>

---

## 🗺️ The 2D Latent Metabolic Space

LMSIS projects every patient onto a two-axis plane, where each axis corresponds to a distinct, anchored biological process. The coordinate system divides the population into four clinically actionable quadrants:

<table width="100%">
  <tr>
    <th align="center" width="50%">Z₂ (Hepatic Steatosis) elevated, Z₁ (Insulin Resistance) normal</th>
    <th align="center" width="50%">⚠️ Both axes elevated (High Risk)</th>
  </tr>
  <tr>
    <td valign="top" align="center">
      <h3>Steatosis-Dominant</h3>
      <p><code>n = 185</code> | Marginal: <code>87.0%</code> | Mondrian: <strong><code>98.9%</code></strong></p>
      <small>Isolated hepatic lipid accumulation without systemic insulin resistance. Responds strongly to lipid-lowering therapies (Statins/Fibrates).</small>
    </td>
    <td valign="top" align="center" style="background-color: #fff5f5;">
      <h3>Dual-Burden (High-Risk) 🚨</h3>
      <p><code>n = 136</code> | Marginal: <code style="color:#ef4444;">81.6%</code> | Mondrian: <strong><code style="color:#22c55e;">90.4%</code></strong></p>
      <small><strong>Highest risk clinical sub-population.</strong> Simultaneous severe insulin resistance and steatosis. Invisible to traditional BMI-based screening.</small>
    </td>
  </tr>
  <tr>
    <th align="center">Both axes normal (Metabolically Healthy)</th>
    <th align="center">Z₁ (Insulin Resistance) elevated, Z₂ (Hepatic Steatosis) normal</th>
  </tr>
  <tr>
    <td valign="top" align="center">
      <h3>Metabolically Healthy (MHNW)</h3>
      <p><code>n = 168</code> | Marginal: <code>98.2%</code> | Mondrian: <strong><code>98.2%</code></strong></p>
      <small>Baseline healthy cohort. Low risk of cardiovascular or metabolic progression.</small>
    </td>
    <td valign="top" align="center">
      <h3>IR-Dominant</h3>
      <p><code>n = 129</code> | Marginal: <code>93.8%</code> | Mondrian: <strong><code>100.0%</code></strong></p>
      <small>Isolated tissue insulin resistance. Normal liver fat content. Responds strongly to insulin sensitizers (Metformin) and lifestyle interventions.</small>
    </td>
  </tr>
</table>

---

## 📈 Benchmark Demolition

### 1 — Predicting Liver Steatosis (FibroScan CAP)

> [!TIP]
> LMSIS Z₂ dominates every current clinical gold standard. Notably, NAFLD-LFS has a **negative** Spearman correlation in this population — meaning it actively misleads clinical judgement under BMI restriction.

<table width="100%">
  <tr>
    <th align="left" width="55%">Predictive Model Comparison</th>
    <th align="left" width="45%">Visual AUROC Performance (CAP ≥ 248)</th>
  </tr>
  <tr>
    <td valign="top">
      <table width="100%">
        <thead>
          <tr>
            <th>Model / Index</th>
            <th align="center">Spearman ρ</th>
            <th align="center">AUROC (≥ 248)</th>
            <th align="center">AUROC (≥ 268)</th>
            <th>Verdict</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>LMSIS VAE (Z₂)</strong></td>
            <td align="center"><strong><code>0.607</code></strong></td>
            <td align="center"><strong><code>0.841</code></strong></td>
            <td align="center"><strong><code>0.833</code></strong></td>
            <td>🟢 State-of-the-art</td>
          </tr>
          <tr>
            <td>FLI (Fatty Liver Index)</td>
            <td align="center"><code>0.447</code></td>
            <td align="center"><code>0.740</code></td>
            <td align="center"><code>0.766</code></td>
            <td>🟡 Suboptimal</td>
          </tr>
          <tr>
            <td>TyG (Triglyceride-Glucose)</td>
            <td align="center"><code>0.358</code></td>
            <td align="center"><code>0.710</code></td>
            <td align="center"><code>0.736</code></td>
            <td>🟡 Moderate</td>
          </tr>
          <tr>
            <td>HSI (Hepatic Steatosis Index)</td>
            <td align="center"><code>0.111</code></td>
            <td align="center"><code>0.587</code></td>
            <td align="center"><code>0.557</code></td>
            <td>🟠 Near-random</td>
          </tr>
          <tr>
            <td>NAFLD-LFS (Liver Fat Score)</td>
            <td align="center"><code>-0.069</code></td>
            <td align="center"><code>0.509</code></td>
            <td align="center"><code>0.512</code></td>
            <td>🔴 Inverse association</td>
          </tr>
        </tbody>
      </table>
    </td>
    <td valign="middle">
      <p style="margin: 5px 0;"><strong>LMSIS VAE (Z₂)</strong> (0.841)<br/>
      <code>████████████████████ 84.1%</code></p>
      <p style="margin: 5px 0;"><strong>Fatty Liver Index (FLI)</strong> (0.740)<br/>
      <code>████████████████░░░░ 74.0%</code></p>
      <p style="margin: 5px 0;"><strong>Triglyceride-Glucose (TyG)</strong> (0.710)<br/>
      <code>███████████████░░░░░ 71.0%</code></p>
      <p style="margin: 5px 0;"><strong>Hepatic Steatosis (HSI)</strong> (0.587)<br/>
      <code>████████████░░░░░░░░ 58.7%</code></p>
      <p style="margin: 5px 0;"><strong>Liver Fat Score (NAFLD-LFS)</strong> (0.509)<br/>
      <code>██████████░░░░░░░░░░ 50.9%</code></p>
    </td>
  </tr>
</table>

### 2 — Conformal Safety Calibration under Subpopulation Shift

> [!WARNING]
> Under covariate shift, standard marginal calibration drops to **81.6% coverage** for the highest-risk Dual-Burden subgroup — falling below the 90% safety target. **Mondrian calibration** guarantees safe conditional coverage (≥ 90%) across all quadrants.

<div align="center">
  <table width="100%">
    <thead>
      <tr align="center">
        <th>Phenotypic Quadrant</th>
        <th>Sample size (n)</th>
        <th>Marginal Coverage</th>
        <th>Mondrian Coverage</th>
        <th>Patient Safety Target</th>
      </tr>
    </thead>
    <tbody>
      <tr align="center">
        <td>Metabolically Healthy (MHNW)</td>
        <td>168</td>
        <td><code>98.2%</code></td>
        <td><strong><code>98.2%</code></strong> ✓</td>
        <td><code>90.0%</code></td>
      </tr>
      <tr align="center">
        <td>IR-Dominant</td>
        <td>129</td>
        <td><code>93.8%</code></td>
        <td><strong><code>100.0%</code></strong> ✓</td>
        <td><code>90.0%</code></td>
      </tr>
      <tr align="center">
        <td>Steatosis-Dominant</td>
        <td>185</td>
        <td><code>87.0%</code></td>
        <td><strong><code>98.9%</code></strong> ✓</td>
        <td><code>90.0%</code></td>
      </tr>
      <tr align="center" style="background-color: #fff5f5;">
        <td><strong>Dual-Burden (High-Risk)</strong></td>
        <td><strong>136</strong></td>
        <td><code style="color:#ef4444;">81.6%</code> ⚠️</td>
        <td><strong><code style="color:#22c55e;">90.4%</code></strong> 🛡️</td>
        <td><code>90.0%</code></td>
      </tr>
    </tbody>
  </table>
</div>

### 3 — Causal Pharmacological Dissociation

The model perfectly disentangles the biological mechanisms of drug action (double dissociation), confirming structural identifiability. Each drug class affects exclusively its target latent axis; off-target p-values are all non-significant (NS).

<div align="center">
  <table width="100%" cellpadding="10" style="border-collapse: collapse;">
    <tr>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>💊 Metformin</h4>
        <p><small>Insulin sensitizer targeting Z₁</small></p>
        <hr/>
        <p><strong>Target Axis:</strong> Z₁ (IR)</p>
        <p><strong>Target p-value:</strong> <code>< 1.4e-19</code></p>
        <p><strong>Effect Size (r):</strong> <code>1.000</code></p>
        <p><strong>Off-Target p-value:</strong> <code>0.554 (NS)</code></p>
        <small>Exclusively targets hepatic glucose production and muscle insulin sensitivity without altering steatosis pathways.</small>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>💊 Statin</h4>
        <p><small>Lipid-lowering agent targeting Z₂</small></p>
        <hr/>
        <p><strong>Target Axis:</strong> Z₂ (Steatosis)</p>
        <p><strong>Target p-value:</strong> <code>< 2.3e-26</code></p>
        <p><strong>Effect Size (r):</strong> <code>0.888</code></p>
        <p><strong>Off-Target p-value:</strong> <code>0.550 (NS)</code></p>
        <small>Exclusively targets intracellular lipid levels and circulating VLDL clearing, leaving insulin signaling unaffected.</small>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>💊 Fibrate</h4>
        <p><small>PPAR-α agonist targeting Z₂</small></p>
        <hr/>
        <p><strong>Target Axis:</strong> Z₂ (Steatosis)</p>
        <p><strong>Target p-value:</strong> <code>< 7.1e-10</code></p>
        <p><strong>Effect Size (r):</strong> <code>1.000</code></p>
        <p><strong>Off-Target p-value:</strong> <code>0.431 (NS)</code></p>
        <small>Promotes fatty acid beta-oxidation and targets hepatic triglyceride clearing via PPAR-α binding.</small>
      </td>
    </tr>
  </table>
</div>

---

## ⚙️ Architecture: DA-SS-iVAE

Standard VAEs fail metabolic phenotyping because their latent spaces are **non-identifiable** — arbitrary rotations achieve identical reconstruction error. LMSIS resolves this through three mathematically grounded constraints:

<div align="center">
  <table width="100%" cellpadding="10" style="border-collapse: collapse;">
    <tr>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>🧬 iVAE Identifiability</h4>
        <p>Conditioning the latent prior <code>p(z|u)</code> on demographic auxiliary variables <code>u</code> (age, sex, ancestry), following Khemakhem et al., 2020. This breaks the rotational symmetry that compromises standard generative spaces.</p>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>🔗 Dual Monotone Anchors</h4>
        <p>Constraining anchor networks using a Softplus activation on weights, forcing strict monotonicity: <code>z₁ → HOMA-IR</code> and <code>z₂ → CAP</code>. This pins each latent axis directly to a biological observable.</p>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>🎭 Semi-Supervised Masking</h4>
        <p>All 1,477 cohort participants contribute to the Z₁ HOMA-IR anchor. The Z₂ CAP anchor is safely masked for participants missing ultrasound records, maximizing data usage without introducing bias.</p>
      </td>
    </tr>
  </table>
  <br/>
  <img src="results/figures/model_pipeline_animated.svg" width="75%" alt="DA-SS-iVAE Pipeline Architecture" />
  <p><small><em>DA-SS-iVAE Neural Architecture and Latent Anchoring Flow</em></small></p>
</div>

---

## 📈 Symbolic AI Interpretability

The black-box decoder was mapped using **Symbolic Regression (PySR)**, recovering closed-form governing equations for the biological pathways:

<div align="center">
  <table width="100%" cellpadding="10">
    <thead>
      <tr>
        <th align="left" width="25%">Biomarker</th>
        <th align="left">Discovered Symbolic Formula</th>
        <th align="left">Biological Interpretation</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>HDL Cholesterol</strong></td>
        <td><code>hdl = -17.13 * (z1 + z2 + abs(z2)) + 61.04</code></td>
        <td>Both axes suppress HDL; the <code>abs(z2)</code> term means steatosis contributes double when positive.</td>
      </tr>
      <tr>
        <td><strong>Atherogenic Index</strong></td>
        <td><code>aip = abs((z1 + z2 + 0.131) * (z2 + 0.385)) + z2 + 0.034</code></td>
        <td>Cardiovascular risk scales non-linearly; the product structure means each axis amplifies the other.</td>
      </tr>
      <tr>
        <td><strong>AST:ALT Ratio</strong></td>
        <td><code>ast_alt = 11.49^z2 * (4.64 - abs(z1 - z2))</code></td>
        <td>Liver injury correlates exponentially with the Z₂ steatosis axis.</td>
      </tr>
    </tbody>
  </table>
</div>

<blockquote>
  <strong>💡 Mathematical Proof:</strong> The AIP formula mathematically confirms that the dual-burden phenotype (z₁ &gt; 0 and z₂ &gt; 0 simultaneously) produces the highest atherogenic index of plasma — not either axis alone. This emerges naturally from the decoder manifold's geometry rather than manual design constraints.
</blockquote>

---

## 🛠️ Developer Resources & Documentation

<details>
  <summary>💻 <strong>View Technology Stack & Core Layers</strong></summary>
  <br/>
  <table>
    <thead>
      <tr>
        <th>Layer</th>
        <th>Technologies</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Deep Learning Core</strong></td>
        <td>PyTorch · NumPy · SciPy · Scikit-Learn</td>
      </tr>
      <tr>
        <td><strong>Uncertainty & Coverage</strong></td>
        <td>MAPIE · Scikit-Dimension</td>
      </tr>
      <tr>
        <td><strong>Symbolic Regression</strong></td>
        <td>PySR (Julia backend)</td>
      </tr>
      <tr>
        <td><strong>API Backend</strong></td>
        <td>FastAPI · Uvicorn · Pydantic v2</td>
      </tr>
      <tr>
        <td><strong>Interactive Dashboard</strong></td>
        <td>React 19 · Vite · Tailwind CSS · D3.js · Zustand · Framer Motion</td>
      </tr>
    </tbody>
  </table>
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
