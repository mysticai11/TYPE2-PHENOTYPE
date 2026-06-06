import torch
import torch.nn as nn

class ConditionalEncoder(nn.Module):
    def __init__(self, x_dim: int = 15, u_dim: int = 6, hidden: int = 256, k: int = 2, dropout: float = 0.1):
        super().__init__()
        in_dim = x_dim + u_dim
        self.input_proj = nn.Sequential(nn.Linear(in_dim, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.res_block = nn.Sequential(nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.LayerNorm(hidden))
        self.act = nn.GELU()
        self.mu_head = nn.Linear(hidden, k)
        self.logvar_head = nn.Linear(hidden, k)
        nn.init.xavier_uniform_(self.mu_head.weight, gain=0.1)
        nn.init.zeros_(self.mu_head.bias)
        nn.init.constant_(self.logvar_head.bias, -1.0)

    def forward(self, x: torch.Tensor, u: torch.Tensor):
        xu = torch.cat([x, u], dim=-1)
        h = self.input_proj(xu)
        h = self.act(h + self.res_block(h))
        mu = self.mu_head(h)
        logvar = self.logvar_head(h).clamp(-6, 2)
        return mu, logvar

    def reparameterise(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + std * eps

    @torch.no_grad()
    def encode(self, x: torch.Tensor, u: torch.Tensor):
        mu, _ = self.forward(x, u)
        return mu
