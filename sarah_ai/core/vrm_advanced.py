"""
Advanced VRM Animation and Action System
Provides hundreds of animations, expressions, and advanced control
"""

import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import math

class AnimationCategory(Enum):
    """Categories for organizing animations"""
    IDLE = "idle"
    GREETING = "greeting"
    EMOTION = "emotion"
    ACTION = "action"
    REACTION = "reaction"
    INTERACTION = "interaction"
    DANCE = "dance"
    POSE = "pose"
    WORK = "work"
    PLAY = "play"
    COMBAT = "combat"
    SPECIAL = "special"

class ActionPriority(Enum):
    """Priority levels for action queuing"""
    BACKGROUND = 0  # Breathing, idle
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3  # Should interrupt current action

@dataclass
class VRMAnimation:
    """Definition of a single animation"""
    name: str
    category: AnimationCategory
    description: str
    duration: float
    loop: bool = False
    interrupt_idle: bool = True
    priority: ActionPriority = ActionPriority.NORMAL
    cooldown: float = 0.0  # Minimum time before repeating
    bone_targets: Dict[str, Tuple[float, float, float]] = None  # bone -> (rx, ry, rz)
    requires_permission: Optional[str] = None
    ai_reaction: Optional[str] = None

@dataclass
class VRMExpression:
    """Definition of a facial expression"""
    name: str
    description: str
    intensity: float = 1.0
    duration: float = 0.1
    blend_target: Optional[str] = None
    enable_blink: bool = True

@dataclass
class CameraTrackingData:
    """Real-time camera position tracking"""
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    rotation_x: float = 0.0  # pitch
    rotation_y: float = 0.0  # yaw
    rotation_z: float = 0.0  # roll
    fov: float = 35.0
    distance_to_model: float = 3.5
    angle_to_model: float = 0.0  # 0=front, 90=side, 180=back
    looking_at_body_part: Optional[str] = None

class VRMAdvancedEngine:
    """Advanced VRM animation and control system"""
    
    def __init__(self):
        self.animations = {}
        self.expressions = {}
        self.outfits = {}
        self.accessories = {}
        self.current_outfit = "default"
        self.camera_tracking = CameraTrackingData()
        self.action_queue = []
        self.current_animation = None
        self.current_expression = None
        self.expression_intensity = 0.0
        self.last_action_time = {}
        
        self._build_animation_library()
        self._build_expression_library()
        self._build_outfit_library()
        self._build_accessory_library()
    
    def _build_animation_library(self):
        """Build comprehensive animation library"""
        
        # IDLE & BREATHING
        self.animations["idle"] = VRMAnimation(
            "idle", AnimationCategory.IDLE, "Default idle stance",
            duration=float('inf'), loop=True, priority=ActionPriority.BACKGROUND
        )
        self.animations["breathe"] = VRMAnimation(
            "breathe", AnimationCategory.IDLE, "Deep breathing motion",
            duration=float('inf'), loop=True, priority=ActionPriority.BACKGROUND
        )
        self.animations["sway"] = VRMAnimation(
            "sway", AnimationCategory.IDLE, "Gentle side-to-side sway",
            duration=float('inf'), loop=True, priority=ActionPriority.BACKGROUND
        )
        self.animations["shift_weight"] = VRMAnimation(
            "shift_weight", AnimationCategory.IDLE, "Shift weight from foot to foot",
            duration=2.0, loop=True, priority=ActionPriority.BACKGROUND
        )
        
        # GREETINGS
        greetings = [
            ("wave", "Friendly hand wave"),
            ("bow", "Respectful bow"),
            ("salute", "Military-style salute"),
            ("thumbs_up", "Give thumbs up"),
            ("peace_sign", "Show peace sign"),
            ("wave_excited", "Enthusiastic wave with both hands"),
            ("hand_on_chest", "Hand on chest greeting"),
            ("hai", "Cute Japanese greeting"),
        ]
        for i, (name, desc) in enumerate(greetings):
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.GREETING, desc,
                duration=2.0 + (i * 0.2), loop=False, priority=ActionPriority.NORMAL
            )
        
        # EMOTIONS
        emotions = [
            ("happy", "Joy, excitement", 0.5),
            ("sad", "Sadness, crying", 3.0),
            ("angry", "Anger, frustration", 2.0),
            ("surprised", "Shock, surprise", 1.5),
            ("confused", "Confusion, uncertainty", 2.5),
            ("embarrassed", "Shyness, embarrassment", 2.0),
            ("proud", "Pride, confidence", 2.0),
            ("afraid", "Fear, nervousness", 2.0),
            ("thinking", "Contemplation, thinking", 3.0),
            ("smug", "Smug, confident smile", 1.5),
            ("bored", "Boredom, disinterest", 2.0),
            ("excited", "Extreme excitement", 1.5),
            ("calm", "Peace, tranquility", float('inf')),
            ("determined", "Resolve, determination", 2.0),
            ("dizzy", "Dizziness, confusion", 3.0),
            ("crying", "Tears, crying", 4.0),
        ]
        for name, desc, duration in emotions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.EMOTION, desc,
                duration=duration, loop=False, priority=ActionPriority.NORMAL
            )
        
        # ACTIONS
        actions = [
            ("punch", "Forward punch", 0.8, ActionPriority.HIGH),
            ("kick", "Forward kick", 1.0, ActionPriority.HIGH),
            ("spin_kick", "Spin and kick", 1.2, ActionPriority.HIGH),
            ("stomp", "Stomp foot angrily", 0.6, ActionPriority.NORMAL),
            ("slip", "Slip and fall", 1.5, ActionPriority.HIGH),
            ("trip", "Trip and stumble", 1.2, ActionPriority.HIGH),
            ("faint", "Dramatic faint/collapse", 3.0, ActionPriority.HIGH),
            ("stretch", "Body stretch", 2.0, ActionPriority.NORMAL),
            ("yawn", "Yawn with exhaustion", 2.5, ActionPriority.NORMAL),
            ("sneeze", "Sneeze gesture", 1.0, ActionPriority.NORMAL),
            ("cough", "Coughing motion", 1.5, ActionPriority.NORMAL),
            ("doubt", "Doubt/uncertainty gesture", 1.5, ActionPriority.NORMAL),
            ("shrug", "Shrug shoulders", 1.0, ActionPriority.NORMAL),
            ("nod", "Nod head yes", 1.0, ActionPriority.NORMAL),
            ("shake_head", "Shake head no", 1.0, ActionPriority.NORMAL),
        ]
        for name, desc, duration, priority in actions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.ACTION, desc,
                duration=duration, loop=False, priority=priority
            )
        
        # INTERACTIONS & AFFECTION
        interactions = [
            ("hug", "Open arms for hug", 3.0),
            ("kiss", "Blow a kiss", 2.0),
            ("hold_hands", "Offer hand to hold", 2.0),
            ("pat_head_user", "Pat user's head affectionately", 1.5),
            ("wink", "Wink at camera", 0.8),
            ("wink_left", "Wink left eye", 0.6),
            ("wink_right", "Wink right eye", 0.6),
            ("blush", "Embarrassed blush", 2.0),
            ("coy_smile", "Coy, playful smile", 1.5),
            ("touch_face", "Touch own face shyly", 1.2),
            ("hide_face", "Hide face behind hands", 2.0),
            ("catwalk", "Confident catwalk pose", 2.5),
            ("pole_dance_prep", "Prepare for pole dance", 3.0),
            ("kneel", "Kneel down", 2.0),
            ("sit_lap", "Sit on your lap", 3.0),
        ]
        for name, desc, duration in interactions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.INTERACTION, desc,
                duration=duration, loop=False, priority=ActionPriority.NORMAL
            )
        
        # DANCES
        dances = [
            ("dance_cute", "Cute dance", 4.0, "cute"),
            ("dance_seductive", "Seductive dance", 5.0, "seductive"),
            ("dance_silly", "Silly/goofy dance", 4.0, "silly"),
            ("dance_energetic", "High-energy dance", 3.5, "energetic"),
            ("dance_slow", "Slow, graceful dance", 5.5, "graceful"),
            ("dance_hip_hop", "Hip-hop style dance", 4.0, "hip-hop"),
            ("headbang", "Headbang to music", 3.0, "metal"),
            ("dance_popular_1", "Popular dance style 1", 4.0, None),
            ("dance_popular_2", "Popular dance style 2", 4.0, None),
            ("dance_vtuber", "VTuber signature dance", 4.5, "vtuber"),
        ]
        for name, desc, duration, style in dances:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.DANCE, desc,
                duration=duration, loop=False, priority=ActionPriority.NORMAL
            )
        
        # WORK/FOCUSED ACTIONS
        work_actions = [
            ("read_book", "Reading from a book", 4.0),
            ("write_paper", "Writing on paper", 3.0),
            ("type_keyboard", "Typing on keyboard", float('inf')),
            ("paint", "Painting motion", 3.0),
            ("draw", "Drawing/sketching", 3.0),
            ("cook", "Cooking motion", 3.0),
            ("clean", "Cleaning motion", 2.5),
            ("fix_device", "Repairing electronics", 3.5),
            ("sew", "Sewing motion", 3.0),
            ("play_instrument_guitar", "Playing guitar", 4.0),
            ("play_instrument_piano", "Playing piano", 4.0),
            ("play_instrument_violin", "Playing violin", 4.0),
            ("play_instrument_flute", "Playing flute", 3.5),
            ("conduct", "Conducting orchestra", 4.0),
        ]
        for name, desc, duration in work_actions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.WORK, desc,
                duration=duration, loop=False, priority=ActionPriority.NORMAL
            )
        
        # PLAY & FUN
        play_actions = [
            ("jump", "Excited jump", 1.0),
            ("hop", "Little hop", 0.8),
            ("run_in_place", "Running in place", 2.0),
            ("skip", "Skip happily", 2.0),
            ("cartwheel", "Do a cartwheel", 2.5),
            ("backflip", "Backflip", 1.5),
            ("roll", "Roll on ground", 2.0),
            ("crawl", "Crawl on hands and knees", 2.5),
            ("play_peek_a_boo", "Peak-a-boo gesture", 1.5),
            ("juggle", "Juggling motion", 3.0),
            ("throw_ball", "Throw a ball", 1.2),
            ("catch", "Catch motion", 1.0),
        ]
        for name, desc, duration in play_actions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.PLAY, desc,
                duration=duration, loop=False, priority=ActionPriority.NORMAL
            )
        
        # COMBAT (FOR GAME INTERACTIONS)
        combat_actions = [
            ("ready_stance", "Combat ready stance", 1.0),
            ("dodge_left", "Dodge left", 0.8),
            ("dodge_right", "Dodge right", 0.8),
            ("block", "Blocking stance", 1.0),
            ("slash", "Sword slash", 1.0),
            ("stab", "Sword stab", 0.8),
            ("swing_hammer", "Swing heavy hammer", 1.2),
            ("shoot_bow", "Draw and shoot bow", 1.5),
            ("cast_magic", "Cast magic spell", 1.5),
            ("grab", "Grab opponent", 1.0),
            ("defend", "Defensive pose", 1.0),
            ("victory", "Victory pose", 2.0),
            ("defeat", "Defeat pose", 3.0),
        ]
        for name, desc, duration in combat_actions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.COMBAT, desc,
                duration=duration, loop=False, priority=ActionPriority.NORMAL
            )
        
        # SPECIAL/REACTIONS TO CAMERA
        special_actions = [
            ("notice_camera", "Notice camera and look at it", 1.5),
            ("blush_embarrassed", "Blush after being caught", 2.0),
            ("turn_around_angry", "Turn around angrily at viewer", 1.5),
            ("cover_self", "Self-conscious cover", 1.5),
            ("accuse_user", "Point finger accusingly", 1.5),
            ("smile_confident", "Give confident smile", 1.5),
            ("tease", "Tease the user", 2.0),
            ("ignore_user", "Turn away, ignore", 2.5),
            ("beckon", "Beckon user to come closer", 1.5),
            ("lean_forward", "Lean in close", 1.5),
            ("back_away", "Back away nervously", 1.5),
        ]
        for name, desc, duration in special_actions:
            self.animations[name] = VRMAnimation(
                name, AnimationCategory.SPECIAL, desc,
                duration=duration, loop=False, priority=ActionPriority.HIGH
            )
    
    def _build_expression_library(self):
        """Build comprehensive facial expression library"""
        
        base_expressions = [
            "neutral", "happy", "sad", "angry", "surprised", 
            "confused", "disgusted", "fearful", "content",
            "excited", "calm", "embarrassed", "proud", "smug",
            "annoyed", "concerned", "skeptical", "mischievous"
        ]
        
        for expr in base_expressions:
            self.expressions[expr] = VRMExpression(expr, f"{expr.title()} expression")
        
        # Blend expressions for more nuance
        for expr in base_expressions:
            for i in range(1, 4):
                intensity = i * 0.25
                self.expressions[f"{expr}_intense"] = VRMExpression(
                    f"{expr}_intense", f"Intense {expr} expression", intensity=intensity
                )
    
    def _build_outfit_library(self):
        """Build outfit/avatar collection"""
        
        self.outfits = {
            "default": {
                "name": "Default Sarah",
                "description": "Default outfit",
                "model_path": "/static/models/sarah.vrm",
                "color_scheme": "pink",
                "tags": ["default"],
            },
            "school_uniform": {
                "name": "School Uniform",
                "description": "Classic anime school girl uniform",
                "model_path": "/static/models/outfits/school_uniform.vrm",
                "color_scheme": "blue",
                "tags": ["cute", "casual", "school"],
            },
            "casual_dress": {
                "name": "Casual Dress",
                "description": "Comfy casual dress",
                "model_path": "/static/models/outfits/casual_dress.vrm",
                "color_scheme": "purple",
                "tags": ["casual", "comfortable"],
            },
            "formal_dress": {
                "name": "Formal Dress",
                "description": "Elegant formal gown",
                "model_path": "/static/models/outfits/formal_dress.vrm",
                "color_scheme": "white",
                "tags": ["elegant", "formal"],
            },
            "maid_outfit": {
                "name": "Maid Outfit",
                "description": "Cute maid costume",
                "model_path": "/static/models/outfits/maid_outfit.vrm",
                "color_scheme": "black",
                "tags": ["cute", "costume"],
            },
            "bunny_girl": {
                "name": "Bunny Girl",
                "description": "Playful bunny costume",
                "model_path": "/static/models/outfits/bunny_girl.vrm",
                "color_scheme": "white",
                "tags": ["costume", "playful"],
            },
            "vampire": {
                "name": "Vampire",
                "description": "Elegant vampire outfit",
                "model_path": "/static/models/outfits/vampire.vrm",
                "color_scheme": "red",
                "tags": ["costume", "gothic"],
            },
            "angel": {
                "name": "Angel",
                "description": "Angelic outfit with wings",
                "model_path": "/static/models/outfits/angel.vrm",
                "color_scheme": "white",
                "tags": ["costume", "angelic"],
            },
            "demon": {
                "name": "Demon",
                "description": "Playful demon costume",
                "model_path": "/static/models/outfits/demon.vrm",
                "color_scheme": "red",
                "tags": ["costume", "demonic"],
            },
            "sporty": {
                "name": "Sporty Wear",
                "description": "Athletic sportswear",
                "model_path": "/static/models/outfits/sporty.vrm",
                "color_scheme": "cyan",
                "tags": ["athletic", "casual"],
            },
            "swimwear": {
                "name": "Swimwear",
                "description": "Beach/pool outfit",
                "model_path": "/static/models/outfits/swimwear.vrm",
                "color_scheme": "cyan",
                "tags": ["beach", "casual"],
            },
            "winter_coat": {
                "name": "Winter Coat",
                "description": "Cozy winter outfit",
                "model_path": "/static/models/outfits/winter_coat.vrm",
                "color_scheme": "white",
                "tags": ["winter", "casual"],
            },
            "pajamas": {
                "name": "Pajamas",
                "description": "Cute sleepwear",
                "model_path": "/static/models/outfits/pajamas.vrm",
                "color_scheme": "pink",
                "tags": ["sleepwear", "cute"],
            },
            "mecha": {
                "name": "Mecha Suit",
                "description": "Combat mecha outfit",
                "model_path": "/static/models/outfits/mecha.vrm",
                "color_scheme": "silver",
                "tags": ["mecha", "combat"],
            },
            "magical_girl": {
                "name": "Magical Girl",
                "description": "Magical girl transformation",
                "model_path": "/static/models/outfits/magical_girl.vrm",
                "color_scheme": "pink",
                "tags": ["magical", "costume"],
            },
        }
    
    def _build_accessory_library(self):
        """Build accessory collection"""
        
        self.accessories = {
            # Weapons
            "sword": {"name": "Sword", "slot": "hand", "type": "weapon"},
            "katana": {"name": "Katana", "slot": "hand", "type": "weapon"},
            "bow": {"name": "Bow", "slot": "hand", "type": "weapon"},
            "staff": {"name": "Magic Staff", "slot": "hand", "type": "weapon"},
            "wand": {"name": "Magic Wand", "slot": "hand", "type": "weapon"},
            "gun": {"name": "Gun", "slot": "hand", "type": "weapon"},
            
            # Head accessories
            "headphones": {"name": "Headphones", "slot": "head", "type": "gear"},
            "crown": {"name": "Crown", "slot": "head", "type": "accessory"},
            "halo": {"name": "Halo", "slot": "head", "type": "accessory"},
            "horn": {"name": "Horn", "slot": "head", "type": "accessory"},
            "cat_ears": {"name": "Cat Ears", "slot": "head", "type": "accessory"},
            "rabbit_ears": {"name": "Rabbit Ears", "slot": "head", "type": "accessory"},
            
            # Items
            "book": {"name": "Book", "slot": "hand", "type": "prop"},
            "coffee_cup": {"name": "Coffee Cup", "slot": "hand", "type": "prop"},
            "microphone": {"name": "Microphone", "slot": "hand", "type": "prop"},
            "phone": {"name": "Smartphone", "slot": "hand", "type": "prop"},
            "tablet": {"name": "Tablet", "slot": "hand", "type": "prop"},
            
            # Auras/effects
            "sparkle_aura": {"name": "Sparkle Aura", "slot": "body", "type": "effect"},
            "flame_aura": {"name": "Flame Aura", "slot": "body", "type": "effect"},
            "shadow_aura": {"name": "Shadow Aura", "slot": "body", "type": "effect"},
        }
    
    def update_camera_tracking(self, data: Dict) -> CameraTrackingData:
        """Update real-time camera position and tracking"""
        self.camera_tracking = CameraTrackingData(
            position_x=data.get('position_x', 0),
            position_y=data.get('position_y', 0),
            position_z=data.get('position_z', 0),
            rotation_x=data.get('rotation_x', 0),
            rotation_y=data.get('rotation_y', 0),
            rotation_z=data.get('rotation_z', 0),
            fov=data.get('fov', 35),
            distance_to_model=data.get('distance_to_model', 3.5),
            angle_to_model=data.get('angle_to_model', 0),
            looking_at_body_part=data.get('looking_at_body_part'),
        )
        return self.camera_tracking
    
    def get_ai_aware_context(self) -> Dict:
        """Get context for LLM about camera position and viewer perspective"""
        return {
            'camera_position': {
                'x': self.camera_tracking.position_x,
                'y': self.camera_tracking.position_y,
                'z': self.camera_tracking.position_z,
            },
            'camera_angle': self.camera_tracking.angle_to_model,
            'distance': self.camera_tracking.distance_to_model,
            'looking_at': self.camera_tracking.looking_at_body_part or 'face',
            'viewer_position': self._get_viewer_position_description(),
            'viewer_intent': self._analyze_viewer_intent(),
        }
    
    def _get_viewer_position_description(self) -> str:
        """Describe viewer position relative to model"""
        angle = self.camera_tracking.angle_to_model
        
        if angle < 30 or angle > 330:
            return "directly in front of me"
        elif 30 <= angle < 90:
            return "to my left side"
        elif 90 <= angle < 150:
            return "to my left"
        elif 150 <= angle < 210:
            return "directly behind me"
        elif 210 <= angle < 270:
            return "to my right"
        elif 270 <= angle < 330:
            return "to my right side"
        else:
            return "somewhere around me"
    
    def _analyze_viewer_intent(self) -> str:
        """Analyze potential viewer intent based on camera position"""
        y = self.camera_tracking.position_y
        body_part = self.camera_tracking.looking_at_body_part or "face"
        
        # Determine if looking up or down
        if y < -0.5:
            if "leg" in body_part or "foot" in body_part:
                return "suspicious_upskirt"
            return "looking_down"
        elif y < 0.5:
            return "looking_at_legs"
        elif y < 1.3:
            return "looking_at_torso"
        elif y < 1.6:
            return "looking_at_chest"
        else:
            return "looking_at_face"
    
    def get_animation(self, name: str) -> Optional[VRMAnimation]:
        """Get animation by name"""
        return self.animations.get(name.lower())
    
    def get_expression(self, name: str) -> Optional[VRMExpression]:
        """Get expression by name"""
        return self.expressions.get(name.lower())
    
    def get_outfit(self, name: str) -> Optional[Dict]:
        """Get outfit by name"""
        return self.outfits.get(name.lower())
    
    def get_all_animations(self) -> Dict[str, Dict]:
        """Return all animations organized by category"""
        result = {}
        for cat in AnimationCategory:
            result[cat.value] = {}
        
        for name, anim in self.animations.items():
            cat = anim.category.value
            result[cat][name] = {
                "name": anim.name,
                "description": anim.description,
                "duration": anim.duration,
                "loop": anim.loop,
                "priority": anim.priority.value,
            }
        
        return result
    
    def get_all_expressions(self) -> Dict[str, Dict]:
        """Return all expressions"""
        result = {}
        for name, expr in self.expressions.items():
            result[name] = {
                "name": expr.name,
                "description": expr.description,
                "intensity": expr.intensity,
            }
        return result
    
    def get_all_outfits(self) -> Dict[str, Dict]:
        """Return all available outfits"""
        return self.outfits
    
    def get_all_accessories(self) -> Dict[str, Dict]:
        """Return all available accessories"""
        return self.accessories
    
    def queui_action(self, name: str, priority: ActionPriority = ActionPriority.NORMAL) -> bool:
        """Queue an action for playback"""
        anim = self.get_animation(name)
        if not anim:
            return False
        
        # Check cooldown
        if name in self.last_action_time:
            elapsed = 0  # Would be calculated from actual time
            if elapsed < anim.cooldown:
                return False
        
        self.action_queue.append({
            "name": name,
            "priority": priority,
            "animation": anim
        })
        
        return True
    
    def get_stats(self) -> Dict:
        """Get statistics about the VRM system"""
        return {
            "total_animations": len(self.animations),
            "animations_by_category": {
                cat.value: len([a for a in self.animations.values() if a.category == cat])
                for cat in AnimationCategory
            },
            "total_expressions": len(self.expressions),
            "total_outfits": len(self.outfits),
            "total_accessories": len(self.accessories),
            "current_outfit": self.current_outfit,
            "action_queue_length": len(self.action_queue),
        }
