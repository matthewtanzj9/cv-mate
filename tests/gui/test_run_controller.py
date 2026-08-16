"""Headless tests for RunController — QProcess needs an event loop, not a
real display, so this genuinely runs in CI with no screen at all.
"""

from __future__ import annotations

import os
from pathlib import Path

from cvmate.gui.run_controller import RunController


def _write_script(tmp_path: Path, code: str) -> Path:
    path = tmp_path / "script.py"
    path.write_text(code)
    return path


def test_run_streams_output(qtbot, tmp_path):
    script = _write_script(tmp_path, "print('hi')")
    controller = RunController()
    chunks: list[str] = []
    controller.outputReceived.connect(chunks.append)

    with qtbot.waitSignal(controller.finished, timeout=5000):
        controller.run(script)

    assert "hi" in "".join(chunks)


def test_debug_env_var_passed_when_enabled(qtbot, tmp_path):
    script = _write_script(tmp_path, "import os; print(os.environ.get('CVMATE_DEBUG'))")
    controller = RunController()
    chunks: list[str] = []
    controller.outputReceived.connect(chunks.append)

    with qtbot.waitSignal(controller.finished, timeout=5000):
        controller.run(script, debug=True)

    assert "1" in "".join(chunks)


def test_debug_env_var_absent_when_disabled(qtbot, tmp_path):
    script = _write_script(tmp_path, "import os; print(os.environ.get('CVMATE_DEBUG'))")
    controller = RunController()
    chunks: list[str] = []
    controller.outputReceived.connect(chunks.append)

    with qtbot.waitSignal(controller.finished, timeout=5000):
        controller.run(script, debug=False)

    assert "None" in "".join(chunks)


def test_cwd_is_the_scripts_own_directory(qtbot, tmp_path):
    script = _write_script(tmp_path, "import os; print(os.getcwd())")
    controller = RunController()
    chunks: list[str] = []
    controller.outputReceived.connect(chunks.append)

    with qtbot.waitSignal(controller.finished, timeout=5000):
        controller.run(script)

    output = "".join(chunks).strip()
    assert os.path.realpath(output) == os.path.realpath(str(tmp_path))


def test_stop_terminates_a_running_process(qtbot, tmp_path):
    script = _write_script(tmp_path, "import time; time.sleep(30)")
    controller = RunController()

    with qtbot.waitSignal(controller.started, timeout=5000):
        controller.run(script)
    assert controller.is_running is True

    with qtbot.waitSignal(controller.finished, timeout=5000):
        controller.stop()
    assert controller.is_running is False


def test_is_running_false_before_any_run():
    controller = RunController()
    assert controller.is_running is False
