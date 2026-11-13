"""Regenerate tools/prebuilt/<feature>_<region>.json from the retail DOLs.

Rebuilding prebuilts needs devkitPPC and retail main.dol dumps for every region.
End users don't need this: prebuilt JSONs are committed.

    python3 tools/gen_prebuilt.py [/path/to/dols_folder]
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))

from dol import Dol
import features
import gen_cc
import gen_gc
from regions import REGIONS

DOLS_DIR = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SPM_DOLS', '.')

# one flat <key>.dol per release (keys are in tools/regions.py)
DOL_PATHS = {r: os.path.join(DOLS_DIR, '%s.dol' % r) for r in REGIONS}

out_dir = os.path.join(HERE, 'prebuilt')
os.makedirs(out_dir, exist_ok=True)

# Set USA reference DOL for gen_gc
usa_dol = Dol(DOL_PATHS['R8PE01r2'])
gen_gc.USA_DOL = usa_dol

for region in REGIONS:
    path = DOL_PATHS[region]
    if not os.path.exists(path):
        print(f'Skipping {region}: {path} not found')
        continue
    dol = Dol(path)
    print(f'Building features for {region}...')

    f_cc = gen_cc.build(region, dol)
    with open(os.path.join(out_dir, f'cc_{region}.json'), 'w') as f:
        json.dump(features.dump(f_cc), f, indent=2)

    f_gc = gen_gc.build(region, dol)
    with open(os.path.join(out_dir, f'gc_{region}.json'), 'w') as f:
        json.dump(features.dump(f_gc), f, indent=2)

print('Prebuilt JSONs generated successfully!')
