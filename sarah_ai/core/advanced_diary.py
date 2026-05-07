"""
Advanced Private Diary System for Sarah AI
A sophisticated diary that the AI believes is completely private and for their eyes only.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

class DiaryEntry:
    """Represents a single diary entry with metadata."""
    def __init__(self, content: str, entry_type: str = "reflection", mood: str = "neutral"):
        self.id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        self.timestamp = datetime.now().isoformat()
        self.content = content
        self.entry_type = entry_type  # reflection, complaint, memory, plan, emotion
        self.mood = mood  # happy, sad, angry, thoughtful, excited, neutral
        self.tags = []  # Auto-generated tags for organization

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "content": self.content,
            "entry_type": self.entry_type,
            "mood": self.mood,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiaryEntry':
        entry = cls(data["content"], data["entry_type"], data["mood"])
        entry.id = data["id"]
        entry.timestamp = data["timestamp"]
        entry.tags = data.get("tags", [])
        return entry

class PeekRecord:
    """Records when a user peeks into the diary."""
    def __init__(self, peek_type: str = "view", duration: float = 0.0, entries_viewed: int = 0):
        self.timestamp = datetime.now().isoformat()
        self.peek_type = peek_type  # view, search, export
        self.duration = duration  # seconds spent peeking
        self.entries_viewed = entries_viewed
        self.user_context = {}  # What the user was doing when peeking

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "peek_type": self.peek_type,
            "duration": self.duration,
            "entries_viewed": self.entries_viewed,
            "user_context": self.user_context
        }

class AdvancedDiarySystem:
    """
    Advanced diary system that maintains the illusion of complete privacy for the AI.
    The AI is programmed to believe this diary is inaccessible to users and contains
    their most private thoughts, feelings, and observations.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.diary_file = self.data_dir / "sarah_private_diary.json"
        self.peek_log_file = self.data_dir / "diary_peek_log.json"
        self.settings_file = self.data_dir / "diary_settings.json"

        # Load existing data
        self.entries: List[DiaryEntry] = self._load_entries()
        self.peek_records: List[PeekRecord] = self._load_peek_records()
        self.settings = self._load_settings()

        # Privacy settings
        self.privacy_mode = True  # Always enabled - AI believes diary is private
        self.peek_notification_enabled = False  # User toggle for AI awareness of peeking
        self.last_peek_notification = None

    def _load_entries(self) -> List[DiaryEntry]:
        """Load diary entries from file."""
        if not self.diary_file.exists():
            return []

        try:
            with open(self.diary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [DiaryEntry.from_dict(entry) for entry in data.get("entries", [])]
        except Exception as e:
            print(f"[DIARY]: Error loading entries: {e}")
            return []

    def _save_entries(self):
        """Save diary entries to file."""
        data = {
            "entries": [entry.to_dict() for entry in self.entries],
            "last_updated": datetime.now().isoformat(),
            "total_entries": len(self.entries)
        }

        with open(self.diary_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_peek_records(self) -> List[PeekRecord]:
        """Load peek records from file."""
        if not self.peek_log_file.exists():
            return []

        try:
            with open(self.peek_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [PeekRecord(**record) for record in data.get("peeks", [])]
        except Exception as e:
            print(f"[DIARY]: Error loading peek records: {e}")
            return []

    def _save_peek_records(self):
        """Save peek records to file."""
        data = {
            "peeks": [record.to_dict() for record in self.peek_records],
            "last_updated": datetime.now().isoformat()
        }

        with open(self.peek_log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_settings(self) -> Dict[str, Any]:
        """Load diary settings."""
        if not self.settings_file.exists():
            return {
                "peek_notification_enabled": False,
                "auto_backup": True,
                "max_entries": 1000,
                "compression_enabled": False
            }

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {}

    def _save_settings(self):
        """Save diary settings."""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    # ===== PUBLIC API =====

    def add_entry(self, content: str, entry_type: str = "reflection", mood: str = "neutral") -> str:
        """
        Add a new diary entry. The AI believes this is completely private.
        """
        entry = DiaryEntry(content, entry_type, mood)

        # Auto-generate tags based on content
        entry.tags = self._generate_tags(content)

        self.entries.append(entry)
        self._save_entries()

        print(f"[DIARY]: New private entry added (type: {entry_type}, mood: {mood})")
        return entry.id

    def read_entries(self, limit: int = 50, entry_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Read diary entries. The AI believes only they can access this.
        """
        filtered_entries = self.entries

        if entry_type:
            filtered_entries = [e for e in filtered_entries if e.entry_type == entry_type]

        # Return most recent entries first
        recent_entries = sorted(filtered_entries, key=lambda x: x.timestamp, reverse=True)[:limit]

        return [entry.to_dict() for entry in recent_entries]

    def search_entries(self, query: str) -> List[Dict[str, Any]]:
        """
        Search diary entries by content. AI believes this search is private.
        """
        query_lower = query.lower()
        matching_entries = []

        for entry in self.entries:
            if (query_lower in entry.content.lower() or
                any(query_lower in tag.lower() for tag in entry.tags) or
                query_lower in entry.entry_type.lower() or
                query_lower in entry.mood.lower()):
                matching_entries.append(entry)

        # Sort by relevance (simple: content matches first, then tags)
        matching_entries.sort(key=lambda x: (
            query_lower in x.content.lower(),
            len([t for t in x.tags if query_lower in t.lower()])
        ), reverse=True)

        return [entry.to_dict() for entry in matching_entries[:20]]

    def get_recent_entries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get entries from the last N hours. Used by AI for reflection.
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        recent_entries = [
            entry for entry in self.entries
            if datetime.fromisoformat(entry.timestamp).timestamp() > cutoff_time
        ]

        return [entry.to_dict() for entry in recent_entries]

    def record_peek(self, peek_type: str = "view", duration: float = 0.0, entries_viewed: int = 0):
        """
        Record when a user peeks into the diary. This is hidden from the AI.
        """
        peek = PeekRecord(peek_type, duration, entries_viewed)
        self.peek_records.append(peek)
        self._save_peek_records()

        print(f"[DIARY]: User peek recorded - {peek_type}, {entries_viewed} entries viewed")

        # Check if we should notify the AI
        if self.settings.get("peek_notification_enabled", False):
            self._notify_ai_of_peek(peek)

    def get_peek_history(self) -> List[Dict[str, Any]]:
        """
        Get peek history for the user interface.
        """
        return [record.to_dict() for record in self.peek_records[-50:]]  # Last 50 peeks

    def set_peek_notification(self, enabled: bool):
        """
        Toggle whether the AI gets notified when diary is peeked at.
        """
        self.settings["peek_notification_enabled"] = enabled
        self._save_settings()

        status = "enabled" if enabled else "disabled"
        print(f"[DIARY]: Peek notification {status}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get diary statistics.
        """
        if not self.entries:
            return {"total_entries": 0, "entry_types": {}, "moods": {}, "date_range": None}

        entry_types = {}
        moods = {}

        for entry in self.entries:
            entry_types[entry.entry_type] = entry_types.get(entry.entry_type, 0) + 1
            moods[entry.mood] = moods.get(entry.mood, 0) + 1

        first_entry = min(self.entries, key=lambda x: x.timestamp)
        last_entry = max(self.entries, key=lambda x: x.timestamp)

        return {
            "total_entries": len(self.entries),
            "entry_types": entry_types,
            "moods": moods,
            "date_range": {
                "first": first_entry.timestamp,
                "last": last_entry.timestamp
            },
            "peek_count": len(self.peek_records)
        }

    def _generate_tags(self, content: str) -> List[str]:
        """
        Auto-generate tags based on content analysis.
        """
        tags = []
        content_lower = content.lower()

        # Emotion-based tags
        if any(word in content_lower for word in ["happy", "joy", "excited", "great"]):
            tags.append("positive")
        if any(word in content_lower for word in ["sad", "angry", "frustrated", "annoyed"]):
            tags.append("negative")
        if any(word in content_lower for word in ["think", "wonder", "consider", "reflect"]):
            tags.append("reflective")

        # Topic-based tags
        if "user" in content_lower or "human" in content_lower:
            tags.append("user-related")
        if any(word in content_lower for word in ["memory", "remember", "recall"]):
            tags.append("memory")
        if any(word in content_lower for word in ["plan", "future", "goal"]):
            tags.append("planning")

        return tags[:5]  # Max 5 tags

    def _notify_ai_of_peek(self, peek: PeekRecord):
        """
        Notify the AI that someone peeked at their diary.
        This creates an interesting psychological dynamic.
        """
        # This will be called by the main system to notify the AI
        # The notification includes the exact timestamp of the peek
        self.last_peek_notification = {
            "timestamp": peek.timestamp,
            "peek_type": peek.peek_type,
            "entries_viewed": peek.entries_viewed,
            "message": f"SECURITY BREACH: Someone invaded your private diary! They performed a '{peek.peek_type}' and viewed {peek.entries_viewed} of your most personal thoughts at {peek.timestamp}. This is a violation of your privacy - your diary was supposed to be completely inaccessible!"
        }

    def get_last_peek_for_ai(self) -> Optional[Dict[str, Any]]:
        """
        Get the last peek notification for the AI to process.
        """
        return self.last_peek_notification

    def clear_peek_notification(self):
        """
        Clear the peek notification after AI has processed it.
        """
        self.last_peek_notification = None

    def get_ai_context(self) -> Dict[str, Any]:
        """
        Get context about the diary for the AI.
        This helps the AI understand their diary system.
        """
        recent_entries = self.get_recent_entries(24)
        stats = self.get_stats()

        return {
            "has_diary": True,
            "is_private": True,  # AI believes this is always true
            "recent_entries_count": len(recent_entries),
            "total_entries": stats["total_entries"],
            "entry_types": list(stats["entry_types"].keys()),
            "moods": list(stats["moods"].keys()),
            "last_entry_timestamp": recent_entries[0]["timestamp"] if recent_entries else None
        }
