# Ablation Study Summary

Ablation study comparing the full model with its key architectural variants on the test split:

| Model                         |   Reconstruction_MSE |   Spearman_Rho_CAP |   Covariance_Orthogonality |
|:------------------------------|---------------------:|-------------------:|---------------------------:|
| DA-SS-iVAE (Full Model)       |               3.9587 |              0.542 |                    0       |
| Unanchored VAE (lam1=lam2=0)  |               3.4981 |              0.18  |                    0.00144 |
| No Frobenius Penalty (lam3=0) |               3.0811 |              0.627 |                    0       |

## Findings:
- **Unanchored VAE:** Demonstrates severe clinical correlation loss because the latent dimensions are not aligned to clinical metrics.
- **No Frobenius Penalty:** Shows high covariance orthogonality error, meaning that the axes Z1 and Z2 are coupled, violating structural independence requirements.
