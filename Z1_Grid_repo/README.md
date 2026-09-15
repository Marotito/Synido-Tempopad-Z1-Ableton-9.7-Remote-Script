# Z1_Grid — Synido TempoPAD Z-1 control surface script for Ableton Live 9

*[Versión en español](README.es.md)*

A MIDI Remote Script that turns the **Synido TempoPAD Z-1** into a proper
Session View clip launcher in Ableton Live 9, with real clip colours,
scene launching and a shift layer.

**Status: working MVP.** Daily-driver stable on Live 9.7 / macOS. Everything
described below is tested on hardware, not theoretical.

The Z-1 ships with no Live integration at all — the vendor only provides a
stock `UserConfiguration.txt` that maps three transport buttons. This script
replaces that with a real control surface.

---

## TL;DR for people who found this looking for Z-1 info

Even if you never use this script, [docs/HARDWARE.md](docs/HARDWARE.md)
is probably what you came for. Short version:

- **The Z-1 uses the Novation Launchpad colour palette, exactly.** Verified
  two independent ways. Ableton's own `Launchpad_MK2/Colors.py` tables work
  on it unmodified.
- **User Mode is MIDI channel 3.** Pads are notes 36–99, side buttons 100–107.
- **The 8×8 grid is not linearly numbered.** Columns 1–4 start at 36,
  columns 5–8 start at 68. Formula in the docs.
- **No blink or pulse.** All 16 MIDI channels tested; only channel 3 lights
  up, always solid. The Launchpad's channel-based blink/pulse trick does not
  work here.
- **The device clears its LEDs when you change hardware mode, and sends no
  MIDI about it.** Any script needs a manual refresh button.

---

## Features

- **8×8 clip grid** with real Live clip colours, using Ableton's official
  `CLIP_COLOR_TABLE` / `RGB_COLOR_TABLE`. All 60 Live clip colours map to 60
  distinct pad colours — no collisions.
- **Readable playback states.** Playing / queued / recording use velocities
  outside the range Live's clip palette uses (60–119), so a stopped clip can
  never look like a playing one.
- **Software blink for the queued state**, since the hardware can't do it.
  Costs nothing while idle: it only repaints the columns that actually have
  a queued clip.
- **Shift layer** (Record button, latching) — column 1 launches scenes with
  their real colours; the rest of the grid is blanked by a
  `BackgroundComponent` so stray notes don't leak into the armed MIDI track.
- **Track and scene navigation** on the side buttons, active in both layers,
  with Live's session ring following along.
- **Manual refresh** (Octave button) for when you switch the Z-1 back from
  Drum/Key/Custom mode.

## Requirements

- Ableton Live 9.2+ (developed and tested on 9.7)
- Synido TempoPAD Z-1
- macOS or Windows

## Install

Live 9 does **not** support remote scripts in the User Library — that only
arrived in Live 10.1.13. The script has to go inside the application bundle.

```
<Live>/Contents/App-Resources/MIDI Remote Scripts/Z1_Grid/
```

macOS users: `tools/deploy.sh` handles this, including backing up the stock
scripts first and clearing stale `.pyc` files. Run it from the machine that
runs Live.

```bash
chmod +x tools/deploy.sh
./tools/deploy.sh          # deploy
./tools/deploy.sh log      # tail Live's Log.txt
```

Backups go to `~/Z1_Grid_backups` by default. Override with
`--backup /some/path` or the `Z1_BACKUP_DIR` environment variable.

Then in Live: **Preferences → MIDI → Control Surface → Z1_Grid**, with the
Z-1 as both Input and Output. Put the hardware in **User Mode**.

> Back up the stock `MIDI Remote Scripts` folder before touching it. If you
> overwrite a factory script you will have to reinstall Live to get it back.
> `deploy.sh` does this for you.

## Layout

```
        ┌───────────────────────────────┐
        │                               │  ← Octave     refresh
        │                               │  ← Transpose  scenes up
        │        8 × 8 clip grid        │  ← Velocity   scenes down
        │                               │  ← Light      tracks left
        │   col 1 = scenes when Shift   │  ← MMC        tracks right
        │                               │  ← Stop       stop all clips
        │                               │  ← Play       (free)
        │                               │  ← Record     SHIFT (latching)
        └───────────────────────────────┘
```

| State | Velocity | Colour |
|---|---|---|
| Clip stopped | from clip | real Live clip colour |
| Clip playing | 53 | magenta |
| Clip queued | 13 | yellow, blinking |
| Recording | 56 | hot pink |
| Queued to record | 8 | pale orange |
| Empty slot | 0 | off |

Playback-state colours deliberately sit outside 60–119, the range Live's
clip palette occupies. That is why they can never be confused with a clip's
own colour. If you change them, keep them out of that range.

## Known limitations

- **No blink in hardware.** The queued-state blink is done in software by a
  framework `Task`. It is cheap but it is not free.
- **Manual refresh after a hardware mode change.** The Z-1 does not report
  mode changes over MIDI, so the script cannot know it needs to repaint.
- **One button per side function.** Only 8 side buttons, and 7 are taken.
- **Live 9 only, for now.** The `_Framework` API shifted in Live 10/11.
  Ports welcome.

## Roadmap

See [CONTRIBUTING.md](CONTRIBUTING.md). Short list:

- Session zoom (whole-set overview as a song selector)
- Per-track stop clip on a shift layer
- Mixer mode (mute / solo / arm)
- Live 10 / 11 port

## Docs

- [docs/HARDWARE.md](docs/HARDWARE.md) ([es](docs/HARDWARE.es.md)) — everything we measured about the
  Z-1: note map, palette, channels, what it can't do
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ([es](docs/ARCHITECTURE.es.md)) — how the script is built and
  the framework gotchas that cost us time
- [CONTRIBUTING.md](CONTRIBUTING.md) ([es](CONTRIBUTING.es.md)) — roadmap and how to help

## Tools

`tools/` contains the standalone measurement scripts used to characterise
the hardware. They run outside Live and need `mido` + `python-rtmidi`. They
are included because they are how the hardware findings were produced, and
because they are useful for any other Launchpad-like clone:

- `z1_filas.py` — sweep all 127 velocities, one row per photo, with a
  binary pass label so photos are self-identifying
- `z1_parpadeo.py` — probe all 16 MIDI channels for blink/pulse support
- `z1_colores.py` — earlier checkerboard sweep (superseded, kept for reference)

## Credits

Project conceived and directed by **Marote**, who did all hardware testing
and measurement, decompiled Live's `_Framework` and the factory Launchpad
scripts for reference, made the design calls (channel layout, shift model,
colour scheme), and caught several bugs in testing.

Code and technical analysis by **Claude** (Anthropic), working from those
measurements and decisions.

The colour tables come from Ableton's own `Launchpad_MK2/Colors.py`, which
turned out to apply to this device unchanged.

## Licence

MIT. See [LICENSE](LICENSE).

Not affiliated with Synido, Ableton or Novation.
