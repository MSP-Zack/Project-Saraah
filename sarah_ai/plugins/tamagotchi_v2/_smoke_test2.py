#!/usr/bin/env python3
import sys
from pathlib import Path
import threading
from pprint import pprint

# Ensure repo root is importable
repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))

from sarah_ai.plugins.tamagotchi_v2 import Plugin


def run_autonomous(plugin: Plugin, out: dict):
    try:
        out['result'] = plugin.autonomous_action()
    except Exception as e:
        out['error'] = str(e)


def main():
    p = Plugin()
    print("Starting autonomous action with timeout (5s)")
    out = {}
    t = threading.Thread(target=run_autonomous, args=(p, out))
    t.start()
    t.join(5.0)
    if t.is_alive():
        print("Autonomous action timed out (thread still alive)")
    else:
        print("Autonomous action result:")
        pprint(out.get('result') or out.get('error'))


if __name__ == '__main__':
    main()
