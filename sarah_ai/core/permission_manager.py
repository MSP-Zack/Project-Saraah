import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class PermissionManager:
    """
    Central permission system controlling what the LLM is allowed to do.
    All capabilities are OFF by default for safety.
    """
    
    def __init__(self, config_path: str = "core/permissions.json"):
        self.config_path = config_path
        self.default_permissions = {
            "mouse_control": {
                "enabled": False,
                "description": "Move and click the mouse cursor",
                "risk": "medium",
                "icon": "mouse"
            },
            "keyboard_control": {
                "enabled": False,
                "description": "Type text and press keyboard keys",
                "risk": "medium",
                "icon": "keyboard"
            },
            "file_operations": {
                "enabled": False,
                "description": "Create, edit, delete files and folders",
                "risk": "high",
                "icon": "file"
            },
            "browser_control": {
                "enabled": False,
                "description": "Open and interact with web browser",
                "risk": "medium",
                "icon": "browser"
            },
            "app_control": {
                "enabled": False,
                "description": "Open and interact with applications (PyCharm, etc.)",
                "risk": "high",
                "icon": "app"
            },
            "screen_vision": {
                "enabled": False,
                "description": "Capture and view the screen for LLM analysis",
                "risk": "low",
                "icon": "screen"
            },
            "webcam_vision": {
                "enabled": False,
                "description": "Access webcam to see the user",
                "risk": "low",
                "icon": "camera"
            },
            "proactive_chat": {
                "enabled": True,
                "description": "Sarah can initiate conversation without user input",
                "risk": "low",
                "icon": "chat"
            },
            "vrm_actions": {
                "enabled": True,
                "description": "Control VRM model animations and expressions",
                "risk": "low",
                "icon": "user"
            },
            "system_shell": {
                "enabled": False,
                "description": "Execute shell commands (limited, no admin)",
                "risk": "critical",
                "icon": "terminal"
            },
            "memory_edit": {
                "enabled": True,
                "description": "Sarah can modify her own memory entries",
                "risk": "medium",
                "icon": "brain"
            },
            "diary_access": {
                "enabled": True,
                "description": "Sarah can read and write her private diary file",
                "risk": "medium",
                "icon": "notebook"
            },
            "image_generation": {
                "enabled": False,
                "description": "Sarah can generate or fetch images using the internet and browser tools",
                "risk": "medium",
                "icon": "image"
            }
        }
        self.permissions = self.load_permissions()
    
    def load_permissions(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                # Merge with defaults to ensure new permissions are added
                merged = self.default_permissions.copy()
                merged.update(saved)
                return merged
        return self.default_permissions.copy()
    
    def save_permissions(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.permissions, f, indent=4)
    
    def is_enabled(self, permission_key: str) -> bool:
        return self.permissions.get(permission_key, {}).get("enabled", False)
    
    def set_permission(self, permission_key: str, enabled: bool):
        if permission_key in self.permissions:
            self.permissions[permission_key]["enabled"] = enabled
            self.save_permissions()
    
    def get_all(self) -> Dict[str, Any]:
        return self.permissions
    
    def get_enabled_tools(self) -> List[str]:
        """Return list of enabled capability keys for LLM tool registration."""
        enabled = []
        for key, perm in self.permissions.items():
            if perm.get("enabled", False):
                enabled.append(key)
        return enabled
