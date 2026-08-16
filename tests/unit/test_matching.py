"""Offline unit tests for TemplateScaleMatcher against checked-in sample
images (NFR7) — no live screen/game required.
"""

from pathlib import Path

import cv2

from cvmate.matching import TemplateScaleMatcher
from cvmate.pattern import Pattern

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE_PATH = ASSETS / "templates" / "ok_button.png"

# The template was pasted into button_present.png at (120, 80) at 90% scale.
KNOWN_X, KNOWN_Y, KNOWN_SCALE = 120, 80, 0.9


def _load(name: str) -> "cv2.typing.MatLike":
    image = cv2.imread(str(ASSETS / "screenshots" / name), cv2.IMREAD_COLOR)
    assert image is not None, f"missing test fixture: {name}"
    return image


def test_find_best_locates_present_button():
    pattern = Pattern(TEMPLATE_PATH, threshold=0.8)
    haystack = _load("button_present.png")

    result = TemplateScaleMatcher().find_best(haystack, pattern)

    assert result is not None
    assert result.confidence >= pattern.threshold
    assert abs(result.x - KNOWN_X) <= 3
    assert abs(result.y - KNOWN_Y) <= 3


def test_find_best_returns_none_when_absent():
    pattern = Pattern(TEMPLATE_PATH, threshold=0.8)
    haystack = _load("button_absent.png")

    result = TemplateScaleMatcher().find_best(haystack, pattern)

    assert result is None


def test_find_all_finds_the_single_instance():
    pattern = Pattern(TEMPLATE_PATH, threshold=0.8)
    haystack = _load("button_present.png")

    results = TemplateScaleMatcher().find_all(haystack, pattern, max_results=5)

    assert len(results) == 1
    assert results[0].confidence >= pattern.threshold


def test_pattern_scale_opt_out_still_matches_at_native_scale():
    # Opting out of the sweep (scales=(1,1)) should still find a match when
    # searched at native template scale, just with a lower confidence peak
    # than the true 0.9x scale would give.
    haystack = _load("button_present.png")
    single_scale_pattern = Pattern(TEMPLATE_PATH, threshold=0.5, scales=(1.0, 1.0), scale_steps=1)

    result = TemplateScaleMatcher().find_best(haystack, single_scale_pattern)

    assert result is not None
    assert result.scale == 1.0
