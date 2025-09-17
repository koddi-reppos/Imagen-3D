"""
STL file generation utilities
"""
import numpy as np
from typing import List, Tuple
from io import StringIO


def create_stl_header() -> str:
    """Create STL file header"""
    return "solid modelo3d\n"


def create_stl_footer() -> str:
    """Create STL file footer"""
    return "endsolid modelo3d\n"


def calculate_normal(v1: List[float], v2: List[float], v3: List[float]) -> np.ndarray:
    """Calculate triangle normal vector"""
    edge1 = np.array(v2) - np.array(v1)
    edge2 = np.array(v3) - np.array(v1)
    normal = np.cross(edge1, edge2)
    norm = np.linalg.norm(normal)
    if norm > 0:
        normal = normal / norm
    return normal


def write_triangle_to_buffer(buffer: StringIO, v1: List[float], v2: List[float], v3: List[float]) -> None:
    """Write a triangle to STL buffer"""
    normal = calculate_normal(v1, v2, v3)
    
    buffer.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
    buffer.write("    outer loop\n")
    buffer.write(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}\n")
    buffer.write(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
    buffer.write(f"      vertex {v3[0]:.6f} {v3[1]:.6f} {v3[2]:.6f}\n")
    buffer.write("    endloop\n")
    buffer.write("  endfacet\n")


def generate_stl_content(triangles: List[Tuple[List[float], List[float], List[float]]]) -> str:
    """Generate complete STL file content from triangles"""
    buffer = StringIO()
    buffer.write(create_stl_header())
    
    for v1, v2, v3 in triangles:
        write_triangle_to_buffer(buffer, v1, v2, v3)
    
    buffer.write(create_stl_footer())
    return buffer.getvalue()