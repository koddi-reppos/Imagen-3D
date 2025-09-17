"""
FastAPI main application with advanced AI capabilities
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os

from .api.routes import router
from .api.image_routes import router as image_router
from .api.job_routes import router as job_router
from .database.database import connect_database, disconnect_database, create_tables
from .services.providers.base import provider_manager
from .services.providers.openai_provider import OpenAIImageProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("🚀 Starting Advanced AI 3D Generator...")
    
    # Create database tables
    create_tables()
    print("✅ Database tables created")
    
    # Connect to database
    await connect_database()
    print("✅ Database connected")
    
    # Initialize AI providers
    await initialize_providers()
    
    yield
    
    # Shutdown
    await disconnect_database()
    print("👋 Shutdown complete")


async def initialize_providers():
    """Initialize and register AI providers"""
    providers_initialized = []
    
    # Register OpenAI provider if API key is available
    if os.getenv("OPENAI_API_KEY"):
        openai_provider = OpenAIImageProvider()
        provider_manager.register_image_gen_provider("openai", openai_provider)
        providers_initialized.append("OpenAI DALL-E")
    
    # TODO: Add more providers here
    # - Stability AI (Clipdrop)
    # - Replicate 
    # - Enhanced Meshy AI
    
    print(f"✅ AI Providers initialized: {', '.join(providers_initialized) if providers_initialized else 'None (check API keys)'}")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Advanced AI 3D Generator",
    description="Professional AI-powered 3D model generation platform with image processing",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Serve static frontend files
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "generador-3d"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)