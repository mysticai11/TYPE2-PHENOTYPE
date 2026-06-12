# National Burden Analysis & Prevalence Estimates

Extrapolated using NHANES complex survey design weights (pooled J+P cycles, 2017-March 2020) to the US normal-BMI adult population (N ≈ 80,000,000).

**Analytical cohort:** n=1477 complete normal-BMI fasting participants (J-cycle n=574, P-cycle n=903).

**Survey design:** WTMEC_POOLED weights (WTMEC2YR/2 for J, WTMECPRP/2 for P), PSU=SDMVPSU, Strata=SDMVSTRA (P-cycle strata offset +100 to prevent collision).

**Note on NHA (Non-Hispanic Asian):** RIDRETH3 (which contains code 6=NHA) is only available in J-cycle. P-cycle uses RIDRETH1 which codes Asian Americans under 'Other'. NHA prevalence estimates are therefore drawn from J-cycle only (n=119) and should be interpreted with caution.

---

## Overall Prevalence

| Phenotype          |   Sample N |   Weighted Prevalence (%) | 95% CI           |   National Estimate (M) | National Estimate 95% CI (M)   |
|:-------------------|-----------:|--------------------------:|:-----------------|------------------------:|:-------------------------------|
| MHNW               |        385 |                     23.2  | [12.66%, 33.74%] |                   18.56 | [10.13M, 26.99M]               |
| IR-Dominant        |        264 |                     18.53 | [2.17%, 34.88%]  |                   14.82 | [1.74M, 27.90M]                |
| Steatosis-Dominant |        346 |                     28.39 | [4.71%, 52.06%]  |                   22.71 | [3.77M, 41.65M]                |
| Dual-Burden        |        482 |                     29.89 | [0.00%, 80.45%]  |                   23.91 | [0.00M, 64.36M]                |

## Median Intervention Levers for Dual-Burden Patients

| Biomarker      |   Median Required Delta | Unit   |
|:---------------|------------------------:|:-------|
| FASTINGGLUCOSE |                   -8.66 | mg/dL  |
| FASTINGINSULIN |                   -3.11 | uU/mL  |
| TRIGLYCERIDES  |                 -110.98 | mg/dL  |
| GGT            |                   -8.26 | U/L    |
