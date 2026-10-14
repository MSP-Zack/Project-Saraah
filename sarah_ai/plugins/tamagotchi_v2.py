"""Wrapper to expose the tamagotchi_v2 package as a plugin module for PluginManager.

PluginManager expects a single .py file under plugins/ with a `Plugin` class.
This wrapper imports the package implementation from the tamagotchi_v2 package directory.
"""
try:
    from .tamagotchi_v2 import Plugin as PluginImpl
except Exception:
    # Fallback: try importing as top-level package
    from tamagotchi_v2 import Plugin as PluginImpl

class Plugin(PluginImpl):
    pass
