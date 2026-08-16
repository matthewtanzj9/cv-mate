"""``Region``/``Match``: the primary scripting surface (FR7-FR13).

``Region.find(pattern)`` returns a ``Match``, and ``Match`` *is-a* ``Region``
scoped to the matched bounding box plus mouse-action methods — this is what
makes ``find(pattern).click()`` type-check, and lets a match itself be
searched further (``find(icon).find(sub_icon)``), for free, via inheritance.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

from .capture import CaptureBackend, default_capture_backend
from .config import DebugConfig
from .debug import get_logger, save_annotated
from .exceptions import CvMateTimeoutError, InvalidRegionError, PatternNotFoundError
from .input import InputController, default_input_controller
from .matching import Matcher, TemplateScaleMatcher
from .pattern import Pattern

if TYPE_CHECKING:
    from .match import MatchResult

logger = get_logger()

DEFAULT_TIMEOUT = 10.0
DEFAULT_POLL_INTERVAL = 0.5


class Region:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        capture: CaptureBackend | None = None,
        matcher: Matcher | None = None,
        input_controller: InputController | None = None,
        debug: DebugConfig | None = None,
    ) -> None:
        if width <= 0 or height <= 0:
            raise InvalidRegionError(f"Region width/height must be positive, got ({width}, {height})")

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self._debug = debug if debug is not None else DebugConfig.from_env()
        self._capture = capture
        self._matcher = matcher
        self._input_controller = input_controller

    # -- lazily-resolved collaborators -------------------------------------
    # Resolved on first use (not at __init__) so a Region can be constructed
    # and used for pure detection (find/exists) without ever needing a real
    # input backend, and so importing/instantiating cv-mate never touches an
    # OS-specific backend until something actually requires it.

    @property
    def capture_backend(self) -> CaptureBackend:
        if self._capture is None:
            self._capture = default_capture_backend()
        return self._capture

    @property
    def matcher(self) -> Matcher:
        if self._matcher is None:
            self._matcher = TemplateScaleMatcher(debug=self._debug)
        return self._matcher

    @property
    def input_controller(self) -> InputController:
        if self._input_controller is None:
            self._input_controller = default_input_controller()
        return self._input_controller

    # -- geometry -----------------------------------------------------------

    def bbox(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def sub_region(self, x: int, y: int, width: int, height: int) -> "Region":
        """A region nested within this one, at region-local coordinates
        ``(x, y)``, sharing this region's capture/matcher/input backends."""
        return Region(
            self.x + x,
            self.y + y,
            width,
            height,
            capture=self._capture,
            matcher=self._matcher,
            input_controller=self._input_controller,
            debug=self._debug,
        )

    # -- capture --------------------------------------------------------------

    def capture_image(self) -> np.ndarray:
        image = self.capture_backend.grab(self.bbox())
        if self._debug.enabled:
            logger.debug("captured region %s -> shape=%s", self.bbox(), image.shape)
        return image

    # -- detection (FR4-FR8) -------------------------------------------------

    def find(self, pattern: "Pattern | str") -> "Match":
        pattern = self._resolve_pattern(pattern)
        image = self.capture_image()
        result = self.matcher.find_best(image, pattern)
        if result is None:
            raise PatternNotFoundError(
                f"Pattern {pattern.name!r} not found in region {self.bbox()} "
                f"(threshold={pattern.threshold})"
            )
        if self._debug.save_annotated:
            save_annotated(image, [result], self._debug.annotated_output_dir, tag=pattern.name)
        return Match(result, region=self)

    def find_all(self, pattern: "Pattern | str", max_results: int = 10) -> list["Match"]:
        pattern = self._resolve_pattern(pattern)
        image = self.capture_image()
        results = self.matcher.find_all(image, pattern, max_results=max_results)
        if self._debug.save_annotated and results:
            save_annotated(image, results, self._debug.annotated_output_dir, tag=pattern.name)
        return [Match(result, region=self) for result in results]

    def exists(self, pattern: "Pattern | str") -> bool:
        pattern = self._resolve_pattern(pattern)
        image = self.capture_image()
        return self.matcher.find_best(image, pattern) is not None

    def wait_for_appear(
        self,
        pattern: "Pattern | str",
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> "Match":
        pattern = self._resolve_pattern(pattern)
        deadline = time.monotonic() + timeout
        while True:
            try:
                return self.find(pattern)
            except PatternNotFoundError:
                pass
            if time.monotonic() >= deadline:
                raise CvMateTimeoutError(
                    f"Pattern {pattern.name!r} did not appear within {timeout}s"
                )
            time.sleep(poll_interval)

    def wait_for_vanish(
        self,
        pattern: "Pattern | str",
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> None:
        pattern = self._resolve_pattern(pattern)
        deadline = time.monotonic() + timeout
        while self.exists(pattern):
            if time.monotonic() >= deadline:
                raise CvMateTimeoutError(
                    f"Pattern {pattern.name!r} did not vanish within {timeout}s"
                )
            time.sleep(poll_interval)

    # -- input on a bare point in the region (FR9-FR12) ----------------------

    def click(self, x: int, y: int, **kwargs) -> "Region":
        """Click at region-local coordinates ``(x, y)``."""
        self.input_controller.click(self.x + x, self.y + y, **kwargs)
        return self

    def move_to(self, x: int, y: int) -> "Region":
        self.input_controller.move_to(self.x + x, self.y + y)
        return self

    def _resolve_pattern(self, pattern: "Pattern | str") -> Pattern:
        return Pattern(pattern, asset_folder=None) if isinstance(pattern, str) else pattern

    def __repr__(self) -> str:
        return f"{type(self).__name__}(x={self.x}, y={self.y}, width={self.width}, height={self.height})"


class Match(Region):
    """A found match: a :class:`Region` scoped to the matched bounding box,
    plus mouse-action helpers at the match's own coordinates (default click
    point is the match's center).
    """

    def __init__(self, result: "MatchResult", *, region: Region) -> None:
        super().__init__(
            region.x + result.x,
            region.y + result.y,
            result.width,
            result.height,
            capture=region._capture,
            matcher=region._matcher,
            input_controller=region._input_controller,
            debug=region._debug,
        )
        self._result = result

    @property
    def result(self) -> "MatchResult":
        return self._result

    @property
    def confidence(self) -> float:
        return self._result.confidence

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def click(self, *, button: str = "left", clicks: int = 1, offset: tuple[int, int] = (0, 0)) -> "Match":
        cx, cy = self.center
        self.input_controller.click(cx + offset[0], cy + offset[1], button=button, clicks=clicks)
        return self

    def double_click(self) -> "Match":
        return self.click(clicks=2)

    def right_click(self) -> "Match":
        return self.click(button="right")

    def drag_to(self, target: "Match | tuple[int, int]", *, button: str = "left") -> "Match":
        target_x, target_y = target.center if isinstance(target, Match) else target
        cx, cy = self.center
        self.input_controller.drag(cx, cy, target_x, target_y, button=button)
        return self

    def hover(self) -> "Match":
        cx, cy = self.center
        self.input_controller.move_to(cx, cy)
        return self

    def __repr__(self) -> str:
        return f"Match(x={self.x}, y={self.y}, confidence={self._result.confidence:.3f})"
