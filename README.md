# Super Paper Mario Patch

Play **Super Paper Mario** (Wii) with a **GameCube controller** or a **Classic Controller**! Works across all four regional releases: USA Rev 2 (`R8PE01`), Europe Rev 1 (`R8PP01`), Japan Rev 1 (`R8PJ01`), and Korea (`R8PK01`).

The patches are applied directly to your own clean disc image (`.wbfs` or `.iso`): drop your copy onto the patcher window and play the result on a Wii (USB loader) or in Dolphin. Nothing copyrighted from the game is distributed in this repository.

![Super Paper Mario](assets/logo.png)

## Highlights

- **GameCube Controller Support**: Native port 1 GameCube controller support via hardware Serial Interface (SI) auto-polling and extension report synthesis. Works seamlessly with or without a connected Wii Remote!
- **Classic Controller Support**: Built-in integration of Vague Rant and crediar's acclaimed Classic Controller patch.
- **Full Analog Controls**:
  - Control stick (or CC left stick): Character movement and crouching.
  - C-stick (or CC right stick): Smooth Tippi pointer aiming.
  - Dedicated pointer toggle: Press **L** (or CC L/ZL) to toggle Tippi pointer mode on and off cleanly without holding buttons!
- **All 4 Regional Releases Supported**:
  - `R8PE01`: *Super Paper Mario* (USA Rev 2)
  - `R8PP01`: *Super Paper Mario* (Europe Rev 1)
  - `R8PJ01`: *Super Paper Mario* (Japan Rev 1)
  - `R8PK01`: *Super Paper Mario* (Korea)

---

## Controls

### GameCube Controller

| Action | Button | Game Function / Wiimote Equivalent |
| --- | --- | --- |
| **Move / Duck** | **Control Stick / D-Pad** | D-Pad |
| **Aim Tippi Pointer** | **C-Stick** (or Control Stick in pointer mode) | Pointer |
| **Jump / Confirm** | **A** | Button 2 |
| **Pixl Ability / Cancel** | **B** | Button 1 |
| **Flip 2D / 3D** | **Y** (or R) | Button A |
| **Quick Menu** | **X** | Button 1 + 2 |
| **Toggle Pointer Mode** | **L** | Toggle Pointer Mode |
| **Inspect / Flip** | **R** | Button A |
| **Pause Menu (+)** | **Start** | Plus (+) |
| **Controls / Character (-)** | **Z** | Minus (-) |

*Note: GameCube controller connects to GameCube Port 1.*

### Classic Controller

| Action | Button | Game Function / Wiimote Equivalent |
| --- | --- | --- |
| **Move / Duck** | **Left Stick / D-Pad** | D-Pad |
| **Aim Tippi Pointer** | **Right Stick** (or Left Stick in pointer mode) | Pointer |
| **Jump / Confirm** | **A** | Button 2 |
| **Pixl Ability / Cancel** | **B** | Button 1 |
| **Flip 2D / 3D** | **Y** (or R / ZR) | Button A |
| **Quick Menu** | **X** | Button 1 + 2 |
| **Toggle Pointer Mode** | **L / ZL** | Toggle Pointer Mode |
| **Inspect / Flip** | **R / ZR** | Button A |
| **Pause Menu (+)** | **+** | Plus (+) |
| **Controls / Character (-)** | **-** | Minus (-) |

---

## Installing & Patching

### Graphical Patcher (GUI)

Download the standalone GUI patcher from the [Releases](https://github.com/quatric/Super-Paper-Mario-Patch/releases) page (available for macOS, Windows, and Linux), or run it from source:

```bash
python3 tools/gui.py
```

1. Choose which controllers you want enabled (**Classic Controller** and/or **GameCube controller**).
2. Drop your clean `.wbfs` or `.iso` file onto the application window (or click to browse).
3. The patcher validates your disc against retail checksums, injects the routines into `sys/main.dol`, rebuilds the image in place, and preserves your untouched original as `<filename>.bak`.

### Command-Line Patcher (CLI)

Patch a disc image directly from the terminal:

```bash
python3 tools/patch_disc.py "Super Paper Mario.wbfs" --cc --gc
```

Or patch an extracted `main.dol` file directly:

```bash
python3 tools/patcher.py main.dol main_patched.dol --cc --gc
```

### Gecko Codes (Dolphin)

Pre-generated Gecko codes for each game ID are located in the `codes/` directory:
- `R8PE01.ini` / `R8PE01.txt` (USA Rev 2)
- `R8PP01.ini` / `R8PP01.txt` (Europe Rev 1)
- `R8PJ01.ini` / `R8PJ01.txt` (Japan Rev 1)
- `R8PK01.ini` / `R8PK01.txt` (Korea)

Copy the `.ini` file into Dolphin's `Sys/GameSettings/` or your user `GameSettings/` folder.

### Riivolution

XML patches are provided in `riivolution/`:
- `R8PE01.xml`
- `R8PP01.xml`
- `R8PJ01.xml`
- `R8PK01.xml`

Place the XML file in `/riivolution/` on your SD card or USB drive.

---

## Credits & Acknowledgments

- **Vague Rant & crediar**: Original Classic Controller Gecko code implementations.
- **quatric**: GameCube SI hardware polling bridge, Classic Controller synthesis engine, patcher tools, Riivolution patches, and multi-region porting.
- **Intelligent Systems & Nintendo**: *Super Paper Mario*.

## License

This project is licensed under the [MIT License](LICENSE).

### Modded images

The disc patcher identifies the executable from its patch sites, so mods with the same ID4 are supported even when the last two ID characters change. The original disc ID and filename are preserved. Mods that change required patch sites may be incompatible.
