"""Find the Super Paper Mario addresses the GameCube-pad patch needs in any revision.

Everything is written once against USA Rev 2 (R8PE01r2); the other discs share
the same compiled code at other addresses. A function is located by matching
a window of USA instructions against the target DOL with the relocatable bits
(branch displacements, address halves, small-data offsets) masked out, and it
must match exactly once. Data addresses are then read back from the matched
code (the lis/addi that references them), never guessed.
"""
import struct

def mask(w):
    op = w >> 26
    if op in (18,):                      # b / bl: keep opcode, AA, LK
        return w & 0xFC000003
    if op == 16:                         # bc: keep everything but displacement
        return w & 0xFFFF0003
    if op in (7, 14, 15, 24, 25, 26, 27, 28, 29):   # mulli/addi/lis/ori/oris/xori/andi
        return w & 0xFFFF0000
    if 32 <= op <= 55:                   # loads/stores: drop displacement
        return w & 0xFFFF0000
    return w

def words(d, va, n):
    b = d.read(va, n * 4)
    return list(struct.unpack('>%dI' % n, b)) if b and len(b) == n * 4 else None

class Finder:
    def __init__(self, ref, tgt):
        self.ref, self.tgt = ref, tgt
        # Find main text section (usually Text 1 or first text with >0x100000 size)
        text_secs = [x for x in tgt.secs if x[3] < 7 and x[2] > 0x10000]
        o, a, s, _ = text_secs[0] if text_secs else tgt.secs[0]
        self.tw = struct.unpack('>%dI' % (s // 4), tgt.data[o:o + s])
        self.tbase = a
        self.tm = [mask(w) for w in self.tw]

    def _hits(self, rm, tm, tbase, n):
        hits, first = [], rm[0]
        for i in range(len(tm) - n):
            if tm[i] == first and tm[i:i + n] == rm:
                hits.append(tbase + i * 4)
        return hits

    def locate(self, ref_va, n=24, ordered=False):
        """address in the target of the code at ref_va; must match exactly once"""
        rw = words(self.ref, ref_va, n)
        if not rw:
            raise SystemExit('could not read reference words at 0x%08X' % ref_va)
        rm = [mask(w) for w in rw]
        hits = self._hits(rm, self.tm, self.tbase, n)
        if len(hits) != 1 and ordered:
            text_secs = [x for x in self.ref.secs if x[3] < 7 and x[2] > 0x10000]
            o, a, s, _ = text_secs[0] if text_secs else self.ref.secs[0]
            rtm = [mask(w) for w in struct.unpack('>%dI' % (s // 4), self.ref.data[o:o + s])]
            rhits = self._hits(rm, rtm, a, n)
            if len(rhits) == len(hits) and ref_va in rhits:
                return hits[rhits.index(ref_va)]
        if len(hits) != 1:
            raise SystemExit('anchor %08X: %d matches: %s' % (ref_va, len(hits), [hex(h) for h in hits]))
        return hits[0]

    def pair(self, va_start, n=20):
        """the target revision's value for the address loaded by lis + addi near va_start"""
        for i in range(n):
            w = self.tgt.r32(va_start + i * 4)
            if (w >> 26) == 15:  # lis
                reg = (w >> 21) & 31
                for j in range(1, 10):
                    w2 = self.tgt.r32(va_start + (i + j) * 4)
                    if (w2 >> 26) == 14 and ((w2 >> 16) & 31) == reg and ((w2 >> 21) & 31) == reg:
                        imm = w2 & 0xFFFF
                        if imm >= 0x8000:
                            imm -= 0x10000
                        return (((w & 0xFFFF) << 16) + imm) & 0xFFFFFFFF
        raise SystemExit('no lis/addi pair found near 0x%08X' % va_start)


# USA reference addresses
REF_FUNCS = {
    'WPADProbe':           (0x802ce890, 20, False),
    'SIGetType':           (0x8026b440, 24, False),
    'KPADiRead':           (0x802df4f0, 8, False),
}

STATE_ADDR = 0x80005D40  # padding in Section 0 text

def resolve(ref, tgt):
    f = Finder(ref, tgt)
    r = {}
    for name, (va, n, ordr) in REF_FUNCS.items():
        r[name] = f.locate(va, n=n, ordered=ordr)

    # find sample count check (lbz r0, 271(r31)) inside KPADiRead
    for va in range(r['KPADiRead'], r['KPADiRead'] + 0x200, 4):
        if tgt.r32(va) == 0x881f010f:
            r['sample_site'] = va
            break
    else:
        raise SystemExit('sample_site (lbz r0, 271(r31)) not found inside KPADiRead')

    r['SiTypes'] = f.pair(r['SIGetType'], n=15)
    r['SiBusy'] = r['SiTypes'] - 0x18
    r['SiShadow'] = r['SiBusy'] + 4
    r['WpadTbl'] = f.pair(r['WPADProbe'], n=15)

    # OSDisableInterrupts is called early in WPADProbe
    for i in range(12):
        w = tgt.r32(r['WPADProbe'] + i * 4)
        if (w >> 26) == 18 and (w & 1) == 1:
            disp = w & 0x03FFFFFC
            if disp >= 0x02000000:
                disp -= 0x04000000
            r['OSDisableInterrupts'] = r['WPADProbe'] + i * 4 + disp
            break
    else:
        raise SystemExit('OSDisableInterrupts call not found in WPADProbe')

    r['OSRestoreInterrupts'] = r['OSDisableInterrupts'] + 0x28
    r['STATE'] = STATE_ADDR
    return r
