"""
Stats panel — Prism-style statistical comparison configuration.
Lets users select a test, comparison mode, and display mode,
then shows the full results summary and controls significance bracket display.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QGroupBox,
    QCheckBox, QTextEdit, QSpinBox, QPushButton, QLabel,
    QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt

from core.stats_engine import (
    STAT_TESTS, POSTHOC_METHODS, COMPARE_MODES, DISPLAY_MODES,
    StatsResult,
)


class StatsPanel(QWidget):
    """Panel for configuring and displaying statistical tests."""

    stats_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ---- Test selection ----
        test_group = QGroupBox("Statistical Test")
        test_layout = QFormLayout(test_group)

        self.test_combo = QComboBox()
        self.test_combo.addItems(STAT_TESTS)
        self.test_combo.currentIndexChanged.connect(self._on_test_change)
        test_layout.addRow("Test:", self.test_combo)

        self.posthoc_combo = QComboBox()
        self.posthoc_combo.addItems(POSTHOC_METHODS)
        self.posthoc_combo.currentIndexChanged.connect(lambda: self.stats_changed.emit())
        test_layout.addRow("Post-hoc:", self.posthoc_combo)

        self.compare_combo = QComboBox()
        self.compare_combo.addItems(COMPARE_MODES)
        self.compare_combo.currentIndexChanged.connect(self._on_compare_change)
        test_layout.addRow("Compare:", self.compare_combo)

        self.control_spin = QSpinBox()
        self.control_spin.setRange(0, 99)
        self.control_spin.setValue(0)
        self.control_spin.setPrefix("Group #")
        self.control_spin.setToolTip("0-based index of the control group (first group = 0)")
        self.control_spin.valueChanged.connect(lambda: self.stats_changed.emit())
        self.control_label = QLabel("Control:")
        test_layout.addRow(self.control_label, self.control_spin)

        layout.addWidget(test_group)

        # ---- Display options ----
        disp_group = QGroupBox("Display")
        disp_layout = QFormLayout(disp_group)

        self.display_combo = QComboBox()
        self.display_combo.addItems(DISPLAY_MODES)
        self.display_combo.currentIndexChanged.connect(lambda: self.stats_changed.emit())
        disp_layout.addRow("P-value format:", self.display_combo)

        self.show_ns_check = QCheckBox("Show ns (not significant)")
        self.show_ns_check.setChecked(False)
        self.show_ns_check.toggled.connect(lambda: self.stats_changed.emit())
        disp_layout.addRow(self.show_ns_check)

        self.bracket_check = QCheckBox("Show brackets")
        self.bracket_check.setChecked(True)
        self.bracket_check.toggled.connect(lambda: self.stats_changed.emit())
        disp_layout.addRow(self.bracket_check)

        layout.addWidget(disp_group)

        # ---- Results ----
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(180)
        self.results_text.setStyleSheet(
            "QTextEdit { font-family: 'Menlo', 'Consolas', monospace; font-size: 11px; }"
        )
        self.results_text.setPlaceholderText("Select a test and render to see results...")
        results_layout.addWidget(self.results_text)
        layout.addWidget(results_group)

        layout.addStretch()

        # Initial visibility
        self._on_test_change()
        self._on_compare_change()

    def _on_test_change(self):
        test = self.test_combo.currentText()
        is_multi = test in ("One-way ANOVA", "Kruskal-Wallis")
        self.posthoc_combo.setEnabled(is_multi)
        self.compare_combo.setEnabled(is_multi)
        self.control_spin.setEnabled(is_multi and self.compare_combo.currentText() == "Compare to control")
        self.control_label.setEnabled(self.control_spin.isEnabled())
        self.stats_changed.emit()

    def _on_compare_change(self):
        is_ctrl = self.compare_combo.currentText() == "Compare to control"
        test = self.test_combo.currentText()
        is_multi = test in ("One-way ANOVA", "Kruskal-Wallis")
        self.control_spin.setEnabled(is_ctrl and is_multi)
        self.control_label.setEnabled(self.control_spin.isEnabled())
        self.stats_changed.emit()

    # ---- Getters ----

    def get_test_name(self) -> str:
        return self.test_combo.currentText()

    def get_posthoc(self) -> str:
        return self.posthoc_combo.currentText()

    def get_compare_mode(self) -> str:
        return self.compare_combo.currentText()

    def get_control_index(self) -> int:
        return self.control_spin.value()

    def get_display_mode(self) -> str:
        return self.display_combo.currentText()

    def get_show_ns(self) -> bool:
        return self.show_ns_check.isChecked()

    def get_show_brackets(self) -> bool:
        return self.bracket_check.isChecked()

    def set_results(self, result: StatsResult):
        """Display the analysis results."""
        self.results_text.setPlainText(result.summary or "No results.")

    def get_stats_config(self) -> dict:
        """Return all stats configuration as a dict."""
        return {
            "test": self.get_test_name(),
            "posthoc": self.get_posthoc(),
            "compare_mode": self.get_compare_mode(),
            "control_index": self.get_control_index(),
            "display_mode": self.get_display_mode(),
            "show_ns": self.get_show_ns(),
            "show_brackets": self.get_show_brackets(),
        }
