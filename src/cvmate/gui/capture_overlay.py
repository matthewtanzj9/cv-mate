"""``CaptureOverlay``: a frameless, translucent widget spanning every
monitor, used to click-drag select a screen region to capture as a
template image.

This widget only handles the on-screen *selection UI* — it never touches
``cvmate.capture`` itself. The actual pixel grab (via
``default_capture_backend()``) is done by ``CaptureController`` after this
widget has hidden itself, so the overlay never appears in its own capture.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

SCRIM_COLOR = QColor(0, 0, 0, 60)
SELECTION_FILL = QColor(80, 160, 255, 40)
SELECTION_BORDER = QColor(80, 160, 255, 220)


def virtual_desktop_geometry() -> QRect:
    """The union of every connected screen's geometry, in the same
    "all monitors combined" space as
    ``cvmate.capture.CaptureBackend.virtual_desktop_bbox()``.
    """
    screens = QGuiApplication.screens()
    geometry = screens[0].geometry()
    for screen in screens[1:]:
        geometry = geometry.united(screen.geometry())
    return geometry


class CaptureOverlay(QWidget):
    """Drag-select a rectangular region across the full virtual desktop."""

    regionSelected = Signal(int, int, int, int)  # left, top, width, height
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(virtual_desktop_geometry())

        self._origin: QPoint | None = None
        self._current_rect: QRect | None = None

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override naming
        painter = QPainter(self)
        painter.fillRect(self.rect(), SCRIM_COLOR)
        if self._current_rect is not None:
            painter.fillRect(self._current_rect, SELECTION_FILL)
            painter.setPen(SELECTION_BORDER)
            painter.drawRect(self._current_rect)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._origin = event.position().toPoint()
        self._current_rect = QRect(self._origin, self._origin)
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._origin is None:
            return
        self._current_rect = QRect(self._origin, event.position().toPoint()).normalized()
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._origin is None or self._current_rect is None:
            return
        rect = self._current_rect
        # Map from widget-local coordinates to virtual-desktop-absolute
        # coordinates (they differ whenever the overlay's own origin isn't
        # (0, 0), i.e. whenever the leftmost/topmost monitor isn't at the
        # desktop origin).
        top_left = self.mapToGlobal(rect.topLeft())

        self._origin = None
        self._current_rect = None

        # Hide (not just close()) before emitting, and flush the hide to the
        # compositor, so CaptureController's grab() — triggered by the
        # signal below — never sees this overlay's own pixels.
        self.hide()
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        if rect.width() < 2 or rect.height() < 2:
            self.cancelled.emit()
        else:
            self.regionSelected.emit(top_left.x(), top_left.y(), rect.width(), rect.height())
        self.close()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._origin = None
            self._current_rect = None
            self.hide()
            self.cancelled.emit()
            self.close()
        else:
            super().keyPressEvent(event)
