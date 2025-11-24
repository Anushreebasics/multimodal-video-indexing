import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import json
import os
from sentence_transformers import SentenceTransformer
from model import TwoStreamTemporalEncoder

# Configuration
DATA_DIR = "research/data"
BATCH_SIZE = 32
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

def evaluate():
    print(f"Evaluating on {DEVICE}...")
    
    dataset = TwoStreamDataset(DATA_DIR)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    model = TwoStreamTemporalEncoder().to(DEVICE)
    model.load_state_dict(torch.load("research/models/temporal_encoder.pt", map_location=DEVICE))
    model.eval()
    
    print("Generating embeddings...")
    all_video_embs = []
    all_text_embs = []
    
    with torch.no_grad():
        for spatial, motion_pixels, text_emb in dataloader:
            spatial = spatial.to(DEVICE)
            motion_pixels = motion_pixels.to(DEVICE)
            text_emb = text_emb.to(DEVICE)
            
            video_emb = model(spatial, motion_pixels)
            
            all_video_embs.append(video_emb.cpu())
            all_text_embs.append(text_emb.cpu())
            
    all_video_embs = torch.cat(all_video_embs, dim=0)
    all_text_embs = torch.cat(all_text_embs, dim=0)
    
    # Calculate Similarity Matrix
    # [Num_Videos, Num_Texts]
    similarity_matrix = torch.matmul(all_video_embs, all_text_embs.t())
    
    # Calculate Recall@K
    num_samples = len(similarity_matrix)
    print(f"Calculating metrics on {num_samples} pairs...")
    
    recall_1 = 0
    recall_5 = 0
    recall_10 = 0
    
    for i in range(num_samples):
        # Get indices of top K matches for video i
        scores = similarity_matrix[i]
        _, indices = scores.topk(10)
        
        # Check if correct index (i) is in top K
        if i in indices[:1]:
            recall_1 += 1
        if i in indices[:5]:
            recall_5 += 1
        if i in indices[:10]:
            recall_10 += 1
            
    r1 = (recall_1 / num_samples) * 100
    r5 = (recall_5 / num_samples) * 100
    r10 = (recall_10 / num_samples) * 100
    
    print("\n" + "="*30)
    print("Evaluation Results")
    print("="*30)
    print(f"Top-1 Accuracy (Recall@1):  {r1:.2f}%")
    print(f"Top-5 Accuracy (Recall@5):  {r5:.2f}%")
    print(f"Top-10 Accuracy (Recall@10): {r10:.2f}%")
    print("="*30)

if __name__ == "__main__":
    evaluate()
