import torch
import torch.nn as nn

class TemporalEncoder(nn.Module):
    def __init__(self, input_dim=512, hidden_dim=512, output_dim=384, num_heads=8, num_layers=4):
        super(TemporalEncoder, self).__init__()
        
        # 1. Input Projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # 2. Positional Encoding (Learnable)
        # Assuming max 100 frames
        self.pos_embed = nn.Parameter(torch.randn(1, 100, hidden_dim))
        
        # 3. Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=num_heads, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 4. Aggregation (CLS token style or Mean Pooling)
        # We'll use Mean Pooling for simplicity
        
        # 5. Output Projection (to align with Text Embeddings)
        self.output_proj = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        # x shape: [Batch, Frames, Input_Dim]
        batch_size, frames, _ = x.shape
        
        # Project input
        x = self.input_proj(x)
        
        # Add positional encoding (broadcast across batch)
        x = x + self.pos_embed[:, :frames, :]
        
        # Pass through Transformer
        x = self.transformer(x)
        
        # Mean Pooling (Temporal Aggregation)
        # Shape: [Batch, Hidden_Dim]
        video_embedding = x.mean(dim=1)
        
        # Project to output space
        video_embedding = self.output_proj(video_embedding)
        
        # Normalize (Crucial for Contrastive Learning)
        video_embedding = video_embedding / video_embedding.norm(dim=-1, keepdim=True)
        
        return video_embedding

if __name__ == "__main__":
    # Test the model
    model = TemporalEncoder()
    dummy_input = torch.randn(2, 20, 512) # Batch=2, Frames=20, Dim=512
    output = model(dummy_input)
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
