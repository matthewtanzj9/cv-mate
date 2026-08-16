"""Sanity checks for the theme module and its wiring into the app/widgets."""

from __future__ import annotations

from PySide6.QtGui import QFont

from cvmate.gui import theme
from cvmate.gui.highlighter import KEYWORD_FORMAT
from cvmate.gui.main_window import MainWindow


def test_editor_font_is_monospace():
    font = theme.editor_font()
    assert font.fixedPitch() is True
    assert font.styleHint() == QFont.StyleHint.Monospace


def test_stylesheet_is_non_empty_and_mentions_key_widgets():
    assert "QPlainTextEdit" in theme.STYLESHEET
    assert "QDockWidget" in theme.STYLESHEET
    assert theme.BACKGROUND in theme.STYLESHEET


def test_highlighter_colors_come_from_theme():
    # Regression guard: the syntax highlighter's colors must stay sourced
    # from theme.py, not drift back to independently hardcoded hex values,
    # or the editor's dark background and its token colors could mismatch
    # again (the original low-contrast bug this theme pass fixed).
    assert KEYWORD_FORMAT.foreground().color().name().lower() == theme.TOKEN_KEYWORD.lower()


def test_main_window_editor_uses_the_theme_font(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.editor.font().fixedPitch() is True
    assert window.output_pane.font().fixedPitch() is True


def test_toolbar_actions_have_icons(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.run_action.icon().isNull()
    assert not window.stop_action.icon().isNull()
    assert not window.capture_action.icon().isNull()
