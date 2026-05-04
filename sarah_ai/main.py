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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Add core and plugins to path
sys.path.insert(0, str(Path(__file__).parent))

from core.llm_brain import LLMBrain
from core.tts_engine import TTSEngine
from core.stt_engine import STTEngine
from core.vision_engine import VisionEngine
from core.screen_engine import ScreenEngine
from core.memory_engine import MemoryEngine
from core.permission_manager import PermissionManager
from core.action_engine import ActionEngine
from core.vrm_action_engine import VRMActionEngine
from plugins.plugin_manager import PluginManager

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
    return FileResponse("static/index.html")

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

# WebSocket connections
connected_clients: list = []

# Runtime state
runtime_state = {
    "screen_vision_enabled": False,
    "webcam_vision_enabled": False,
    "thinking_mode": False,
    "proactive_mode": True,
    "current_voice_profile": "default",
    "sarah_status": "idle",
    "last_activity": datetime.now().isoformat(),
    "screen_capture_count": 0
}

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
        vrm_actions=vrm_actions
    )
    print("[INIT]: Sarah's brain online.")
    
    # TTS Engine
    tts_engine = TTSEngine()
    print("[INIT]: TTS engine ready.")
    
    # STT Engine
    try:
        stt_engine = STTEngine()
        print("[INIT]: STT engine ready.")
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
    # Auto-load plugins
    plugin_manager.load_plugin("chess_game")
    plugin_manager.load_plugin("tamagotchi_pet")
    plugin_manager.load_plugin("collab_editor")
    print(f"[INIT]: Plugins loaded - {plugin_manager.list_plugins()}")
    
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

class ConfigUpdate(BaseModel):
    system_prompt: Optional[str] = None
    voice_profile: Optional[str] = None
    thinking_mode: Optional[bool] = None
    proactive_mode: Optional[bool] = None

# ========== HTTP ENDPOINTS ==========

@app.get("/api/status")
def get_status():
    """Get current system status."""
    return {
        "status": "online",
        "sarah_status": runtime_state["sarah_status"],
        "thinking_mode": runtime_state["thinking_mode"],
        "proactive_mode": runtime_state["proactive_mode"],
        "permissions": permission_manager.get_all() if permission_manager else {},
        "action_status": action_engine.get_status() if action_engine else {},
        "memory_stats": memory_engine.get_stats() if memory_engine else {},
        "voice_profiles": tts_engine.profiles if tts_engine else {},
        "plugins": plugin_manager.list_plugins() if plugin_manager else []
    }

@app.get("/api/permissions")
def get_permissions():
    """Get all permission settings."""
    return permission_manager.get_all() if permission_manager else {}

@app.post("/api/permissions")
def update_permission(update: PermissionUpdate):
    """Update a permission."""
    if permission_manager:
        permission_manager.set_permission(update.key, update.enabled)
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
    
    return {"success": True, "config": runtime_state}

@app.get("/api/vrm/actions")
def get_vrm_actions():
    """Get all VRM actions for reference."""
    if vrm_actions:
        return vrm_actions.get_all_actions()
    return {}

@app.get("/api/screen/monitors")
def get_monitors():
    """Get available screen monitors."""
    if screen_engine:
        return {"monitors": screen_engine.get_monitor_list()}
    return {"monitors": []}

# ========== CHESS ENDPOINTS ==========
@app.post("/api/chess/new")
def chess_new():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_game")
        if plugin:
            return plugin.new_game()
    return {"success": False, "error": "Chess plugin not loaded"}

@app.get("/api/chess/board")
def chess_board():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_game")
        if plugin:
            return plugin.get_board()
    return {"success": False, "error": "Chess plugin not loaded"}

@app.post("/api/chess/move")
def chess_move(from_row: int, from_col: int, to_row: int, to_col: int):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("chess_game")
        if plugin:
            return plugin.make_move(from_row, from_col, to_row, to_col)
    return {"success": False, "error": "Chess plugin not loaded"}

# ========== PET ENDPOINTS ==========
@app.get("/api/pet/state")
def pet_state():
    if plugin_manager:
        plugin = plugin_manager.get_plugin("tamagotchi_pet")
        if plugin:
            return plugin.get_state()
    return {"success": False, "error": "Pet plugin not loaded"}

@app.post("/api/pet/{action}")
def pet_action(action: str, data: dict = None):
    if plugin_manager:
        plugin = plugin_manager.get_plugin("tamagotchi_pet")
        if plugin:
            data = data or {}
            method = getattr(plugin, action, None)
            if method:
                if action in ["feed", "play"]:
                    return method(data.get("type", "regular"))
                elif action == "rename":
                    return method(data.get("name", "Pixel"))
                elif action == "sarah_interact":
                    return method(data.get("action", "pet"))
                return method()
    return {"success": False, "error": "Action not available"}

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
    
    elif msg_type == "thinking_mode":
        runtime_state["thinking_mode"] = data.get("enabled", False)
        if sarah_brain:
            sarah_brain.thinking_mode = runtime_state["thinking_mode"]
    
    elif msg_type == "proactive_mode":
        runtime_state["proactive_mode"] = data.get("enabled", False)
    
    elif msg_type == "voice_profile":
        if tts_engine:
            tts_engine.set_profile(data.get("profile", "default"))
    
    elif msg_type == "tool_execute":
        await handle_tool_execute(ws, data)
    
    elif msg_type == "pet_action":
        await handle_pet_action(ws, data)
    
    elif msg_type == "chess_move":
        await handle_chess_move(ws, data)
    
    elif msg_type == "editor_action":
        await handle_editor_action(ws, data)

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
    # Note: The browser STT sends transcribed text directly.
    # If using Python STT, we'd process audio bytes here.
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
    
    except Exception as e:
        result["error"] = str(e)
    
    await ws.send_json({"action": "tool_result", "result": result})

async def handle_pet_action(ws: WebSocket, data: dict):
    """Handle pet-related actions."""
    action = data.get("action", "")
    if plugin_manager:
        plugin = plugin_manager.get_plugin("tamagotchi_pet")
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

# ========== STATIC FILES ==========
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ========== MAIN ==========
if __name__ == "__main__":
    initialize()
    
    # Start proactive chat in background
    loop = asyncio.get_event_loop()
    loop.create_task(proactive_chat_loop())
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
