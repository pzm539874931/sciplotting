"""
Layout Composer - arranges multiple figures into a composite layout
for publication-ready multi-panel figures (e.g. Figure 1A, 1B, 1C...).

Supports grid layout with configurable rows/cols, panel labels (A, B, C...),
spacing, and export as a single combined figure.
"""

import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QGroupBox,
    QFormLayout, QFileDialog, QMessageBox, QScrollArea, QSizePolicy,
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSignal

from core.plot_engine import EXPORT_FORMATS


class LayoutComposer(QWidget):
    """
    Composite layout editor that arranges multiple sub-figures
    into a grid and exports them as one combined figure.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._figure_pngs: dict[str, bytes] = {}  # name -> PNG bytes
        self._figure_order: list[str] = []         # ordered names

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ---- Controls ----
        ctrl_group = QGroupBox("Layout Settings")
        ctrl_layout = QFormLayout(ctrl_group)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 6)
        self.rows_spin.setValue(1)
        self.rows_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Rows:", self.rows_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 6)
        self.cols_spin.setValue(2)
        self.cols_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Columns:", self.cols_spin)

        self.total_width_spin = QDoubleSpinBox()
        self.total_width_spin.setRange(4, 30)
        self.total_width_spin.setValue(12.0)
        self.total_width_spin.setSingleStep(0.5)
        self.total_width_spin.setSuffix(" in")
        self.total_width_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Total Width:", self.total_width_spin)

        self.total_height_spin = QDoubleSpinBox()
        self.total_height_spin.setRange(3, 20)
        self.total_height_spin.setValue(5.0)
        self.total_height_spin.setSingleStep(0.5)
        self.total_height_spin.setSuffix(" in")
        self.total_height_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Total Height:", self.total_height_spin)

        self.hspace_spin = QDoubleSpinBox()
        self.hspace_spin.setRange(0.0, 1.0)
        self.hspace_spin.setValue(0.3)
        self.hspace_spin.setSingleStep(0.05)
        self.hspace_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("H-Space:", self.hspace_spin)

        self.wspace_spin = QDoubleSpinBox()
        self.wspace_spin.setRange(0.0, 1.0)
        self.wspace_spin.setValue(0.3)
        self.wspace_spin.setSingleStep(0.05)
        self.wspace_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("W-Space:", self.wspace_spin)

        self.label_check = QCheckBox("Show Panel Labels (A, B, C...)")
        self.label_check.setChecked(True)
        self.label_check.toggled.connect(self._refresh)
        ctrl_layout.addRow(self.label_check)

        self.label_size_spin = QSpinBox()
        self.label_size_spin.setRange(10, 36)
        self.label_size_spin.setValue(18)
        self.label_size_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Label Size:", self.label_size_spin)

        self.label_x_spin = QDoubleSpinBox()
        self.label_x_spin.setRange(-0.5, 1.5)
        self.label_x_spin.setValue(-0.05)
        self.label_x_spin.setSingleStep(0.01)
        self.label_x_spin.setDecimals(3)
        self.label_x_spin.setToolTip("X position of panel label in axes coordinates (0=left edge, 1=right edge)")
        self.label_x_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Label X:", self.label_x_spin)

        self.label_y_spin = QDoubleSpinBox()
        self.label_y_spin.setRange(-0.5, 1.5)
        self.label_y_spin.setValue(1.05)
        self.label_y_spin.setSingleStep(0.01)
        self.label_y_spin.setDecimals(3)
        self.label_y_spin.setToolTip("Y position of panel label in axes coordinates (0=bottom edge, 1=top edge)")
        self.label_y_spin.valueChanged.connect(self._refresh)
        ctrl_layout.addRow("Label Y:", self.label_y_spin)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(300)
        ctrl_layout.addRow("Export DPI:", self.dpi_spin)

        layout.addWidget(ctrl_group)

        # Quick presets
        preset_row = QHBoxLayout()
        for label, r, c, w, h in [
            ("1x2", 1, 2, 12, 5), ("2x2", 2, 2, 12, 9),
            ("1x3", 1, 3, 15, 5), ("2x3", 2, 3, 15, 9),
            ("3x1", 3, 1, 6, 14),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(
                lambda checked, rr=r, cc=c, ww=w, hh=h: self._set_preset(rr, cc, ww, hh)
            )
            preset_row.addWidget(btn)
        layout.addLayout(preset_row)

        # ---- Preview ----
        self.preview_label = QLabel("Compose multiple figures into one layout.\n"
                                    "Add figures in the tabs above, then preview here.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet(
            "QLabel { background: #f5f5f5; border: 1px solid #ccc; border-radius: 4px; }"
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview_label)
        layout.addWidget(scroll, stretch=1)

        # ---- Export button ----
        export_row = QHBoxLayout()
        export_row.addStretch()

        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(list(EXPORT_FORMATS.keys()))
        export_row.addWidget(QLabel("Format:"))
        export_row.addWidget(self.fmt_combo)

        self.export_btn = QPushButton("Export Composed Figure")
        self.export_btn.clicked.connect(self._export)
        export_row.addWidget(self.export_btn)
        layout.addLayout(export_row)

        self._current_pixmap = None

    def _set_preset(self, r, c, w, h):
        self.rows_spin.setValue(r)
        self.cols_spin.setValue(c)
        self.total_width_spin.setValue(w)
        self.total_height_spin.setValue(h)

    def update_figures(self, figure_pngs: dict[str, bytes], figure_order: list[str]):
        """Called by MainWindow whenever figure tabs change."""
        self._figure_pngs = figure_pngs
        self._figure_order = figure_order
        self._refresh()

    def _refresh(self):
        """Re-render the composite preview."""
        if not self._figure_pngs or not self._figure_order:
            self.preview_label.setText("No figures to compose. Create figures in the tabs above.")
            self._current_pixmap = None
            return

        png = self._render_composite(dpi=100)
        if not png:
            return

        img = QImage.fromData(png)
        pixmap = QPixmap.fromImage(img)
        self._current_pixmap = pixmap
        scaled = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _render_composite(self, dpi: int = 100) -> bytes:
        """Compose all sub-figure PNGs into one matplotlib figure."""
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        total_w = self.total_width_spin.value()
        total_h = self.total_height_spin.value()
        hspace = self.hspace_spin.value()
        wspace = self.wspace_spin.value()
        show_labels = self.label_check.isChecked()
        label_size = self.label_size_spin.value()
        label_x = self.label_x_spin.value()
        label_y = self.label_y_spin.value()

        fig = plt.figure(figsize=(total_w, total_h), dpi=dpi)
        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=hspace, wspace=wspace)

        panel_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for idx, name in enumerate(self._figure_order):
            if idx >= rows * cols:
                break
            png_data = self._figure_pngs.get(name, b"")
            if not png_data:
                continue

            row_idx = idx // cols
            col_idx = idx % cols
            ax = fig.add_subplot(gs[row_idx, col_idx])

            # Load sub-figure PNG as image
            img = Image.open(io.BytesIO(png_data))
            ax.imshow(np.array(img))
            ax.axis("off")

            if show_labels and idx < len(panel_labels):
                ax.text(
                    label_x, label_y, panel_labels[idx],
                    transform=ax.transAxes,
                    fontsize=label_size, fontweight="bold",
                    va="bottom", ha="right",
                )

        # Render to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _export(self):
        """Export the composite figure."""
        if not self._figure_pngs:
            QMessageBox.warning(self, "Warning", "No figures to export.")
            return

        fmt_key = self.fmt_combo.currentText()
        fmt_info = EXPORT_FORMATS[fmt_key]
        ext = fmt_info["ext"]
        export_dpi = self.dpi_spin.value()

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Composed Figure", f"composed_figure{ext}",
            f"Figure (*{ext});;All Files (*)"
        )
        if not path:
            return

        try:
            png = self._render_composite(dpi=export_dpi)
            if fmt_info["ext"] == ".png":
                Path(path).write_bytes(png)
            else:
                # For PDF/SVG/EPS/TIFF, re-render with matplotlib savefig
                self._export_vector(path, fmt_key, export_dpi)
            QMessageBox.information(self, "Success", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

    def _export_vector(self, path: str, fmt_key: str, dpi: int):
        """Export as vector (PDF/SVG/EPS) or TIFF."""
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        total_w = self.total_width_spin.value()
        total_h = self.total_height_spin.value()
        hspace = self.hspace_spin.value()
        wspace = self.wspace_spin.value()
        show_labels = self.label_check.isChecked()
        label_size = self.label_size_spin.value()
        label_x = self.label_x_spin.value()
        label_y = self.label_y_spin.value()

        fmt_info = EXPORT_FORMATS[fmt_key]

        fig = plt.figure(figsize=(total_w, total_h), dpi=dpi)
        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=hspace, wspace=wspace)
        panel_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for idx, name in enumerate(self._figure_order):
            if idx >= rows * cols:
                break
            png_data = self._figure_pngs.get(name, b"")
            if not png_data:
                continue
            row_idx = idx // cols
            col_idx = idx % cols
            ax = fig.add_subplot(gs[row_idx, col_idx])
            img = Image.open(io.BytesIO(png_data))
            ax.imshow(np.array(img))
            ax.axis("off")
            if show_labels and idx < len(panel_labels):
                ax.text(
                    label_x, label_y, panel_labels[idx],
                    transform=ax.transAxes,
                    fontsize=label_size, fontweight="bold",
                    va="bottom", ha="right",
                )

        fig.savefig(path, dpi=dpi, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_pixmap:
            scaled = self._current_pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)
