import torch
import torch.nn as nn

class Decoder(nn.Module):
    def __init__(self, k: int = 2, x_dim: int = 15, hidden: int = 256):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(k, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Linear(hidden, x_dim))

    def forward(self, z: torch.Tensor):
        return self.net(z)
