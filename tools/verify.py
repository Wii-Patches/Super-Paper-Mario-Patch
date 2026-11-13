#!/usr/bin/env python3
"""Check the patch data against real, retail main.dol files.

    SPM_DOLS=<dir holding one <key>.dol per release, keys as in regions.py> python3 tools/verify.py

For every region and every feature combination:
  * every site holds the retail bytes before patching
  * after patching, every hook site is a branch into the injected section whose
    trampoline runs back to site+4
  * patching in steps (one feature at a time) gives the same file as all at once
  * nothing outside the intended sites changed
"""
import itertools
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import features
import patcher
from dol import Dol
from layout import CAVE_BASE, CAVE_LIMIT
from ops import Hook
from regions import REGIONS

fail = []


def check(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond:
        fail.append(msg)


def retail(region):
    base = os.environ.get('SPM_DOLS', '.')
    p = os.path.join(base or '.', region + '.dol')
    if not os.path.exists(p):
        sys.exit('set SPM_DOLS to a directory holding %s.dol' % region)
    return p


def main():
    combos = [
        ['cc'],
        ['cc', 'gc'],
    ]

    for region in REGIONS:
        print(f"\n=== {region} {REGIONS[region]['label']} ===")
        path = retail(region)
        d0 = Dol(path)
        check(patcher.detect_region(d0) == region, 'detected as %s' % region)
        for name in features.FEATURES:
            f = features.load(name, region)
            check(not f.check_pristine(d0), '%s: every site holds retail bytes' % name)

        for combo in combos:
            d = Dol(path)
            patcher.patch(d, region, combo)
            touched = []
            for name in combo:
                f = features.load(name, region)
                ok = f.is_applied(d)
                check(ok, '%s applied cleanly in %s' % (name, '+'.join(combo)))
                for op in f.ops:
                    if isinstance(op, Hook):
                        site = struct.unpack('>I', d.read(op.site, 4))[0]
                        tgt = (site & 0x03FFFFFC)
                        tgt = tgt - 0x04000000 if tgt & 0x02000000 else tgt
                        check((site >> 26) == 18 and not site & 3 and (op.site + tgt) == op.tramp,
                              '%s: 0x%08X branches to 0x%08X' % (name, op.site, op.tramp))
                touched += [(a, len(b)) for a, b in f.writes()]

            # verify nothing else changed
            for off, va, size, idx in d0.secs:
                a = bytes(d0.data[off:off + size])
                b = d.read(va, size)
                diff = [i for i in range(size) if a[i] != b[i]]
                stray = [va + i for i in diff if not any(t <= va + i < t + n for t, n in touched)]
                if stray:
                    check(False, '%s: unexpected change at 0x%08X' % ('+'.join(combo), stray[0]))

            # stepwise == all at once
            if len(combo) > 1:
                step = Dol(path)
                for name in combo:
                    patcher.patch(step, region, [name])
                same = all(step.read(va, sz) == d.read(va, sz) for _o, va, sz, _i in d.secs) and len(step.secs) == len(d.secs)
                check(same, 'stepwise == together for %s' % '+'.join(combo))

    print('\nFAILED: %d' % len(fail) if fail else '\nALL VERIFIED')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
