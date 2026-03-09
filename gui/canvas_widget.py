"""
Canvas widget - displays the matplotlib figure preview.
Supports static mode (QPixmap) and interactive mode (matplotlib FigureCanvas with zoom/pan).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QMenu, QApplication, QPushButton, QStackedWidget,
)
from PyQt6.QtGui import QPixmap, QImage, QAction
from PyQt6.QtCore import Qt, pyqtSignal

import io
import matplotlib
matplotlib.use("Agg")


class CanvasWidget(QWidget):
    """Widget that displays a matplotlib figure as a QPixmap or interactive canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Toolbar
        tb = QHBoxLayout()
        self.interactive_btn = QPushButton("🔍 Interactive")
        self.interactive_btn.setCheckable(True)
        self.interactive_btn.setChecked(False)
        self.interactive_btn.setFixedHeight(24)
        self.interactive_btn.setToolTip("Toggle interactive zoom/pan mode")
        self.interactive_btn.toggled.connect(self._toggle_interactive)
        tb.addWidget(self.interactive_btn)

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setFixedHeight(24)
        self.copy_btn.setToolTip("Copy figure to clipboard (Ctrl+Shift+C)")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        tb.addWidget(self.copy_btn)

        tb.addStretch()
        layout.addLayout(tb)

        # Stack: static image vs interactive canvas
        self._stack = QStackedWidget()

        # Static image label
        self.image_label = QLabel("Preview will appear here")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet(
            "QLabel { background-color: #f5f5f5; border: 1px solid #ccc; border-radius: 4px; }"
        )
        self.image_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.image_label.customContextMenuRequested.connect(self._show_context_menu)
        self._stack.addWidget(self.image_label)

        # Interactive canvas placeholder (created lazily)
        self._interactive_widget = None
        self._toolbar_widget = None

        layout.addWidget(self._stack)

        self._current_pixmap: QPixmap | None = None
        self._png_bytes: bytes = b""
        self._current_fig = None
        self._interactive_mode = False

    def update_figure(self, png_bytes: bytes, fig=None):
        """Update the displayed figure from PNG bytes."""
        self._current_fig = fig
        if not png_bytes:
            self.image_label.setText("No preview available")
            self._current_pixmap = None
            self._png_bytes = b""
            return

        self._png_bytes = png_bytes
        img = QImage.fromData(png_bytes)
        pixmap = QPixmap.fromImage(img)
        self._current_pixmap = pixmap

        if not self._interactive_mode:
            self._fit_pixmap()
        else:
            self._update_interactive()

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
        if not self._interactive_mode:
            self._fit_pixmap()

    def _toggle_interactive(self, checked):
        self._interactive_mode = checked
        if checked:
            self._setup_interactive()
            self._update_interactive()
            if self._interactive_widget:
                self._stack.setCurrentWidget(self._interactive_widget)
        else:
            self._stack.setCurrentWidget(self.image_label)
            self._fit_pixmap()

    def _setup_interactive(self):
        """Create interactive matplotlib canvas if not already done."""
        if self._interactive_widget is not None:
            return
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
            from matplotlib.figure import Figure

            self._mpl_fig = Figure(figsize=(6, 4.5))
            self._mpl_canvas = FigureCanvasQTAgg(self._mpl_fig)
            self._mpl_canvas.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

            container = QWidget()
            vl = QVBoxLayout(container)
            vl.setContentsMargins(0, 0, 0, 0)
            self._mpl_toolbar = NavigationToolbar2QT(self._mpl_canvas, container)
            vl.addWidget(self._mpl_toolbar)
            vl.addWidget(self._mpl_canvas)

            self._interactive_widget = container
            self._stack.addWidget(container)
        except ImportError:
            self._interactive_widget = QLabel("Interactive mode requires matplotlib Qt backend")
            self._stack.addWidget(self._interactive_widget)

    def _update_interactive(self):
        """Render the current figure onto the interactive canvas."""
        if not hasattr(self, '_mpl_canvas') or self._png_bytes is None:
            return
        try:
            from PIL import Image
            import numpy as np
            img = Image.open(io.BytesIO(self._png_bytes))
            self._mpl_fig.clear()
            ax = self._mpl_fig.add_subplot(111)
            ax.imshow(np.array(img))
            ax.axis('off')
            self._mpl_fig.tight_layout(pad=0)
            self._mpl_canvas.draw()
        except Exception:
            pass

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        copy_act = QAction("Copy to Clipboard", self)
        copy_act.triggered.connect(self.copy_to_clipboard)
        copy_act.setEnabled(self._current_pixmap is not None)
        menu.addAction(copy_act)
        menu.exec(self.image_label.mapToGlobal(pos))

    def copy_to_clipboard(self):
        """Copy current figure to system clipboard."""
        if self._current_pixmap is not None:
            QApplication.clipboard().setPixmap(self._current_pixmap)
