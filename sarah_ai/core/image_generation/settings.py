"""
Image Generation Settings Management
Handles all configuration, toggles, and preferences for the image system
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

from .types import (
    ImageGenerationSettings, ImageProvider, ImageModel,
    ImageQuality, ContentSafetyLevel
)


class SettingsManager:
    """
    Manages all image generation settings
    Provides UI-friendly interfaces for configuration
    """
    
    def __init__(self, settings_file: Path):
        self.settings_file = settings_file
        self.current_settings = ImageGenerationSettings()
        self._load()
    
    def _load(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self._apply_settings(data)
                print(f"[SETTINGS]: Loaded image generation settings")
            except Exception as e:
                print(f"[SETTINGS]: Error loading settings: {e}")
    
    def _apply_settings(self, data: Dict[str, Any]):
        """Apply loaded settings to current settings object"""
        try:
            # Basic settings
            self.current_settings.enabled = data.get("enabled", True)
            self.current_settings.huggingface_api_key = data.get("huggingface_api_key")
            self.current_settings.replicate_api_key = data.get("replicate_api_key")
            
            # Provider
            provider_str = data.get("provider", "huggingface")
            try:
                self.current_settings.provider = ImageProvider(provider_str)
            except:
                self.current_settings.provider = ImageProvider.HUGGING_FACE
            
            # Model
            model_str = data.get("model", "FLUX_DEV")
            try:
                self.current_settings.model = ImageModel[model_str]
            except:
                self.current_settings.model = ImageModel.FLUX_DEV
            
            # Safety settings
            self.current_settings.sfw_only = data.get("sfw_only", True)
            
            # Sarah settings
            self.current_settings.allow_sarah_generation = data.get("allow_sarah_generation", True)
            self.current_settings.sarah_generation_cooldown = data.get("sarah_generation_cooldown", 3600)
            
            # Storage settings
            self.current_settings.save_images = data.get("save_images", True)
            self.current_settings.save_path = data.get("save_path", "./images")
            self.current_settings.organize_by_source = data.get("organize_by_source", True)
            
            # Quality settings
            quality_str = data.get("default_quality", "STANDARD")
            try:
                self.current_settings.default_quality = ImageQuality[quality_str]
            except:
                self.current_settings.default_quality = ImageQuality.STANDARD
            
        except Exception as e:
            print(f"[SETTINGS]: Error applying settings: {e}")
    
    def save(self):
        """Save current settings to file"""
        try:
            data = {
                "enabled": self.current_settings.enabled,
                "provider": self.current_settings.provider.value,
                "model": self.current_settings.model.name,
                "huggingface_api_key": self.current_settings.huggingface_api_key,
                "replicate_api_key": self.current_settings.replicate_api_key,
                "sfw_only": self.current_settings.sfw_only,
                "allow_sarah_generation": self.current_settings.allow_sarah_generation,
                "sarah_generation_cooldown": self.current_settings.sarah_generation_cooldown,
                "save_images": self.current_settings.save_images,
                "save_path": self.current_settings.save_path,
                "organize_by_source": self.current_settings.organize_by_source,
                "default_quality": self.current_settings.default_quality.name,
                "default_width": self.current_settings.default_width,
                "default_height": self.current_settings.default_height,
            }
            
            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"[SETTINGS]: Saved image generation settings")
        except Exception as e:
            print(f"[SETTINGS]: Error saving settings: {e}")
    
    # ============ UI-Friendly Getters/Setters ============
    
    def toggle_enable_generation(self) -> bool:
        """Toggle image generation on/off"""
        self.current_settings.enabled = not self.current_settings.enabled
        self.save()
        return self.current_settings.enabled
    
    def toggle_sarah_generation(self) -> bool:
        """Toggle Sarah's autonomous image generation"""
        self.current_settings.allow_sarah_generation = not self.current_settings.allow_sarah_generation
        self.save()
        return self.current_settings.allow_sarah_generation
    
    def toggle_save_images(self) -> bool:
        """Toggle image saving (can still preview without saving)"""
        self.current_settings.save_images = not self.current_settings.save_images
        self.save()
        return self.current_settings.save_images
    
    def toggle_sfw_only(self) -> bool:
        """Toggle SFW-only enforcement"""
        self.current_settings.sfw_only = not self.current_settings.sfw_only
        self.save()
        return self.current_settings.sfw_only
    
    def set_provider(self, provider: str) -> bool:
        """Set image generation provider"""
        try:
            self.current_settings.provider = ImageProvider(provider)
            self.save()
            return True
        except:
            return False
    
    def set_model(self, model: str) -> bool:
        """Set image generation model"""
        try:
            self.current_settings.model = ImageModel[model]
            self.save()
            return True
        except:
            return False
    
    def set_api_key(self, api_key: str) -> bool:
        """Deprecated: keep for compatibility"""
        try:
            self.current_settings.huggingface_api_key = api_key
            self.save()
            return True
        except:
            return False
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """Get all settings as dictionary for UI"""
        return {
            "generation_enabled": self.current_settings.enabled,
            "sarah_generation_enabled": self.current_settings.allow_sarah_generation,
            "images_save_enabled": self.current_settings.save_images,
            "sfw_only": self.current_settings.sfw_only,
            "current_provider": self.current_settings.provider.value,
            "current_model": self.current_settings.model.name,
            "default_quality": self.current_settings.default_quality.name,
            "sarah_generation_cooldown_minutes": self.current_settings.sarah_generation_cooldown / 60,
            "available_providers": [p.value for p in ImageProvider],
            "available_models": [m.name for m in ImageModel],
            "available_qualities": [q.name for q in ImageQuality],
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status for display"""
        return {
            "generation_active": self.current_settings.enabled,
            "sarah_can_generate": self.current_settings.allow_sarah_generation,
            "images_being_saved": self.current_settings.save_images,
            "nsfw_protection": "Enabled" if self.current_settings.sfw_only else "Disabled",
            "current_provider": self.current_settings.provider.value,
            "current_model": self.current_settings.model.name,
            "message": self._get_status_message(),
        }
    
    def _get_status_message(self) -> str:
        """Get human-readable status message"""
        messages = []
        
        if not self.current_settings.enabled:
            messages.append("Image generation is disabled")
        else:
            messages.append("Image generation is active")
        
        if self.current_settings.allow_sarah_generation:
            messages.append("Sarah can autonomously generate images")
        else:
            messages.append("Sarah cannot generate images autonomously")
        
        if self.current_settings.save_images:
            messages.append("Images will be saved to storage")
        else:
            messages.append("Images will only be previewed (not saved)")
        
        if self.current_settings.sfw_only:
            messages.append("SFW mode: adult content filtered")
        else:
            messages.append("No content filtering")
        
        return " | ".join(messages)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.current_settings = ImageGenerationSettings()
        self.save()
        print("[SETTINGS]: Reset to default settings")
