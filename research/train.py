import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import os
from sentence_transformers import SentenceTransformer
from model import TemporalEncoder

# Configuration
DATA_DIR = "research/data"
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class VideoCaptionDataset(Dataset):
    def __init__(self, data_dir):
        self.features = torch.load(os.path.join(data_dir, "video_features.pt"))
        with open(os.path.join(data_dir, "captions.json"), "r") as f:
            self.captions = json.load(f)
            
        # Pre-compute text embeddings for speed (in real training, do this on fly or cache)
        print("Pre-computing text embeddings...")
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_embeddings = self.text_model.encode(self.captions, convert_to_tensor=True)
        print("Text embeddings ready.")

    def __len__(self):
        return len(self.captions)

    def __getitem__(self, idx):
        return self.features[idx], self.text_embeddings[idx]

def train():
    print(f"Training on {DEVICE}...")
    
    # 1. Data
    dataset = VideoCaptionDataset(DATA_DIR)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # 2. Model
    # Output dim must match text embedding dim (384 for all-MiniLM-L6-v2)
    model = TemporalEncoder(output_dim=384).to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    
    # 3. Loss Function (InfoNCE / CLIP Loss)
    # We want diagonal elements (correct pairs) to have high similarity
    logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))
    
    print("Starting training...")
    for epoch in range(EPOCHS):
        total_loss = 0
        for batch_idx, (video_features, text_embeddings) in enumerate(dataloader):
            video_features = video_features.to(DEVICE)
            text_embeddings = text_embeddings.to(DEVICE)
            
            optimizer.zero_grad()
            
            # Forward pass
            video_embeddings = model(video_features)
            
            # Calculate similarity matrix
            # [Batch, Batch]
            logits = torch.matmul(video_embeddings, text_embeddings.T) * logit_scale.exp()
            
            # Labels: Diagonal elements are correct pairs (0, 1, 2...)
            labels = torch.arange(len(video_features)).to(DEVICE)
            
            # Symmetric Loss
            loss_v = nn.functional.cross_entropy(logits, labels)
            loss_t = nn.functional.cross_entropy(logits.T, labels)
            loss = (loss_v + loss_t) / 2
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {avg_loss:.4f}")
        
    # Save model
    torch.save(model.state_dict(), "research/models/temporal_encoder.pt")
    print("Model saved to research/models/temporal_encoder.pt")

if __name__ == "__main__":
    import numpy as np # Needed for logit_scale init
    train()
