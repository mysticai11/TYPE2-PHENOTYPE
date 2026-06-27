import torch
import numpy as np
from scipy.integrate import solve_ivp

def _ensure_decoder_model(model):
    if hasattr(model, 'decoder'):
        return model
    class Wrapper(torch.nn.Module):
        def __init__(self, dec):
            super().__init__()
            self.decoder = dec
    return Wrapper(model)

def decoder_jacobian(model, z: torch.Tensor) -> torch.Tensor:
    """
    Compute ∂f/∂z at point z.
    Returns J ∈ ℝ^(p × k)
    """
    model = _ensure_decoder_model(model)
    def func(inputs):
        return model.decoder(inputs)
    J = torch.autograd.functional.jacobian(func, z, create_graph=False)
    # J is of shape (batch, p, batch, k). We squeeze to get (p, k)
    return J.squeeze()

def pullback_metric(model, z: torch.Tensor) -> np.ndarray:
    """
    G(z) = J(z)ᵀ J(z) — the Riemannian metric at z.
    G ∈ ℝ^(k × k)
    """
    z_t = torch.tensor(z, dtype=torch.float32).unsqueeze(0)
    J = decoder_jacobian(model, z_t).detach().numpy()   # (p, k)
    return J.T @ J   # (k, k)

def geodesic_ode(t, state, model):
    """
    Geodesic ODE: d²γ/dt² + Γ(γ)(dγ/dt, dγ/dt) = 0
    where Γ are Christoffel symbols of the pullback metric.
    
    State: [z₁, z₂, dz₁/dt, dz₂/dt]
    Numerically stable via finite-difference Christoffel approximation.
    """
    z     = np.array(state[:2])
    dzdt  = np.array(state[2:])
    eps   = 1e-4

    G     = pullback_metric(model, z)
    G_inv = np.linalg.inv(G + 1e-6 * np.eye(2))  # regularised inverse

    # Numerical Christoffel symbols via finite differences
    # Γᵢⱼₖ = 0.5 * Gⁱˡ (∂ⱼGₗₖ + ∂ₖGₗⱼ - ∂ₗGⱼₖ)
    dG = np.zeros((2, 2, 2))
    for m in range(2):
        z_plus  = z.copy(); z_plus[m]  += eps
        z_minus = z.copy(); z_minus[m] -= eps
        dG[m]   = (pullback_metric(model, z_plus)
                   - pullback_metric(model, z_minus)) / (2 * eps)

    Gamma = np.zeros((2, 2, 2))
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    Gamma[i,j,k] += 0.5 * G_inv[i,l] * (
                        dG[j,l,k] + dG[k,l,j] - dG[l,j,k]
                    )

    d2z_dt2 = -np.einsum('ijk,j,k->i', Gamma, dzdt, dzdt)
    return np.concatenate([dzdt, d2z_dt2])

def compute_geodesic(model, z_start: np.ndarray,
                      z_end: np.ndarray,
                      n_steps: int = 50) -> np.ndarray:
    """
    Compute geodesic from z_start to z_end using boundary value problem.
    
    Uses shooting method: try different initial velocities, pick the one
    that lands closest to z_end.
    Returns: path ∈ ℝ^(n_steps × 2)
    """
    model = _ensure_decoder_model(model)
    direction = z_end - z_start

    t_span    = (0.0, 1.0)
    t_eval    = np.linspace(0, 1, n_steps)

    # Shooting: try initial velocities scaled by distance
    best_path, best_error = None, np.inf

    for scale in [1.0, 1.5]:
        v0     = direction * scale
        state0 = np.concatenate([z_start, v0])

        sol = solve_ivp(
            geodesic_ode, t_span, state0,
            args=(model,), t_eval=t_eval,
            method='RK45', rtol=1e-3, atol=1e-4,
        )

        if sol.success:
            endpoint_error = np.linalg.norm(sol.y[:2, -1] - z_end)
            if endpoint_error < best_error:
                best_error = endpoint_error
                best_path  = sol.y[:2].T    # (n_steps, 2)

    return best_path   # (n_steps, 2)

def geodesic_to_clinical_interventions(model, path: np.ndarray,
                                        scaler, feature_names: list) -> list:
    """
    Map geodesic waypoints to clinical biomarker changes.
    
    For each step along the geodesic, decode to biomarker space
    and report the delta from the current position.
    
    Returns list of dicts: [
        {"step": 1, "z": [...], "progress": 0.1, "biomarker_deltas": {"triglycerides": -12.4, ...}}
    ]
    """
    model = _ensure_decoder_model(model)

    if path is None or len(path) == 0:
        return []

    interventions = []
    z_t = torch.tensor(path, dtype=torch.float32)

    with torch.no_grad():
        x_path = model.decoder(z_t).numpy()           # (n_steps, p)
    x_path_unscaled = scaler.inverse_transform(x_path)

    for i in range(1, len(path)):
        delta = x_path_unscaled[i] - x_path_unscaled[0]
        # Only report features with change > 1% of their range
        significant = {
            feature_names[j]: round(float(delta[j]), 2)
            for j in range(len(feature_names))
            if abs(delta[j]) > 0.01 * abs(x_path_unscaled[0, j])
        }
        interventions.append({
            "step":            i,
            "z":               path[i].tolist(),
            "progress":        round(i / len(path), 3),
            "biomarker_deltas": significant,
        })

    return interventions


class RiemannianManifold:
    def __init__(self, decoder_model, input_dim=2, output_dim=3):
        if hasattr(decoder_model, 'decoder'):
            self.model = decoder_model
        else:
            class Wrapper(torch.nn.Module):
                def __init__(self, dec):
                    super().__init__()
                    self.decoder = dec
            self.model = Wrapper(decoder_model)
        self.input_dim = input_dim
        self.output_dim = output_dim

    def metric(self, z):
        return pullback_metric(self.model, z)

    def christoffel_symbols(self, z):
        eps = 1e-4
        G = self.metric(z)
        G_inv = np.linalg.inv(G + 1e-6 * np.eye(self.input_dim))
        dG = np.zeros((self.input_dim, self.input_dim, self.input_dim))
        for m in range(self.input_dim):
            z_plus = z.copy(); z_plus[m] += eps
            z_minus = z.copy(); z_minus[m] -= eps
            dG[m] = (self.metric(z_plus) - self.metric(z_minus)) / (2 * eps)
        
        Gamma = np.zeros((self.input_dim, self.input_dim, self.input_dim))
        for i in range(self.input_dim):
            for j in range(self.input_dim):
                for k in range(self.input_dim):
                    for l in range(self.input_dim):
                        Gamma[i,j,k] += 0.5 * G_inv[i,l] * (
                            dG[j,l,k] + dG[k,l,j] - dG[l,j,k]
                        )
        return Gamma

