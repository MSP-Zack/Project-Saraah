"""Guarded autonomous heartbeat state for Sarah."""

import json
import os
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


class HeartbeatEngine:
    """Persisted heartbeat policy and bounded activity history."""

    def __init__(self, data_dir: str = "data"):
        self._lock = threading.RLock()
        self.path = Path(data_dir) / "sarah_heartbeat.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> Dict[str, Any]:
        defaults = {
            "enabled": False,
            "interval_minutes": 30,
            "max_runs_per_day": 8,
            "min_idle_minutes": 15,
            "last_run_at": None,
            "run_day": None,
            "runs_today": 0,
            "running": False,
            "cancel_requested": False,
            "current_reason": None,
            "current_decision": None,
            "history": [],
        }
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                defaults.update(loaded if isinstance(loaded, dict) else {})
            except (OSError, json.JSONDecodeError):
                pass
        if defaults.get("running"):
            defaults["running"] = False
            defaults["cancel_requested"] = False
            defaults["current_reason"] = None
            defaults["current_decision"] = None
            defaults["history"] = ([
                {
                    "id": uuid.uuid4().hex,
                    "timestamp": datetime.now().isoformat(),
                    "status": "recovered",
                    "summary": "Recovered an interrupted heartbeat after restart.",
                }
            ] + defaults.get("history", []))[:100]
        return defaults

    def _save(self):
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self.state))

    def update_settings(self, enabled: Optional[bool] = None, interval_minutes: Optional[int] = None,
                        max_runs_per_day: Optional[int] = None, min_idle_minutes: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            if enabled is not None:
                self.state["enabled"] = bool(enabled)
            if interval_minutes is not None:
                self.state["interval_minutes"] = max(5, min(1440, int(interval_minutes)))
            if max_runs_per_day is not None:
                self.state["max_runs_per_day"] = max(1, min(100, int(max_runs_per_day)))
            if min_idle_minutes is not None:
                self.state["min_idle_minutes"] = max(0, min(1440, int(min_idle_minutes)))
            if not self.state["enabled"]:
                self.state["cancel_requested"] = True
            self._save()
            return self.snapshot()

    def request_cancel(self) -> Dict[str, Any]:
        with self._lock:
            self.state["cancel_requested"] = True
            self._save()
            return self.snapshot()

    def begin_run(self, now: Optional[datetime] = None, reason: str = "") -> Optional[str]:
        current = now or datetime.now()
        day = current.strftime("%Y-%m-%d")
        with self._lock:
            if not self.state["enabled"] or self.state["running"]:
                return None
            if self.state.get("run_day") != day:
                self.state["run_day"] = day
                self.state["runs_today"] = 0
            if self.state["runs_today"] >= self.state["max_runs_per_day"]:
                return None
            last_run = self.state.get("last_run_at")
            if last_run:
                elapsed = current - datetime.fromisoformat(last_run)
                if elapsed < timedelta(minutes=self.state["interval_minutes"]):
                    return None
            self.state["running"] = True
            self.state["cancel_requested"] = False
            self.state["current_reason"] = str(reason or "scheduled continuity check")[:500]
            self.state["current_decision"] = None
            self.state["last_run_at"] = current.isoformat()
            self.state["runs_today"] += 1
            run_id = uuid.uuid4().hex
            self._save()
            return run_id

    def is_cancel_requested(self) -> bool:
        with self._lock:
            return bool(self.state.get("cancel_requested"))

    def finish_run(self, run_id: str, status: str, summary: str = "", decision: str = "observe") -> Dict[str, Any]:
        with self._lock:
            self.state["running"] = False
            self.state["cancel_requested"] = False
            self.state["history"] = ([
                {
                    "id": run_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": status,
                    "reason": self.state.get("current_reason") or "scheduled continuity check",
                    "decision": decision,
                    "summary": summary[:1000],
                }
            ] + self.state.get("history", []))[:100]
            self.state["current_reason"] = None
            self.state["current_decision"] = None
            self._save()
            return self.snapshot()
