"""Headless tests for CaptureController's orchestration logic.

The overlay/backend/dialogs are all mocked or faked out here — this only
exercises the *orchestration* (grab -> save -> insert snippet), not real
screen capture or real mouse-drag interaction (those need a real desktop,
see the GUI's manual/integration test notes).
"""

from __future__ import annotations

import numpy as np

import cvmate.gui.capture_controller as capture_controller_module
from cvmate.gui.capture_controller import (
    CaptureController,
    build_pattern_snippet,
    overlay_rect_to_bbox,
)
from cvmate.gui.editor import ScriptEditor


class FakeCaptureBackend:
    def __init__(self) -> None:
        self.grab_calls: list[tuple] = []

    def grab(self, bbox=None):
        self.grab_calls.append(bbox)
        return np.zeros((10, 10, 3), dtype=np.uint8)


def test_overlay_rect_to_bbox_is_identity():
    assert overlay_rect_to_bbox(10, 20, 30, 40) == (10, 20, 30, 40)


def test_build_pattern_snippet_format():
    assert build_pattern_snippet("images/ok.png") == 'Pattern("images/ok.png")'


def test_build_pattern_snippet_normalizes_backslashes():
    assert build_pattern_snippet("images\\ok.png") == 'Pattern("images/ok.png")'


def test_on_region_selected_grabs_with_correct_bbox_saves_and_inserts_snippet(qtbot, tmp_path):
    script_path = tmp_path / "bot.py"
    script_path.write_text("screen.exists()")

    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(script_path)
    cursor = editor.textCursor()
    cursor.setPosition(len("screen.exists("))  # just after the "(", before ")"
    editor.setTextCursor(cursor)

    fake_backend = FakeCaptureBackend()
    controller = CaptureController(
        editor,
        None,
        capture_backend_factory=lambda: fake_backend,
        prompt_filename=lambda parent: "ok:button.png",
    )

    controller._on_region_selected(100, 200, 50, 25)

    assert fake_backend.grab_calls == [(100, 200, 50, 25)]
    saved = tmp_path / "images" / "ok_button.png"
    assert saved.exists()
    assert editor.toPlainText() == 'screen.exists(Pattern("images/ok_button.png"))'


def test_on_region_selected_does_nothing_when_filename_prompt_cancelled(qtbot, tmp_path):
    script_path = tmp_path / "bot.py"
    script_path.write_text("")
    editor = ScriptEditor()
    qtbot.addWidget(editor)
    editor.open_file(script_path)

    fake_backend = FakeCaptureBackend()
    controller = CaptureController(
        editor,
        None,
        capture_backend_factory=lambda: fake_backend,
        prompt_filename=lambda parent: None,  # user hit Cancel
    )

    controller._on_region_selected(0, 0, 10, 10)

    assert fake_backend.grab_calls == [(0, 0, 10, 10)]  # grab still happens...
    assert editor.toPlainText() == ""  # ...but nothing gets inserted
    assert not (tmp_path / "images").exists()


def test_start_capture_blocks_and_prompts_when_script_unsaved(qtbot, monkeypatch):
    editor = ScriptEditor()
    qtbot.addWidget(editor)

    shown = []
    monkeypatch.setattr(
        capture_controller_module.QMessageBox,
        "information",
        staticmethod(lambda *a, **k: shown.append(True)),
    )

    controller = CaptureController(editor, None)
    controller.start_capture()

    assert shown == [True]
    assert controller._overlay is None  # never got as far as creating an overlay
