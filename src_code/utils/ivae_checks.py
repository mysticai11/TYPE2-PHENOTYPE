import torch
import numpy as np

def check_iVAE_rank_condition(model, u_samples, k=2):
    """
    Checks the iVAE rank condition on the prior parameter matrix.
    The prior (ConditionalPrior) maps u to prior parameters (mu, logvar).
    We require that the parameters vary with u such that the matrix of differences
    or derivatives has full rank (2k).
    Empirically, we can evaluate the prior parameters (mu, logvar) for the given u_samples
    and check the rank of the resulting parameter matrix.
    """
    model.eval()
    with torch.no_grad():
        # u_samples shape: [N, u_dim]
        u_tensor = torch.tensor(u_samples, dtype=torch.float32)
        mu_p, lv_p = model.prior(u_tensor)
        # prior parameters shape: [N, 2*k]
        params = torch.cat([mu_p, lv_p], dim=1).numpy()
    
    # Check linear independence (rank) of the prior parameters across the batch
    rank = np.linalg.matrix_rank(params, tol=1e-4)
    result = {
        "rank": int(rank),
        "required": 2 * k,
        "condition_met": bool(rank >= (2 * k))
    }
    return result
