import os
import importlib.util
import json
import asyncio
from typing import Dict, List, Any, Optional

class PluginManager:
    """
    Dynamic plugin system for Sarah.
    Loads and manages plugins that extend functionality.
    Each plugin can register tools, handlers, and UI components.
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Any] = {}
        self.hooks: Dict[str, List] = {}
        
        os.makedirs(plugins_dir, exist_ok=True)
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin by name."""
        plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
        if not os.path.exists(plugin_path):
            return False
        
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'Plugin'):
                plugin_instance = module.Plugin()
                self.plugins[plugin_name] = plugin_instance
                print(f"[PLUGIN]: Loaded '{plugin_name}' - {plugin_instance.get_info()}")
                return True
            return False
        except Exception as e:
            print(f"[PLUGIN]: Failed to load '{plugin_name}': {e}")
            return False
    
    def unload_plugin(self, plugin_name: str):
        """Unload a plugin."""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            if hasattr(plugin, 'on_unload'):
                plugin.on_unload()
            del self.plugins[plugin_name]
    
    def get_plugin(self, name: str) -> Optional[Any]:
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict]:
        """List all loaded plugins with their info."""
        return [{"name": name, "info": p.get_info()} for name, p in self.plugins.items()]
    
    def call_hook(self, hook_name: str, *args, **kwargs):
        """Call a hook on all plugins that implement it."""
        results = []
        for plugin in self.plugins.values():
            if hasattr(plugin, hook_name):
                method = getattr(plugin, hook_name)
                try:
                    result = method(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"[PLUGIN]: Hook error in {plugin}: {e}")
        return results
    
    async def call_hook_async(self, hook_name: str, *args, **kwargs):
        """Async version of call_hook."""
        results = []
        for plugin in self.plugins.values():
            if hasattr(plugin, hook_name):
                method = getattr(plugin, hook_name)
                try:
                    if asyncio.iscoroutinefunction(method):
                        result = await method(*args, **kwargs)
                    else:
                        result = method(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"[PLUGIN]: Async hook error: {e}")
        return results
