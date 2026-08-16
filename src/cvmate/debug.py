"""Logging and annotated-capture helpers for cv-mate's debug mode.

Design goal (NFR10): debug output must be cheap to enable/disable and safe
to leave in production scripts. Every call site that produces verbose output
is expected to guard on ``DebugConfig.enabled`` *before* doing any work, so
the cost of a disabled debug mode is a single boolean check.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import cv2
import numpy as np

if TYPE_CHECKING:
    from .match import MatchResult

_LOGGER_NAME = "cvmate"


def get_logger() -> logging.Logger:
    """The module-level logger, configured with a :class:`~logging.NullHandler`
    by default so importing cv-mate never prints to stdout uninvited. A host
    script that wants to see log output attaches its own handler (or calls
    ``logging.basicConfig`` before running) in the usual way.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def ensure_visible_when_enabled(enabled: bool) -> None:
    """Make debug logging actually show up when a caller turns debug mode
    on, without requiring the host script to separately call
    ``logging.basicConfig()``.

    A ``NullHandler`` alone (see :func:`get_logger`) is deliberately silent
    — the right default for a library — but that also means
    ``DebugConfig(enabled=True)`` would produce *zero* visible output in a
    plain script or a GUI-launched subprocess, since Python's logging module
    drops DEBUG-level records before any handler sees them unless the
    logger's effective level is lowered too. That defeats the entire point
    of FR19's debug mode, so: the first time debug mode is turned on in a
    process that hasn't configured its own logging, attach a simple
    ``StreamHandler`` and set the level to DEBUG. If the host script *has*
    already added its own handler (e.g. its own ``basicConfig`` call, or
    embedding another app's logging setup), this leaves it alone — the
    presence of any handler beyond the default ``NullHandler`` is taken as
    "the host is already handling this."
    """
    if not enabled:
        return
    logger = get_logger()
    only_null_handlers = all(isinstance(h, logging.NullHandler) for h in logger.handlers)
    if only_null_handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def annotate(image: np.ndarray, matches: Iterable["MatchResult"]) -> np.ndarray:
    """Return a copy of ``image`` with a bounding box + confidence label
    drawn over each match, for visual "what did the framework see" debugging.
    """
    annotated = image.copy()
    for match in matches:
        top_left = (match.x, match.y)
        bottom_right = (match.x + match.width, match.y + match.height)
        cv2.rectangle(annotated, top_left, bottom_right, (0, 255, 0), 2)
        label = f"{match.confidence:.2f} @ {match.scale:.2f}x"
        label_origin = (match.x, max(0, match.y - 8))
        cv2.putText(
            annotated,
            label,
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    return annotated


def save_annotated(
    image: np.ndarray,
    matches: Iterable["MatchResult"],
    output_dir: Path,
    tag: str = "match",
) -> Path:
    """Draw match annotations onto ``image`` and save it under ``output_dir``
    with a timestamped filename. Returns the path written to.

    This is deliberately a separate, more expensive opt-in than plain verbose
    logging (drawing + PNG-encoding + disk I/O costs meaningfully more than a
    log line), so scripts can get verbose logs without paying this cost.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    path = output_dir / f"{tag}_{timestamp}.png"
    annotated = annotate(image, matches)
    cv2.imwrite(str(path), annotated)
    return path
