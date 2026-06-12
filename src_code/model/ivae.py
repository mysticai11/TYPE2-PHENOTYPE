import torch
import torch.nn as nn
import torch.nn.functional as F
from .encoder import ConditionalEncoder
from .decoder import Decoder
from .prior import ConditionalPrior
from .anchor import DualAnchorMonotoneNetwork

class iVAE_MetabolicStateModel(nn.Module):
    def __init__(self, x_dim=14, u_dim=6, k=2, beta=4.0,
                 lam1=0.8, lam2=1.2, lam_ortho=0.1,
                 # Legacy single-lambda compat: if lambda_anchor provided, split evenly
                 lambda_anchor=None):
        super().__init__()
        self.encoder = ConditionalEncoder(x_dim, u_dim, k=k)
        self.decoder = Decoder(k, x_dim)
        self.prior = ConditionalPrior(u_dim, k)
        self.anchor = DualAnchorMonotoneNetwork()
        self.beta = beta
        # Support legacy lambda_anchor arg for loading old checkpoints
        if lambda_anchor is not None:
            self.lam1 = lambda_anchor
            self.lam2 = lambda_anchor
        else:
            self.lam1 = lam1      # HOMA-IR anchor weight
            self.lam2 = lam2      # CAP anchor weight (higher: imaging signal is rarer)
        self.lam_ortho = lam_ortho

    def forward(self, x, u):
        mu_q, logvar_q = self.encoder(x, u)
        z = self.encoder.reparameterise(mu_q, logvar_q)
        x_hat = self.decoder(z)
        mu_p, logvar_p = self.prior(u)
        h_hat = self.anchor(z[:, 0], z[:, 1])
        return x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z

    def loss(self, x, u, h, h_mask, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z=None):
        # Reconstruction
        recon = F.mse_loss(x_hat, x, reduction='mean')

        # KL divergence from conditional prior
        var_q = logvar_q.exp()
        var_p = logvar_p.exp()
        kl = 0.5 * (logvar_p - logvar_q - 1 + var_q / var_p + (mu_q - mu_p).pow(2) / var_p)
        kl = kl.mean()

        # Anchor loss: separate weights for HOMA-IR (lam1) and CAP (lam2)
        # h is [batch, 2], h_hat is [batch, 2], h_mask is [batch, 2]
        anc1 = F.mse_loss(h_hat[:, 0], h[:, 0], reduction='mean')  # HOMA-IR, always available

        mask2 = h_mask[:, 1].bool()
        if mask2.sum() > 0:
            anc2 = F.mse_loss(h_hat[mask2, 1], h[mask2, 1], reduction='mean')  # CAP, masked
        else:
            anc2 = torch.tensor(0.0)

        # Orthogonality regulariser: penalise ONLY off-diagonal covariance
        # Do NOT penalise diagonal — forcing unit variance interferes with anchor scaling
        ortho = torch.tensor(0.0)
        if z is not None and z.shape[0] > 1:
            z_centered = z - z.mean(dim=0)
            cov = (z_centered.T @ z_centered) / (z.shape[0] - 1)
            off_diag = cov - torch.diag(torch.diag(cov))
            ortho = off_diag.pow(2).sum()

        total = recon + self.beta * kl + self.lam1 * anc1 + self.lam2 * anc2 + self.lam_ortho * ortho
        anchor_total = anc1 + anc2
        return total, recon, kl, anchor_total

