import face_recognition
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple
from sklearn.cluster import DBSCAN
import json
import os

class FaceRecognitionService:
    def __init__(self):
        print("Face Recognition Service initialized")
        self.face_database_path = "backend/face_database.json"
        self.face_database = self._load_face_database()
    
    def _load_face_database(self) -> Dict[str, Any]:
        """Load face database from JSON file"""
        if os.path.exists(self.face_database_path):
            with open(self.face_database_path, 'r') as f:
                return json.load(f)
        return {"faces": [], "people": {}}
    
    def _save_face_database(self):
        """Save face database to JSON file"""
        with open(self.face_database_path, 'w') as f:
            json.dump(self.face_database, f, indent=2)
    
    def detect_and_encode_faces(self, image_path: str, video_id: str, timestamp: float) -> List[Dict[str, Any]]:
        """
        Detect faces in an image and generate encodings.
        
        Args:
            image_path: Path to the image file
            video_id: ID of the video
            timestamp: Timestamp in the video
            
        Returns:
            List of face data with encodings
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations (bounding boxes)
            face_locations = face_recognition.face_locations(image, model="hog")  # Use HOG instead of CNN for stability
            
            # Generate face encodings (128-dimensional vectors)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            faces = []
            for i, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
                face_id = f"{video_id}_{timestamp}_{i}"
                
                face_data = {
                    "face_id": face_id,
                    "video_id": video_id,
                    "timestamp": timestamp,
                    "encoding": encoding.tolist(),  # Convert numpy array to list for JSON
                    "location": location,  # (top, right, bottom, left)
                    "person_name": None,  # To be tagged by user
                    "cluster_id": None  # To be assigned by clustering
                }
                faces.append(face_data)
            
            return faces
        except Exception as e:
            print(f"Error detecting faces in {image_path}: {e}")
            return []
    
    def cluster_faces(self, video_id: str) -> Dict[int, List[str]]:
        """
        Cluster faces from a video using DBSCAN.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary mapping cluster_id to list of face_ids
        """
        # Get all faces for this video
        video_faces = [f for f in self.face_database["faces"] if f["video_id"] == video_id]
        
        if len(video_faces) < 2:
            return {}
        
        # Extract encodings
        encodings = np.array([f["encoding"] for f in video_faces])
        
        # Cluster using DBSCAN (density-based clustering)
        # eps=0.5 is a good default for face_recognition encodings
        clustering = DBSCAN(eps=0.5, min_samples=2, metric='euclidean').fit(encodings)
        
        # Group faces by cluster
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label == -1:  # Noise/outlier
                continue
            # Convert numpy int64 to Python int for JSON serialization
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(video_faces[idx]["face_id"])
            
            # Update cluster_id in database
            for face in self.face_database["faces"]:
                if face["face_id"] == video_faces[idx]["face_id"]:
                    face["cluster_id"] = label
        
        self._save_face_database()
        return clusters
    
    def tag_face(self, face_id: str, person_name: str):
        """
        Tag a face with a person's name.
        All faces in the same cluster will be tagged.
        
        Args:
            face_id: ID of the face to tag
            person_name: Name of the person
        """
        # Find the face
        target_face = None
        for face in self.face_database["faces"]:
            if face["face_id"] == face_id:
                target_face = face
                break
        
        if not target_face:
            return
        
        # Tag this face
        target_face["person_name"] = person_name
        
        # Tag all faces in the same cluster
        cluster_id = target_face.get("cluster_id")
        if cluster_id is not None:
            for face in self.face_database["faces"]:
                if face.get("cluster_id") == cluster_id:
                    face["person_name"] = person_name
        
        # Update people index
        if person_name not in self.face_database["people"]:
            self.face_database["people"][person_name] = []
        
        self.face_database["people"][person_name].append(face_id)
        self._save_face_database()
    
    def search_by_person(self, person_name: str) -> List[Dict[str, Any]]:
        """
        Find all appearances of a person.
        
        Args:
            person_name: Name of the person
            
        Returns:
            List of face occurrences with timestamps
        """
        results = []
        for face in self.face_database["faces"]:
            if face.get("person_name") == person_name:
                results.append({
                    "video_id": face["video_id"],
                    "timestamp": face["timestamp"],
                    "face_id": face["face_id"]
                })
        return results
    
    def add_faces_to_database(self, faces: List[Dict[str, Any]]):
        """Add detected faces to the database"""
        self.face_database["faces"].extend(faces)
        self._save_face_database()
    
    def get_clusters_for_video(self, video_id: str) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get all face clusters for a video.
        
        Returns:
            Dictionary mapping cluster_id to list of face data
        """
        video_faces = [f for f in self.face_database["faces"] if f["video_id"] == video_id]
        
        clusters = {}
        for face in video_faces:
            cluster_id = face.get("cluster_id", -1)
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(face)
        
        return clusters
