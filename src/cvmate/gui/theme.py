"""Centralized visual theme for the GUI.

Kept in one place so the app-wide dark stylesheet and the syntax
highlighter's token colors (originally VS Code Dark+ values, tuned for a
dark background — they were washed-out and low-contrast on the default
white editor background) never drift out of sync with each other.
"""

from __future__ import annotations

from PySide6.QtGui import QFont

BACKGROUND = "#1e1e1e"
BACKGROUND_ALT = "#252526"
FOREGROUND = "#d4d4d4"
BORDER = "#3c3c3c"
ACCENT = "#569cd6"
SELECTION_BACKGROUND = "#264f78"

# Syntax token colors — imported by highlighter.py so the editor's coloring
# and the rest of the theme are always drawn from one source of truth.
TOKEN_KEYWORD = "#569CD6"
TOKEN_STRING = "#CE9178"
TOKEN_COMMENT = "#6A9955"
TOKEN_NUMBER = "#B5CEA8"

EDITOR_FONT_FAMILIES = ["Cascadia Mono", "Consolas", "Courier New", "monospace"]
EDITOR_FONT_SIZE = 11

STYLESHEET = f"""
QWidget {{
    background-color: {BACKGROUND};
    color: {FOREGROUND};
}}
QMainWindow::separator {{
    background-color: {BORDER};
    width: 1px;
    height: 1px;
}}
QDockWidget, QToolBar, QMenuBar, QMenu, QStatusBar {{
    background-color: {BACKGROUND_ALT};
    color: {FOREGROUND};
}}
QMenuBar::item:selected, QMenu::item:selected {{
    background-color: {ACCENT};
    color: #ffffff;
}}
QDockWidget::title {{
    background-color: {BACKGROUND_ALT};
    padding: 5px 6px;
    border-bottom: 1px solid {BORDER};
}}
QPlainTextEdit, QTextBrowser, QTextEdit, QLineEdit {{
    background-color: {BACKGROUND};
    color: {FOREGROUND};
    border: 1px solid {BORDER};
    selection-background-color: {SELECTION_BACKGROUND};
}}
QToolBar {{
    border: none;
    spacing: 6px;
    padding: 4px;
}}
QToolButton {{
    background: transparent;
    padding: 4px 8px;
    border-radius: 4px;
}}
QToolButton:hover {{
    background-color: {BORDER};
}}
QToolButton:disabled {{
    color: #6a6a6a;
}}
QCheckBox {{
    padding: 0 6px;
}}
QSplitter::handle {{
    background-color: {BORDER};
}}
QScrollBar:vertical, QScrollBar:horizontal {{
    background-color: {BACKGROUND_ALT};
    border: none;
}}
QScrollBar::handle {{
    background-color: {BORDER};
    border-radius: 3px;
}}
QPushButton {{
    background-color: {BACKGROUND_ALT};
    border: 1px solid {BORDER};
    padding: 4px 12px;
    border-radius: 3px;
}}
QPushButton:hover {{
    background-color: {BORDER};
}}
"""


def editor_font() -> QFont:
    """A monospace font for the script editor and output pane — falls back
    through a preference list since not every OS has "Cascadia Mono"."""
    font = QFont()
    font.setFamilies(EDITOR_FONT_FAMILIES)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    font.setPointSize(EDITOR_FONT_SIZE)
    return font
