"""
Database models for advanced AI platform
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_ENHANCE = "image_enhance"
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    BASIC_3D = "basic_3d"


class AssetKind(str, Enum):
    IMAGE = "image"
    MESH = "mesh"
    ZIP = "zip"
    PREVIEW = "preview"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)  # JobType
    status = Column(String, default=JobStatus.PENDING.value)
    provider = Column(String, nullable=True)  # AI provider used
    
    # Input parameters (JSON string)
    params = Column(Text, nullable=True)
    
    # Results
    asset_id = Column(String, nullable=True)  # Reference to created asset
    output_metadata = Column(Text, nullable=True)  # JSON with additional info
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Progress tracking
    progress_percent = Column(Integer, default=0)
    estimated_duration = Column(Integer, nullable=True)  # seconds
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # External tracking
    external_job_id = Column(String, nullable=True)  # For long-running external APIs


class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    kind = Column(String, nullable=False)  # AssetKind
    
    # File info
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    
    # Metadata
    size_bytes = Column(Integer, nullable=False)
    checksum = Column(String, nullable=True)  # SHA256
    width = Column(Integer, nullable=True)  # For images
    height = Column(Integer, nullable=True)  # For images
    
    # 3D specific
    triangles = Column(Integer, nullable=True)
    
    # Preview info
    preview_asset_id = Column(String, nullable=True)  # Reference to preview image
    
    # Additional metadata (JSON string)
    metadata = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Access tracking
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)


class AIProviderConfig(Base):
    __tablename__ = "ai_provider_configs"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    
    # Capabilities
    supports_text_to_image = Column(Boolean, default=False)
    supports_image_enhance = Column(Boolean, default=False)
    supports_text_to_3d = Column(Boolean, default=False)
    supports_image_to_3d = Column(Boolean, default=False)
    
    # Limits
    max_concurrent_jobs = Column(Integer, default=3)
    rate_limit_per_minute = Column(Integer, default=10)
    max_image_size_mb = Column(Float, default=25.0)
    
    # Cost tracking
    cost_per_request = Column(Float, default=0.0)
    
    # Configuration (JSON string)
    config = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())