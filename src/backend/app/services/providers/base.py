"""
Base interfaces for AI providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProviderTask:
    """Represents a task submitted to an AI provider"""
    id: str
    status: TaskStatus
    progress: int = 0  # 0-100
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    estimated_duration: Optional[int] = None  # seconds


@dataclass
class GeneratedAsset:
    """Represents a generated asset from AI provider"""
    data: bytes
    content_type: str
    filename: str
    metadata: Dict[str, Any] = None


class ImageGenerationProvider(ABC):
    """Base class for text-to-image providers"""
    
    @abstractmethod
    async def create_task(self, prompt: str, **kwargs) -> ProviderTask:
        """Create a new image generation task"""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> ProviderTask:
        """Get the status of a task"""
        pass
    
    @abstractmethod
    async def download_result(self, task: ProviderTask) -> GeneratedAsset:
        """Download the generated image"""
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        pass


class ImageEnhancementProvider(ABC):
    """Base class for image enhancement providers"""
    
    @abstractmethod
    async def create_task(self, image_data: bytes, operations: list, **kwargs) -> ProviderTask:
        """Create a new image enhancement task"""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> ProviderTask:
        """Get the status of a task"""
        pass
    
    @abstractmethod
    async def download_result(self, task: ProviderTask) -> GeneratedAsset:
        """Download the enhanced image"""
        pass


class Text3DProvider(ABC):
    """Base class for text-to-3D providers"""
    
    @abstractmethod
    async def create_task(self, prompt: str, **kwargs) -> ProviderTask:
        """Create a new 3D model generation task from text"""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> ProviderTask:
        """Get the status of a task"""
        pass
    
    @abstractmethod
    async def download_result(self, task: ProviderTask) -> GeneratedAsset:
        """Download the generated 3D model"""
        pass


class Image3DProvider(ABC):
    """Base class for image-to-3D providers"""
    
    @abstractmethod
    async def create_task(self, image_data: bytes, **kwargs) -> ProviderTask:
        """Create a new 3D model generation task from image"""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> ProviderTask:
        """Get the status of a task"""
        pass
    
    @abstractmethod
    async def download_result(self, task: ProviderTask) -> GeneratedAsset:
        """Download the generated 3D model"""
        pass


class ProviderManager:
    """Manages all AI providers"""
    
    def __init__(self):
        self.image_gen_providers: Dict[str, ImageGenerationProvider] = {}
        self.image_enhance_providers: Dict[str, ImageEnhancementProvider] = {}
        self.text_3d_providers: Dict[str, Text3DProvider] = {}
        self.image_3d_providers: Dict[str, Image3DProvider] = {}
    
    def register_image_gen_provider(self, name: str, provider: ImageGenerationProvider):
        """Register an image generation provider"""
        self.image_gen_providers[name] = provider
    
    def register_image_enhance_provider(self, name: str, provider: ImageEnhancementProvider):
        """Register an image enhancement provider"""
        self.image_enhance_providers[name] = provider
    
    def register_text_3d_provider(self, name: str, provider: Text3DProvider):
        """Register a text-to-3D provider"""
        self.text_3d_providers[name] = provider
    
    def register_image_3d_provider(self, name: str, provider: Image3DProvider):
        """Register an image-to-3D provider"""
        self.image_3d_providers[name] = provider
    
    def get_available_providers(self) -> Dict[str, Dict[str, list]]:
        """Get all available providers organized by capability"""
        return {
            "text_to_image": list(self.image_gen_providers.keys()),
            "image_enhance": list(self.image_enhance_providers.keys()),
            "text_to_3d": list(self.text_3d_providers.keys()),
            "image_to_3d": list(self.image_3d_providers.keys())
        }


# Global provider manager instance
provider_manager = ProviderManager()