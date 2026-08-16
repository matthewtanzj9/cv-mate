"""Screen-capture abstraction (FR1-FR3).

:class:`CaptureBackend` is the seam that lets the rest of the library stay
OS-agnostic (NFR5): :class:`~cvmate.region.Region`/`~cvmate.screen.Screen`
depend only on this interface, never on ``mss`` directly. A future macOS/
Linux backend is an additive implementation of this ABC plus a dispatch
change in :func:`default_capture_backend` — no change to any calling code.
"""

from __future__ import annotations

import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

BBox = tuple[int, int, int, int]  # (left, top, width, height)


@dataclass(frozen=True)
class MonitorInfo:
    """Describes one physical monitor in virtual-desktop coordinates."""

    index: int
    left: int
    top: int
    width: int
    height: int


class CaptureBackend(ABC):
    """Abstract screen-capture backend."""

    @abstractmethod
    def grab(self, bbox: BBox | None = None) -> np.ndarray:
        """Capture pixels for ``bbox`` (left, top, width, height) in virtual
        desktop coordinates, or the full virtual desktop if ``bbox`` is
        ``None``. Returns a BGR ``np.ndarray`` (OpenCV's native channel
        order), shape ``(height, width, 3)``.
        """

    @abstractmethod
    def list_monitors(self) -> list[MonitorInfo]:
        """Enumerate physical monitors (FR3)."""

    @abstractmethod
    def virtual_desktop_bbox(self) -> BBox:
        """The bounding box (left, top, width, height) spanning every
        monitor combined — used by ``Screen(monitor=None)``."""


class WindowsCaptureBackend(CaptureBackend):
    """Capture backend built on ``mss``.

    ``mss`` already provides fast, per-monitor and virtual-desktop bbox
    capture with no compiled extension, on Windows, macOS, and Linux alike —
    this class is a thin adapter today, but keeping it behind
    :class:`CaptureBackend` still buys swapability later (e.g. to a
    higher-FPS Windows-specific backend such as ``dxcam``) without touching
    any caller.
    """

    def __init__(self) -> None:
        import mss  # local import: avoid a hard dependency at package-import time

        self._mss = mss.mss()

    def grab(self, bbox: BBox | None = None) -> np.ndarray:
        monitor = self._bbox_to_mss_region(bbox)
        shot = self._mss.grab(monitor)
        # mss returns BGRA; drop the alpha channel to get OpenCV's native BGR.
        frame = np.asarray(shot)[:, :, :3]
        return np.ascontiguousarray(frame)

    def list_monitors(self) -> list[MonitorInfo]:
        # mss.monitors[0] is the full virtual desktop; entries from index 1
        # onward are the individual physical monitors.
        monitors = self._mss.monitors[1:]
        return [
            MonitorInfo(
                index=i,
                left=m["left"],
                top=m["top"],
                width=m["width"],
                height=m["height"],
            )
            for i, m in enumerate(monitors)
        ]

    def virtual_desktop_bbox(self) -> BBox:
        full = self._mss.monitors[0]
        return (full["left"], full["top"], full["width"], full["height"])

    def _bbox_to_mss_region(self, bbox: BBox | None) -> dict:
        if bbox is None:
            return self._mss.monitors[0]
        left, top, width, height = bbox
        return {"left": left, "top": top, "width": width, "height": height}


def default_capture_backend() -> CaptureBackend:
    """Return the capture backend appropriate for the current OS.

    Only Windows is implemented in v1 (NFR2); this dispatch point is where a
    future macOS/Linux backend would be plugged in.
    """
    system = platform.system()
    if system == "Windows":
        return WindowsCaptureBackend()
    # mss itself is cross-platform, so it's reasonable to fall back to the
    # same backend during development on non-Windows machines; input
    # simulation (input.py) is where the hard Windows-only line is drawn.
    return WindowsCaptureBackend()
