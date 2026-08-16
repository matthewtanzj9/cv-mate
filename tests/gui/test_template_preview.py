"""Tests for the Template Preview panel.

extract_pattern_path()/resolve_template_path() are plain functions (no Qt)
tested directly; TemplatePreviewPanel's live-update behavior is tested
headlessly via qtbot.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from cvmate.gui.editor import ScriptEditor
from cvmate.gui.template_preview import (
    TemplatePreviewPanel,
    extract_pattern_path,
    resolve_template_path,
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SAMPLE_IMAGE = ASSETS / "templates" / "ok_button.png"


# -- extract_pattern_path -----------------------------------------------------


def test_extract_pattern_path_simple_call():
    assert extract_pattern_path('screen.exists(Pattern("images/ok.png"))') == "images/ok.png"


def test_extract_pattern_path_single_quotes():
    assert extract_pattern_path("Pattern('images/ok.png')") == "images/ok.png"


def test_extract_pattern_path_from_asset_variant():
    assert extract_pattern_path('Pattern.from_asset("ok.png", threshold=0.9)') == "ok.png"


def test_extract_pattern_path_no_match_returns_none():
    assert extract_pattern_path("screen = Screen()") is None
    assert extract_pattern_path("") is None


def test_extract_pattern_path_picks_the_call_under_the_column():
    line = 'a = Pattern("first.png"); b = Pattern("second.png")'
    column_in_second = line.index('"second.png"') + 2
    assert extract_pattern_path(line, column_in_second) == "second.png"


def test_extract_pattern_path_defaults_to_first_when_column_is_none():
    line = 'a = Pattern("first.png"); b = Pattern("second.png")'
    assert extract_pattern_path(line) == "first.png"


# -- resolve_template_path ----------------------------------------------------


def test_resolve_template_path_relative_to_script_dir(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    shutil.copy(SAMPLE_IMAGE, images_dir / "ok.png")
    script_path = tmp_path / "bot.py"

    resolved = resolve_template_path("images/ok.png", script_path)

    assert resolved == (images_dir / "ok.png").resolve()


def test_resolve_template_path_missing_file_returns_none(tmp_path):
    script_path = tmp_path / "bot.py"
    assert resolve_template_path("images/nope.png", script_path) is None


def test_resolve_template_path_falls_back_to_cwd_when_no_script(tmp_path, monkeypatch):
    shutil.copy(SAMPLE_IMAGE, tmp_path / "ok.png")
    monkeypatch.chdir(tmp_path)

    assert resolve_template_path("ok.png", None) == (tmp_path / "ok.png").resolve()


# -- TemplatePreviewPanel (headless, qtbot) -----------------------------------


def _place_cursor_at_end(editor: ScriptEditor) -> None:
    cursor = editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    editor.setTextCursor(cursor)


def test_panel_shows_placeholder_with_no_pattern_on_the_line(qtbot):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    panel = TemplatePreviewPanel(editor)
    qtbot.addWidget(panel)

    editor.setPlainText("screen = Screen()")
    _place_cursor_at_end(editor)
    panel.refresh()

    assert "Move the cursor" in panel.status_label.text()
    assert panel.image_label.pixmap() is None or panel.image_label.pixmap().isNull()


def test_panel_shows_not_found_for_a_missing_image(qtbot, tmp_path):
    script_path = tmp_path / "bot.py"
    script_path.write_text("")
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(script_path)
    panel = TemplatePreviewPanel(editor)
    qtbot.addWidget(panel)

    editor.setPlainText('Pattern("images/missing.png")')
    _place_cursor_at_end(editor)
    panel.refresh()

    assert "file not found" in panel.status_label.text()


def test_panel_shows_the_image_when_it_exists(qtbot, tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    shutil.copy(SAMPLE_IMAGE, images_dir / "ok.png")
    script_path = tmp_path / "bot.py"
    script_path.write_text("")

    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(script_path)
    panel = TemplatePreviewPanel(editor)
    qtbot.addWidget(panel)

    editor.setPlainText('Pattern("images/ok.png")')
    _place_cursor_at_end(editor)
    panel.refresh()

    assert "images/ok.png" in panel.status_label.text()
    assert "px" in panel.status_label.text()
    assert not panel.image_label.pixmap().isNull()


def test_panel_refreshes_automatically_on_cursor_move(qtbot, tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    shutil.copy(SAMPLE_IMAGE, images_dir / "ok.png")
    script_path = tmp_path / "bot.py"
    script_path.write_text("")

    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(script_path)
    panel = TemplatePreviewPanel(editor)
    qtbot.addWidget(panel)

    editor.setPlainText('Pattern("images/ok.png")\nx = 1')
    # Move cursor to the second, pattern-less line — no explicit panel.refresh() call.
    cursor = editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    assert "Move the cursor" in panel.status_label.text()
