"""
Job management system for async AI operations
"""
import json
import asyncio
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from pathlib import Path

from ..database.database import get_database
from ..database.models import Job, Asset, JobType, JobStatus, AssetKind
from .providers.base import provider_manager, ProviderTask, TaskStatus


class JobManager:
    """Manages AI jobs and asset storage"""
    
    def __init__(self):
        self.database = get_database()
        self.storage_path = Path("./data/assets")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different asset types
        (self.storage_path / "images").mkdir(exist_ok=True)
        (self.storage_path / "meshes").mkdir(exist_ok=True)
        (self.storage_path / "zips").mkdir(exist_ok=True)
        (self.storage_path / "previews").mkdir(exist_ok=True)
    
    async def create_job(
        self, 
        job_type: JobType, 
        params: Dict[str, Any], 
        provider: str = None
    ) -> str:
        """Create a new job"""
        
        job_id = await self.database.execute(
            """
            INSERT INTO jobs (type, params, provider, status, created_at)
            VALUES (:type, :params, :provider, :status, :created_at)
            """,
            {
                "type": job_type.value,
                "params": json.dumps(params),
                "provider": provider,
                "status": JobStatus.PENDING.value,
                "created_at": datetime.utcnow()
            }
        )
        
        # Start processing the job asynchronously
        asyncio.create_task(self._process_job(str(job_id)))
        
        return str(job_id)
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details"""
        query = """
            SELECT j.*, a.filename, a.file_path, a.size_bytes, a.mime_type
            FROM jobs j
            LEFT JOIN assets a ON j.asset_id = a.id
            WHERE j.id = :job_id
        """
        
        result = await self.database.fetch_one(query, {"job_id": job_id})
        
        if result:
            job_data = dict(result)
            if job_data["params"]:
                job_data["params"] = json.loads(job_data["params"])
            if job_data["output_metadata"]:
                job_data["output_metadata"] = json.loads(job_data["output_metadata"])
            return job_data
        
        return None
    
    async def list_jobs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List recent jobs"""
        query = """
            SELECT j.*, a.filename, a.size_bytes
            FROM jobs j
            LEFT JOIN assets a ON j.asset_id = a.id
            ORDER BY j.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        results = await self.database.fetch_all(query, {"limit": limit, "offset": offset})
        
        jobs = []
        for result in results:
            job_data = dict(result)
            if job_data["params"]:
                job_data["params"] = json.loads(job_data["params"])
            jobs.append(job_data)
        
        return jobs
    
    async def save_asset(
        self, 
        data: bytes, 
        filename: str, 
        kind: AssetKind, 
        mime_type: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Save an asset to storage and database"""
        
        # Generate checksum
        checksum = hashlib.sha256(data).hexdigest()
        
        # Determine storage path
        subdir = {
            AssetKind.IMAGE: "images",
            AssetKind.MESH: "meshes", 
            AssetKind.ZIP: "zips",
            AssetKind.PREVIEW: "previews"
        }[kind]
        
        # Safe filename
        safe_filename = self._safe_filename(filename)
        file_path = self.storage_path / subdir / safe_filename
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(data)
        
        # Save to database
        asset_id = await self.database.execute(
            """
            INSERT INTO assets (kind, filename, file_path, mime_type, size_bytes, checksum, metadata, created_at)
            VALUES (:kind, :filename, :file_path, :mime_type, :size_bytes, :checksum, :metadata, :created_at)
            """,
            {
                "kind": kind.value,
                "filename": safe_filename,
                "file_path": str(file_path),
                "mime_type": mime_type,
                "size_bytes": len(data),
                "checksum": checksum,
                "metadata": json.dumps(metadata) if metadata else None,
                "created_at": datetime.utcnow()
            }
        )
        
        return str(asset_id)
    
    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset details"""
        query = "SELECT * FROM assets WHERE id = :asset_id"
        result = await self.database.fetch_one(query, {"asset_id": asset_id})
        
        if result:
            asset_data = dict(result)
            if asset_data["metadata"]:
                asset_data["metadata"] = json.loads(asset_data["metadata"])
            return asset_data
        
        return None
    
    async def list_assets(self, kind: AssetKind = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List assets"""
        if kind:
            query = "SELECT * FROM assets WHERE kind = :kind ORDER BY created_at DESC LIMIT :limit"
            results = await self.database.fetch_all(query, {"kind": kind.value, "limit": limit})
        else:
            query = "SELECT * FROM assets ORDER BY created_at DESC LIMIT :limit"
            results = await self.database.fetch_all(query, {"limit": limit})
        
        assets = []
        for result in results:
            asset_data = dict(result)
            if asset_data["metadata"]:
                asset_data["metadata"] = json.loads(asset_data["metadata"])
            assets.append(asset_data)
        
        return assets
    
    async def _process_job(self, job_id: str):
        """Process a job asynchronously"""
        try:
            await self._update_job_status(job_id, JobStatus.PROCESSING)
            
            job = await self.get_job(job_id)
            if not job:
                return
            
            job_type = JobType(job["type"])
            params = job["params"]
            provider_name = job["provider"]
            
            # Route to appropriate processor
            if job_type == JobType.TEXT_TO_IMAGE:
                await self._process_text_to_image(job_id, params, provider_name)
            elif job_type == JobType.TEXT_TO_3D:
                await self._process_text_to_3d(job_id, params, provider_name)
            elif job_type == JobType.IMAGE_TO_3D:
                await self._process_image_to_3d(job_id, params, provider_name)
            elif job_type == JobType.IMAGE_ENHANCE:
                await self._process_image_enhance(job_id, params, provider_name)
            
        except Exception as e:
            await self._update_job_error(job_id, str(e))
    
    async def _process_text_to_image(self, job_id: str, params: Dict[str, Any], provider_name: str):
        """Process text-to-image job"""
        provider = provider_manager.image_gen_providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not available")
        
        # Create task with provider
        task = await provider.create_task(params["prompt"], **params.get("options", {}))
        
        # Store external task ID
        await self._update_job_external_id(job_id, task.id)
        
        # Poll for completion
        while task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            await asyncio.sleep(5)  # Poll every 5 seconds
            task = await provider.get_task_status(task.id)
            await self._update_job_progress(job_id, task.progress)
        
        if task.status == TaskStatus.COMPLETED:
            # Download result
            asset = await provider.download_result(task)
            
            # Save asset
            asset_id = await self.save_asset(
                asset.data,
                asset.filename,
                AssetKind.IMAGE,
                asset.content_type,
                asset.metadata
            )
            
            # Update job
            await self._update_job_success(job_id, asset_id, task.metadata)
        
        elif task.status == TaskStatus.FAILED:
            await self._update_job_error(job_id, task.error_message or "Generation failed")
    
    async def _process_text_to_3d(self, job_id: str, params: Dict[str, Any], provider_name: str):
        """Process text-to-3D job"""
        # Similar to text_to_image but for 3D providers
        provider = provider_manager.text_3d_providers.get(provider_name)
        if not provider:
            raise ValueError(f"3D Provider {provider_name} not available")
        
        # Implementation similar to text_to_image
        # This would use the existing Meshy AI integration
        pass
    
    async def _process_image_to_3d(self, job_id: str, params: Dict[str, Any], provider_name: str):
        """Process image-to-3D job"""
        # Implementation for image-to-3D conversion
        pass
    
    async def _process_image_enhance(self, job_id: str, params: Dict[str, Any], provider_name: str):
        """Process image enhancement job"""
        # Implementation for image enhancement
        pass
    
    async def _update_job_status(self, job_id: str, status: JobStatus):
        """Update job status"""
        await self.database.execute(
            "UPDATE jobs SET status = :status WHERE id = :job_id",
            {"status": status.value, "job_id": job_id}
        )
    
    async def _update_job_progress(self, job_id: str, progress: int):
        """Update job progress"""
        await self.database.execute(
            "UPDATE jobs SET progress_percent = :progress WHERE id = :job_id",
            {"progress": progress, "job_id": job_id}
        )
    
    async def _update_job_external_id(self, job_id: str, external_id: str):
        """Update external job ID"""
        await self.database.execute(
            "UPDATE jobs SET external_job_id = :external_id WHERE id = :job_id",
            {"external_id": external_id, "job_id": job_id}
        )
    
    async def _update_job_success(self, job_id: str, asset_id: str, metadata: Dict[str, Any] = None):
        """Mark job as successful"""
        await self.database.execute(
            """
            UPDATE jobs SET 
                status = :status, 
                asset_id = :asset_id, 
                output_metadata = :metadata,
                completed_at = :completed_at,
                progress_percent = 100
            WHERE id = :job_id
            """,
            {
                "status": JobStatus.COMPLETED.value,
                "asset_id": asset_id,
                "metadata": json.dumps(metadata) if metadata else None,
                "completed_at": datetime.utcnow(),
                "job_id": job_id
            }
        )
    
    async def _update_job_error(self, job_id: str, error_message: str):
        """Mark job as failed"""
        await self.database.execute(
            """
            UPDATE jobs SET 
                status = :status, 
                error_message = :error_message,
                completed_at = :completed_at
            WHERE id = :job_id
            """,
            {
                "status": JobStatus.FAILED.value,
                "error_message": error_message,
                "completed_at": datetime.utcnow(),
                "job_id": job_id
            }
        )
    
    def _safe_filename(self, filename: str) -> str:
        """Generate safe filename"""
        import re
        import uuid
        
        # Remove dangerous characters
        safe = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Add UUID prefix to avoid collisions
        name, ext = os.path.splitext(safe)
        return f"{uuid.uuid4().hex[:8]}_{name}{ext}"


# Global job manager instance
job_manager = JobManager()