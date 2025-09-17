"""
API routes for 3D model generation
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any

from ..models.schemas import (
    GenerateRequest, GenerateResponse, FileListResponse, ZipRequest, TemplateResponse,
    CubeParams, CylinderParams, SphereParams, CustomBoxParams, AIModelParams
)
from ..services.generator import (
    generate_cube, generate_cylinder, generate_sphere, generate_custom_box
)
from ..services.ai_generator import ai_generator
from ..services.storage import storage

router = APIRouter()


async def validate_and_generate(model_type: str, params: Dict[str, Any]) -> tuple:
    """Validate parameters and generate model"""
    try:
        if model_type == "cube":
            validated_params = CubeParams(**params)
            return generate_cube(validated_params.size)
        
        elif model_type == "cylinder":
            validated_params = CylinderParams(**params)
            return generate_cylinder(
                validated_params.radius, 
                validated_params.height, 
                validated_params.segments
            )
        
        elif model_type == "sphere":
            validated_params = SphereParams(**params)
            return generate_sphere(validated_params.radius, validated_params.segments)
        
        elif model_type == "custom_box":
            validated_params = CustomBoxParams(**params)
            return generate_custom_box(
                validated_params.length,
                validated_params.width,
                validated_params.height,
                validated_params.wall_thickness
            )
        
        elif model_type == "ai_model":
            validated_params = AIModelParams(**params)
            return await ai_generator.generate_professional_model(
                template_id=validated_params.template_id,
                custom_prompt=validated_params.custom_prompt
            )
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=TemplateResponse)
async def get_templates():
    """Get available AI model templates"""
    try:
        templates = ai_generator.get_available_templates()
        return TemplateResponse(templates=templates, total_count=len(templates))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_model(request: GenerateRequest):
    """Generate a 3D model and return metadata"""
    try:
        # Generate STL content and metadata
        stl_content, metadata = await validate_and_generate(request.model_type, request.params)
        
        # Save file to storage
        file_metadata = storage.save_file(stl_content, metadata)
        
        return GenerateResponse(
            success=True,
            message="Model generated successfully",
            metadata=file_metadata,
            download_url=f"/api/files/{file_metadata.filename}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/files", response_model=FileListResponse)
async def list_files():
    """List all generated STL files"""
    try:
        files = storage.list_files()
        return FileListResponse(files=files, total_count=len(files))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/files/{filename}")
async def download_file(filename: str):
    """Download a specific STL file"""
    try:
        file_path = storage.get_file_path(filename)
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/zip")
async def create_zip(request: ZipRequest):
    """Create and download a ZIP file with selected STL files"""
    try:
        zip_path = storage.create_zip(request.filenames)
        if not zip_path:
            raise HTTPException(status_code=400, detail="Failed to create ZIP file")
        
        def cleanup_zip():
            # Generator to stream the file and cleanup after
            try:
                with open(zip_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Cleanup ZIP file after streaming
                if zip_path.exists():
                    zip_path.unlink()
        
        return StreamingResponse(
            cleanup_zip(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_path.name}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZIP creation failed: {str(e)}")