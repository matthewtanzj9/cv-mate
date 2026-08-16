"""Entry point for the ``cvmate-gui`` console script."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from . import theme
from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
