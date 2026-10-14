from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class NeedsEngine:
    """Encapsulates needs decay, action effects, and event callbacks.

    This is intentionally small but structured so we can later replace
    heuristics with more advanced systems (e.g., hunger curves, illnesses).
    """

    def __init__(self, state: Dict[str, Any], decay_rates: Optional[Dict[str, float]] = None):
        self.state = state
        self.decay_rates = decay_rates or {
            "hunger": 3.0,  # per hour
            "energy": 2.0,
            "happiness": 1.5,
            "hygiene": 1.0,
        }
        # Modifiers by lifecycle stage to allow tuning (e.g., babies decay faster)
        self.stage_modifiers = {
            "baby": 1.2,
            "adult": 1.0,
            "elder": 1.1,
        }
        # Passive energy recovery while sleeping (per hour)
        self.sleep_recovery_rate = 5.0
        self._callbacks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._flags: Dict[str, bool] = {"hungry_alerted": False, "sick_alerted": False}

    def register_callback(self, name: str, cb: Callable[[Dict[str, Any]], None]):
        self._callbacks.setdefault(name, []).append(cb)

    def update_decay_rates(self, decay_rates: Dict[str, float]):
        """Update decay rates at runtime (useful for tuning)."""
        self.decay_rates.update(decay_rates)

    def _emit(self, name: str, payload: Dict[str, Any]):
        for cb in self._callbacks.get(name, []):
            try:
                cb(payload)
            except Exception:
                # swallow callback exceptions for robustness
                pass

    def tick(self, elapsed_hours: float) -> None:
        needs = self.state["needs"]

        # Apply linear decay with stage modifiers and sleeping behavior
        stage = self.state.get("stage", "adult")
        stage_factor = self.stage_modifiers.get(stage, 1.0)

        sleeping = bool(self.state.get("status", {}).get("is_sleeping"))

        for k, rate in self.decay_rates.items():
            if k not in needs:
                continue

            if sleeping and k == "energy":
                # Passive recovery while sleeping
                needs[k] = min(100.0, needs[k] + elapsed_hours * self.sleep_recovery_rate)
                continue

            # apply decay; reduce decay while sleeping for non-energy needs
            decay_multiplier = 0.5 if sleeping else 1.0
            needs[k] = max(0.0, needs[k] - elapsed_hours * rate * stage_factor * decay_multiplier)

        # Health drift based on other needs
        if needs.get("hunger", 100) < 20 or needs.get("hygiene", 100) < 20:
            needs["health"] = max(0.0, needs.get("health", 100) - elapsed_hours * 2.0)
        else:
            needs["health"] = min(100.0, needs.get("health", 100) + elapsed_hours * 0.25)

        # Events
        if needs.get("hunger", 100) < 30 and not self._flags.get("hungry_alerted"):
            self._flags["hungry_alerted"] = True
            self._emit("on_hungry", self.state)

        if needs.get("health", 100) < 40 and not self._flags.get("sick_alerted"):
            self._flags["sick_alerted"] = True
            self._emit("on_sick", self.state)

        # Reset alerts when recovered
        if needs.get("hunger", 100) >= 50 and self._flags.get("hungry_alerted"):
            self._flags["hungry_alerted"] = False

        if needs.get("health", 100) >= 60 and self._flags.get("sick_alerted"):
            self._flags["sick_alerted"] = False

    def apply_action(self, action: str, **kwargs) -> Dict[str, Any]:
        needs = self.state["needs"]
        result = {"success": False, "message": "Unknown action", "state": self.state}

        if action == "feed":
            food_type = kwargs.get("food_type", "regular")
            gains = {"regular": 25, "snack": 10, "meal": 40, "premium": 50}
            gain = gains.get(food_type, 25)
            needs["hunger"] = min(100.0, needs.get("hunger", 0) + gain)
            self.state.setdefault("counters", {}).setdefault("meals_fed", 0)
            self.state["counters"]["meals_fed"] += 1
            result = {"success": True, "message": f"Fed ({food_type})", "state": self.state}

        elif action == "pet":
            needs["happiness"] = min(100.0, needs.get("happiness", 0) + 15)
            self.state.setdefault("counters", {}).setdefault("interactions_count", 0)
            self.state["counters"]["interactions_count"] += 1
            result = {"success": True, "message": "Petted", "state": self.state}

        elif action == "play":
            if needs.get("energy", 0) < 15:
                result = {"success": False, "message": "Too tired to play", "state": self.state}
            else:
                needs["happiness"] = min(100.0, needs.get("happiness", 0) + 20)
                needs["energy"] = max(0.0, needs.get("energy", 100) - 15)
                self.state.setdefault("counters", {}).setdefault("games_played", 0)
                self.state["counters"]["games_played"] += 1
                result = {"success": True, "message": "Played", "state": self.state}

        elif action == "clean":
            needs["hygiene"] = 100.0
            needs["happiness"] = min(100.0, needs.get("happiness", 0) + 10)
            result = {"success": True, "message": "Cleaned", "state": self.state}

        elif action == "sleep":
            if needs.get("energy", 100) > 80:
                result = {"success": False, "message": "Not tired yet", "state": self.state}
            else:
                self.state.setdefault("status", {})["is_sleeping"] = True
                needs["energy"] = min(100.0, needs.get("energy", 0) + 40)
                result = {"success": True, "message": "Sleeping", "state": self.state}

        elif action == "wake_up":
            if not self.state.get("status", {}).get("is_sleeping"):
                result = {"success": False, "message": "Already awake", "state": self.state}
            else:
                self.state.setdefault("status", {})["is_sleeping"] = False
                result = {"success": True, "message": "Woke up", "state": self.state}

        elif action == "medicate":
            if not self.state.get("status", {}).get("is_sick") and needs.get("health", 100) > 50:
                result = {"success": False, "message": "Not sick", "state": self.state}
            else:
                needs["health"] = min(100.0, needs.get("health", 100) + 30)
                self.state.setdefault("status", {})["is_sick"] = False
                result = {"success": True, "message": "Medicated", "state": self.state}

        # Emit a generic action event
        self._emit("on_action", {"action": action, "state": self.state})
        return result

    def get_llm_context(self) -> str:
        s = self.state
        return (
            f"PET STATUS - {s.get('name','Pet')} ({s.get('stage','unknown')}):\n"
            f"- Hunger: {s['needs']['hunger']:.0f}/100\n"
            f"- Energy: {s['needs']['energy']:.0f}/100\n"
            f"- Happiness: {s['needs']['happiness']:.0f}/100\n"
            f"- Hygiene: {s['needs']['hygiene']:.0f}/100\n"
            f"- Health: {s['needs']['health']:.0f}/100\n"
            f"- Mood: {s.get('status',{}).get('mood','unknown')}\n"
            f"- Sleeping: {'Yes' if s.get('status',{}).get('is_sleeping') else 'No'}\n"
            f"- Sick: {'Yes' if s.get('status',{}).get('is_sick') else 'No'}\n"
        )

    def suggest_actions(self, top_n: int = 3) -> List[Dict[str, Any]]:
        # Simple heuristics-based suggestions with reasons
        needs = self.state["needs"]
        candidates: List[Dict[str, Any]] = []

        urgency = lambda key: max(0.0, 100.0 - needs.get(key, 100.0))

        candidates.append({"action": "feed", "score": urgency("hunger"), "reason": "Hunger"})
        candidates.append({"action": "sleep", "score": urgency("energy"), "reason": "Low energy"})
        candidates.append({"action": "play", "score": urgency("happiness"), "reason": "Low happiness"})
        candidates.append({"action": "clean", "score": urgency("hygiene"), "reason": "Needs grooming"})

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_n]
