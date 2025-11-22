from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api import endpoints
import os

app = FastAPI(title="Multimodal Video Indexer")

# Create directories if they don't exist
os.makedirs("backend/uploads", exist_ok=True)
os.makedirs("backend/frames", exist_ok=True)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")
app.mount("/frames", StaticFiles(directory="backend/frames"), name="frames")

# Include routers
app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Multimodal Video Indexer API is running"}
