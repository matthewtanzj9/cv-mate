"""Pure-data configuration objects.

Kept dependency-free (no cv2/numpy imports) so they're cheap to import and
easy to unit test in isolation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScaleRange:
    """A range of scale factors to sweep when matching a pattern (FR18).

    ``steps`` is the number of linearly-spaced scale factors tried between
    ``min_scale`` and ``max_scale`` (inclusive). ``steps=1`` degenerates to a
    single scale factor (``min_scale``), which is how a script opts out of
    the multi-scale sweep entirely for a pattern it knows won't resize.
    """

    min_scale: float = 0.8
    max_scale: float = 1.2
    steps: int = 5

    def __post_init__(self) -> None:
        if self.steps < 1:
            raise ValueError("ScaleRange.steps must be >= 1")
        if self.min_scale <= 0 or self.max_scale <= 0:
            raise ValueError("ScaleRange scale factors must be positive")
        if self.min_scale > self.max_scale:
            raise ValueError("ScaleRange.min_scale must be <= max_scale")

    def is_single_scale(self) -> bool:
        return self.steps == 1 or self.min_scale == self.max_scale

    @property
    def step_size(self) -> float:
        """Spacing between adjacent scale factors in this range."""
        if self.is_single_scale():
            return 0.0
        return (self.max_scale - self.min_scale) / (self.steps - 1)

    def factors(self) -> list[float]:
        """The concrete scale factors this range expands to."""
        if self.is_single_scale():
            return [self.min_scale]
        step_size = (self.max_scale - self.min_scale) / (self.steps - 1)
        return [self.min_scale + i * step_size for i in range(self.steps)]

    def coarse(self) -> "ScaleRange":
        """A wider-stride, fewer-step version of this range, used for the
        first pass of a coarse-to-fine search."""
        if self.is_single_scale():
            return self
        return ScaleRange(self.min_scale, self.max_scale, steps=max(3, self.steps // 2))

    def narrowed_around(self, scale: float, margin: float = 0.05) -> "ScaleRange":
        """A narrow range around ``scale``, clamped to this range's bounds —
        used for the refine pass of a coarse-to-fine search."""
        lo = max(self.min_scale, scale - margin)
        hi = min(self.max_scale, scale + margin)
        if lo > hi:
            lo, hi = hi, lo
        return ScaleRange(lo, hi, steps=self.steps)


@dataclass
class DebugConfig:
    """Controls verbose logging and annotated-capture output (FR19/NFR10).

    Resolved once per :class:`~cvmate.region.Region`/`~cvmate.screen.Screen`
    at construction time (not re-read per frame), so leaving debug off costs
    nothing beyond the initial env-var read and a boolean check at each call
    site.
    """

    enabled: bool = False
    save_annotated: bool = False
    annotated_output_dir: Path = Path("./cvmate_debug")

    @classmethod
    def from_env(cls) -> "DebugConfig":
        """Build a :class:`DebugConfig` from environment variables:

        - ``CVMATE_DEBUG=1`` enables verbose logging.
        - ``CVMATE_DEBUG_SAVE=1`` additionally saves annotated captures.
        - ``CVMATE_DEBUG_DIR=<path>`` overrides the output directory.
        """
        enabled = _env_flag("CVMATE_DEBUG")
        save_annotated = _env_flag("CVMATE_DEBUG_SAVE")
        out_dir = os.environ.get("CVMATE_DEBUG_DIR")
        return cls(
            enabled=enabled,
            save_annotated=save_annotated,
            annotated_output_dir=Path(out_dir) if out_dir else Path("./cvmate_debug"),
        )


_TRUTHY = {"1", "true", "yes", "on"}


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY
