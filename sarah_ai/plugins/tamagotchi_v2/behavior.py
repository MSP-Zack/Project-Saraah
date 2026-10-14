import random
from typing import Any, Dict


class BehaviorManager:
    """Lightweight behavior decision system using utility scoring.

    This manager selects the most urgent action for the pet to perform
    when it is autonomous (not being actively controlled by the user).
    """

    def __init__(self, state: Dict[str, Any], rng: random.Random | None = None):
        self.state = state
        self.rng = rng or random.Random()

    def _score_actions(self) -> Dict[str, float]:
        needs = self.state.get("needs", {})
        hunger_deficit = max(0.0, 100.0 - needs.get("hunger", 100.0))
        energy_deficit = max(0.0, 100.0 - needs.get("energy", 100.0))
        happiness_deficit = max(0.0, 100.0 - needs.get("happiness", 100.0))
        hygiene_deficit = max(0.0, 100.0 - needs.get("hygiene", 100.0))

        scores = {
            "seek_food": hunger_deficit * 1.2,
            "sleep": energy_deficit * 1.0,
            "play": happiness_deficit * (1.0 if needs.get("energy", 100) > 20 else 0.2),
            "groom": hygiene_deficit * 0.8,
            "wander": 5.0 + self.rng.random() * 5.0,
            "interact_with_sarah": 3.0 + happiness_deficit * 0.3,
        }
        return scores

    def decide(self) -> str:
        scores = self._score_actions()
        if not scores:
            return "idle"
        # pick highest scoring action, but add small randomness
        items = sorted(scores.items(), key=lambda t: t[1], reverse=True)
        top = items[0]
        # 10% chance to pick a low-priority playful action
        if self.rng.random() < 0.10:
            return "wander"
        return top[0]
