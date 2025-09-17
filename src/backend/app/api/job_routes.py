"""
Job management and WebSocket APIs
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio

from ..services.job_manager import job_manager
from ..services.providers.base import provider_manager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/")
async def list_jobs(limit: int = 50, offset: int = 0):
    """List all jobs"""
    
    jobs = await job_manager.list_jobs(limit, offset)
    
    return {
        "jobs": jobs,
        "count": len(jobs)
    }


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and details"""
    
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in ["pending", "processing"]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    # Update job status to cancelled
    database = job_manager.database
    await database.execute(
        "UPDATE jobs SET status = 'cancelled' WHERE id = :job_id",
        {"job_id": job_id}
    )
    
    return {"success": True, "message": "Job cancelled"}


@router.get("/providers/available")
async def get_available_providers():
    """Get all available AI providers and their capabilities"""
    
    providers = provider_manager.get_available_providers()
    
    # Add provider details
    detailed_providers = {
        "text_to_image": {
            "openai": {
                "name": "OpenAI DALL-E",
                "models": ["dall-e-3", "dall-e-2"],
                "sizes": ["1024x1024", "1792x1024", "1024x1792"],
                "styles": ["vivid", "natural"],
                "quality": ["standard", "hd"],
                "speed": "fast",
                "cost": "medium"
            }
        },
        "image_enhance": {},
        "text_to_3d": {
            "meshy": {
                "name": "Meshy AI",
                "styles": ["realistic", "cartoon", "fantasy"],
                "quality": ["draft", "standard", "high"],
                "speed": "medium",
                "cost": "high"
            }
        },
        "image_to_3d": {
            "meshy": {
                "name": "Meshy AI Image-to-3D",
                "styles": ["realistic", "stylized"],
                "quality": ["draft", "standard", "high"],
                "speed": "medium",
                "cost": "high"
            }
        }
    }
    
    return {
        "available": providers,
        "details": detailed_providers
    }


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time job updates"""
    
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connection",
            "message": "Connected to job updates"
        }, websocket)
        
        # Keep connection alive and send periodic updates
        while True:
            # In a real implementation, you'd listen for job status changes
            # and send updates when they occur
            await asyncio.sleep(5)
            
            # Send heartbeat
            await manager.send_personal_message({
                "type": "heartbeat",
                "timestamp": asyncio.get_event_loop().time()
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)