# Contributing

*[Versión en español](CONTRIBUTING.es.md)*

This started as a personal project to make a cheap Launchpad-clone usable in
Live, and it works well enough to gig with. It's public because the hardware
findings are worth sharing and because there's plenty left to build.

Issues, ideas and PRs all welcome — including "this doesn't work on my
setup", which is useful data.

## Before you write code

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), especially the framework
gotchas. Most of them cost hours to find and they are not documented
anywhere else.

Two conventions that have earned their keep:

- **Write Python that parses as both 2.7 and 3.** Live 9 runs 2.7, but
  avoiding `except X, e` and `print` statements lets you syntax-check with
  python3 before deploying. Each deploy costs a Live restart; catching
  syntax errors locally is worth the small constraint.
- **Read the framework method before calling it.** The `_Framework` sources
  decompile cleanly with `uncompyle6`. Assertions in there are strict and
  fail in ways that leave the device in a broken half-state.

## Testing

There is no test harness for a live control surface, but you can get a long
way by decompiling `_Framework` and stubbing what you need. The software
blink was validated against Ableton's real `Task.py` with a simulated Live
before it ever touched hardware.

When reporting a bug, include `Log.txt`:

- macOS: `~/Library/Preferences/Ableton/Live 9.x/Log.txt`
- Windows: `%APPDATA%\Ableton\Live 9.x\Preferences\Log.txt`

Or `./tools/deploy.sh log` on macOS.

## Roadmap

### Session zoom
`SessionZoomingComponent` shows the whole set as 8×8 blocks — each pad is a
region you jump to. For a set organised as colour-coded song blocks, this
is effectively a song selector. Highest value/effort ratio of anything left.

### Per-track stop clip
`set_stop_track_clip_buttons` on a shift layer. The Launchpad carves a row
out of the main matrix with `submatrix[:, 4:5]`; same trick applies.

### Mixer mode
`MixerComponent` gives mute/solo/arm with zero custom code. Note that
`set_send_controls` expects **continuous** controls — it calls `connect_to`
on a parameter — so sends can't be driven from pads without writing LOM
code yourself.

### Live 10 / 11 port
The `_Framework` API changed. Someone with a Live 10+ install would need to
check the same method contracts documented in ARCHITECTURE.md.

### SysEx / direct RGB
The vendor editor stores colours as RGB triples, hinting the device may take
RGB over SysEx. If that works in real time it removes the 128-colour limit
entirely. Capture what the editor sends on "Send to Hardware" with MIDI
Monitor — that's the whole experiment.

### Other Launchpad clones
If your device also turns out to use the Launchpad palette, most of this is
reusable — change the note map and the channel. Reports from other hardware
are very welcome; `tools/z1_filas.py` and `tools/z1_parpadeo.py` will
characterise a new device in an afternoon.

## What this project won't do

- Ship a fork of Ableton's factory scripts. Reference them, don't vendor them.
- Add features that need hardware capabilities the Z-1 doesn't have.
  We tested; it doesn't blink. Work with that.
