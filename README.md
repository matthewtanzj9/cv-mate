# cv-mate

A general-purpose, OpenCV-based gameplay automation framework: detect
on-screen visual patterns and trigger mouse actions from a Sikuli-style
scripting API. Conceptually similar to [Sikuli](http://www.sikuli.org/), with
a few deliberate improvements — most notably multi-scale pattern matching
(Sikuli only matches at a single fixed scale) and a first-class debug mode.

> **v1 scope:** Windows 10/11 only, mouse automation only (no keyboard yet).
> See `requirements`/architecture discussion for the full rationale.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .[dev]
```

```python
from cvmate import Screen, Pattern

screen = Screen()
ok_button = Pattern("ok_button.png", threshold=0.85)

screen.wait_for_appear(ok_button, timeout=10.0).click()
```

Run it standalone — no extra runtime or GUI tooling required:

```bash
python examples/click_button.py
```

## Core concepts

- **`Screen`** — a `Region` scoped to a monitor (or the full virtual desktop
  across all monitors when constructed with no arguments).
- **`Region`** — a rectangular area you can capture, search within, and
  click into. `Screen` is a `Region`; so is a `Match`.
- **`Pattern`** — a template image plus its own match threshold and
  (optional) scale range, loaded from a local image-asset file or an
  in-memory array.
- **`Match`** — what `Region.find()` returns: a `Region` scoped to the
  matched bounding box, plus mouse-action helpers (`.click()`,
  `.double_click()`, `.right_click()`, `.drag_to()`, `.hover()`). Because a
  `Match` *is* a `Region`, you can search inside a match too:
  `screen.find(icon).find(sub_icon)`.

```python
from cvmate import Screen, Pattern

screen = Screen()

# One-shot check
if screen.exists(Pattern("enemy_marker.png")):
    ...

# Wait, with a timeout
screen.wait_for_appear(Pattern("loot.png"), timeout=15.0).click()

# Multiple candidates in one search
for match in screen.find_all(Pattern("coin.png")):
    match.click()

# A pattern that's known not to resize can opt out of the multi-scale sweep
fixed_ui = Pattern("hud_icon.png").with_scale_range(1.0, 1.0, steps=1)
```

## Multi-scale matching

By default, patterns are matched across a range of scale factors (a
scale-pyramid search, coarse-to-fine), so scripts stay robust to game window
resizing or different resolutions — unlike Sikuli, which only matches at the
exact size the template was captured at:

```python
# Search a wider range than the default (0.8x-1.2x) if the game window can
# be resized a lot, or narrow it (or opt out entirely) for a fixed-size HUD:
Pattern("icon.png", scales=(0.5, 2.0), scale_steps=9)
Pattern("hud_icon.png", scales=(1.0, 1.0), scale_steps=1)  # opt out
```

## Debug mode

Debug output is off by default and cheap to enable — set an environment
variable, no code changes required:

```bash
set CVMATE_DEBUG=1          # verbose match logging
set CVMATE_DEBUG_SAVE=1     # also save annotated screenshots of matches
set CVMATE_DEBUG_DIR=out    # where annotated screenshots are saved
```

Or per-script:

```python
from cvmate import Screen, DebugConfig

screen = Screen(debug=DebugConfig(enabled=True, save_annotated=True))
```

## Extensibility

Screen capture and mouse input each sit behind an abstract interface
(`CaptureBackend`, `InputController`), and pattern matching sits behind
`Matcher`. This is what lets:
- a future macOS/Linux backend be added without changing any script,
- a future keyboard-input feature be added additively, without touching
  existing mouse-only scripts,
- a future feature-based matcher (ORB/SIFT/AKAZE) be swapped in for
  `TemplateScaleMatcher` without touching `Pattern` or scripts.

## Testing

```bash
pytest tests/unit
```

Unit tests run fully offline against small, synthetic (non-copyrighted)
sample images checked into `tests/assets/` — no live screen or game
required. Tests exercising the real Windows capture/input backends live
under `tests/integration/` and are excluded from the default test run.

## Project layout

```
src/cvmate/       core library (capture, matching, input, scripting API)
tests/unit/       offline unit tests
tests/assets/     small synthetic images used by the unit tests
examples/         runnable example scripts
```
