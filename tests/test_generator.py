"""
Tests for 3D model generation
"""
import pytest
from src.backend.app.services.generator import (
    generate_cube, generate_cylinder, generate_sphere, generate_custom_box
)


class TestCubeGeneration:
    def test_cube_basic(self):
        """Test basic cube generation"""
        content, metadata = generate_cube(10.0)
        
        assert metadata["model_type"] == "cube"
        assert metadata["dimensions"]["size"] == 10.0
        assert metadata["triangles"] == 12  # Cube has 12 triangles
        assert "solid modelo3d" in content
        assert "endsolid modelo3d" in content
    
    def test_cube_different_sizes(self):
        """Test cube with different sizes"""
        for size in [0.1, 1.0, 50.0, 500.0]:
            content, metadata = generate_cube(size)
            assert metadata["dimensions"]["size"] == size
            assert len(content) > 0


class TestCylinderGeneration:
    def test_cylinder_basic(self):
        """Test basic cylinder generation"""
        content, metadata = generate_cylinder(5.0, 10.0, 20)
        
        assert metadata["model_type"] == "cylinder"
        assert metadata["dimensions"]["radius"] == 5.0
        assert metadata["dimensions"]["height"] == 10.0
        assert metadata["dimensions"]["segments"] == 20
        assert metadata["triangles"] == 80  # 20 segments * 4 triangles per segment
        assert "solid modelo3d" in content
    
    def test_cylinder_segments_clamping(self):
        """Test that segments are properly clamped"""
        # Test minimum clamping
        content, metadata = generate_cylinder(5.0, 10.0, 3)
        assert metadata["dimensions"]["segments"] == 6
        
        # Test maximum clamping  
        content, metadata = generate_cylinder(5.0, 10.0, 300)
        assert metadata["dimensions"]["segments"] == 256


class TestSphereGeneration:
    def test_sphere_basic(self):
        """Test basic sphere generation"""
        content, metadata = generate_sphere(5.0, 20)
        
        assert metadata["model_type"] == "sphere"
        assert metadata["dimensions"]["radius"] == 5.0
        assert metadata["dimensions"]["segments"] == 20
        assert metadata["triangles"] > 0
        assert "solid modelo3d" in content
    
    def test_sphere_segments_clamping(self):
        """Test that segments are properly clamped"""
        # Test minimum clamping
        content, metadata = generate_sphere(5.0, 3)
        assert metadata["dimensions"]["segments"] == 6
        
        # Test maximum clamping
        content, metadata = generate_sphere(5.0, 200)
        assert metadata["dimensions"]["segments"] == 128


class TestCustomBoxGeneration:
    def test_custom_box_basic(self):
        """Test basic custom box generation"""
        content, metadata = generate_custom_box(20.0, 15.0, 10.0, 2.0)
        
        assert metadata["model_type"] == "custom_box"
        assert metadata["dimensions"]["length"] == 20.0
        assert metadata["dimensions"]["width"] == 15.0
        assert metadata["dimensions"]["height"] == 10.0
        assert metadata["dimensions"]["wall_thickness"] == 2.0
        assert metadata["triangles"] > 0
        assert "solid modelo3d" in content


class TestSTLFormat:
    def test_stl_format_validity(self):
        """Test that generated STL follows proper format"""
        content, _ = generate_cube(10.0)
        
        lines = content.strip().split('\n')
        
        # Check header
        assert lines[0] == "solid modelo3d"
        
        # Check footer
        assert lines[-1] == "endsolid modelo3d"
        
        # Check facet structure
        facet_count = content.count("facet normal")
        endfacet_count = content.count("endfacet")
        assert facet_count == endfacet_count
        
        # Check triangle count matches metadata
        _, metadata = generate_cube(10.0)
        assert facet_count == metadata["triangles"]