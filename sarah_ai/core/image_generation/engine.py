"""
Advanced Image Generation Engine
Central orchestrator for image generation with support for multiple providers
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import base64
from PIL import Image
import io
import hashlib

from .types import (
    ImageGenerationRequest, GeneratedImage, ImageGenerationSettings,
    ImageProvider, ImageModel, ImageQuality, ContentSafetyLevel, ImageMetadata
)
from .providers import ImageGenerationProvider, HuggingFaceProvider, ReplicateProvider, ComfyUIProvider


class ImageGenerationEngine:
    """
    Premium image generation engine with multiple provider support
    Features:
    - Multiple free API providers (Hugging Face, Replicate)
    - Local ComfyUI support (optional)
    - Sarah AI autonomous generation
    - Advanced image management
    - Vision integration
    """
    
    def __init__(self, storage_path: Path = Path("./images")):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subfolders
        self.sarah_images_path = self.storage_path / "sarah_generated"
        self.user_images_path = self.storage_path / "user_generated"
        self.sarah_images_path.mkdir(exist_ok=True)
        self.user_images_path.mkdir(exist_ok=True)
        
        # Settings
        self.settings = ImageGenerationSettings()
        self.settings_file = self.storage_path / "settings.json"
        self.images_metadata_file = self.storage_path / "metadata.json"
        
        # Providers
        self.providers: Dict[ImageProvider, ImageGenerationProvider] = {
            ImageProvider.HUGGING_FACE: HuggingFaceProvider(),
            ImageProvider.REPLICATE: ReplicateProvider(),
            ImageProvider.COMFYUI_LOCAL: ComfyUIProvider(),
        }
        self.current_provider: Optional[ImageGenerationProvider] = None
        
        # History and metadata
        self.history_file = self.storage_path / "history.json"
        self.history: List[Dict[str, Any]] = []
        self.generation_cache: Dict[str, GeneratedImage] = {}
        self.images_metadata: Dict[str, ImageMetadata] = {}
        self.last_sarah_generation: datetime = datetime.now() - timedelta(hours=24)
        
        print("[IMAGE GEN]: Engine initialized with storage at", self.storage_path)
    
    async def initialize(self):
        """Initialize all providers and load settings"""
        print("[IMAGE GEN]: Initializing providers...")
        
        # Load settings
        await self.load_settings()
        
        # Initialize providers
        for provider_type, provider in self.providers.items():
            try:
                kwargs = {
                    "api_key": self.settings.api_key,
                    "base_url": self.settings.local_comfyui_url,
                }
                initialized = await provider.initialize(**kwargs)
                if initialized:
                    print(f"[IMAGE GEN]: {provider.provider_name} initialized")
                else:
                    print(f"[IMAGE GEN]: {provider.provider_name} not available")
            except Exception as e:
                print(f"[IMAGE GEN]: Failed to initialize {provider.provider_name}: {e}")
        
        # Set current provider
        if isinstance(self.settings.provider, str):
            try:
                self.settings.provider = ImageProvider(self.settings.provider)
            except Exception:
                try:
                    self.settings.provider = ImageProvider[self.settings.provider]
                except Exception:
                    self.settings.provider = ImageProvider.HUGGING_FACE

        if self.settings.provider in self.providers:
            self.current_provider = self.providers[self.settings.provider]
            if self.current_provider.is_available:
                print(f"[IMAGE GEN]: Using {self.current_provider.provider_name}")
            else:
                # Fallback to first available
                for p in self.providers.values():
                    if p.is_available:
                        self.current_provider = p
                        print(f"[IMAGE GEN]: Fallback to {p.provider_name}")
                        break
        
        # Load metadata and history
        await self.load_metadata()
        await self._load_history()
        
        print("[IMAGE GEN]: Initialization complete")
    
    async def generate_image(self, prompt: str, user_id: Optional[str] = None,
                           **kwargs) -> GeneratedImage:
        """Generate image from prompt"""
        if not self.current_provider:
            raise Exception("No image provider available")
        
        request = ImageGenerationRequest(
            prompt=prompt,
            source="user",
            user_id=user_id,
            **kwargs
        )

        if self.settings.sfw_only:
            request.prompt = f"{request.prompt}. SFW safe for work, family friendly, no explicit content."
            if request.negative_prompt:
                request.negative_prompt = f"{request.negative_prompt}, nudity, sexual content, violence"
            else:
                request.negative_prompt = "nudity, sexual content, violence"
        
        image = await self.current_provider.generate_image(request)
        image.prompt = request.prompt
        
        if self.settings.save_images:
            await self.save_image(image)
        
        self._record_history({
            "type": "generate",
            "prompt": prompt,
            "provider": self.current_provider.provider_name,
            "model": request.model or self.settings.model.value,
            "source": image.source,
            "user_id": user_id,
            "image_id": image.image_id,
            "saved": image.saved,
            "timestamp": image.created_at.isoformat(),
        })
        
        return image
    
    async def generate_image_from_image(self, image_input: bytes, prompt: str,
                                       strength: float = 0.8,
                                       user_id: Optional[str] = None,
                                       **kwargs) -> GeneratedImage:
        """Generate image from image input (img2img)"""
        if not self.current_provider:
            raise Exception("No image provider available")
        
        request = ImageGenerationRequest(
            prompt=prompt,
            image_input=image_input,
            strength=strength,
            source="user",
            user_id=user_id,
            **kwargs
        )

        if self.settings.sfw_only:
            request.prompt = f"{request.prompt}. Keep the result safe for work, no explicit adult content."
            request.negative_prompt = (request.negative_prompt or "") + ", nudity, sexual content, violence"
        
        image = await self.current_provider.image_to_image(request)
        if self.settings.save_images:
            await self.save_image(image)
        
        self._record_history({
            "type": "image_to_image",
            "prompt": prompt,
            "provider": self.current_provider.provider_name,
            "model": request.model or self.settings.model.value,
            "source": image.source,
            "user_id": user_id,
            "image_id": image.image_id,
            "saved": image.saved,
            "timestamp": image.created_at.isoformat(),
        })
        
        return image
    
    async def save_image(self, image: GeneratedImage) -> str:
        """Save generated image to storage"""
        if not self.settings.save_images:
            image.saved = False
            return ""
        
        # Determine save path
        if image.source == "sarah":
            base_path = self.sarah_images_path
        else:
            base_path = self.user_images_path
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_hash = hashlib.md5(image.prompt.encode()).hexdigest()[:8]
        filename = f"{timestamp}_{prompt_hash}.png"
        filepath = base_path / filename
        
        # Save image
        try:
            # Save as PNG
            img = Image.open(io.BytesIO(image.image_data))
            img.save(filepath, "PNG")
            
            image.saved = True
            image.save_path = str(filepath)
            
            # Update metadata
            metadata = ImageMetadata(
                image_id=image.image_id,
                filename=filename,
                filepath=str(filepath),
                prompt=image.prompt,
                model=image.model_used,
                provider=image.provider,
                source=image.source,
                created_at=image.created_at,
                modified_at=datetime.now(),
                file_size=len(image.image_data),
                width=img.width,
                height=img.height,
                format="png",
                generation_time=image.generation_time,
            )
            
            self.images_metadata[image.image_id] = metadata
            await self.save_metadata()
            
            print(f"[IMAGE GEN]: Saved image {image.image_id[:8]}... to {filename}")
            return str(filepath)
            
        except Exception as e:
            print(f"[IMAGE GEN]: Failed to save image: {e}")
            raise
    
    async def decide_generate_image(self, context: Dict[str, Any]) -> bool:
        """Decide if Sarah should autonomously generate an image"""
        if not self.settings.allow_sarah_generation:
            return False
        
        # Check cooldown
        time_since_last = datetime.now() - self.last_sarah_generation
        if time_since_last.total_seconds() < self.settings.sarah_generation_cooldown:
            return False
        
        # Decision factors from personality and context:
        # - Emotional state (wants to share mood)
        # - Boredom level
        # - User's birthday (send birthday card)
        # - User preference for images
        # - Message clarity improvement (explain visual concept)
        
        # Simple decision for now - can be enhanced with personality system
        import random
        decision_probability = 0.15  # 15% chance to generate
        
        if random.random() < decision_probability:
            self.last_sarah_generation = datetime.now()
            return True
        
        return False
    
    async def generate_sarah_image(self, context: Dict[str, Any]) -> Optional[GeneratedImage]:
        """Generate image autonomously as Sarah"""
        if not await self.decide_generate_image(context):
            return None
        
        # Generate appropriate prompt based on context
        # This integrates with Sarah's personality and understanding
        prompt = context.get("generated_prompt", "A beautiful sunset over mountains")
        
        try:
            request = ImageGenerationRequest(
                prompt=prompt,
                source="sarah",
                **{
                    "quality": ImageQuality.STANDARD,
                    "width": 1024,
                    "height": 1024,
                }
            )
            
            image = await self.current_provider.generate_image(request)
            
            # Always save Sarah's generations
            await self.save_image(image)
            
            print(f"[IMAGE GEN]: Sarah generated image with prompt: {prompt[:50]}...")
            return image
            
        except Exception as e:
            print(f"[IMAGE GEN]: Sarah image generation failed: {e}")
            return None
    
    async def load_settings(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    settings_data = json.load(f)
                    if "provider" in settings_data:
                        try:
                            self.settings.provider = ImageProvider(settings_data["provider"])
                        except Exception:
                            try:
                                self.settings.provider = ImageProvider[settings_data["provider"]]
                            except Exception:
                                self.settings.provider = ImageProvider.HUGGING_FACE
                    if "model" in settings_data:
                        model_value = settings_data["model"]
                        try:
                            self.settings.model = ImageModel[model_value]
                        except Exception:
                            try:
                                self.settings.model = ImageModel(model_value)
                            except Exception:
                                self.settings.model = ImageModel.FLUX_DEV
                    if "default_quality" in settings_data:
                        quality_value = settings_data["default_quality"]
                        try:
                            self.settings.default_quality = ImageQuality[quality_value]
                        except Exception:
                            try:
                                self.settings.default_quality = ImageQuality(quality_value)
                            except Exception:
                                self.settings.default_quality = ImageQuality.STANDARD
                    self.settings.api_key = settings_data.get("api_key", self.settings.api_key)
                    self.settings.local_comfyui_url = settings_data.get("local_comfyui_url", self.settings.local_comfyui_url)
                    self.settings.sfw_only = settings_data.get("sfw_only", self.settings.sfw_only)
                    self.settings.allow_sarah_generation = settings_data.get("allow_sarah_generation", self.settings.allow_sarah_generation)
                    self.settings.save_images = settings_data.get("save_images", self.settings.save_images)
                    self.settings.save_path = settings_data.get("save_path", self.settings.save_path)
                    self.settings.sarah_generation_cooldown = settings_data.get("sarah_generation_cooldown", self.settings.sarah_generation_cooldown)
                    self.settings.organize_by_source = settings_data.get("organize_by_source", self.settings.organize_by_source)
                    print(f"[IMAGE GEN]: Loaded settings from {self.settings_file}")
            except Exception as e:
                print(f"[IMAGE GEN]: Failed to load settings: {e}")
        else:
            await self.save_settings()
    
    async def save_settings(self):
        """Save settings to file"""
        try:
            settings_dict = {
                "enabled": self.settings.enabled,
                "provider": self.settings.provider.value,
                "model": self.settings.model.name,
                "api_key": self.settings.api_key,
                "local_comfyui_url": self.settings.local_comfyui_url,
                "sfw_only": self.settings.sfw_only,
                "allow_sarah_generation": self.settings.allow_sarah_generation,
                "save_images": self.settings.save_images,
                "default_quality": self.settings.default_quality.name,
                "save_path": self.settings.save_path,
                "organize_by_source": self.settings.organize_by_source,
                "sarah_generation_cooldown": self.settings.sarah_generation_cooldown,
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_dict, f, indent=2)
            
            print(f"[IMAGE GEN]: Saved settings to {self.settings_file}")
        except Exception as e:
            print(f"[IMAGE GEN]: Failed to save settings: {e}")
    
    async def load_metadata(self):
        """Load image metadata"""
        if self.images_metadata_file.exists():
            try:
                with open(self.images_metadata_file, 'r') as f:
                    data = json.load(f)
                    # Deserialize metadata
                    for image_id, meta_dict in data.items():
                        try:
                            meta_dict['created_at'] = datetime.fromisoformat(meta_dict['created_at'])
                            meta_dict['modified_at'] = datetime.fromisoformat(meta_dict['modified_at'])
                            self.images_metadata[image_id] = ImageMetadata(
                                image_id=meta_dict['image_id'],
                                filename=meta_dict['filename'],
                                filepath=meta_dict['filepath'],
                                prompt=meta_dict['prompt'],
                                model=meta_dict['model'],
                                provider=ImageProvider(meta_dict['provider']) if isinstance(meta_dict['provider'], str) else meta_dict['provider'],
                                source=meta_dict['source'],
                                created_at=meta_dict['created_at'],
                                modified_at=meta_dict['modified_at'],
                                file_size=meta_dict['file_size'],
                                width=meta_dict['width'],
                                height=meta_dict['height'],
                                format=meta_dict['format'],
                                generation_time=meta_dict['generation_time'],
                                metadata=meta_dict.get('metadata', {}),
                            )
                        except Exception:
                            continue
                    print(f"[IMAGE GEN]: Loaded metadata for {len(self.images_metadata)} images")
            except Exception as e:
                print(f"[IMAGE GEN]: Failed to load metadata: {e}")
    
    async def save_metadata(self):
        """Save image metadata"""
        try:
            metadata_dict = {}
            for image_id, metadata in self.images_metadata.items():
                metadata_dict[image_id] = {
                    "image_id": metadata.image_id,
                    "filename": metadata.filename,
                    "filepath": metadata.filepath,
                    "prompt": metadata.prompt,
                    "model": metadata.model,
                    "provider": metadata.provider.value,
                    "source": metadata.source,
                    "created_at": metadata.created_at.isoformat(),
                    "modified_at": metadata.modified_at.isoformat(),
                    "width": metadata.width,
                    "height": metadata.height,
                    "format": metadata.format,
                    "generation_time": metadata.generation_time,
                    "metadata": metadata.metadata,
                }
            
            with open(self.images_metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
        except Exception as e:
            print(f"[IMAGE GEN]: Failed to save metadata: {e}")

    async def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    async def _save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-200:], f, indent=2)
        except Exception as e:
            print(f"[IMAGE GEN]: Failed to save history: {e}")

    def _record_history(self, entry: Dict[str, Any]):
        entry["timestamp"] = datetime.now().isoformat()
        self.history.insert(0, entry)
        asyncio.create_task(self._save_history())

    async def list_saved_images(self) -> List[str]:
        images = []
        for folder in [self.sarah_images_path, self.user_images_path]:
            if folder.exists():
                for file in sorted(folder.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True):
                    if file.is_file():
                        url_path = f"/images/{folder.name}/{file.name}"
                        images.append(url_path)
        return images

    async def get_history(self) -> List[Dict[str, Any]]:
        return self.history
    
    async def get_sarah_images(self) -> List[str]:
        """Get all Sarah-generated image paths"""
        return [str(f) for f in self.sarah_images_path.glob("*.png")]
    
    async def get_user_images(self) -> List[str]:
        """Get all user-generated image paths"""
        return [str(f) for f in self.user_images_path.glob("*.png")]
    
    async def get_all_images(self) -> Dict[str, List[str]]:
        """Get all images organized by source"""
        return {
            "sarah_generated": await self.get_sarah_images(),
            "user_generated": await self.get_user_images(),
        }

    async def set_provider(self, provider: str) -> bool:
        try:
            provider_enum = ImageProvider(provider)
        except Exception:
            try:
                provider_enum = ImageProvider[provider]
            except Exception:
                return False

        if provider_enum in self.providers:
            self.settings.provider = provider_enum
            if self.providers[provider_enum].is_available:
                self.current_provider = self.providers[provider_enum]
            await self.save_settings()
            return True
        return False

    async def set_model(self, model: str) -> bool:
        try:
            self.settings.model = ImageModel[model]
        except Exception:
            try:
                self.settings.model = ImageModel(model)
            except Exception:
                return False
        await self.save_settings()
        return True

    async def set_sfw_only(self, value: bool) -> None:
        self.settings.sfw_only = value
        await self.save_settings()

    async def set_save_images(self, value: bool) -> None:
        self.settings.save_images = value
        await self.save_settings()

    async def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        sarah_images = await self.get_sarah_images()
        user_images = await self.get_user_images()
        
        return {
            "provider": self.settings.provider.value,
            "enabled": self.settings.enabled,
            "sarah_generations_allowed": self.settings.allow_sarah_generation,
            "save_images_enabled": self.settings.save_images,
            "sfw_only": self.settings.sfw_only,
            "total_sarah_images": len(sarah_images),
            "total_user_images": len(user_images),
            "total_images": len(sarah_images) + len(user_images),
            "storage_path": str(self.storage_path),
            "provider_status": await self.current_provider.get_status() if self.current_provider else None,
        }
