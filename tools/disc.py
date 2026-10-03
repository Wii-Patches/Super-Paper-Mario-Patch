"""Patch a whole disc image: extract with wit, patch sys/main.dol, rebuild.

The rebuilt image replaces the original in place, keeping its filename and
folder (USB loaders key off the `/wbfs/<Title> [ID6]/` layout); the untouched
original is kept next to it as `<name>.bak`.
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features
import patcher
from dol import Dol
from regions import REGIONS


def find_wit():
    """A wit bundled with this app (PyInstaller build) wins over PATH.

    --add-binary'd files land next to sys._MEIPASS: a plain onedir build puts
    them in _internal/, and a windowed macOS .app puts them in
    Contents/Frameworks/ instead of Contents/MacOS/ alongside the binary.
    """
    name = 'wit.exe' if os.name == 'nt' else 'wit'
    if getattr(sys, 'frozen', False):
        for base in (getattr(sys, '_MEIPASS', None), os.path.dirname(sys.executable)):
            if base:
                bundled = os.path.join(base, name)
                if os.path.isfile(bundled):
                    return bundled
    return shutil.which('wit')


def find_file(root, name):
    for r, _, files in os.walk(root):
        if name in files:
            return os.path.join(r, name)
    return None


def read_disc_id(fst, image_path):
    boot = find_file(fst, 'boot.bin')
    id6 = None
    if boot:
        with open(boot, 'rb') as f:
            header = f.read(8)
        id6 = header[0:6].decode('ascii', 'replace')

    # Read revision from disc image header
    rev = 0
    try:
        with open(image_path, 'rb') as f:
            magic = f.read(4)
            if magic == b'WBFS':
                f.seek(0x207)
                rev = f.read(1)[0]
            else:
                f.seek(7)
                rev = f.read(1)[0]
    except Exception:
        pass
    return id6, rev


def run_patch(image_path, log, done, which=('cc', 'gc')):
    """Patch `image_path` in place. `which` names the features to apply."""
    try:
        wit = find_wit()
        if wit is None:
            raise RuntimeError('wit (Wiimms ISO Tool) not found: not bundled with this '
                               'build and not on PATH')
        which = [w for w in patcher.ORDER if w in which]
        if not which:
            raise RuntimeError('nothing selected: select at least one patch option')
        fmt = '--iso' if image_path.lower().endswith('.iso') else '--wbfs'

        with tempfile.TemporaryDirectory(prefix='spm_patch_') as tmp:
            fst = os.path.join(tmp, 'fst')
            log('extracting %s...' % os.path.basename(image_path))
            r = subprocess.run([wit, 'extract', image_path, '--dest', fst, '--psel', 'data',
                                '--overwrite', '-q'], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('extract failed:\n' + (r.stderr or r.stdout))

            dol_path = find_file(fst, 'main.dol')
            if not dol_path or os.path.basename(os.path.dirname(dol_path)) != 'sys':
                raise RuntimeError('could not find sys/main.dol in the extracted disc')
            dol = Dol(dol_path)

            region = patcher.detect_region(dol)
            if not region:
                disc_id, disc_ver = read_disc_id(fst, image_path)
                raise RuntimeError('%s v%d is not a Super Paper Mario release this patcher knows.\n\n'
                                   'Supported: %s' % (disc_id, disc_ver, ', '.join(
                                       '%s (%s)' % (k, v['short']) for k, v in REGIONS.items())))
            log('disc: %s (%s)' % (region, REGIONS[region]['label']))

            have = patcher.status(dol, region)
            todo = []
            for name in which:
                st = have.get(name)
                if st == 'patched':
                    log('%s is already in this disc, skipping' % features.TITLES[name])
                elif st == 'clean':
                    todo.append(name)
                else:
                    raise RuntimeError('the main.dol does not match the retail %s (%s) -- already modified '
                                       'by something else, or not an unmodified dump. Not patching it.'
                                       % (REGIONS[region]['label'], features.TITLES[name]))
            if not todo:
                raise RuntimeError('nothing left to add: the selected patches are already in this disc.')

            for t in patcher.patch(dol, region, todo):
                log('  added %s' % t)
            dol.save(dol_path)
            log('  patched main.dol')

            staged = os.path.join(tmp, 'patched.img')
            log('rebuilding...')
            cmd = [wit, 'copy', fst, '--dest', staged, fmt, '--overwrite', '-q']
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('rebuild failed:\n' + (r.stderr or r.stdout))

            bak = image_path + '.bak'
            if not os.path.exists(bak):
                log('saving original as %s...' % os.path.basename(bak))
                shutil.move(image_path, bak)
            else:
                log('leaving existing %s untouched' % os.path.basename(bak))
                os.remove(image_path)
            shutil.move(staged, image_path)
            log('done.')
            done(True, 'Successfully patched %s' % os.path.basename(image_path))
    except Exception as e:
        log('error: %s' % e)
        done(False, str(e))
