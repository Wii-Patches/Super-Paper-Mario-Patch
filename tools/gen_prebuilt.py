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

DOL_PATHS = {
    'R8PE01': os.path.join(DOLS_DIR, 'extracted_spm_usa2', 'sys', 'main.dol'),
    'R8PP01': os.path.join(DOLS_DIR, 'extracted_spm_pal1', 'sys', 'main.dol'),
    'R8PJ01': os.path.join(DOLS_DIR, 'extracted_spm_jpn1', 'sys', 'main.dol'),
    'R8PK01': os.path.join(DOLS_DIR, 'extracted_spm_kor', 'sys', 'main.dol'),
}

# Fallback: check flat DOL names
for r, p in list(DOL_PATHS.items()):
    if not os.path.exists(p):
        flat = os.path.join(DOLS_DIR, f'{r}.dol')
        if os.path.exists(flat):
            DOL_PATHS[r] = flat

out_dir = os.path.join(HERE, 'prebuilt')
os.makedirs(out_dir, exist_ok=True)

# Set USA reference DOL for gen_gc
usa_dol = Dol(DOL_PATHS['R8PE01'])
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
