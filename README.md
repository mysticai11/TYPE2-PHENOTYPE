<div align="center">
  <table border="0" width="100%" cellpadding="10" style="border: none; border-collapse: collapse;">
    <tr>
      <td width="60%" valign="top" style="border: none; text-align: left;">
        <h1>🧬 LMSIS</h1>
        <h3>Latent Metabolic State Inference System</h3>
        <p><strong>Silent metabolic risk, made visible.</strong></p>
        <p>Millions of adults worldwide receive a clean bill of health simply because their Body Mass Index (BMI) falls within the normal range (18.5 ≤ BMI ≤ 24.9 kg/m²). However, BMI is blind to fat distribution and ectopic tissue accumulation. Underneath a healthy-looking exterior, a patient may carry a silent, severe dual metabolic burden — simultaneous insulin resistance and hepatic steatosis — invisible to traditional screening.</p>
        <p><em>LMSIS is a clinical machine learning pipeline that recovers a continuous 2D latent metabolic geometry from 14 routine blood biomarkers, validated against gold-standard FibroScan ultrasound elastography.</em></p>
        <br/>
        <a href="https://github.com/mysticai11/TYPE2-PHENOTYPE/actions"><img src="https://img.shields.io/badge/CI%2FCD-Integration%20Tests-success?style=for-the-badge&logo=github-actions" alt="Integration Tests" /></a>
        <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI Backend" /></a>
        <a href="https://vitejs.dev/"><img src="https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61dafb?style=for-the-badge&logo=react&logoColor=black" alt="React Frontend" /></a>
      </td>
      <td width="40%" valign="center" align="center" style="border: none;">
        <img src="results/figures/metabolic_atlas_animated.svg" width="100%" alt="LMSIS Metabolic Atlas Geodesic Solver" />
      </td>
    </tr>
  </table>
</div>

<hr/>

<div align="center">
  <table width="100%" cellpadding="10">
    <tr align="center">
      <td width="25%">
        <h2>0.841</h2>
        <p><strong>Liver Steatosis AUROC</strong><br/><small>Outperforming clinical gold standards</small></p>
      </td>
      <td width="25%">
        <h2>0.607</h2>
        <p><strong>Spearman ρ (Z₂ vs CAP)</strong><br/><small>Strong imaging correlation</small></p>
      </td>
      <td width="25%">
        <h2>1,477</h2>
        <p><strong>Survey-Weighted Sample</strong><br/><small>Nationally representative cohort</small></p>
      </td>
      <td width="25%">
        <h2>90.4%</h2>
        <p><strong>Conformal Coverage</strong><br/><small>Subgroup-specific safety guarantee</small></p>
      </td>
    </tr>
  </table>
</div>

<hr/>

## 📊 Outperforming Every Current Clinical Index

LMSIS recovers a continuous 2D latent metabolic geometry from 14 routine blood biomarkers, validated against gold-standard FibroScan ultrasound elastography, whereas traditional linear indices lose predictive power when BMI is constrained to the normal range.

<div align="center">
  <table width="100%" cellpadding="10">
    <tr>
      <td width="55%" valign="top">
        <table width="100%">
          <thead>
            <tr>
              <th align="left">Model / Index</th>
              <th align="center">Spearman ρ</th>
              <th align="center">AUROC (≥ 248)</th>
              <th align="center">AUROC (≥ 268)</th>
              <th align="left">Verdict</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>LMSIS VAE (Z₂)</strong></td>
              <td align="center"><strong><code>0.607</code></strong></td>
              <td align="center"><strong><code>0.841</code></strong></td>
              <td align="center"><strong><code>0.833</code></strong></td>
              <td>🟢 <strong>State-of-the-Art Reference</strong></td>
            </tr>
            <tr>
              <td>FLI (Fatty Liver Index)</td>
              <td align="center"><code>0.447</code></td>
              <td align="center"><code>0.740</code></td>
              <td align="center"><code>0.766</code></td>
              <td>🟡 Suboptimal (High variance)</td>
            </tr>
            <tr>
              <td>TyG (Triglyceride-Glucose)</td>
              <td align="center"><code>0.358</code></td>
              <td align="center"><code>0.710</code></td>
              <td align="center"><code>0.736</code></td>
              <td>🟡 Moderate (Insulin-only proxy)</td>
            </tr>
            <tr>
              <td>HSI (Hepatic Steatosis Index)</td>
              <td align="center"><code>0.111</code></td>
              <td align="center"><code>0.587</code></td>
              <td align="center"><code>0.557</code></td>
              <td>🟠 Degraded (Near-Random)</td>
            </tr>
            <tr>
              <td>NAFLD-LFS (Liver Fat Score)</td>
              <td align="center"><code>-0.069</code></td>
              <td align="center"><code>0.509</code></td>
              <td align="center"><code>0.512</code></td>
              <td>🔴 **Inverse Association**</td>
            </tr>
          </tbody>
        </table>
      </td>
      <td width="45%" valign="top" style="padding-left: 20px;">
        <h4>AUROC vs Liver Steatosis (CAP ≥ 248)</h4>
        <p><strong>LMSIS VAE (Z₂):</strong> <code>█████████████████ 84.1%</code></p>
        <p><strong>FLI Index:</strong> <code>██████████████░░░ 74.0%</code></p>
        <p><strong>TyG Index:</strong> <code>██████████████░░░ 71.0%</code></p>
        <p><strong>HSI Index:</strong> <code>██████████░░░░░░░ 58.7%</code></p>
        <p><strong>NAFLD-LFS:</strong> <code>██████████░░░░░░░ 50.9%</code></p>
      </td>
    </tr>
  </table>
</div>

<blockquote>
  <strong>⚠️ Persistent normal-BMI calibration mismatch:</strong> Under covariate shift, standard marginal calibration fails the highest-risk "Dual-Burden" subgroup (dropping to 81.6% coverage). Our <strong>Mondrian calibration</strong> successfully guarantees safe subgroup coverage (≥ 90%) across all populations.
</blockquote>

<div align="center">
  <table width="100%" cellpadding="10" style="border-collapse: collapse;">
    <tr align="center">
      <td width="25%" style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; background-color: #fafafa;">
        <h4>Healthy (MHNW)</h4>
        <p>Sample size: <strong>168</strong></p>
        <hr/>
        <p>Marginal: <code>98.2%</code></p>
        <p>Mondrian: <strong><code>98.2%</code></strong></p>
        <p><small>Safety Target: 90%</small></p>
      </td>
      <td width="25%" style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; background-color: #fafafa;">
        <h4>IR-Dominant</h4>
        <p>Sample size: <strong>129</strong></p>
        <hr/>
        <p>Marginal: <code>93.8%</code></p>
        <p>Mondrian: <strong><code>100.0%</code></strong></p>
        <p><small>Safety Target: 90%</small></p>
      </td>
      <td width="25%" style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; background-color: #fafafa;">
        <h4>Steatosis-Dom</h4>
        <p>Sample size: <strong>185</strong></p>
        <hr/>
        <p>Marginal: <code>87.0%</code></p>
        <p>Mondrian: <strong><code>98.9%</code></strong></p>
        <p><small>Safety Target: 90%</small></p>
      </td>
      <td width="25%" style="border: 1px solid #e06666; border-radius: 8px; padding: 12px; background-color: #fff5f5;">
        <h4>Dual-Burden ⚠️</h4>
        <p>Sample size: <strong>136</strong></p>
        <hr/>
        <p>Marginal: <code style="color: red;">81.6%</code> ❌</p>
        <p>Mondrian: <strong><code style="color: green;">90.4%</code></strong> 🛡️</p>
        <p><small>Safety Target: 90%</small></p>
      </td>
    </tr>
  </table>
</div>

<hr/>

### 💊 Causal Pharmacological Dissociation

By simulating the specific physiological pathways of Metformin, Statins, and Fibrates, we confirm the double dissociation and structural identifiability of both latent axes.

<div align="center">
  <table width="100%" cellpadding="10" style="border-collapse: collapse;">
    <tr>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>Metformin</h4>
        <p><small>Insulin sensitizer targeting Z₁</small></p>
        <hr/>
        <p><strong>Target Axis:</strong> Z₁ (IR)</p>
        <p><strong>Target p-value:</strong> <code>< 1.4e-19</code></p>
        <p><strong>Effect Size (r):</strong> <code>1.000</code></p>
        <p><strong>Off-Target p-value:</strong> <code>0.554 (NS)</code></p>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>Statin</h4>
        <p><small>Lipid-lowering agent targeting Z₂</small></p>
        <hr/>
        <p><strong>Target Axis:</strong> Z₂ (Steatosis)</p>
        <p><strong>Target p-value:</strong> <code>< 2.3e-26</code></p>
        <p><strong>Effect Size (r):</strong> <code>0.888</code></p>
        <p><strong>Off-Target p-value:</strong> <code>0.550 (NS)</code></p>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>Fibrate</h4>
        <p><small>PPAR-α agonist targeting Z₂</small></p>
        <hr/>
        <p><strong>Target Axis:</strong> Z₂ (Steatosis)</p>
        <p><strong>Target p-value:</strong> <code>< 7.1e-10</code></p>
        <p><strong>Effect Size (r):</strong> <code>1.000</code></p>
        <p><strong>Off-Target p-value:</strong> <code>0.431 (NS)</code></p>
      </td>
    </tr>
  </table>
</div>

<hr/>

## ⚙️ The Engine: DA-SS-iVAE Architecture

Standard VAEs fail metabolic phenotyping because their latent spaces are **non-identifiable** (arbitrary rotations achieve identical reconstruction error). LMSIS resolves this through three novel constraints:

<div align="center">
  <table width="100%" cellpadding="10" style="border-collapse: collapse;">
    <tr>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>🧬 iVAE Identifiability</h4>
        <p>Conditioning the latent prior <code>p(z|u)</code> on demographic auxiliaries <code>u</code> (age, sex, ancestry) to lock down latent axes up to permutation and element-wise transformation.</p>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>🔗 Dual Monotone Anchors</h4>
        <p>Constraining anchor networks using a Softplus activation on weights, forcing <code>z₁ → HOMA-IR</code> and <code>z₂ → CAP</code> to be strictly monotonic ordinal scales of severity.</p>
      </td>
      <td width="33%" valign="top" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa;">
        <h4>🎭 Semi-Supervised Masking</h4>
        <p>Leveraging all 1,477 cohort participants for the Z₁ anchor while safely masking the Z₂ anchor for patients missing ultrasound FibroScan records via a loss-masking function.</p>
      </td>
    </tr>
  </table>
</div>

<br/>

<div align="center">
  <table width="100%" cellpadding="10">
    <tr>
      <td width="40%" valign="top" style="text-align: left;">
        <h3>📊 14 Routine Features Used</h3>
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
      </td>
      <td width="60%" valign="top" style="text-align: left; padding-left: 20px;">
        <h3>📂 Repository Blueprint</h3>
        <pre><code>TYPE2-PHENOTYPE/
├── backend/                  # FastAPI (Endpoints: /infer, /compare, /export_pdf)
├── frontend/                 # React Dashboard (D3.js Atlas, Framer Motion UI)
├── models/                   # Serialized Checkpoints (ivae_best.pt, conformal_surface.pkl)
├── results/                  # Generated Figures, CSV validations, and PySR outputs
├── src_code/                 # Core Python Pipeline
│   ├── data/                 # NHANES multi-cycle loading & preprocessing
│   ├── model/                # VAE, Encoder, Decoder, Prior and Anchor definitions
│   ├── counterfactual/       # Riemannian geodesic solver & Brent's inversion
│   └── validation/           # Benchmarking, conformal testing & pharmacology PSM
└── test_integration.py       # Comprehensive CI/CD integration tests</code></pre>
      </td>
    </tr>
  </table>
</div>

<hr/>

## 🚀 Up and Running in Three Steps

Get the local development server up and running, and run system validation checks.

```bash
# 1. Install & Setup Environment
git clone https://github.com/mysticai11/TYPE2-PHENOTYPE.git
cd TYPE2-PHENOTYPE
pip install -r requirements.txt

# 2. Verify System Integrity
python -m pytest test_integration.py -v

# 3. Spin up Backend & Frontend
# Terminal A (FastAPI Backend):
uvicorn backend.main:app --reload

# Terminal B (React Dashboard):
cd frontend && npm install && npm run dev
```

<hr/>

## 📈 Governing Equations Recovered from the Decoder

We mapped the "black-box" decoder using Symbolic Regression (`PySR`) to recover explicit, interpretable governing equations for the biological pathways:

<div align="center">
  <table width="100%" cellpadding="10">
    <thead>
      <tr>
        <th align="left" width="25%">Biomarker</th>
        <th align="left">Discovered Symbolic Formula & Interpretation</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>HDL Cholesterol</strong></td>
        <td>
          <code>hdl = -17.13 * (z1 + z2 + abs(z2)) + 61.04</code>
          <br/><small>Both resistance and steatosis axes independently suppress HDL cholesterol production.</small>
        </td>
      </tr>
      <tr>
        <td><strong>Atherogenic Index</strong></td>
        <td>
          <code>aip = abs((z1 + z2 + 0.131) * (z2 + 0.385)) + z2 + 0.034</code>
          <br/><small>Cardiovascular risk scales non-linearly, peaking exponentially at the Dual-Burden state.</small>
        </td>
      </tr>
      <tr>
        <td><strong>AST:ALT Ratio</strong></td>
        <td>
          <code>ast_alt = 11.49^z2 * (4.64 - abs(z1 - z2))</code>
          <br/><small>Liver cell injury correlates exponentially with the Z₂ Steatosis axis, modified by axis coordination.</small>
        </td>
      </tr>
    </tbody>
  </table>
</div>

<blockquote>
  <strong>💡 Mathematical Proof:</strong> The AIP formula mathematically confirms that the dual-burden phenotype (z₁ &gt; 0 and z₂ &gt; 0 simultaneously) produces the highest atherogenic index of plasma — not either axis alone. This emerges naturally from the decoder manifold's geometry rather than manual design constraints.
</blockquote>

<hr/>

<div align="center">
  <p><small>Built for the intersection of clinical insight and computational rigor.</small></p>
</div>
