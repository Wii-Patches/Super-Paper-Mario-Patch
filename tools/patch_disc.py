#!/usr/bin/env python3
"""Command-line tool to patch a .wbfs/.iso disc image in place.

    python3 tools/patch_disc.py "Super Paper Mario.wbfs" --cc --gc
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import disc
import features
import patcher


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('image', help='Path to .wbfs or .iso disc image')
    ap.add_argument('--cc', action='store_true', help='Enable Classic Controller support')
    ap.add_argument('--gc', action='store_true', help='Enable GameCube Controller support (port 1)')
    a = ap.parse_args()

    explicit = [n for n in patcher.ORDER if getattr(a, n, False)]
    which = explicit if explicit else ['cc', 'gc']

    ok = []
    disc.run_patch(a.image, print, lambda good, msg: ok.append(good), which)
    sys.exit(0 if ok and ok[0] else 1)


if __name__ == '__main__':
    main()
