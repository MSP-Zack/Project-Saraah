import json
import os
import threading
import random
from datetime import datetime
from typing import Dict, Any

from .needs_engine import NeedsEngine
from .behavior import BehaviorManager
from .mini_games import MiniGameManager


class TamagotchiManager:
    """A manager that composes a NeedsEngine and BehaviorManager.

    Responsibilities:
    - keep authoritative pet state
    - run ticks to decay needs
    - expose actions used by the frontend/LLM
    - provide LLM context and suggestions
    """

    def __init__(self, save_file: str = "memory/tamagotchi_v2.json"):
        self.save_file = save_file
        self.lock = threading.Lock()
        self.state = self._load_or_create()

        # core subsystems
        self.needs = NeedsEngine(self.state)
        self.behavior = BehaviorManager(self.state, random.Random())
        self.minigames = MiniGameManager(self.state)

        # attempt migration from v1 save if present
        self._migrate_from_v1()

    def _load_or_create(self) -> Dict[str, Any]:
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        now_iso = datetime.now().isoformat()
        return {
            "name": "PixelV2",
            "species": "fox",
            "stage": "baby",
            "age_days": 0,
            "birth_date": now_iso,
            "last_checked": now_iso,
            "needs": {
                "hunger": 80,
                "energy": 80,
                "happiness": 80,
                "hygiene": 80,
                "health": 100,
            },
            "personality": {"playful": 50, "shy": 30, "curious": 60},
            "status": {"is_sleeping": False, "is_sick": False, "mood": "happy"},
            "counters": {"interactions_count": 0, "meals_fed": 0, "games_played": 0},
        }

    def _migrate_from_v1(self) -> None:
        old_path = "memory/tamagotchi.json"
        if not os.path.exists(old_path):
            return

        try:
            with open(old_path, "r") as f:
                old = json.load(f)
        except Exception:
            return

        # If the v2 file already exists, don't overwrite
        if os.path.exists(self.save_file):
            return

        # Map common fields
        self.state["name"] = old.get("name", self.state["name"])
        self.state["species"] = old.get("species", self.state["species"])
        self.state["stage"] = old.get("stage", self.state["stage"])
        self.state["birth_date"] = old.get("birth_date", self.state["birth_date"])

        for k in ("hunger", "energy", "happiness", "hygiene", "health"):
            if k in old:
                self.state["needs"][k] = old[k]

        # Counters
        for c in ("interactions_count", "meals_fed", "games_played"):
            if c in old:
                self.state.setdefault("counters", {})[c] = old[c]

        self.save()

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.save_file), exist_ok=True)
        self.state["last_checked"] = datetime.now().isoformat()
        with open(self.save_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def tick(self) -> None:
        """Advance time-dependent systems using last_checked timestamp."""
        with self.lock:
            now = datetime.now()
            try:
                last = datetime.fromisoformat(self.state.get("last_checked"))
            except Exception:
                last = now
            hours = max(0.0, (now - last).total_seconds() / 3600.0)
            if hours <= 0:
                return

            self.needs.tick(hours)
            self.state["last_checked"] = now.isoformat()
            self.save()

    def get_state(self) -> Dict[str, Any]:
        self.tick()
        return self.state

    # Action wrappers delegate to NeedsEngine
    def feed(self, food_type: str = "regular") -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("feed", food_type=food_type)
            self.save()
            return r

    def pet(self) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("pet")
            self.save()
            return r

    def play(self, game_type: str = "default") -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("play", game_type=game_type)
            self.save()
            return r

    def clean(self) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("clean")
            self.save()
            return r

    def sleep(self) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("sleep")
            self.save()
            return r

    def wake_up(self) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("wake_up")
            self.save()
            return r

    def medicate(self) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            r = self.needs.apply_action("medicate")
            self.save()
            return r

    def sarah_interact(self, action: str) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            # For now, sarah_interact maps to a small set of needs actions
            if action == "pet":
                r = self.needs.apply_action("pet")
            elif action == "feed":
                r = self.needs.apply_action("feed", food_type="treat")
            elif action == "play":
                r = self.needs.apply_action("play")
            else:
                r = {"success": False, "message": "Unknown sarah action", "state": self.state}
            self.save()
            return r

    def autonomous_tick_action(self) -> Dict[str, Any]:
        """Run a single autonomous decision and apply it.

        This avoids nested locking by calling `tick()` (which manages its own lock),
        then applying the chosen action inside a short critical section.
        """
        # advance time first (tick owns its own lock)
        self.tick()

        action = self.behavior.decide()
        # apply the chosen action inside the lock to avoid races when mutating state
        with self.lock:
            if action == "seek_food":
                result = self.needs.apply_action("feed", food_type="snack")
            elif action == "sleep":
                result = self.needs.apply_action("sleep")
            elif action == "play":
                result = self.needs.apply_action("play")
            elif action == "groom":
                result = self.needs.apply_action("clean")
            elif action == "wander":
                result = {"success": True, "message": "Wandered around", "state": self.state}
            elif action == "interact_with_sarah":
                result = {"success": True, "message": "Sought Sarah for attention", "state": self.state}
            else:
                result = {"success": True, "message": "Idle", "state": self.state}

            # persist the result
            self.save()

        return {"action": action, "result": result}

    # --- Mini-game integration ---
    def start_minigame(self, game_type: str = "fetch", difficulty: str = "normal") -> Dict[str, Any]:
        with self.lock:
            self.tick()
            return self.minigames.start_session(game_type, difficulty)

    def submit_minigame(self, session_id: str, score: int) -> Dict[str, Any]:
        with self.lock:
            self.tick()
            res = self.minigames.submit_result(session_id, int(score))
            # persist changes to state
            self.save()
            return res

    def get_llm_context(self) -> str:
        return self.needs.get_llm_context()

    def suggest_actions(self, top_n: int = 3):
        return self.needs.suggest_actions(top_n)


class Plugin:
    def __init__(self):
        self.manager = TamagotchiManager()

    def get_info(self) -> Dict[str, str]:
        return {"name": "Tamagotchi v2", "description": "Next-gen virtual pet", "version": "0.2"}

    def get_state(self) -> Dict[str, Any]:
        return self.manager.get_state()

    def feed(self, food_type: str = "regular") -> Dict[str, Any]:
        return self.manager.feed(food_type)

    def pet(self) -> Dict[str, Any]:
        return self.manager.pet()

    def play(self, game_type: str = "default") -> Dict[str, Any]:
        return self.manager.play(game_type)

    def clean(self) -> Dict[str, Any]:
        return self.manager.clean()

    def sleep(self) -> Dict[str, Any]:
        return self.manager.sleep()

    def wake_up(self) -> Dict[str, Any]:
        return self.manager.wake_up()

    def medicate(self) -> Dict[str, Any]:
        return self.manager.medicate()

    def sarah_interact(self, action: str) -> Dict[str, Any]:
        return self.manager.sarah_interact(action)

    # Mini-games
    def start_minigame(self, game_type: str = "fetch", difficulty: str = "normal") -> Dict[str, Any]:
        return self.manager.start_minigame(game_type, difficulty)

    def submit_minigame(self, session_id: str, score: int) -> Dict[str, Any]:
        return self.manager.submit_minigame(session_id, score)

    # Added utilities for autonomous and LLM integration
    def autonomous_action(self) -> Dict[str, Any]:
        return self.manager.autonomous_tick_action()

    def get_llm_context(self) -> str:
        return self.manager.get_llm_context()

    def suggest_actions(self, top_n: int = 3):
        return self.manager.suggest_actions(top_n)
