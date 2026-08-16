"""Unit tests for Region/Match built on fake CaptureBackend/InputController
implementations — proving the extensibility ABCs (NFR5) let Region logic be
tested with zero OS dependency (NFR7).
"""

from pathlib import Path

import cv2
import pytest

from cvmate.capture import CaptureBackend, MonitorInfo
from cvmate.config import DebugConfig
from cvmate.exceptions import CvMateTimeoutError, InvalidRegionError, PatternNotFoundError
from cvmate.input import InputController
from cvmate.pattern import Pattern
from cvmate.region import Region

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE_PATH = ASSETS / "templates" / "ok_button.png"
KNOWN_X, KNOWN_Y = 120, 80


class FakeCaptureBackend(CaptureBackend):
    """Always returns the same fixed frame, regardless of the requested
    bbox — enough to drive Region's find/exists/wait logic in tests."""

    def __init__(self, image):
        self._image = image

    def grab(self, bbox=None):
        return self._image

    def list_monitors(self):
        h, w = self._image.shape[:2]
        return [MonitorInfo(0, 0, 0, w, h)]

    def virtual_desktop_bbox(self):
        h, w = self._image.shape[:2]
        return (0, 0, w, h)


class FakeInputController(InputController):
    """Records every call instead of touching the real mouse."""

    def __init__(self):
        self.calls: list[tuple] = []

    def move_to(self, x, y):
        self.calls.append(("move_to", x, y))

    def click(self, x, y, *, button="left", clicks=1):
        self.calls.append(("click", x, y, button, clicks))

    def drag(self, x1, y1, x2, y2, *, button="left", duration=0.2):
        self.calls.append(("drag", x1, y1, x2, y2, button))

    def scroll(self, x, y, amount):
        self.calls.append(("scroll", x, y, amount))


def _haystack(name: str):
    image = cv2.imread(str(ASSETS / "screenshots" / name), cv2.IMREAD_COLOR)
    assert image is not None, f"missing test fixture: {name}"
    return image


def _pattern() -> Pattern:
    return Pattern(TEMPLATE_PATH, threshold=0.8)


def test_region_rejects_non_positive_geometry():
    with pytest.raises(InvalidRegionError):
        Region(0, 0, 0, 10)
    with pytest.raises(InvalidRegionError):
        Region(0, 0, 10, -5)


def test_find_returns_match_offset_by_region_origin():
    capture = FakeCaptureBackend(_haystack("button_present.png"))
    region = Region(1000, 500, 260, 200, capture=capture, input_controller=FakeInputController())

    match = region.find(_pattern())

    assert abs(match.x - (1000 + KNOWN_X)) <= 3
    assert abs(match.y - (500 + KNOWN_Y)) <= 3
    assert match.confidence >= 0.8


def test_find_raises_pattern_not_found_when_absent():
    capture = FakeCaptureBackend(_haystack("button_absent.png"))
    region = Region(0, 0, 260, 200, capture=capture, input_controller=FakeInputController())

    with pytest.raises(PatternNotFoundError):
        region.find(_pattern())


def test_exists_true_and_false():
    present = Region(0, 0, 260, 200, capture=FakeCaptureBackend(_haystack("button_present.png")))
    absent = Region(0, 0, 260, 200, capture=FakeCaptureBackend(_haystack("button_absent.png")))

    assert present.exists(_pattern()) is True
    assert absent.exists(_pattern()) is False


def test_exists_saves_an_annotated_capture_like_find_does(tmp_path):
    # Regression test: exists() used to call the matcher directly, bypassing
    # find()'s save_annotated step entirely, so DebugConfig(save_annotated=True)
    # silently did nothing for exists() — the exact bug reported after real
    # GUI testing. exists() now routes through find(), so it gets the same
    # observability for free.
    debug = DebugConfig(enabled=True, save_annotated=True, annotated_output_dir=tmp_path)
    region = Region(
        0, 0, 260, 200,
        capture=FakeCaptureBackend(_haystack("button_present.png")),
        debug=debug,
    )

    assert region.exists(_pattern()) is True
    assert list(tmp_path.iterdir()), "exists() should have saved an annotated capture"


def test_find_click_chaining_dispatches_to_input_controller():
    fake_input = FakeInputController()
    region = Region(
        0, 0, 260, 200,
        capture=FakeCaptureBackend(_haystack("button_present.png")),
        input_controller=fake_input,
    )

    matched = region.find(_pattern()).click()

    assert matched.confidence >= 0.8
    assert fake_input.calls, "click() should have dispatched to the InputController"
    assert fake_input.calls[0][0] == "click"


def test_wait_for_appear_times_out_when_never_present():
    region = Region(
        0, 0, 260, 200,
        capture=FakeCaptureBackend(_haystack("button_absent.png")),
        input_controller=FakeInputController(),
    )

    with pytest.raises(CvMateTimeoutError):
        region.wait_for_appear(_pattern(), timeout=0.3, poll_interval=0.1)


def test_wait_for_vanish_returns_immediately_when_already_absent():
    region = Region(
        0, 0, 260, 200,
        capture=FakeCaptureBackend(_haystack("button_absent.png")),
        input_controller=FakeInputController(),
    )

    region.wait_for_vanish(_pattern(), timeout=1.0, poll_interval=0.1)  # should not raise


def test_sub_region_coordinates_are_relative_to_parent():
    region = Region(100, 100, 260, 200, capture=FakeCaptureBackend(_haystack("button_present.png")))

    sub = region.sub_region(10, 20, 50, 50)

    assert (sub.x, sub.y, sub.width, sub.height) == (110, 120, 50, 50)


def test_match_is_a_region_and_supports_nested_find():
    # A Match should itself be searchable, since it IS-A Region scoped to
    # the matched bounding box (this is what makes find(icon).find(sub) work).
    region = Region(0, 0, 260, 200, capture=FakeCaptureBackend(_haystack("button_present.png")))

    match = region.find(_pattern())

    assert isinstance(match, Region)
    assert match.width > 0 and match.height > 0
