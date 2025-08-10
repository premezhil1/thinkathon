"""
FastAPI Backend for Call Summary and Quality Analyzer
Handles audio upload, processing, and serves the React frontend.
"""

import os
import sys
import json
import uuid
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analyzer import CallAnalyzer
from audio_transcriber import AudioTranscriber
from database import CallAnalyzerDB

# Initialize FastAPI app
app = FastAPI(
    title="Call Summary and Quality Analyzer API",
    description="API for analyzing customer care conversations",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzers and database
call_analyzer = CallAnalyzer()
audio_transcriber = AudioTranscriber()
db = CallAnalyzerDB("../call_analyzer.db")

# In-memory storage for processing status (use Redis in production)
processing_status = {}
analysis_results = {}

# Valid industries (restricted list)
VALID_INDUSTRIES = ['eCommerce', 'Telecom', 'Healthcare', 'Travel', 'Real Estate']

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic models
class AnalysisRequest(BaseModel):
    conversation_data: Dict[str, Any]
    industry: Optional[str] = "general"

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ProcessingStatus(BaseModel):
    analysis_id: str
    status: str  # "processing", "completed", "error"
    progress: int  # 0-100
    stage: str  # "transcription", "analysis", "visualization"
    message: str

class UserCreateRequest(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = ""
    full_name: Optional[str] = ""
    department: Optional[str] = ""
    role: Optional[str] = "user"

class UserUpdateRequest(BaseModel):
    username: str
    email: Optional[str] = ""
    full_name: Optional[str] = ""
    department: Optional[str] = ""
    role: Optional[str] = "user"
    is_active: Optional[bool] = True

# Create necessary directories
os.makedirs("uploads", exist_ok=True)

@app.websocket("/ws/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send current status if available
            if analysis_id in processing_status:
                status = processing_status[analysis_id]
                await websocket.send_json(status)
            
            await asyncio.sleep(1)  # Send updates every second
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def update_progress(analysis_id: str, status: str, progress: int, stage: str, message: str):
    """Update processing progress and notify WebSocket clients."""
    status_update = {
        "analysis_id": analysis_id,
        "status": status,
        "progress": progress,
        "stage": stage,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    processing_status[analysis_id] = status_update
    
    # Broadcast to WebSocket clients
    await manager.broadcast(json.dumps(status_update))

async def process_audio_file(file_path: str, analysis_id: str, industry: str = "general", user_id: str = "default_user"):
    """Background task to process audio file with complete data capture."""
    try:
        await update_progress(analysis_id, "processing", 10, "transcription", "Starting audio transcription...")
        
        # Run CPU-intensive transcription in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            transcription = await loop.run_in_executor(pool, audio_transcriber.transcribe_with_whisper, file_path)
        
        if not transcription:
            await update_progress(analysis_id, "error", 0, "transcription", "Failed to transcribe audio")
            return


        await update_progress(analysis_id, "processing", 30, "transcription", "Starting Speaker Identification...")
        
        # Run CPU-intensive transcription in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            transcription_result = await loop.run_in_executor(pool, audio_transcriber.speaker_with_diarization, file_path, transcription)
        
        if not transcription_result:
            await update_progress(analysis_id, "error", 0, "transcription", "Failed to diarization")
            return

        await update_progress(analysis_id, "processing", 50, "analysis", "Performing NLP analysis...") 

        transcription_result['industry'] = industry

        await update_progress(analysis_id, "processing", 60, "saving", "Analyzing Conversation...")
        
        # Run CPU-intensive analysis in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            analysis_result = await loop.run_in_executor(pool, call_analyzer.analyze_conversation, transcription_result)
        
        await update_progress(analysis_id, "processing", 80, "saving", "Saving analysis results...")
         
        
        # Prepare complete analysis data for database
        complete_analysis_data = {
            'analysis_id': analysis_id,
            'user_id': user_id,
            'processed_at': datetime.now().isoformat(),
            'source_file': os.path.basename(file_path),
            'industry': industry,
            'duration': transcription_result['duration'],
            'participants': len(transcription_result['participants']),
            'sentiment': analysis_result.get('overall_sentiment', {}).get('label', 'neutral'),
            'transcription': transcription_result,
            'conversation': transcription_result.get('dialogue', []) ,
            'analysis': analysis_result,
            'file_path': file_path,
            'quality_score': analysis_result.get('quality_score', 0.0)
        }

        await update_progress(analysis_id, "processing", 90, "visualization", "Generating visualizations...")
        
        # Save to database (run in thread pool to avoid blocking)
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            success = await loop.run_in_executor(pool, db.save_analysis_result, complete_analysis_data)
        if not success:
            await update_progress(analysis_id, "error", 0, "saving", "Failed to save analysis results")
            return
             
        
        # Update final status
        db.save_processing_status(analysis_id, "completed", 100, "Analysis completed successfully")
        await update_progress(analysis_id, "completed", 100, "completed", "Analysis completed successfully!")
        
        # Keep audio file for user access (don't delete)
        # if os.path.exists(file_path):
        #     os.remove(file_path)
            
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        db.save_processing_status(analysis_id, "error", 0, error_msg)
        await update_progress(analysis_id, "error", 0, "error", error_msg)


@app.post("/api/upload-audio", response_model=AnalysisResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    industry: str = Form(...),
    user_id: str = Form("default_user")
):
    """Upload and process audio file with user-based storage."""
    
    # Validate industry
    if industry not in VALID_INDUSTRIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid industry. Must be one of: {', '.join(VALID_INDUSTRIES)}"
        )

    try:    
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Validate file type
        if not file.filename.lower().endswith(('.mp3')):
            raise HTTPException(status_code=400, detail="Unsupported file format")
    
    
        # Create user-specific upload directory
        user_upload_dir = f"uploads/{user_id}"
        os.makedirs(user_upload_dir, exist_ok=True)

        # 2. Save uploaded file
        input_file_path = f"{user_upload_dir}/{analysis_id}_{file.filename}"
        with open(input_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 3. Prepare output path (change to .wav)
        file_path = input_file_path.rsplit(".", 1)[0] + ".wav"

        # 4. Convert using ffmpeg     
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_file_path, "-ac", "1", "-ar", "16000", file_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )     
        
        # Initialize processing status
        processing_status[analysis_id] = {
            "status": "processing",
            "progress": 0,
            "stage": "upload",
            "message": "File uploaded successfully",
            "user_id": user_id,
            "industry": industry,
            "source_file": file.filename,
            "file_path": file_path
        }
        
        # Save initial processing status to database
        db.save_processing_status(analysis_id, "processing", 0, "File uploaded successfully")
        
        # Start background processing
        background_tasks.add_task(process_audio_file, file_path, analysis_id, industry, user_id)
        
        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "File uploaded successfully. Processing started.",
            "user_id": user_id,
            "industry": industry
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/status/{analysis_id}", response_model=ProcessingStatus)
async def get_analysis_status(analysis_id: str):
    #print(f"Status requested for analysis_id={analysis_id}")
    if analysis_id not in processing_status:
        print(f"Analysis {analysis_id} not found")
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    status = processing_status[analysis_id]
    #print(f"Returning status for {analysis_id}: {status}")
    return ProcessingStatus(**status)

@app.get("/api/stats")
async def get_database_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    industry: Optional[str] = None
):
    """Get comprehensive database statistics for homepage with optional filters"""
    try:
        stats = db.get_database_stats(date_from=date_from, date_to=date_to, industry=industry)
        
        # Add top user performance data to stats
        top_user_performance = db.get_top_user_performance_by_sentiment(
            date_from=date_from, 
            date_to=date_to, 
            industry=industry
        )
        stats['top_user_performance'] = top_user_performance
        
        return stats
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get stats: {str(e)}"}
        )

def format_time(seconds):
    seconds = int(seconds)  # ensure integer
    if seconds > 60:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"
    return str(seconds)

@app.get("/api/results/{analysis_id}")
async def get_results(analysis_id: str):
    """Get analysis results"""
    try:
        
        results = db.get_analysis_result(analysis_id)
        if results:           
            
            return results
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Analysis results not found"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get results: {str(e)}"}
        )

@app.get("/api/dashboard/topic-sentiments")
async def get_topic_sentiments(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    industry: Optional[str] = None
):
    """Get topic-sentiment analysis data for dashboard with optional filters."""
    try: 
        data = db.get_topic_sentiment_analysis(
            date_from=date_from,
            date_to=date_to,
            industry=industry
        )
        return JSONResponse(content=data)
    except Exception as e:
        print(f"Error getting topic sentiments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic sentiments: {str(e)}")

@app.get("/api/analyses")
async def list_analyses(user_id: str = None):
    """List all completed analyses, optionally filtered by user."""
    try:
        if user_id:
            # Get analyses for specific user from database
            db_results = db.get_analysis_results_by_user(user_id)
            analyses = []
            for result in db_results:
                analyses.append({
                    "analysis_id": result["analysis_id"],
                    "processed_at": result["processed_at"],
                    "source_file": result["source_file"],
                    "industry": result["industry"],
                    "duration": result["duration"],
                    "participants": result["participants"],
                    "sentiment": result["sentiment"],
                    "quality_score": result.get("analysis", {}).get("quality_score", 0.0),
                    "file_path": result.get("file_path", "")
                })
        else:
            # Get all analyses from database
            db_results = db.get_all_analysis_results()
            analyses = []
            for result in db_results:
                analyses.append({
                    "analysis_id": result["analysis_id"],
                    "processed_at": result["processed_at"],
                    "source_file": result["source_file"],
                    "industry": result["industry"],
                    "duration": result["duration"],
                    "participants": result["participants"],
                    "sentiment": result["sentiment"],
                    "quality_score": result.get("analysis", {}).get("quality_score", 0.0),
                    "file_path": result.get("file_path", "")
                })
        
        return {"analyses": analyses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analyses: {str(e)}")


@app.get("/api/user/{user_id}/status")
async def get_user_status(user_id: str):
    """Get user status with saved audio files and analysis count."""
    try:
        # Get user's analyses from database
        user_analyses = db.get_analysis_results_by_user(user_id)
        
        # Get user's audio files
        user_upload_dir = f"uploads/{user_id}"
        audio_files = []
        if os.path.exists(user_upload_dir):
            for file in os.listdir(user_upload_dir):
                if file.lower().endswith(('.mp3')):
                    file_path = os.path.join(user_upload_dir, file)
                    file_stats = os.stat(file_path)
                    audio_files.append({
                        "filename": file,
                        "size": file_stats.st_size,
                        "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        "path": file_path
                    })
        
        return {
            "user_id": user_id,
            "total_analyses": len(user_analyses),
            "audio_files": audio_files,
            "recent_analyses": user_analyses[:5],  # Last 5 analyses
            "status": "active" if user_analyses else "new"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user status: {str(e)}")

@app.get("/api/industries")
async def get_available_industries():
    """Get list of available industries."""
    return {"industries": VALID_INDUSTRIES}

@app.get("/api/users")
async def get_all_users():
    """Get all users."""
    try:
        users = db.get_all_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@app.get("/api/users/{user_id}/performance")
async def get_user_performance(user_id: str, date_from: str = None, date_to: str = None):
    """Get comprehensive performance metrics for a specific user/agent."""
    try:
        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        performance_data = db.get_user_performance_metrics(user_id, date_from, date_to)
        
        # Add user info to the response
        performance_data['user_info'] = user
        
        return {"performance": performance_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user performance: {str(e)}")

@app.get("/api/topics")
async def get_topic_statistics(date_from: str = None, date_to: str = None, industry: str = None):
    """Get topic distribution statistics with optional filtering."""
    try:
        topic_stats = db.get_topic_statistics(date_from=date_from, date_to=date_to, industry=industry)
        return {"topic_statistics": topic_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic statistics: {str(e)}")

@app.get("/api/history")
async def get_history(date_from: str = None, date_to: str = None):
    """Get analysis history with optional date filtering"""
    try:
        history = db.get_analysis_history(date_from=date_from, date_to=date_to)
        return {"history": history}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get history: {str(e)}"}
        )


@app.post("/api/database/clear-data")
async def clear_all_data():
    """Clear all data from tables without dropping table structure."""
    try:
        success = db.clear_all_data()
        if success:
            # Also clear in-memory storage
            global processing_status, analysis_results
            processing_status.clear()
            analysis_results.clear()
            
            return {"message": "All data cleared successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "api:app",  # Import string required for reload mode
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
