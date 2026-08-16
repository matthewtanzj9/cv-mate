"""Unit tests for ScaleRange and the coarse-to-fine multi-scale search
(FR18) — this is the behavior that's an explicit improvement over Sikuli's
single-scale-only matching.
"""

from pathlib import Path

import cv2
import pytest

from cvmate.config import ScaleRange
from cvmate.matching import TemplateScaleMatcher
from cvmate.pattern import Pattern

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE_PATH = ASSETS / "templates" / "ok_button.png"
TRUE_SCALE = 0.9  # the scale the button was actually pasted in at, in the fixture


def test_scale_range_factors_are_linearly_spaced():
    scale_range = ScaleRange(0.8, 1.2, steps=5)
    assert scale_range.factors() == pytest.approx([0.8, 0.9, 1.0, 1.1, 1.2])


def test_single_scale_range_is_an_opt_out():
    scale_range = ScaleRange(1.0, 1.0, steps=1)
    assert scale_range.is_single_scale()
    assert scale_range.factors() == [1.0]


def test_coarse_has_fewer_or_equal_steps():
    scale_range = ScaleRange(0.5, 1.5, steps=11)
    coarse = scale_range.coarse()
    assert coarse.steps <= scale_range.steps
    assert coarse.min_scale == scale_range.min_scale
    assert coarse.max_scale == scale_range.max_scale


def test_narrowed_around_stays_within_bounds():
    scale_range = ScaleRange(0.5, 1.5, steps=11)
    narrowed = scale_range.narrowed_around(0.52, margin=0.1)  # near the lower edge

    assert narrowed.min_scale >= scale_range.min_scale
    assert narrowed.max_scale <= scale_range.max_scale
    assert narrowed.min_scale == scale_range.min_scale  # clamped, since 0.52-0.1 < 0.5


def test_invalid_scale_range_rejected():
    with pytest.raises(ValueError):
        ScaleRange(1.2, 0.8)  # min > max
    with pytest.raises(ValueError):
        ScaleRange(0.8, 1.2, steps=0)


def test_coarse_to_fine_recovers_the_true_scale():
    haystack = cv2.imread(str(ASSETS / "screenshots" / "button_present.png"), cv2.IMREAD_COLOR)
    pattern = Pattern(TEMPLATE_PATH, threshold=0.7, scales=(0.5, 1.5), scale_steps=11)
    matcher = TemplateScaleMatcher(coarse_to_fine=True)

    result = matcher.find_best(haystack, pattern)

    assert result is not None
    assert abs(result.scale - TRUE_SCALE) < 0.1


def test_coarse_to_fine_matches_exhaustive_search_quality():
    haystack = cv2.imread(str(ASSETS / "screenshots" / "button_present.png"), cv2.IMREAD_COLOR)
    pattern = Pattern(TEMPLATE_PATH, threshold=0.7, scales=(0.5, 1.5), scale_steps=11)

    coarse_to_fine = TemplateScaleMatcher(coarse_to_fine=True).find_best(haystack, pattern)
    exhaustive = TemplateScaleMatcher(coarse_to_fine=False).find_best(haystack, pattern)

    assert coarse_to_fine is not None and exhaustive is not None
    # Coarse-to-fine should be within a small margin of the fully exhaustive
    # sweep's confidence, not just "found something".
    assert coarse_to_fine.confidence >= exhaustive.confidence - 0.02
