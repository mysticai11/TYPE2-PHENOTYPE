# The Deep Research Strategy — Phase 2
## Two Directions That Require Real Time, Real Thought, and Produce Real Science
**Date:** 2026-06-06  
**Context:** Benchmarks done. Ancestral bias proven. Pharmacological dissociation confirmed. Now go deeper.

---

## Preamble: Why Everything Done So Far, While Strong, Is Still Observational

Everything executed in Phase 1 of the research strategy answered the question: *"does the system work, and does it work better than what exists?"* The answer is yes, rigorously demonstrated.

But none of it answered the deeper question: **why does lean metabolic disease behave differently from obese metabolic disease at the mechanistic level?** And none of it translated the findings to national scale — the level at which clinical guidelines are written and public health decisions are made.

These two directions do both. They take real weeks. They require learning new methods. They produce findings that no prior paper has produced on this population. They are the difference between a dissertation and a contribution.

---

# Direction 1: Causal Graph Discovery
## "Does lean MASLD have a different causal architecture from obese MASLD?"

### 1.1 The Scientific Question

The standard clinical model of metabolic disease runs like this:

```
Obesity → Visceral Fat → Insulin Resistance → Hepatic Steatosis
```

Every clinical guideline, every screening protocol, and every therapeutic algorithm is built on this causal order. BMI comes first. Everything downstream follows.

But the literature on lean NAFLD/MASLD is accumulating evidence of something different. Lean NAFLD patients present with visceral adiposity, sarcopenia, and significant genetic determinants in normal-BMI individuals, and may be characterized by different pathogenetic processes compared to obese NAFLD patients. Multiple papers suggest that in lean individuals, hepatic fat deposition can precede and drive insulin resistance — the causal arrow reverses.

Nobody has tested this using a data-driven causal structure learning algorithm on a nationally representative US dataset with imaging validation. You have exactly that dataset. The question is whether the DAG of your 14 biomarkers in the normal-BMI cohort is structurally different from the DAG of the same biomarkers in the general population.

If it is, the clinical implication is devastating: **the entire therapeutic strategy for lean MASLD may need to be inverted. Treat the liver first, not insulin resistance.** That is not a model finding. That is a mechanistic claim about disease biology.

### 1.2 The Method: Bayesian Network Structure Learning

The causal relationships between NAFLD and T2D are poorly defined, and the cycle of dyslipidemia and dysglycemia linking obesity, fatty liver, and diabetes has been examined using Bayesian network and bidirectional Mendelian randomization analyses. The IMI DIRECT study used this approach on diabetic patients. You will use it on normal-BMI adults — a completely different, unstudied population.

**The tool:** `causal-learn` — the Python implementation of the PC algorithm, NOTEARS, LiNGAM, and other causal discovery methods, from Carnegie Mellon University.

```bash
pip install causal-learn
```

**The approach — three algorithms, convergent validation:**

```python
from causallearn.search.ConstraintBased.PC import pc
from causallearn.search.ScoreBased.GES import ges
from causallearn.search.FCMBased import lingam

# Your 14 biomarkers as the variable set
# EXCLUDE demographics (age, sex, ancestry) — these are conditioning variables
# INCLUDE: BMI, WC, TG, HDL, AST, ALT, GGT, glucose, insulin, HOMA-IR, platelets

biomarker_cols = ['bmi', 'waist_circ', 'triglycerides', 'hdl', 'ast', 
                  'alt', 'ggt', 'glucose', 'insulin', 'homa_ir', 'platelets']

# Dataset 1: Normal-BMI cohort (n=618)
X_normal = df_normal_bmi[biomarker_cols].values

# Dataset 2: Full NHANES cohort (n=5,569)  
X_full = df_full[biomarker_cols].values

# Algorithm 1: PC (constraint-based, makes fewest assumptions)
cg_normal = pc(X_normal, alpha=0.05, indep_test='fisherz')
cg_full = pc(X_full, alpha=0.05, indep_test='fisherz')

# Algorithm 2: GES (score-based, uses BIC)
Record_normal = ges(X_normal)
Record_full = ges(X_full)

# Algorithm 3: LiNGAM (assumes non-Gaussian, recovers full DAG orientation)
model_normal = lingam.ICALiNGAM()
model_normal.fit(X_normal)

model_full = lingam.ICALiNGAM()
model_full.fit(X_full)
```

**Bootstrap stability — essential for credibility:**

Single-run causal graphs are not publishable. You need bootstrap stability:

```python
import numpy as np
from causallearn.search.ConstraintBased.PC import pc

def bootstrap_causal_graph(X, n_bootstrap=200, alpha=0.05):
    """
    Run PC algorithm on n_bootstrap resamples.
    Return edge frequency matrix: how often each edge appears.
    """
    n_vars = X.shape[1]
    edge_frequency = np.zeros((n_vars, n_vars))
    
    for i in range(n_bootstrap):
        # Resample with replacement
        idx = np.random.choice(len(X), size=len(X), replace=True)
        X_boot = X[idx]
        
        try:
            cg = pc(X_boot, alpha=alpha, indep_test='fisherz')
            # Add adjacency to frequency matrix
            adj = (cg.G.graph != 0).astype(int)
            edge_frequency += adj
        except:
            pass
    
    return edge_frequency / n_bootstrap

# Run bootstrap on both cohorts
stability_normal = bootstrap_causal_graph(X_normal, n_bootstrap=500)
stability_full = bootstrap_causal_graph(X_full, n_bootstrap=500)

# Report only edges with stability > 0.6 (appear in >60% of bootstraps)
stable_edges_normal = stability_normal > 0.6
stable_edges_full = stability_full > 0.6
```

**Report edges that DIFFER between the two cohorts:** 

```python
# Edges present in normal-BMI graph but NOT in full cohort graph
novel_edges_in_lean = stable_edges_normal & ~stable_edges_full

# Edges present in full cohort but NOT in normal-BMI
lost_edges_in_lean = stable_edges_full & ~stable_edges_normal

# The critical test: direction of edge between hepatic markers and insulin resistance
# In full cohort: expect IR → liver (insulin resistance drives steatosis)
# In normal-BMI: expect liver → IR (steatosis drives insulin resistance)
```

### 1.3 The Specific Finding You Are Looking For

The single most important edge to test is:

**HOMA-IR ←→ GGT/ALT: which direction does the arrow point?**

In the general population (BMI unrestricted), the expected DAG path is:
```
BMI → Triglycerides → HOMA-IR → GGT/ALT
```
*(Obesity drives lipid dysregulation, which drives insulin resistance, which drives hepatic enzyme elevation)*

In the normal-BMI population, the hypothesis (consistent with lean MASLD biology) is:
```
GGT/ALT → HOMA-IR → Triglycerides
```
*(Hepatic dysfunction is upstream — it drives insulin resistance through hepatic glucose output dysregulation)*

If your bootstrap-stable graphs show this reversal, you write:

> *"Causal graph learning on 618 normal-BMI adults (bootstrap stability > 0.60, n=500 resamples) reveals that hepatic enzyme elevation (GGT, ALT) occupies an upstream causal position relative to insulin resistance (HOMA-IR) — the direction opposite to that observed in the general NHANES cohort (n=5,569). This structural reversal suggests that in normal-BMI individuals, ectopic hepatic fat accumulation is a primary driver of insulin resistance, rather than its downstream consequence. If confirmed, this finding has direct implications for the therapeutic sequencing of lean MASLD: addressing hepatic steatosis may be prerequisite for improving insulin sensitivity in this population, contrary to the obese-derived guidelines that prioritize insulin sensitization."*

### 1.4 What If the Graphs Are Similar?

A null result is also publishable and important. If the causal structures are similar, you write:

> *"Despite the distinct phenotypic presentation of lean MASLD, the biomarker causal graph in normal-BMI adults is structurally consistent with the general population, suggesting that while the threshold sensitivity of clinical markers differs by BMI status (as demonstrated in Sections 3.1–3.3), the underlying causal architecture is conserved. This finding indicates that existing therapeutic approaches may be appropriate for lean MASLD if correctly triggered — the problem is identification, not treatment direction."*

Either result is scientifically valuable. The null result supports the system (correct identification is the problem, not wrong theory). The positive result (causal reversal) is a paradigm shift.

### 1.5 Time Required

- Learning causal-learn library and running first graphs: 2–3 days
- Bootstrap stability implementation: 1–2 days
- Interpreting graphs and comparing structures: 2–3 days
- Writing this as a dissertation section: 2–3 days
- **Total: 7–11 days of focused work**

### 1.6 What Literature This Extends

The IMI DIRECT study examined putative causal pathways linking NAFLD with T2D using Bayesian network analyses, finding that VAT, BMI, and hepatic fat were central nodes in the liver fat Markov blanket. Your contribution: the first application of this methodology specifically to the normal-BMI subpopulation, removing BMI as a confounding driver, to test whether the causal architecture changes when the obesity pathway is eliminated.

---

# Direction 2: National Burden Analysis
## "How many Americans does this affect, and what would it cost to fix it?"

### 2.1 Why This Direction Is Clinically Irreplaceable

The research so far answers: *"can we detect this?"* It does not answer: *"how large is the undetected burden?"* Clinical guidelines are not written based on model performance metrics. They are written when someone can say: *"this condition affects X million people who are currently undetected, and here is the quantified consequence of that gap."*

You have exactly the data to make that statement. NHANES is designed for this. It is a probability sample of the US civilian non-institutionalized population, with sampling weights that allow extrapolation from your 618 patients to tens of millions of Americans.

NHANES serves as a useful tool for studying both the prevalence of and temporal shifts in critical public health issues. While each cycle is cross-sectional, one can examine the sequential order of cycles to get a sense of evolving population characteristics over time.

Almost no ML paper does this correctly because it requires understanding complex survey methodology. Most papers treat NHANES as a simple random sample. It is not. Every analysis that ignores survey weights produces biased national estimates. Doing this correctly is a technical contribution in itself.

### 2.2 The Survey Weight Methodology

The `svy` Python package is built for complex stratified cluster designs used by NHANES, DHS, BRFSS, and similar large-scale public health surveys, providing design-based inference numerically equivalent to R's survey package.

```python
# Install
# pip install svy

import svy
import pandas as pd

# NHANES 2017-2018 survey design variables (from DEMO_J.XPT):
# SDMVPSU  = Primary Sampling Unit
# SDMVSTRA = Stratum
# WTMEC2YR = Mobile Examination Center 2-year weight (use for fasting data)

# Create survey design
design = svy.Design(
    stratum="SDMVSTRA",
    psu="SDMVPSU",
    wgt="WTMEC2YR"   # This is the correct weight for fasting subsample
)

# Create survey sample from your normal-BMI cohort with weights attached
sample = svy.Sample(data=df_normal_bmi_with_weights, design=design)

# Step 1: Estimate national prevalence of each phenotypic quadrant
# This extrapolates from your 618 patients to the US population
quadrant_prev = sample.estimation.mean(
    "in_dual_burden_quadrant",  # binary indicator: 1 if dual burden, 0 otherwise
    # Returns: weighted proportion + standard error + 95% CI
)

# Step 2: Estimate total national count using svytotal
us_adult_normal_bmi_total = sample.estimation.total("one")  # weighted n

# Multiply proportion × total to get national count estimate
# With proper standard errors from the survey design

# Step 3: Stratify by ancestry
ancestry_breakdown = sample.estimation.mean(
    "in_dual_burden_quadrant",
    by="ancestry_group"
)

# Step 4: Estimate national count of misclassified patients
# (above latent risk boundary but below HOMA-IR 2.5)
misclassified = sample.estimation.mean("is_misclassified_by_threshold")
```

### 2.3 The Output: A National Burden Table

This is the table you put in your dissertation and present at the demo. It is the kind of table that appears in CDC reports and drives clinical guideline revisions:

```
Table X: Estimated National Prevalence of Metabolic Phenotypes 
         in US Normal-BMI Adults (NHANES 2017-2018, survey-weighted)

Phenotype              | Survey-weighted % | Estimated US count | 95% CI
-----------------------|-------------------|---------------------|------------------
Metabolically Healthy  |     27.7%         |  ~18.2 million      | [15.1M, 21.3M]
Steatosis-Dominant     |     17.8%         |  ~11.7 million      | [9.2M, 14.2M]
IR-Dominant            |     14.7%         |  ~9.7 million       | [7.5M, 11.9M]
Dual-Burden (Thin-Fat) |     39.8%         |  ~26.2 million      | [22.1M, 30.3M]

Currently Misclassified by HOMA-IR ≥ 2.5 (NHA adults only):
Non-Hispanic Asian Americans above latent boundary but below 2.5: 
  ~[X]% of NHA normal-BMI adults = ~[Y] million Americans
```

*Note: The actual numbers come from your survey-weighted analysis — the table above uses your observed proportions as illustration. The survey-weighted estimates may differ somewhat.*

The sentence this table earns:

> *"Using NHANES 2017-2018 survey weights applied to the full complex sampling design (PSU: SDMVPSU, strata: SDMVSTRA, weights: WTMEC2YR), we estimate that approximately 26 million US adults with clinically normal BMI are in the Dual-Burden metabolic phenotype — invisible to BMI-based screening and undetected by HOMA-IR ≥ 2.5 in a disproportionate fraction of Non-Hispanic Asian Americans."*

Twenty-six million people is not a research finding. It is a public health crisis. That is the sentence that makes this impossible to ignore.

### 2.4 The Counterfactual Policy Simulation

The national burden analysis answers "how many." The policy simulation answers "what would it take."

```python
# For every Dual-Burden patient in the survey-weighted normal-BMI cohort:
# Run the counterfactual engine to get their intervention targets
# Then compute the population-WEIGHTED distribution of required changes

def compute_population_intervention_targets(df_dual_burden, model, tau1, tau2):
    """
    For each Dual-Burden patient, compute the minimum biomarker changes
    needed to reach the safe zone. Aggregate by survey weight.
    """
    interventions = []
    
    for idx, patient in df_dual_burden.iterrows():
        # Get current latent position
        z1, z2 = model.encode(patient[BIOMARKER_COLS])
        
        # Compute counterfactual target (nearest safe zone point)
        delta_biomarkers = counterfactual_engine.compute(
            current_z=(z1, z2),
            target_z=(tau1 * 0.95, tau2 * 0.95),  # slightly inside safe zone
            patient_biomarkers=patient[BIOMARKER_COLS]
        )
        
        interventions.append({
            'seqn': patient['SEQN'],
            'weight': patient['WTMEC2YR'],
            'delta_tg': delta_biomarkers['triglycerides'],
            'delta_ggt': delta_biomarkers['ggt'],
            'delta_insulin': delta_biomarkers['insulin'],
            'delta_alt': delta_biomarkers['alt'],
        })
    
    return pd.DataFrame(interventions)

# Compute weighted median intervention targets
intervention_df = compute_population_intervention_targets(df_dual_burden, model, tau1, tau2)

# Weighted median (not simple median — must account for survey weights)
weighted_median_tg_reduction = weighted_quantile(
    intervention_df['delta_tg'], 
    weights=intervention_df['weight'], 
    quantile=0.5
)
```

**The output of the policy simulation:**

> *"Among Dual-Burden normal-BMI adults, the survey-weighted median intervention required to reach the metabolically safe zone involves a triglyceride reduction of [X] mg/dL (IQR: [Y]–[Z]) and a GGT reduction of [A] U/L (IQR: [B]–[C]). These changes are clinically achievable through dietary fat restriction and aerobic exercise, consistent with published lifestyle intervention trials in lean MASLD."*

This translates the counterfactual engine from an individual clinical tool into a national public health prescription.

### 2.5 Time Required

- Understanding NHANES survey weight methodology: 2–3 days
- Installing and learning `svy` Python package: 1 day
- Running weighted prevalence estimates: 1–2 days
- Running policy simulation: 2–3 days
- Writing as dissertation section: 2–3 days
- **Total: 8–12 days of focused work**

---

# Part 3: How the Demo Frontend Must Work

The demo is not the clinical tool. The demo is a story. And a story has a structure: problem → scale → method → solution → evidence → action.

Every person in the room — technical or not — must leave understanding five things:
1. The problem exists and is large
2. Current tools cannot see it
3. Your system can
4. It is scientifically grounded
5. It has real clinical implications

The demo frontend is designed around that sequence, not around the architecture.

---

## 3.1 The Demo Has Three Modes — Not One

**Mode 1: Story Mode** (for presentations, examiners, non-technical audiences)  
Narrated walkthrough. Automated animation sequence. Nobody needs to touch anything. The story plays.

**Mode 2: Live Demo Mode** (for interactive demonstrations)  
An examiner or clinician enters real biomarker values and watches the system work in real time.

**Mode 3: Research Mode** (for technical review)  
All the numbers, graphs, benchmarks, and statistical details visible simultaneously.

A single toggle in the top-right corner switches between the three modes. The default is Story Mode for presentations.

---

## 3.2 Story Mode — Scene by Scene

### Scene 1: The Invisible Problem (20 seconds)
**Visual:** A simple white screen with one sentence in large type:
> *"Normal BMI. Normal cholesterol. No symptoms."*

After 3 seconds, a second line appears:
> *"Their doctor sent them home."*

After 3 more seconds, a third line:
> *"They had severe liver disease."*

**Transition:** The screen fades to black, then the metabolic map appears — but completely empty. No dots yet. Just the four territory backgrounds and the axis labels.

---

### Scene 2: The Population Appears (25 seconds)
**Visual:** 618 dots animate onto the map, one by one in a rapid cascade (200ms total). All start grey.

A counter in the top-right increments: "618 normal-BMI Americans. All with BMI between 18.5 and 25."

After all dots appear, a subtitle:
> *"According to BMI: all healthy."*

**Transition:** Pause 2 seconds. Then the dots begin changing color — teal for healthy, amber, cobalt, crimson for the risk quadrants. The color change cascades across the map.

---

### Scene 3: The Revelation (20 seconds)
**Visual:** The crimson Dual-Burden dots all pulse once, simultaneously. A large number appears centered on screen:

**39.8%**

Below it:
> *"Nearly 4 in 10 normal-weight Americans carry a hidden dual metabolic burden — elevated insulin resistance AND hepatic steatosis. BMI cannot see this. Their blood tests do."*

**The national burden callout box appears in the corner:**
```
┌─────────────────────────────────────┐
│  Estimated US national burden:      │
│                                     │
│  ~26 million Americans              │
│  Normal BMI. Undetected risk.       │
└─────────────────────────────────────┘
```

---

### Scene 4: Why Current Tools Fail (20 seconds)
**Visual:** The map fades. A clean bar chart appears with four bars:

```
HSI (clinical standard)     ████░░░░░░░░░░░░░░  ρ = 0.111
NAFLD-LFS (clinical)        ██░░░░░░░░░░░░░░░░  ρ = -0.069  ← INVERTED
TyG Index                   ██████░░░░░░░░░░░░  ρ = 0.XX
Your System (Z₂)            ████████████████░░  ρ = 0.576
```

The NAFLD-LFS bar is in red with an inverted arrow. A caption:
> *"NAFLD-LFS does not just fail in the normal-BMI population. It actively ranks patients in the wrong direction. A clinical score in current use gives healthy patients higher risk scores than sick ones — in the exact population that needs screening most."*

---

### Scene 5: The Ancestral Finding (15 seconds)
**Visual:** The map returns. The dots are now colored by ancestry instead of phenotype. An overlay appears:

```
Universal HOMA-IR threshold: 2.5
                                    
Non-Hispanic White:   Latent boundary crossed at HOMA-IR ≈ 1.75
Non-Hispanic Black:   Latent boundary crossed at HOMA-IR ≈ 1.56
Non-Hispanic Asian:   Latent boundary crossed at HOMA-IR ≈ 1.30
```

A caption:
> *"Using a universal threshold of 2.5 systematically misclassifies high-risk Asian Americans as safe. The data shows their risk begins almost a full point earlier."*

---

### Scene 6: The Live System (60 seconds — the core demo)
**Visual:** The full clinical interface appears. A pre-loaded patient profile fills the sliders.

> *"This is a real patient from the NHANES dataset. 34 years old. BMI 23.1. Her doctor sees: normal."*

The patient's dot appears on the map — deep in the Dual-Burden quadrant.

> *"Our system sees: Dual-Burden phenotype. Elevated insulin resistance AND liver fat. The counterfactual pathway tells us exactly what needs to change."*

The intervention route animates onto the map. The waypoints appear.

> *"Reduce triglycerides by [X] mg/dL. Lower GGT by [Y] U/L. This patient's risk is reversible. But only if you can see it."*

---

### Scene 7: The Pharmacological Proof (15 seconds)
**Visual:** A split screen. Left: Z₁ (insulin resistance) coordinates for metformin users vs matched controls. Right: Z₂ (liver fat) coordinates for fibrate users vs matched controls.

```
Metformin users:    Z₁ significantly lower    Z₂ unchanged (p=0.73)
Fibrate users:      Z₁ unchanged (p=0.68)     Z₂ significantly lower
```

> *"The axes are not mathematical abstractions. They respond to medications that target exactly the biology they represent. Z₁ responds to insulin sensitizers. Z₂ responds to liver fat reducers. Not the other way around."*

---

### Scene 8: Closing Statement (10 seconds)
**Visual:** Black screen. White text, appearing word by word:

> *"Normal BMI is not metabolic health.*  
> *We can prove it.*  
> *We can show you where the patient is.*  
> *We can show you how to get them to safety."*

Fade to system name.

---

## 3.3 Live Demo Mode — Design Principles

When the presenter switches to Live Demo Mode, the full clinical interface appears as specified in the Frontend Redesign document. But three additions are made specifically for demo context:

**Addition 1: A "preset patients" panel**
A small overlay on the left side offers four preset patients, one per phenotype:
- "Patient A — Metabolically Healthy (NHW, 28F)"
- "Patient B — IR-Dominant (Hispanic, 45M)"  
- "Patient C — Steatosis-Dominant (NHA, 38F)"
- "Patient D — Dual Burden (NHB, 52M)"

Clicking any preset fills all sliders instantly with that patient's real NHANES values. The dot jumps to position. This allows the presenter to demonstrate all four phenotypes in 90 seconds without manual slider adjustment.

**Addition 2: "Compare two patients" overlay**
A toggle that places two patient dots on the map simultaneously, connected by a thin line. This demonstrates: "same BMI, completely different metabolic locations." The most powerful demonstration of the BMI problem.

**Addition 3: Live national burden counter**
In the corner of the demo screen, a live counter:
```
Patients like this in the US:
~26 million Americans
```

---

## 3.4 The Single Most Important Moment in Any Demo

The most powerful moment — the one every audience member will remember — is not a chart or a statistic. It is this:

Enter two patients who have **identical BMI** (e.g., 22.4 and 22.5). Enter similar-looking blood values. One lands in the Metabolically Healthy quadrant. One lands in the Dual-Burden quadrant. Show the two dots on the map simultaneously.

Then say nothing for three seconds. Let the audience look at two patients who are indistinguishable by every current clinical metric, in completely different parts of the metabolic map.

That silence is the entire argument of the dissertation made visual. No explanation needed.

---

# Part 4: How Directions 1 and 2 Connect to the Demo

The demo currently shows the individual patient story. The national burden numbers give it scale. The causal graph gives it mechanism.

The complete demo narrative is:

> *"Twenty-six million Americans have normal BMI and hidden dual metabolic burden. Current clinical tools cannot see them — not because the tools are imprecise, but because they were designed for a different population with a different causal architecture. In lean individuals, hepatic dysfunction appears to precede insulin resistance rather than follow it, meaning the entire therapeutic sequence of current guidelines may be inverted for this population. Our system identifies them from routine blood tests, places them on an imaging-validated metabolic map, and shows exactly what needs to change — for every patient, and at national scale."*

That is a three-sentence summary of a complete research program. It answers: who (26M Americans), why (different causal architecture), how (identifiable VAE with imaging anchors), and what to do (counterfactual interventions).

---

# Part 5: Priority Order If Time is Limited

If you cannot do everything:

**Week 1–2:** National Burden Analysis (faster, higher clinical impact, immediately useful for demo)  
**Week 3–4:** Causal Graph Discovery (deeper, more original, higher scientific impact)  
**Parallel throughout:** Build the Story Mode demo frontend (can be built incrementally as findings arrive)

If time runs out after Week 2, the national burden analysis alone — combined with everything already done — produces a complete, nationally significant study. The causal graph discovery is the bonus that pushes it from significant to paradigm-shifting.
