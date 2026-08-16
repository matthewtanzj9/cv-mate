"""Headless smoke tests for MainWindow's API reference dock panel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QTextBrowser

from cvmate.gui.main_window import MainWindow


def test_api_reference_dock_exists_and_is_docked_right(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert isinstance(window.api_reference_dock, QDockWidget)
    assert window.dockWidgetArea(window.api_reference_dock) == Qt.DockWidgetArea.RightDockWidgetArea


def test_api_reference_dock_contains_a_populated_text_browser(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    browser = window.api_reference_dock.widget()
    assert isinstance(browser, QTextBrowser)
    assert "Screen" in browser.toPlainText()
    assert "Pattern" in browser.toPlainText()


def test_view_menu_can_toggle_the_dock(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()  # a dock's isVisible() reflects the top-level window's shown state

    assert window.api_reference_dock.isVisible() is True
    window.api_reference_dock.toggleViewAction().trigger()
    assert window.api_reference_dock.isVisible() is False
