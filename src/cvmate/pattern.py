"""``Pattern``: a template image plus the matching parameters to use for it
(FR13, FR14, FR18).

A ``Pattern`` never encodes *how* it is matched (that decision lives with
whichever :class:`~cvmate.matching.Matcher` a `Region`/`Screen` is
configured with) — it only carries the template pixels and per-pattern
overrides such as confidence threshold and scale range.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .assets import load_image, resolve_asset_path
from .config import ScaleRange

DEFAULT_THRESHOLD = 0.8


class Pattern:
    def __init__(
        self,
        image: str | Path | np.ndarray,
        *,
        threshold: float = DEFAULT_THRESHOLD,
        scales: tuple[float, float] | None = None,
        scale_steps: int | None = None,
        asset_folder: str | Path | None = None,
    ) -> None:
        if not 0.0 < threshold <= 1.0:
            raise ValueError("threshold must be in (0.0, 1.0]")

        self.threshold = threshold
        self.scale_range: ScaleRange | None = (
            ScaleRange(scales[0], scales[1], steps=scale_steps or 5) if scales is not None else None
        )
        self._asset_folder = asset_folder

        if isinstance(image, np.ndarray):
            self._path: Path | None = None
            self._image = image
        else:
            self._path = resolve_asset_path(image, asset_folder)
            self._image = None  # lazily loaded via .image, so cheap to construct many Patterns

    @classmethod
    def from_asset(cls, filename: str, **kwargs) -> "Pattern":
        """Equivalent to ``Pattern(filename, **kwargs)`` — kept as an
        explicit alternate constructor for readability in scripts, e.g.
        ``Pattern.from_asset("ok_button.png", threshold=0.9)``.
        """
        return cls(filename, **kwargs)

    @property
    def image(self) -> np.ndarray:
        if self._image is None:
            assert self._path is not None
            self._image = load_image(self._path)
        return self._image

    @property
    def name(self) -> str:
        return self._path.name if self._path is not None else "<in-memory image>"

    def similar(self, threshold: float) -> "Pattern":
        """Return a copy of this pattern with a different confidence
        threshold, leaving the template image and scale range unchanged."""
        return self._copy_with(threshold=threshold)

    def with_scale_range(self, min_scale: float, max_scale: float, steps: int | None = None) -> "Pattern":
        """Return a copy of this pattern with an explicit scale range.

        ``with_scale_range(1.0, 1.0, steps=1)`` opts a pattern out of the
        multi-scale sweep entirely, for game windows known not to resize.
        """
        copy = self._copy_with()
        copy.scale_range = ScaleRange(min_scale, max_scale, steps=steps or 5)
        return copy

    def _copy_with(self, threshold: float | None = None) -> "Pattern":
        source = self._path if self._path is not None else self._image
        copy = Pattern(
            source,
            threshold=threshold if threshold is not None else self.threshold,
            asset_folder=self._asset_folder,
        )
        copy.scale_range = self.scale_range
        return copy

    def __repr__(self) -> str:
        return f"Pattern({self.name!r}, threshold={self.threshold})"
