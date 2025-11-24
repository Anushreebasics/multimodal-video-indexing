import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models.video as video_models

class AttentionPooling(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.Tanh(),
            nn.Linear(input_dim // 2, 1),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        # x: [Batch, Frames, Dim]
        weights = self.attention(x)
        return torch.sum(x * weights, dim=1)

class TwoStreamTemporalEncoder(nn.Module):
    """
    Two-Stream Network for Fine-Grained Action Recognition.
    
    Stream A: Spatial (CLIP features) - Captures objects/scenes
    Stream B: Motion (Raw Video Clips -> 3D CNN) - Captures movement dynamics
    
    Fusion: Cross-Attention + Concatenation
    """
    def __init__(self, 
                 spatial_dim=512, 
                 motion_dim=512, 
                 hidden_dim=512, 
                 output_dim=384, 
                 num_heads=8, 
                 num_layers=4, 
                 dropout=0.1):
        super(TwoStreamTemporalEncoder, self).__init__()
        
        # --- Stream A: Spatial ---
        self.spatial_proj = nn.Sequential(
            nn.Linear(spatial_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        self.spatial_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=num_heads, batch_first=True, norm_first=True),
            num_layers=num_layers
        )
        
        # --- Stream B: Motion (3D CNN Backbone) ---
        # Initialize from scratch (pretrained=False)
        self.motion_backbone = video_models.r3d_18(pretrained=False)
        self.motion_backbone.fc = nn.Identity() # Remove classification head
        # r3d_18 output is 512-dim
        
        self.motion_proj = nn.Sequential(
            nn.Linear(512, hidden_dim), # r3d output is 512
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        # We don't need a transformer for motion stream if we only have 1 clip per video
        # But to match dimensions for cross-attention, we treat it as a sequence of length 1 (or repeat)
        
        # --- Fusion ---
        # Cross-Attention: Spatial attends to Motion
        self.cross_attn = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=num_heads, batch_first=True)
        self.fusion_norm = nn.LayerNorm(hidden_dim)
        
        # Pooling
        self.pool = AttentionPooling(hidden_dim * 2) # We will concat spatial + fused
        
        # Output Head
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
        
        self.pos_embed = nn.Parameter(torch.randn(1, 100, hidden_dim) * 0.02)
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)

    def forward(self, x_spatial, x_motion_pixels):
        # x_spatial: [B, T, 512] (CLIP features)
        # x_motion_pixels: [B, C, D, H, W] (Raw video clips)
        
        B, T, _ = x_spatial.shape
        
        # 1. Process Spatial Stream
        s = self.spatial_proj(x_spatial) + self.pos_embed[:, :T, :]
        s_enc = self.spatial_transformer(s)
        
        # 2. Process Motion Stream (3D CNN)
        # Pass raw pixels through 3D CNN
        m_feat = self.motion_backbone(x_motion_pixels) # [B, 512]
        m = self.motion_proj(m_feat) # [B, Hidden]
        
        # Reshape for Attention: [B, 1, Hidden]
        m_seq = m.unsqueeze(1)
        
        # 3. Fusion (Spatial attends to Motion)
        # Query=Spatial [B, T, H], Key=Motion [B, 1, H], Value=Motion [B, 1, H]
        # Each spatial frame attends to the global motion context
        fused, _ = self.cross_attn(s_enc, m_seq, m_seq)
        fused = self.fusion_norm(s_enc + fused) # Residual connection
        
        # 4. Concatenate Original Spatial + Fused Motion Context
        combined = torch.cat([s_enc, fused], dim=-1) # [B, T, Hidden*2]
        
        # 5. Pooling
        video_embedding = self.pool(combined)
        
        # 6. Output Projection
        video_embedding = self.output_proj(video_embedding)
        video_embedding = F.normalize(video_embedding, p=2, dim=-1)
        
        return video_embedding

if __name__ == "__main__":
    model = TwoStreamTemporalEncoder()
    print("TwoStreamTemporalEncoder initialized.")
    dummy_spatial = torch.randn(2, 10, 512)
    dummy_motion = torch.randn(2, 3, 16, 112, 112) # [B, C, T, H, W]
    output = model(dummy_spatial, dummy_motion)
    print(f"Output shape: {output.shape}")
