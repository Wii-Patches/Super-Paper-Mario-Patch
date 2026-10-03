"""Load the prebuilt feature definitions (tools/prebuilt/<feature>_<region>.json)."""
import json
import os
import struct
import sys

from ops import Blob, Feature, Hook, Patch

if getattr(sys, 'frozen', False):
    PREBUILT = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), 'prebuilt')
else:
    PREBUILT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prebuilt')

FEATURES = ('cc', 'gc')
TITLES = {
    'cc': 'Classic Controller',
    'gc': 'GameCube controller',
}


def dump(feature):
    ops = []
    for op in feature.ops:
        if isinstance(op, Patch):
            ops.append(dict(t='patch', addr=op.addr, new=op.new.hex(), orig=op.orig.hex(), note=op.note))
        elif isinstance(op, Blob):
            ops.append(dict(t='blob', addr=op.addr, data=op.data.hex(), note=op.note))
        elif isinstance(op, Hook):
            ops.append(dict(t='hook', site=op.site, orig=op.orig, payload=op.payload, tramp=op.tramp, note=op.note))
    return dict(feature=feature.name, title=feature.title, region=feature.region, ops=ops)


def load_dict(j):
    ops = []
    for o in j['ops']:
        if o['t'] == 'patch':
            ops.append(Patch(o['addr'], bytes.fromhex(o['new']), bytes.fromhex(o['orig']), o.get('note', '')))
        elif o['t'] == 'blob':
            ops.append(Blob(o['addr'], bytes.fromhex(o['data']), o.get('note', '')))
        elif o['t'] == 'hook':
            ops.append(Hook(o['site'], o['orig'], o['payload'], o['tramp'], o.get('note', '')))
    return Feature(j['feature'], j['title'], j['region'], ops)


def load(name, region):
    with open(os.path.join(PREBUILT, '%s_%s.json' % (name, region))) as f:
        return load_dict(json.load(f))


def available(name, region):
    return os.path.exists(os.path.join(PREBUILT, '%s_%s.json' % (name, region)))
