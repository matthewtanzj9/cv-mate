"""Small dialog helpers for the GUI."""

from __future__ import annotations

from PySide6.QtWidgets import QInputDialog, QWidget

DEFAULT_TEMPLATE_NAME = "template.png"


def prompt_template_filename(parent: "QWidget | None") -> "str | None":
    """Ask the user for a base filename for a just-captured template
    image. Returns ``None`` if the user cancelled.

    The returned text is raw user input — callers should still run it
    through :func:`cvmate.gui.naming.sanitize_filename` before using it as
    an actual path component.
    """
    text, ok = QInputDialog.getText(
        parent,
        "Save template as",
        "Filename:",
        text=DEFAULT_TEMPLATE_NAME,
    )
    return text if ok else None
