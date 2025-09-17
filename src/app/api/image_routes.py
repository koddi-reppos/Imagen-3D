"""
Advanced image generation and processing APIs
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List, Dict, Any
import json
import magic
from pathlib import Path

from ..database.models import JobType, AssetKind
from ..services.job_manager import job_manager
from ..services.providers.base import provider_manager

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """Upload an image file"""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Size limit (25MB)
    MAX_SIZE = 25 * 1024 * 1024
    content = await file.read()
    
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")
    
    # Detect actual MIME type
    mime_type = magic.from_buffer(content, mime=True)
    if not mime_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Save asset
    metadata = {
        "original_filename": file.filename,
        "description": description,
        "upload_method": "user_upload"
    }
    
    asset_id = await job_manager.save_asset(
        content,
        file.filename or "uploaded_image",
        AssetKind.IMAGE,
        mime_type,
        metadata
    )
    
    asset = await job_manager.get_asset(asset_id)
    
    return {
        "success": True,
        "asset_id": asset_id,
        "filename": asset["filename"],
        "size_bytes": asset["size_bytes"],
        "mime_type": asset["mime_type"]
    }


@router.post("/generate")
async def generate_image(
    prompt: str = Form(...),
    provider: str = Form("openai"),
    model: Optional[str] = Form("dall-e-3"),
    size: Optional[str] = Form("1024x1024"),
    quality: Optional[str] = Form("standard"),
    style: Optional[str] = Form("vivid")
):
    """Generate an image from text prompt"""
    
    # Check if provider is available
    available_providers = provider_manager.get_available_providers()
    if provider not in available_providers.get("text_to_image", []):
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    # Create job
    params = {
        "prompt": prompt,
        "options": {
            "model": model,
            "size": size,
            "quality": quality,
            "style": style
        }
    }
    
    job_id = await job_manager.create_job(JobType.TEXT_TO_IMAGE, params, provider)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Image generation started",
        "estimated_duration": "10-30 seconds"
    }


@router.post("/enhance/{asset_id}")
async def enhance_image(
    asset_id: str,
    operations: List[str] = Form(...),  # ["upscale", "denoise", "background_remove"]
    provider: str = Form("clipdrop")
):
    """Enhance an existing image"""
    
    # Get original asset
    asset = await job_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset["kind"] != AssetKind.IMAGE.value:
        raise HTTPException(status_code=400, detail="Asset must be an image")
    
    # Check if provider is available
    available_providers = provider_manager.get_available_providers()
    if provider not in available_providers.get("image_enhance", []):
        raise HTTPException(status_code=400, detail=f"Enhancement provider {provider} not available")
    
    # Create job
    params = {
        "asset_id": asset_id,
        "operations": operations,
        "options": {}
    }
    
    job_id = await job_manager.create_job(JobType.IMAGE_ENHANCE, params, provider)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Image enhancement started",
        "operations": operations
    }


@router.get("/")
async def list_images(limit: int = 20):
    """List uploaded and generated images"""
    
    assets = await job_manager.list_assets(AssetKind.IMAGE, limit)
    
    return {
        "images": assets,
        "count": len(assets)
    }


@router.get("/{asset_id}")
async def get_image_info(asset_id: str):
    """Get image information"""
    
    asset = await job_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if asset["kind"] != AssetKind.IMAGE.value:
        raise HTTPException(status_code=400, detail="Asset is not an image")
    
    return asset


@router.get("/{asset_id}/download")
async def download_image(asset_id: str):
    """Download an image file"""
    
    asset = await job_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    
    file_path = Path(asset["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=asset["filename"],
        media_type=asset["mime_type"]
    )


@router.delete("/{asset_id}")
async def delete_image(asset_id: str):
    """Delete an image"""
    
    asset = await job_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file from disk
    file_path = Path(asset["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    database = job_manager.database
    await database.execute(
        "DELETE FROM assets WHERE id = :asset_id",
        {"asset_id": asset_id}
    )
    
    return {"success": True, "message": "Image deleted"}


@router.post("/{asset_id}/to-3d")
async def image_to_3d(
    asset_id: str,
    provider: str = Form("meshy"),
    style: str = Form("realistic"),
    quality: str = Form("high")
):
    """Convert image to 3D model"""
    
    # Get original asset
    asset = await job_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if asset["kind"] != AssetKind.IMAGE.value:
        raise HTTPException(status_code=400, detail="Asset must be an image")
    
    # Check if provider is available
    available_providers = provider_manager.get_available_providers()
    if provider not in available_providers.get("image_to_3d", []):
        raise HTTPException(status_code=400, detail=f"3D conversion provider {provider} not available")
    
    # Create job
    params = {
        "asset_id": asset_id,
        "options": {
            "style": style,
            "quality": quality
        }
    }
    
    job_id = await job_manager.create_job(JobType.IMAGE_TO_3D, params, provider)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Image-to-3D conversion started",
        "estimated_duration": "2-5 minutes"
    }