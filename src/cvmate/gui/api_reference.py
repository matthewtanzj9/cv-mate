"""Static content for the GUI's built-in API reference panel.

Kept as a plain string-returning function (no Qt import at all) so its
content is trivially unit-testable without a QApplication/display.
"""

from __future__ import annotations

_STYLE = """
<style>
  body { font-family: sans-serif; font-size: 9pt; }
  h2 { font-size: 11pt; margin-top: 14px; margin-bottom: 4px; border-bottom: 1px solid #888; }
  h3 { font-size: 10pt; margin-top: 10px; margin-bottom: 2px; }
  code, .sig { font-family: Consolas, monospace; font-size: 8.5pt; }
  .sig { display: block; margin: 2px 0 2px 8px; }
  ul { margin: 2px 0 8px 0; padding-left: 18px; }
  li { margin-bottom: 3px; }
  .ret { color: #666; }
</style>
"""


def render_api_reference_html() -> str:
    """The full HTML content shown in the "API Reference" dock panel."""
    return _STYLE + """
<h2>Screen</h2>
<span class="sig">Screen(monitor: int | None = None, **kwargs)</span>
<ul>
  <li>A <code>Region</code> scoped to a monitor, or the whole virtual desktop if <code>monitor=None</code>.</li>
  <li><code>Screen.list_monitors()</code> <span class="ret">→ list[MonitorInfo]</span> (staticmethod)</li>
</ul>

<h2>Region</h2>
<span class="sig">Region(x, y, width, height, *, capture=None, matcher=None, input_controller=None, debug=None)</span>
<ul>
  <li><code>.find(pattern)</code> <span class="ret">→ Match</span> — raises <code>PatternNotFoundError</code></li>
  <li><code>.find_all(pattern, max_results=10)</code> <span class="ret">→ list[Match]</span></li>
  <li><code>.exists(pattern)</code> <span class="ret">→ bool</span> — single-shot, no wait</li>
  <li><code>.wait_for_appear(pattern, timeout=10.0, poll_interval=0.5)</code> <span class="ret">→ Match</span> — raises <code>CvMateTimeoutError</code></li>
  <li><code>.wait_for_vanish(pattern, timeout=10.0, poll_interval=0.5)</code> <span class="ret">→ None</span> — raises <code>CvMateTimeoutError</code></li>
  <li><code>.capture_image()</code> <span class="ret">→ np.ndarray</span> (BGR)</li>
  <li><code>.sub_region(x, y, width, height)</code> <span class="ret">→ Region</span> — local coordinates</li>
  <li><code>.click(x, y, **kwargs)</code> / <code>.move_to(x, y)</code> <span class="ret">→ Region</span> — bare-point actions</li>
</ul>

<h2>Match (Region)</h2>
<div>What <code>.find()</code> / <code>.find_all()</code> return — everything <code>Region</code> has, plus:</div>
<ul>
  <li><code>.click(*, button="left", clicks=1, offset=(0,0))</code> <span class="ret">→ Match</span></li>
  <li><code>.double_click()</code> / <code>.right_click()</code> <span class="ret">→ Match</span></li>
  <li><code>.drag_to(target, *, button="left")</code> <span class="ret">→ Match</span></li>
  <li><code>.hover()</code> <span class="ret">→ Match</span></li>
  <li><code>.center</code> <span class="ret">→ (x, y)</span>, <code>.confidence</code> <span class="ret">→ float</span>, <code>.result</code> <span class="ret">→ MatchResult</span></li>
</ul>
<div>Since <code>Match</code> <i>is</i> a <code>Region</code>, chain further searches: <code>screen.find(icon).find(sub_icon)</code></div>

<h2>Pattern</h2>
<span class="sig">Pattern(image, *, threshold=0.8, scales=None, scale_steps=None, asset_folder=None)</span>
<ul>
  <li><code>image</code> can be a filename, a <code>Path</code>, or an in-memory <code>np.ndarray</code></li>
  <li><code>Pattern.from_asset(filename, **kwargs)</code> — alternate constructor</li>
  <li><code>.similar(threshold)</code> <span class="ret">→ Pattern</span></li>
  <li><code>.with_scale_range(min_scale, max_scale, steps=None)</code> <span class="ret">→ Pattern</span> — <code>(1.0, 1.0, steps=1)</code> opts out of the multi-scale sweep</li>
  <li><code>.image</code> <span class="ret">→ np.ndarray</span> (lazy-loaded), <code>.name</code> <span class="ret">→ str</span></li>
</ul>

<h2>Config</h2>
<span class="sig">DebugConfig(enabled=False, save_annotated=False, annotated_output_dir=Path("./cvmate_debug"))</span>
<ul>
  <li><code>DebugConfig.from_env()</code> — reads <code>CVMATE_DEBUG</code>, <code>CVMATE_DEBUG_SAVE</code>, <code>CVMATE_DEBUG_DIR</code></li>
</ul>
<span class="sig">ScaleRange(min_scale=0.8, max_scale=1.2, steps=5)</span>
<div>Rarely constructed directly — usually via <code>Pattern(scales=..., scale_steps=...)</code>.</div>

<h2>MatchResult</h2>
<div>Frozen dataclass: <code>x, y, width, height, confidence, scale, pattern</code>, plus <code>.center</code>.</div>

<h2>Exceptions</h2>
<div>All inherit <code>CvMateError</code>:</div>
<ul>
  <li><code>PatternNotFoundError</code> — from <code>.find()</code></li>
  <li><code>CvMateTimeoutError</code> — from <code>.wait_for_appear()</code> / <code>.wait_for_vanish()</code></li>
  <li><code>InvalidRegionError</code> — bad geometry on construction</li>
  <li><code>AssetNotFoundError</code> — image file missing/undecodable</li>
</ul>

<h2>Quick example</h2>
<pre class="sig">from cvmate import Screen, Pattern

screen = Screen()
ok_button = Pattern("images/ok_button.png", threshold=0.85)
screen.wait_for_appear(ok_button, timeout=10.0).click()</pre>
"""
