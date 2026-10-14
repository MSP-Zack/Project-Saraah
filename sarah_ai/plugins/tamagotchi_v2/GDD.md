# Tamagotchi v2 - Game Design Document

## Vision
Rebuild the existing Tamagotchi into a full-featured, persistent virtual pet mini-game with high-quality VRM presentation, emergent AI-driven behavior, deep LLM interaction through Sarah, and a polished set of activities that make the pet feel like a complete game rather than a demo.

## Core Pillars
- Immersion: 3D VRM pet with locomotion, animation blending, lip-sync and expressive feedback.
- Depth: multi-layered needs, long-term memory, personality and progression (evolution, skills).
- Interaction: Sarah (LLM) acts as caregiver/companion; voice and text-driven interactions are meaningful.
- Replayability: mini-games, activities, missions, and daily goals.
- Integratability: clean plugin API for `sarah_ai` and frontend components for the `app` React UI.

## MVP (first milestone)
- Persistent `PetState` with needs: hunger, energy, happiness, hygiene, health.
- `TamagotchiManager` plugin: authoritative server-side (Python) state, events, save/load and migration from existing `tamagotchi.json`.
- Frontend `TamagotchiGame` React component with `PetVRM` using the existing `VRMViewer` and a HUD showing core needs.
- Basic locomotion: agent can navigate small scenes and idle/express animations.
- LLM integration hooks: `get_llm_context()` and `suggest_actions()` for Sarah to recommend care steps.
- One mini-game (placeholder) and simple audio feedback (SFX + TTS stubs).

## Major Systems (architecture)
- State & Persistence: single source-of-truth state in Python plugin; JSON save plus migration and optional cloud sync.
- Needs Engine: deterministic decay, modifiers, and recovery paths. Exposes callbacks/events (on_hungry, on_sick, on_evolve).
- Behavior System: behavior tree or utility AI that chooses actions when unsupervised (for emergent actions like exploring, seeking the player).
- Animation/VRM: frontend subsystem that maps pet state and behavior to animation blends and root motion.
- Interaction Layer: APIs for direct user actions (feed/pet/play) and LLM-driven suggestions and dialogues.
- Activities/Mini-games: modular activities with clear contracts so new games can be added without touching core engine.

## Integration Points in This Repo
- Existing plugin: `sarah_ai/plugins/tamagotchi_pet.py` — will be audited and migrated as needed.
- New plugin (v2): `sarah_ai/plugins/tamagotchi_v2/` — authoritative implementation and migration helpers.
- Frontend viewer: `app/src/components/VRMViewer.tsx` — reusable VRM renderer for `PetVRM`.
- New frontend components: `app/src/components/TamagotchiGame/` — game UI, HUD, and mini-game shells.

## Roadmap (phases)
1. Spike (1 week): Tech spike for VRM locomotion, LLM prompt patterns, and behavior proof-of-concept.
2. Core Engine + Frontend MVP (3-6 weeks): TamagotchiManager, persistence, VRM viewer integration, HUD, basic interactions.
3. Activities & Depth (6-12 weeks): Mini-games, training/progression, audio and TTS, polish.
4. Social & Multiplayer (optional): Presence, shared events, trading/visiting other pets.

## Immediate Implementation Tasks (this PR)
1. Audit `sarah_ai/plugins/tamagotchi_pet.py` and list gaps.
2. Add `sarah_ai/plugins/tamagotchi_v2/` skeleton with `TamagotchiManager` and `Plugin` wrapper.
3. Add frontend skeleton `app/src/components/TamagotchiGame/` with `TamagotchiGame`, `PetVRM`, and `HUD` components.
4. Wire basic state fetch stubs and document next integration steps.

---
