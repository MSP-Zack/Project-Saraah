# Tamagotchi v2 (plugin skeleton)

This folder contains an initial skeleton for the Tamagotchi v2 plugin. It is intended to replace and extend `sarah_ai/plugins/tamagotchi_pet.py` with a modular architecture (NeedsEngine, Behavior, LLM hooks, persistence).

Files:
- `plugin.py` - core skeleton with `TamagotchiManager` and `Plugin` wrapper.
- `GDD.md` - design notes and roadmap (in the repository root for the plugin).

Next steps:
- Implement BehaviorTree (or utility AI) and NeedsEngine in `plugin.py`.
- Add migration logic from the v1 save file (`memory/tamagotchi.json`).
- Add event hooks for frontend/VRM (e.g., on_evolve, on_sick) and LLM prompt templates.
