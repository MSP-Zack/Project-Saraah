# Sarah AI Architecture Guide

## Purpose

This document is the source-of-truth orientation guide for an AI or engineer extending Project-Saraah. It describes how the application is actually connected today, which modules own runtime behavior, which systems are legacy or disconnected, how data flows through the app, and what rules must be followed when adding features.

Sarah is a local FastAPI backend plus a React/Vite frontend. The product goal is a persistent, multimodal AI companion with a 3D avatar, voice, vision, memory, games, tools, autonomy, and a coherent evolving self-model.

This is an architecture document, not an end-user manual.

## Repository Layout

```text
Project-Saraah/
├── app/                              React/Vite frontend
│   ├── package.json                  Frontend scripts and dependencies
│   ├── vite.config.ts                Vite, React, alias, dev server
│   └── src/
│       ├── main.tsx                  React entry point
│       ├── App.tsx                   Main shell, tab registry, VRM background
│       ├── App.css, index.css        Global styling
│       ├── components/               Feature panels and visual systems
│       │   ├── ChatPanel.tsx         Text chat, browser microphone/STT
│       │   ├── SettingsPanel.tsx     Runtime settings and feature toggles
│       │   ├── MemoryPanel.tsx       Classic memory API view
│       │   ├── SelfModelPanel.tsx    Versioned Sarah self-model editor
│       │   ├── GoalsPanel.tsx        Hierarchical goal and progress UI
│       │   ├── HeartbeatPanel.tsx    Guarded autonomy controls/history
│       │   ├── PerceptionPanel.tsx   Live webcam context and history
│       │   ├── DiaryPanel.tsx        Private diary inspection/settings
│       │   ├── VRMViewer.tsx         Three.js scene and avatar owner
│       │   ├── VRMPanel.tsx          Hardcoded manual avatar controls
│       │   ├── VRMActionsPanel.tsx   Backend-listed manual actions
│       │   ├── OutfitPanel.tsx       VRM outfit switching
│       │   ├── FBXTestPanel.tsx      Temporary FBX animation tester
│       │   ├── ChessPanel.tsx        Chess UI
│       │   ├── StrategoPanel.tsx     Stratego UI
│       │   ├── PetPanel.tsx          Tamagotchi UI
│       │   ├── EditorPanel.tsx       Collaborative editor UI
│       │   ├── ImagePanel.tsx        Image search/generation UI
│       │   ├── EbooksPanel.tsx       Ebook upload/reading UI
│       │   ├── NotesPanel.tsx        Sticky notes UI
│       │   ├── ToolsPanel.tsx        Plugin/status display
│       │   ├── PermissionPanel.tsx   Capability permissions
│       │   ├── StatusBar.tsx         Connection/status indicators
│       │   ├── ThinkingDisplay.tsx   Optional thinking display
│       │   └── ui/                   Shared Radix/shadcn-style primitives
│       ├── hooks/
│       │   ├── useWebSocket.ts       WebSocket connection and message router
│       │   ├── useStore.ts            Zustand application state
│       │   └── use-mobile.ts          Responsive helper
│       ├── types/index.ts             Shared frontend state/domain types
│       ├── lib/utils.ts               Frontend utilities
│       └── pages/Home.tsx             Page component, lightly used by shell
├── sarah_ai/
│   ├── main.py                        FastAPI application and runtime orchestrator
│   ├── requirements.txt               Backend dependencies
│   ├── core/
│   │   ├── llm_brain.py               LLM client, prompt assembly, tool execution
│   │   ├── memory_engine.py           LIVE memory store and retrieval path
│   │   ├── embedding_provider.py      Optional OpenAI-compatible embeddings
│   │   ├── self_model.py              Versioned persistent identity state
│   │   ├── goal_engine.py              Persistent hierarchical goals
│   │   ├── heartbeat_engine.py         Guarded heartbeat policy/history
│   │   ├── advanced_diary.py            Private diary/reflection storage
│   │   ├── permission_manager.py       Capability gates for AI tools
│   │   ├── action_engine.py             Computer/file/browser actions
│   │   ├── tts_engine.py                Text-to-speech orchestration
│   │   ├── stt_engine.py                Older STT implementation
│   │   ├── stt_engine_advanced.py       LIVE advanced STT implementation
│   │   ├── vision_engine.py              OpenCV webcam capture
│   │   ├── screen_engine.py              Desktop screenshot capture
│   │   ├── image_generation/             Image engine, providers, analysis
│   │   ├── memory_system/                LEGACY/DISCONNECTED advanced memory prototype
│   │   ├── vrm_action_engine.py           LIVE simple VRM action registry
│   │   ├── vrm_advanced.py                LEGACY/PARTIAL advanced VRM library
│   │   └── tts_providers/                 TTS adapters
│   ├── plugins/
│   │   ├── plugin_manager.py              Root-file plugin loader
│   │   ├── chess_v2.py                    LIVE chess plugin selected at startup
│   │   ├── chess_game.py                  Chess fallback/core implementation
│   │   ├── stratego.py                     LIVE Stratego plugin
│   │   ├── stratego_v2/                    Separate package, not current loader target
│   │   ├── tamagotchi_v2.py                LIVE pet plugin selected at startup
│   │   ├── tamagotchi_v2/                  Pet implementation package
│   │   ├── tamagotchi_pet.py               Pet fallback
│   │   ├── collab_editor.py                LIVE collaborative editor plugin
│   │   ├── image_generation.py             LIVE image plugin
│   │   └── ebook_reader.py                 LIVE premium ebook adapter
│   ├── data/                              Runtime JSON: diary, notes, self, goals, heartbeat
│   ├── memory/                            Classic memory, game saves, documents
│   ├── images/                            Image engine storage
│   └── static/                            Served frontend/assets/models/FBX tests
├── memory/                                Workspace-level pet/tamagotchi data
├── test_memory/                           Large experimental memory fixture tree
├── test_memory_system.py                  Test/demo for disconnected advanced memory
├── plugins/                               Workspace-level plugin area, separate from live sarah_ai/plugins
└── SARAH_ARCHITECTURE_GUIDE.md            This document
```

Generated `__pycache__` files and built frontend assets are artifacts, not architecture. They should not be treated as source changes.

## Runtime Startup

The live server is `sarah_ai/main.py`.

When executed directly:

1. `initialize()` creates the permission manager.
2. `MemoryEngine` loads classic JSON memory from the current working directory's `memory/` directory.
3. `SelfModel`, `GoalEngine`, and `HeartbeatEngine` load durable state from `sarah_ai/data/` when the server is started from the project root.
4. `VRMActionEngine`, diary, vision analyzer, LLM brain, TTS, STT, webcam, screen, action, plugin, and ebook systems are initialized.
5. The plugin manager loads root-level files from `sarah_ai/plugins/`:
   - `chess_v2` with `chess_game` fallback
   - `stratego`
   - `tamagotchi_v2` with `tamagotchi_pet` fallback
   - `collab_editor`
   - `image_generation`
6. Background tasks start:
   - existing proactive chat/diary loop
   - nightly exact-duplicate librarian
   - guarded heartbeat loop
   - pet monitor
7. Uvicorn serves FastAPI and static files.

Important: `initialize()` is only called in the `if __name__ == "__main__"` path. Importing `sarah_ai.main` creates routes and globals but does not initialize subsystems.

## Frontend Startup

`app/src/main.tsx` mounts `App`.

`App.tsx`:

- starts `useWebSocket()`;
- renders `VRMViewer` as the full-screen Three.js background;
- renders a right-side tab panel;
- maps tabs to feature components;
- shows webcam perception overlay, thinking display, and status bar.

The frontend is not a router-driven application. The tab registry in `App.tsx` is the primary feature navigation mechanism.

## Primary Data Flow

### Normal chat

```text
ChatPanel
  -> getWebSocket().send({type: "text", content, tts_enabled, use_vision})
  -> main.handle_websocket_message
  -> main.handle_chat_message
  -> optional webcam frame + optional screen screenshot
  -> LLMBrain.generate_response
  -> memory history + self-model + active goals + optional recalled memories
  -> provider-compatible LLM
  -> LLMBrain tool execution and follow-up
  -> optional TTS file
  -> broadcast {action: "reply", text, actions, audio_url}
  -> useWebSocket.handleMessage
  -> Zustand chat state + audio + VRM DOM events
```

`LLMBrain` is the current owner of prompt assembly and AI tool execution. Do not add a second chat pipeline without explicitly deciding how histories, tools, TTS, and websocket events stay consistent.

### WebSocket contract

Backend inbound types currently include:

- `text`
- `stt_audio`
- `start_voice_listening`
- `stop_voice_listening`
- `set_speaking_state`
- `vision_frame` (currently a no-op stub)
- `toggle_screen_vision`
- `toggle_webcam_vision`
- `screen_capture`
- `vrm_body_click`
- `vrm_manual_action`
- `thinking_mode`
- `proactive_mode`
- `voice_profile`
- `config_update`
- `tool_execute`
- pet/chess/Stratego/editor/image action messages

Frontend outbound handling includes:

- `reply`
- `system`
- `screen_capture`
- `vrm_reaction`
- `interrupt_tts`
- `chess_update`
- `stratego_update`
- `pet_update`
- `pet_move`
- `editor_update`
- `vision_update`
- `tool_result`

When adding a websocket message:

1. define its backend producer;
2. add its frontend consumer in `useWebSocket.ts` or a registered `onWebSocketMessage` handler;
3. update shared types/state if it persists in UI;
4. test reconnect and multiple-client behavior.

### REST feature flow

Most panels use direct `/api/...` fetches. The backend route is usually in `main.py`, and domain logic lives in a core engine or plugin. REST routes do not automatically update other clients; use `broadcast_message` when state changes must be live everywhere.

## Memory and Personhood Systems

### Live memory: `MemoryEngine`

`core/memory_engine.py` is the live memory owner passed into `LLMBrain`.

It stores:

- conversation history;
- explicit facts;
- explicit durable memories;
- vision observations;
- embeddings when a provider is configured;
- reversible memory archive;
- semantic links;
- librarian state.

AI memory actions are exposed by `LLMBrain` as `memory_manage`. They are executed in `LLMBrain._execute_tool`, not in the frontend. The frontend memory panel uses REST endpoints for browsing/editing.

Provider-backed embeddings are opt-in:

- `SARAH_EMBEDDING_API_KEY` or `OPENAI_API_KEY`
- `SARAH_EMBEDDING_MODEL`
- optional `SARAH_EMBEDDING_BASE_URL`

Without these settings, Sarah uses lexical overlap retrieval. Existing memories require the explicit bounded `/api/memory/embeddings/backfill` operation before semantic search can cover them.

### Self-model

`core/self_model.py` owns versioned identity sections. It uses optimistic revision checks and archives previous state. `LLMBrain.get_full_system_prompt()` injects the current self-model into every generation.

The frontend editor is `SelfModelPanel.tsx` and the API is `/api/self-model`.

### Goals

`core/goal_engine.py` owns durable hierarchical goals and append-only progress notes. `LLMBrain` exposes `goal_manage` when memory editing permission is enabled. Goals are injected into the system prompt and used by heartbeat wake reasons.

Frontend: `GoalsPanel.tsx`.
API: `/api/goals`, `/api/goals/{goal_id}`.

### Heartbeat

`core/heartbeat_engine.py` persists an opt-in policy, daily cap, interval, idle threshold, cancellation state, current wake reason, decision history, and restart recovery.

`main.heartbeat_loop()` only wakes Sarah when:

- heartbeat is enabled;
- Sarah is not already running;
- the user has been idle long enough;
- interval and daily cap allow a run.

A heartbeat prompt asks Sarah to inspect self/goal context and choose a bounded action. Decisions are classified as `observe`, `reflect`, `remember`, `advance_goal`, `idle`, `cancelled`, or `error`. Tool-confirmed effects take precedence over model-declared tags.

Frontend: `HeartbeatPanel.tsx`.
API: `/api/heartbeat`, `/api/heartbeat/cancel`.

### Nightly librarian

The current librarian is intentionally conservative. It runs once per calendar day at `SARAH_LIBRARIAN_HOUR` (default 3) and:

- archives exact normalized duplicates;
- reports semantic duplicate candidates when embeddings exist;
- creates conservative embedding links;
- never automatically merges semantic candidates;
- preserves archived records.

The librarian is not yet a full LLM judging pipeline. A future pass can review candidates with confidence thresholds and user-visible approval.

### Diary

`core/advanced_diary.py` is private reflection storage. It is separate from durable memory and self-model. The UI can inspect it through privileged endpoints, and peek events can be surfaced to Sarah if enabled.

Do not treat the diary as an authoritative user-memory store. It is reflective/private state.

### Disconnected memory prototype

`core/memory_system/` contains a multi-layer experimental architecture with working/episodic/semantic/procedural/emotional stores, graph storage, vector storage, decay, and consolidation. It is not initialized by `main.py`, not passed to `LLMBrain`, and currently creates random placeholder embeddings. Do not extend it as if it were live. Either migrate it deliberately into `MemoryEngine` or mark it as an experiment.

## Vision and Perception

`VisionEngine` owns OpenCV webcam capture. `ImageUnderstandingSystem` owns image analysis/captioning. The continuous monitor in `main.py`:

1. captures a frame;
2. generates a description using configured Hugging Face captioning or local image statistics;
3. stores changed descriptions as vision observations;
4. broadcasts `vision_update`;
5. may generate a rate-limited proactive comment;
6. supplies the latest description as uncertain context during chat.

Frontend: `PerceptionPanel.tsx`, webcam overlay, `useWebSocket.ts`.

Known limitations:

- `handle_vision_frame` is a stub; live backend webcam capture is the active path.
- synchronous OpenCV capture occurs inside the async monitor and should eventually move to an executor/thread.
- the current local fallback describes dimensions/colors, not objects or actions.
- screen vision is on-demand capture, not a continuous screen perception stream.

## Avatar and VRM

### Live owner

`app/src/components/VRMViewer.tsx` owns the actual Three.js scene, VRM loading, animation loop, expressions, lip sync, outfit changes, pet movement, and temporary FBX preview.

`core/vrm_action_engine.py` is the live backend registry used for action metadata, body reactions, and LLM action guidance.

Frontend action events:

- `vrm-expression`
- `vrm-animation`
- `vrm-lipsync`
- `vrm-outfit-change`
- `pet-move`
- `fbx-animation-test`
- `fbx-animation-clear`

### Partial/legacy owner

`core/vrm_advanced.py` contains a much larger animation/outfit/accessory library. Its endpoints instantiate the engine for metadata responses, but the live viewer does not consume that engine’s animation queue. Adding an animation only to `vrm_advanced.py` does not make it playable in the avatar.

This is a real consolidation gap. Future avatar work must choose one authoritative action/animation registry and make the viewer consume it.

### FBX testing

Temporary FBX files belong in `sarah_ai/static/fbx_tests/`. `FBXTestPanel.tsx` scans `/api/fbx-tests`, uses Three.js `FBXLoader` to inspect clips, and sends selected files to `VRMViewer`. The preview displays the FBX temporarily instead of Sarah’s VRM; it is not animation retargeting onto Sarah’s skeleton.

## Voice and Audio

- `stt_engine_advanced.py` is initialized and receives websocket audio chunks.
- browser microphone data flows from `ChatPanel` to `stt_audio`.
- STT transcription calls `handle_chat_message` using the `text` field; the server normalizes both `content` and `text`.
- `tts_engine.py` produces `/static/response.mp3` for chat replies.
- frontend plays reply audio from `audio_url`.
- interruption broadcasts `interrupt_tts`, but the backend TTS engine interruption remains incomplete.

Voice clone upload is a scaffold. `process_clone_job` has a real Coqui path when configured, while the Resemble path is explicitly not implemented.

## Plugins and Games

`PluginManager` only loads `Plugin` classes from direct files in `sarah_ai/plugins/`. It does not recursively discover every directory or automatically register plugin tools with `LLMBrain`.

Live plugin connections:

- Chess: `chess_v2` wrapper reuses `chess_game.py`; routes broadcast `chess_update`.
- Stratego: `stratego.py`; routes broadcast `stratego_update`.
- Pet: `tamagotchi_v2.py` with fallback; routes broadcast `pet_update`, `pet_move`, and VRM reactions.
- Editor: `collab_editor.py`; routes broadcast `editor_update`.
- Images: `image_generation.py`; REST routes call the plugin.
- Ebooks: `plugins/ebook_reader.py` wraps `core/ebook_reader.py`; REST routes call the wrapper.

The separate `stratego_v2/` package is not the direct plugin selected by current startup unless the loader is changed.

## Feature Integration Findings

### Audit status: 2026-10-09

The repository was audited after the major feature additions. The core live paths do connect, but the untouched-file concern was valid in several areas: Sarah contains multiple parallel implementations whose names imply more integration than currently exists. The main verified runtime defects found during this audit were repaired:

- server STT callbacks sent `text` while chat only read `content`;
- the VRM REST body-interaction route called `add_conversation` with an invalid argument shape;
- startup scheduled `pet_monitor()` even though the effective function was nested inside a legacy proactive loop;
- duplicate proactive-loop declarations obscured which loop actually ran;
- backend dependency/runtime import issues were repaired with headless OpenCV, maintained WebRTC VAD wheels, and ebook plugin import compatibility.

The backend now compiles and imports successfully. Static analysis still reports a broad set of older annotation-quality issues in `main.py`; those are code-quality debt, not current import failures.

### Verified connected

- Chat ↔ LLM ↔ memory history ↔ self-model/goals.
- Chat ↔ webcam/screen snapshots ↔ LLM vision input.
- Continuous webcam ↔ vision memory ↔ websocket ↔ perception UI.
- Heartbeat ↔ self-model/goals ↔ LLM ↔ diary/memory/goal tools.
- VRM reply actions ↔ websocket ↔ Three.js viewer.
- Games/pet/editor plugin routes ↔ frontend panels and websocket updates.
- Outfit REST state ↔ viewer outfit-change event.

### Verified gaps or legacy seams

1. `core/memory_system/` is disconnected from live memory and uses placeholder random embeddings.
2. `core/vrm_advanced.py` is not the live avatar animation owner.
3. `handle_vision_frame` is a no-op legacy websocket path.
4. Screen perception is on-demand only.
5. TTS interruption is frontend pause plus backend TODO, not a complete cancellation pipeline.
6. Voice clone Resemble integration is a scaffold.
7. Plugin discovery is direct-file only and does not automatically expose plugin tools to the brain.
8. `app/src/hooks/useWebSocket.ts` uses broad `any` types and global singleton websocket state; reconnect and multi-client semantics need a later typed connection layer.
9. `MemoryEngine` JSON writes are not yet atomic/locked like the newer self/goal/heartbeat services.
10. Many existing panels use direct fetches and do not share a typed API client or centralized query/cache layer.
11. `vrm_advanced.py` and `memory_system/` should be treated as candidates for consolidation, not assumed runtime systems.

## Extension Rules for Future AIs

1. Find the live owner before editing a similarly named legacy module.
2. Trace the complete path: UI action → REST/websocket → main route/handler → domain service/plugin → broadcast/state update.
3. Do not create a second source of truth for memory, avatar actions, goals, or runtime state.
4. Add a typed frontend contract for every new websocket action or API response.
5. Preserve user data. Prefer migrations, archives, atomic writes, and soft merges.
6. Add permission checks before giving the model a new consequential tool.
7. Autonomous behavior must be opt-in, bounded, cancellable, rate-limited, and logged.
8. Never claim an action succeeded unless the tool/domain service returned success.
9. Provider-dependent features must degrade clearly and locally when unconfigured.
10. Test the narrow behavior first, then build the frontend and compile the backend.
11. Do not copy external repositories. Use their architecture as inspiration and implement Sarah-specific systems.
12. Keep this guide updated whenever ownership, routes, persistence, or message contracts change.

## Recommended Consolidation Roadmap

1. Add automated backend integration tests for startup, API routes, websocket contracts, and plugin loading.
2. Make JSON domain stores atomic and process-safe, or migrate durable state to a transactional database.
3. Consolidate live VRM actions and advanced animation metadata into one registry consumed by `VRMViewer`.
4. Move webcam capture off the async event loop and introduce real object/action perception providers.
5. Replace the disconnected experimental memory system or remove it after a deliberate migration.
6. Add a typed API client and discriminated websocket message union in the frontend.
7. Finish TTS cancellation and voice-clone provider adapters.
8. Add user-facing review for semantic memory candidates and link graph navigation.
9. Add observability: startup health, provider availability, task outcomes, latency, and failure history.
10. Keep all autonomy changes behind explicit policy, budget, and audit controls.
