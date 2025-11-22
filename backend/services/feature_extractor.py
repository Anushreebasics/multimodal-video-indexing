import whisper
from ultralytics import YOLO
import easyocr
import cv2
import torch
import os
from PIL import Image
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class FeatureExtractor:
    def __init__(self):
        print("Loading models...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.whisper_model = whisper.load_model("base", device=self.device)
        self.yolo_model = YOLO("yolov8n.pt")  # Load nano model for speed
        self.reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        # Load CLIP for visual features (ViT-B-32 outputs 512-dim)
        self.clip_model = SentenceTransformer('clip-ViT-B-32')
        print("Models loaded.")

    def extract_features(self, video_path: str, audio_path: str, frame_paths: List[str]) -> Dict[str, Any]:
        features = {
            "transcript": [],
            "objects": [],
            "text": []
        }
        
        # 1. Speech-to-Text
        if audio_path and os.path.exists(audio_path):
            print("Transcribing audio...")
            result = self.whisper_model.transcribe(audio_path)
            features["transcript"] = result["segments"]
        
        # 2. Object Detection & OCR on Frames
        print(f"Analyzing {len(frame_paths)} frames...")
        for i, frame_path in enumerate(frame_paths):
            if not os.path.exists(frame_path):
                continue
                
            # Object Detection
            results = self.yolo_model(frame_path, verbose=False)
            frame_objects = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = self.yolo_model.names[cls_id]
                    conf = float(box.conf[0])
                    frame_objects.append({"label": label, "confidence": conf})
            
            # OCR
            ocr_results = self.reader.readtext(frame_path, detail=0)
            
            if frame_objects or ocr_results:
                features["objects"].append({
                    "frame_index": i,
                    "timestamp": i, # Assuming 1 frame per second for now
                    "objects": frame_objects,
                    "ocr_text": ocr_results
                })
        
        # 3. Extract CLIP Frame Embeddings for Temporal Model
        # Load images
        images = []
        valid_frame_paths = [p for p in frame_paths if os.path.exists(p)]
        if valid_frame_paths:
            for p in valid_frame_paths:
                images.append(Image.open(p))
            
            print(f"Encoding {len(images)} frames with CLIP...")
            # Encode images
            frame_embeddings = self.clip_model.encode(images)
            features["frame_embeddings"] = frame_embeddings.tolist() # List of lists
                
        return features
