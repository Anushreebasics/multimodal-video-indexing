import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import os
from sentence_transformers import SentenceTransformer
from model import TwoStreamTemporalEncoder

# Configuration
DATA_DIR = "research/data"
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class TwoStreamDataset(Dataset):
    def __init__(self, data_dir):
        self.spatial_features = torch.load(os.path.join(data_dir, "video_features_clip.pt"))
        self.motion_clips = torch.load(os.path.join(data_dir, "video_clips.pt")) # Raw pixels
        with open(os.path.join(data_dir, "captions.json"), "r") as f:
            self.captions = json.load(f)
            
        print("Pre-computing text embeddings...")
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_embeddings = self.text_model.encode(self.captions, convert_to_tensor=True)
        print("Text embeddings ready.")

    def __len__(self):
        return len(self.captions)

    def __getitem__(self, idx):
        return (
            self.spatial_features[idx], 
            self.motion_clips[idx], 
            self.text_embeddings[idx]
        )

def train():
    print(f"Training on {DEVICE}...")
    
    dataset = TwoStreamDataset(DATA_DIR)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    model = TwoStreamTemporalEncoder().to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()
    
    print("Starting training...")
    for epoch in range(EPOCHS):
        total_loss = 0
        for batch_idx, (spatial, motion_pixels, text_emb) in enumerate(dataloader):
            spatial = spatial.to(DEVICE)
            motion_pixels = motion_pixels.to(DEVICE)
            text_emb = text_emb.to(DEVICE)
            
            # Forward pass
            video_emb = model(spatial, motion_pixels)
            
            # Contrastive Loss (Symmetric)
            # 1. Video -> Text
            logits_per_video = torch.matmul(video_emb, text_emb.t()) * 10.0
            # 2. Text -> Video
            logits_per_text = logits_per_video.t()
            
            labels = torch.arange(len(video_emb)).to(DEVICE)
            
            loss_v = criterion(logits_per_video, labels)
            loss_t = criterion(logits_per_text, labels)
            loss = (loss_v + loss_t) / 2
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {total_loss/len(dataloader):.4f}")
        
    # Save model
    os.makedirs("research/models", exist_ok=True)
    torch.save(model.state_dict(), "research/models/temporal_encoder.pt")
    print("Model saved to research/models/temporal_encoder.pt")

if __name__ == "__main__":
    train()

