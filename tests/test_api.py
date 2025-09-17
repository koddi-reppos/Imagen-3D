"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.backend.app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "generador-3d"


class TestGenerateEndpoint:
    def test_generate_cube(self):
        """Test cube generation via API"""
        payload = {
            "model_type": "cube",
            "params": {"size": 10.0}
        }
        
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "metadata" in data
        assert data["metadata"]["model_type"] == "cube"
        assert data["metadata"]["dimensions"]["size"] == 10.0
    
    def test_generate_cylinder(self):
        """Test cylinder generation via API"""
        payload = {
            "model_type": "cylinder",
            "params": {
                "radius": 5.0,
                "height": 10.0,
                "segments": 20
            }
        }
        
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["model_type"] == "cylinder"
    
    def test_generate_invalid_params(self):
        """Test generation with invalid parameters"""
        payload = {
            "model_type": "cube",
            "params": {"size": -1.0}  # Invalid negative size
        }
        
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400
    
    def test_generate_invalid_model_type(self):
        """Test generation with invalid model type"""
        payload = {
            "model_type": "invalid_type",
            "params": {"size": 10.0}
        }
        
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 422  # Pydantic validation error


class TestFilesEndpoint:
    def test_list_files(self):
        """Test file listing endpoint"""
        response = client.get("/api/files")
        assert response.status_code == 200
        
        data = response.json()
        assert "files" in data
        assert "total_count" in data
        assert isinstance(data["files"], list)
        assert isinstance(data["total_count"], int)


class TestZipEndpoint:
    def test_zip_empty_list(self):
        """Test ZIP creation with empty file list"""
        payload = {"filenames": []}
        
        response = client.post("/api/zip", json=payload)
        assert response.status_code == 422  # Validation error for empty list
    
    def test_zip_nonexistent_files(self):
        """Test ZIP creation with non-existent files"""
        payload = {"filenames": ["nonexistent.stl"]}
        
        response = client.post("/api/zip", json=payload)
        assert response.status_code == 400


class TestValidation:
    def test_cube_size_validation(self):
        """Test cube size parameter validation"""
        # Test minimum size
        payload = {
            "model_type": "cube",
            "params": {"size": 0.05}  # Below minimum
        }
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400
        
        # Test maximum size
        payload = {
            "model_type": "cube", 
            "params": {"size": 600.0}  # Above maximum
        }
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400
    
    def test_cylinder_segments_validation(self):
        """Test cylinder segments validation"""
        # Test minimum segments
        payload = {
            "model_type": "cylinder",
            "params": {
                "radius": 5.0,
                "height": 10.0,
                "segments": 3  # Below minimum
            }
        }
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400
    
    def test_custom_box_wall_thickness_validation(self):
        """Test custom box wall thickness validation"""
        payload = {
            "model_type": "custom_box",
            "params": {
                "length": 10.0,
                "width": 10.0,
                "height": 10.0,
                "wall_thickness": 6.0  # Too thick for box size
            }
        }
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 400