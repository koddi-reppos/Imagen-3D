# 🔧 Generador 3D - Modelos STL para Impresión

Una aplicación web completa para generar modelos 3D listos para impresión. Crea cubos, cilindros, esferas y cajas personalizadas con parámetros ajustables y descárga archivos STL de alta calidad.

## ✨ Características

- **🎯 Interfaz Web Moderna**: Diseño responsive con vista previa 3D en tiempo real
- **📐 Múltiples Geometrías**: Cubos, cilindros, esferas y cajas huecas personalizables
- **🔧 Parámetros Precisos**: Control total sobre dimensiones y resolución
- **📁 Gestión de Archivos**: Lista, descarga individual o en ZIP de múltiples modelos
- **⚡ API REST Robusta**: Backend FastAPI con validación de datos
- **🌐 Listo para Producción**: Configuración completa para deployment

## 🚀 Inicio Rápido

### Instalación Local

```bash
# Clonar repositorio
git clone <repository-url>
cd generador-3d

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
uvicorn src.backend.app.main:app --host 0.0.0.0 --port 5000 --reload
```

### Con Docker

```bash
# Construir imagen
docker build -t generador-3d .

# Ejecutar contenedor
docker run -p 5000:5000 generador-3d
```

## 📖 Uso

1. **Selecciona el tipo de modelo** (cubo, cilindro, esfera, caja)
2. **Ajusta los parámetros** según tus necesidades
3. **Vista previa 3D** para verificar el diseño
4. **Genera el modelo** y obtén el archivo STL
5. **Descarga individual** o **crea ZIP** con múltiples modelos

### Tipos de Modelos Disponibles

#### 🟦 Cubo
- **Tamaño**: 0.1 - 500 mm

#### ⚪ Cilindro
- **Radio**: 0.1 - 250 mm
- **Altura**: 0.1 - 500 mm
- **Segmentos**: 6 - 256 (resolución)

#### 🔵 Esfera
- **Radio**: 0.1 - 250 mm
- **Segmentos**: 6 - 128 (resolución)

#### 📦 Caja Personalizada (Hueca)
- **Largo**: 1 - 500 mm
- **Ancho**: 1 - 500 mm
- **Alto**: 1 - 500 mm
- **Grosor de Pared**: 0.1 - 50 mm

## 🏗️ Arquitectura

```
src/
├── backend/
│   └── app/
│       ├── api/           # Rutas REST API
│       ├── models/        # Schemas Pydantic
│       ├── services/      # Lógica de negocio
│       └── main.py        # Aplicación FastAPI
└── frontend/
    ├── index.html         # Interfaz principal
    ├── css/styles.css     # Estilos modernos
    └── js/main.js         # Lógica cliente + Three.js

data/exports/              # Archivos STL generados
tests/                     # Tests automatizados
```

## 🔌 API Endpoints

- `POST /api/generate` - Generar modelo 3D
- `GET /api/files` - Listar archivos generados
- `GET /api/files/{filename}` - Descargar archivo STL
- `POST /api/zip` - Crear ZIP de archivos seleccionados
- `GET /health` - Health check

### Ejemplo de Uso de API

```python
import requests

# Generar cubo de 20mm
response = requests.post('http://localhost:5000/api/generate', json={
    "model_type": "cube",
    "params": {"size": 20.0}
})

data = response.json()
print(f"Archivo generado: {data['metadata']['filename']}")
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Cobertura
pytest --cov=src tests/
```

## 🐳 Deployment

### Render

```yaml
services:
  - type: web
    name: generador-3d
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.backend.app.main:app --host 0.0.0.0 --port $PORT
```

### Fly.io

```bash
fly deploy
```

### Docker

```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["uvicorn", "src.backend.app.main:app", "--host", "0.0.0.0", "--port", "5000"]
```

## 🛠️ Desarrollo

### Estructura de Desarrollo

```bash
# Activar modo desarrollo
export ENVIRONMENT=development

# Ejecutar con recarga automática
uvicorn src.backend.app.main:app --reload

# Ejecutar tests en modo watch
pytest-watch
```

### Contribuir

1. Fork el repositorio
2. Crea feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📋 TODO / Roadmap

- [ ] **Más geometrías**: Pirámides, conos, toroides
- [ ] **Operaciones booleanas**: Unión, intersección, diferencia
- [ ] **Importar STL**: Editar modelos existentes
- [ ] **Texturas y colores**: Soporte para impresoras multi-color
- [ ] **Optimización automática**: Reducción de triángulos
- [ ] **Plantillas pre-diseñadas**: Modelos comunes listos para usar

## 🔧 Tecnologías

- **Backend**: FastAPI, Pydantic, Uvicorn
- **Frontend**: Vanilla JS, Three.js, CSS Grid
- **3D Generation**: NumPy, geometría computacional
- **File Handling**: STL ASCII format, ZIP compression
- **Deployment**: Docker, Docker Compose

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para detalles

## 🤝 Soporte

- **Issues**: [GitHub Issues](../../issues)
- **Documentación**: [Wiki](../../wiki)
- **API Docs**: `http://localhost:5000/docs` (cuando esté ejecutándose)

---

**⭐ Si te gusta este proyecto, considera darle una estrella en GitHub**