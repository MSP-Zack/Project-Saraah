"""
Image Generation Types and Data Structures
Shared types for the image generation system
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class ImageProvider(Enum):
    """Available image generation providers"""
    HUGGING_FACE = "huggingface"  # Free API tier
    REPLICATE = "replicate"  # Free tier with credits
    COMFYUI_LOCAL = "comfyui_local"  # Local ComfyUI instance


class ImageModel(Enum):
    """Best-in-class models for May 2026"""
    # Hugging Face models
    FLUX_DEV = "black-forest-labs/FLUX.1-dev"  # Best quality (HF)
    FLUX_SCHNELL = "black-forest-labs/FLUX.1-schnell"  # Fast (HF)
    RELIBERATE_V3 = "stablediffusion/reliberate-v3"  # Reliable
    
    # Replicate models
    FLUX_PRO = "black-forest-labs/flux-pro"  # Premium (Replicate)
    FLUX_REALISM = "black-forest-labs/flux-realism"  # Realistic


class ImageQuality(Enum):
    """Image quality presets"""
    DRAFT = "draft"  # Fast, lower quality
    STANDARD = "standard"  # Good balance
    HIGH = "high"  # Highest quality


class ImageStyle(Enum):
    """Predefined artistic styles"""
    PHOTOREALISTIC = "photorealistic"
    ARTISTIC = "artistic"
    CARTOON = "cartoon"
    ANIME = "anime"
    OIL_PAINTING = "oil painting"
    WATERCOLOR = "watercolor"
    SKETCH = "sketch"


class ContentSafetyLevel(Enum):
    """Content safety settings"""
    STRICT = "strict"  # SFW only
    MODERATE = "moderate"  # SFW mostly
    OFF = "off"  # No filtering


@dataclass
class ImageGenerationRequest:
    """Request to generate an image"""
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    quality: ImageQuality = ImageQuality.STANDARD
    style: Optional[ImageStyle] = None
    num_steps: int = 20
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    model: Optional[str] = None
    
    # Image-to-image
    image_input: Optional[bytes] = None  # Base64 or bytes
    strength: float = 0.8  # Influence of input image (0-1)
    
    # Metadata
    source: str = "user"  # "user" or "sarah"
    user_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedImage:
    """Result of image generation"""
    image_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    image_data: bytes = b""
    prompt: str = ""
    negative_prompt: Optional[str] = None
    model_used: str = ""
    provider: ImageProvider = ImageProvider.HUGGING_FACE
    quality: ImageQuality = ImageQuality.STANDARD
    generation_time: float = 0.0  # Seconds
    url: Optional[str] = None  # If provider returns URL
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "user"
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    saved: bool = False
    save_path: Optional[str] = None


@dataclass
class ImageGenerationSettings:
    """Settings for image generation"""
    # Provider settings
    enabled: bool = True
    provider: ImageProvider = ImageProvider.HUGGING_FACE
    model: ImageModel = ImageModel.FLUX_DEV
    huggingface_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    local_comfyui_url: Optional[str] = None
    
    # Safety settings
    sfw_only: bool = True
    content_safety_level: ContentSafetyLevel = ContentSafetyLevel.STRICT
    
    # Sarah settings
    allow_sarah_generation: bool = True
    sarah_generation_cooldown: int = 3600  # Seconds between Sarah generations
    
    # Storage settings
    save_images: bool = True
    save_path: str = "./images"
    organize_by_source: bool = True  # Separate Sarah vs user
    
    # Quality settings
    default_quality: ImageQuality = ImageQuality.STANDARD
    default_width: int = 1024
    default_height: int = 1024
    max_width: int = 2048
    max_height: int = 2048
    
    # Performance
    cache_generations: bool = True
    cache_size: int = 100
    batch_processing: bool = False


@dataclass
class ImageMetadata:
    """Metadata about a generated or stored image"""
    image_id: str
    filename: str
    filepath: str
    prompt: str
    model: str
    provider: ImageProvider
    source: str  # "user" or "sarah"
    created_at: datetime
    modified_at: datetime
    file_size: int  # Bytes
    width: int
    height: int
    format: str  # jpg, png, webp
    generation_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
