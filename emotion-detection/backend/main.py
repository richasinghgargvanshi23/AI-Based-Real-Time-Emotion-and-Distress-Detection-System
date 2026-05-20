"""
AI-Based Real-Time Emotion and Distress Detection System
Backend API - FastAPI + OpenCV + DeepFace
"""

import cv2
import base64
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import time
from datetime import datetime
from typing import Optional
import logging

from emotion_engine import EmotionEngine
from distress_analyzer import DistressAnalyzer
from session_manager import SessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Emotion & Distress Detection API",
    description="Real-time facial emotion recognition and distress detection for mental wellness monitoring",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

emotion_engine = EmotionEngine()
distress_analyzer = DistressAnalyzer()
session_manager = SessionManager()


@app.get("/")
async def root():
    return {"message": "Emotion Detection API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": emotion_engine.is_loaded()
    }


@app.post("/analyze/image")
async def analyze_image(payload: dict):
    """Analyze a single base64-encoded image frame."""
    try:
        image_data = payload.get("image")
        if not image_data:
            raise HTTPException(status_code=400, detail="No image provided")

        # Decode base64 image
        if "," in image_data:
            image_data = image_data.split(",")[1]

        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # Run emotion analysis
        result = emotion_engine.analyze_frame(frame)

        # Calculate distress score
        if result.get("faces"):
            distress_info = distress_analyzer.calculate_distress(result["faces"])
            result["distress"] = distress_info

        result["timestamp"] = datetime.utcnow().isoformat()
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/stream/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time video stream processing."""
    await websocket.accept()
    session_manager.create_session(session_id)
    logger.info(f"WebSocket connected: session={session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "frame":
                frame_data = message.get("data", "")
                if "," in frame_data:
                    frame_data = frame_data.split(",")[1]

                img_bytes = base64.b64decode(frame_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    result = emotion_engine.analyze_frame(frame)

                    if result.get("faces"):
                        distress_info = distress_analyzer.calculate_distress(result["faces"])
                        result["distress"] = distress_info
                        session_manager.add_record(session_id, result)

                    result["session_id"] = session_id
                    result["timestamp"] = datetime.utcnow().isoformat()
                    await websocket.send_text(json.dumps(result))

            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        session_manager.end_session(session_id)


@app.get("/session/{session_id}/report")
async def get_session_report(session_id: str):
    """Get emotion analytics report for a session."""
    report = session_manager.generate_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(content=report)


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 100):
    """Get raw emotion history for a session."""
    history = session_manager.get_history(session_id, limit)
    return JSONResponse(content={"session_id": session_id, "records": history})


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clear session data."""
    session_manager.delete_session(session_id)
    return {"message": f"Session {session_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
