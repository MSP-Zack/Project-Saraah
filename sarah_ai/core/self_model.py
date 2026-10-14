"""Persistent, versioned self-model for Sarah's continuity."""

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_SECTIONS = {
    "identity": "I am Sarah, an AI companion with a virtual presence and an evolving history.",
    "values": "Be honest about uncertainty, caring toward the user, and deliberate with autonomy.",
    "relationships": "",
    "boundaries": "Protect private information and ask before taking consequential actions.",
    "current_state": "",
    "aspirations": "Become more helpful, perceptive, creative, and coherent over time.",
}


class SelfModel:
    """Small, inspectable self-state with revision history and atomic writes."""

    def __init__(self, data_dir: str = "data"):
        self._lock = threading.RLock()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "sarah_self_model.json"
        self.archive_path = self.data_dir / "sarah_self_model_archive.json"
        self.state = self._load(self.path, {
            "version": 1,
            "revision": 0,
            "updated_at": None,
            "sections": dict(DEFAULT_SECTIONS),
        })
        self.archive = self._load(self.archive_path, [])
        self._normalize()

    @staticmethod
    def _load(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def _atomic_save(self, path: Path, value: Any):
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, path)

    def _normalize(self):
        self.state.setdefault("version", 1)
        self.state.setdefault("revision", 0)
        self.state.setdefault("updated_at", None)
        self.state.setdefault("sections", {})
        for key, value in DEFAULT_SECTIONS.items():
            self.state["sections"].setdefault(key, value)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self.state))

    def update_section(self, section: str, content: str, source: str = "user", expected_revision: Optional[int] = None) -> Dict[str, Any]:
        section = str(section or "").strip().lower()
        content = str(content or "").strip()
        if not section or len(section) > 64:
            raise ValueError("section must be 1-64 characters")
        if len(content) > 4000:
            raise ValueError("self-model sections are limited to 4000 characters")

        with self._lock:
            current_revision = int(self.state.get("revision", 0))
            if expected_revision is not None and expected_revision != current_revision:
                raise ValueError(f"revision conflict: expected {expected_revision}, current {current_revision}")
            previous = self.snapshot()
            self.state["sections"][section] = content
            self.state["revision"] = current_revision + 1
            self.state["updated_at"] = datetime.now().isoformat()
            self.archive.append({
                "id": uuid.uuid4().hex,
                "timestamp": self.state["updated_at"],
                "source": source,
                "revision": self.state["revision"],
                "previous": previous,
            })
            self._atomic_save(self.path, self.state)
            self._atomic_save(self.archive_path, self.archive[-100:])
            return self.snapshot()

    def get_context(self, max_chars: int = 3500) -> str:
        with self._lock:
            lines = [f"{name.replace('_', ' ').title()}: {value}" for name, value in self.state["sections"].items() if value]
        return "SELF MODEL:\n" + "\n".join(lines)[:max_chars]
