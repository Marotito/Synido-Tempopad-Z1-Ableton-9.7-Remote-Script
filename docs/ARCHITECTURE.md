# Architecture

*[Versión en español](ARCHITECTURE.es.md)*

How the script is put together, and — more usefully — the `_Framework`
gotchas that cost us time. Every one of these was found the hard way.

---

## Files

```
Z1_Grid/
  __init__.py     entry point Live looks for (create_instance)
  Z1_Grid.py      the control surface
  paleta.py       colour tables and helpers
```

`paleta.py` holds Ableton's `RGB_COLOR_TABLE` and `CLIP_COLOR_TABLE`
(extracted from `Launchpad_MK2/Colors.py`), plus the hue families and a
`velocity_de_clip()` helper with nearest-colour fallback for custom clip
colours.

## Component layout

```
ControlSurface
├── ButtonMatrixElement  8×8      all pads, ch 3, notes 36–99
│     ├── scene matrix   8×1      column 1, rebuilt as a ROW (see below)
│     └── submatrix[1:, :] 7×8    the rest, for BackgroundComponent
├── 7 × ButtonElement               side buttons, notes 100–107
├── SessionComponent (is_enabled=False, layer=navigation)
├── BackgroundComponent (is_enabled=False, layer=rest of grid)
└── ModesComponent
      ├── 'sesion'   → SessionComponent + clip_launch_buttons
      └── 'escenas'  → SessionComponent + scene_launch_buttons + Background
```

Mode switching is handled by `ModesComponent`. The shift button's latching
behaviour is ours; everything after that — grabbing and releasing controls —
is the framework's `Layer` resource system. Adding a mixer layer later means
adding an `add_mode` call, not touching existing code.

---

## Framework gotchas

These are the ones that actually bit us. If you're writing a Live 9 remote
script, this section may be the most useful thing in the repo.

### `set_stopped_value()` silently disables RGB mode

```python
def set_clip_palette(self, palette):
    self._stopped_value = None       # ← the None is what enables colour mode
    self._clip_palette = palette

def set_stopped_value(self, value):
    self._stopped_value = value
    self._clip_palette = []          # ← wipes the palette
```

`_feedback_value()` falls through to the clip's own colour only when
`_stopped_value is None`. So:

- Call `set_rgb_mode()` **first**
- Set `set_started_value` / `set_recording_value` / `set_triggered_*`
  **after** — those are separate fields and are safe
- **Never** call `set_stopped_value()` once RGB mode is on

No error, no warning — the clips just quietly stop showing their colour.

### `SessionComponent.update()` does not cascade to clip slots

Changing a `ClipSlotComponent` value and calling `session.update()` does
**not** repaint the pads. You have to call `update()` on the clip slot
components themselves.

This is why the software blink repaints per-slot, and why it only touches
the columns that actually have something queued rather than all 64.

### `set_scene_launch_buttons` wants a row, not a column

```python
assert not buttons or buttons.width() == self._num_scenes and buttons.height() == 1
```

Scene launch buttons must be an **8-wide, 1-tall** matrix — regardless of
how they're arranged physically. Our scene column is physically vertical,
but the matrix has to be built as a single row:

```python
column_0 = [rows[r][0] for r in range(8)]
scene_matrix = ButtonMatrixElement(rows=[column_0])
```

The Launchpad does the same with its physically-vertical side buttons.
Passing `submatrix[0:1, :]` gives a 1×8 and fails the assertion — and
because it fails *during* a mode change, it leaves controls half-assigned
and the device behaving erratically. Wrap mode switches in try/except and
fall back to a known mode.

### Components with a layer must start disabled

```python
assert layer is None or not is_enabled
```

Any component constructed with `layer=` must have `is_enabled=False`. The
mode enables it, and `_internal_on_enabled_changed` grabs the layer then.
That's the whole mechanism — no manual control assignment anywhere.

### `send_value` won't resend an identical value

Use `force=True` when you need a resend (for example after a hardware mode
change), or call `clear_send_cache()` first.

### `set_light()` with an int does not do what you expect

`ButtonElement.set_light(value)` treats its argument as a **skin colour
name**, looks it up, and on `SkinColorMissingError` falls back to a plain
on/off. Since this script has no skin, raw ints must go through
`send_value()`. The framework does this correctly itself:

```python
if in_range(value_to_send, 0, 128):
    button.send_value(value_to_send)
else:
    button.set_light(value_to_send)
```

### Optional imports must not be able to kill the script

An early version imported a diagnostic module at top level. When that file
was missing from a deploy, the whole script failed to load — and the symptom
was "nothing happens at all", which points nowhere. Guard optional imports:

```python
try:
    import contratos
except ImportError:
    contratos = None
```

---

## Software blink

The Z-1 can't blink in hardware, so the queued state blinks via a framework
`Task`. Live calls `update_display()` every 100 ms and that's where tasks
tick, so 100 ms is the finest available grain.

```python
self._tasks.add(
    Task.repeat(
        Task.sequence(Task.wait(0.25),
                      Task.run(self._toggle_phase))))
```

Cost control:

- Before repainting, check `track.fired_slot_index` and `scene.is_triggered`.
  Nothing queued → return immediately. Idle cost is one cheap check per tick.
- When something *is* queued, repaint only the columns that have a queued
  clip. 8 slot updates per phase, not 64.
- When the queue clears, leave the colour **on**, not off.

Measured: no observable CPU change on a 2012 MacBook Pro i5.

---

## Testing approach

Live remote scripts can't be unit tested directly — but the `_Framework`
modules can be decompiled (`uncompyle6`) and the parts that matter can be
stubbed. The blink logic was validated against Ableton's **real** `Task.py`
with a simulated Live, before ever reaching hardware.

Two things worth copying:

- **Write in syntax valid in both Python 2.7 and 3.** Live 9 runs Python
  2.7, but if you avoid `except X, e` and friends you can syntax-check with
  python3 on any machine. Catches a whole class of deploy-and-pray errors.
- **Verify method contracts before writing against them.** Nearly every bug
  in this project came from assuming what a framework method did instead of
  reading it. The assertions that broke us were sitting in plain sight in
  source we already had.

---

## Deployment

Live 9 has no User Library support for remote scripts (Live 10.1.13+ only),
so the script lives inside the app bundle and is lost on reinstall. Keep the
source under version control elsewhere and treat the bundle as a deploy
target. `tools/deploy.sh` does that, plus a version-stamped backup of the
factory scripts and clearing stale `.pyc` files — Live compiles on launch,
and a stale `.pyc` means debugging code that no longer exists.
