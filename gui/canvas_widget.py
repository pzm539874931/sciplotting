"""
Canvas widget - displays the matplotlib figure preview inside the Qt GUI.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt


class CanvasWidget(QWidget):
    """Widget that displays a matplotlib figure as a QPixmap."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel("Preview will appear here")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet(
            "QLabel { background-color: #f5f5f5; border: 1px solid #ccc; border-radius: 4px; }"
        )
        layout.addWidget(self.image_label)

        self._current_pixmap: QPixmap | None = None

    def update_figure(self, png_bytes: bytes):
        """Update the displayed figure from PNG bytes."""
        if not png_bytes:
            self.image_label.setText("No preview available")
            self._current_pixmap = None
            return

        img = QImage.fromData(png_bytes)
        pixmap = QPixmap.fromImage(img)
        self._current_pixmap = pixmap
        self._fit_pixmap()

    def _fit_pixmap(self):
        if self._current_pixmap is None:
            return
        scaled = self._current_pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_pixmap()
