#!/usr/bin/env python3
from pprint import pprint
import sys
from pathlib import Path

# Ensure repository root is on sys.path so 'sarah_ai' is importable
repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))

from sarah_ai.plugins.tamagotchi_v2 import Plugin


def pretty_needs(state):
    needs = state.get("needs", {})
    return {k: round(v, 2) for k, v in needs.items()}


def main():
    p = Plugin()
    print("Plugin info:")
    pprint(p.get_info())

    state = p.get_state()
    print("Initial state needs:")
    pprint(pretty_needs(state))

    print("LLM context sample:\n")
    print(p.get_llm_context())

    print("Suggestions:")
    pprint(p.suggest_actions())

    print("Running an autonomous action:")
    auto = p.autonomous_action()
    pprint(auto)

    print("Feeding a meal:")
    pprint(p.feed("meal"))

    print("Petting:")
    pprint(p.pet())


if __name__ == "__main__":
    main()
