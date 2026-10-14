"""
Image Generation Provider Interface and Base Classes
Defines the contract for all image generation providers
"""

import asyncio
from abc import ABC, abstractmethod
import base64
import os
from typing import Optional, List, Dict, Any
import io
from datetime import datetime

from .types import ImageGenerationRequest, GeneratedImage, ImageProvider


class ImageGenerationProvider(ABC):
    """Base class for all image generation providers"""
    
    def __init__(self):
        self.provider_name: str = ""
        self.supported_models: List[str] = []
        self.rate_limit_remaining: int = 0
        self.rate_limit_reset_time: Optional[datetime] = None
        self.is_available: bool = False
        
    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """Initialize provider with credentials or configuration"""
        pass
    
    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Generate a single image from request"""
        pass
    
    @abstractmethod
    async def image_to_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Generate image from image input (modification/variation)"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    async def validate_request(self, request: ImageGenerationRequest) -> bool:
        """Validate that request meets provider requirements"""
        if not request.prompt:
            raise ValueError("Prompt cannot be empty")
        if request.width > 2048 or request.height > 2048:
            raise ValueError("Image dimensions exceed maximum")
        return True
    
    async def apply_nsfw_filter(self, image_data: bytes, sfw_only: bool) -> Optional[bytes]:
        """Apply NSFW filtering if needed. Return None if filtered out."""
        # Subclasses can override for more sophisticated filtering
        # For now, just pass through
        return image_data if sfw_only else image_data
    
    async def get_cost(self, request: ImageGenerationRequest) -> float:
        """Get estimated cost (in credits or USD) for generation"""
        return 0.0  # Free providers return 0
    
    async def check_rate_limit(self) -> bool:
        """Check if provider is rate limited"""
        if self.rate_limit_remaining <= 0:
            return False
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Get provider status information"""
        return {
            "name": self.provider_name,
            "available": self.is_available,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset_time": self.rate_limit_reset_time,
            "supported_models": self.supported_models
        }


class HuggingFaceProvider(ImageGenerationProvider):
    """Hugging Face Inference API Provider (Free tier)"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "Hugging Face Inference"
        self.api_key: Optional[str] = None
        self.api_url = "https://api-inference.huggingface.co/models"
        self.supported_models = [
            "black-forest-labs/FLUX.1-dev",
            "black-forest-labs/FLUX.1-schnell",
            "stablediffusion/reliberate-v3",
        ]
        
    async def initialize(self, api_key: Optional[str] = None, **kwargs) -> bool:
        """Initialize with API key"""
        if api_key:
            self.api_key = api_key
        else:
            # Try to get from environment
            import os
            self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        if self.api_key:
            self.is_available = True
            return True
        else:
            print("[IMAGE GEN]: Warning - Hugging Face API key not configured")
            return False
    
    async def generate_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Generate image using Hugging Face API"""
        if not await self.validate_request(request):
            raise ValueError("Invalid request")
        
        try:
            import os
            import requests
            import time
            
            model = request.model or "black-forest-labs/FLUX.1-schnell"  # Default to fast model
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            payload = {
                "inputs": request.prompt,
                "parameters": {
                    "negative_prompt": request.negative_prompt or "",
                    "width": request.width,
                    "height": request.height,
                    "guidance_scale": request.guidance_scale,
                    "num_inference_steps": request.num_steps,
                }
            }
            
            # Add seed if specified
            if request.seed is not None:
                payload["parameters"]["seed"] = request.seed
            
            url = f"{self.api_url}/{model}"
            
            def sync_request():
                return requests.post(url, json=payload, headers=headers, timeout=120)
            start_time = time.time()
            response = await asyncio.to_thread(sync_request)
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                image_data = response.content
                
                # Apply NSFW filter if needed
                image_data = await self.apply_nsfw_filter(image_data, True)
                
                return GeneratedImage(
                    image_data=image_data,
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    model_used=model,
                    provider=ImageProvider.HUGGING_FACE,
                    quality=request.quality,
                    generation_time=generation_time,
                    source=request.source,
                    user_id=request.user_id,
                    metadata={"status_code": response.status_code}
                )
            else:
                raise Exception(f"HF API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[IMAGE GEN]: Generation failed: {str(e)}")
            raise
    
    async def image_to_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Generate from image input using ControlNet or inpainting"""
        if not request.image_input:
            raise ValueError("image_input required for image-to-image generation")
        
        # For now, fall back to standard generation
        # In production, would use actual img2img models
        return await self.generate_image(request)
    
    async def get_available_models(self) -> List[str]:
        """Get available models"""
        return self.supported_models
    
    async def get_status(self) -> Dict[str, Any]:
        """Get provider status"""
        status = await super().get_status()
        status["api_configured"] = bool(self.api_key)
        return status


class ReplicateProvider(ImageGenerationProvider):
    """Replicate.com Provider (Free tier with credits)"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "Replicate"
        self.api_key: Optional[str] = None
        self.api_url = "https://api.replicate.com/v1"
        self.supported_models = [
            "black-forest-labs/flux-pro",
            "black-forest-labs/flux-realism",
            "stability-ai/sdxl",
        ]
    
    async def initialize(self, api_key: Optional[str] = None, **kwargs) -> bool:
        """Initialize with API key"""
        if api_key:
            self.api_key = api_key
        else:
            import os
            self.api_key = os.getenv("REPLICATE_API_TOKEN")
        
        if self.api_key:
            self.is_available = True
            return True
        else:
            print("[IMAGE GEN]: Warning - Replicate API key not configured")
            return False
    
    async def generate_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Generate using Replicate API"""
        if not await self.validate_request(request):
            raise ValueError("Invalid request")
        
        try:
            import replicate
            import requests
            import time
            
            # Set API token
            replicate.api.token = self.api_key
            
            model = request.model or "black-forest-labs/flux-pro"
            
            input_data = {
                "prompt": request.prompt,
                "width": request.width,
                "height": request.height,
                "guidance": request.guidance_scale,
                "num_inference_steps": request.num_steps,
            }
            
            if request.negative_prompt:
                input_data["negative_prompt"] = request.negative_prompt
            if request.seed is not None:
                input_data["seed"] = request.seed
            
            start_time = time.time()
            output = await asyncio.to_thread(
                replicate.run,
                model,
                input=input_data
            )
            generation_time = time.time() - start_time
            
            # Download image from output URL
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
                def sync_download():
                    return requests.get(image_url, timeout=30)
                image_response = await asyncio.to_thread(sync_download)
                image_data = image_response.content
            else:
                raise Exception("Unexpected Replicate output format")
            
            return GeneratedImage(
                image_data=image_data,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                model_used=model,
                provider=ImageProvider.REPLICATE,
                quality=request.quality,
                generation_time=generation_time,
                url=output[0] if isinstance(output, list) else output,
                source=request.source,
                user_id=request.user_id,
            )
            
        except Exception as e:
            print(f"[IMAGE GEN]: Replicate generation failed: {str(e)}")
            raise
    
    async def image_to_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Image-to-image using Replicate"""
        if not request.image_input:
            raise ValueError("image_input required for image-to-image generation")
        return await self.generate_image(request)
    
    async def get_available_models(self) -> List[str]:
        """Get available models"""
        return self.supported_models


class ComfyUIProvider(ImageGenerationProvider):
    """Local ComfyUI Provider"""

    def __init__(self):
        super().__init__()
        self.provider_name = "ComfyUI Local"
        self.base_url = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
        self.supported_models = ["stable-diffusion-v1-5", "sdxl", "anything-v5"]

    async def initialize(self, base_url: Optional[str] = None, **kwargs) -> bool:
        if base_url:
            self.base_url = base_url
        try:
            import requests
            url = f"{self.base_url.rstrip('/')}/sdapi/v1/progress"
            def sync_test():
                return requests.get(url, timeout=5)
            response = await asyncio.to_thread(sync_test)
            self.is_available = response.status_code == 200
        except Exception:
            self.is_available = False
        return self.is_available

    async def generate_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        if not await self.validate_request(request):
            raise ValueError("Invalid request")

        try:
            import requests
            import time
            
            url = f"{self.base_url.rstrip('/')}/sdapi/v1/txt2img"
            payload = {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt or "",
                "width": request.width,
                "height": request.height,
                "steps": request.num_steps,
                "cfg_scale": request.guidance_scale,
                "seed": request.seed if request.seed is not None else -1,
                "sampler_name": "Euler a"
            }
            
            def sync_request():
                return requests.post(url, json=payload, timeout=120)
            start_time = time.time()
            response = await asyncio.to_thread(sync_request)
            generation_time = time.time() - start_time
            response.raise_for_status()
            data = response.json()
            images = data.get("images", [])
            if not images:
                raise Exception("ComfyUI returned no images")
            image_base64 = images[0]
            image_data = base64.b64decode(image_base64)
            
            return GeneratedImage(
                image_data=image_data,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                model_used=request.model or "comfyui_local",
                provider=ImageProvider.COMFYUI_LOCAL,
                quality=request.quality,
                generation_time=generation_time,
                source=request.source,
                user_id=request.user_id,
            )
        except Exception as e:
            print(f"[IMAGE GEN]: ComfyUI generation failed: {e}")
            raise

    async def image_to_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        if not request.image_input:
            raise ValueError("image_input required for image-to-image generation")

        try:
            import requests
            import time
            url = f"{self.base_url.rstrip('/')}/sdapi/v1/img2img"
            encoded_img = base64.b64encode(request.image_input).decode("utf-8")
            payload = {
                "init_images": [encoded_img],
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt or "",
                "steps": request.num_steps,
                "cfg_scale": request.guidance_scale,
                "denoising_strength": request.strength,
                "seed": request.seed if request.seed is not None else -1,
            }
            def sync_request():
                return requests.post(url, json=payload, timeout=120)
            start_time = time.time()
            response = await asyncio.to_thread(sync_request)
            generation_time = time.time() - start_time
            response.raise_for_status()
            data = response.json()
            images = data.get("images", [])
            if not images:
                raise Exception("ComfyUI returned no images")
            image_data = base64.b64decode(images[0])
            return GeneratedImage(
                image_data=image_data,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                model_used=request.model or "comfyui_local",
                provider=ImageProvider.COMFYUI_LOCAL,
                quality=request.quality,
                generation_time=generation_time,
                source=request.source,
                user_id=request.user_id,
            )
        except Exception as e:
            print(f"[IMAGE GEN]: ComfyUI image-to-image failed: {e}")
            raise

    async def get_available_models(self) -> List[str]:
        return self.supported_models
