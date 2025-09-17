"""
File storage and management service
"""
import os
import json
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models.schemas import FileMetadata


class StorageService:
    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.export_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load file index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_index(self) -> None:
        """Save file index to disk"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except IOError:
            pass
    
    def _generate_filename(self, base_filename: str) -> str:
        """Generate unique filename with timestamp if needed"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_filename)
        # Sanitize filename
        name = "".join(c for c in name if c.isalnum() or c in "._-")
        unique_filename = f"{name}_{timestamp}{ext}"
        return unique_filename
    
    def save_file(self, content: str, metadata: Dict[str, Any]) -> FileMetadata:
        """Save STL file and update index"""
        base_filename = metadata["filename"]
        unique_filename = self._generate_filename(base_filename)
        file_path = self.export_dir / unique_filename
        
        # Write STL content
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Get file size
        size_bytes = file_path.stat().st_size
        created_at = datetime.now().isoformat()
        
        # Create file metadata
        file_metadata = FileMetadata(
            filename=unique_filename,
            model_type=metadata["model_type"],
            dimensions=metadata["dimensions"],
            triangles=metadata["triangles"],
            size_bytes=size_bytes,
            created_at=created_at
        )
        
        # Update index
        self.index[unique_filename] = file_metadata.dict()
        self._save_index()
        
        return file_metadata
    
    def get_file_path(self, filename: str) -> Optional[Path]:
        """Get file path if it exists"""
        file_path = self.export_dir / filename
        if file_path.exists() and filename in self.index:
            return file_path
        return None
    
    def list_files(self) -> List[FileMetadata]:
        """List all generated files"""
        files = []
        for filename, metadata in self.index.items():
            file_path = self.export_dir / filename
            if file_path.exists():
                files.append(FileMetadata(**metadata))
            else:
                # Remove from index if file doesn't exist
                del self.index[filename]
                self._save_index()
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x.created_at, reverse=True)
        return files
    
    def create_zip(self, filenames: List[str]) -> Optional[Path]:
        """Create ZIP file with selected STL files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"models_3d_{timestamp}.zip"
        zip_path = self.export_dir / zip_filename
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in filenames:
                    file_path = self.get_file_path(filename)
                    if file_path:
                        zipf.write(file_path, filename)
                    else:
                        return None  # File not found
            
            return zip_path
        except Exception:
            return None
    
    def cleanup_old_files(self, max_files: int = 100) -> None:
        """Keep only the newest N files"""
        files = self.list_files()
        if len(files) > max_files:
            files_to_remove = files[max_files:]
            for file_metadata in files_to_remove:
                file_path = self.export_dir / file_metadata.filename
                if file_path.exists():
                    file_path.unlink()
                if file_metadata.filename in self.index:
                    del self.index[file_metadata.filename]
            self._save_index()


# Global storage instance
storage = StorageService()