# Technical Architecture & Implementation Details

This document explains how the Classic Controller and GameCube controller patches operate in *Super Paper Mario*, where they hook into the game's executable, and how a unified operational definition compiles into static DOL patches, Gecko codes, and Riivolution XML files.

---

## 1. Unified Operation Pipeline

Every patch is modeled as a sequence of atomic operations against the game's `main.dol`:

| Operation | Static DOL (`main.dol`) | Gecko Code (`codes/`) | Riivolution (`riivolution/`) |
| --- | --- | --- | --- |
| **Patch** | Overwrite bytes in-place | `04` / `06` code | `<memory value="..." offset="..." />` |
| **Hook** | Branch to injected trampoline section (`0x80001820`), execute displaced instruction, branch back | `C2` code | `<memory>` (branch + trampoline bytes) |

- **Idempotent and Verified**: `tools/prebuilt/<feature>_<region>.json` encodes the expected pristine retail bytes for every site. `tools/patcher.py` verifies these bytes before writing, preventing corruption of already-modified or foreign DOL files.
- **Self-Contained Trampolines**: All hook trampolines carry their required logic or resolve external SDK symbols through absolute addresses.
- **Section Injection**: For static DOL patching, an additional text section is allocated at `0x80001820` (the Wii's boot-time scratch area, which is unused after kernel boot). The section size is padded to a 32-byte boundary to satisfy strict Wii DOL loader alignment.

---

## 2. Low-Memory Layout

```
0x80001820 - 0x80002000 : Classic Controller Hook Trampolines (CC_BASE .. CC_END)
0x80002000 - 0x80002A00 : GameCube Controller Bridge Trampolines (GC_BASE .. GC_END)
0x80003000              : CAVE_LIMIT (End of safe scratch RAM)
...
0x80005D40 - 0x80005D50 : GC Bridge State Struct (STATE: in Section 0 zero-padding)
```

The GameCube bridge maintains a 16-byte state struct at `0x80005D40` (verified zero-padding in Section 0 text across every game build):
```c
struct GcState {
    u32 initialized;
    u32 counter;
    u32 last_buttons;
    u32 connected;
};
```

---

## 3. Classic Controller Hook Engine

Vague Rant & crediar's Classic Controller patch hooks into the game's controller input processing pipeline:

1. **HBM Timer Hook** (`04` Patch):
   Prevents timeout disconnects during the Home Button menu when using Classic Controller.
2. **Pointer Hook** (`C2` Hook):
   Intercepts Tippi pointer handling. Translates Classic Controller right stick deflection and L-trigger toggles into onscreen pointer coordinates.
3. **Stick Hook** (`C2` Hook):
   Translates Classic Controller left analog stick movement into directional inputs for Mario and other playable characters.
4. **Button Hook** (`C2` Hook):
   Remaps Classic Controller buttons directly to Super Paper Mario actions (A = Jump/Confirm, B = Pixl/Cancel, Y = Flip 2D/3D, X = Quick Menu, L = Pointer toggle, R = Inspect).

---

## 4. GameCube Controller Bridge

Rather than writing a separate driver from scratch, the GameCube controller support acts as an **SI-to-Classic-Controller synthesis bridge**. It hooks three strategic points in the Revolution SDK:

### A. SI Auto-Polling & Hotplug Recovery (`HOOK_POLL` @ `KPADiRead`)
- Reads the hardware Serial Interface (SI) result registers at `SIC0INBUFH` (`0xCD006404`).
- Handles SI communication errors: If the `NOREP` (no response) latch is set, it checks whether SI auto-polling needs to be re-armed, restores the shadow registers, and triggers a clean rescan.
- Supports runtime hotplugging of the controller in port 1.

### B. Classic Controller Report Synthesizer (`HOOK_SAMPLE` @ `sample_site`)
- Located just before `KPADiRead`'s sample count check (`lbz r0, 0x10f(r31)`).
- When channel 0 is read and a GameCube controller is detected in port 1:
  - Synthesizes a valid `WPAD_EXP_CLASSIC` data packet directly into the `KPADUnifiedWpad` sample structure.
  - Maps GameCube Control Stick -> Classic Controller Left Stick (`cl.lstick_x`, `cl.lstick_y`).
  - Maps GameCube C-Stick -> Classic Controller Right Stick (`cl.rstick_x`, `cl.rstick_y`).
  - Maps GameCube digital buttons (A, B, X, Y, L, R, Z, Start, D-Pad) to matching Classic Controller button masks.
  - Sets sample format to `WPAD_FMT_EXP` (format 3) and sample count to 1, ensuring the game processes the synthesized sample immediately.

### C. WPADProbe Expansion Spoofing (`HOOK_PROBE` @ `WPADProbe`)
- Intercepts `WPADProbe(chan, &type)`.
- If channel 0 is probed and a GameCube controller is active, it writes `WPAD_DEV_CLASSIC` (type 2) into `*type` and returns `WPAD_ERR_NONE` (0).
- This allows playing with a GameCube controller even when **no Wii Remote is connected or synced to the console**!

---

## 5. Regional Address Table

Hook sites across the supported executables. USA, Japan and Europe each shipped revisions; USA Rev 0/1/2 and Japan Rev 0/1 each have a different `main.dol`, while Europe Rev 0 and Rev 1 ship a byte-identical one and share a column. Each patch set is keyed by the name in the header (`R8PE01r1` etc.), which is also the Dolphin `GameSettings` file name.

`src/relocate_cc.py` derives every non-USA-Rev-2 Classic Controller code from the USA Rev 2 reference, and `src/gcpad/anchors.py` does the same for the GameCube bridge, so adding a revision means dropping in its `main.dol` and running `tools/gen_prebuilt.py`.

| Symbol / Hook Site | USA Rev 0 (`R8PE01r0`) | USA Rev 1 (`R8PE01r1`) | USA Rev 2 (`R8PE01r2`) | Europe Rev 0/1 (`R8PP01`) | Japan Rev 0 (`R8PJ01r0`) | Japan Rev 1 (`R8PJ01r1`) | Korea (`R8PK01`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CC HBM Timer** | `0x80311980` | `0x803124A8` | `0x80312630` | `0x803146E0` | `0x80311930` | `0x80312294` | `0x803264BC` |
| **CC Pointer Hook** | `0x802DDD98` | `0x802DEA34` | `0x802DEAD4` | `0x802E0B84` | `0x802DDD48` | `0x802DE820` | `0x802E786C` |
| **CC Stick Hook** | `0x802DE6C8` | `0x802DF364` | `0x802DF404` | `0x802E14B4` | `0x802DE678` | `0x802DF150` | `0x802E819C` |
| **CC Button Hook** | `0x802DEDB0` | `0x802DFA54` | `0x802DFAF4` | `0x802E1BA4` | `0x802DED60` | `0x802DF840` | `0x802E88A0` |
| **Read Function (HOOK_POLL)** | `0x802DE7B4` | `0x802DF450` | `0x802DF4F0` | `0x802E15A0` | `0x802DE764` | `0x802DF23C` | `0x802E8288` |
| **Sample Check (HOOK_SAMPLE)** | `0x802DE8B8` | `0x802DF554` | `0x802DF5F4` | `0x802E16A4` | `0x802DE868` | `0x802DF340` | `0x802E83A0` |
| **WPADProbe (HOOK_PROBE)** | `0x802CE208` | `0x802CE7F0` | `0x802CE890` | `0x802D0940` | `0x802CE1B8` | `0x802CE554` | `0x802D6590` |
| **SIGetType** | `0x8026ACA0` | `0x8026B3A0` | `0x8026B440` | `0x8026D4F0` | `0x8026AC50` | `0x8026B300` | `0x8026F800` |
| **SiTypes** | `0x804A6D68` | `0x804A83F0` | `0x804A8580` | `0x804E9B98` | `0x8047C008` | `0x8047D470` | `0x8051E348` |
| **SiBusy** | `0x804A6D50` | `0x804A83D8` | `0x804A8568` | `0x804E9B80` | `0x8047BFF0` | `0x8047D458` | `0x8051E330` |
| **SiShadow** | `0x804A6D54` | `0x804A83DC` | `0x804A856C` | `0x804E9B84` | `0x8047BFF4` | `0x8047D45C` | `0x8051E334` |
| **WpadTbl** | `0x8055F550` | `0x80560DD0` | `0x80560F50` | `0x805A2550` | `0x80534850` | `0x80535E50` | `0x805CA850` |
| **OSDisableInterrupts** | `0x802716B8` | `0x80271D88` | `0x80271E28` | `0x80273ED8` | `0x80271668` | `0x80271CE8` | `0x802765F4` |
| **OSRestoreInterrupts** | `0x802716E0` | `0x80271DB0` | `0x80271E50` | `0x80273F00` | `0x80271690` | `0x80271D10` | `0x8027661C` |
| **STATE** | `0x80005D40` | `0x80005D40` | `0x80005D40` | `0x80005D40` | `0x80005D40` | `0x80005D40` | `0x80005D40` |
