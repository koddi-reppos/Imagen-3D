"""
Advanced AI 3D Model Generation using professional APIs
"""
import asyncio
import aiohttp
import requests
import os
import time
from typing import Dict, Any, Optional, Tuple
import json
from typing import Dict, Any, Optional, Tuple
import json


class MeshyAIGenerator:
    """Integration with Meshy AI for professional 3D model generation"""
    
    def __init__(self):
        self.api_key = os.getenv("MESHY_API_KEY")
        self.base_url = "https://api.meshy.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_from_text(self, prompt: str, style: str = "realistic") -> Optional[Dict[str, Any]]:
        """Generate 3D model from text description"""
        if not self.api_key:
            raise ValueError("MESHY_API_KEY not configured")
        
        # Start generation task
        payload = {
            "prompt": prompt,
            "style": style,
            "quality": "high",
            "format": "stl"
        }
        
        async with aiohttp.ClientSession() as session:
            # Create generation task
            async with session.post(
                f"{self.base_url}/text-to-3d",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status != 200:
                    return None
                
                task_data = await response.json()
                task_id = task_data.get("task_id")
                
                if not task_id:
                    return None
                
                # Poll for completion
                return await self._poll_task_completion(session, task_id)
    
    async def _poll_task_completion(self, session: aiohttp.ClientSession, task_id: str, max_wait: int = 300) -> Optional[Dict[str, Any]]:
        """Poll task until completion"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            async with session.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self.headers
            ) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                status = data.get("status")
                
                if status == "completed":
                    return data
                elif status == "failed":
                    return None
                
                # Wait before next poll
                await asyncio.sleep(10)
        
        return None
    
    async def download_model(self, download_url: str) -> Optional[bytes]:
        """Download the generated STL file"""
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    return await response.read()
        return None


class AIModelGenerator:
    """Main AI model generator with fallback options"""
    
    def __init__(self):
        self.meshy = MeshyAIGenerator()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined professional model templates"""
        return {
            "castillo_medieval": {
                "prompt": "Detailed medieval castle with towers, walls, and battlements, stone texture, fortress architecture, ready for 3D printing",
                "category": "Architecture",
                "style": "realistic",
                "description": "Castillo medieval completo con torres y murallas"
            },
            "muneco_ninja": {
                "prompt": "Cartoon ninja character with black outfit, katana sword, dynamic pose, anime style, game ready asset",
                "category": "Characters",
                "style": "cartoon",
                "description": "Muñeco ninja estilo anime con katana"
            },
            "dragon_fantastico": {
                "prompt": "Majestic fantasy dragon with detailed scales, wings spread, breathing fire pose, high detail sculpture",
                "category": "Fantasy",
                "style": "realistic",
                "description": "Dragón fantástico con alas extendidas"
            },
            "casa_moderna": {
                "prompt": "Modern house architecture with clean lines, large windows, minimalist design, contemporary style",
                "category": "Architecture", 
                "style": "realistic",
                "description": "Casa moderna minimalista"
            },
            "robot_futurista": {
                "prompt": "Futuristic robot with mechanical details, LED lights, sci-fi design, articulated joints",
                "category": "Sci-Fi",
                "style": "realistic",
                "description": "Robot futurista con detalles mecánicos"
            },
            "princesa_cartoon": {
                "prompt": "Cute cartoon princess character with flowing dress, crown, Disney-style animation, child-friendly",
                "category": "Characters",
                "style": "cartoon",
                "description": "Princesa estilo cartoon con vestido"
            },
            "nave_espacial": {
                "prompt": "Sleek spaceship design with thruster engines, cockpit windows, sci-fi spacecraft, Star Wars inspired",
                "category": "Sci-Fi",
                "style": "realistic",
                "description": "Nave espacial con motores y cabina"
            },
            "torre_mago": {
                "prompt": "Wizard tower with spiral staircase, magical crystals, fantasy architecture, mystical details",
                "category": "Fantasy",
                "style": "realistic",
                "description": "Torre de mago con cristales mágicos"
            },
            "dinosaurio_trex": {
                "prompt": "Realistic T-Rex dinosaur with detailed texture, open mouth showing teeth, museum quality",
                "category": "Animals",
                "style": "realistic", 
                "description": "Tiranosaurio Rex con textura detallada"
            },
            "coche_deportivo": {
                "prompt": "Sports car with aerodynamic design, racing stripes, detailed wheels, luxury automotive",
                "category": "Vehicles",
                "style": "realistic",
                "description": "Coche deportivo aerodinámico"
            }
        }
    
    async def generate_professional_model(self, template_id: str = None, custom_prompt: str = None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Generate professional 3D model"""
        
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            prompt = template["prompt"]
            style = template.get("style", "realistic")
            category = template.get("category", "Custom")
        elif custom_prompt:
            prompt = self._enhance_prompt(custom_prompt)
            style = "realistic"
            category = "Custom"
        else:
            raise ValueError("Either template_id or custom_prompt must be provided")
        
        try:
            # Try Meshy AI first
            result = await self.meshy.generate_from_text(prompt, style)
            
            if result and result.get("status") == "completed":
                download_url = result.get("download_url")
                if download_url:
                    stl_data = await self.meshy.download_model(download_url)
                    if stl_data:
                        # Convert bytes to string for STL
                        stl_content = stl_data.decode('utf-8', errors='ignore')
                        
                        metadata = {
                            "filename": f"{template_id or 'custom'}_{int(time.time())}.stl",
                            "model_type": "ai_generated",
                            "category": category,
                            "prompt": prompt,
                            "style": style,
                            "ai_provider": "meshy",
                            "triangles": stl_content.count("facet normal") if stl_content else 0
                        }
                        
                        return stl_content, metadata
            
                # Fallback to local generation with enhanced geometry
            return await self._fallback_generation(prompt, template_id or "custom")
            
        except Exception as e:
            # Fallback to local generation
            return await self._fallback_generation(prompt, template_id or "custom")
    
    def _enhance_prompt(self, prompt: str) -> str:
        """Enhance user prompt for better AI generation"""
        enhancements = [
            "high detail",
            "3D printable",
            "clean topology", 
            "professional quality",
            "optimized for printing"
        ]
        
        enhanced = f"{prompt}, {', '.join(enhancements)}"
        return enhanced
    
    async def _fallback_generation(self, prompt: str, template_id: str) -> Tuple[str, Dict[str, Any]]:
        """Fallback to local procedural generation"""
        from .generator import generate_cube
        
        # Generate a more complex shape as fallback
        stl_content, metadata = generate_cube(20.0)
        
        # Update metadata to reflect AI attempt
        metadata.update({
            "filename": f"{template_id}_fallback_{int(time.time())}.stl",
            "model_type": "ai_fallback",
            "prompt": prompt,
            "ai_provider": "local_fallback",
            "note": "AI generation failed, using enhanced geometric fallback"
        })
        
        return stl_content, metadata
    
    def get_available_templates(self) -> Dict[str, Any]:
        """Get all available professional model templates"""
        return self.templates


# Global AI generator instance
ai_generator = AIModelGenerator()