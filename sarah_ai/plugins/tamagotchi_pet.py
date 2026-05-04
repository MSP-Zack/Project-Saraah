import json
import os
import random
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class TamagotchiPet:
    """
    Advanced virtual pet system.
    The pet has needs, emotions, evolution stages, and can interact
    with both the user and Sarah's VRM avatar.
    """
    
    def __init__(self):
        self.save_file = "memory/tamagotchi.json"
        self.state = self._load_or_create()
        self.last_update = datetime.now()
    
    def _load_or_create(self) -> Dict:
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r') as f:
                return json.load(f)
        
        return {
            "name": "Pixel",
            "species": "fox",
            "stage": "baby",  # baby -> child -> teen -> adult
            "age_days": 0,
            "birth_date": datetime.now().isoformat(),
            
            # Core needs (0-100)
            "hunger": 80,        # 100 = full, 0 = starving
            "energy": 80,        # 100 = energetic, 0 = exhausted
            "happiness": 80,     # 100 = ecstatic, 0 = depressed
            "hygiene": 80,       # 100 = clean, 0 = filthy
            "health": 100,       # 100 = healthy, 0 = sick
            
            # Personality traits (develop over time)
            "personality": {
                "playful": 50,
                "shy": 30,
                "brave": 40,
                "curious": 60
            },
            
            # Status
            "is_sleeping": False,
            "is_sick": False,
            "mood": "happy",  # happy, sad, excited, tired, sick, hungry, angry
            
            # Stats
            "interactions_count": 0,
            "meals_fed": 0,
            "games_played": 0,
            "care_missed": 0,
            
            # Care tracking
            "last_fed": datetime.now().isoformat(),
            "last_pet": datetime.now().isoformat(),
            "last_cleaned": datetime.now().isoformat(),
            "last_played": datetime.now().isoformat(),
            
            # Messages from the pet
            "recent_messages": []
        }
    
    def save(self):
        os.makedirs(os.path.dirname(self.save_file), exist_ok=True)
        with open(self.save_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _update_needs(self):
        """Update needs based on time passed."""
        now = datetime.now()
        last = datetime.fromisoformat(self.state["last_fed"])
        hours_passed = (now - last).total_seconds() / 3600
        
        # Decay rates per hour
        self.state["hunger"] = max(0, self.state["hunger"] - hours_passed * 3)
        self.state["energy"] = max(0, self.state["energy"] - hours_passed * 2)
        self.state["happiness"] = max(0, self.state["happiness"] - hours_passed * 1.5)
        self.state["hygiene"] = max(0, self.state["hygiene"] - hours_passed * 1)
        
        # Health affected by other needs
        if self.state["hunger"] < 20 or self.state["hygiene"] < 20:
            self.state["health"] = max(0, self.state["health"] - hours_passed * 2)
        elif self.state["health"] < 100:
            self.state["health"] = min(100, self.state["health"] + hours_passed * 1)
        
        # Determine mood
        self._update_mood()
        
        # Evolution check
        self._check_evolution()
        
        self.last_update = now
        self.save()
    
    def _update_mood(self):
        """Update mood based on needs."""
        if self.state["is_sick"] or self.state["health"] < 30:
            self.state["mood"] = "sick"
        elif self.state["is_sleeping"]:
            self.state["mood"] = "sleeping"
        elif self.state["hunger"] < 30:
            self.state["mood"] = "hungry"
        elif self.state["happiness"] > 80 and self.state["energy"] > 50:
            self.state["mood"] = "excited"
        elif self.state["energy"] < 20:
            self.state["mood"] = "tired"
        elif self.state["happiness"] < 30:
            self.state["mood"] = "sad"
        elif self.state["hygiene"] < 20:
            self.state["mood"] = "grumpy"
        else:
            self.state["mood"] = "happy"
    
    def _check_evolution(self):
        """Check if pet should evolve."""
        age = self.state["age_days"]
        stage = self.state["stage"]
        
        if stage == "baby" and age >= 2:
            self.state["stage"] = "child"
            self._add_message(f"{self.state['name']} evolved into a child!")
        elif stage == "child" and age >= 5:
            self.state["stage"] = "teen"
            self._add_message(f"{self.state['name']} evolved into a teenager!")
        elif stage == "teen" and age >= 10:
            self.state["stage"] = "adult"
            self._add_message(f"{self.state['name']} is fully grown!")
    
    def _add_message(self, msg: str):
        self.state["recent_messages"].insert(0, {
            "text": msg,
            "time": datetime.now().isoformat()
        })
        self.state["recent_messages"] = self.state["recent_messages"][:20]
    
    def feed(self, food_type: str = "regular") -> Dict:
        """Feed the pet."""
        self._update_needs()
        
        if self.state["is_sleeping"]:
            return {"success": False, "message": f"{self.state['name']} is sleeping! Don't wake them up."}
        
        food_values = {
            "regular": 25,
            "treat": 15,
            "meal": 40,
            "snack": 10,
            "premium": 50
        }
        
        gain = food_values.get(food_type, 25)
        self.state["hunger"] = min(100, self.state["hunger"] + gain)
        self.state["meals_fed"] += 1
        self.state["last_fed"] = datetime.now().isoformat()
        
        messages = {
            "regular": f"Yum! {self.state['name']} enjoyed the food!",
            "treat": f"{self.state['name']} loved the treat! *happy wiggles*",
            "meal": f"{self.state['name']} ate a big meal! So satisfied!",
            "snack": f"{self.state['name']} nibbled on the snack.",
            "premium": f"{self.state['name']} devoured the gourmet meal! *sparkly eyes*"
        }
        
        self._add_message(messages.get(food_type, "Fed!"))
        self.save()
        return {"success": True, "message": messages.get(food_type), "state": self.get_state()}
    
    def pet(self) -> Dict:
        """Pet the pet."""
        self._update_needs()
        
        if self.state["is_sleeping"]:
            return {"success": False, "message": f"{self.state['name']} is sleeping peacefully..."}
        
        self.state["happiness"] = min(100, self.state["happiness"] + 15)
        self.state["interactions_count"] += 1
        self.state["last_pet"] = datetime.now().isoformat()
        
        reactions = [
            f"{self.state['name']} purrs happily! *wags tail*",
            f"{self.state['name']} snuggles into your hand! So cute!",
            f"{self.state['name']} makes happy squeaking noises!",
            f"{self.state['name']} rolls over for belly rubs!"
        ]
        
        msg = random.choice(reactions)
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def play(self, game_type: str = "default") -> Dict:
        """Play with the pet."""
        self._update_needs()
        
        if self.state["is_sleeping"]:
            return {"success": False, "message": f"{self.state['name']} is too tired to play."}
        
        if self.state["energy"] < 20:
            return {"success": False, "message": f"{self.state['name']} is too tired. Let them rest!"}
        
        self.state["happiness"] = min(100, self.state["happiness"] + 20)
        self.state["energy"] = max(0, self.state["energy"] - 15)
        self.state["games_played"] += 1
        self.state["last_played"] = datetime.now().isoformat()
        
        games = {
            "default": f"You played with {self.state['name']}! They had so much fun!",
            "fetch": f"{self.state['name']} happily fetched the ball! Good pet!",
            "hide_seek": f"{self.state['name']} loves hide and seek! *excited bouncing*",
            "puzzle": f"{self.state['name']} solved the puzzle! So smart!",
            "dance": f"{self.state['name']} danced with you! *spinning happily*"
        }
        
        msg = games.get(game_type, games["default"])
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def clean(self) -> Dict:
        """Clean/groom the pet."""
        self._update_needs()
        
        self.state["hygiene"] = 100
        self.state["happiness"] = min(100, self.state["happiness"] + 10)
        self.state["last_cleaned"] = datetime.now().isoformat()
        
        msg = f"{self.state['name']} is all clean and fluffy now! *sparkles*"
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def sleep(self) -> Dict:
        """Put the pet to sleep."""
        if self.state["energy"] > 80:
            return {"success": False, "message": f"{self.state['name']} isn't tired yet!"}
        
        self.state["is_sleeping"] = True
        self.state["energy"] = min(100, self.state["energy"] + 40)
        
        msg = f"{self.state['name']} curled up and fell asleep... zzz..."
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def wake_up(self) -> Dict:
        """Wake the pet up."""
        if not self.state["is_sleeping"]:
            return {"success": False, "message": f"{self.state['name']} is already awake!"}
        
        self.state["is_sleeping"] = False
        msg = f"{self.state['name']} woke up! *yawns and stretches*"
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def medicate(self) -> Dict:
        """Give medicine to sick pet."""
        if not self.state["is_sick"] and self.state["health"] > 50:
            return {"success": False, "message": f"{self.state['name']} isn't sick!"}
        
        self.state["health"] = min(100, self.state["health"] + 30)
        self.state["is_sick"] = False
        
        if self.state["health"] > 50:
            msg = f"{self.state['name']} is feeling better! *weak smile*"
        else:
            msg = f"{self.state['name']} took the medicine. Still recovering..."
        
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def sarah_interact(self, action: str) -> Dict:
        """Sarah's VRM avatar interacts with the pet."""
        self._update_needs()
        
        actions = {
            "pet": f"Sarah gently pets {self.state['name']}. They love her!",
            "feed": f"Sarah feeds {self.state['name']} a special treat!",
            "play": f"Sarah plays with {self.state['name']}! They're having so much fun together!",
            "sing": f"Sarah sings a lullaby to {self.state['name']}... they look so peaceful.",
            "dance": f"Sarah dances with {self.state['name']}! So adorable!",
            "cuddle": f"Sarah cuddles {self.state['name']}... *happy purring noises*"
        }
        
        msg = actions.get(action, f"Sarah interacts with {self.state['name']}!")
        
        if action == "pet":
            self.state["happiness"] = min(100, self.state["happiness"] + 10)
        elif action == "feed":
            self.state["hunger"] = min(100, self.state["hunger"] + 15)
        elif action == "play":
            self.state["happiness"] = min(100, self.state["happiness"] + 15)
            self.state["energy"] = max(0, self.state["energy"] - 5)
        
        self._add_message(msg)
        self.save()
        return {"success": True, "message": msg, "state": self.get_state()}
    
    def get_state(self) -> Dict:
        """Get current pet state."""
        self._update_needs()
        return self.state
    
    def rename(self, new_name: str) -> Dict:
        """Rename the pet."""
        old_name = self.state["name"]
        self.state["name"] = new_name
        self._add_message(f"{old_name} is now called {new_name}!")
        self.save()
        return {"success": True, "message": f"Renamed to {new_name}!", "state": self.get_state()}
    
    def get_llm_context(self) -> str:
        """Get formatted context for the LLM about the pet's state."""
        s = self.state
        return f"""
PET STATUS - {s['name']} the {s['species']} ({s['stage']}):
- Hunger: {s['hunger']:.0f}/100
- Energy: {s['energy']:.0f}/100
- Happiness: {s['happiness']:.0f}/100
- Hygiene: {s['hygiene']:.0f}/100
- Health: {s['health']:.0f}/100
- Mood: {s['mood']}
- Sleeping: {'Yes' if s['is_sleeping'] else 'No'}
- Sick: {'Yes' if s['is_sick'] else 'No'}

You can help take care of {s['name']} by reminding the user to feed, play with, or clean them.
"""


# Plugin interface
class Plugin:
    def __init__(self):
        self.pet = TamagotchiPet()
    
    def get_info(self) -> Dict:
        return {
            "name": "Tamagotchi Pet",
            "description": "Virtual pet that lives with Sarah",
            "version": "1.0"
        }
    
    def get_state(self) -> Dict:
        return self.pet.get_state()
    
    def feed(self, food_type: str = "regular") -> Dict:
        return self.pet.feed(food_type)
    
    def pet(self) -> Dict:
        return self.pet.pet()
    
    def play(self, game_type: str = "default") -> Dict:
        return self.pet.play(game_type)
    
    def clean(self) -> Dict:
        return self.pet.clean()
    
    def sleep(self) -> Dict:
        return self.pet.sleep()
    
    def wake_up(self) -> Dict:
        return self.pet.wake_up()
    
    def medicate(self) -> Dict:
        return self.pet.medicate()
    
    def sarah_interact(self, action: str) -> Dict:
        return self.pet.sarah_interact(action)
    
    def rename(self, new_name: str) -> Dict:
        return self.pet.rename(new_name)
    
    def get_llm_context(self) -> str:
        return self.pet.get_llm_context()
