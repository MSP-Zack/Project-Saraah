import base64
import io
import asyncio
from PIL import Image
import mss
import numpy as np

class ScreenEngine:
    """
    Captures screen content for LLM vision analysis.
    Uses mss for fast, cross-platform screen capture.
    Supports full screen and region capture.
    """
    
    def __init__(self):
        self.sct = mss.mss()
        self.last_capture = None
        self.capture_count = 0
    
    async def capture_screen(self, monitor_index: int = 0, quality: int = 50, max_width: int = 1280) -> str:
        """
        Capture screen and return base64 encoded JPEG.
        Lower quality for faster transmission to LLM.
        """
        try:
            loop = asyncio.get_event_loop()
            # Run blocking capture in executor
            img_b64 = await loop.run_in_executor(None, self._capture_sync, monitor_index, quality, max_width)
            self.capture_count += 1
            return img_b64
        except Exception as e:
            print(f"[SCREEN]: Capture failed: {e}")
            return None
    
    def _capture_sync(self, monitor_index: int, quality: int, max_width: int) -> str:
        monitors = self.sct.monitors
        if monitor_index >= len(monitors):
            monitor_index = 0
        
        monitor = monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Resize if too large
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        
        # Compress to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        
        self.last_capture = img
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    async def capture_region(self, left: int, top: int, width: int, height: int, quality: int = 60) -> str:
        """Capture a specific screen region."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._capture_region_sync, left, top, width, height, quality)
        except Exception as e:
            print(f"[SCREEN]: Region capture failed: {e}")
            return None
    
    def _capture_region_sync(self, left, top, width, height, quality) -> str:
        region = {"left": left, "top": top, "width": width, "height": height}
        screenshot = self.sct.grab(region)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def get_monitor_list(self) -> list:
        """Get list of available monitors."""
        monitors = []
        for i, m in enumerate(self.sct.monitors[1:], 1):
            monitors.append({
                "index": i,
                "width": m["width"],
                "height": m["height"],
                "left": m["left"],
                "top": m["top"]
            })
        return monitors
    
    def get_capture_count(self) -> int:
        return self.capture_count
