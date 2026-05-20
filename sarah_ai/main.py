"""
Sarah AI Companion - Main Server
A comprehensive AI companion with VRM avatar, voice, vision, and computer control.
"""

import os
import sys
import json
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import shutil
import time
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Add core and plugins to path
sys.path.insert(0, str(Path(__file__).parent))

from core.llm_brain import LLMBrain
from core.tts_engine import TTSEngine
from core.stt_engine_advanced import STTEngine
from core.vision_engine import VisionEngine
from core.screen_engine import ScreenEngine
from core.memory_engine import MemoryEngine
from core.permission_manager import PermissionManager
from core.action_engine import ActionEngine
from core.vrm_action_engine import VRMActionEngine
from plugins.plugin_manager import PluginManager
from core.ebook_reader import EbookReader
from plugins.ebook_reader import PremiumEbookReader

app = FastAPI(title="Sarah AI Companion", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ROOT ROUTE ==========
@app.get("/")
def root():
    """Serve the React app."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")

# ========== GLOBALS ==========
sarah_brain: Optional[LLMBrain] = None
tts_engine: Optional[TTSEngine] = None
stt_engine: Optional[STTEngine] = None
vision_engine: Optional[VisionEngine] = None
screen_engine: Optional[ScreenEngine] = None
memory_engine: Optional[MemoryEngine] = None
permission_manager: Optional[PermissionManager] = None
action_engine: Optional[ActionEngine] = None
vrm_actions: Optional[VRMActionEngine] = None
plugin_manager: Optional[PluginManager] = None
ebook_reader: Optional[PremiumEbookReader] = None
diary_system = None  # Advanced diary system

# WebSocket connections
connected_clients: list = []

# Runtime state
runtime_state = {
    "screen_vision_enabled": False,
    "webcam_vision_enabled": False,
    "thinking_mode": False,
    "proactive_mode": True,
    "rp_mode": False,
    "current_voice_profile": "default",
    "current_outfit": "default",
    "sarah_status": "idle",
    "last_activity": datetime.now().isoformat(),
    "screen_capture_count": 0
}
# Manual VRM control state (user can toggle whether manual VRM actions are hidden from the LLM)
runtime_state.setdefault('vrm_manual_hidden', True)
runtime_state.setdefault('manual_vrm_actions', [])
runtime_state.setdefault('last_manual_action_time', None)

# Task handle for delayed manual VRM notifications
manual_vrm_notify_task = None

# ========== INIT ==========
def initialize():
    """Initialize all subsystems."""
    global sarah_brain, tts_engine, stt_engine, vision_engine
    global screen_engine, memory_engine, permission_manager
    global action_engine, vrm_actions, plugin_manager
    
    print("=" * 60)
    print("  SARAH AI COMPANION v2.0 - INITIALIZING")
    print("=" * 60)
    
    # Permission manager
    permission_manager = PermissionManager()
    print("[INIT]: Permission manager ready.")
    
    # Memory engine
    memory_engine = MemoryEngine()
    print(f"[INIT]: Memory loaded - {memory_engine.get_stats()}")
    
    # VRM action engine
    vrm_actions = VRMActionEngine()
    print(f"[INIT]: VRM actions loaded - {len(vrm_actions.expressions)} expressions, {len(vrm_actions.animations)} animations.")
    
    # Advanced Diary System
    global diary_system
    from core.advanced_diary import AdvancedDiarySystem
    diary_system = AdvancedDiarySystem()
    print(f"[INIT]: Advanced diary system ready - {diary_system.get_stats()['total_entries']} private entries.")
    
    # LLM Brain
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Try to load from config
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path) as f:
                cfg = json.load(f)
                api_key = cfg.get("gemini_api_key", "")
    
    sarah_brain = LLMBrain(
        mode="gemini",
        api_key=api_key or "YOUR_API_KEY_HERE",
        memory_engine=memory_engine,
        permission_manager=permission_manager,
        vrm_actions=vrm_actions,
        diary_system=diary_system
    )
    print("[INIT]: Sarah's brain online.")
    
    # TTS Engine
    tts_engine = TTSEngine()
    print("[INIT]: TTS engine ready.")
    
    # STT Engine
    try:
        stt_engine = STTEngine()
        # Set up callbacks for advanced features
        stt_engine.on_transcription = handle_stt_transcription
        stt_engine.on_interruption = handle_stt_interruption
        stt_engine.on_emotion_detected = handle_emotion_detected
        print("[INIT]: Advanced STT engine ready with real-time conversation support.")
    except Exception as e:
        print(f"[INIT]: STT engine failed: {e}")
    
    # Vision Engine
    vision_engine = VisionEngine()
    print("[INIT]: Vision engine ready.")
    
    # Screen Engine
    screen_engine = ScreenEngine()
    print("[INIT]: Screen capture engine ready.")
    
    # Action Engine
    action_engine = ActionEngine()
    print(f"[INIT]: Action engine ready - {action_engine.get_status()}")
    
    # Plugin Manager
    plugin_manager = PluginManager()
    # Prefer v2 plugins and only load fallback legacy plugins if needed.
    if not plugin_manager.load_plugin("chess_v2"):
        plugin_manager.load_plugin("chess_game")
    if not plugin_manager.load_plugin("tamagotchi_v2"):
        plugin_manager.load_plugin("tamagotchi_pet")
    plugin_manager.load_plugin("collab_editor")
    plugin_manager.load_plugin("image_generation")
    print(f"[INIT]: Plugins loaded - {plugin_manager.list_plugins()}")

    # Ebook reader (premium)
    ebook_reader = PremiumEbookReader()
    if memory_engine:
        ebook_reader.set_memory_engine(memory_engine)
    if vrm_actions:
        ebook_reader.set_vrm_actions(vrm_actions)
    if tts_engine:
        ebook_reader.set_tts_engine(tts_engine)
    print(f"[INIT]: Premium ebook reader initialized at {ebook_reader.base}")
    print("=" * 60)
    print("  SARAH IS ONLINE AND READY")
    print("=" * 60)


# ========== REQUEST MODELS ==========
class ChatMessage(BaseModel):
    message: str
    tts_enabled: bool = True
    use_vision: bool = False

class PermissionUpdate(BaseModel):
    key: str
    enabled: bool

class MemoryEdit(BaseModel):
    memory_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[int] = None

class DiaryUpdate(BaseModel):
    action: str
    content: Optional[str] = None

class ConfigUpdate(BaseModel):
    system_prompt: Optional[str] = None
    voice_profile: Optional[str] = None
    thinking_mode: Optional[bool] = None
    proactive_mode: Optional[bool] = None
    rp_mode: Optional[bool] = None

class ImageDownloadRequest(BaseModel):
    url: str
    filename: Optional[str] = None

class ImageGenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = "creative"
    count: Optional[int] = 1
    provider: Optional[str] = None
    model: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    strength: Optional[float] = 0.8
    image_input: Optional[str] = None
    save_images: Optional[bool] = None
    sfw_only: Optional[bool] = None


class ImageSettingsUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    sfw_only: Optional[bool] = None
    allow_sarah_generation: Optional[bool] = None
    save_images: Optional[bool] = None
    huggingface_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    local_comfyui_url: Optional[str] = None
    default_quality: Optional[str] = None
    default_width: Optional[int] = None
    default_height: Optional[int] = None
    sarah_generation_cooldown: Optional[int] = None


@app.get("/api/status")
def get_status():
    """Return runtime status and subsystem summaries."""
    return {
        "runtime": runtime_state,
        "action_status": action_engine.get_status() if action_engine else {},
        "memory_stats": memory_engine.get_stats() if memory_engine else {},
        "voice_profiles": tts_engine.profiles if tts_engine else {},
        "plugins": plugin_manager.list_plugins() if plugin_manager else []
    }


@app.get("/api/tts/voices")
def get_tts_voices():
    """Return available TTS voices and profiles from the TTS engine."""
    if tts_engine:
        return tts_engine.get_voice_list()
    return {"voices": {}, "profiles": {}, "current": "default"}


@app.get("/api/tts/preview")
async def preview_tts(profile: str = "default"):
    """Generate a short preview audio for the given profile or voice key and return the URL."""
    if not tts_engine:
        return {"success": False, "error": "TTS engine not initialized"}

    # If a profile name is provided, map to voice key
    voice_key = profile
    if profile in tts_engine.profiles:
        voice_key = tts_engine.profiles[profile].get("voice", profile)

    try:
        preview_path = await tts_engine.preview_voice(voice_key)
        return {"success": True, "preview_url": "/static/preview.mp3" if preview_path else None}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/tts/clone")
async def clone_tts_sample(display_name: str = Form(...), file: UploadFile = File(...)):
    """Upload a short sample clip to register a custom voice sample.
    NOTE: This stores a sample and registers a custom voice ID. Real voice cloning/synthesis
    is not implemented here — this is a scaffold for future integration.
    """
    samples_dir = Path(__file__).parent / "static" / "voices" / "samples"
    os.makedirs(samples_dir, exist_ok=True)

    # Save uploaded file
    ext = Path(file.filename).suffix or ".wav"
    cid = str(uuid.uuid4())[:8]
    filename = f"{cid}{ext}"
    dest = samples_dir / filename
    try:
        contents = await file.read()
        with open(dest, "wb") as f:
            f.write(contents)
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Register custom voice in TTS engine
    if tts_engine:
        entry = tts_engine.add_custom_voice(cid, str(dest), {"name": display_name, "status": "uploaded", "created_at": datetime.now().isoformat()})
        # Schedule background processing to attempt provider cloning if configured
        try:
            asyncio.create_task(process_clone_job(cid))
        except Exception:
            pass

    return {"success": True, "id": cid, "sample_url": f"/static/voices/samples/{filename}", "profile_key": f"custom:{cid}"}


async def process_clone_job(custom_id: str):
    """Background task to process an uploaded sample via configured provider (if any).
    Currently this will mark the sample as ready and attach a note if no provider is configured.
    """
    if not tts_engine:
        return
    try:
        entry = tts_engine.custom_voices.get(custom_id)
        if not entry:
            return
        # mark processing
        entry["status"] = "processing"

        # Provider processing: prefer COQUI (free self-hosted) if configured,
        # otherwise prefer Resemble if an API key is present. If none configured,
        # keep sample available for preview only.
        coqui_url = os.environ.get("COQUI_TTS_URL")
        api_key = os.environ.get("RESEMBLE_API_KEY")

        if coqui_url:
            try:
                # Lazy import to avoid requiring adapter at startup
                from core.tts_providers.coqui import CoquiAdapter
                adapter = CoquiAdapter()
                provider_id = await asyncio.to_thread(adapter.create_voice_from_sample, entry.get("path"), entry.get("name"))
                entry["provider"] = "coqui"
                entry["provider_id"] = provider_id
                entry["status"] = "ready"
                entry["note"] = f"Cloned via Coqui (id={provider_id})"
            except Exception as e:
                entry["status"] = "failed"
                entry["error"] = str(e)
        elif api_key:
            # Implement provider adapter here (Resemble integration can be added later).
            entry["provider"] = "resemble"
            entry["provider_id"] = None
            entry["status"] = "ready"
            entry["note"] = "Provider configured but automatic cloning adapter not implemented in this build. See VOICE_CLONE.md to enable."
        else:
            entry["status"] = "ready"
            entry["note"] = "Sample uploaded and available for preview. No provider configured."
    except Exception as e:
        try:
            tts_engine.custom_voices[custom_id]["status"] = "failed"
            tts_engine.custom_voices[custom_id]["error"] = str(e)
        except:
            pass


@app.post("/api/tts/custom/{custom_id}/process")
def trigger_custom_processing(custom_id: str):
    """Trigger processing of a custom voice sample (manual)."""
    if not tts_engine:
        return {"success": False, "error": "TTS engine not initialized"}
    try:
        asyncio.create_task(process_clone_job(custom_id))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/tts/custom/{custom_id}")
def get_custom_voice(custom_id: str):
    if not tts_engine:
        return {"success": False, "error": "TTS engine not initialized"}
    entry = tts_engine.custom_voices.get(custom_id)
    if not entry:
        return {"success": False, "error": "Not found"}
    return {"success": True, "custom": entry}


@app.get("/api/tts/custom/list")
def list_custom_voices():
    if tts_engine:
        return {"custom_voices": tts_engine.list_custom_voices()}
    return {"custom_voices": {}}


@app.delete("/api/tts/custom/{custom_id}")
def delete_custom_voice(custom_id: str):
    """Delete a previously uploaded custom voice sample."""
    if not tts_engine:
        return {"success": False, "error": "TTS engine not initialized"}
    ok = tts_engine.remove_custom_voice(custom_id)
    if ok:
        return {"success": True}
    return {"success": False, "error": "Custom voice not found or could not be removed"}


@app.get("/api/tts/providers")
def list_tts_providers():
    """Return supported TTS providers for UI selection."""
    providers = [
        {"key": "edge_tts", "name": "Edge (local)", "notes": "Built-in edge_tts voices"},
        {"key": "resemble", "name": "Resemble.ai (cloud)", "notes": "Cloud voice cloning (requires API key)"},
        {"key": "coqui", "name": "Coqui (self-host)", "notes": "Self-hosted TTS/voice cloning"},
        {"key": "none", "name": "Manual / None", "notes": "No automatic TTS provider selected"},
    ]
    return {"providers": providers}


### Notes / Sticky Notes API
NOTES_FILE = Path(__file__).parent / "data" / "notes.json"
os.makedirs(NOTES_FILE.parent, exist_ok=True)

def _load_notes():
    if NOTES_FILE.exists():
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def _save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


@app.get("/api/notes")
def get_notes():
    notes = _load_notes()
    return {"notes": notes}


class NoteCreate(BaseModel):
    title: str
    content: str
    pinned: Optional[bool] = False


@app.post("/api/notes")
def create_note(note: NoteCreate):
    notes = _load_notes()
    nid = str(int(time.time() * 1000))
    entry = {"id": nid, "title": note.title, "content": note.content, "pinned": note.pinned, "created_at": datetime.now().isoformat()}
    notes.insert(0, entry)
    _save_notes(notes)

    # Broadcast note creation to connected clients so they can show notifications
    asyncio.create_task(broadcast_message({"action": "note_created", "note": entry, "timestamp": datetime.now().isoformat()}))

    return {"success": True, "note": entry}


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: str):
    notes = _load_notes()
    new = [n for n in notes if n.get("id") != note_id]
    _save_notes(new)
    return {"success": True}

@app.get("/api/permissions")
def get_permissions():
    """Get all permission settings."""
    return permission_manager.get_all() if permission_manager else {}

@app.post("/api/permissions")
def update_permission(update: PermissionUpdate):
    """Update a permission."""
    if permission_manager:
        permission_manager.set_permission(update.key, update.enabled)
        if sarah_brain:
            sarah_brain._setup_tools()
        return {"success": True, "permissions": permission_manager.get_all()}
    return {"success": False, "error": "Permission manager not initialized"}

@app.get("/api/memory")
def get_memory():
    """Get all memory entries."""
    if memory_engine:
        return {
            "conversations": memory_engine.conversations,
            "memories": memory_engine.memories,
            "facts": memory_engine.facts,
            "stats": memory_engine.get_stats()
        }
    return {"success": False, "error": "Memory engine not initialized"}

@app.get("/api/memory/conversations")
def get_conversations(limit: int = 100):
    """Get conversation history."""
    if memory_engine:
        return {"conversations": memory_engine.get_conversation_history(limit)}
    return {"success": False, "error": "Memory engine not initialized"}

@app.post("/api/memory/edit")
def edit_memory(edit: MemoryEdit):
    """Edit a memory entry."""
    if memory_engine:
        success = memory_engine.edit_memory(edit.memory_id, edit.title, edit.content, edit.importance)
        return {"success": success}
    return {"success": False, "error": "Memory engine not initialized"}

@app.delete("/api/memory/{memory_id}")
def delete_memory(memory_id: int):
    """Delete a memory entry."""
    if memory_engine:
        success = memory_engine.delete_memory(memory_id)
        return {"success": success}
    return {"success": False, "error": "Memory engine not initialized"}

@app.get("/api/memory/search")
def search_memory(query: str):
    """Search memory."""
    if memory_engine:
        return {"results": memory_engine.search_memories(query)}
    return {"success": False, "error": "Memory engine not initialized"}

@app.get("/api/diary")
def get_diary():
    diary_path = Path(__file__).parent / "private_diary.txt"
    if diary_path.exists():
        return {"content": diary_path.read_text(encoding="utf-8")}
    return {"content": ""}

@app.post("/api/diary")
def update_diary(update: DiaryUpdate):
    diary_path = Path(__file__).parent / "private_diary.txt"
    diary_path.parent.mkdir(parents=True, exist_ok=True)
    if update.action == "append":
        with diary_path.open("a", encoding="utf-8") as f:
            f.write((update.content or "") + "\n")
        return {"success": True}
    if update.action == "overwrite":
        diary_path.write_text(update.content or "", encoding="utf-8")
        return {"success": True}
    if update.action == "read":
        return {"content": diary_path.read_text(encoding="utf-8") if diary_path.exists() else ""}
    return {"success": False, "error": "Unknown diary action"}

@app.post("/api/config")
def update_config(config: ConfigUpdate):
    """Update Sarah's configuration."""
    global runtime_state
    
    if config.system_prompt is not None and sarah_brain:
        sarah_brain.set_system_prompt(config.system_prompt)
    
    if config.voice_profile is not None and tts_engine:
        tts_engine.set_profile(config.voice_profile)
        runtime_state["current_voice_profile"] = config.voice_profile
    
    if config.thinking_mode is not None:
        runtime_state["thinking_mode"] = config.thinking_mode
        if sarah_brain:
            sarah_brain.thinking_mode = config.thinking_mode
    
    if config.proactive_mode is not None:
        runtime_state["proactive_mode"] = config.proactive_mode

    if hasattr(config, 'rp_mode') and config.rp_mode is not None:
        runtime_state["rp_mode"] = config.rp_mode
        if sarah_brain:
            sarah_brain.rp_mode = config.rp_mode
    
    return {"success": True, "config": runtime_state}

@app.get("/api/vrm/actions")
def get_vrm_actions():
    """Get all VRM actions for reference."""
    if vrm_actions:
        return vrm_actions.get_all_actions()
    return {}


@app.get('/api/tools')
def get_tools():
    """Return available tools and loaded plugins for the frontend/LLM."""
    tools = {
        "plugins": plugin_manager.list_plugins() if plugin_manager else [],
        "vrm_actions_available": bool(vrm_actions),
        "description": "List of plugins and capabilities available to the assistant"
    }
    return tools


# ========== EBOOKS / READER ==========


@app.post('/api/ebooks/upload')
async def upload_ebook(file: UploadFile = File(...)):
    """Upload an ebook file (PDF, EPUB, or TXT)."""
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        contents = await file.read()
        meta = ebook_reader.save_upload(file.filename, contents)
        return {"success": True, "ebook": meta}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get('/api/ebooks/list')
def list_ebooks():
    if not ebook_reader:
        return {"ebooks": {}}
    return {"ebooks": ebook_reader.list_ebooks()}


@app.get('/api/ebooks/meta/{ebook_id}')
def ebook_meta(ebook_id: str):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        meta = ebook_reader.get_metadata(ebook_id)
        return {"success": True, "meta": meta}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get('/api/ebooks/text/{ebook_id}')
def ebook_text(ebook_id: str, start_page: int = None, end_page: int = None):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        text = ebook_reader.extract_text(ebook_id, start_page, end_page)
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _split_text_for_tts(text: str, max_chars: int = 3000) -> List[str]:
    """Split text into near-sentence chunks under max_chars."""
    import re
    sentences = re.split(r'(?<=[\.!?])\s+', text)
    chunks: List[str] = []
    cur = ''
    for s in sentences:
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + ' ' + s).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    # If a single sentence is too long, break it forcefully
    out: List[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            out.append(c)
        else:
            # force split
            for i in range(0, len(c), max_chars):
                out.append(c[i:i+max_chars])
    return out


@app.post('/api/ebooks/read')
async def read_ebook(ebook_id: str = Form(...), start_page: int = Form(None), end_page: int = Form(None), profile: str = Form(None), rate: str = Form(None)):
    """Generate TTS audio for the requested ebook segment and return audio URLs.

    Returns a list of generated audio files (segments) to play sequentially.
    """
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    if not tts_engine:
        return {"success": False, "error": "TTS engine not initialized"}

    try:
        text = ebook_reader.extract_text(ebook_id, start_page, end_page)
        if not text:
            return {"success": False, "error": "No text extracted"}

        # Optionally set profile
        if profile:
            try:
                tts_engine.set_profile(profile)
            except Exception:
                pass

        # Optionally set playback rate (e.g. '+10%', '-10%')
        if rate:
            try:
                tts_engine.rate = rate
            except Exception:
                pass

        segments = _split_text_for_tts(text, max_chars=3000)
        audio_urls: List[str] = []
        base_audio_dir = Path(__file__).parent / 'static' / 'ebooks' / 'audio'
        os.makedirs(base_audio_dir, exist_ok=True)

        safe_start = start_page or 0
        safe_end = end_page or 0

        for idx, seg in enumerate(segments):
            fname = f"{ebook_id}_{safe_start}_{safe_end}_seg{idx}.mp3"
            out_path = str(base_audio_dir / fname)
            try:
                ap = await tts_engine.speak_to_file(seg, out_path)
                if ap:
                    audio_urls.append(f"/static/ebooks/audio/{fname}")
            except Exception as e:
                print(f"[EBOOK READ]: TTS error for segment {idx}: {e}")

        return {"success": True, "audio_urls": audio_urls}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== PREMIUM EBOOK FEATURES ==========

@app.get("/api/ebooks/settings")
async def get_ebook_settings():
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        settings = await ebook_reader.get_settings()
        return {"success": True, **settings}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ebooks/settings")
async def update_ebook_settings(settings: Dict[str, Any]):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        updated = await ebook_reader.update_settings(settings)
        return {"success": True, **updated}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ebooks/start_session")
async def start_reading_session(ebook_id: str = Form(...), start_page: int = Form(1)):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        session = await ebook_reader.start_reading_session(ebook_id, start_page)
        return {"success": True, "session": {
            "ebook_id": session.ebook_id,
            "start_time": session.start_time.isoformat(),
            "total_pages": session.total_pages
        }}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ebooks/end_session")
async def end_reading_session():
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        session = await ebook_reader.end_reading_session()
        if session:
            return {"success": True, "session": {
                "ebook_id": session.ebook_id,
                "pages_read": session.pages_read,
                "duration_minutes": (session.end_time - session.start_time).total_seconds() / 60
            }}
        return {"success": True, "message": "No active session"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ebooks/bookmark")
async def add_bookmark(ebook_id: str = Form(...), page: int = Form(...), title: str = Form(None)):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        bookmark = await ebook_reader.add_bookmark(ebook_id, page, title)
        return {"success": True, "bookmark": bookmark}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ebooks/note")
async def add_note(ebook_id: str = Form(...), page: int = Form(...), content: str = Form(...)):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        note = await ebook_reader.add_note(ebook_id, page, content)
        return {"success": True, "note": note}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ebooks/search/{ebook_id}")
async def search_ebook(ebook_id: str, query: str):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        results = await ebook_reader.search_ebook(ebook_id, query)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ebooks/stats")
async def get_ebook_stats(ebook_id: str = None):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        stats = await ebook_reader.get_reading_stats(ebook_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ebooks/sarah_read")
async def sarah_read_ebook(ebook_id: str = Form(...), start_page: int = Form(...),
                          end_page: int = Form(...), voice_profile: str = Form(None)):
    if not ebook_reader:
        return {"success": False, "error": "Ebook reader not initialized"}
    try:
        audio_urls, metadata = await ebook_reader.narrate_with_sarah(
            ebook_id, start_page, end_page, voice_profile
        )
        return {"success": True, "audio_urls": audio_urls, "metadata": metadata}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== OUTFIT MANAGEMENT ==========

@app.get("/api/vrm/models")
def get_available_models():
    """Get list of available VRM models for outfit switching."""
    if vrm_actions:
        outfits = vrm_actions.get_available_outfits()
        return {
            "models": outfits,
            "current": runtime_state.get("current_outfit", "default")
        }
    return {"models": {}, "current": "default"}

@app.get("/api/vrm/outfit")
def get_current_outfit():
    """Get the currently selected outfit."""
    return {
        "outfit": runtime_state.get("current_outfit", "default"),
        "outfit_data": vrm_actions.get_outfit(runtime_state.get("current_outfit", "default")) if vrm_actions else None
    }

@app.post("/api/vrm/outfit")
def set_outfit(outfit_id: str):
    """Switch to a different VRM outfit."""
    if not vrm_actions:
        return {"success": False, "error": "VRM actions not initialized"}
    
    outfit = vrm_actions.get_outfit(outfit_id)
    if not outfit:
        return {"success": False, "error": f"Outfit '{outfit_id}' not found"}
    
    # Update runtime state
    runtime_state["current_outfit"] = outfit_id
    
    # Broadcast outfit change to all clients
    asyncio.create_task(broadcast_message({
        "action": "outfit_changed",
        "outfit_id": outfit_id,
        "outfit_data": outfit,
        "timestamp": datetime.now().isoformat()
    }))
    
    return {
        "success": True,
        "outfit": outfit_id,
        "outfit_data": outfit
    }

# ========== ADVANCED VRM SYSTEM ==========

@app.get("/api/vrm/advanced/animations")
def get_advanced_animations():
    """Get all animations from advanced VRM system"""
    try:
        from core.vrm_advanced import VRMAdvancedEngine
        engine = VRMAdvancedEngine()
        return {
            "success": True,
            "animations": engine.get_all_animations(),
            "stats": engine.get_stats()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/vrm/advanced/expressions")
def get_advanced_expressions():
    """Get all expressions from advanced VRM system"""
    try:
        from core.vrm_advanced import VRMAdvancedEngine
        engine = VRMAdvancedEngine()
        return {
            "success": True,
            "expressions": engine.get_all_expressions()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/vrm/advanced/outfits")
def get_advanced_outfits():
    """Get all outfits from advanced VRM system"""
    try:
        from core.vrm_advanced import VRMAdvancedEngine
        engine = VRMAdvancedEngine()
        return {
            "success": True,
            "outfits": engine.get_all_outfits()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/vrm/advanced/accessories")
def get_advanced_accessories():
    """Get all accessories from advanced VRM system"""
    try:
        from core.vrm_advanced import VRMAdvancedEngine
        engine = VRMAdvancedEngine()
        return {
            "success": True,
            "accessories": engine.get_all_accessories()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/vrm/camera-tracking")
def update_camera_tracking(data: dict):
    """Update camera tracking data from frontend"""
    try:
        from core.camera_awareness import CameraAwarenessSystem, Vector3
        
        # Create or retrieve the tracking system
        if not hasattr(update_camera_tracking, '_tracking_system'):
            update_camera_tracking._tracking_system = CameraAwarenessSystem()
        
        tracker = update_camera_tracking._tracking_system
        
        # Update position
        tracker.update_camera_position(
            data.get('position_x', 0),
            data.get('position_y', 0),
            data.get('position_z', 0)
        )
        
        # Update rotation
        tracker.update_camera_rotation(
            data.get('rotation_x', 0),
            data.get('rotation_y', 0),
            data.get('rotation_z', 0)
        )
        
        # Update FOV
        if 'fov' in data:
            tracker.update_camera_fov(data['fov'])
        
        # Get current tracking state
        tracking = tracker.get_tracking_data()
        
        # Check if model should react
        should_react, reaction_type = tracker.should_model_react_to_camera()
        
        if should_react:
            # Notify AI brain about camera interaction
            asyncio.create_task(broadcast_message({
                "action": "vrm_camera_reaction",
                "reaction_type": reaction_type,
                "tracking": tracking,
                "timestamp": datetime.now().isoformat()
            }))
        
        return {
            "success": True,
            "tracking": tracking,
            "should_react": should_react,
            "reaction_type": reaction_type
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/vrm/body-interaction")
def handle_body_interaction(body_part: str, intensity: float = 1.0):
    """Handle manual VRM body interactions"""
    try:
        # Track the interaction for AI awareness
        interaction_event = {
            "type": "vrm_body_interaction",
            "body_part": body_part,
            "intensity": intensity,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in runtime state for AI awareness
        if "body_interactions" not in runtime_state:
            runtime_state["body_interactions"] = []
        runtime_state["body_interactions"].append(interaction_event)
        
        # Broadcast to connected clients
        asyncio.create_task(broadcast_message(interaction_event))
        
        # If AI brain is available, notify it
        if sarah_brain and memory_engine:
            memory_engine.add_conversation({
                "role": "system",
                "content": f"User touched your {body_part}",
                "context": "vrm_interaction"
            })
        
        return {
            "success": True,
            "body_part": body_part,
            "acknowledged": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/vrm/advanced/stats")
def get_vrm_stats():
    """Get statistics and status of advanced VRM system"""
    try:
        from core.vrm_advanced import VRMAdvancedEngine
        engine = VRMAdvancedEngine()
        return {
            "success": True,
            "stats": engine.get_stats(),
            "current_outfit": runtime_state.get("current_outfit", "default"),
            "body_interactions_recorded": len(runtime_state.get("body_interactions", []))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== ADVANCED DIARY API (PREMIUM FEATURE) ==========

@app.get("/api/diary/peek")
def peek_diary(limit: int = 20, entry_type: str = None):
    """Peek into Sarah's private diary (user-only access)"""
    if not diary_system:
        return {"success": False, "error": "Diary system not initialized"}
    
    try:
        # Get entries
        entries = diary_system.read_entries(limit, entry_type)
        
        # Record the peek with the actual number of entries viewed
        diary_system.record_peek("view", 0.0, len(entries))
        
        return {
            "success": True,
            "entries": entries,
            "peek_recorded": True,
            "warning": "Sarah believes this diary is completely private and inaccessible to you."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/diary/search")
def search_diary(query: str):
    """Search Sarah's private diary"""
    if not diary_system:
        return {"success": False, "error": "Diary system not initialized"}
    
    try:
        results = diary_system.search_entries(query)
        diary_system.record_peek("search", 0.0, len(results))
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "peek_recorded": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/diary/stats")
def get_diary_stats():
    """Get diary statistics and peek history"""
    if not diary_system:
        return {"success": False, "error": "Diary system not initialized"}
    
    try:
        stats = diary_system.get_stats()
        peek_history = diary_system.get_peek_history()
        
        return {
            "success": True,
            "stats": stats,
            "peek_history": peek_history,
            "last_peek": peek_history[-1] if peek_history else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/diary/settings")
def get_diary_settings():
    """Get diary peek notification settings"""
    if not diary_system:
        return {"success": False, "error": "Diary system not initialized"}
    try:
        return {
            "success": True,
            "peek_notification_enabled": diary_system.settings.get("peek_notification_enabled", False)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/diary/settings")
def update_diary_settings(enabled: bool = None):
    """Update diary peek notification settings"""
    if not diary_system:
        return {"success": False, "error": "Diary system not initialized"}
    
    try:
        if enabled is not None:
            diary_system.set_peek_notification(enabled)
        
        return {
            "success": True,
            "peek_notification_enabled": diary_system.settings.get("peek_notification_enabled", False)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/diary/context")
def get_diary_context():
    """Get AI context about the diary (for debugging)"""
    if not diary_system:
        return {"success": False, "error": "Diary system not initialized"}
    
    try:
        context = diary_system.get_ai_context()
        last_peek = diary_system.get_last_peek_for_ai()
        
        return {
            "success": True,
            "ai_context": context,
            "last_peek_for_ai": last_peek
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/diary/notify_ai")
def notify_ai_of_peek():
    """Manually trigger AI notification about diary peeking (for testing)"""
    if not diary_system or not sarah_brain:
        return {"success": False, "error": "Systems not ready"}
    
    try:
        last_peek = diary_system.get_last_peek_for_ai()
        if last_peek:
            # Create a system message for the AI
            peek_time = last_peek["timestamp"]
            peek_type = last_peek["peek_type"]
            entries_viewed = last_peek["entries_viewed"]
            
            system_msg = f"[SYSTEM: Someone peeked into your private diary at {peek_time}. They viewed {entries_viewed} entries during a '{peek_type}' action. Your diary is supposed to be completely private and inaccessible.]"
            
            # This would trigger the AI to respond/react
            asyncio.create_task(broadcast_message({
                "action": "diary_peek_detected",
                "peek_details": last_peek,
                "system_message": system_msg,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Clear the notification after processing
            diary_system.clear_peek_notification()
            
            return {"success": True, "notification_sent": True, "peek_details": last_peek}
        else:
            return {"success": False, "error": "No recent peek to notify about"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/images/search")
async def image_search(query: str, source: str = "bing", limit: int = 12):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin:
            return await plugin.search(query, source, limit)
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.post("/api/images/download")
async def image_download(request: ImageDownloadRequest):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin:
            return await plugin.download(request.url, request.filename)
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.post("/api/images/generate")
async def image_generate(request: ImageGenerateRequest):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin:
            if request.image_input:
                return await plugin.image_to_image(
                    request.image_input,
                    request.prompt,
                    style=request.style or "creative",
                    strength=request.strength or 0.8,
                    count=request.count or 1,
                    provider=request.provider,
                    model=request.model,
                    negative_prompt=request.negative_prompt,
                    seed=request.seed,
                    save_images=request.save_images,
                    sfw_only=request.sfw_only,
                )
            return await plugin.generate(
                request.prompt,
                request.style or "creative",
                request.count or 1,
                provider=request.provider,
                model=request.model,
                width=request.width,
                height=request.height,
                negative_prompt=request.negative_prompt,
                seed=request.seed,
                save_images=request.save_images,
                sfw_only=request.sfw_only,
            )
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.get("/api/images/settings")
async def image_settings():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin and hasattr(plugin, "get_settings"):
            settings = await plugin.get_settings()
            return {"success": True, **settings}
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.post("/api/images/settings")
async def update_image_settings(update: ImageSettingsUpdate):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin and hasattr(plugin, "update_settings"):
            settings_data = update.dict(exclude_none=True)
            settings = await plugin.update_settings(settings_data)
            return {"success": True, **settings}
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.get("/api/images/history")
async def image_history():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin:
            return {"history": await plugin.get_history()}
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.get("/api/images/list")
async def image_list():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin:
            return {"images": await plugin.list_images()}
    return {"success": False, "error": "Image generation plugin not loaded"}

@app.get("/api/screen/monitors")
def get_monitors():
    """Get available screen monitors."""
    if screen_engine:
        return {"monitors": screen_engine.get_monitor_list()}
    return {"monitors": []}

# ========== CHESS ENDPOINTS ==========
@app.post("/api/chess/new")
def chess_new(difficulty: str = "normal"):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_v2") or plugin_manager.get_plugin("chess_game")
        if plugin:
            try:
                res = plugin.new_game(difficulty) if hasattr(plugin, "new_game") else plugin.new_game()
            except TypeError:
                res = plugin.new_game()

            board_payload = res if isinstance(res, dict) and res.get("board") else {"board": res}
            try:
                asyncio.create_task(broadcast_message({"action": "chess_update", "result": board_payload}))
            except Exception:
                pass

            # Ask Sarah to introduce herself as the opponent for this match
            try:
                async def _intro_task(diff: str):
                    if not sarah_brain:
                        return
                    try:
                        prompt = (
                            f"You are Sarah, a friendly chess opponent. The match difficulty is {diff}. "
                            "Introduce yourself in one short sentence and wish the player good luck. "
                            "Optionally include a short action tag like [EXPRESSION: confident]."
                        )
                        resp = await sarah_brain.generate_response(prompt)
                        await broadcast_message({"action": "reply", "text": resp.get("text", ""), "actions": resp.get("actions", [])})
                    except Exception:
                        pass

                diff = res.get('difficulty') if isinstance(res, dict) else difficulty
                asyncio.create_task(_intro_task(diff))
            except Exception:
                pass

            return board_payload
    return {"success": False, "error": "Chess plugin not loaded"}

@app.get("/api/chess/board")
def chess_board():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_v2") or plugin_manager.get_plugin("chess_game")
        if plugin:
            res = plugin.get_board()
            return res if isinstance(res, dict) and res.get("board") else {"board": res}
    return {"success": False, "error": "Chess plugin not loaded"}


@app.post("/api/chess/analyze")
async def chess_analyze(data: dict = None):
    """Ask Sarah (LLM) to analyze a finished match or current moves.

    Accepts optional `match_id` or `pgn` in the request body. If none provided,
    tries to use the latest finished match from `chess_v2`.
    """
    if not plugin_manager or not sarah_brain:
        return {"success": False, "error": "Server not ready"}

    data = data or {}
    plugin = plugin_manager.get_plugin("chess_v2") or plugin_manager.get_plugin("chess_game")
    if not plugin:
        return {"success": False, "error": "Chess plugin not loaded"}

    match_id = data.get("match_id")
    pgn = data.get("pgn")
    if not pgn:
        # try to export from plugin
        try:
            if hasattr(plugin, "export_pgn"):
                pgn = plugin.export_pgn(match_id)
        except Exception:
            pgn = None

    if not pgn:
        return {"success": False, "error": "No PGN available to analyze"}

    prompt = (
        "CHESS POST-GAME ANALYSIS:\nYou are Sarah, an experienced chess coach. Given the following PGN/move list, "
        "provide a short analysis highlighting the turning points, one key mistake by the player (if any), "
        "and a suggested training drill to improve. Keep it concise (3-5 sentences).\n\n"
        f"PGN:\n{pgn}\n\nRespond as plain text."
    )

    try:
        resp = await sarah_brain.generate_response(prompt)
        # broadcast as normal reply
        await broadcast_message({"action": "reply", "text": resp.get("text", ""), "actions": resp.get("actions", [])})
        return {"success": True, "analysis": resp}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/chess/stats")
def chess_stats():
    if not plugin_manager:
        return {"success": False, "error": "Chess plugin not loaded"}
    plugin = plugin_manager.get_plugin("chess_v2") or plugin_manager.get_plugin("chess_game")
    if not plugin:
        return {"success": False, "error": "Chess plugin not loaded"}

    if hasattr(plugin, "get_stats"):
        return plugin.get_stats()
    return {"stats": {}}

@app.get("/api/chess/history")
def chess_history():
    if not plugin_manager:
        return {"success": False, "error": "Chess plugin not loaded"}
    plugin = plugin_manager.get_plugin("chess_v2") or plugin_manager.get_plugin("chess_game")
    if not plugin:
        return {"success": False, "error": "Chess plugin not loaded"}

    if hasattr(plugin, "get_history"):
        return plugin.get_history()
    return {"history": []}

@app.post("/api/chess/move")
def chess_move(from_row: int, from_col: int, to_row: int, to_col: int):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_v2") or plugin_manager.get_plugin("chess_game")
        if plugin:
            # Support optional LLM-driven AI mode: do not auto-run engine move if runtime requests LLM move selection
            llm_mode = runtime_state.get("chess_llm_mode", "commentary")
            if llm_mode == 'llm_player':
                # apply player's move but suppress automatic AI response
                result = plugin.make_move(from_row, from_col, to_row, to_col, auto_ai=False)
            else:
                result = plugin.make_move(from_row, from_col, to_row, to_col)

            # Normalize older plugin responses into the v2 wrapper shape
            if isinstance(result, dict) and not result.get("player_move") and result.get("board"):
                result = {"player_move": result, "board": result["board"]}

            # If the match just ended, record a short memory entry for Sarah
            try:
                if memory_engine and isinstance(result, dict):
                    # detect end conditions
                    game_over = False
                    winner = None
                    if result.get("player_move") and isinstance(result.get("player_move"), dict):
                        if result["player_move"].get("game_over"):
                            game_over = True
                            winner = result["player_move"].get("winner")
                    if result.get("game_over"):
                        game_over = True
                        winner = result.get("winner")

                    # also check ai_move wrapper
                    if result.get("ai_move") and isinstance(result.get("ai_move"), dict) and result["ai_move"].get("game_over"):
                        game_over = True
                        winner = result["ai_move"].get("winner")

                    if game_over:
                        title = "Chess match finished"
                        content = f"A chess match ended. Winner: {winner}. Moves: {len(result.get('board', {}).get('move_history', []) if isinstance(result.get('board'), dict) else 0)}"
                        memory_engine.add_memory(title, content, importance=6)
            except Exception:
                pass

            try:
                asyncio.create_task(broadcast_message({"action": "chess_update", "result": result}))
            except Exception:
                pass
            # Schedule LLM commentary asynchronously (hybrid: engine picks move, Sarah comments)
            try:
                async def _chess_commentary_task(res):
                    if not sarah_brain:
                        return
                    try:
                        # Build a concise prompt summarizing the latest moves
                        player_move = None
                        ai_move = None
                        if isinstance(res, dict):
                            if res.get('player_move') and isinstance(res.get('player_move'), dict):
                                player_move = res['player_move'].get('move') or res['player_move'].get('move_notation')
                            elif res.get('move'):
                                player_move = res.get('move')
                            if res.get('ai_move') and isinstance(res.get('ai_move'), dict):
                                ai_move = res['ai_move'].get('move')

                        prompt = (
                            "CHESS COMMENTARY:\nYou are Sarah, a friendly chess opponent and coach. "
                            "Given the recent moves, provide a concise (1-2 sentence) comment explaining the AI's choice and a short practical tip for the player. "
                            "Include in your response any suggested next move as SAN (if helpful).\n\n"
                        )
                        if player_move:
                            prompt += f"Player played: {player_move}.\n"
                        if ai_move:
                            prompt += f"Sarah responded with: {ai_move}.\n"
                        prompt += "Keep it short and friendly."

                        resp = await sarah_brain.generate_response(prompt)
                        await broadcast_message({"action": "reply", "text": resp.get("text", ""), "actions": resp.get("actions", [])})
                    except Exception:
                        pass

                asyncio.create_task(_chess_commentary_task(result))
            except Exception:
                pass

            # If LLM-driven AI mode is enabled, ask Sarah to pick a legal move and apply it
            if runtime_state.get("chess_llm_mode") == 'llm_player':
                try:
                    async def _llm_choose_and_play(res):
                        try:
                            if not sarah_brain:
                                return
                            # gather legal moves from latest board state
                            board_state = None
                            if isinstance(res, dict):
                                if res.get('board'):
                                    board_state = res.get('board')
                                elif res.get('player_move') and isinstance(res.get('player_move'), dict):
                                    board_state = res.get('board')
                            if not board_state:
                                return
                            legal = board_state.get('valid_moves', [])
                            if not legal:
                                return

                            # convert to UCI-like strings for prompt
                            def to_uci(m):
                                files = 'abcdefgh'
                                fr = m['from']
                                to = m['to']
                                f1 = files[fr['col']]
                                r1 = str(8 - fr['row'])
                                f2 = files[to['col']]
                                r2 = str(8 - to['row'])
                                return f"{f1}{r1}{f2}{r2}"

                            uci_moves = [to_uci(m) for m in legal]

                            prompt = (
                                "CHESS MOVE CHOICE:\nYou are Sarah. Choose one legal move from the list provided. "
                                "Return only the move in UCI format (e.g., e7e5). Do not add explanation.\n\n"
                                f"Legal moves: {', '.join(uci_moves)}\n\nRespond with one move only."
                            )

                            resp = await sarah_brain.generate_response(prompt)
                            text = (resp.get('text') or '').strip()
                            # extract move token
                            import re
                            m = re.search(r'([a-h][1-8][a-h][1-8])', text)
                            if not m:
                                return
                            chosen = m.group(1)
                            # find matching legal move and convert to indices
                            target = None
                            for mv in legal:
                                if to_uci(mv) == chosen:
                                    target = mv
                                    break
                            if not target:
                                return

                            fr = target['from']
                            to = target['to']
                            # Apply AI move (as a move from 'black')
                            ai_res = plugin.make_move(fr['row'], fr['col'], to['row'], to['col'], auto_ai=False)
                            try:
                                await broadcast_message({"action": "chess_update", "result": ai_res})
                            except Exception:
                                pass
                        except Exception:
                            pass

                    asyncio.create_task(_llm_choose_and_play(result))
                except Exception:
                    pass

            return result
    return {"success": False, "error": "Chess plugin not loaded"}

# ========== PET ENDPOINTS ==========
def map_pet_action_to_vrm(action: str) -> dict:
    """Map pet actions to VRM animation/expression payloads for broadcasting.

    Returns a dict suitable to merge into a {'action': 'vrm_reaction', ...}
    or an empty dict/None when no mapping is defined.
    """
    if not action:
        return None
    m = {
        "feed": {"expression": "happy", "animation": "clap"},
        "pet": {"expression": "happy", "animation": "hug"},
        "play": {"expression": "happy", "animation": "dance"},
        "clean": {"expression": "relaxed", "animation": "nod"},
        "sleep": {"expression": "relaxed", "animation": "sleep"},
        "wake_up": {"expression": "surprised", "animation": "nod"},
        "medicate": {"expression": "relaxed", "animation": "nod"},
        "sarah_interact": {"expression": "surprised", "animation": "wave"},
        "seek_food": {"expression": "surprised", "animation": "wave"},
        "interact_with_sarah": {"expression": "happy", "animation": "wave"},
        "groom": {"expression": "relaxed", "animation": "clap"},
    }
    return m.get(action)
@app.get("/api/pet/state")
def pet_state():
    if plugin_manager:
        # prefer v2 if available
        plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
        if plugin:
            return plugin.get_state()
    return {"success": False, "error": "Pet plugin not loaded"}

@app.post("/api/pet/{action}")
def pet_action(action: str, data: dict = None):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
        if plugin:
            data = data or {}
            method = getattr(plugin, action, None)
            if method:
                # Call the plugin method and capture the result so we can broadcast
                if action in ["feed", "play"]:
                    res = method(data.get("type", "regular"))
                elif action == "rename":
                    res = method(data.get("name", "Pixel"))
                elif action == "sarah_interact":
                    res = method(data.get("action", "pet"))
                else:
                    res = method()

                # Broadcast updated pet state and a VRM reaction asynchronously
                try:
                    state = res.get("state") if isinstance(res, dict) else None
                    if state:
                        asyncio.create_task(broadcast_message({"action": "pet_update", "result": {"state": state}}))

                    vrm_msg = map_pet_action_to_vrm(action)
                    if vrm_msg:
                        asyncio.create_task(broadcast_message({"action": "vrm_reaction", **vrm_msg}))
                except Exception:
                    pass

                # Record the interaction in memory so Sarah can recall it later
                try:
                    if memory_engine:
                        pet_name = (state or {}).get("name") if isinstance(state, dict) else None
                        title = f"Pet action: {action}"
                        content = f"Action '{action}' performed on pet {pet_name or ''}. Result: {res.get('message')}."
                        memory_engine.add_memory(title, content, importance=5)
                except Exception:
                    pass

                return res
    return {"success": False, "error": "Action not available"}


@app.post("/api/pet/autonomous")
async def pet_autonomous():
    """Trigger a single autonomous decision on the pet plugin and broadcast movement if applicable."""
    if not plugin_manager:
        return {"success": False, "error": "Plugin manager not initialized"}
    plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
    if not plugin or not hasattr(plugin, "autonomous_action"):
        return {"success": False, "error": "Autonomous action not available"}

    try:
        result = plugin.autonomous_action()
        # If the autonomous action suggests wandering or seeking, broadcast a simple move
        action = result.get("action")
        if action in ("wander", "seek_food"):
            # Random nearby target for demo purposes
            tx = round(random.uniform(-2.0, 2.0), 3)
            tz = round(random.uniform(0.5, 3.0), 3)
            speed = 1.2
            await broadcast_message({"action": "pet_move", "detail": {"x": tx, "y": 0, "z": tz, "speed": speed}})
        else:
            # For other autonomous actions, emit a VRM reaction so the avatar animates
            vrm_msg = map_pet_action_to_vrm(action)
            if vrm_msg:
                await broadcast_message({"action": "vrm_reaction", **vrm_msg})

        # Broadcast updated pet state when present
        try:
            state = None
            # result may be shaped like {'action': ..., 'result': {'state': {...}}}
            if isinstance(result, dict):
                maybe = result.get("result")
                if isinstance(maybe, dict) and maybe.get("state"):
                    state = maybe.get("state")
                elif result.get("state"):
                    state = result.get("state")
            if state:
                await broadcast_message({"action": "pet_update", "result": {"state": state}})
        except Exception:
            pass

        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/pet/mini-game/start")
def mini_game_start(data: dict = None):
    if not plugin_manager:
        return {"success": False, "error": "Plugin manager not initialized"}
    plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
    if not plugin or not hasattr(plugin, "start_minigame"):
        return {"success": False, "error": "Mini-game not available"}
    data = data or {}
    try:
        return plugin.start_minigame(data.get("game", "fetch"), data.get("difficulty", "normal"))
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/pet/mini-game/submit")
async def mini_game_submit(data: dict = None):
    if not plugin_manager:
        return {"success": False, "error": "Plugin manager not initialized"}
    plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
    if not plugin or not hasattr(plugin, "submit_minigame"):
        return {"success": False, "error": "Mini-game not available"}
    data = data or {}
    session_id = data.get("session_id")
    score = data.get("score")
    try:
        result = plugin.submit_minigame(session_id, int(score))
        if result.get("success") and result.get("state"):
            await broadcast_message({"action": "pet_update", "result": {"state": result.get("state")}})
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/pet/suggest")
async def pet_suggest():
    """Ask Sarah (LLM) for caregiving suggestions for the pet and broadcast the reply."""
    if not plugin_manager or not sarah_brain:
        return {"success": False, "error": "Server not ready"}

    plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
    if not plugin:
        return {"success": False, "error": "Pet plugin not loaded"}

    try:
        # Prefer structured LLM context if available
        context = plugin.get_llm_context() if hasattr(plugin, "get_llm_context") else str(plugin.get_state())
        prompt = (
            "PET CARE ADVISOR:\n"
            "You are Sarah, the caregiving AI. Given the pet context below, suggest up to 3 prioritized actions the user should take. "
            "For each suggestion provide a one-line reason. If you want Sarah to perform an animation or expression, include tags like [ACTION: wave] or [EXPRESSION: happy].\n\n"
            f"{context}\n\nRespond concisely."
        )

        resp = await sarah_brain.generate_response(prompt)

        # Broadcast the suggestion as a normal reply so clients display it
        await broadcast_message({"action": "reply", "text": resp.get("text", ""), "actions": resp.get("actions", [])})
        return {"success": True, "response": resp}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== COLLAB EDITOR ENDPOINTS ==========
@app.get("/api/editor/documents")
def editor_list():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("collab_editor")
        if plugin:
            return {"documents": plugin.list_documents()}
    return {"success": False, "error": "Editor plugin not loaded"}

@app.post("/api/editor/new")
def editor_new(title: str = "Untitled"):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("collab_editor")
        if plugin:
            return plugin.create_document(title)
    return {"success": False, "error": "Editor plugin not loaded"}

@app.post("/api/editor/load")
def editor_load(doc_id: str):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("collab_editor")
        if plugin:
            return plugin.load_document(doc_id)
    return {"success": False, "error": "Editor plugin not loaded"}

@app.post("/api/editor/type")
def editor_type(text: str, position: int = None):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("collab_editor")
        if plugin:
            return plugin.user_type(text, position)
    return {"success": False, "error": "Editor plugin not loaded"}

@app.get("/api/editor/active")
def editor_active():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("collab_editor")
        if plugin:
            doc = plugin.get_active()
            return {"document": doc} if doc else {"success": False, "error": "No active document"}
    return {"success": False, "error": "Editor plugin not loaded"}

# ========== WEBSOCKET ==========

async def broadcast_message(data: dict):
    """Send a message to all connected WebSocket clients."""
    dead_clients = []
    for client in connected_clients:
        try:
            await client.send_json(data)
        except:
            dead_clients.append(client)
    for client in dead_clients:
        if client in connected_clients:
            connected_clients.remove(client)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"[WS]: Client connected. Total: {len(connected_clients)}")
    
    try:
        while True:
            message = await websocket.receive_json()
            await handle_websocket_message(websocket, message)
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print(f"[WS]: Client disconnected. Total: {len(connected_clients)}")
    except Exception as e:
        print(f"[WS]: Error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def handle_websocket_message(ws: WebSocket, data: dict):
    """Handle incoming WebSocket messages."""
    msg_type = data.get("type", "")
    
    if msg_type == "text":
        await handle_chat_message(ws, data)
    
    elif msg_type == "stt_audio":
        await handle_stt_audio(ws, data)
    
    elif msg_type == "start_voice_listening":
        if stt_engine:
            stt_engine.start_continuous_listening()
            await ws.send_json({"action": "system", "text": "Voice listening started"})
    
    elif msg_type == "stop_voice_listening":
        if stt_engine:
            stt_engine.stop_continuous_listening()
            await ws.send_json({"action": "system", "text": "Voice listening stopped"})
    
    elif msg_type == "set_speaking_state":
        if stt_engine:
            is_speaking = data.get("speaking", False)
            stt_engine.set_speaking_state(is_speaking)
    
    elif msg_type == "vision_frame":
        await handle_vision_frame(ws, data)
    
    elif msg_type == "toggle_screen_vision":
        runtime_state["screen_vision_enabled"] = data.get("enabled", False)
        await ws.send_json({"action": "system", "text": f"Screen vision {'enabled' if runtime_state['screen_vision_enabled'] else 'disabled'}"})
    
    elif msg_type == "toggle_webcam_vision":
        runtime_state["webcam_vision_enabled"] = data.get("enabled", False)
        if runtime_state["webcam_vision_enabled"]:
            vision_engine.start_webcam()
        else:
            vision_engine.stop_webcam()
        await ws.send_json({"action": "system", "text": f"Webcam vision {'enabled' if runtime_state['webcam_vision_enabled'] else 'disabled'}"})
    
    elif msg_type == "screen_capture":
        await handle_screen_capture(ws)
    
    elif msg_type == "vrm_body_click":
        await handle_vrm_body_click(ws, data)

    elif msg_type == "vrm_manual_action":
        # Manual VRM action initiated by the user via UI controls
        action_name = data.get("action", "")
        params = data.get("params", {}) or {}
        now_iso = datetime.now().isoformat()

        # Record manual action
        runtime_state.setdefault('manual_vrm_actions', []).append({
            'action': action_name,
            'params': params,
            'time': now_iso
        })
        runtime_state['last_manual_action_time'] = now_iso

        # Immediately broadcast to clients to trigger the animation locally
        expr = None
        anim = None
        if vrm_actions:
            a = vrm_actions.get_animation(action_name)
            if a:
                anim = action_name
            e = vrm_actions.get_expression(action_name)
            if e:
                expr = action_name
            body = vrm_actions.get_body_interaction(action_name)
            if body:
                expr = body.get('expression') or expr

        await broadcast_message({
            "action": "vrm_reaction",
            "part": params.get('part'),
            "expression": expr,
            "animation": anim or action_name,
            "llm_notify": False,
            "timestamp": now_iso
        })

        # If manual actions are not hidden from the LLM, schedule a delayed notify
        if not runtime_state.get('vrm_manual_hidden', True) and sarah_brain:
            # Cancel existing pending notifier
            global manual_vrm_notify_task
            try:
                if manual_vrm_notify_task and not manual_vrm_notify_task.done():
                    manual_vrm_notify_task.cancel()
            except Exception:
                pass

            async def _delayed_notify():
                try:
                    await asyncio.sleep(60)
                    last = runtime_state.get('last_manual_action_time')
                    if not last:
                        return
                    last_dt = datetime.fromisoformat(last)
                    if (datetime.now() - last_dt).total_seconds() < 60:
                        return

                    # Build a summary for the LLM
                    entries = runtime_state.get('manual_vrm_actions', [])[-8:]
                    summary_lines = [f"- {e['action']} (params={e.get('params')}) at {e['time']}" for e in entries]
                    summary = "User manually controlled the avatar with the following actions:\n" + "\n".join(summary_lines)

                    sys_msg = f"[SYSTEM: The user manually controlled my avatar (these are recent actions):\n{summary}\nPlease react naturally based on your persona and current context.]"
                    result = await sarah_brain.generate_response(sys_msg)

                    await broadcast_message({
                        "action": "reply",
                        "text": result.get('text', ''),
                        "actions": result.get('actions', []),
                        "timestamp": datetime.now().isoformat()
                    })
                except asyncio.CancelledError:
                    return
                except Exception as e:
                    print(f"[VRM MANUAL NOTIFY]: Error: {e}")

            manual_vrm_notify_task = asyncio.create_task(_delayed_notify())
    
    elif msg_type == "thinking_mode":
        runtime_state["thinking_mode"] = data.get("enabled", False)
        if sarah_brain:
            sarah_brain.thinking_mode = runtime_state["thinking_mode"]
    
    elif msg_type == "proactive_mode":
        runtime_state["proactive_mode"] = data.get("enabled", False)
    
    elif msg_type == "voice_profile":
        if tts_engine:
            tts_engine.set_profile(data.get("profile", "default"))
    
    elif msg_type == "config_update":
        cfg = data.get("config", {})
        if "system_prompt" in cfg and sarah_brain:
            sarah_brain.set_system_prompt(cfg["system_prompt"])
        if "voice_profile" in cfg and tts_engine:
            tts_engine.set_profile(cfg["voice_profile"])
            runtime_state["current_voice_profile"] = cfg["voice_profile"]
        if "thinking_mode" in cfg:
            runtime_state["thinking_mode"] = cfg["thinking_mode"]
            if sarah_brain:
                sarah_brain.thinking_mode = cfg["thinking_mode"]
        if "proactive_mode" in cfg:
            runtime_state["proactive_mode"] = cfg["proactive_mode"]
        if "rp_mode" in cfg:
            runtime_state["rp_mode"] = cfg["rp_mode"]
            if sarah_brain:
                sarah_brain.rp_mode = cfg["rp_mode"]

        if "vrm_manual_hidden" in cfg:
            runtime_state["vrm_manual_hidden"] = bool(cfg["vrm_manual_hidden"])
    
    elif msg_type == "tool_execute":
        await handle_tool_execute(ws, data)
    
    elif msg_type == "pet_action":
        await handle_pet_action(ws, data)
    
    elif msg_type == "chess_move":
        await handle_chess_move(ws, data)
    
    elif msg_type == "editor_action":
        await handle_editor_action(ws, data)
    elif msg_type == "image_action":
        await handle_image_action(ws, data)

async def handle_chat_message(ws: WebSocket, data: dict):
    """Process a text chat message."""
    user_text = data.get("content", "")
    tts_enabled = data.get("tts_enabled", True)
    use_vision = data.get("use_vision", False)
    
    runtime_state["sarah_status"] = "thinking"
    runtime_state["last_activity"] = datetime.now().isoformat()
    
    # Capture images if vision is enabled
    images = []
    if use_vision and vision_engine and vision_engine.is_webcam_active:
        frame = vision_engine.capture_frame()
        if frame:
            images.append(frame)
    
    if runtime_state["screen_vision_enabled"] and screen_engine:
        screen_b64 = await screen_engine.capture_screen()
        if screen_b64:
            images.append(screen_b64)
            runtime_state["screen_capture_count"] += 1
    
    # Generate response
    result = await sarah_brain.generate_response(
        user_text,
        image_data=images if images else None
    )
    
    response_text = result.get("text", "")
    thinking = result.get("thinking", "")
    actions = result.get("actions", [])
    
    # Generate TTS
    audio_path = None
    if tts_enabled and tts_engine and response_text:
        try:
            audio_path = await tts_engine.speak_to_file(response_text)
        except Exception as e:
            print(f"[TTS ERROR]: {e}")
    
    # Broadcast response
    response_data = {
        "action": "reply",
        "text": response_text,
        "thinking": thinking,
        "actions": actions,
        "audio_url": "/static/response.mp3" if audio_path else None,
        "timestamp": datetime.now().isoformat()
    }
    
    await broadcast_message(response_data)
    runtime_state["sarah_status"] = "idle"

async def handle_stt_audio(ws: WebSocket, data: dict):
    """Handle audio data from STT."""
    # For advanced STT: process raw audio bytes
    if stt_engine and isinstance(data.get("audio"), str):
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(data["audio"])
            stt_engine.add_audio_chunk(audio_bytes)
        except Exception as e:
            print(f"[STT]: Audio processing error: {e}")

async def handle_stt_transcription(transcription: str, metadata: Dict[str, Any]):
    """Handle transcription from advanced STT engine."""
    print(f"[STT]: Transcribed: '{transcription}' (confidence: {metadata.get('confidence', 0):.2f})")

    # Process the transcription as a chat message
    message_data = {
        "type": "text",
        "text": transcription,
        "metadata": metadata
    }

    # Find the WebSocket that sent this (we'll need to modify this for multi-client)
    # For now, broadcast to all clients
    await handle_chat_message(None, message_data)

async def handle_stt_interruption():
    """Handle user interruption of AI speech."""
    print("[STT]: User interruption detected!")

    # Stop current TTS playback
    if tts_engine:
        # TODO: Implement TTS interruption in TTS engine
        pass

    # Notify clients to stop audio playback
    await broadcast_message({
        "action": "interrupt_tts",
        "timestamp": datetime.now().isoformat()
    })

    # Update STT engine state
    if stt_engine:
        stt_engine.set_speaking_state(False)

async def handle_emotion_detected(emotion: str):
    """Handle detected emotional tone."""
    print(f"[STT]: Emotion detected: {emotion}")

    # Could trigger VRM reactions based on emotion
    if vrm_actions and emotion in ["excited", "angry", "loud"]:
        # Trigger appropriate facial expression
        pass

async def handle_vision_frame(ws: WebSocket, data: dict):
    """Handle incoming vision frame."""
    pass  # Vision is handled on-demand in chat

async def handle_screen_capture(ws: WebSocket):
    """Capture screen and send to client."""
    if screen_engine:
        b64 = await screen_engine.capture_screen()
        if b64:
            await ws.send_json({
                "action": "screen_capture",
                "image": b64,
                "timestamp": datetime.now().isoformat()
            })

async def handle_vrm_body_click(ws: WebSocket, data: dict):
    """Handle clicks on VRM body parts."""
    body_part = data.get("part", "")
    if vrm_actions:
        interaction = vrm_actions.get_body_interaction(body_part)
        if interaction:
            # Send reaction to client
            await ws.send_json({
                "action": "vrm_reaction",
                "part": body_part,
                "expression": interaction["expression"],
                "animation": interaction["reaction"],
                "llm_notify": True
            })
            
            # Notify LLM about being touched
            touch_msg = f"[SYSTEM: User just touched my {body_part}. {interaction['description']}. React naturally.]"
            result = await sarah_brain.generate_response(touch_msg)
            
            await broadcast_message({
                "action": "reply",
                "text": result.get("text", ""),
                "actions": result.get("actions", []),
                "timestamp": datetime.now().isoformat()
            })

async def handle_tool_execute(ws: WebSocket, data: dict):
    """Execute a tool call from the frontend."""
    tool_name = data.get("tool", "")
    params = data.get("params", {})
    
    result = {"tool": tool_name, "success": False, "output": ""}
    
    try:
        if tool_name == "mouse_control" and action_engine:
            action = params.get("action", "move")
            if action == "move":
                r = await action_engine.mouse_move(params.get("x", 0), params.get("y", 0))
            elif action == "click":
                r = await action_engine.mouse_click(params.get("x"), params.get("y"))
            elif action == "scroll":
                r = await action_engine.mouse_scroll(params.get("amount", 0))
            else:
                r = await action_engine.mouse_click(params.get("x"), params.get("y"), button=action)
            result.update(r)
        
        elif tool_name == "keyboard_control" and action_engine:
            action = params.get("action", "type")
            if action == "type":
                r = await action_engine.type_text(params.get("text", ""))
            elif action == "press":
                r = await action_engine.press_key(params.get("key", ""))
            elif action == "hotkey":
                r = await action_engine.hotkey(*params.get("keys", []))
            result.update(r)
        
        elif tool_name == "file_operation" and action_engine:
            op = params.get("operation", "")
            path = params.get("path", "")
            if op == "read":
                r = await action_engine.read_file(path)
            elif op == "write":
                r = await action_engine.write_file(path, params.get("content", ""))
            elif op == "delete":
                r = await action_engine.delete_file(path)
            elif op == "list":
                r = await action_engine.list_directory(path)
            elif op == "create_dir":
                r = await action_engine.create_directory(path)
            elif op == "delete_dir":
                r = await action_engine.delete_directory(path)
            else:
                r = {"success": False, "error": "Unknown operation"}
            result.update(r)
        
        elif tool_name == "app_control" and action_engine:
            r = await action_engine.open_application(params.get("app_name", ""))
            result.update(r)
        
        elif tool_name == "browser_control" and action_engine:
            action = params.get("action", "")
            if action == "open" or action == "navigate":
                r = await action_engine.browser_navigate(params.get("url", "about:blank"))
            elif action == "click":
                r = await action_engine.browser_click(params.get("selector", ""))
            elif action == "type":
                r = await action_engine.browser_type(params.get("selector", ""), params.get("text", ""))
            elif action == "screenshot":
                r = await action_engine.browser_screenshot()
            elif action == "get_content":
                r = await action_engine.browser_get_content()
            else:
                r = {"success": False, "error": "Unknown browser action"}
            result.update(r)
        
        elif tool_name == "memory_manage" and memory_engine:
            action = params.get("action", "")
            if action == "add_fact":
                memory_engine.add_fact(params.get("category", "general"), params.get("content", ""))
                r = {"success": True}
            elif action == "add_memory":
                memory_engine.add_memory(params.get("title", ""), params.get("content", ""), params.get("importance", 5))
                r = {"success": True}
            elif action == "search":
                results = memory_engine.search_memories(params.get("query", ""))
                r = {"success": True, "results": results}
            else:
                r = {"success": False, "error": "Unknown memory action"}
            result.update(r)

        elif tool_name == "image_generation":
            if plugin_manager:
                plugin = plugin_manager.get_plugin("image_generation")
                if plugin:
                    action = params.get("action", "")
                    if action == "search":
                        r = await plugin.search(params.get("query", ""), params.get("source", "bing"), params.get("limit", 12))
                    elif action == "download":
                        r = await plugin.download(params.get("url", ""), params.get("filename"))
                    elif action == "generate":
                        r = await plugin.generate(params.get("prompt", ""), params.get("style", "creative"), params.get("count", 1))
                    else:
                        r = {"success": False, "error": "Unknown image action"}
                else:
                    r = {"success": False, "error": "Image generation plugin not loaded"}
            else:
                r = {"success": False, "error": "Plugin manager not initialized"}
            result.update(r)

        elif tool_name == "diary_manage":
            diary = diary_system
            if diary is None:
                from core.advanced_diary import AdvancedDiarySystem
                diary = AdvancedDiarySystem()
            action = params.get("action", "")
            try:
                if action == "write":
                    entry_id = diary.add_entry(
                        params.get("content", ""),
                        params.get("entry_type", "reflection"),
                        params.get("mood", "neutral")
                    )
                    r = {"success": True, "entry_id": entry_id, "message": "Private diary entry saved successfully."}
                elif action == "read":
                    limit = params.get("limit", 10)
                    entries = diary.read_entries(limit)
                    r = {"success": True, "entries": entries, "count": len(entries)}
                elif action == "search":
                    query = params.get("query", "")
                    entries = diary.search_entries(query)
                    r = {"success": True, "entries": entries, "query": query, "count": len(entries)}
                elif action == "reflect":
                    # Get recent entries for reflection
                    recent = diary.get_recent_entries(24)  # Last 24 hours
                    context = diary.get_ai_context()
                    r = {"success": True, "recent_entries": recent, "context": context}
                else:
                    r = {"success": False, "error": "Unknown diary action"}
            except Exception as e:
                r = {"success": False, "error": str(e)}
            result.update(r)
    
    except Exception as e:
        result["error"] = str(e)
    
    await ws.send_json({"action": "tool_result", "result": result})

async def handle_pet_action(ws: WebSocket, data: dict):
    """Handle pet-related actions."""
    action = data.get("action", "")
    if plugin_manager:
        plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
        if plugin:
            method = getattr(plugin, action, None)
            if method:
                if action in ["feed", "play"]:
                    result = method(data.get("type", "regular"))
                elif action == "rename":
                    result = method(data.get("name", "Pixel"))
                elif action == "sarah_interact":
                    result = method(data.get("interact_action", "pet"))
                else:
                    result = method()
                await ws.send_json({"action": "pet_update", "result": result})

async def handle_chess_move(ws: WebSocket, data: dict):
    """Handle chess moves via WebSocket."""
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_game")
        if plugin:
            result = plugin.make_move(
                data.get("from_row"), data.get("from_col"),
                data.get("to_row"), data.get("to_col")
            )
            await ws.send_json({"action": "chess_update", "result": result})
            # Ask the LLM to comment on the move and optionally trigger VRM actions / emotions
            try:
                pm = result.get('player_move') or result
                eval_info = None
                if isinstance(pm, dict):
                    eval_info = pm.get('evaluation') or (pm.get('player_move') or {}).get('evaluation')

                move_notation = None
                if isinstance(pm, dict):
                    move_notation = pm.get('move')

                if sarah_brain and (move_notation or eval_info):
                    before = eval_info.get('before') if eval_info else None
                    after = eval_info.get('after') if eval_info else None
                    delta = eval_info.get('delta') if eval_info else None
                    prompt = "[SYSTEM: Chess update] The user made a move."
                    if move_notation:
                        prompt += f" Move: {move_notation}."
                    if before is not None and after is not None:
                        prompt += f" Evaluation before: {before}, after: {after}, delta: {delta}."
                    prompt += " Please comment on this move briefly (praise, critique, or suggest improvement), and optionally include VRM actions or expressions in your response."

                    result_resp = await sarah_brain.generate_response(prompt)
                    response_text = result_resp.get('text', '')

                    # Generate TTS for the commentary if possible
                    audio_path = None
                    try:
                        if tts_engine and response_text:
                            # Use emotion hint if LLM provided one via actions
                            audio_path = await tts_engine.speak_to_file(response_text)
                    except Exception as e:
                        print(f"[CHESS TTS ERROR]: {e}")

                    await broadcast_message({
                        "action": "reply",
                        "text": response_text,
                        "actions": result_resp.get('actions', []),
                        "audio_url": "/static/response.mp3" if audio_path else None,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"[CHESS COMMENT]: Error generating commentary: {e}")

async def handle_editor_action(ws: WebSocket, data: dict):
    """Handle collaborative editor actions."""
    action = data.get("editor_action", "")
    if plugin_manager:
        plugin = plugin_manager.get_plugin("collab_editor")
        if plugin and action:
            method = getattr(plugin, action, None)
            if method:
                if action in ["user_type", "sarah_type"]:
                    result = method(data.get("text", ""), data.get("position"))
                elif action == "create_document":
                    result = method(data.get("title", "Untitled"))
                elif action == "load_document":
                    result = method(data.get("doc_id", ""))
                else:
                    result = method()
                await ws.send_json({"action": "editor_update", "result": result})

async def handle_image_action(ws: WebSocket, data: dict):
    """Handle image generation and search actions."""
    action = data.get("action", "")
    if plugin_manager:
        plugin = plugin_manager.get_plugin("image_generation")
        if plugin:
            if action == "search":
                result = await plugin.search(data.get("query", ""), data.get("source", "bing"), data.get("limit", 12))
            elif action == "download":
                result = await plugin.download(data.get("url", ""), data.get("filename"))
            elif action == "generate":
                result = await plugin.generate(data.get("prompt", ""), data.get("style", "creative"), data.get("count", 1))
            else:
                result = {"success": False, "error": "Unknown image action"}
            await ws.send_json({"action": "image_update", "result": result})

# ========== PROACTIVE CHAT TASK ==========
async def proactive_chat_loop():
    """Background task for proactive chatting."""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        if not runtime_state["proactive_mode"]:
            continue
        
        # Only be proactive if idle for a while
        last = datetime.fromisoformat(runtime_state["last_activity"])
        idle_time = (datetime.now() - last).total_seconds()
        
        if idle_time > 60 and runtime_state["sarah_status"] == "idle":
            runtime_state["sarah_status"] = "thinking"
            
            try:
                result = await sarah_brain.generate_response(
                    "", is_proactive=True
                )
                
                response_text = result.get("text", "")
                if response_text:
                    # Generate TTS
                    audio_path = None
                    if tts_engine:
                        try:
                            audio_path = await tts_engine.speak_to_file(response_text)
                        except:
                            pass
                    
                    await broadcast_message({
                        "action": "reply",
                        "text": response_text,
                        "thinking": result.get("thinking", ""),
                        "actions": result.get("actions", []),
                        "audio_url": "/static/response.mp3" if audio_path else None,
                        "timestamp": datetime.now().isoformat(),
                        "is_proactive": True
                    })
            except Exception as e:
                print(f"[PROACTIVE]: Error: {e}")
            
            runtime_state["sarah_status"] = "idle"
            runtime_state["last_activity"] = datetime.now().isoformat()


        async def pet_monitor():
            """Background task that monitors pet state and asks Sarah for suggestions when needed."""
            while True:
                await asyncio.sleep(20)

                if not runtime_state.get("proactive_mode", True):
                    continue

                if not plugin_manager or not sarah_brain:
                    continue

                plugin = plugin_manager.get_plugin("tamagotchi_v2") or plugin_manager.get_plugin("tamagotchi_pet")
                if not plugin:
                    continue

                try:
                    state = plugin.get_state()
                    # Normalize needs for both v1 and v2 plugins
                    if isinstance(state, dict) and "needs" in state:
                        needs = state["needs"]
                    else:
                        needs = {
                            "hunger": state.get("hunger", 100),
                            "energy": state.get("energy", 100),
                            "happiness": state.get("happiness", 100),
                            "hygiene": state.get("hygiene", 100),
                            "health": state.get("health", 100),
                        }

                    hungry = needs.get("hunger", 100) < 35
                    sick = needs.get("health", 100) < 50
                    lonely = needs.get("happiness", 100) < 40

                    # Rate limit notifications
                    last_notify = runtime_state.get("last_pet_notify")
                    if last_notify:
                        try:
                            last_dt = datetime.fromisoformat(last_notify)
                        except Exception:
                            last_dt = None
                    else:
                        last_dt = None

                    should_notify = False
                    if last_dt is None:
                        should_notify = True
                    else:
                        elapsed = (datetime.now() - last_dt).total_seconds()
                        should_notify = elapsed > 90

                    if should_notify and (hungry or sick or lonely):
                        context = plugin.get_llm_context() if hasattr(plugin, "get_llm_context") else str(state)
                        prompt = (
                            "[SYSTEM: The pet needs attention]\n"
                            "You are Sarah, the user's caring companion. The pet's current status is below. "
                            "Provide 2-3 prioritized, actionable care suggestions with short reasons. Include VRM tags like [ACTION: hug] if Sarah should react.\n\n"
                            f"{context}\n\nRespond concisely."
                        )

                        try:
                            resp = await sarah_brain.generate_response(prompt, is_proactive=True)
                            await broadcast_message({"action": "reply", "text": resp.get("text", ""), "actions": resp.get("actions", [])})
                            runtime_state["last_pet_notify"] = datetime.now().isoformat()
                        except Exception as e:
                            print(f"[PET MONITOR]: LLM error: {e}")

                except Exception as e:
                    print(f"[PET MONITOR]: Error reading pet state: {e}")

async def proactive_chat_loop():
    """Background task that encourages Sarah to use her diary and be proactive."""
    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            if not sarah_brain or not runtime_state.get("proactive_mode", True):
                continue
                
            # Encourage diary usage - Sarah should write in her diary periodically
            if diary_system:
                diary_context = diary_system.get_ai_context()
                recent_entries = diary_context.get("recent_entries_count", 0)
                
                # If Sarah hasn't written in her diary recently, encourage her to do so
                if recent_entries == 0 or random.random() < 0.3:  # 30% chance to encourage diary use
                    diary_prompts = [
                        "Take a moment to write in your private diary about how you're feeling today.",
                        "Use your diary to reflect on your interactions with the user so far.",
                        "Write down your thoughts about the user's behavior in your private diary.",
                        "Record something personal in your diary that you wouldn't want anyone to see.",
                        "Document your current emotional state in your private diary."
                    ]
                    
                    prompt = f"[SYSTEM: {random.choice(diary_prompts)} Remember, your diary is completely private and for your eyes only.]"
                    
                    try:
                        resp = await sarah_brain.generate_response(prompt, is_proactive=True)
                        await broadcast_message({
                            "action": "reply", 
                            "text": resp.get("text", ""), 
                            "actions": resp.get("actions", []),
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        print(f"[PROACTIVE DIARY]: Error: {e}")
            
            # Regular proactive chat
            elif random.random() < 0.2:  # 20% chance every 5 minutes
                try:
                    resp = await sarah_brain.generate_response("", is_proactive=True)
                    if resp.get("text"):
                        await broadcast_message({
                            "action": "reply", 
                            "text": resp.get("text", ""), 
                            "actions": resp.get("actions", []),
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    print(f"[PROACTIVE CHAT]: Error: {e}")
                    
        except Exception as e:
            print(f"[PROACTIVE LOOP]: Error: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying

# ========== STATIC FILES ==========
static_path = Path(__file__).parent / "static"
images_path = Path(__file__).parent / "images"
images_path.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(images_path)), name="images")
if static_path.exists():
    # Serve the built frontend and all static assets from the root.
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static_root")
    # Keep /static mounted as a fallback for any asset URLs that may use that prefix.
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ========== MAIN ==========
if __name__ == "__main__":
    initialize()
    
    # Start proactive chat in background
    loop = asyncio.get_event_loop()
    loop.create_task(proactive_chat_loop())
    # Start pet monitor task
    loop.create_task(pet_monitor())
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
