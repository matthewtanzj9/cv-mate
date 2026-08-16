"""``RunController``: runs a saved script as a real subprocess.

Uses ``QProcess`` rather than an in-process thread — a user script can
crash, hang, or block (e.g. on ``wait_for_appear``), and a subprocess is
independently killable without taking the GUI down with it. ``QProcess``
also integrates with Qt's event loop for non-blocking, incremental output
streaming (no manual polling/bridging thread needed).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

STOP_GRACE_MS = 2000


class RunController(QObject):
    outputReceived = Signal(str)
    started = Signal()
    finished = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process: QProcess | None = None
        self._kill_timer: QTimer | None = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def run(self, script_path: Path, *, debug: bool = False, debug_save: bool = False) -> None:
        """Launch ``sys.executable <script_path>`` with cwd set to the
        script's own directory (matching the images/ save convention and
        cvmate's own asset-resolution cwd fallback), and CVMATE_DEBUG /
        CVMATE_DEBUG_SAVE set in the child's environment per the flags —
        this directly mirrors cvmate.config.DebugConfig.from_env(), no new
        debug mechanism is invented here.
        """
        if self.is_running:
            return

        process = QProcess(self)
        process.setProgram(sys.executable)
        process.setArguments([str(script_path)])
        process.setWorkingDirectory(str(script_path.parent))
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        env = QProcessEnvironment.systemEnvironment()
        if debug:
            env.insert("CVMATE_DEBUG", "1")
        if debug_save:
            env.insert("CVMATE_DEBUG_SAVE", "1")
        process.setProcessEnvironment(env)

        process.readyReadStandardOutput.connect(self._on_ready_read)
        process.finished.connect(self._on_finished)

        self._process = process
        process.start()
        self.started.emit()

    def stop(self) -> None:
        """Ask the running process to terminate gracefully (lets any
        script `finally:` cleanup run); force-kill it if it hasn't exited
        within STOP_GRACE_MS.
        """
        if not self.is_running:
            return
        assert self._process is not None
        self._process.terminate()

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self._force_kill)
        timer.start(STOP_GRACE_MS)
        self._kill_timer = timer

    def _force_kill(self) -> None:
        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()

    def _on_ready_read(self) -> None:
        if self._process is None:
            return
        chunk = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if chunk:
            self.outputReceived.emit(chunk)

    def _on_finished(self, exit_code: int, exit_status) -> None:
        if self._kill_timer is not None:
            self._kill_timer.stop()
            self._kill_timer = None
        self._process = None
        self.finished.emit(exit_code)
