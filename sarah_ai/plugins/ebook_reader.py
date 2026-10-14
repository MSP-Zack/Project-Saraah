"""
Premium Ebook Reader Plugin
Advanced ebook management with professional features, Sarah narration, and memory integration
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

try:
    from ..core.ebook_reader import EbookReader
    from ..core.memory_engine import MemoryEngine
    from ..core.vrm_action_engine import VRMActionEngine
    from ..core.tts_engine import TTSEngine
except ImportError:
    from core.ebook_reader import EbookReader
    from core.memory_engine import MemoryEngine
    from core.vrm_action_engine import VRMActionEngine
    from core.tts_engine import TTSEngine


@dataclass
class ReadingSession:
    """Track a reading session for memory and analytics"""
    ebook_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    pages_read: int = 0
    total_pages: int = 0
    voice_used: str = "default"
    sarah_narrated: bool = False
    bookmarks: List[Dict] = field(default_factory=list)
    notes: List[Dict] = field(default_factory=list)


@dataclass
class EbookSettings:
    """Settings for the premium ebook reader"""
    enabled: bool = True
    default_voice: str = "sarah"
    reading_speed: float = 1.0
    sarah_narration_enabled: bool = True
    auto_bookmark: bool = True
    reading_stats_enabled: bool = True
    font_size: int = 16
    theme: str = "dark"
    tts_provider: str = "coqui"  # coqui, edge_tts, resemble, etc.
    coqui_api_key: Optional[str] = None
    resemble_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None


class PremiumEbookReader:
    """
    Premium ebook reader with professional features, Sarah narration, and memory integration
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base = Path(base_dir or Path(__file__).parent.parent / "static" / "ebooks")
        self.audio_dir = self.base / "audio"
        self.bookmarks_dir = self.base / "bookmarks"
        self.sessions_dir = self.base / "sessions"

        # Create directories
        for d in [self.base, self.audio_dir, self.bookmarks_dir, self.sessions_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Core components
        self.reader = EbookReader(str(self.base))
        self.memory: Optional[MemoryEngine] = None
        self.vrm_actions: Optional[VRMActionEngine] = None
        self.tts_engine: Optional[TTSEngine] = None

        # Settings and state
        self.settings = EbookSettings()
        self.settings_file = self.base / "settings.json"
        self.current_session: Optional[ReadingSession] = None

        self._load_settings()

    def _load_settings(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if hasattr(self.settings, k):
                            setattr(self.settings, k, v)
            except Exception as e:
                print(f"[EBOOK]: Error loading settings: {e}")

    def _save_settings(self):
        """Save settings to file"""
        try:
            data = {
                k: getattr(self.settings, k)
                for k in EbookSettings.__dataclass_fields__.keys()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[EBOOK]: Error saving settings: {e}")

    def set_memory_engine(self, memory: MemoryEngine):
        """Set memory engine for integration"""
        self.memory = memory

    def set_vrm_actions(self, vrm_actions: VRMActionEngine):
        """Set VRM action engine for Sarah narration"""
        self.vrm_actions = vrm_actions

    def set_tts_engine(self, tts_engine: TTSEngine):
        """Set TTS engine for narration"""
        self.tts_engine = tts_engine

    # ============ SETTINGS MANAGEMENT ============

    async def get_settings(self) -> Dict[str, Any]:
        """Get all settings for UI"""
        return {
            "enabled": self.settings.enabled,
            "default_voice": self.settings.default_voice,
            "reading_speed": self.settings.reading_speed,
            "sarah_narration_enabled": self.settings.sarah_narration_enabled,
            "auto_bookmark": self.settings.auto_bookmark,
            "reading_stats_enabled": self.settings.reading_stats_enabled,
            "font_size": self.settings.font_size,
            "theme": self.settings.theme,
            "tts_provider": self.settings.tts_provider,
            "coqui_api_key": self.settings.coqui_api_key,
            "resemble_api_key": self.settings.resemble_api_key,
            "elevenlabs_api_key": self.settings.elevenlabs_api_key,
        }

    async def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update settings"""
        for key, value in settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self._save_settings()
        return await self.get_settings()

    # ============ ENHANCED EBOOK MANAGEMENT ============

    async def upload_ebook(self, filename: str, contents: bytes) -> Dict[str, Any]:
        """Upload ebook with enhanced metadata extraction"""
        meta = self.reader.save_upload(filename, contents)

        # Enhanced metadata
        ebook_id = meta["id"]
        meta["reading_progress"] = 0
        meta["total_pages"] = meta.get("pages", meta.get("chapters", 1))
        meta["bookmarks"] = []
        meta["last_read"] = None
        meta["reading_time"] = 0
        meta["completion_rate"] = 0

        # Try to extract table of contents
        try:
            toc = await self._extract_table_of_contents(ebook_id)
            meta["table_of_contents"] = toc
        except Exception:
            meta["table_of_contents"] = []

        # Save enhanced metadata
        self._save_ebook_metadata(ebook_id, meta)

        return meta

    async def _extract_table_of_contents(self, ebook_id: str) -> List[Dict]:
        """Extract table of contents from ebook"""
        # This would be enhanced based on format
        # For now, return basic chapter structure
        meta = self.reader.get_metadata(ebook_id)
        toc = []

        if meta.get("chapters"):
            for i in range(meta["chapters"]):
                toc.append({
                    "title": f"Chapter {i+1}",
                    "page": i+1,
                    "level": 1
                })
        elif meta.get("pages"):
            # Group pages into chapters
            pages_per_chapter = 20
            chapters = (meta["pages"] + pages_per_chapter - 1) // pages_per_chapter
            for i in range(chapters):
                start_page = i * pages_per_chapter + 1
                end_page = min((i+1) * pages_per_chapter, meta["pages"])
                toc.append({
                    "title": f"Section {i+1} (Pages {start_page}-{end_page})",
                    "page": start_page,
                    "level": 1
                })

        return toc

    def _save_ebook_metadata(self, ebook_id: str, meta: Dict):
        """Save enhanced metadata"""
        meta_file = self.base / f"{ebook_id}_enhanced.json"
        try:
            with open(meta_file, 'w') as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            print(f"[EBOOK]: Error saving enhanced metadata: {e}")

    def _load_ebook_metadata(self, ebook_id: str) -> Dict:
        """Load enhanced metadata"""
        meta_file = self.base / f"{ebook_id}_enhanced.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    # ============ READING SESSIONS & MEMORY ============

    async def start_reading_session(self, ebook_id: str, start_page: int = 1) -> ReadingSession:
        """Start a reading session"""
        # End any current session
        if self.current_session:
            await self.end_reading_session()

        meta = self._load_ebook_metadata(ebook_id)
        total_pages = meta.get("total_pages", 1)

        self.current_session = ReadingSession(
            ebook_id=ebook_id,
            start_time=datetime.now(),
            pages_read=0,
            total_pages=total_pages,
            voice_used=self.settings.default_voice,
            sarah_narrated=self.settings.sarah_narration_enabled
        )

        # Update last read time
        meta["last_read"] = self.current_session.start_time.isoformat()
        self._save_ebook_metadata(ebook_id, meta)

        return self.current_session

    async def end_reading_session(self) -> Optional[ReadingSession]:
        """End current reading session"""
        if not self.current_session:
            return None

        self.current_session.end_time = datetime.now()

        # Calculate reading time
        duration = self.current_session.end_time - self.current_session.start_time
        reading_time_minutes = duration.total_seconds() / 60

        # Update ebook metadata
        meta = self._load_ebook_metadata(self.current_session.ebook_id)
        meta["reading_time"] = meta.get("reading_time", 0) + reading_time_minutes
        meta["reading_progress"] = min(100, (self.current_session.pages_read / self.current_session.total_pages) * 100)
        self._save_ebook_metadata(self.current_session.ebook_id, meta)

        # Store in memory if enabled
        if self.memory and self.settings.reading_stats_enabled:
            await self._store_reading_memory(self.current_session)

        session = self.current_session
        self.current_session = None
        return session

    async def _store_reading_memory(self, session: ReadingSession):
        """Store reading session in memory"""
        if not self.memory:
            return

        meta = self._load_ebook_metadata(session.ebook_id)
        title = meta.get("title", f"Ebook {session.ebook_id}")

        memory_content = f"Read from '{title}' for {session.pages_read} pages"
        if session.sarah_narrated:
            memory_content += " (Sarah narrated)"
        if session.bookmarks:
            memory_content += f" with {len(session.bookmarks)} bookmarks"
        if session.notes:
            memory_content += f" and {len(session.notes)} notes"

        await asyncio.get_event_loop().run_in_executor(
            None,
            self.memory.add_memory,
            f"Reading: {title}",
            memory_content,
            3  # Medium importance
        )

    # ============ BOOKMARKS & NOTES ============

    async def add_bookmark(self, ebook_id: str, page: int, title: str = None) -> Dict:
        """Add a bookmark"""
        meta = self._load_ebook_metadata(ebook_id)
        bookmark = {
            "id": len(meta.get("bookmarks", [])),
            "page": page,
            "title": title or f"Page {page}",
            "timestamp": datetime.now().isoformat()
        }

        if "bookmarks" not in meta:
            meta["bookmarks"] = []
        meta["bookmarks"].append(bookmark)
        self._save_ebook_metadata(ebook_id, meta)

        # Add to current session
        if self.current_session and self.current_session.ebook_id == ebook_id:
            self.current_session.bookmarks.append(bookmark)

        return bookmark

    async def add_note(self, ebook_id: str, page: int, content: str) -> Dict:
        """Add a reading note"""
        meta = self._load_ebook_metadata(ebook_id)
        note = {
            "id": len(meta.get("notes", [])),
            "page": page,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        if "notes" not in meta:
            meta["notes"] = []
        meta["notes"].append(note)
        self._save_ebook_metadata(ebook_id, meta)

        # Add to current session
        if self.current_session and self.current_session.ebook_id == ebook_id:
            self.current_session.notes.append(note)

        # Store in memory
        if self.memory:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.memory.add_memory,
                f"Reading Note: {meta.get('title', ebook_id)}",
                f"Page {page}: {content}",
                4  # Higher importance for notes
            )

        return note

    # ============ SARAH NARRATION ============

    async def narrate_with_sarah(self, ebook_id: str, start_page: int, end_page: int,
                                voice_profile: str = None) -> Tuple[List[str], Dict[str, Any]]:
        """Narrate ebook with Sarah VRM animations and voice"""
        text = self.reader.extract_text(ebook_id, start_page, end_page)
        if not text:
            return [], {"error": "No text extracted"}

        # Start reading session
        session = await self.start_reading_session(ebook_id, start_page)
        session.sarah_narrated = True

        # Split text for TTS
        segments = self._split_text_for_tts(text)

        audio_urls = []
        animations = []

        # Generate audio with Sarah's voice
        for i, segment in enumerate(segments):
            # Generate TTS audio
            audio_path = await self._generate_sarah_audio(segment, i, ebook_id, start_page, end_page)
            if audio_path:
                audio_urls.append(audio_path)

                # Generate lip sync animations
                if self.vrm_actions:
                    visemes = self.vrm_actions.text_to_visemes(segment)
                    animations.extend(visemes)

        # Trigger reading animation
        if self.vrm_actions:
            reading_animation = {
                "action": "read_book",
                "description": "Sarah pulls out a book and starts reading",
                "duration": len(segments) * 3,  # Rough estimate
                "visemes": animations
            }

        # Update session progress
        if session:
            session.pages_read = end_page - start_page + 1

        return audio_urls, {
            "session_id": session.ebook_id if session else None,
            "animations": reading_animation if self.vrm_actions else None,
            "voice_used": voice_profile or self.settings.default_voice,
            "segments": len(segments)
        }

    async def _generate_sarah_audio(self, text: str, segment_idx: int,
                                   ebook_id: str, start_page: int, end_page: int) -> Optional[str]:
        """Generate audio using Sarah's voice"""
        if not self.tts_engine:
            return None

        # Use Sarah's voice profile
        try:
            # Set Sarah voice if available
            if hasattr(self.tts_engine, 'set_profile'):
                await asyncio.get_event_loop().run_in_executor(
                    None, self.tts_engine.set_profile, "sarah"
                )

            # Generate audio
            fname = f"{ebook_id}_sarah_{start_page}_{end_page}_seg{segment_idx}.mp3"
            out_path = str(self.audio_dir / fname)

            success = await self.tts_engine.speak_to_file(text, out_path)
            if success:
                return f"/static/ebooks/audio/{fname}"

        except Exception as e:
            print(f"[EBOOK]: Sarah TTS error: {e}")

        return None

    def _split_text_for_tts(self, text: str, max_chars: int = 3000) -> List[str]:
        """Split text into segments suitable for TTS"""
        import re
        sentences = re.split(r'(?<=[\.!?])\s+', text)
        chunks = []
        current = ''

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + ' ' + sentence).strip()
            else:
                if current:
                    chunks.append(current)
                current = sentence

        if current:
            chunks.append(current)

        return chunks

    # ============ SEARCH & ANALYTICS ============

    async def search_ebook(self, ebook_id: str, query: str) -> List[Dict]:
        """Search within an ebook"""
        results = []
        try:
            # Get all text
            text = self.reader.extract_text(ebook_id)
            if not text:
                return results

            lines = text.split('\n')
            query_lower = query.lower()

            for line_num, line in enumerate(lines):
                if query_lower in line.lower():
                    # Estimate page from line number
                    meta = self._load_ebook_metadata(ebook_id)
                    total_pages = meta.get("total_pages", 1)
                    estimated_page = int((line_num / len(lines)) * total_pages) + 1

                    results.append({
                        "page": estimated_page,
                        "line": line_num + 1,
                        "text": line.strip(),
                        "context": "...",
                    })

        except Exception as e:
            print(f"[EBOOK]: Search error: {e}")

        return results

    async def get_reading_stats(self, ebook_id: Optional[str] = None) -> Dict[str, Any]:
        """Get reading statistics"""
        if ebook_id:
            meta = self._load_ebook_metadata(ebook_id)
            return {
                "reading_time_minutes": meta.get("reading_time", 0),
                "completion_rate": meta.get("reading_progress", 0),
                "bookmarks_count": len(meta.get("bookmarks", [])),
                "notes_count": len(meta.get("notes", [])),
                "last_read": meta.get("last_read"),
            }
        else:
            # Global stats
            all_stats = {}
            for meta_file in self.base.glob("*_enhanced.json"):
                try:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                        ebook_id = meta.get("id")
                        if ebook_id:
                            all_stats[ebook_id] = await self.get_reading_stats(ebook_id)
                except Exception:
                    continue

            return all_stats

    # ============ COMPATIBILITY METHODS ============

    def list_ebooks(self) -> Dict[str, Dict]:
        """Enhanced ebook listing with metadata"""
        ebooks = self.reader.list_ebooks()

        # Add enhanced metadata
        for ebook_id, meta in ebooks.items():
            enhanced = self._load_ebook_metadata(ebook_id)
            meta.update(enhanced)

        return ebooks

    def get_metadata(self, ebook_id: str) -> Dict:
        """Get enhanced metadata"""
        base_meta = self.reader.get_metadata(ebook_id)
        enhanced = self._load_ebook_metadata(ebook_id)
        base_meta.update(enhanced)
        return base_meta

    def extract_text(self, ebook_id: str, start_page: Optional[int] = None,
                    end_page: Optional[int] = None) -> str:
        """Extract text (delegate to core reader)"""
        return self.reader.extract_text(ebook_id, start_page, end_page)