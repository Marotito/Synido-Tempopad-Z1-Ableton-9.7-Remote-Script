# Synido TempoPAD Z-1 — hardware reference

*[Versión en español](HARDWARE.es.md)*

Everything here was measured on real hardware or read from Ableton's own
decompiled scripts. Where something is inferred rather than verified, it
says so.

If you are writing your own script for this device, or for another
Launchpad-like clone, this is the part worth reading.

---

## 1. Modes and MIDI channels

The Z-1 has five hardware modes, selected by buttons above the grid. The
channel each mode transmits on is **fixed in firmware** — only Custom Mode
lets you change it.

| Mode | Channel | Notes | Editable? |
|---|---|---|---|
| Drum | 1 | 36–99 | no |
| Key | 1 | 36–84 (C2–C6) | no |
| **User** | **3** | **36–99 + 100–107** | no |
| Custom | 1 default | 36–99, note/CC/PC per pad | yes, 1–16 |
| Easy | — | standalone audio/light mode | — |

**User Mode is the one to target.** It is the only mode where the device
accepts incoming MIDI to drive its LEDs.

Because Drum and Key both sit on channel 1 with overlapping note ranges,
Live cannot tell them apart. If you want a drum layer and a melodic layer
armed at the same time, configure **Custom Mode on channel 2** with the
vendor editor and use that instead of Drum Mode.

## 2. Grid note map — not linear

This trips up everyone. The 8×8 grid is **two blocks of four columns**:

- Columns 1–4 are notes 36–67
- Columns 5–8 are notes 68–99

```python
def note_of(column, row):        # row 0 = top row
    return 36 + 32 * (column // 4) + (7 - row) * 4 + (column % 4)
```

Inverse:

```python
def pad_of(note):                # returns (column, row), row 0 = top
    d = note - 36
    return (4 * (d // 32) + (d % 32) % 4,
            7 - (d % 32) // 4)
```

Corners, to sanity-check any implementation:

```
top-left  64      top-right  99
bot-left  36      bot-right  71
```

## 3. Side buttons

The eight buttons down the right edge send **notes 100–107 on channel 3**,
momentary (127 on press, 0 on release), top to bottom:

| Note | Legend |
|---|---|
| 100 | Octave |
| 101 | Transpose |
| 102 | Velocity |
| 103 | Light |
| 104 | MMC |
| 105 | Stop |
| 106 | Play |
| 107 | Record |

The manual's feature table marks these as non-functional in User Mode, and
in terms of their *labelled* function that is true — Stop/Play/Record do not
drive transport. But they do transmit notes on channel 3, so a script can
map them to anything.

**They have the full RGB palette**, same as the pads. Initially they looked
like they only did red/green/white; that was the framework's default
feedback values, not a hardware limit.

The buttons across the top (mode selectors, arrows) send **nothing**.

## 4. Colour palette — it's the Launchpad palette

**The Z-1 replicates the Novation Launchpad RGB palette exactly.**

Verified two independent ways:

1. **Photographed on hardware.** All 127 velocities swept, one row of 8 per
   photo, with a white anchor pad for camera white-balance correction and a
   binary pass label so each photo identified itself.
2. **Against Ableton's own tables.** `Launchpad_MK2/Colors.py` in Live 9.7
   contains `RGB_COLOR_TABLE`, 128 velocity→RGB pairs. It matched the
   photographic measurement on all 128 values.

Practical consequences:

- Ableton's `CLIP_COLOR_TABLE` maps Live's 60 clip colours straight onto
  this device. Use it — don't write your own nearest-colour matcher.
- `SessionComponent.set_rgb_mode(CLIP_COLOR_TABLE, RGB_COLOR_TABLE)` works
  as-is.
- The Launchpad's colour constants (`Rgb.GREEN` = 21, etc.) are valid here.

### Structure of the palette

- **0–3** — off, dark grey, grey, white
- **4–63** — 15 hue families of 4: `[pale, full, dark, dim]`.
  Red 4–7, orange 8–11, yellow 12–15, lime 16–19, greens 20–31,
  cyan 32–39, blue 40–47, violet 48–51, magenta 52–55, pink 56–59.
- **64–127** — unstructured extras. This is the range Live's clip palette
  actually uses.

**Live's clip palette only uses velocities 60–119.** Everything outside that
range is free for UI states and can never be confused with a clip colour.
That is the single most useful fact in this document if you're designing
feedback.

The 4-value families in 4–63 are useful for a "colour family per song,
shade per function" scheme — but be warned that `dark` and `dim` are very
low brightness and hard to read under stage lighting.

## 5. Things the Z-1 cannot do

### No blink, no pulse

The Launchpad asks its hardware to blink or pulse by sending the note on a
different MIDI channel (`BLINK_LED_CHANNEL = 1`, `PULSE_LED_CHANNEL = 2` in
`Launchpad_MK2/consts.py`). That's why Ableton can use plain green for both
"stopped green clip" and "playing" — the motion carries the distinction, not
the hue.

**The Z-1 does not implement this.** All 16 MIDI channels were probed
(`tools/z1_parpadeo.py`): only channel 3 lights anything, and always solid.

Consequences: either pick state colours that can't collide with clip
colours, or blink in software. This script does both — distinct colours for
playing/recording, software blink for queued.

### LEDs clear on mode change, silently

Switching the Z-1 to Drum/Key/Custom and back to User leaves every LED off.
**The device sends no MIDI when the mode changes**, so a script has no way
to know it should repaint.

There's no way around a manual refresh. Note that clearing the send cache is
required — the framework will not resend a value identical to the last one
it sent:

```python
matrix.clear_send_cache()
for button in side_buttons:
    button.clear_send_cache()
self.refresh_state()
```

### Velocity is fixed in User Mode

User Mode transmits full velocity regardless of how hard you hit. Fine for
clip launching, useless for playing. Use Drum or Custom Mode for that.

## 6. Power

Rated 2.5 W. At 5 V that's ~500 mA — the entire budget of a USB 2.0 port.
The device has a separate USB-C power input; **use it**, especially
alongside a bus-powered audio interface. This was a real problem on the
development machine (2012 MacBook Pro with a bus-powered Mbox 2).

## 7. Vendor editor

The Synido editor requires **macOS 10.14+**. It won't run on older systems,
which matters if you're running Live 9 on an older OS. Settings are written
to the device, so you can configure on a newer machine and use on an older
one.

The editor's config files store colours as **RGB triples**, not velocity
indices — suggesting the device may accept RGB over SysEx for Custom Mode
configuration. **Not investigated.** If real-time RGB over SysEx works, it
would remove the 128-colour limit entirely. Good first contribution: capture
what the editor sends on "Send to Hardware".

## 8. Reproducing the measurements

`tools/z1_filas.py` is the measurement rig. It lights the top row with 8
consecutive velocities and encodes the pass number in binary on the bottom
row, so each photo identifies itself and nothing depends on shooting order.

```bash
pip3 install mido python-rtmidi
python3 tools/z1_filas.py plan                   # print all 16 passes
python3 tools/z1_filas.py ports
python3 tools/z1_filas.py fila 1 --port "TempoPAD"
```

Shoot at low ISO. Overexposed LED centres clip to white and destroy the hue
— that ruined the first attempt.
