#!/usr/bin/env python3
"""
Generador de Maquetas 3D para Impresión
Crea archivos STL listos para imprimir
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

def create_stl_header():
    """Crear header STL"""
    return "solid modelo3d\n"

def create_stl_footer():
    """Crear footer STL"""
    return "endsolid modelo3d\n"

def write_triangle_to_stl(file, v1, v2, v3):
    """Escribir un triángulo al archivo STL"""
    # Calcular normal
    edge1 = np.array(v2) - np.array(v1)
    edge2 = np.array(v3) - np.array(v1)
    normal = np.cross(edge1, edge2)
    normal = normal / np.linalg.norm(normal)
    
    file.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
    file.write("    outer loop\n")
    file.write(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}\n")
    file.write(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
    file.write(f"      vertex {v3[0]:.6f} {v3[1]:.6f} {v3[2]:.6f}\n")
    file.write("    endloop\n")
    file.write("  endfacet\n")

def create_cube(size=10.0):
    """Crear un cubo STL"""
    filename = f"cubo_{size}mm.stl"
    
    with open(filename, 'w') as f:
        f.write(create_stl_header())
        
        # Definir vértices del cubo
        vertices = [
            [0, 0, 0], [size, 0, 0], [size, size, 0], [0, size, 0],  # Base inferior
            [0, 0, size], [size, 0, size], [size, size, size], [0, size, size]  # Base superior
        ]
        
        # Definir caras del cubo (12 triángulos)
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
        
        for face in faces:
            v1, v2, v3 = [vertices[i] for i in face]
            write_triangle_to_stl(f, v1, v2, v3)
        
        f.write(create_stl_footer())
    
    return filename

def create_cylinder(radius=5.0, height=10.0, segments=20):
    """Crear un cilindro STL"""
    filename = f"cilindro_r{radius}_h{height}.stl"
    
    with open(filename, 'w') as f:
        f.write(create_stl_header())
        
        # Generar puntos del círculo
        angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
        
        # Vértices base inferior
        base_inferior = [[radius * np.cos(angle), radius * np.sin(angle), 0] for angle in angles]
        centro_inferior = [0, 0, 0]
        
        # Vértices base superior
        base_superior = [[radius * np.cos(angle), radius * np.sin(angle), height] for angle in angles]
        centro_superior = [0, 0, height]
        
        # Base inferior (triángulos desde el centro)
        for i in range(segments):
            next_i = (i + 1) % segments
            write_triangle_to_stl(f, centro_inferior, base_inferior[next_i], base_inferior[i])
        
        # Base superior (triángulos desde el centro)
        for i in range(segments):
            next_i = (i + 1) % segments
            write_triangle_to_stl(f, centro_superior, base_superior[i], base_superior[next_i])
        
        # Lados del cilindro
        for i in range(segments):
            next_i = (i + 1) % segments
            # Triángulo 1
            write_triangle_to_stl(f, base_inferior[i], base_superior[i], base_inferior[next_i])
            # Triángulo 2
            write_triangle_to_stl(f, base_inferior[next_i], base_superior[i], base_superior[next_i])
        
        f.write(create_stl_footer())
    
    return filename

def create_sphere(radius=5.0, segments=20):
    """Crear una esfera STL"""
    filename = f"esfera_r{radius}.stl"
    
    with open(filename, 'w') as f:
        f.write(create_stl_header())
        
        # Generar puntos de la esfera usando coordenadas esféricas
        vertices = []
        
        # Generar vértices
        for i in range(segments + 1):
            lat = np.pi * i / segments - np.pi/2  # -π/2 a π/2
            for j in range(segments):
                lon = 2 * np.pi * j / segments  # 0 a 2π
                
                x = radius * np.cos(lat) * np.cos(lon)
                y = radius * np.cos(lat) * np.sin(lon)
                z = radius * np.sin(lat)
                vertices.append([x, y, z])
        
        # Generar triángulos
        for i in range(segments):
            for j in range(segments):
                # Índices de los vértices
                current = i * segments + j
                next_lat = (i + 1) * segments + j
                next_lon = i * segments + (j + 1) % segments
                next_both = (i + 1) * segments + (j + 1) % segments
                
                if i < segments:  # No generar triángulos en el último anillo
                    # Triángulo 1
                    write_triangle_to_stl(f, vertices[current], vertices[next_lat], vertices[next_lon])
                    # Triángulo 2
                    write_triangle_to_stl(f, vertices[next_lon], vertices[next_lat], vertices[next_both])
        
        f.write(create_stl_footer())
    
    return filename

def create_custom_box(length=20.0, width=15.0, height=10.0, wall_thickness=2.0):
    """Crear una caja personalizada con paredes"""
    filename = f"caja_{length}x{width}x{height}.stl"
    
    with open(filename, 'w') as f:
        f.write(create_stl_header())
        
        # Crear caja exterior
        ext_vertices = [
            [0, 0, 0], [length, 0, 0], [length, width, 0], [0, width, 0],  # Base exterior
            [0, 0, height], [length, 0, height], [length, width, height], [0, width, height]  # Tapa exterior
        ]
        
        # Crear caja interior (hueca)
        t = wall_thickness
        int_vertices = [
            [t, t, t], [length-t, t, t], [length-t, width-t, t], [t, width-t, t],  # Base interior
            [t, t, height], [length-t, t, height], [length-t, width-t, height], [t, width-t, height]  # Tapa interior
        ]
        
        # Caras exteriores
        ext_faces = [
            # Base
            [0, 1, 2], [0, 2, 3],
            # Lados
            [0, 4, 5], [0, 5, 1],  # Frontal
            [1, 5, 6], [1, 6, 2],  # Derecho
            [2, 6, 7], [2, 7, 3],  # Trasero
            [3, 7, 4], [3, 4, 0],  # Izquierdo
            # No agregamos tapa superior para que sea una caja abierta
        ]
        
        # Escribir caras exteriores
        for face in ext_faces:
            v1, v2, v3 = [ext_vertices[i] for i in face]
            write_triangle_to_stl(f, v1, v2, v3)
        
        # Caras interiores (invertidas para que las normales apunten hacia afuera)
        int_faces = [
            # Base interior (invertida)
            [0, 2, 1], [0, 3, 2],
            # Lados interiores (invertidos)
            [0, 5, 4], [0, 1, 5],  # Frontal
            [1, 6, 5], [1, 2, 6],  # Derecho
            [2, 7, 6], [2, 3, 7],  # Trasero
            [3, 4, 7], [3, 0, 4],  # Izquierdo
        ]
        
        # Escribir caras interiores
        for face in int_faces:
            v1, v2, v3 = [int_vertices[i] for i in face]
            write_triangle_to_stl(f, v1, v2, v3)
        
        # Conectar paredes (entre exterior e interior)
        # Pared frontal
        write_triangle_to_stl(f, ext_vertices[0], int_vertices[0], ext_vertices[4])
        write_triangle_to_stl(f, int_vertices[0], int_vertices[4], ext_vertices[4])
        write_triangle_to_stl(f, ext_vertices[1], ext_vertices[5], int_vertices[1])
        write_triangle_to_stl(f, int_vertices[1], ext_vertices[5], int_vertices[5])
        
        f.write(create_stl_footer())
    
    return filename

def visualize_model(model_type="cube", **kwargs):
    """Visualizar modelo 3D antes de imprimir"""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    if model_type == "cube":
        size = kwargs.get('size', 10)
        # Dibujar cubo
        vertices = np.array([
            [0, 0, 0], [size, 0, 0], [size, size, 0], [0, size, 0],
            [0, 0, size], [size, 0, size], [size, size, size], [0, size, size]
        ])
        
        # Dibujar aristas
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Base inferior
            [4, 5], [5, 6], [6, 7], [7, 4],  # Base superior
            [0, 4], [1, 5], [2, 6], [3, 7]   # Aristas verticales
        ]
        
        for edge in edges:
            points = vertices[edge]
            ax.plot3D(*points.T, 'b-', linewidth=2)
        
        ax.scatter(*vertices.T, color='red', s=50)
        ax.set_title(f'Cubo {size}x{size}x{size} mm')
    
    elif model_type == "cylinder":
        radius = kwargs.get('radius', 5)
        height = kwargs.get('height', 10)
        segments = kwargs.get('segments', 20)
        
        # Generar cilindro para visualización
        theta = np.linspace(0, 2*np.pi, segments)
        z_base = np.zeros_like(theta)
        z_top = np.full_like(theta, height)
        
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        # Dibujar círculos base
        ax.plot(x, y, z_base, 'b-', linewidth=2)
        ax.plot(x, y, z_top, 'b-', linewidth=2)
        
        # Dibujar líneas verticales
        for i in range(0, segments, segments//8):
            ax.plot([x[i], x[i]], [y[i], y[i]], [0, height], 'b-', linewidth=1)
        
        ax.set_title(f'Cilindro R={radius}mm H={height}mm')
    
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_box_aspect([1,1,1])
    
    plt.tight_layout()
    plt.savefig('preview_3d.png', dpi=150, bbox_inches='tight')
    plt.show()

def main():
    print("🔧 GENERADOR DE MAQUETAS 3D PARA IMPRESIÓN 🔧")
    print("=" * 50)
    
    while True:
        print("\n📋 MODELOS DISPONIBLES:")
        print("1. Cubo básico")
        print("2. Cilindro")
        print("3. Esfera")
        print("4. Caja personalizada (hueca)")
        print("5. Visualizar modelo")
        print("6. Listar archivos STL generados")
        print("0. Salir")
        
        try:
            opcion = input("\n➤ Selecciona una opción (0-6): ").strip()
            
            if opcion == "0":
                print("👋 ¡Hasta luego!")
                break
            
            elif opcion == "1":
                size = float(input("📏 Tamaño del cubo en mm (default: 10): ") or 10)
                filename = create_cube(size)
                visualize_model("cube", size=size)
                print(f"✅ Cubo creado: {filename}")
                print(f"📐 Dimensiones: {size}x{size}x{size} mm")
            
            elif opcion == "2":
                radius = float(input("📏 Radio en mm (default: 5): ") or 5)
                height = float(input("📏 Altura en mm (default: 10): ") or 10)
                segments = int(input("🔧 Resolución (segmentos, default: 20): ") or 20)
                filename = create_cylinder(radius, height, segments)
                visualize_model("cylinder", radius=radius, height=height, segments=segments)
                print(f"✅ Cilindro creado: {filename}")
                print(f"📐 Dimensiones: R={radius}mm, H={height}mm")
            
            elif opcion == "3":
                radius = float(input("📏 Radio en mm (default: 5): ") or 5)
                segments = int(input("🔧 Resolución (segmentos, default: 20): ") or 20)
                filename = create_sphere(radius, segments)
                print(f"✅ Esfera creada: {filename}")
                print(f"📐 Dimensiones: R={radius}mm")
            
            elif opcion == "4":
                length = float(input("📏 Largo en mm (default: 20): ") or 20)
                width = float(input("📏 Ancho en mm (default: 15): ") or 15)
                height = float(input("📏 Alto en mm (default: 10): ") or 10)
                thickness = float(input("📏 Grosor de pared en mm (default: 2): ") or 2)
                filename = create_custom_box(length, width, height, thickness)
                print(f"✅ Caja creada: {filename}")
                print(f"📐 Dimensiones: {length}x{width}x{height} mm")
                print(f"🧱 Grosor de pared: {thickness} mm")
            
            elif opcion == "5":
                model_type = input("Tipo de modelo para visualizar (cube/cylinder): ").strip().lower()
                if model_type == "cube":
                    size = float(input("Tamaño: ") or 10)
                    visualize_model("cube", size=size)
                elif model_type == "cylinder":
                    radius = float(input("Radio: ") or 5)
                    height = float(input("Altura: ") or 10)
                    visualize_model("cylinder", radius=radius, height=height)
            
            elif opcion == "6":
                stl_files = [f for f in os.listdir('.') if f.endswith('.stl')]
                if stl_files:
                    print("\n📁 ARCHIVOS STL GENERADOS:")
                    for i, file in enumerate(stl_files, 1):
                        size = os.path.getsize(file)
                        print(f"{i}. {file} ({size} bytes)")
                else:
                    print("📂 No hay archivos STL generados aún")
            
            else:
                print("❌ Opción inválida. Por favor selecciona 0-6.")
        
        except ValueError:
            print("❌ Error: Ingresa valores numéricos válidos")
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()