import os
import json
import random
import torch
from PIL import Image
import numpy as np

# For this demonstration/research project, we will simulate the MSR-VTT dataset structure
# because downloading 10GB+ of video data is not feasible for a quick setup.
# In a real scenario, you would download the actual videos and captions.

DATA_DIR = "research/data"
os.makedirs(DATA_DIR, exist_ok=True)

def create_dummy_dataset(num_samples=100):
    print(f"Creating dummy dataset with {num_samples} samples...")
    
    dataset = []
    
    # Create dummy features (simulating pre-extracted CLIP features)
    # Shape: [num_samples, num_frames, feature_dim]
    # Let's assume 20 frames per video, 512-dim CLIP features
    features = torch.randn(num_samples, 20, 512)
    torch.save(features, os.path.join(DATA_DIR, "video_features.pt"))
    
    # Create dummy captions
    captions = []
    actions = ["running", "eating", "playing", "sleeping", "driving"]
    subjects = ["man", "woman", "dog", "cat", "car"]
    
    for i in range(num_samples):
        action = random.choice(actions)
        subject = random.choice(subjects)
        caption = f"a {subject} is {action}"
        captions.append(caption)
        
    with open(os.path.join(DATA_DIR, "captions.json"), "w") as f:
        json.dump(captions, f)
        
    print(f"Dataset created at {DATA_DIR}")
    print("- video_features.pt: [100, 20, 512]")
    print("- captions.json: 100 captions")

if __name__ == "__main__":
    create_dummy_dataset()
