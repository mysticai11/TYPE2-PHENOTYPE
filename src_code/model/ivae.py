import torch
import torch.nn as nn
from .encoder import ConditionalEncoder
from .decoder import Decoder
from .prior import ConditionalPrior
from .anchor import DualAnchorMonotoneNetwork

class iVAE_MetabolicStateModel(nn.Module):
    def __init__(self, x_dim=15, u_dim=6, k=2, beta=4.0, lambda_anchor=0.5):
        super().__init__()
        self.encoder = ConditionalEncoder(x_dim, u_dim, k=k)
        self.decoder = Decoder(k, x_dim)
        self.prior = ConditionalPrior(u_dim, k)
        self.anchor = DualAnchorMonotoneNetwork()
        self.beta = beta
        self.lambda_anchor = lambda_anchor

    def forward(self, x, u):
        mu_q, logvar_q = self.encoder(x, u)
        z = self.encoder.reparameterise(mu_q, logvar_q)
        x_hat = self.decoder(z)
        mu_p, logvar_p = self.prior(u)
        h_hat = self.anchor(z[:, 0], z[:, 1])
        return x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat, z

    def loss(self, x, u, h, h_mask, x_hat, mu_q, logvar_q, mu_p, logvar_p, h_hat):
        recon = torch.nn.functional.mse_loss(x_hat, x, reduction='mean')
        var_q = logvar_q.exp()
        var_p = logvar_p.exp()
        kl = 0.5 * (logvar_p - logvar_q - 1 + var_q / var_p + (mu_q - mu_p).pow(2) / var_p)
        kl = kl.mean()
        
        # Semi-supervised masked anchor loss
        # h is [batch_size, 2], h_hat is [batch_size, 2], h_mask is [batch_size, 2]
        sq_err = (h_hat - h).pow(2)
        # Multiply by mask to ignore missing CAP scores, then take mean over valid elements
        anchor = (sq_err * h_mask).sum() / (h_mask.sum() + 1e-8)
        
        total = recon + self.beta * kl + self.lambda_anchor * anchor
        return total, recon, kl, anchor
