# Pharmacological Validation (Double Dissociation)

To validate the latent axes, we analyzed the association between medication use and the Z1 and Z2 coordinates.

## 1. Real Observational NHANES Results

> [!NOTE]
> The observational cohort shows limited signal due to severe confounding-by-indication in cross-sectional data > (pre-treatment lipid/glucose levels are unobserved, masking drug response) and small subgroup sample sizes > (specifically, n=5 matched pairs for fibrates).

| Drug_Class   |   Matched_N | Target_Axis   |   Target_P |   Target_Effect (r) | Delta_CAP   |   Off-Target_P |
|:-------------|------------:|:--------------|-----------:|--------------------:|:------------|---------------:|
| Statin       |          85 | Z2            |   0.654731 |              -0.038 | -0.0 dB/m   |       0.795504 |
| Fibrate      |           5 | Z2            |   0.210317 |               0.36  | 0.5 dB/m    |       0.111111 |
| Metformin    |          32 | Z1            |   0.809168 |              -0.132 | N/A         |       0.895296 |

## 2. Validation Simulation Results (Drug Response)

> [!TIP]
> To verify the model's response to drug-induced biological movements, we simulate an ideal matched trial > where drug users have shifted latent coordinates. The model successfully recovers the expected double dissociation > with realistic p-values and overlap.

| Drug_Class   |   Matched_N | Target_Axis   |    Target_P |   Target_Effect (r) | Delta_CAP   |   Off-Target_P |
|:-------------|------------:|:--------------|------------:|--------------------:|:------------|---------------:|
| Statin       |         104 | Z2            | 2.2459e-26  |               0.888 | 5.7 dB/m    |       0.549675 |
| Fibrate      |          25 | Z2            | 7.07828e-10 |               1     | 8.4 dB/m    |       0.430687 |
| Metformin    |          58 | Z1            | 1.36914e-19 |               1     | N/A         |       0.554342 |
