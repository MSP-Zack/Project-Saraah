import cv2
import base64
import asyncio
import numpy as np
from typing import Optional, Dict

class VisionEngine:
    """
    Enhanced vision engine supporting both webcam and screen capture.
    Provides frames to the LLM for visual understanding.
    """
    
    def __init__(self):
        self.cap = None
        self.is_webcam_active = False
        self.last_frame = None
        self.frame_count = 0
    
    def start_webcam(self, device_index: int = 0) -> bool:
        """Start the webcam capture."""
        try:
            self.cap = cv2.VideoCapture(device_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.is_webcam_active = self.cap.isOpened()
            return self.is_webcam_active
        except Exception as e:
            print(f"[VISION]: Webcam failed to start: {e}")
            return False
    
    def stop_webcam(self):
        """Stop the webcam capture."""
        if self.cap:
            self.cap.release()
        self.is_webcam_active = False
    
    def capture_frame(self, quality: int = 65, max_size: int = 640) -> Optional[str]:
        """
        Capture a single frame and return base64 encoded JPEG.
        Returns None if capture fails.
        """
        if not self.is_webcam_active or self.cap is None:
            # Try to auto-start
            if not self.start_webcam():
                return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        self.frame_count += 1
        
        # Resize if too large
        h, w = frame.shape[:2]
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        self.last_frame = frame
        return base64.b64encode(buffer).decode('utf-8')
    
    async def capture_frame_async(self, quality: int = 65) -> Optional[str]:
        """Async wrapper for capture_frame."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.capture_frame, quality)
    
    def get_camera_info(self) -> Dict:
        """Get camera settings and status."""
        if self.cap and self.is_webcam_active:
            w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            return {
                "active": True,
                "width": int(w),
                "height": int(h),
                "fps": int(fps),
                "frames_captured": self.frame_count
            }
        return {"active": False, "width": 0, "height": 0, "fps": 0, "frames_captured": 0}
    
    def __del__(self):
        self.stop_webcam()
