"""
OpenAI provider for image generation using DALL-E
"""
import os
import uuid
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from openai import OpenAI

from .base import ImageGenerationProvider, ProviderTask, TaskStatus, GeneratedAsset


class OpenAIImageProvider(ImageGenerationProvider):
    """OpenAI DALL-E image generation provider"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tasks: Dict[str, ProviderTask] = {}
    
    async def create_task(self, prompt: str, **kwargs) -> ProviderTask:
        """Create a DALL-E image generation task"""
        
        # DALL-E parameters
        model = kwargs.get("model", "dall-e-3")
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")
        style = kwargs.get("style", "vivid")
        
        task_id = str(uuid.uuid4())
        
        try:
            # DALL-E is synchronous but fast, so we'll simulate async
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    n=1
                )
            )
            
            image_url = response.data[0].url
            revised_prompt = getattr(response.data[0], 'revised_prompt', prompt)
            
            task = ProviderTask(
                id=task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                result_url=image_url,
                metadata={
                    "model": model,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "original_prompt": prompt,
                    "revised_prompt": revised_prompt
                },
                estimated_duration=10  # DALL-E is usually fast
            )
            
        except Exception as e:
            task = ProviderTask(
                id=task_id,
                status=TaskStatus.FAILED,
                progress=0,
                error_message=str(e)
            )
        
        self.tasks[task_id] = task
        return task
    
    async def get_task_status(self, task_id: str) -> ProviderTask:
        """Get task status (DALL-E completes immediately)"""
        return self.tasks.get(task_id)
    
    async def download_result(self, task: ProviderTask) -> GeneratedAsset:
        """Download the generated image from OpenAI"""
        if not task.result_url:
            raise ValueError("No result URL available")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(task.result_url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download image: {response.status}")
                
                image_data = await response.read()
                
                # Determine filename based on metadata
                size = task.metadata.get("size", "1024x1024") if task.metadata else "1024x1024"
                filename = f"dalle_{task.id}_{size}.png"
                
                return GeneratedAsset(
                    data=image_data,
                    content_type="image/png",
                    filename=filename,
                    metadata={
                        "provider": "openai",
                        "model": task.metadata.get("model") if task.metadata else "dall-e-3",
                        "original_prompt": task.metadata.get("original_prompt") if task.metadata else "",
                        "revised_prompt": task.metadata.get("revised_prompt") if task.metadata else ""
                    }
                )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task (not applicable for DALL-E since it's immediate)"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False
    
    def is_available(self) -> bool:
        """Check if OpenAI API key is available"""
        return bool(os.getenv("OPENAI_API_KEY"))