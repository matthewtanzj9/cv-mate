"""Headless tests for ScriptEditor: dirty-tracking, save/open, title
formatting, and the cursor-insertion seam the capture tool depends on.
"""

from __future__ import annotations

from pathlib import Path

from cvmate.gui.editor import ScriptEditor, format_title


def test_format_title_untitled_not_dirty():
    assert format_title(None, False) == "Untitled"


def test_format_title_untitled_dirty():
    assert format_title(None, True) == "*Untitled"


def test_format_title_with_path():
    assert format_title(Path("foo.py"), False) == "foo.py"
    assert format_title(Path("foo.py"), True) == "*foo.py"


def test_new_editor_is_not_dirty(qtbot):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    assert editor.is_dirty is False
    assert editor.current_path is None
    assert editor.title == "Untitled"


def test_typing_marks_dirty_and_emits_signal(qtbot):
    editor = ScriptEditor()
    qtbot.addWidget(editor)

    with qtbot.waitSignal(editor.dirtyChanged, timeout=1000) as blocker:
        qtbot.keyClicks(editor, "hello")

    assert blocker.args == [True]
    assert editor.is_dirty is True


def test_save_without_path_is_a_noop_returning_false(qtbot):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    # Real typing (not setPlainText, which Qt treats as "loading" content
    # and deliberately leaves the modified flag alone) so this test
    # actually exercises the dirty state.
    qtbot.keyClicks(editor, "x = 1")

    assert editor.save() is False
    assert editor.is_dirty is True  # nothing was written, so still dirty


def test_save_as_writes_file_sets_path_and_clears_dirty(qtbot, tmp_path):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("print('hi')")

    path = tmp_path / "script.py"
    editor.save_as(path)

    assert editor.current_path == path
    assert editor.is_dirty is False
    assert path.read_text() == "print('hi')"


def test_save_with_existing_path_overwrites_file(qtbot, tmp_path):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    path = tmp_path / "script.py"
    editor.save_as(path)

    editor.setPlainText("x = 2")
    assert editor.save() is True
    assert path.read_text() == "x = 2"


def test_open_file_loads_content_and_resets_dirty(qtbot, tmp_path):
    path = tmp_path / "script.py"
    path.write_text("import cvmate")

    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(path)

    assert editor.toPlainText() == "import cvmate"
    assert editor.current_path == path
    assert editor.is_dirty is False


def test_new_file_clears_editor_and_path(qtbot, tmp_path):
    path = tmp_path / "script.py"
    path.write_text("x = 1")

    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(path)
    editor.new_file()

    assert editor.toPlainText() == ""
    assert editor.current_path is None
    assert editor.is_dirty is False


def test_insert_text_at_cursor_inserts_at_the_cursor_position(qtbot):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("screen.exists()")

    cursor = editor.textCursor()
    cursor.setPosition(len("screen.exists("))
    editor.setTextCursor(cursor)

    editor.insert_text_at_cursor('Pattern("images/x.png")')

    assert editor.toPlainText() == 'screen.exists(Pattern("images/x.png"))'


def test_insert_text_at_cursor_replaces_a_selection(qtbot):
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Pattern(OLD)")

    cursor = editor.textCursor()
    cursor.setPosition(len("Pattern("))
    cursor.setPosition(len("Pattern(OLD"), cursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_text_at_cursor('"images/new.png"')

    assert editor.toPlainText() == 'Pattern("images/new.png")'
