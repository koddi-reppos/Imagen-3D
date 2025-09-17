"""
Pydantic models for API validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Dict, Any, Optional


class CubeParams(BaseModel):
    size: float = Field(..., ge=0.1, le=500.0, description="Cube size in mm")


class CylinderParams(BaseModel):
    radius: float = Field(..., ge=0.1, le=250.0, description="Cylinder radius in mm")
    height: float = Field(..., ge=0.1, le=500.0, description="Cylinder height in mm")
    segments: int = Field(20, ge=6, le=256, description="Number of segments for smoothness")


class SphereParams(BaseModel):
    radius: float = Field(..., ge=0.1, le=250.0, description="Sphere radius in mm")
    segments: int = Field(20, ge=6, le=128, description="Number of segments for smoothness")


class CustomBoxParams(BaseModel):
    length: float = Field(..., ge=1.0, le=500.0, description="Box length in mm")
    width: float = Field(..., ge=1.0, le=500.0, description="Box width in mm")
    height: float = Field(..., ge=1.0, le=500.0, description="Box height in mm")
    wall_thickness: float = Field(..., ge=0.1, le=50.0, description="Wall thickness in mm")
    
    @validator('wall_thickness')
    def validate_wall_thickness(cls, v, values):
        if 'length' in values and 'width' in values:
            min_dimension = min(values['length'], values['width']) / 2
            if v >= min_dimension:
                raise ValueError(f"Wall thickness must be less than {min_dimension:.1f}mm")
        return v


class AIModelParams(BaseModel):
    template_id: Optional[str] = Field(None, description="ID of predefined template")
    custom_prompt: Optional[str] = Field(None, description="Custom text prompt for AI generation")
    style: Literal["realistic", "cartoon", "fantasy", "sci-fi"] = Field("realistic", description="Art style")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.template_id and not self.custom_prompt:
            raise ValueError("Either template_id or custom_prompt must be provided")


class GenerateRequest(BaseModel):
    model_type: Literal["cube", "cylinder", "sphere", "custom_box", "ai_model"] = Field(..., description="Type of 3D model to generate")
    params: Dict[str, Any] = Field(..., description="Parameters specific to the model type")


class FileMetadata(BaseModel):
    filename: str
    model_type: str
    dimensions: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    triangles: int
    size_bytes: int
    created_at: str
    prompt: Optional[str] = None
    style: Optional[str] = None
    ai_provider: Optional[str] = None


class GenerateResponse(BaseModel):
    success: bool
    message: str
    metadata: Optional[FileMetadata] = None
    download_url: Optional[str] = None


class FileListResponse(BaseModel):
    files: List[FileMetadata]
    total_count: int


class ZipRequest(BaseModel):
    filenames: List[str] = Field(..., min_length=1, description="List of STL filenames to include in ZIP")


class TemplateResponse(BaseModel):
    templates: Dict[str, Dict[str, Any]]
    total_count: int