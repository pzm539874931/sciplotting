"""
Config panel - provides UI controls for all plot configuration options.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QDoubleSpinBox, QSpinBox, QCheckBox, QGroupBox, QScrollArea,
    QHBoxLayout, QPushButton, QColorDialog, QLabel,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor

from core.plot_engine import PlotConfig, PLOT_TYPES, STYLE_PRESETS, EXPORT_FORMATS


class ConfigPanel(QWidget):
    """Panel for configuring plot appearance and parameters."""

    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QVBoxLayout(inner)
        form.setContentsMargins(4, 4, 4, 4)

        # --- Plot type & style ---
        type_group = QGroupBox("Plot Type & Style")
        type_layout = QFormLayout(type_group)

        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(PLOT_TYPES)
        self.plot_type_combo.currentTextChanged.connect(lambda: self.config_changed.emit())
        type_layout.addRow("Plot Type:", self.plot_type_combo)

        self.style_combo = QComboBox()
        self.style_combo.addItems(list(STYLE_PRESETS.keys()))
        self.style_combo.currentTextChanged.connect(lambda: self.config_changed.emit())
        type_layout.addRow("Style Preset:", self.style_combo)

        form.addWidget(type_group)

        # --- Labels ---
        label_group = QGroupBox("Labels")
        label_layout = QFormLayout(label_group)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Figure title")
        self.title_edit.textChanged.connect(lambda: self.config_changed.emit())
        label_layout.addRow("Title:", self.title_edit)

        self.xlabel_edit = QLineEdit()
        self.xlabel_edit.setPlaceholderText("X-axis label")
        self.xlabel_edit.textChanged.connect(lambda: self.config_changed.emit())
        label_layout.addRow("X Label:", self.xlabel_edit)

        self.ylabel_edit = QLineEdit()
        self.ylabel_edit.setPlaceholderText("Y-axis label")
        self.ylabel_edit.textChanged.connect(lambda: self.config_changed.emit())
        label_layout.addRow("Y Label:", self.ylabel_edit)

        form.addWidget(label_group)

        # --- Figure size ---
        size_group = QGroupBox("Figure Size")
        size_layout = QFormLayout(size_group)

        self.fig_width_spin = QDoubleSpinBox()
        self.fig_width_spin.setRange(2, 20)
        self.fig_width_spin.setValue(6.0)
        self.fig_width_spin.setSingleStep(0.5)
        self.fig_width_spin.setSuffix(" in")
        self.fig_width_spin.valueChanged.connect(lambda: self.config_changed.emit())
        size_layout.addRow("Width:", self.fig_width_spin)

        self.fig_height_spin = QDoubleSpinBox()
        self.fig_height_spin.setRange(2, 20)
        self.fig_height_spin.setValue(4.5)
        self.fig_height_spin.setSingleStep(0.5)
        self.fig_height_spin.setSuffix(" in")
        self.fig_height_spin.valueChanged.connect(lambda: self.config_changed.emit())
        size_layout.addRow("Height:", self.fig_height_spin)

        # Quick presets
        preset_row = QHBoxLayout()
        for label, w, h in [("3.5×2.5 (1-col)", 3.5, 2.5),
                             ("6×4.5 (2-col)", 6.0, 4.5),
                             ("7×5 (full)", 7.0, 5.0)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, ww=w, hh=h: self._set_size(ww, hh))
            preset_row.addWidget(btn)
        size_layout.addRow("Quick:", preset_row)

        form.addWidget(size_group)

        # --- Appearance ---
        appear_group = QGroupBox("Appearance")
        appear_layout = QFormLayout(appear_group)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 32)
        self.font_size_spin.setValue(12)
        self.font_size_spin.valueChanged.connect(lambda: self.config_changed.emit())
        appear_layout.addRow("Font Size:", self.font_size_spin)

        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 5.0)
        self.linewidth_spin.setValue(1.5)
        self.linewidth_spin.setSingleStep(0.25)
        self.linewidth_spin.valueChanged.connect(lambda: self.config_changed.emit())
        appear_layout.addRow("Line Width:", self.linewidth_spin)

        self.marker_size_spin = QDoubleSpinBox()
        self.marker_size_spin.setRange(0, 15)
        self.marker_size_spin.setValue(5.0)
        self.marker_size_spin.setSingleStep(0.5)
        self.marker_size_spin.valueChanged.connect(lambda: self.config_changed.emit())
        appear_layout.addRow("Marker Size:", self.marker_size_spin)

        self.marker_combo = QComboBox()
        markers = ["o", "s", "^", "v", "D", "x", "+", "*", ".", "None"]
        self.marker_combo.addItems(markers)
        self.marker_combo.currentTextChanged.connect(lambda: self.config_changed.emit())
        appear_layout.addRow("Marker:", self.marker_combo)

        self.colormap_combo = QComboBox()
        cmaps = ["viridis", "plasma", "inferno", "magma", "cividis",
                 "coolwarm", "RdBu", "Spectral", "YlGnBu", "hot"]
        self.colormap_combo.addItems(cmaps)
        self.colormap_combo.currentTextChanged.connect(lambda: self.config_changed.emit())
        appear_layout.addRow("Colormap:", self.colormap_combo)

        form.addWidget(appear_group)

        # --- Axis options ---
        axis_group = QGroupBox("Axis Options")
        axis_layout = QFormLayout(axis_group)

        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.toggled.connect(lambda: self.config_changed.emit())
        axis_layout.addRow(self.grid_check)

        self.logx_check = QCheckBox("Log Scale X")
        self.logx_check.toggled.connect(lambda: self.config_changed.emit())
        axis_layout.addRow(self.logx_check)

        self.logy_check = QCheckBox("Log Scale Y")
        self.logy_check.toggled.connect(lambda: self.config_changed.emit())
        axis_layout.addRow(self.logy_check)

        self.legend_check = QCheckBox("Show Legend")
        self.legend_check.setChecked(True)
        self.legend_check.toggled.connect(lambda: self.config_changed.emit())
        axis_layout.addRow(self.legend_check)

        self.legend_loc_combo = QComboBox()
        self.legend_loc_combo.addItems([
            "best", "upper right", "upper left", "lower left", "lower right",
            "center left", "center right", "upper center", "lower center", "center",
        ])
        self.legend_loc_combo.currentTextChanged.connect(lambda: self.config_changed.emit())
        axis_layout.addRow("Legend Loc:", self.legend_loc_combo)

        self.tight_layout_check = QCheckBox("Tight Layout")
        self.tight_layout_check.setChecked(True)
        self.tight_layout_check.toggled.connect(lambda: self.config_changed.emit())
        axis_layout.addRow(self.tight_layout_check)

        form.addWidget(axis_group)

        # --- Histogram / Bar specific ---
        special_group = QGroupBox("Type-Specific Options")
        special_layout = QFormLayout(special_group)

        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(5, 200)
        self.bins_spin.setValue(20)
        self.bins_spin.valueChanged.connect(lambda: self.config_changed.emit())
        special_layout.addRow("Hist Bins:", self.bins_spin)

        self.bar_width_spin = QDoubleSpinBox()
        self.bar_width_spin.setRange(0.1, 1.0)
        self.bar_width_spin.setValue(0.6)
        self.bar_width_spin.setSingleStep(0.1)
        self.bar_width_spin.valueChanged.connect(lambda: self.config_changed.emit())
        special_layout.addRow("Bar Width:", self.bar_width_spin)

        self.capsize_spin = QDoubleSpinBox()
        self.capsize_spin.setRange(0, 10)
        self.capsize_spin.setValue(3.0)
        self.capsize_spin.setSingleStep(0.5)
        self.capsize_spin.valueChanged.connect(lambda: self.config_changed.emit())
        special_layout.addRow("Errorbar Cap:", self.capsize_spin)

        self.show_points_check = QCheckBox("Show Individual Points")
        self.show_points_check.setChecked(True)
        self.show_points_check.setToolTip("Prism-style: overlay individual replicate data points on bar/errorbar charts")
        self.show_points_check.toggled.connect(lambda: self.config_changed.emit())
        special_layout.addRow(self.show_points_check)

        form.addWidget(special_group)

        # --- Background ---
        bg_group = QGroupBox("Background")
        bg_layout = QFormLayout(bg_group)

        # Figure background color
        fig_bg_row = QHBoxLayout()
        self.fig_bg_btn = QPushButton()
        self.fig_bg_btn.setFixedSize(60, 24)
        self._fig_bg_color = "#FFFFFF"
        self._update_color_btn(self.fig_bg_btn, self._fig_bg_color)
        self.fig_bg_btn.clicked.connect(lambda: self._pick_color("fig_bg"))
        fig_bg_row.addWidget(self.fig_bg_btn)
        self.fig_bg_preset = QComboBox()
        self.fig_bg_preset.addItems(["White", "Light Gray", "Dark", "Transparent"])
        self.fig_bg_preset.currentTextChanged.connect(self._on_fig_bg_preset)
        fig_bg_row.addWidget(self.fig_bg_preset)
        bg_layout.addRow("Figure BG:", fig_bg_row)

        # Plot area background color
        ax_bg_row = QHBoxLayout()
        self.ax_bg_btn = QPushButton()
        self.ax_bg_btn.setFixedSize(60, 24)
        self._ax_bg_color = "#FFFFFF"
        self._update_color_btn(self.ax_bg_btn, self._ax_bg_color)
        self.ax_bg_btn.clicked.connect(lambda: self._pick_color("ax_bg"))
        ax_bg_row.addWidget(self.ax_bg_btn)
        self.ax_bg_preset = QComboBox()
        self.ax_bg_preset.addItems(["White", "Light Gray", "Cream", "Light Blue"])
        self.ax_bg_preset.currentTextChanged.connect(self._on_ax_bg_preset)
        ax_bg_row.addWidget(self.ax_bg_preset)
        bg_layout.addRow("Plot Area BG:", ax_bg_row)

        # Gradient option
        self.use_gradient_check = QCheckBox("Use Gradient Background")
        self.use_gradient_check.toggled.connect(self._on_gradient_toggle)
        bg_layout.addRow(self.use_gradient_check)

        # Gradient start color
        grad_start_row = QHBoxLayout()
        self.grad_start_btn = QPushButton()
        self.grad_start_btn.setFixedSize(60, 24)
        self._grad_start_color = "#FFFFFF"
        self._update_color_btn(self.grad_start_btn, self._grad_start_color)
        self.grad_start_btn.clicked.connect(lambda: self._pick_color("grad_start"))
        self.grad_start_btn.setEnabled(False)
        grad_start_row.addWidget(self.grad_start_btn)
        grad_start_row.addWidget(QLabel("Start"))
        bg_layout.addRow("Gradient:", grad_start_row)

        # Gradient end color
        grad_end_row = QHBoxLayout()
        self.grad_end_btn = QPushButton()
        self.grad_end_btn.setFixedSize(60, 24)
        self._grad_end_color = "#E0E0E0"
        self._update_color_btn(self.grad_end_btn, self._grad_end_color)
        self.grad_end_btn.clicked.connect(lambda: self._pick_color("grad_end"))
        self.grad_end_btn.setEnabled(False)
        grad_end_row.addWidget(self.grad_end_btn)
        grad_end_row.addWidget(QLabel("End"))
        bg_layout.addRow("", grad_end_row)

        # Gradient direction
        self.grad_dir_combo = QComboBox()
        self.grad_dir_combo.addItems(["Vertical", "Horizontal"])
        self.grad_dir_combo.currentTextChanged.connect(lambda: self.config_changed.emit())
        self.grad_dir_combo.setEnabled(False)
        bg_layout.addRow("Direction:", self.grad_dir_combo)

        form.addWidget(bg_group)

        form.addStretch()

        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _set_size(self, w, h):
        self.fig_width_spin.setValue(w)
        self.fig_height_spin.setValue(h)

    def _update_color_btn(self, btn: QPushButton, color: str):
        """Update button style to show color."""
        qc = QColor(color)
        brightness = (qc.red() * 299 + qc.green() * 587 + qc.blue() * 114) / 1000
        text_color = "white" if brightness < 128 else "black"
        btn.setStyleSheet(
            f"background-color: {color}; color: {text_color}; "
            f"border: 1px solid #888; border-radius: 3px;"
        )
        btn.setText(color[:7])

    def _pick_color(self, which: str):
        """Open color picker for specified button."""
        if which == "fig_bg":
            current = QColor(self._fig_bg_color)
        elif which == "ax_bg":
            current = QColor(self._ax_bg_color)
        elif which == "grad_start":
            current = QColor(self._grad_start_color)
        elif which == "grad_end":
            current = QColor(self._grad_end_color)
        else:
            return

        color = QColorDialog.getColor(current, self, "Select Color")
        if color.isValid():
            hex_color = color.name()
            if which == "fig_bg":
                self._fig_bg_color = hex_color
                self._update_color_btn(self.fig_bg_btn, hex_color)
            elif which == "ax_bg":
                self._ax_bg_color = hex_color
                self._update_color_btn(self.ax_bg_btn, hex_color)
            elif which == "grad_start":
                self._grad_start_color = hex_color
                self._update_color_btn(self.grad_start_btn, hex_color)
            elif which == "grad_end":
                self._grad_end_color = hex_color
                self._update_color_btn(self.grad_end_btn, hex_color)
            self.config_changed.emit()

    def _on_fig_bg_preset(self, preset: str):
        """Apply figure background preset."""
        presets = {
            "White": "#FFFFFF",
            "Light Gray": "#F5F5F5",
            "Dark": "#2D2D2D",
            "Transparent": "#FFFFFF",  # Will be handled specially in export
        }
        if preset in presets:
            self._fig_bg_color = presets[preset]
            self._update_color_btn(self.fig_bg_btn, self._fig_bg_color)
            self.config_changed.emit()

    def _on_ax_bg_preset(self, preset: str):
        """Apply plot area background preset."""
        presets = {
            "White": "#FFFFFF",
            "Light Gray": "#F8F8F8",
            "Cream": "#FFFEF0",
            "Light Blue": "#F0F8FF",
        }
        if preset in presets:
            self._ax_bg_color = presets[preset]
            self._update_color_btn(self.ax_bg_btn, self._ax_bg_color)
            self.config_changed.emit()

    def _on_gradient_toggle(self, checked: bool):
        """Toggle gradient controls enabled state."""
        self.grad_start_btn.setEnabled(checked)
        self.grad_end_btn.setEnabled(checked)
        self.grad_dir_combo.setEnabled(checked)
        self.ax_bg_btn.setEnabled(not checked)
        self.ax_bg_preset.setEnabled(not checked)
        self.config_changed.emit()

    def get_config(self) -> PlotConfig:
        """Build a PlotConfig from current UI state."""
        cfg = PlotConfig()
        cfg.plot_type = self.plot_type_combo.currentText()
        cfg.style_preset = self.style_combo.currentText()
        cfg.title = self.title_edit.text()
        cfg.xlabel = self.xlabel_edit.text()
        cfg.ylabel = self.ylabel_edit.text()
        cfg.fig_width = self.fig_width_spin.value()
        cfg.fig_height = self.fig_height_spin.value()
        cfg.font_size = self.font_size_spin.value()
        cfg.line_width = self.linewidth_spin.value()
        cfg.marker_size = self.marker_size_spin.value()
        marker = self.marker_combo.currentText()
        cfg.marker_style = "" if marker == "None" else marker
        cfg.grid = self.grid_check.isChecked()
        cfg.log_x = self.logx_check.isChecked()
        cfg.log_y = self.logy_check.isChecked()
        cfg.show_legend = self.legend_check.isChecked()
        cfg.legend_loc = self.legend_loc_combo.currentText()
        cfg.tight_layout = self.tight_layout_check.isChecked()
        cfg.bins = self.bins_spin.value()
        cfg.bar_width = self.bar_width_spin.value()
        cfg.capsize = self.capsize_spin.value()
        cfg.show_individual_points = self.show_points_check.isChecked()
        cfg.colormap = self.colormap_combo.currentText()
        # Background options
        cfg.fig_facecolor = self._fig_bg_color
        cfg.ax_facecolor = self._ax_bg_color
        cfg.use_gradient = self.use_gradient_check.isChecked()
        cfg.gradient_start = self._grad_start_color
        cfg.gradient_end = self._grad_end_color
        cfg.gradient_direction = self.grad_dir_combo.currentText().lower()
        return cfg

    def set_config(self, cfg: PlotConfig):
        """Restore UI state from a PlotConfig (used when loading templates)."""
        self.plot_type_combo.setCurrentText(cfg.plot_type)
        self.style_combo.setCurrentText(cfg.style_preset)
        self.title_edit.setText(cfg.title)
        self.xlabel_edit.setText(cfg.xlabel)
        self.ylabel_edit.setText(cfg.ylabel)
        self.fig_width_spin.setValue(cfg.fig_width)
        self.fig_height_spin.setValue(cfg.fig_height)
        self.font_size_spin.setValue(cfg.font_size)
        self.linewidth_spin.setValue(cfg.line_width)
        self.marker_size_spin.setValue(cfg.marker_size)
        self.marker_combo.setCurrentText(cfg.marker_style or "None")
        self.grid_check.setChecked(cfg.grid)
        self.logx_check.setChecked(cfg.log_x)
        self.logy_check.setChecked(cfg.log_y)
        self.legend_check.setChecked(cfg.show_legend)
        self.legend_loc_combo.setCurrentText(cfg.legend_loc)
        self.tight_layout_check.setChecked(cfg.tight_layout)
        self.bins_spin.setValue(cfg.bins)
        self.bar_width_spin.setValue(cfg.bar_width)
        self.capsize_spin.setValue(cfg.capsize)
        self.show_points_check.setChecked(cfg.show_individual_points)
        self.colormap_combo.setCurrentText(cfg.colormap)
        # Background options
        self._fig_bg_color = cfg.fig_facecolor
        self._update_color_btn(self.fig_bg_btn, self._fig_bg_color)
        self._ax_bg_color = cfg.ax_facecolor
        self._update_color_btn(self.ax_bg_btn, self._ax_bg_color)
        self.use_gradient_check.setChecked(cfg.use_gradient)
        self._grad_start_color = cfg.gradient_start
        self._update_color_btn(self.grad_start_btn, self._grad_start_color)
        self._grad_end_color = cfg.gradient_end
        self._update_color_btn(self.grad_end_btn, self._grad_end_color)
        self.grad_dir_combo.setCurrentText(cfg.gradient_direction.title())
