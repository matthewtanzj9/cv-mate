"""``Screen``: a :class:`~cvmate.region.Region` scoped to a monitor, or the
full virtual desktop across all monitors (FR1, FR3).
"""

from __future__ import annotations

from .capture import CaptureBackend, MonitorInfo, default_capture_backend
from .config import DebugConfig
from .input import InputController
from .matching import Matcher
from .region import Region


class Screen(Region):
    def __init__(
        self,
        monitor: int | None = None,
        *,
        capture: CaptureBackend | None = None,
        matcher: Matcher | None = None,
        input_controller: InputController | None = None,
        debug: DebugConfig | None = None,
    ) -> None:
        backend = capture or default_capture_backend()

        if monitor is None:
            x, y, width, height = backend.virtual_desktop_bbox()
        else:
            monitors = backend.list_monitors()
            if not 0 <= monitor < len(monitors):
                raise ValueError(
                    f"No monitor at index {monitor}; {len(monitors)} monitor(s) detected"
                )
            m = monitors[monitor]
            x, y, width, height = m.left, m.top, m.width, m.height

        super().__init__(
            x,
            y,
            width,
            height,
            capture=backend,
            matcher=matcher,
            input_controller=input_controller,
            debug=debug,
        )
        self.monitor = monitor

    @staticmethod
    def list_monitors() -> list[MonitorInfo]:
        return default_capture_backend().list_monitors()

    def __repr__(self) -> str:
        return f"Screen(monitor={self.monitor}, x={self.x}, y={self.y}, width={self.width}, height={self.height})"
