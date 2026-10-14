import uuid
from datetime import datetime, timedelta
from typing import Any, Dict


class MiniGameManager:
    """Simple server-side mini-game session manager.

    - start_session(game, difficulty) -> {session_id, max_score, rounds}
    - submit_result(session_id, score) -> applies rewards to `state` and returns result
    """

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(self, game: str = "fetch", difficulty: str = "normal") -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        if game == "fetch":
            rounds = 10
            max_score = rounds
            duration_seconds = 30
        else:
            rounds = 5
            max_score = rounds
            duration_seconds = 20

        expires_at = (now + timedelta(minutes=5)).isoformat()
        self.sessions[session_id] = {
            "game": game,
            "difficulty": difficulty,
            "max_score": max_score,
            "rounds": rounds,
            "start_time": now.isoformat(),
            "expires_at": expires_at,
            "submitted": False,
        }

        return {
            "success": True,
            "session_id": session_id,
            "max_score": max_score,
            "rounds": rounds,
            "expires_at": expires_at,
        }

    def submit_result(self, session_id: str, score: int) -> Dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            return {"success": False, "error": "Invalid session_id"}

        if s.get("submitted"):
            return {"success": False, "error": "Already submitted"}

        try:
            expires = datetime.fromisoformat(s["expires_at"])
        except Exception:
            expires = None

        if expires and datetime.now() > expires:
            return {"success": False, "error": "Session expired"}

        if score < 0 or score > s["max_score"]:
            return {"success": False, "error": "Invalid score"}

        # Reward calculation (tunable)
        happiness_gain = min(40, 5 + int(score) * 3)
        energy_cost = min(60, int(score) * 3)

        needs = self.state.setdefault("needs", {})
        needs["happiness"] = min(100.0, needs.get("happiness", 50.0) + happiness_gain)
        needs["energy"] = max(0.0, needs.get("energy", 50.0) - energy_cost)

        self.state.setdefault("counters", {}).setdefault("games_played", 0)
        self.state["counters"]["games_played"] += 1

        # Log recent message
        self.state.setdefault("recent_messages", [])
        self.state["recent_messages"].insert(0, {
            "text": f"Played {s['game']} and scored {score}/{s['max_score']}",
            "time": datetime.now().isoformat()
        })
        self.state["recent_messages"] = self.state["recent_messages"][:20]

        s["submitted"] = True

        return {
            "success": True,
            "score": score,
            "max_score": s["max_score"],
            "happiness_gain": happiness_gain,
            "energy_cost": energy_cost,
            "state": self.state,
        }
