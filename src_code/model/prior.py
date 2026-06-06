import torch
import torch.nn as nn

class ConditionalPrior(nn.Module):
    def __init__(self, u_dim: int = 6, k: int = 2, hidden: int = 128):
        super().__init__()
        self.mu_net = nn.Sequential(nn.Linear(u_dim, hidden), nn.GELU(), nn.Linear(hidden, k))
        self.logvar_net = nn.Sequential(nn.Linear(u_dim, hidden), nn.GELU(), nn.Linear(hidden, k))
        nn.init.zeros_(self.mu_net[-1].bias)
        nn.init.constant_(self.logvar_net[-1].bias, 0.0)

    def forward(self, u: torch.Tensor):
        mu_p = self.mu_net(u)
        logvar_p = self.logvar_net(u).clamp(-4, 2)
        return mu_p, logvar_p
