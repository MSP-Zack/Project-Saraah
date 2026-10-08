"""Durable hierarchical goals with append-only progress history."""

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class GoalEngine:
    """Goal state that is inspectable, scoped, and safe to update."""

    PRIORITIES = {"high", "medium", "low"}
    STATUSES = {"active", "completed", "abandoned"}

    def __init__(self, data_dir: str = "data"):
        self._lock = threading.RLock()
        self.path = Path(data_dir) / "sarah_goals.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.goals = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self):
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.goals, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    def _find(self, goal_id: str) -> Dict[str, Any]:
        for goal in self.goals:
            if goal["id"] == goal_id:
                return goal
        raise ValueError("goal not found")

    def list_goals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            result = [goal for goal in self.goals if status is None or goal["status"] == status]
            return json.loads(json.dumps(result))

    def create_goal(self, title: str, description: str = "", priority: str = "medium", parent_id: Optional[str] = None, source: str = "user") -> Dict[str, Any]:
        title = str(title or "").strip()
        priority = str(priority or "medium").lower()
        if not title or len(title) > 200:
            raise ValueError("title must be 1-200 characters")
        if priority not in self.PRIORITIES:
            raise ValueError("priority must be high, medium, or low")
        with self._lock:
            if parent_id:
                parent = self._find(parent_id)
                if parent["status"] != "active":
                    raise ValueError("parent goal must be active")
            now = datetime.now().isoformat()
            goal = {
                "id": uuid.uuid4().hex,
                "title": title,
                "description": str(description or "").strip()[:1000],
                "priority": priority,
                "status": "active",
                "parent_id": parent_id,
                "created_at": now,
                "updated_at": now,
                "source": source,
                "progress": [],
            }
            self.goals.append(goal)
            self._save()
            return json.loads(json.dumps(goal))

    def update_goal(self, goal_id: str, status: Optional[str] = None, priority: Optional[str] = None, progress_note: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            goal = self._find(goal_id)
            if status is not None and status not in self.STATUSES:
                raise ValueError("invalid goal status")
            if priority is not None and priority not in self.PRIORITIES:
                raise ValueError("invalid goal priority")
            if status == "completed" and goal.get("status") == "completed":
                return json.loads(json.dumps(goal))
            if status is not None:
                goal["status"] = status
            if priority is not None:
                goal["priority"] = priority
            if progress_note and str(progress_note).strip():
                goal.setdefault("progress", []).append({
                    "timestamp": datetime.now().isoformat(),
                    "note": str(progress_note).strip()[:2000],
                })
            goal["updated_at"] = datetime.now().isoformat()
            self._save()
            return json.loads(json.dumps(goal))

    def get_context(self, limit: int = 8) -> str:
        goals = self.list_goals("active")[:limit]
        if not goals:
            return "ACTIVE GOALS: none"
        lines = [f"- [{goal['priority']}] {goal['title']} (id={goal['id']})" for goal in goals]
        return "ACTIVE GOALS:\n" + "\n".join(lines)
