import numpy as np
from typing import List, Dict, Any, Tuple
import librosa
import os

class EventDetector:
    def __init__(self):
        self.scene_change_threshold = 0.3  # Cosine similarity threshold
        self.audio_spike_threshold = 0.7   # Normalized volume threshold
        
    def detect_scene_changes(self, frame_embeddings: List[np.ndarray], timestamps: List[float]) -> List[Dict[str, Any]]:
        """
        Detect scene changes by analyzing frame embedding similarity.
        
        Args:
            frame_embeddings: List of CLIP embeddings for each frame
            timestamps: Corresponding timestamps
            
        Returns:
            List of scene change events
        """
        if len(frame_embeddings) < 2:
            return []
        
        scene_changes = []
        
        for i in range(1, len(frame_embeddings)):
            # Calculate cosine similarity between consecutive frames
            emb1 = np.array(frame_embeddings[i-1])
            emb2 = np.array(frame_embeddings[i])
            
            # Normalize
            emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-8)
            emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-8)
            
            similarity = np.dot(emb1_norm, emb2_norm)
            
            # Scene change detected if similarity drops significantly
            if similarity < (1 - self.scene_change_threshold):
                scene_changes.append({
                    "timestamp": timestamps[i],
                    "type": "scene_change",
                    "score": 1 - similarity,  # Higher score = bigger change
                    "description": f"Scene transition detected (similarity: {similarity:.2f})"
                })
        
        return scene_changes
    
    def detect_audio_events(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Detect audio events like spikes, silence, and music changes.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of audio events
        """
        if not os.path.exists(audio_path):
            return []
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Calculate RMS energy (volume)
            rms = librosa.feature.rms(y=y)[0]
            
            # Normalize
            rms_normalized = rms / (np.max(rms) + 1e-8)
            
            # Calculate time for each RMS frame
            hop_length = 512
            times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
            
            events = []
            
            # Detect volume spikes (applause, explosions, etc.)
            for i, (time, volume) in enumerate(zip(times, rms_normalized)):
                if volume > self.audio_spike_threshold:
                    # Check if it's a new spike (not continuation)
                    if i == 0 or rms_normalized[i-1] < self.audio_spike_threshold:
                        events.append({
                            "timestamp": float(time),
                            "type": "audio_spike",
                            "score": float(volume),
                            "description": f"Audio spike detected (volume: {volume:.2f})"
                        })
            
            # Detect silence periods (potential scene transitions)
            silence_threshold = 0.1
            in_silence = False
            silence_start = 0
            
            for i, (time, volume) in enumerate(zip(times, rms_normalized)):
                if volume < silence_threshold and not in_silence:
                    in_silence = True
                    silence_start = time
                elif volume >= silence_threshold and in_silence:
                    in_silence = False
                    duration = time - silence_start
                    if duration > 0.5:  # At least 0.5s of silence
                        events.append({
                            "timestamp": float(silence_start),
                            "type": "silence",
                            "score": float(duration),
                            "description": f"Silence period ({duration:.1f}s)"
                        })
            
            return events
            
        except Exception as e:
            print(f"Error detecting audio events: {e}")
            return []
    
    def score_events(self, 
                     scene_changes: List[Dict], 
                     audio_events: List[Dict],
                     entities: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Combine and score all events to identify highlights.
        
        Args:
            scene_changes: Scene change events
            audio_events: Audio events
            entities: Optional entity mentions
            
        Returns:
            Sorted list of all events with importance scores
        """
        all_events = []
        
        # Add scene changes with boosted scores
        for event in scene_changes:
            event["importance"] = event["score"] * 1.2  # Scene changes are important
            all_events.append(event)
        
        # Add audio events
        for event in audio_events:
            # Audio spikes are more important than silence
            multiplier = 1.5 if event["type"] == "audio_spike" else 0.8
            event["importance"] = event["score"] * multiplier
            all_events.append(event)
        
        # Add entity mentions if provided
        if entities:
            for entity in entities:
                all_events.append({
                    "timestamp": entity.get("timestamp", 0),
                    "type": "entity_mention",
                    "score": 0.7,
                    "importance": 0.9,  # Entity mentions are quite important
                    "description": f"Mentioned: {entity.get('text', 'unknown')}"
                })
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])
        
        return all_events
    
    def generate_summary(self, events: List[Dict[str, Any]], video_duration: float) -> Dict[str, Any]:
        """
        Generate hierarchical summary from events.
        
        Args:
            events: List of all events
            video_duration: Total video duration in seconds
            
        Returns:
            Summary with top moments and statistics
        """
        if not events:
            return {
                "top_moments": [],
                "event_count": 0,
                "scene_count": 0,
                "highlight_description": "No significant events detected"
            }
        
        # Get top moments (highest importance scores)
        sorted_events = sorted(events, key=lambda x: x.get("importance", 0), reverse=True)
        top_moments = [e["timestamp"] for e in sorted_events[:5]]
        
        # Count event types
        scene_count = len([e for e in events if e["type"] == "scene_change"])
        audio_spike_count = len([e for e in events if e["type"] == "audio_spike"])
        
        # Generate description
        description = f"Video contains {scene_count} scene changes"
        if audio_spike_count > 0:
            description += f" and {audio_spike_count} audio highlights"
        description += f". Top {min(5, len(top_moments))} moments identified."
        
        return {
            "top_moments": top_moments,
            "event_count": len(events),
            "scene_count": scene_count,
            "audio_spike_count": audio_spike_count,
            "highlight_description": description,
            "events_by_type": {
                "scene_change": scene_count,
                "audio_spike": audio_spike_count,
                "silence": len([e for e in events if e["type"] == "silence"])
            }
        }

if __name__ == "__main__":
    # Test the event detector
    detector = EventDetector()
    print("Event Detector initialized successfully")
