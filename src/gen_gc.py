"""Build the GameCube controller feature for one region from src/gcpad/."""
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, 'gcpad'))
from layout import GC_BASE, GC_END
from ops import Feature, Hook
import anchors

DEVKIT = os.environ.get('DEVKITPPC', '/opt/devkitpro/devkitPPC')
CC = DEVKIT + '/bin/powerpc-eabi-'

USA_DOL = None

def compile_hook(name, defs):
    src = os.path.join(HERE, 'gcpad')
    tmp = tempfile.mkdtemp(prefix='gcpad')
    D = ['-D%s=%s' % kv for kv in defs.items()] + ['-DHOOK_' + name]
    cflags = [
        '-O2', '-fno-unroll-loops', '-mbig-endian', '-msoft-float', '-msdata=none',
        '-ffreestanding', '-fno-pic', '-fno-asynchronous-unwind-tables',
        '-fno-stack-protector', '-nostdlib', '-Wall'
    ]
    subprocess.check_call([CC + 'gcc'] + cflags + D + ['-c', src + '/gcpad.c', '-o', tmp + '/g.o'])
    subprocess.check_call([CC + 'gcc', '-mbig-endian', '-c', '-x', 'assembler-with-cpp'] + D +
                          [src + '/hooks.S', '-o', tmp + '/h.o'])
    subprocess.check_call([CC + 'ld', '-T', src + '/link.ld', '-o', tmp + '/b.elf', tmp + '/h.o', tmp + '/g.o'])
    subprocess.check_call([CC + 'objcopy', '-O', 'binary', tmp + '/b.elf', tmp + '/b.bin'])
    b = open(tmp + '/b.bin', 'rb').read()
    # clean up temp dir
    for f in ('g.o', 'h.o', 'b.elf', 'b.bin'):
        p = os.path.join(tmp, f)
        if os.path.exists(p): os.remove(p)
    os.rmdir(tmp)
    return list(struct.unpack('>%dI' % (len(b) // 4), b))

def build(region, dol):
    global USA_DOL
    if USA_DOL is None:
        USA_DOL = dol if region == 'R8PE01r2' else None

    # resolve addresses using USA reference DOL
    a = anchors.resolve(USA_DOL if USA_DOL is not None else dol, dol)

    defs = {
        'STATE': '0x%08Xu' % a['STATE'],
        'SI_TYPES': '0x%08Xu' % a['SiTypes'],
        'SI_BUSY': '0x%08Xu' % a['SiBusy'],
        'SI_SHADOW': '0x%08Xu' % a['SiShadow'],
        'WPAD_TBL': '0x%08Xu' % a['WpadTbl'],
        'FN_SIGETTYPE': '0x%08Xu' % a['SIGetType'],
        'FN_OSDISABLE': '0x%08Xu' % a['OSDisableInterrupts'],
        'FN_OSRESTORE': '0x%08Xu' % a['OSRestoreInterrupts'],
    }

    ops, cur = [], GC_BASE

    hook_specs = [
        ('POLL', a['KPADiRead'], 'KPADiRead: SI hardware auto-poller'),
        ('SAMPLE', a['sample_site'], 'KPADiRead: GameCube pad -> Classic Controller sample bridge'),
        ('PROBE', a['WPADProbe'], 'WPADProbe: report Classic Controller on channel 0'),
    ]

    for name, site, note in hook_specs:
        body = compile_hook(name, defs)
        orig = struct.unpack('>I', dol.read(site, 4))[0]
        ops.append(Hook(site, orig, body, cur, note=note))
        cur += (len(body) * 4 + 15) & ~15

    if cur > GC_END:
        raise SystemExit(f'gc code overflows its window: 0x{cur:X} > 0x{GC_END:X}')

    return Feature('gc', 'GameCube controller', region, ops)
