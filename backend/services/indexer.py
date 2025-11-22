import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List
import uuid
import torch
import os
from backend.services.temporal_model import TemporalEncoder

class Indexer:
    def __init__(self):
        print("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(path="backend/chroma_db")
        self.collection = self.client.get_or_create_collection(name="video_index")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load Temporal Model
        print("Loading Temporal Fusion Model...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.temporal_model = TemporalEncoder(output_dim=384).to(self.device)
        model_path = "backend/models/temporal_encoder.pt"
        if os.path.exists(model_path):
            self.temporal_model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.temporal_model.eval()
            print("Temporal Fusion Model loaded.")
        else:
            print("Warning: Temporal Fusion Model weights not found.")
            
        print("ChromaDB initialized.")

    def index_features(self, video_id: str, features: Dict[str, Any]):
        print(f"Indexing features for video {video_id}...")
        
        # 1. Index Transcript
        for segment in features.get("transcript", []):
            text = segment["text"]
            start = segment["start"]
            end = segment["end"]
            self._add_to_index(
                video_id=video_id,
                text=text,
                metadata={
                    "type": "transcript",
                    "start": start,
                    "end": end,
                    "video_id": video_id
                }
            )
            
        # 2. Index Visual Objects & OCR
        for frame_data in features.get("objects", []):
            timestamp = frame_data["timestamp"]
            
            # Index Objects
            objects = [obj["label"] for obj in frame_data["objects"]]
            if objects:
                text = f"Objects: {', '.join(objects)}"
                self._add_to_index(
                    video_id=video_id,
                    text=text,
                    metadata={
                        "type": "visual",
                        "timestamp": timestamp,
                        "video_id": video_id,
                        "objects": ",".join(objects)
                    }
                )
            
            # Index OCR
            ocr_text = frame_data.get("ocr_text", [])
            if ocr_text:
                text = f"Text on screen: {' '.join(ocr_text)}"
                self._add_to_index(
                    video_id=video_id,
                    text=text,
                    metadata={
                        "type": "ocr",
                        "timestamp": timestamp,
                        "video_id": video_id
                    }
                )
                
        # 3. Index Temporal Video Embedding
        if "frame_embeddings" in features:
            print(f"Generating temporal embedding for {video_id}...")
            frame_embeddings = torch.tensor(features["frame_embeddings"]).unsqueeze(0).to(self.device) # [1, Frames, 512]
            with torch.no_grad():
                video_embedding = self.temporal_model(frame_embeddings).squeeze(0).cpu().tolist() # [384]
            
            self._add_embedding_to_index(
                video_id=video_id,
                embedding=video_embedding,
                text="Video Content Summary", # Placeholder text
                metadata={
                    "type": "video_summary",
                    "start": 0, # Represents whole video
                    "end": features.get("duration", 0), # We should capture duration
                    "video_id": video_id
                }
            )
            
        print(f"Indexing complete for {video_id}")

    def _add_to_index(self, video_id: str, text: str, metadata: Dict[str, Any]):
        embedding = self.embedding_model.encode(text).tolist()
        self._add_embedding_to_index(video_id, embedding, text, metadata)

    def _add_embedding_to_index(self, video_id: str, embedding: List[float], text: str, metadata: Dict[str, Any]):
        doc_id = f"{video_id}_{str(uuid.uuid4())}"
        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def search(self, query: str, video_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Build where clause for filtering by video_id
        where_clause = {"video_id": video_id} if video_id else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit if not video_id else limit * 10,  # Get more results if filtering
            where=where_clause
        )
        
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else 0
                })
        
        # Limit results after filtering
        return formatted_results[:limit]
