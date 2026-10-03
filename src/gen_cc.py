"""Build the Classic Controller feature: Vague Rant's Gecko codes, as ops."""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from layout import CC_BASE, CC_END
from ops import Feature, Hook, Patch

def parse(text, dol):
    lines = [l.split()[:2] for l in text.splitlines() if l.strip() and not l.lstrip().startswith(('*', '$', '#'))]
    i, out = 0, []
    while i < len(lines):
        a, b = lines[i]
        kind, addr = int(a[:2], 16), 0x80000000 | (int(a[2:], 16) & 0x01FFFFFF)
        if kind == 4:
            new_bytes = bytes.fromhex(b)
            orig_bytes = dol.read(addr, len(new_bytes))
            out.append(('04', addr, new_bytes, orig_bytes))
            i += 1
        elif kind == 0xC2:
            n = int(b, 16)
            ws = [int(x, 16) for ln in lines[i + 1:i + 1 + n] for x in ln]
            out.append(('C2', addr, ws))
            i += 1 + n
        else:
            raise ValueError('unsupported code line: %s %s' % (a, b))
    return out

def build(region, dol):
    fn = f'{region}.txt'
    text = open(os.path.join(HERE, 'cc', fn)).read()
    ops, cur = [], CC_BASE
    hook_notes = [
        'pointer: left/right stick -> Tippi cursor',
        'read_kpad_stick: left stick -> digital D-pad directions',
        'read_kpad_button: Classic Controller buttons -> Wii Remote bits & pointer toggle'
    ]
    parsed = parse(text, dol)
    hook_idx = 0
    for item in parsed:
        if item[0] == '04':
            _, addr, new_bytes, orig_bytes = item
            ops.append(Patch(addr, new_bytes, orig_bytes, note='HBM: disable 64-frame getInfoAsync timer'))
        elif item[0] == 'C2':
            _, addr, body = item
            orig = struct.unpack('>I', dol.read(addr, 4))[0]
            note = hook_notes[hook_idx] if hook_idx < len(hook_notes) else ''
            hook_idx += 1
            ops.append(Hook(addr, orig, body, cur, note=note))
            cur += (len(body) * 4 + 15) & ~15

    if cur > CC_END:
        raise SystemExit(f'cc code overflows its window: 0x{cur:X} > 0x{CC_END:X}')
    return Feature('cc', 'Classic Controller', region, ops)
