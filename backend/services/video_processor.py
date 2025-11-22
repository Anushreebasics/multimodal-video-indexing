import uuid
import os
import subprocess
import cv2
from typing import List

class VideoProcessor:
    def __init__(self):
        self.upload_dir = "backend/uploads"
        self.frames_dir = "backend/frames"
        self.audio_dir = "backend/audio"
        os.makedirs(self.frames_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)

    def process_video(self, video_path: str) -> str:
        video_id = str(uuid.uuid4())
        print(f"Processing video: {video_path} with ID: {video_id}")
        
        # 1. Extract Audio
        audio_path = self.extract_audio(video_path, video_id)
        
        # 2. Extract Frames (e.g., every 1 second)
        frame_paths = self.extract_frames(video_path, video_id, interval=1)
        
        return video_id

    def extract_audio(self, video_path: str, video_id: str) -> str:
        audio_path = os.path.join(self.audio_dir, f"{video_id}.mp3")
        # ffmpeg -i input.mp4 -q:a 0 -map a output.mp3
        command = [
            "ffmpeg", "-i", video_path,
            "-q:a", "0", "-map", "a",
            audio_path, "-y"
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Audio extracted to {audio_path}")
            return audio_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            return ""

    def extract_frames(self, video_path: str, video_id: str, interval: int = 1) -> List[str]:
        video_frames_dir = os.path.join(self.frames_dir, video_id)
        os.makedirs(video_frames_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval)
        
        frame_paths = []
        count = 0
        saved_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % frame_interval == 0:
                frame_name = f"frame_{saved_count}.jpg"
                frame_path = os.path.join(video_frames_dir, frame_name)
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                saved_count += 1
            
            count += 1
        
        cap.release()
        print(f"Extracted {len(frame_paths)} frames to {video_frames_dir}")
        return frame_paths
