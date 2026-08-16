"""``ScriptEditor``: the plain-Python script editor widget.

Save/load is just reading and writing a ``.py`` text file — there is no
custom project format. The one method the capture tool depends on is
``insert_text_at_cursor``, which is the entire integration seam between the
editor and the screen-capture tool (see ``capture_controller.py``).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit, QWidget


def format_title(path: Path | None, dirty: bool) -> str:
    """Pure formatting helper (no widget needed) so it's trivially testable:
    the display name for a script, with a leading ``*`` marker when dirty.
    """
    name = path.name if path is not None else "Untitled"
    return f"*{name}" if dirty else name


class ScriptEditor(QPlainTextEdit):
    """A single open ``.py`` script file."""

    dirtyChanged = Signal(bool)
    titleChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path: Path | None = None
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.modificationChanged.connect(self._on_modification_changed)

    # -- file identity -------------------------------------------------------

    @property
    def current_path(self) -> Path | None:
        return self._path

    @property
    def is_dirty(self) -> bool:
        return self.document().isModified()

    @property
    def title(self) -> str:
        return format_title(self._path, self.is_dirty)

    # -- file operations ------------------------------------------------------

    def new_file(self) -> None:
        self.clear()
        self._path = None
        self.document().setModified(False)
        self._emit_title()

    def open_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        self.setPlainText(text)
        self._path = path
        self.document().setModified(False)
        self._emit_title()

    def save(self) -> bool:
        """Write to ``current_path``. Returns False (no-op) if there's no
        path yet — the caller (MainWindow) is responsible for prompting a
        save-as file dialog and calling :meth:`save_as` instead."""
        if self._path is None:
            return False
        self._write(self._path)
        return True

    def save_as(self, path: Path) -> None:
        self._write(path)
        self._path = path

    def _write(self, path: Path) -> None:
        path.write_text(self.toPlainText(), encoding="utf-8")
        self.document().setModified(False)
        self._emit_title()

    # -- capture-tool integration ----------------------------------------------

    def insert_text_at_cursor(self, text: str) -> None:
        """Insert ``text`` at the current cursor position, replacing any
        active selection. This is the only method the screen-capture tool
        calls into — it never manipulates the editor's cursor directly."""
        cursor = self.textCursor()
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.setFocus()

    # -- internal --------------------------------------------------------------

    def _on_modification_changed(self, modified: bool) -> None:
        self.dirtyChanged.emit(modified)
        self._emit_title()

    def _emit_title(self) -> None:
        self.titleChanged.emit(self.title)
