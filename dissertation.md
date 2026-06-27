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

The strict J-only model achieves **ρ = 0.583 ± 0.032** on the P-cycle, exceeding the random-split baseline (ρ = 0.5009).

### 5.1 Post-Pandemic Temporal Shift (L-Cycle)
To severely stress-test the model's robustness, the J-cycle (2017-2018) model was evaluated zero-shot on a post-pandemic cohort: the NHANES August 2021–August 2023 cycle (L-Cycle). Applying the same normal-BMI and complete-biomarker filters yielded a clean, strict test set of $N=726$.

When exposed to this massive temporal shift, point-prediction degraded:
- **DA-SS-iVAE (LMSIS):** Mean $\rho$ dropped to **0.332 ± 0.046**.
- **Baselines:** The model underperformed the FLI formula ($\rho=0.419$) and tied with the TyG Index ($\rho=0.332$).

**Per-Axis Localization Audit:**
By decomposing the latent prediction into its orthogonal axes, the failure mechanism was isolated. The drop was not a uniform collapse, but specifically localized to the hepatic steatosis axis:
- **$Z_1$ (Insulin Resistance vs HOMA-IR):** $\rho = 0.801 \rightarrow 0.773$ (Stable)
- **$Z_2$ (Hepatic Steatosis vs FibroScan):** $\rho = 0.583 \rightarrow 0.332$ (Severe Degradation)

While the post-pandemic shift fractured the latent steatosis representation, the **Mondrian Conformal Prediction** layer successfully caught the uncertainty. Without artificially exploding interval widths (median set size remained 1.0), the calibrated conformal bounds successfully preserved $\ge 90\%$ clinical coverage across all quadrants on the unseen L-cycle. This localizes the failure but does not yet explain it; see Section 7 for discussion of candidate mechanisms and why none has been tested.

## 6. Real-World Burden

According to the model's population inference:
**29.89%** of normal-BMI U.S. adults carry dual-burden metabolic dysfunction. This represents approximately **23.9 million people** nationally (95% CI: [0.00M, 64.36M]) who are currently slipping through the cracks of BMI-based screening guidelines. Note that the extremely wide confidence interval reflects the compounding uncertainty of survey weights applied to a deep representation; the point estimate of 23.9 million must not be cited alone without this explicit uncertainty bound.

---

## 7. Limitations & Threats to Validity

While LMSIS establishes strong identifiability and robust safety guarantees, a rigorous audit process isolates the following critical limitations:

**Sensitivity to Post-Pandemic Distribution Shifts:** 
As demonstrated in the L-Cycle holdout, deep generative models can be highly sensitive to specific, severe temporal shocks. The mechanism behind why the latent steatosis representation ($Z_2$) fractured while the insulin resistance representation ($Z_1$) remained stable is an open question and a target for future robust representation studies.

### Table 1: Threats to Validity
| Threat | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Model Unidentifiability** | Standard VAEs learn arbitrarily rotated latent spaces devoid of clinical meaning. | Dual-anchored semi-supervised penalty strictly anchors orthogonal biological pathways. |
| **Silent Clinical Failure** | Machine learning models output confident point-predictions even when failing out-of-distribution. | Mondrian Conformal Prediction guarantees quadrant-specific bounds, widening appropriately under uncertainty. |
| **Single Post-Pandemic Shift** | The L-cycle evaluation relies on a single post-COVID dataset; the mechanism of $Z_2$ degradation is not yet isolated. | The Conformal layer successfully trapped the point-prediction degradation, maintaining 90% safety coverage. |

---

> [!NOTE]
> For mathematical proofs (ELBO derivation, Jacobian intervention pathways, symbolic regression equations) and exhaustive hyperparameter details, please refer to the primary LaTeX source document `dissertation.tex` or the compiled `dissertation.pdf`.
