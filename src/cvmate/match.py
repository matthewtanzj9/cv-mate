"""The value object returned by a successful pattern match."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pattern import Pattern


@dataclass(frozen=True)
class MatchResult:
    """Where a :class:`~cvmate.pattern.Pattern` was found in a captured
    image, and how confidently.

    Coordinates are relative to the image that was searched (typically a
    :class:`~cvmate.region.Region`'s own capture, i.e. region-local, not
    necessarily full-screen/virtual-desktop coordinates) — callers that need
    absolute coordinates combine this with the searching region's origin,
    which is exactly what :class:`~cvmate.region.Match` does.
    """

    x: int
    y: int
    width: int
    height: int
    confidence: float
    scale: float
    pattern: "Pattern"

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
