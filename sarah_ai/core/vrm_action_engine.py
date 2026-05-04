import json
from typing import Dict, List, Optional
from pathlib import Path

class VRMActionEngine:
    """
    Comprehensive VRM action and animation system.
    Defines all possible VRM animations, expressions, and body interactions.
    Provides the LLM with a structured list of what it can make the VRM do.
    """
    
    def __init__(self):
        # Core expression presets
        self.expressions = {
            "happy": {"description": "Smiling, joyful expression", "vrm_expression": "happy", "value": 1.0},
            "sad": {"description": "Sad, teary-eyed expression", "vrm_expression": "sad", "value": 1.0},
            "angry": {"description": "Angry, furrowed brows", "vrm_expression": "angry", "value": 1.0},
            "relaxed": {"description": "Calm, peaceful expression", "vrm_expression": "relaxed", "value": 1.0},
            "surprised": {"description": "Wide-eyed shock", "vrm_expression": "surprised", "value": 1.0},
            "neutral": {"description": "Default neutral face", "vrm_expression": "neutral", "value": 1.0},
            "blink": {"description": "Blink eyes", "vrm_expression": "blink", "value": 1.0},
            "blinkLeft": {"description": "Wink left eye", "vrm_expression": "blinkLeft", "value": 1.0},
            "blinkRight": {"description": "Wink right eye", "vrm_expression": "blinkRight", "value": 1.0},
        }
        
        # Full body animations
        self.animations = {
            "idle": {"description": "Standing still, breathing", "type": "loop", "priority": 0},
            "breathe": {"description": "Deep breathing animation", "type": "loop", "priority": 0},
            "look_around": {"description": "Eyes looking around idly", "type": "loop", "priority": 0},
            "kiss": {"description": "Blow a kiss", "type": "oneshot", "duration": 2.0, "priority": 3},
            "hug": {"description": "Open arms for a hug", "type": "oneshot", "duration": 3.0, "priority": 3},
            "punch": {"description": "Playful punch forward", "type": "oneshot", "duration": 0.8, "priority": 2},
            "kick": {"description": "Playful kick", "type": "oneshot", "duration": 1.0, "priority": 2},
            "wave": {"description": "Friendly hand wave", "type": "oneshot", "duration": 2.0, "priority": 2},
            "dance": {"description": "Cute dance loop", "type": "loop", "priority": 2},
            "jump": {"description": "Excited jump", "type": "oneshot", "duration": 1.0, "priority": 3},
            "sit": {"description": "Sit down", "type": "state", "priority": 1},
            "stand": {"description": "Stand up", "type": "state", "priority": 1},
            "walk": {"description": "Walking in place", "type": "loop", "priority": 1},
            "run": {"description": "Running in place", "type": "loop", "priority": 1},
            "bow": {"description": "Polite bow", "type": "oneshot", "duration": 1.5, "priority": 2},
            "clap": {"description": "Clapping hands", "type": "oneshot", "duration": 2.0, "priority": 2},
            "think": {"description": "Hand on chin, thinking pose", "type": "state", "priority": 1},
            "sleep": {"description": "Sleeping pose, eyes closed", "type": "state", "priority": 1},
            "spin": {"description": "Spin around happily", "type": "oneshot", "duration": 1.5, "priority": 2},
            "nod": {"description": "Nod head yes", "type": "oneshot", "duration": 1.0, "priority": 2},
            "shake_head": {"description": "Shake head no", "type": "oneshot", "duration": 1.0, "priority": 2},
            "poke": {"description": "Poking gesture", "type": "oneshot", "duration": 0.8, "priority": 2},
            "pat": {"description": "Patting gesture (for pet)", "type": "oneshot", "duration": 1.5, "priority": 2},
            "feed": {"description": "Feeding gesture (for pet)", "type": "oneshot", "duration": 2.0, "priority": 2},
            "play_dead": {"description": "Dramatic faint/play dead", "type": "oneshot", "duration": 3.0, "priority": 3},
            "celebrate": {"description": "Victory celebration", "type": "oneshot", "duration": 2.5, "priority": 3},
        }
        
        # Body part interactions (when user clicks on VRM)
        self.body_interactions = {
            "head": {"description": "Head was patted", "reaction": "happy", "llm_message": "*giggles* You patted my head~ That feels nice.", "expression": "happy"},
            "face": {"description": "Face/cheek was touched", "reaction": "blush", "llm_message": "*blushes* H-hey! That's my face you're touching...", "expression": "happy"},
            "hand": {"description": "Hand was touched", "reaction": "hold", "llm_message": "*holds your hand* You want to hold hands? So sweet~", "expression": "happy"},
            "chest": {"description": "Chest area was touched", "reaction": "surprised", "llm_message": "*gasps* W-where are you touching?! Pervert~", "expression": "surprised"},
            "shoulder": {"description": "Shoulder was touched", "reaction": "comfort", "llm_message": "*leans into your touch* Mmm, that feels reassuring...", "expression": "relaxed"},
            "stomach": {"description": "Stomach/belly was poked", "reaction": "giggle", "llm_message": "*giggles* Hahaha! That tickles! Stop it~", "expression": "happy"},
            "leg": {"description": "Leg was touched", "reaction": "shy", "llm_message": "*shifts nervously* U-um... my leg...", "expression": "surprised"},
            "hair": {"description": "Hair was touched", "reaction": "enjoy", "llm_message": "*closes eyes contentedly* I love it when you play with my hair...", "expression": "relaxed"},
        }
        
        # Lip sync phoneme mapping
        self.viseme_map = {
            "a": "aa", "e": "E", "i": "ih", "o": "oh", "u": "ou",
            "m": "nn", "n": "nn", "b": "PP", "p": "PP",
            "f": "FF", "v": "FF", "w": "ou", "r": "E",
            "th": "TH", "s": "SS", "sh": "SS", "ch": "SS",
            " ": "sil", ".": "sil", ",": "sil"
        }
    
    def get_all_actions(self) -> Dict:
        """Return all actions for LLM reference."""
        return {
            "expressions": self.expressions,
            "animations": self.animations,
            "body_interactions": self.body_interactions
        }
    
    def get_expression(self, name: str) -> Optional[Dict]:
        return self.expressions.get(name.lower())
    
    def get_animation(self, name: str) -> Optional[Dict]:
        return self.animations.get(name.lower())
    
    def get_body_interaction(self, part: str) -> Optional[Dict]:
        return self.body_interactions.get(part.lower())
    
    def text_to_visemes(self, text: str) -> List[Dict]:
        """Convert text to viseme sequence for lip sync."""
        visemes = []
        words = text.lower().split()
        time_per_word = 0.3
        
        for i, word in enumerate(words):
            if not word:
                continue
            # Simple mapping: use first character's viseme
            char = word[0] if word[0] in self.viseme_map else "a"
            viseme = self.viseme_map.get(char, "aa")
            visemes.append({
                "viseme": viseme,
                "start": i * time_per_word,
                "duration": time_per_word * 0.8,
                "word": word
            })
        
        return visemes
    
    def get_llm_action_guide(self) -> str:
        """Generate a formatted guide for the LLM on how to use VRM actions."""
        guide = "\n=== VRM ACTION COMMANDS ===\n"
        guide += "You can control your avatar using these commands:\n\n"
        
        guide += "[EXPRESSION: name] - Set facial expression. Available:\n"
        for name, info in self.expressions.items():
            guide += f"  - {name}: {info['description']}\n"
        
        guide += "\n[ACTION: name] - Perform body animation. Available:\n"
        for name, info in self.animations.items():
            guide += f"  - {name}: {info['description']} ({info['type']})\n"
        
        guide += "\nUse these naturally in your responses. Example: \"I'm so happy to see you! [EXPRESSION: happy] [ACTION: wave]\"\n"
        guide += "=== END VRM ACTIONS ===\n"
        return guide
    
    def get_available_outfits(self) -> Dict:
        """List all available VRM outfit models.

        This will scan the `static/models` folder for `.vrm` files and
        return a mapping the frontend can use. If none are found, it falls
        back to a small set of built-in sample outfits.
        """
        try:
            base = Path(__file__).parent.parent / "static" / "models"
            thumbs = base / "thumbnails"
            outfits: Dict[str, Dict] = {}

            if base.exists():
                for p in sorted(base.glob("*.vrm")):
                    oid = p.stem
                    outfits[oid] = {
                        "id": oid,
                        "name": oid.replace("_", " ").title(),
                        "description": "Auto-detected VRM model",
                        "path": f"/static/models/{p.name}",
                        "thumbnail": f"/static/models/thumbnails/{oid}.png" if (thumbs / f"{oid}.png").exists() else None,
                        "color_scheme": "pink_purple"
                    }

            # Fallback to built-in list when no models detected
            if not outfits:
                outfits = {
                    "default": {
                        "id": "default",
                        "name": "Sarah Classic",
                        "description": "The default Sarah outfit",
                        "path": "/static/models/sarah.vrm",
                        "thumbnail": "/static/models/thumbnails/sarah_classic.png",
                        "color_scheme": "pink_purple"
                    },
                    "futuristic": {
                        "id": "futuristic",
                        "name": "Futuristic Sarah",
                        "description": "High-tech cyberpunk outfit",
                        "path": "/static/models/sarah_futuristic.vrm",
                        "thumbnail": "/static/models/thumbnails/sarah_futuristic.png",
                        "color_scheme": "neon_blue"
                    },
                    "casual": {
                        "id": "casual",
                        "name": "Casual Sarah",
                        "description": "Comfortable everyday outfit",
                        "path": "/static/models/sarah_casual.vrm",
                        "thumbnail": "/static/models/thumbnails/sarah_casual.png",
                        "color_scheme": "warm_tones"
                    },
                    "elegant": {
                        "id": "elegant",
                        "name": "Elegant Sarah",
                        "description": "Formal gown outfit",
                        "path": "/static/models/sarah_elegant.vrm",
                        "thumbnail": "/static/models/thumbnails/sarah_elegant.png",
                        "color_scheme": "gold_white"
                    },
                    "magical": {
                        "id": "magical",
                        "name": "Magical Sarah",
                        "description": "Fantasy wizard outfit",
                        "path": "/static/models/sarah_magical.vrm",
                        "thumbnail": "/static/models/thumbnails/sarah_magical.png",
                        "color_scheme": "purple_stars"
                    }
                }

            return outfits
        except Exception as e:
            print(f"[VRM ACTIONS]: Error scanning models: {e}")
            # Return fallback mapping on error
            return {
                "default": {
                    "id": "default",
                    "name": "Sarah Classic",
                    "description": "The default Sarah outfit",
                    "path": "/static/models/sarah.vrm",
                    "thumbnail": "/static/models/thumbnails/sarah_classic.png",
                    "color_scheme": "pink_purple"
                }
            }
    
    def get_outfit(self, outfit_id: str) -> Optional[Dict]:
        """Get a specific outfit by ID."""
        outfits = self.get_available_outfits()
        return outfits.get(outfit_id)
