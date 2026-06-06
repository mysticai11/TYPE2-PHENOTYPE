import torch
import torch.nn as nn

class DualAnchorMonotoneNetwork(nn.Module):
    def __init__(self, hidden: int = 32):
        super().__init__()
        # Z1 -> HOMA-IR Monotone Network
        self.w1_z1 = nn.Parameter(torch.randn(hidden, 1))
        self.b1_z1 = nn.Parameter(torch.zeros(hidden))
        self.w2_z1 = nn.Parameter(torch.randn(1, hidden))
        self.b2_z1 = nn.Parameter(torch.zeros(1))
        
        # Z2 -> CAP Monotone Network
        self.w1_z2 = nn.Parameter(torch.randn(hidden, 1))
        self.b1_z2 = nn.Parameter(torch.zeros(hidden))
        self.w2_z2 = nn.Parameter(torch.randn(1, hidden))
        self.b2_z2 = nn.Parameter(torch.zeros(1))

    def _pos_weights(self, w_raw):
        return torch.nn.functional.softplus(w_raw)

    def forward(self, z1: torch.Tensor, z2: torch.Tensor):
        z1 = z1.unsqueeze(-1) if z1.dim() == 1 else z1
        z2 = z2.unsqueeze(-1) if z2.dim() == 1 else z2
        
        h1_hidden = torch.tanh(z1 @ self._pos_weights(self.w1_z1).T + self.b1_z1)
        h1_out = (h1_hidden @ self._pos_weights(self.w2_z1).T + self.b2_z1).squeeze(-1)
        
        h2_hidden = torch.tanh(z2 @ self._pos_weights(self.w1_z2).T + self.b1_z2)
        h2_out = (h2_hidden @ self._pos_weights(self.w2_z2).T + self.b2_z2).squeeze(-1)
        
        # Stack into [batch_size, 2] output for [HOMA-IR, CAP]
        return torch.stack([h1_out, h2_out], dim=-1)

    def verify_monotonicity(self, n_pts: int = 1000) -> bool:
        z_test = torch.linspace(-3, 3, n_pts).requires_grad_(True)
        # Test Z1
        y1 = self.forward(z_test, torch.zeros_like(z_test))[:, 0]
        grad1 = torch.autograd.grad(y1.sum(), z_test)[0]
        
        # Test Z2
        z_test2 = torch.linspace(-3, 3, n_pts).requires_grad_(True)
        y2 = self.forward(torch.zeros_like(z_test2), z_test2)[:, 1]
        grad2 = torch.autograd.grad(y2.sum(), z_test2)[0]
        
        return bool((grad1 > 0).all()) and bool((grad2 > 0).all())
