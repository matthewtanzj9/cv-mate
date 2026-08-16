"""``MainWindow``: wires the script editor, capture tool, and script runner
together into one window. Deliberately thin — most behavior lives in the
more directly-testable ``editor``, ``capture_controller``, and
``run_controller`` modules.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTextBrowser,
    QToolBar,
)

from .api_reference import render_api_reference_html
from .capture_controller import CaptureController
from .editor import ScriptEditor
from .highlighter import PythonHighlighter
from .run_controller import RunController
from .template_preview import TemplatePreviewPanel

API_REFERENCE_DOCK_WIDTH = 340

WINDOW_TITLE_SUFFIX = " — cv-mate"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.editor = ScriptEditor(self)
        self._highlighter = PythonHighlighter(self.editor.document())

        self.output_pane = QPlainTextEdit(self)
        self.output_pane.setReadOnly(True)
        self.output_pane.setPlaceholderText("Script output will appear here…")

        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.output_pane)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self.capture_controller = CaptureController(self.editor, self)
        self.run_controller = RunController(self)

        self._build_api_reference_dock()
        self._build_template_preview_dock()
        self._build_menu()
        self._build_toolbar()
        self._wire_signals()

        self.editor.titleChanged.connect(self._update_window_title)
        self._update_window_title(self.editor.title)
        self.resize(900, 700)

    # -- construction ----------------------------------------------------------

    def _build_api_reference_dock(self) -> None:
        """A read-only "API Reference" panel docked to the right, showing
        the cvmate scripting API (Screen/Region/Pattern/Match/... and their
        methods) so a script author doesn't have to alt-tab to docs while
        writing a script. Dockable/floatable/closable like any QDockWidget,
        and toggle-able from the View menu (see _build_menu)."""
        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(False)
        browser.setHtml(render_api_reference_html())

        self.api_reference_dock = QDockWidget("API Reference", self)
        self.api_reference_dock.setWidget(browser)
        self.api_reference_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.api_reference_dock)
        self.resizeDocks([self.api_reference_dock], [API_REFERENCE_DOCK_WIDTH], Qt.Orientation.Horizontal)

    def _build_template_preview_dock(self) -> None:
        """A "Template Preview" panel stacked below the API Reference dock,
        showing the actual image whatever Pattern(...) call the cursor is
        on/near refers to — updates live as you move around the script."""
        self.template_preview_panel = TemplatePreviewPanel(self.editor, self)

        self.template_preview_dock = QDockWidget("Template Preview", self)
        self.template_preview_dock.setWidget(self.template_preview_panel)
        self.template_preview_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.template_preview_dock)
        self.splitDockWidget(self.api_reference_dock, self.template_preview_dock, Qt.Orientation.Vertical)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        new_action = QAction("&New", self, shortcut="Ctrl+N", triggered=self.new_file)
        open_action = QAction("&Open…", self, shortcut="Ctrl+O", triggered=self.open_file)
        save_action = QAction("&Save", self, shortcut="Ctrl+S", triggered=self.save_file)
        save_as_action = QAction("Save &As…", self, shortcut="Ctrl+Shift+S", triggered=self.save_file_as)
        exit_action = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)

        for action in (new_action, open_action, save_action, save_as_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.api_reference_dock.toggleViewAction())
        view_menu.addAction(self.template_preview_dock.toggleViewAction())

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        self.addToolBar(toolbar)

        self.capture_action = QAction("Capture Template", self, triggered=self.capture_controller.start_capture)
        toolbar.addAction(self.capture_action)
        toolbar.addSeparator()

        self.run_action = QAction("Run", self, triggered=self._on_run_clicked)
        self.stop_action = QAction("Stop", self, triggered=self.run_controller.stop)
        self.stop_action.setEnabled(False)
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.stop_action)
        toolbar.addSeparator()

        self.debug_checkbox = QCheckBox("Debug", self)
        self.debug_save_checkbox = QCheckBox("Save annotated", self)
        toolbar.addWidget(self.debug_checkbox)
        toolbar.addWidget(self.debug_save_checkbox)

    def _wire_signals(self) -> None:
        self.run_controller.outputReceived.connect(self._append_output)
        self.run_controller.started.connect(self._on_run_started)
        self.run_controller.finished.connect(self._on_run_finished)

    # -- file menu actions -------------------------------------------------------

    def new_file(self) -> None:
        if self._confirm_discard_if_dirty():
            self.editor.new_file()

    def open_file(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        path_str, _ = QFileDialog.getOpenFileName(self, "Open Script", filter="Python Files (*.py)")
        if path_str:
            self.editor.open_file(Path(path_str))

    def save_file(self) -> None:
        if not self.editor.save():
            self.save_file_as()

    def save_file_as(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(self, "Save Script As", filter="Python Files (*.py)")
        if path_str:
            self.editor.save_as(Path(path_str))

    def _confirm_discard_if_dirty(self) -> bool:
        if not self.editor.is_dirty:
            return True
        choice = QMessageBox.question(
            self,
            "Unsaved changes",
            "This script has unsaved changes. Save before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        if choice == QMessageBox.StandardButton.Save:
            self.save_file()
            return not self.editor.is_dirty  # False if the save dialog was itself cancelled
        return True  # Discard

    # -- run/stop -----------------------------------------------------------------

    def _on_run_clicked(self) -> None:
        if self.editor.current_path is None or self.editor.is_dirty:
            self.save_file()
        if self.editor.current_path is None:
            return  # user cancelled the required save

        self.output_pane.clear()
        self.run_controller.run(
            self.editor.current_path,
            debug=self.debug_checkbox.isChecked(),
            debug_save=self.debug_save_checkbox.isChecked(),
        )

    def _on_run_started(self) -> None:
        self.run_action.setEnabled(False)
        self.stop_action.setEnabled(True)

    def _on_run_finished(self, exit_code: int) -> None:
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self._append_output(f"\n[process exited with code {exit_code}]\n")

    def _append_output(self, text: str) -> None:
        self.output_pane.moveCursor(self.output_pane.textCursor().MoveOperation.End)
        self.output_pane.insertPlainText(text)
        self.output_pane.moveCursor(self.output_pane.textCursor().MoveOperation.End)

    # -- misc --------------------------------------------------------------------

    def _update_window_title(self, title: str) -> None:
        self.setWindowTitle(f"{title}{WINDOW_TITLE_SUFFIX}")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override naming
        if self._confirm_discard_if_dirty():
            event.accept()
        else:
            event.ignore()
