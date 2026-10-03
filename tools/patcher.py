"""Apply the selected patches to one main.dol."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features
from dol import Dol
from ops import apply_static
from regions import REGIONS

ORDER = ('cc', 'gc')


def detect_region(dol):
    """Which release this main.dol is, from its own bytes (None if unknown)."""
    for region in REGIONS:
        for name in ORDER:
            if features.available(name, region):
                f = features.load(name, region)
                if not f.check_pristine(dol) or f.is_applied(dol):
                    return region
    return None


def status(dol, region):
    """{feature: 'clean' | 'patched' | 'mismatch'} for each feature on this DOL."""
    out = {}
    for name in ORDER:
        if not features.available(name, region):
            continue
        f = features.load(name, region)
        if f.is_applied(dol):
            out[name] = 'patched'
        elif not f.check_pristine(dol):
            out[name] = 'clean'
        else:
            out[name] = 'mismatch'
    return out


def patch(dol, region, which):
    """Patch `dol` (a dol.Dol) in place with the features named in `which`."""
    which = list(which)

    # GC requires CC hook to handle synthesized Classic Controller inputs
    if 'gc' in which and 'cc' not in which:
        which.append('cc')

    feats = [features.load(n, region) for n in ORDER if n in which]
    feats = [f for f in feats if not f.is_applied(dol)]
    if not feats:
        return []
    apply_static(dol, feats)
    return [f.title for f in feats]


def patch_file(src, dst, region, which):
    dol = Dol(src)
    done = patch(dol, region, which)
    dol.save(dst)
    return done


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Patch a Super Paper Mario main.dol')
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--region', choices=sorted(REGIONS), help='default: detect')
    ap.add_argument('--cc', action='store_true', help='Classic Controller')
    ap.add_argument('--gc', action='store_true', help='GameCube controller (port 1)')
    a = ap.parse_args()

    d = Dol(a.src)
    reg = a.region or detect_region(d)
    if not reg:
        sys.exit('could not identify this main.dol; pass --region')

    explicit = [n for n in ORDER if getattr(a, n, False)]
    which = explicit if explicit else ['cc', 'gc']

    done = patch_file(a.src, a.dst, reg, which)
    print('Patched %s (%s): %s' % (a.dst, reg, ', '.join(done) or 'nothing new'))
