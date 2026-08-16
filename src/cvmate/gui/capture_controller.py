"""``CaptureController``: orchestrates the screen-capture-to-template flow.

show overlay -> grab pixels via cvmate's own capture backend -> prompt for
a filename -> save PNG next to the open script -> insert a
``Pattern("images/...")`` snippet into the script editor at the cursor.

Deliberately reuses ``cvmate.capture.default_capture_backend()`` for the
actual pixel grab (not a separate Qt screenshot API) so a captured template
is byte-for-byte what ``Region.capture_image()`` will see at match time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import cv2
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox, QWidget

from cvmate.capture import CaptureBackend, default_capture_backend

from .capture_overlay import CaptureOverlay
from .dialogs import prompt_template_filename
from .editor import ScriptEditor
from .naming import sanitize_filename, unique_path

CaptureBackendFactory = Callable[[], CaptureBackend]
FilenamePrompt = Callable[["QWidget | None"], "str | None"]


def overlay_rect_to_bbox(left: int, top: int, width: int, height: int) -> tuple[int, int, int, int]:
    """Maps an overlay-selected rectangle to a ``cvmate.capture`` bbox.

    Identity mapping today (the overlay already works in virtual-desktop-
    absolute coordinates, the same space ``CaptureBackend`` expects) — kept
    as its own function so DPI-scaling correction can be added later, for a
    real mixed-DPI multi-monitor Windows setup, without touching the rest
    of the orchestration below.
    """
    return (left, top, width, height)


def build_pattern_snippet(relative_path: str) -> str:
    """The exact text inserted into the script editor for a captured
    template, e.g. ``Pattern("images/ok_button.png")``.
    """
    posix_path = relative_path.replace("\\", "/")
    return f'Pattern("{posix_path}")'


class CaptureController(QObject):
    def __init__(
        self,
        editor: ScriptEditor,
        parent_widget: QWidget | None = None,
        *,
        capture_backend_factory: CaptureBackendFactory = default_capture_backend,
        prompt_filename: FilenamePrompt | None = None,
    ) -> None:
        super().__init__(parent_widget)
        self._editor = editor
        self._parent_widget = parent_widget
        self._capture_backend_factory = capture_backend_factory
        self._prompt_filename = prompt_filename or prompt_template_filename
        self._overlay: CaptureOverlay | None = None

    def start_capture(self) -> None:
        if self._editor.current_path is None:
            QMessageBox.information(
                self._parent_widget,
                "Save your script first",
                "Save this script before capturing a template image, so cv-mate "
                "knows where to save it (next to the script, in an images/ folder).",
            )
            return

        if self._parent_widget is not None:
            self._parent_widget.hide()

        self._overlay = CaptureOverlay()
        self._overlay.regionSelected.connect(self._on_region_selected)
        self._overlay.cancelled.connect(self._on_cancelled)
        self._overlay.showFullScreen()

    def _on_region_selected(self, left: int, top: int, width: int, height: int) -> None:
        self._restore_parent()

        bbox = overlay_rect_to_bbox(left, top, width, height)
        backend = self._capture_backend_factory()
        image = backend.grab(bbox)

        raw_name = self._prompt_filename(self._parent_widget)
        if not raw_name:
            return

        script_path = self._editor.current_path
        assert script_path is not None  # guaranteed by the guard in start_capture
        images_dir = script_path.parent / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        save_path = unique_path(images_dir, sanitize_filename(raw_name))
        cv2.imwrite(str(save_path), image)

        snippet = build_pattern_snippet(f"images/{save_path.name}")
        self._editor.insert_text_at_cursor(snippet)

    def _on_cancelled(self) -> None:
        self._restore_parent()

    def _restore_parent(self) -> None:
        if self._parent_widget is not None:
            self._parent_widget.show()
        self._overlay = None
