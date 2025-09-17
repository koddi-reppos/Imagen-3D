"""
3D Model geometry generation
"""
import numpy as np
from typing import List, Tuple, Dict, Any
from .stl import generate_stl_content


def generate_cube(size: float) -> Tuple[str, Dict[str, Any]]:
    """Generate cube STL content and metadata"""
    vertices = [
        [0, 0, 0], [size, 0, 0], [size, size, 0], [0, size, 0],  # Base inferior
        [0, 0, size], [size, 0, size], [size, size, size], [0, size, size]  # Base superior
    ]
    
    # Define cube faces (12 triangles)
    faces = [
        # Base inferior
        [0, 1, 2], [0, 2, 3],
        # Base superior
        [4, 6, 5], [4, 7, 6],
        # Lado frontal
        [0, 4, 5], [0, 5, 1],
        # Lado trasero
        [2, 6, 7], [2, 7, 3],
        # Lado izquierdo
        [0, 3, 7], [0, 7, 4],
        # Lado derecho
        [1, 5, 6], [1, 6, 2]
    ]
    
    triangles = []
    for face in faces:
        v1, v2, v3 = [vertices[i] for i in face]
        triangles.append((v1, v2, v3))
    
    stl_content = generate_stl_content(triangles)
    filename = f"cubo_{size}mm.stl"
    
    metadata = {
        "filename": filename,
        "model_type": "cube",
        "dimensions": {"size": size},
        "triangles": len(triangles)
    }
    
    return stl_content, metadata


def generate_cylinder(radius: float, height: float, segments: int = 20) -> Tuple[str, Dict[str, Any]]:
    """Generate cylinder STL content and metadata"""
    # Clamp segments for performance
    segments = max(6, min(segments, 256))
    
    angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
    
    # Generate vertices
    base_inferior = [[radius * np.cos(angle), radius * np.sin(angle), 0] for angle in angles]
    centro_inferior = [0, 0, 0]
    
    base_superior = [[radius * np.cos(angle), radius * np.sin(angle), height] for angle in angles]
    centro_superior = [0, 0, height]
    
    triangles = []
    
    # Base inferior (triangles from center)
    for i in range(segments):
        next_i = (i + 1) % segments
        triangles.append((centro_inferior, base_inferior[next_i], base_inferior[i]))
    
    # Base superior (triangles from center)
    for i in range(segments):
        next_i = (i + 1) % segments
        triangles.append((centro_superior, base_superior[i], base_superior[next_i]))
    
    # Cylinder sides
    for i in range(segments):
        next_i = (i + 1) % segments
        # Triangle 1
        triangles.append((base_inferior[i], base_superior[i], base_inferior[next_i]))
        # Triangle 2
        triangles.append((base_inferior[next_i], base_superior[i], base_superior[next_i]))
    
    stl_content = generate_stl_content(triangles)
    filename = f"cilindro_r{radius}_h{height}.stl"
    
    metadata = {
        "filename": filename,
        "model_type": "cylinder",
        "dimensions": {"radius": radius, "height": height, "segments": segments},
        "triangles": len(triangles)
    }
    
    return stl_content, metadata


def generate_sphere(radius: float, segments: int = 20) -> Tuple[str, Dict[str, Any]]:
    """Generate sphere STL content and metadata"""
    # Clamp segments for performance
    segments = max(6, min(segments, 128))
    
    vertices = []
    
    # Generate vertices using spherical coordinates
    for i in range(segments + 1):
        lat = np.pi * i / segments - np.pi/2  # -π/2 to π/2
        for j in range(segments):
            lon = 2 * np.pi * j / segments  # 0 to 2π
            
            x = radius * np.cos(lat) * np.cos(lon)
            y = radius * np.cos(lat) * np.sin(lon)
            z = radius * np.sin(lat)
            vertices.append([x, y, z])
    
    triangles = []
    
    # Generate triangles
    for i in range(segments):
        for j in range(segments):
            # Vertex indices
            current = i * segments + j
            next_lat = (i + 1) * segments + j
            next_lon = i * segments + (j + 1) % segments
            next_both = (i + 1) * segments + (j + 1) % segments
            
            if i < segments:  # Don't generate triangles in the last ring
                # Triangle 1
                triangles.append((vertices[current], vertices[next_lat], vertices[next_lon]))
                # Triangle 2
                triangles.append((vertices[next_lon], vertices[next_lat], vertices[next_both]))
    
    stl_content = generate_stl_content(triangles)
    filename = f"esfera_r{radius}.stl"
    
    metadata = {
        "filename": filename,
        "model_type": "sphere",
        "dimensions": {"radius": radius, "segments": segments},
        "triangles": len(triangles)
    }
    
    return stl_content, metadata


def generate_custom_box(length: float, width: float, height: float, wall_thickness: float) -> Tuple[str, Dict[str, Any]]:
    """Generate custom hollow box STL content and metadata"""
    t = wall_thickness
    
    # External vertices
    ext_vertices = [
        [0, 0, 0], [length, 0, 0], [length, width, 0], [0, width, 0],  # External base
        [0, 0, height], [length, 0, height], [length, width, height], [0, width, height]  # External top
    ]
    
    # Internal vertices (hollow part)
    int_vertices = [
        [t, t, t], [length-t, t, t], [length-t, width-t, t], [t, width-t, t],  # Internal base
        [t, t, height], [length-t, t, height], [length-t, width-t, height], [t, width-t, height]  # Internal top
    ]
    
    triangles = []
    
    # External faces
    ext_faces = [
        # Base
        [0, 1, 2], [0, 2, 3],
        # Sides
        [0, 4, 5], [0, 5, 1],  # Front
        [1, 5, 6], [1, 6, 2],  # Right
        [2, 6, 7], [2, 7, 3],  # Back
        [3, 7, 4], [3, 4, 0],  # Left
        # No top for open box
    ]
    
    for face in ext_faces:
        v1, v2, v3 = [ext_vertices[i] for i in face]
        triangles.append((v1, v2, v3))
    
    # Internal faces (inverted normals)
    int_faces = [
        # Internal base (inverted)
        [0, 2, 1], [0, 3, 2],
        # Internal sides (inverted)
        [0, 5, 4], [0, 1, 5],  # Front
        [1, 6, 5], [1, 2, 6],  # Right
        [2, 7, 6], [2, 3, 7],  # Back
        [3, 4, 7], [3, 0, 4],  # Left
    ]
    
    for face in int_faces:
        v1, v2, v3 = [int_vertices[i] for i in face]
        triangles.append((v1, v2, v3))
    
    # Connect walls (between external and internal)
    # Front wall
    triangles.append((ext_vertices[0], int_vertices[0], ext_vertices[4]))
    triangles.append((int_vertices[0], int_vertices[4], ext_vertices[4]))
    triangles.append((ext_vertices[1], ext_vertices[5], int_vertices[1]))
    triangles.append((int_vertices[1], ext_vertices[5], int_vertices[5]))
    
    stl_content = generate_stl_content(triangles)
    filename = f"caja_{length}x{width}x{height}.stl"
    
    metadata = {
        "filename": filename,
        "model_type": "custom_box",
        "dimensions": {"length": length, "width": width, "height": height, "wall_thickness": wall_thickness},
        "triangles": len(triangles)
    }
    
    return stl_content, metadata