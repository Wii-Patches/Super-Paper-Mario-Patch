#!/usr/bin/env python3
"""Derive a revision's Classic Controller Gecko text (src/cc/<key>.txt) from USA Rev 2.

    python3 src/relocate_cc.py USA_REV2.dol TARGET.dol [out.txt]

src/cc/R8PE01r2.txt is the hand-written reference.  Every other revision runs the
same compiled code at other addresses, so each site is located by matching a window
of USA Rev 2 instructions (relocatable bits masked, see gcpad/anchors.py) and the
few words inside the payloads that depend on the build are rewritten:

  * the displaced instruction that each payload re-executes (it can carry a
    small-data offset that differs per build, e.g. Korea)
  * the lis/ori pair that loads the address of the helper called by the pointer hook
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, 'gcpad'))
from dol import Dol
import anchors

REF_TXT = os.path.join(HERE, 'cc', 'R8PE01r2.txt')


def parse(text):
    lines = [l.split()[:2] for l in text.splitlines() if l.strip() and not l.lstrip().startswith(('*', '$', '#'))]
    i, out = 0, []
    while i < len(lines):
        a, b = lines[i]
        kind = int(a[:2], 16)
        addr = 0x80000000 | (int(a[2:], 16) & 0x01FFFFFF)
        if kind == 4:
            out.append(['04', addr, int(b, 16)])
            i += 1
        elif kind == 0xC2:
            n = int(b, 16)
            out.append(['C2', addr, [int(x, 16) for ln in lines[i + 1:i + 1 + n] for x in ln]])
            i += 1 + n
        else:
            raise ValueError('unsupported code line: %s %s' % (a, b))
    return out


def fmt(codes):
    out = []
    for c in codes:
        if c[0] == '04':
            out.append('04%06X %08X' % (c[1] & 0x01FFFFFF, c[2]))
        else:
            ws = c[2]
            out.append('C2%06X %08X' % (c[1] & 0x01FFFFFF, len(ws) // 2))
            for i in range(0, len(ws), 2):
                out.append('%08X %08X' % (ws[i], ws[i + 1]))
    return '\n'.join(out) + '\n'


def words(d):
    o, a, s, _ = [x for x in d.secs if x[3] < 7 and x[2] > 0x10000][0]
    return a, struct.unpack('>%dI' % (s // 4), d.data[o:o + s])


def callers(d, target):
    base, w = words(d)
    hits = []
    for i, x in enumerate(w):
        if (x >> 26) == 18 and x & 1 and not x & 2:
            off = (x & 0x03FFFFFC)
            off = off - 0x04000000 if off & 0x02000000 else off
            if base + i * 4 + off == target:
                hits.append(base + i * 4)
    return hits


def find_pattern(d, pat, delta):
    """Addresses (match start + delta) where the exact word pattern occurs."""
    base, w = words(d)
    n = len(pat)
    return [base + i * 4 + delta for i in range(len(w) - n) if all(p is None or w[i + j] == p for j, p in enumerate(pat))]


# stw r0,0x60(r31) ... stw r0,0x64(r31) ... stw r0,0x68(r31): the button hook site
BTN_PATTERN = [0x901F0060, None, None, 0x901F0064, None, 0x901F0068]


def relocate(ref, tgt, ref_codes):
    f = anchors.Finder(ref, tgt)
    ref_btn = find_pattern(ref, BTN_PATTERN, 0x14)
    assert len(ref_btn) == 1
    btn_hits = find_pattern(tgt, BTN_PATTERN, 0x14)

    def locate(va):
        # the store pattern is exact when unique (it also finds revisions whose
        # surrounding code was reshuffled); otherwise fall back to the window match
        if va == ref_btn[0] and len(btn_hits) == 1:
            return btn_hits[0]
        return f.locate(va, n=24, ordered=True)

    # the helper called by the pointer hook: lis rX,hi / ori rX,rX,lo
    fn_ref = None
    for c in ref_codes:
        if c[0] == 'C2':
            ws = c[2]
            for i, x in enumerate(ws):
                if (x >> 16) == 0x3CC0 and any((y >> 16) == 0x60C6 and ((x & 0xFFFF) << 16 | (y & 0xFFFF)) in range(0x80000000, 0x80400000) for y in ws[i + 1:i + 4]):
                    fn_ref = (x & 0xFFFF) << 16 | [y for y in ws[i + 1:i + 4] if (y >> 16) == 0x60C6][0] & 0xFFFF
    assert fn_ref, 'helper address not found in the reference payload'
    fn_tgt = f.locate(fn_ref, n=24, ordered=True)
    if len(callers(tgt, fn_tgt)) != len(callers(ref, fn_ref)):
        print('note: helper 0x%08X has %d callers, the reference has %d' % (fn_tgt, len(callers(tgt, fn_tgt)), len(callers(ref, fn_ref))), file=sys.stderr)

    out = []
    for c in ref_codes:
        site = locate(c[1])
        if c[0] == '04':
            # in-place patch: the original instruction must be the same word
            if ref.r32(c[1]) != tgt.r32(site):
                raise SystemExit('patch site 0x%08X holds a different instruction' % site)
            out.append(['04', site, c[2]])
            continue
        ws = list(c[2])
        r_orig, t_orig = ref.r32(c[1]), tgt.r32(site)
        idx = [i for i, x in enumerate(ws) if x == r_orig]
        if len(idx) != 1:
            raise SystemExit('hook 0x%08X: displaced instruction %08X appears %d times' % (c[1], r_orig, len(idx)))
        ws[idx[0]] = t_orig
        for i, x in enumerate(ws):
            if (x >> 16) == 0x3CC0 and (x & 0xFFFF) == fn_ref >> 16:
                ws[i] = 0x3CC00000 | fn_tgt >> 16
                for j in range(i + 1, i + 4):
                    if ws[j] == 0x60C60000 | (fn_ref & 0xFFFF):
                        ws[j] = 0x60C60000 | (fn_tgt & 0xFFFF)
        out.append(['C2', site, ws])
    return out


def main():
    ref = Dol(sys.argv[1])
    tgt = Dol(sys.argv[2])
    codes = relocate(ref, tgt, parse(open(REF_TXT).read()))
    text = fmt(codes)
    if len(sys.argv) > 3:
        open(sys.argv[3], 'w').write(text)
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
