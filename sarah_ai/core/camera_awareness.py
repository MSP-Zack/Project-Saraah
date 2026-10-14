"""
Real-time Camera Awareness System
Tracks viewer position and enables VRM model awareness of viewer location
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Vector3:
    """3D vector"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def distance_to(self, other: 'Vector3') -> float:
        """Calculate distance to another point"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def angle_to(self, other: 'Vector3') -> float:
        """Calculate angle to another point (in degrees)"""
        dx = other.x - self.x
        dz = other.z - self.z
        angle = math.atan2(dx, dz)
        return math.degrees(angle) % 360
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {'x': self.x, 'y': self.y, 'z': self.z}

@dataclass
class Rotation:
    """3D rotation (Euler angles in radians)"""
    x: float = 0.0  # pitch (up/down)
    y: float = 0.0  # yaw (left/right)
    z: float = 0.0  # roll (tilt)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'x_deg': math.degrees(self.x),
            'y_deg': math.degrees(self.y),
            'z_deg': math.degrees(self.z),
        }

class CameraAwarenessSystem:
    """
    Tracks camera position in real-time and provides the VRM model 
    with awareness of viewer location and perspective
    """
    
    def __init__(self, model_position: Vector3 = None, model_height: float = 1.6):
        self.model_position = model_position or Vector3(0, 0, 0)
        self.model_height = model_height
        
        # Camera state
        self.camera_position = Vector3(0, 1.4, 3.5)
        self.camera_rotation = Rotation()
        self.camera_fov = 35
        
        # Calculated values
        self.distance = 3.5
        self.angle_horizontal = 0  # 0 = front, 90 = left, 180 = back, 270 = right
        self.angle_vertical = 0  # 0 = level, positive = looking down, negative = looking up
        self.looking_at_body_part = "face"
        
        # Tracking history for smoothing
        self.position_history = []
        self.smoothing_factor = 0.3  # Lower = smoother but slower response
        self.max_history = 5
    
    def update_camera_position(self, x: float, y: float, z: float):
        """Update camera position"""
        new_pos = Vector3(x, y, z)
        
        # Apply smoothing
        if self.position_history:
            prev = self.position_history[-1]
            smoothed_x = prev.x + (new_pos.x - prev.x) * self.smoothing_factor
            smoothed_y = prev.y + (new_pos.y - prev.y) * self.smoothing_factor
            smoothed_z = prev.z + (new_pos.z - prev.z) * self.smoothing_factor
            new_pos = Vector3(smoothed_x, smoothed_y, smoothed_z)
        
        self.camera_position = new_pos
        self.position_history.append(new_pos)
        
        # Keep history size limited
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
        
        self._recalculate_tracking()
    
    def update_camera_rotation(self, pitch: float, yaw: float, roll: float = 0):
        """Update camera rotation (angles in radians)"""
        self.camera_rotation = Rotation(pitch, yaw, roll)
        self._recalculate_tracking()
    
    def update_camera_fov(self, fov: float):
        """Update camera field of view (in degrees)"""
        self.camera_fov = fov
    
    def _recalculate_tracking(self):
        """Recalculate tracking metrics based on current positions"""
        # Calculate distance
        self.distance = self.camera_position.distance_to(self.model_position)
        
        # Calculate horizontal angle (yaw)
        self.angle_horizontal = self.model_position.angle_to(self.camera_position)
        
        # Calculate vertical angle (pitch)
        dy = self.camera_position.y - self.model_position.y
        horizontal_dist = math.sqrt(
            (self.camera_position.x - self.model_position.x)**2 +
            (self.camera_position.z - self.model_position.z)**2
        )
        self.angle_vertical = math.atan2(dy, horizontal_dist)
        
        # Determine what body part is being looked at
        self._determine_body_part()
    
    def _determine_body_part(self):
        """Determine which body part the camera is looking at"""
        # Relative camera height compared to model
        rel_height = self.camera_position.y - self.model_position.y
        
        # Simple sphere-cast raycasting based on relative height
        model_top = self.model_position.y + self.model_height
        model_bottom = self.model_position.y
        
        if rel_height > model_top - 0.2:
            self.looking_at_body_part = "head"
        elif rel_height > model_top - 0.4:
            self.looking_at_body_part = "face"
        elif rel_height > model_top - 0.6:
            self.looking_at_body_part = "hair"
        elif rel_height > (model_top - model_bottom) * 0.7:  # Upper body
            self.looking_at_body_part = "shoulder"
        elif rel_height > (model_top - model_bottom) * 0.5:  # Middle
            self.looking_at_body_part = "chest"
        elif rel_height > (model_top - model_bottom) * 0.3:  # Lower mid
            self.looking_at_body_part = "stomach"
        elif rel_height > (model_top - model_bottom) * 0.1:  # Hip area
            self.looking_at_body_part = "hip"
        else:
            self.looking_at_body_part = "leg"
        
        # Check for upskirt perspective (camera very low and below model)
        if rel_height < model_bottom - 0.3 and self.distance < 2.0:
            if 45 <= (self.angle_horizontal % 360) <= 315:  # Not looking from pure sides
                self.looking_at_body_part = "upskirt"
    
    def get_relative_position_description(self) -> str:
        """Get natural language description of viewer position"""
        angle = self.angle_horizontal
        
        # Normalize angle to 0-360
        angle = angle % 360
        
        descriptions = []
        
        # Horizontal position
        if angle < 22.5 or angle >= 337.5:
            descriptions.append("directly in front")
        elif 22.5 <= angle < 67.5:
            descriptions.append("to my front-left")
        elif 67.5 <= angle < 112.5:
            descriptions.append("to my left")
        elif 112.5 <= angle < 157.5:
            descriptions.append("to my back-left")
        elif 157.5 <= angle < 202.5:
            descriptions.append("directly behind")
        elif 202.5 <= angle < 247.5:
            descriptions.append("to my back-right")
        elif 247.5 <= angle < 292.5:
            descriptions.append("to my right")
        elif 292.5 <= angle < 337.5:
            descriptions.append("to my front-right")
        
        # Vertical position
        if self.angle_vertical > 0.3:
            descriptions.append("looking down")
        elif self.angle_vertical < -0.3:
            descriptions.append("looking up")
        else:
            descriptions.append("at eye level")
        
        # Distance
        if self.distance < 1.5:
            descriptions.append("very close")
        elif self.distance < 2.5:
            descriptions.append("close")
        elif self.distance < 4.0:
            descriptions.append("at normal distance")
        elif self.distance < 6.0:
            descriptions.append("far away")
        else:
            descriptions.append("very far away")
        
        return ", ".join(descriptions)
    
    def get_viewer_intent_score(self) -> Dict[str, float]:
        """
        Analyze viewer intent based on camera position.
        Returns scores for different intent types (0-1)
        """
        scores = {
            'suspicious': 0.0,
            'intimate': 0.0,
            'confrontational': 0.0,
            'friendly': 0.0,
            'dominant': 0.0,
            'submissive': 0.0,
            'curious': 0.0,
        }
        
        # Suspicious behavior (upskirt, extreme angles)
        if self.looking_at_body_part == "upskirt":
            scores['suspicious'] = 1.0
        elif self.looking_at_body_part in ["leg", "hip"]:
            scores['suspicious'] = 0.7
        
        # Intimate (close distance, looking at face/chest)
        if self.distance < 2.0 and self.looking_at_body_part in ["face", "chest"]:
            scores['intimate'] = 0.8
        elif self.distance < 1.5:
            scores['intimate'] = 0.9
        
        # Confrontational (behind or below at distance)
        if self.angle_horizontal > 135 and self.angle_horizontal < 225:
            scores['confrontational'] = 0.6
        
        # Friendly (front, normal distance, level)
        if self.angle_horizontal < 45 or self.angle_horizontal > 315:
            scores['friendly'] = 0.7
            if self.distance > 2.0 and self.distance < 4.0:
                scores['friendly'] = 0.9
        
        # Dominant (above, behind)
        if self.angle_vertical < -0.4 or (self.angle_horizontal > 160 and self.angle_horizontal < 200):
            scores['dominant'] = 0.7
        
        # Submissive (below, in front)
        if self.angle_vertical > 0.4:
            scores['submissive'] = 0.7
        
        # Curious (side angles, medium distance)
        if (45 < self.angle_horizontal < 135 or 225 < self.angle_horizontal < 315):
            scores['curious'] = 0.8
        
        return scores
    
    def should_model_react_to_camera(self) -> Tuple[bool, str]:
        """
        Determine if model should actively react to camera position.
        Returns (should_react, reaction_type)
        """
        # If viewer is looking at suspicious areas, react strongly
        if self.looking_at_body_part == "upskirt":
            return True, "caught_upskirt_peek"
        
        # If viewer is very close, model should notice
        if self.distance < 1.5:
            intent_scores = self.get_viewer_intent_score()
            if intent_scores['intimate'] > 0.7:
                return True, "notice_intimate_distance"
            elif intent_scores['confrontational'] > 0.6:
                return True, "notice_confrontation"
        
        # If viewer moves from front to back quickly, model should notice
        if self.angle_horizontal > 135 and self.angle_horizontal < 225:
            if self.distance < 3.0:
                return True, "notice_behind"
        
        return False, "no_reaction"
    
    def get_look_target_for_model(self) -> Vector3:
        """
        Calculate where the model should look based on camera position.
        This is used for the model to look at or away from the camera.
        """
        # Simple version: have model look toward or away from camera
        # More sophisticated version could track camera movements
        
        # Default look direction (slightly offset to avoid perfect alignment)
        look_offset = Vector3(0, 0.1, 0)
        
        if self.angle_horizontal < 45 or self.angle_horizontal > 315:
            # Viewer is in front - look at them
            return self.camera_position
        elif 45 <= self.angle_horizontal < 135:
            # Viewer is to left-back - can look at them
            return self.camera_position
        elif 135 <= self.angle_horizontal < 225:
            # Viewer is directly behind - look away or over shoulder
            return Vector3(
                self.model_position.x,
                self.model_position.y + 1.2,
                self.model_position.z + 2
            )
        else:
            # Viewer is to right-back - can look at them
            return self.camera_position
    
    def get_tracking_data(self) -> Dict:
        """Export all tracking data as dictionary"""
        intent_scores = self.get_viewer_intent_score()
        should_react, reaction_type = self.should_model_react_to_camera()
        
        return {
            "camera": {
                "position": self.camera_position.to_dict(),
                "rotation": self.camera_rotation.to_dict(),
                "fov": self.camera_fov,
            },
            "tracking": {
                "distance": self.distance,
                "angle_horizontal": self.angle_horizontal,
                "angle_vertical": math.degrees(self.angle_vertical),
                "body_part_viewed": self.looking_at_body_part,
                "relative_position": self.get_relative_position_description(),
            },
            "intent": {
                "scores": intent_scores,
                "primary_intent": max(intent_scores.items(), key=lambda x: x[1])[0],
            },
            "reaction": {
                "should_react": should_react,
                "reaction_type": reaction_type,
            },
            "model_look_target": self.get_look_target_for_model().to_dict(),
        }
