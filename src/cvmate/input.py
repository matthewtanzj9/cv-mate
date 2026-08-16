"""Mouse-input abstraction (FR9-FR12).

:class:`InputController` is the second extensibility seam (alongside
:class:`~cvmate.capture.CaptureBackend`): a future keyboard feature is added
as an *additive* new ``KeyboardController`` ABC, not a change to this one, so
existing scripts and existing input backends are unaffected (NFR5).
"""

from __future__ import annotations

import platform
from abc import ABC, abstractmethod

Button = str  # "left" | "right" | "middle"


class InputController(ABC):
    """Abstract mouse-input backend."""

    @abstractmethod
    def move_to(self, x: int, y: int) -> None: ...

    @abstractmethod
    def click(self, x: int, y: int, *, button: Button = "left", clicks: int = 1) -> None: ...

    @abstractmethod
    def drag(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        *,
        button: Button = "left",
        duration: float = 0.2,
    ) -> None: ...

    @abstractmethod
    def scroll(self, x: int, y: int, amount: int) -> None: ...


class WindowsMouseController(InputController):
    """Mouse control via ``pydirectinput``.

    ``pydirectinput`` injects input via the Windows ``SendInput`` API, which
    (unlike plain ``pyautogui``) is reliably picked up by fullscreen/DirectX
    game surfaces — directly relevant since this library targets gameplay
    automation. The dependency is only imported here, lazily, so importing
    ``cvmate`` on a non-Windows machine (e.g. to run the offline unit tests
    in CI) never fails merely because ``pydirectinput`` isn't installed.
    """

    def __init__(self) -> None:
        try:
            import pydirectinput
        except ImportError as exc:  # pragma: no cover - exercised only off-Windows
            raise RuntimeError(
                "WindowsMouseController requires the 'pydirectinput' package, "
                "which is only installable/usable on Windows. Install it with "
                "`pip install pydirectinput` on a Windows machine."
            ) from exc
        self._pdi = pydirectinput

    def move_to(self, x: int, y: int) -> None:
        self._pdi.moveTo(x, y)

    def click(self, x: int, y: int, *, button: Button = "left", clicks: int = 1) -> None:
        self._pdi.click(x=x, y=y, clicks=clicks, button=button)

    def drag(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        *,
        button: Button = "left",
        duration: float = 0.2,
    ) -> None:
        self._pdi.moveTo(x1, y1)
        self._pdi.mouseDown(button=button)
        self._pdi.moveTo(x2, y2, duration=duration)
        self._pdi.mouseUp(button=button)

    def scroll(self, x: int, y: int, amount: int) -> None:
        self._pdi.moveTo(x, y)
        self._pdi.scroll(amount)


def default_input_controller() -> InputController:
    """Return the input backend appropriate for the current OS.

    Only Windows is implemented in v1 (NFR2); this dispatch point is where a
    future macOS/Linux backend would be plugged in.
    """
    system = platform.system()
    if system == "Windows":
        return WindowsMouseController()
    raise RuntimeError(
        f"cv-mate has no InputController implementation for platform {system!r} "
        "in v1 (Windows-only). Pass an explicit `input_controller=` (e.g. a "
        "test fake) if you need to exercise Region/Screen logic on this OS."
    )
