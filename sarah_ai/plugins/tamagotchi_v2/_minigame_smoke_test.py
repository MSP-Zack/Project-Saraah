#!/usr/bin/env python3
from pprint import pprint
import sys
from pathlib import Path

# Ensure repo root on path
repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))

from sarah_ai.plugins.tamagotchi_v2 import Plugin


def main():
    p = Plugin()
    print('Starting mini-game session...')
    r = p.start_minigame('fetch', 'normal')
    pprint(r)
    sid = r.get('session_id')
    print('Submitting test score 7...')
    res = p.submit_minigame(sid, 7)
    pprint(res)


if __name__ == '__main__':
    main()
