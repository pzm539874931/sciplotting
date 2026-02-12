"""
Fitting Panel - UI for curve fitting and data analysis.

Allows users to select a fitting model, perform the fit, and display results.
Fitting curves are overlaid on the main plot.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QFormLayout, QTextEdit, QCheckBox,
    QSpinBox, QDoubleSpinBox, QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.fitting_engine import FittingEngine, FitResult, get_fitting_models


class FittingPanel(QWidget):
    """Panel for curve fitting controls and results."""

    fitting_changed = pyqtSignal()  # Emitted when fit settings change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result: FitResult = FitResult()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # ---- Model Selection ----
        model_group = QGroupBox("Curve Fitting")
        model_layout = QFormLayout(model_group)

        self.model_combo = QComboBox()
        self.model_combo.addItems(list(get_fitting_models().keys()))
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addRow("Model:", self.model_combo)

        self.series_combo = QComboBox()
        self.series_combo.addItem("(All Series)")
        self.series_combo.currentIndexChanged.connect(lambda: self.fitting_changed.emit())
        model_layout.addRow("Fit Series:", self.series_combo)

        layout.addWidget(model_group)

        # ---- Fit Options ----
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)

        self.show_fit_check = QCheckBox("Show Fit Curve")
        self.show_fit_check.setChecked(True)
        self.show_fit_check.toggled.connect(lambda: self.fitting_changed.emit())
        options_layout.addRow(self.show_fit_check)

        self.show_equation_check = QCheckBox("Show Equation on Plot")
        self.show_equation_check.setChecked(True)
        self.show_equation_check.toggled.connect(lambda: self.fitting_changed.emit())
        options_layout.addRow(self.show_equation_check)

        self.show_r2_check = QCheckBox("Show R² on Plot")
        self.show_r2_check.setChecked(True)
        self.show_r2_check.toggled.connect(lambda: self.fitting_changed.emit())
        options_layout.addRow(self.show_r2_check)

        self.show_residuals_check = QCheckBox("Show Residuals")
        self.show_residuals_check.setChecked(False)
        self.show_residuals_check.toggled.connect(lambda: self.fitting_changed.emit())
        options_layout.addRow(self.show_residuals_check)

        self.extrapolate_check = QCheckBox("Extrapolate Curve")
        self.extrapolate_check.setChecked(False)
        self.extrapolate_check.toggled.connect(lambda: self.fitting_changed.emit())
        options_layout.addRow(self.extrapolate_check)

        # Line style for fit
        style_row = QHBoxLayout()
        self.fit_color_combo = QComboBox()
        self.fit_color_combo.addItems(["Auto", "Red", "Blue", "Green", "Black", "Orange", "Purple"])
        self.fit_color_combo.currentIndexChanged.connect(lambda: self.fitting_changed.emit())
        style_row.addWidget(QLabel("Color:"))
        style_row.addWidget(self.fit_color_combo)

        self.fit_style_combo = QComboBox()
        self.fit_style_combo.addItems(["Solid", "Dashed", "Dotted", "Dash-Dot"])
        self.fit_style_combo.currentIndexChanged.connect(lambda: self.fitting_changed.emit())
        style_row.addWidget(QLabel("Style:"))
        style_row.addWidget(self.fit_style_combo)
        options_layout.addRow(style_row)

        layout.addWidget(options_group)

        # ---- Fit Button ----
        self.fit_btn = QPushButton("Perform Fit")
        self.fit_btn.clicked.connect(self._on_fit_clicked)
        self.fit_btn.setStyleSheet(
            "QPushButton { background: #4CAF50; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background: #45a049; }"
        )
        layout.addWidget(self.fit_btn)

        # ---- Results Display ----
        results_group = QGroupBox("Fit Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        self.results_text.setMinimumHeight(150)
        self.results_text.setPlaceholderText("Select a model and click 'Perform Fit' to see results...")
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group, stretch=1)

    def _on_model_changed(self, text):
        """Handle model selection change."""
        self.fitting_changed.emit()

    def _on_fit_clicked(self):
        """Trigger a fit operation (handled by parent)."""
        self.fitting_changed.emit()

    def update_series_list(self, series_labels: list[str]):
        """Update the series combo box with available data series."""
        current = self.series_combo.currentText()
        self.series_combo.blockSignals(True)
        self.series_combo.clear()
        self.series_combo.addItem("(All Series)")
        for label in series_labels:
            self.series_combo.addItem(label)
        # Restore selection if possible
        idx = self.series_combo.findText(current)
        if idx >= 0:
            self.series_combo.setCurrentIndex(idx)
        self.series_combo.blockSignals(False)

    def get_fitting_config(self) -> dict:
        """Return current fitting configuration."""
        color_map = {
            "Auto": None, "Red": "red", "Blue": "blue", "Green": "green",
            "Black": "black", "Orange": "orange", "Purple": "purple"
        }
        style_map = {
            "Solid": "-", "Dashed": "--", "Dotted": ":", "Dash-Dot": "-."
        }
        return {
            "model": self.model_combo.currentText(),
            "series_index": self.series_combo.currentIndex() - 1,  # -1 means all
            "show_fit": self.show_fit_check.isChecked(),
            "show_equation": self.show_equation_check.isChecked(),
            "show_r2": self.show_r2_check.isChecked(),
            "show_residuals": self.show_residuals_check.isChecked(),
            "extrapolate": self.extrapolate_check.isChecked(),
            "color": color_map.get(self.fit_color_combo.currentText()),
            "linestyle": style_map.get(self.fit_style_combo.currentText(), "-"),
        }

    def set_results(self, result: FitResult):
        """Display fit results."""
        self._current_result = result
        self.results_text.setText(result.summary())

    def get_fit_result(self) -> FitResult:
        """Return the current fit result."""
        return self._current_result

    def clear_results(self):
        """Clear the results display."""
        self._current_result = FitResult()
        self.results_text.clear()
