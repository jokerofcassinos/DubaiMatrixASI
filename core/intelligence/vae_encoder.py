"""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                 SOLÉNN                                       ║
    ║                      VAE ENCODER Ω (LATENT CONTEXT)                          ║
    ║                                                                              ║
    ║  "A realidade é uma superposição de estados latentes. A percepção é          ║
    ║   a compressão ótima desses estados em representações úteis."                ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Any

class VaeEncoder(nn.Module):
    """
    Encoder Variacional Soberano (VAE) para Séries Temporais Financeiras. (Ω-4)
    Framework 3-6-9: Fase 6(Ω-31) - Conceito 1.1 (PhD Level).
    """
    
    def __init__(self, input_dim: int = 15, hidden_dim: int = 64, latent_dim: int = 12):
        super(VaeEncoder, self).__init__()
        
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        
        # [Ω-V6.1.1] 1D-CNN Encoder Cascade
        self.encoder_cnn = nn.Sequential(
            nn.Conv1d(input_dim, hidden_dim, kernel_size=3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.LeakyReLU(0.2),
            nn.Conv1d(hidden_dim, hidden_dim * 2, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(hidden_dim * 2),
            nn.LeakyReLU(0.2),
            nn.Flatten()
        )
        
        # [Ω-V6.1.2] Variational Projection (μ, log_var)
        # Assumindo window_size = 50 -> output CNN = (hidden_dim*2) * (window_size/2)
        flatten_size = (hidden_dim * 2) * 25 
        self.fc_mu = nn.Linear(flatten_size, latent_dim)
        self.fc_logvar = nn.Linear(flatten_size, latent_dim)
        
        # [Ω-V6.1.6] Multi-Head Attention for latent importance
        self.attention = nn.MultiheadAttention(embed_dim=latent_dim, num_heads=3, batch_first=True)
        
        # [Ω-V6.1.3] Symmetric Decoder (Reconstruction)
        self.decoder_fc = nn.Linear(latent_dim, flatten_size)
        self.decoder_cnn = nn.Sequential(
            nn.Unflatten(1, (hidden_dim * 2, 25)),
            nn.ConvTranspose1d(hidden_dim * 2, hidden_dim, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.LeakyReLU(0.2),
            nn.ConvTranspose1d(hidden_dim, input_dim, kernel_size=3, padding=1),
            nn.Sigmoid() # Normalizado para returns comprimidos
        )

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """[Ω-V6.1.2] Mapeamento para espaço latente gaussian."""
        h = self.encoder_cnn(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """[Ω-V6.1.5] Reparameterization Trick (Backprop-safe sampling)."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Reconstrução sensorial para validação ELBO."""
        h = self.decoder_fc(z)
        return self.decoder_cnn(h)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Loop de processamento latente-contingente."""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        
        # [Ω-V6.1.6] Refinamento via atenção multi-head
        z_refined, _ = self.attention(z.unsqueeze(1), z.unsqueeze(1), z.unsqueeze(1))
        z_refined = z_refined.squeeze(1)
        
        return self.decode(z_refined), mu, logvar

    def loss_function(self, recon_x: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """[Ω-V6.1.3] Evidence Lower Bound (ELBO) Loss."""
        BCE = F.mse_loss(recon_x, x, reduction='sum')
        # KL Divergence (D_KL) - Regularização do espaço latente
        KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return BCE + KLD
