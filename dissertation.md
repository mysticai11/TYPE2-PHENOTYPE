# Predictive Risk Intelligence for Metabolic Screening in Diabetes
**Latent Metabolic State Inference System (LMSIS)**

*A Semi-Supervised Deep Learning Framework for Early Detection of Metabolic Dysfunction in Normal-BMI Adults*

---

## Abstract
Millions of adults worldwide receive a clean bill of health simply because their Body Mass Index falls within the normal range (18.5 ≤ BMI ≤ 24.9 kg/m²). However, BMI is blind to fat distribution and ectopic tissue accumulation. Underneath a healthy-looking exterior, a patient may carry a silent, severe dual metabolic burden — simultaneous insulin resistance and hepatic steatosis — invisible to traditional screening. 

**LMSIS** deploys a **Dual-Anchored Semi-Supervised Identifiable Variational Autoencoder (DA-SS-iVAE)** to recover a continuous 2D latent metabolic geometry from 14 routine blood biomarkers. 

## 1. System Architecture

The model maps routine features to biological pathways using monotone anchor networks to strictly enforce clinical identifiability.

<div align="center">
  <img src="results/figures/model_pipeline_animated.svg" alt="LMSIS Model Pipeline" width="90%" />
</div>

### Identifiability Constraints
A standard VAE learns a non-identifiable latent space where coordinates can arbitrarily rotate. In LMSIS, the latent space is strictly anchored:
- **$Z_1$ (Insulin Resistance):** Anchored to HOMA-IR using a strictly positive Softplus network.
- **$Z_2$ (Liver Fat):** Anchored to FibroScan CAP using a strictly positive Softplus network (semi-supervised).

## 2. The 2D Latent Metabolic Space

LMSIS projects every patient onto a two-axis plane, dividing the population into four clinically actionable quadrants.

<div align="center">
  <img src="results/figures/metabolic_atlas_animated.svg" alt="LMSIS Metabolic Atlas" width="90%" />
</div>

**Ablation Proof:** Removing the anchor networks collapses the liver-fat Spearman correlation from **0.542 → 0.180** (a 67% degradation). This mathematically guarantees that the clinical anchors, not coincidence, give the coordinates their biological meaning.

## 3. Ancestry-Specific Risk Thresholds

The universal HOMA-IR cutoff of 2.5 misclassifies substantial fractions of every ancestry group as metabolically healthy. LMSIS recovers group-specific implied thresholds, all of which fall significantly below 2.5:

- **Non-Hispanic White (NHW):** 1.47 [1.39–1.58]
- **Non-Hispanic Black (NHB):** 1.37 [1.24–1.48]
- **Hispanic:** 1.28 [1.09–1.53]
- **Non-Hispanic Asian (NHA):** 1.74 [1.59–1.89]

*Validation:* In a real unseen Non-Hispanic Asian cohort (n=355), **24.2%** of patients are misclassified as healthy under the standard 2.5 cutoff, but correctly identified as at-risk by the model's derived threshold.

## 4. Conformal Prediction (Fair Uncertainty)

Standard split Conformal Prediction only guarantees global marginal coverage (90% average). For the highest-risk Dual-Burden subgroup, standard CP drops to **81.6%** coverage, leaving the sickest patients unprotected. 

LMSIS applies **Mondrian Conformal Prediction**, calibrating confidence intervals separately per phenotypic quadrant, which successfully restores **≥90.4%** coverage for all groups, directly addressing the Barber et al. (2023) impossibility theorem.

## 5. Temporal Out-of-Distribution Generalization

LMSIS demonstrates zero data leakage and extreme temporal robustness:
- **Training Cohort:** NHANES 2017–2018 (J-Cycle, n=574)
- **OOD Test Cohort:** NHANES 2019–2020 (P-Cycle, n=903)

The strict J-only model achieves **ρ = 0.5793** on the P-cycle, exceeding the random-split baseline (ρ = 0.5009).

## 6. Real-World Burden

According to the model's population inference:
**29.89%** of normal-BMI U.S. adults carry dual-burden metabolic dysfunction. This represents approximately **23.9 million people** nationally who are currently slipping through the cracks of BMI-based screening guidelines.

---

> [!NOTE]
> For mathematical proofs (ELBO derivation, Jacobian intervention pathways, symbolic regression equations) and exhaustive hyperparameter details, please refer to the primary LaTeX source document `dissertation.tex` or the compiled `dissertation.pdf`.
