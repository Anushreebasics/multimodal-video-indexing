from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from backend.services.video_processor import VideoProcessor
from backend.services.feature_extractor import FeatureExtractor
from backend.services.indexer import Indexer
from backend.services.face_recognition_service import FaceRecognitionService
import shutil
import os

router = APIRouter()

# Initialize services (Lazy loading might be better for production, but this is fine for now)
video_processor = VideoProcessor()
feature_extractor = FeatureExtractor()
indexer = Indexer()
face_service = FaceRecognitionService()

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_video_task(video_path: str, video_id: str):
    print(f"Starting background processing for {video_id}...")
    # 1. Extract Audio & Frames
    # Note: process_video in VideoProcessor currently generates ID and does extraction. 
    # We should refactor slightly or just use the extraction methods directly if we already have ID.
    # Let's use the extraction methods directly since we want to control the flow here.
    
    audio_path = video_processor.extract_audio(video_path, video_id)
    frame_paths = video_processor.extract_frames(video_path, video_id, interval=1)
    
    # 2. Extract Features
    features = feature_extractor.extract_features(video_path, audio_path, frame_paths)
    
    # 3. Detect and encode faces
    print(f"Detecting faces in {len(frame_paths)} frames...")
    all_faces = []
    for i, frame_path in enumerate(frame_paths):
        if os.path.exists(frame_path):
            try:
                faces = face_service.detect_and_encode_faces(frame_path, video_id, timestamp=i)
                if faces:
                    print(f"  Frame {i}: Found {len(faces)} face(s)")
                all_faces.extend(faces)
            except Exception as e:
                print(f"Warning: Face detection failed for frame {i}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Add faces to database
    print(f"Total faces detected: {len(all_faces)}")
    if all_faces:
        try:
            print(f"Adding {len(all_faces)} faces to database...")
            face_service.add_faces_to_database(all_faces)
            print(f"Detected {len(all_faces)} faces")
            
            # Cluster faces
            print(f"Clustering faces for video {video_id}...")
            clusters = face_service.cluster_faces(video_id)
            print(f"Clustered into {len(clusters)} groups")
            print(f"Cluster details: {clusters}")
        except Exception as e:
            print(f"Warning: Face clustering failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No faces detected in this video")
    
    # 4. Index Features
    indexer.index_features(video_id, features)
    
    # 5. Extract and enrich entities with Knowledge Graph
    try:
        from backend.services.knowledge_graph import KnowledgeGraphService
        kg_service = KnowledgeGraphService()
        
        # Extract entities from transcript
        all_entities = []
        for segment in features.get("transcript", []):
            text = segment.get("text", "")
            if text:
                enriched = kg_service.enrich_text(text)
                if enriched.get("entities"):
                    for entity in enriched["entities"]:
                        entity["timestamp"] = segment.get("start", 0)
                        entity["video_id"] = video_id
                        all_entities.append(entity)
        
        # Extract entities from OCR text
        for obj_data in features.get("objects", []):
            ocr_texts = obj_data.get("ocr_text", [])
            if ocr_texts:
                combined_text = " ".join(ocr_texts)
                enriched = kg_service.enrich_text(combined_text)
                if enriched.get("entities"):
                    for entity in enriched["entities"]:
                        entity["timestamp"] = obj_data.get("timestamp", 0)
                        entity["video_id"] = video_id
                        all_entities.append(entity)
        
        if all_entities:
            print(f"Extracted {len(all_entities)} entities with knowledge graph enrichment")
            # Index entities for enhanced search
            for entity in all_entities:
                entity_text = f"{entity['text']} ({entity['label']})"
                if entity.get("wikidata"):
                    entity_text += f" - {entity['wikidata'].get('description', '')}"
                
                indexer._add_to_index(
                    video_id=video_id,
                    text=entity_text,
                    metadata={
                        "type": "entity",
                        "entity_type": entity["label"],
                        "timestamp": entity.get("timestamp", 0),
                        "video_id": video_id,
                        "wikidata_id": entity.get("wikidata", {}).get("wikidata_id", "")
                    }
                )
    except Exception as e:
        print(f"Warning: Knowledge graph enrichment failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Detect temporal events
    try:
        from backend.services.event_detector import EventDetector
        event_detector = EventDetector()
        
        print(f"Detecting temporal events for video {video_id}...")
        
        # Detect scene changes using frame embeddings
        frame_embeddings = features.get("frame_embeddings", [])
        timestamps = list(range(len(frame_embeddings)))  # Frame indices as timestamps
        scene_changes = event_detector.detect_scene_changes(frame_embeddings, timestamps)
        
        # Detect audio events
        audio_events = event_detector.detect_audio_events(audio_path)
        
        # Score and combine all events
        all_events = event_detector.score_events(scene_changes, audio_events)
        
        # Generate summary
        video_duration = len(frame_paths)  # Approximate duration in seconds
        summary = event_detector.generate_summary(all_events, video_duration)
        
        print(f"Detected {len(all_events)} events: {summary['highlight_description']}")
        
        # Store events in a JSON file for this video
        import json
        events_dir = "backend/events"
        os.makedirs(events_dir, exist_ok=True)
        events_file = f"{events_dir}/{video_id}_events.json"
        
        with open(events_file, 'w') as f:
            json.dump({
                "video_id": video_id,
                "duration": video_duration,
                "events": all_events,
                "summary": summary
            }, f, indent=2)
        
        print(f"Events saved to {events_file}")
        
    except Exception as e:
        print(f"Warning: Event detection failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"Background processing complete for {video_id}")

@router.post("/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Generate ID (we can use VideoProcessor to generate ID or do it here)
    # Let's generate here to pass to background task
    import uuid
    video_id = str(uuid.uuid4())
    
    background_tasks.add_task(process_video_task, file_location, video_id)
    
    return {"filename": file.filename, "video_id": video_id, "message": "Video uploaded and processing started in background"}

@router.get("/search")
async def search_videos(query: str, video_id: str = None):
    results = indexer.search(query, video_id=video_id)
    return {"query": query, "results": results}

@router.get("/videos")
async def list_videos():
    # Simple listing of uploaded files for now
    files = os.listdir(UPLOAD_DIR)
    return {"videos": files}

@router.post("/qa")
async def answer_question(question: str, video_id: str):
    """
    Answer a question about a video using BLIP-2.
    
    Args:
        question: Natural language question (e.g., "What color is the car?")
        video_id: ID of the video to query
    
    Returns:
        answer, relevant timestamp, and frame used
    """
    from backend.services.video_qa import VideoQA
    import glob
    
    # Initialize QA model (lazy loading)
    if not hasattr(answer_question, "qa_model"):
        answer_question.qa_model = VideoQA()
    
    # 1. Use semantic search to find relevant segment
    search_results = indexer.search(question, video_id=video_id, limit=1)
    
    if not search_results:
        return {"error": "No relevant content found for this question"}
    
    # Get timestamp from top result
    top_result = search_results[0]
    timestamp = top_result["metadata"].get("timestamp") or top_result["metadata"].get("start", 0)
    
    # 2. Find the frame closest to this timestamp
    frames_dir = f"backend/frames/{video_id}"
    if not os.path.exists(frames_dir):
        return {"error": "Video frames not found. Ensure video has been processed."}
    
    # Get frame at timestamp (assuming 1 frame per second)
    frame_path = os.path.join(frames_dir, f"frame_{int(timestamp)}.jpg")
    
    # If exact frame doesn't exist, use the first available frame
    if not os.path.exists(frame_path):
        available_frames = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
        if not available_frames:
            return {"error": "No frames available"}
        frame_path = available_frames[0]
    
    # 3. Ask BLIP-2 the question
    qa_result = answer_question.qa_model.answer_question(frame_path, question)
    
    return {
        "answer": qa_result["answer"],
        "question": question,
        "timestamp": timestamp,
        "frame_used": os.path.basename(frame_path),
        "context": top_result["text"]
    }

# Face Recognition Endpoints
@router.get("/faces/clusters")
async def get_face_clusters(video_id: str):
    """Get all face clusters for a video"""
    clusters = face_service.get_clusters_for_video(video_id)
    return {"video_id": video_id, "clusters": clusters}

@router.post("/faces/tag")
async def tag_face(face_id: str, person_name: str):
    """Tag a face with a person's name"""
    face_service.tag_face(face_id, person_name)
    return {"message": f"Face tagged as {person_name}", "face_id": face_id}

@router.get("/faces/search")
async def search_by_person(person_name: str):
    """Find all appearances of a person"""
    results = face_service.search_by_person(person_name)
    return {"person_name": person_name, "appearances": results}

# Event Detection Endpoints
@router.get("/events/{video_id}")
async def get_events(video_id: str):
    """Get all detected events for a video"""
    import json
    events_file = f"backend/events/{video_id}_events.json"
    
    if not os.path.exists(events_file):
        raise HTTPException(status_code=404, detail="Events not found for this video")
    
    with open(events_file, 'r') as f:
        data = json.load(f)
    
    return data

@router.get("/summary/{video_id}")
async def get_summary(video_id: str):
    """Get video summary with highlights"""
    import json
    events_file = f"backend/events/{video_id}_events.json"
    
    if not os.path.exists(events_file):
        raise HTTPException(status_code=404, detail="Summary not found for this video")
    
    with open(events_file, 'r') as f:
        data = json.load(f)
    
    return {
        "video_id": video_id,
        "summary": data.get("summary", {}),
        "top_moments": data.get("summary", {}).get("top_moments", [])
    }
