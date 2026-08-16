"""Pattern-matching engine (FR4-FR8, FR18).

:class:`Matcher` is the abstraction that lets :class:`~cvmate.region.Region`
stay agnostic of *how* patterns are located — :class:`TemplateScaleMatcher`
is the v1 implementation (scale-pyramid template matching); a future
feature-based matcher (ORB/SIFT/AKAZE) can be added later as another
``Matcher`` implementation without touching ``Region``/``Pattern`` (NFR5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import cv2
import numpy as np

from .config import DebugConfig, ScaleRange
from .debug import get_logger
from .match import MatchResult
from .pattern import Pattern

logger = get_logger()

DEFAULT_SCALE_RANGE = ScaleRange()


class Matcher(ABC):
    """Abstract pattern-matching backend."""

    @abstractmethod
    def find_best(self, haystack: np.ndarray, pattern: Pattern) -> MatchResult | None:
        """The single best match for ``pattern`` in ``haystack``, or
        ``None`` if nothing clears ``pattern.threshold``."""

    @abstractmethod
    def find_all(self, haystack: np.ndarray, pattern: Pattern, max_results: int = 10) -> list[MatchResult]:
        """All non-overlapping matches for ``pattern`` in ``haystack`` that
        clear ``pattern.threshold``, best-confidence first, capped at
        ``max_results``."""


class TemplateScaleMatcher(Matcher):
    """Scale-pyramid ``cv2.matchTemplate`` matcher.

    For each candidate scale factor, the *template* is resized (cheap — the
    template is normally small, and a single haystack capture is typically
    matched against several patterns per frame, so resizing the template
    rather than the haystack avoids repeating a larger resize per pattern).
    """

    def __init__(
        self,
        *,
        default_scales: ScaleRange = DEFAULT_SCALE_RANGE,
        coarse_to_fine: bool = True,
        debug: DebugConfig | None = None,
    ) -> None:
        self._default_scales = default_scales
        self._coarse_to_fine = coarse_to_fine
        self._debug = debug or DebugConfig()

    def find_best(self, haystack: np.ndarray, pattern: Pattern) -> MatchResult | None:
        scale_range = pattern.scale_range or self._default_scales
        best = self._search(haystack, pattern, scale_range)
        if best is not None and self._debug.enabled:
            logger.debug(
                "find_best(%s): best=%.3f @ scale=%.2f (threshold=%.2f)",
                pattern.name,
                best.confidence,
                best.scale,
                pattern.threshold,
            )
        if best is None or best.confidence < pattern.threshold:
            return None
        return best

    def find_all(self, haystack: np.ndarray, pattern: Pattern, max_results: int = 10) -> list[MatchResult]:
        scale_range = pattern.scale_range or self._default_scales
        candidates: list[MatchResult] = []
        for scale in scale_range.factors():
            candidates.extend(self._candidates_at_scale(haystack, pattern, scale))

        candidates = [c for c in candidates if c.confidence >= pattern.threshold]
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return _suppress_overlapping(candidates)[:max_results]

    def _search(self, haystack: np.ndarray, pattern: Pattern, scale_range: ScaleRange) -> MatchResult | None:
        """Coarse-to-fine scale sweep, tracking the single best-scoring
        candidate. Degenerates to one ``cv2.matchTemplate`` call when
        ``scale_range`` is single-scale or coarse-to-fine search is off.
        """
        if scale_range.is_single_scale() or not self._coarse_to_fine:
            return self._best_at_scales(haystack, pattern, scale_range.factors())

        coarse_range = scale_range.coarse()
        coarse_best = self._best_at_scales(haystack, pattern, coarse_range.factors())
        if coarse_best is None:
            return None

        # The refine window must span at least the coarse pass's own step
        # spacing on each side of its best candidate — otherwise, when the
        # true peak falls *between* two coarse samples (matchTemplate
        # confidence can fall off sharply just one scale-step away from the
        # true size), a narrower window would search right past it. This
        # costs nothing extra: the fine sweep is still just `scale_range.steps`
        # matchTemplate calls, now spread across a window guaranteed to
        # include the coarse best's immediate neighbors.
        margin = max(coarse_range.step_size, 0.01)
        fine_range = scale_range.narrowed_around(coarse_best.scale, margin=margin)
        fine_best = self._best_at_scales(haystack, pattern, fine_range.factors())
        return fine_best if fine_best is not None and fine_best.confidence >= coarse_best.confidence else coarse_best

    def _best_at_scales(self, haystack: np.ndarray, pattern: Pattern, scales: list[float]) -> MatchResult | None:
        best: MatchResult | None = None
        for scale in scales:
            candidate = self._match_at_scale(haystack, pattern, scale)
            if candidate is None:
                continue
            if self._debug.enabled:
                logger.debug("  scale=%.3f confidence=%.3f", scale, candidate.confidence)
            if best is None or candidate.confidence > best.confidence:
                best = candidate
        return best

    def _candidates_at_scale(self, haystack: np.ndarray, pattern: Pattern, scale: float) -> list[MatchResult]:
        template = _resize(pattern.image, scale)
        if not _fits(template, haystack):
            return []
        result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        th, tw = template.shape[:2]
        locations = np.argwhere(result >= pattern.threshold)
        return [
            MatchResult(
                x=int(x),
                y=int(y),
                width=tw,
                height=th,
                confidence=float(result[y, x]),
                scale=scale,
                pattern=pattern,
            )
            for y, x in locations
        ]

    def _match_at_scale(self, haystack: np.ndarray, pattern: Pattern, scale: float) -> MatchResult | None:
        template = _resize(pattern.image, scale)
        if not _fits(template, haystack):
            return None
        result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        th, tw = template.shape[:2]
        return MatchResult(
            x=max_loc[0],
            y=max_loc[1],
            width=tw,
            height=th,
            confidence=float(max_val),
            scale=scale,
            pattern=pattern,
        )


def _resize(image: np.ndarray, scale: float) -> np.ndarray:
    if scale == 1.0:
        return image
    height, width = image.shape[:2]
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(image, new_size, interpolation=interpolation)


def _fits(template: np.ndarray, haystack: np.ndarray) -> bool:
    th, tw = template.shape[:2]
    hh, hw = haystack.shape[:2]
    return th <= hh and tw <= hw


def _suppress_overlapping(matches: list[MatchResult], overlap_threshold: float = 0.3) -> list[MatchResult]:
    """Greedy non-max suppression: given matches sorted best-confidence
    first, drop any later match whose bounding box overlaps an
    already-kept match beyond ``overlap_threshold`` (fraction of the
    smaller box's area). Keeps find_all from returning many near-duplicate
    detections of the same on-screen instance.
    """
    kept: list[MatchResult] = []
    for candidate in matches:
        if not any(_overlap_fraction(candidate, k) > overlap_threshold for k in kept):
            kept.append(candidate)
    return kept


def _overlap_fraction(a: MatchResult, b: MatchResult) -> float:
    ax2, ay2 = a.x + a.width, a.y + a.height
    bx2, by2 = b.x + b.width, b.y + b.height
    ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    smaller_area = min(a.width * a.height, b.width * b.height)
    return intersection / smaller_area if smaller_area else 0.0
