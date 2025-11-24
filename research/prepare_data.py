import os
import json
import torch
import cv2
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torchvision.models.video as video_models
import torchvision.transforms as transforms
import numpy as np
from tqdm import tqdm

# Configuration
DATA_DIR = "research/data"
VIDEO_DIR = os.path.join(DATA_DIR, "TrainValVideo")
FRAMES_PER_VIDEO = 10  # For CLIP
CLIP_DIM = 512
MOTION_DIM = 512       # r3d_18 output dim
MAX_VIDEOS = 300       # Process 300 videos for training


def extract_frames(video_path, num_frames=10):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        return None
        
    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    frames = []
    
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(frame))
            
    cap.release()
    
    # Pad if not enough frames
    while len(frames) < num_frames:
        frames.append(frames[-1] if frames else Image.new('RGB', (224, 224)))
        
    return frames

def extract_video_clip(video_path, num_frames=16):
    """Extract a continuous clip for 3D CNN"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    frames = []
    while len(frames) < num_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (112, 112)) # ResNet3D expects 112x112
        frames.append(frame)
    
    cap.release()
    
    # Pad or Loop
    while len(frames) < num_frames:
        frames.append(frames[-1] if frames else np.zeros((112, 112, 3), dtype=np.uint8))
        
    # Convert to tensor [C, T, H, W]
    # Frames are [T, H, W, C] -> [C, T, H, W]
    frames = np.array(frames)
    frames = torch.from_numpy(frames).permute(3, 0, 1, 2).float() / 255.0
    
    # Normalize (standard ImageNet means/stds)
    # Manual normalization for [C, T, H, W]
    mean = torch.tensor([0.43216, 0.394666, 0.37645]).view(3, 1, 1, 1)
    std = torch.tensor([0.22803, 0.22145, 0.216989]).view(3, 1, 1, 1)
    frames = (frames - mean) / std
    
    return frames.unsqueeze(0) # Add batch dim

def prepare_data():
    print(f"Processing videos from {VIDEO_DIR}...")
    
    # 1. Load Models
    print("Loading CLIP model...")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    

    
    # 2. Find Videos
    video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(('.mp4', '.avi', '.mkv', '.webm'))]
    video_files = video_files[:MAX_VIDEOS]  # Limit to MAX_VIDEOS
    
    print(f"Found {len(video_files)} videos to process.")
    
    clip_features_list = []
    motion_features_list = []
    captions = []
    
    # 3. Process Videos
    for video_file in tqdm(video_files, desc="Extracting features"):
        video_path = os.path.join(VIDEO_DIR, video_file)
        
        # --- Stream A: Spatial (CLIP) ---
        frames = extract_frames(video_path, FRAMES_PER_VIDEO)
        if not frames:
            continue
            
        inputs = clip_processor(images=frames, return_tensors="pt", padding=True)
        with torch.no_grad():
            clip_out = clip_model.get_image_features(**inputs)
        clip_features_list.append(clip_out.unsqueeze(0))
        
        # --- Stream B: Motion (Raw Clips for End-to-End Training) ---
        # Extract clip for 3D CNN input [C, T, H, W]
        motion_input = extract_video_clip(video_path, num_frames=16)
        motion_features_list.append(motion_input) # Save raw tensor
        
        # Caption
        captions.append(f"A video showing {video_file}")
        
    if not clip_features_list:
        print("No features extracted!")
        return
        
    # 4. Save Data
    clip_tensor = torch.cat(clip_features_list, dim=0)     # [N, 10, 512]
    motion_tensor = torch.cat(motion_features_list, dim=0) # [N, C, T, H, W]
    
    torch.save(clip_tensor, os.path.join(DATA_DIR, "video_features_clip.pt"))
    torch.save(motion_tensor, os.path.join(DATA_DIR, "video_clips.pt"))
    
    with open(os.path.join(DATA_DIR, "captions.json"), "w") as f:
        json.dump(captions, f)
        
    print(f"\nData preparation complete!")
    print(f"Saved CLIP features: {clip_tensor.shape}")
    print(f"Saved Raw Video Clips: {motion_tensor.shape}")
    print(f"Saved {len(captions)} captions")

if __name__ == "__main__":
    prepare_data()
