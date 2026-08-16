"""``TemplatePreviewPanel``: shows the actual image a `Pattern(...)` call in
the editor refers to, updating live as the cursor moves.

The path-extraction/resolution logic is split into plain functions (no Qt
import) so it's fully unit-testable without a QApplication; only the
widget itself touches Qt.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .editor import ScriptEditor

PREVIEW_MAX_WIDTH = 300
PREVIEW_MAX_HEIGHT = 200

_PLACEHOLDER_TEXT = "Move the cursor onto a Pattern(...) call to preview its image."

# Matches Pattern("...") / Pattern('...') / Pattern.from_asset("...") —
# capturing the string argument (the image path/filename).
_PATTERN_CALL_RE = re.compile(r"""Pattern(?:\.from_asset)?\s*\(\s*["']([^"']+)["']""")


def extract_pattern_path(line: str, column: int | None = None) -> str | None:
    """Find the image path inside the ``Pattern(...)`` call on ``line``
    nearest to ``column`` (a line can only reasonably have one in practice,
    but this picks the closest if there happen to be several). Returns
    ``None`` if the line has no ``Pattern(...)`` call at all.
    """
    matches = list(_PATTERN_CALL_RE.finditer(line))
    if not matches:
        return None
    if column is None:
        return matches[0].group(1)

    for match in matches:
        if match.start() <= column <= match.end():
            return match.group(1)
    nearest = min(matches, key=lambda m: min(abs(m.start() - column), abs(m.end() - column)))
    return nearest.group(1)


def resolve_template_path(raw_path: str, script_path: Path | None) -> Path | None:
    """Resolve ``raw_path`` (as written in a script, e.g. ``"images/x.png"``)
    the same way the running script itself would: relative to the script's
    own directory (matching the capture tool's save convention and
    ``RunController``'s cwd), falling back to the current working directory
    if there's no open script yet. Returns ``None`` if nothing exists there.
    """
    base = script_path.parent if script_path is not None else Path.cwd()
    candidate = (base / raw_path).resolve()
    return candidate if candidate.is_file() else None


class TemplatePreviewPanel(QWidget):
    def __init__(self, editor: ScriptEditor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor

        self.status_label = QLabel(_PLACEHOLDER_TEXT, self)
        self.status_label.setWordWrap(True)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(PREVIEW_MAX_HEIGHT)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.image_label, 1)

        editor.cursorPositionChanged.connect(self.refresh)
        editor.titleChanged.connect(lambda _title=None: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        cursor = self._editor.textCursor()
        raw_path = extract_pattern_path(cursor.block().text(), cursor.positionInBlock())

        if raw_path is None:
            self._show_status(_PLACEHOLDER_TEXT)
            return

        resolved = resolve_template_path(raw_path, self._editor.current_path)
        if resolved is None:
            self._show_status(f'Pattern("{raw_path}") — file not found')
            return

        pixmap = QPixmap(str(resolved))
        if pixmap.isNull():
            self._show_status(f'Pattern("{raw_path}") — could not load image')
            return

        self.status_label.setText(f'Pattern("{raw_path}")  {pixmap.width()}×{pixmap.height()}px')
        self.image_label.setPixmap(
            pixmap.scaled(
                PREVIEW_MAX_WIDTH,
                PREVIEW_MAX_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _show_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.image_label.clear()
