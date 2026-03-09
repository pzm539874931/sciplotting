"""
Stats panel — Prism-style statistical comparison configuration.
Lets users select a test, comparison mode, and display mode,
then shows the full results summary and controls significance bracket display.
Individual comparisons can be toggled on/off for display.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QGroupBox,
    QCheckBox, QTextEdit, QSpinBox, QPushButton, QLabel,
    QHBoxLayout, QDoubleSpinBox, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import pyqtSignal, Qt

from core.stats_engine import (
    STAT_TESTS, POSTHOC_METHODS, COMPARE_MODES, DISPLAY_MODES,
    StatsResult, ComparisonResult, p_to_stars,
)


class StatsPanel(QWidget):
    """Panel for configuring and displaying statistical tests."""

    stats_changed = pyqtSignal()
    # Emitted when only visibility toggles change (no need to re-run stats)
    visibility_changed = pyqtSignal()

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

        # Bracket style
        self.bracket_style_combo = QComboBox()
        self.bracket_style_combo.addItems([
            "Solid", "Dashed", "Dotted", "Dash-dot",
        ])
        self.bracket_style_combo.currentIndexChanged.connect(lambda: self.stats_changed.emit())
        disp_layout.addRow("Bracket style:", self.bracket_style_combo)

        # Bracket line width
        self.bracket_width_spin = QDoubleSpinBox()
        self.bracket_width_spin.setRange(0.3, 5.0)
        self.bracket_width_spin.setSingleStep(0.25)
        self.bracket_width_spin.setValue(1.0)
        self.bracket_width_spin.setSuffix(" pt")
        self.bracket_width_spin.valueChanged.connect(lambda: self.stats_changed.emit())
        disp_layout.addRow("Bracket width:", self.bracket_width_spin)

        layout.addWidget(disp_group)

        # ---- Results with checkable comparisons ----
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        # Summary text (global test result) — scrollable
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(80)
        self.summary_text.setMinimumHeight(50)
        self.summary_text.setStyleSheet(
            "QTextEdit { font-family: 'Menlo', 'Consolas', monospace; font-size: 11px; }"
        )
        self.summary_text.setPlaceholderText("Run a test to see results...")
        results_layout.addWidget(self.summary_text)

        # Select all / none buttons
        btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton("All")
        self.select_all_btn.setFixedWidth(50)
        self.select_all_btn.setToolTip("Show all comparisons")
        self.select_all_btn.clicked.connect(self._select_all)
        btn_row.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("None")
        self.select_none_btn.setFixedWidth(50)
        self.select_none_btn.setToolTip("Hide all comparisons")
        self.select_none_btn.clicked.connect(self._select_none)
        btn_row.addWidget(self.select_none_btn)

        self.select_sig_btn = QPushButton("Sig. only")
        self.select_sig_btn.setFixedWidth(65)
        self.select_sig_btn.setToolTip("Show only significant comparisons")
        self.select_sig_btn.clicked.connect(self._select_significant)
        btn_row.addWidget(self.select_sig_btn)

        btn_row.addStretch()
        results_layout.addLayout(btn_row)

        # Checkable comparison list
        self.comp_list = QListWidget()
        self.comp_list.setMinimumHeight(100)
        self.comp_list.setStyleSheet(
            "QListWidget { font-family: 'Menlo', 'Consolas', monospace; font-size: 11px; }"
        )
        self.comp_list.setToolTip("Check/uncheck to show/hide individual comparisons")
        self.comp_list.itemChanged.connect(self._on_comp_toggle)
        results_layout.addWidget(self.comp_list)

        layout.addWidget(results_group)

        layout.addStretch()

        # Internal state
        self._comparisons: list[ComparisonResult] = []
        self._updating_list = False  # prevent signal loops

        # Initial visibility
        self._on_test_change()
        self._on_compare_change()

    # ---- Quick selection buttons ----

    def _select_all(self):
        self._set_all_checked(True)

    def _select_none(self):
        self._set_all_checked(False)

    def _select_significant(self):
        self._updating_list = True
        for i in range(self.comp_list.count()):
            item = self.comp_list.item(i)
            if i < len(self._comparisons):
                is_sig = self._comparisons[i].stars != "ns"
                item.setCheckState(Qt.CheckState.Checked if is_sig else Qt.CheckState.Unchecked)
        self._updating_list = False
        self.visibility_changed.emit()

    def _set_all_checked(self, checked: bool):
        self._updating_list = True
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.comp_list.count()):
            self.comp_list.item(i).setCheckState(state)
        self._updating_list = False
        self.visibility_changed.emit()

    def _on_comp_toggle(self, item):
        if not self._updating_list:
            self.visibility_changed.emit()

    # ---- Test/compare mode handlers ----

    def _on_test_change(self):
        test = self.test_combo.currentText()
        is_none = test == "(None)"
        is_multi_test = test in ("One-way ANOVA", "Kruskal-Wallis")
        self.posthoc_combo.setEnabled(is_multi_test)
        self.compare_combo.setEnabled(not is_none)
        is_ctrl = self.compare_combo.currentText() == "Compare to control"
        self.control_spin.setEnabled(not is_none and is_ctrl)
        self.control_label.setEnabled(self.control_spin.isEnabled())
        self.stats_changed.emit()

    def _on_compare_change(self):
        is_ctrl = self.compare_combo.currentText() == "Compare to control"
        test = self.test_combo.currentText()
        is_none = test == "(None)"
        self.control_spin.setEnabled(not is_none and is_ctrl)
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
        """Display the analysis results and populate the comparison checklist."""
        self._comparisons = result.comparisons or []

        # Summary (global test line)
        lines = result.summary.split("\n") if result.summary else []
        # Show header lines (before individual comparisons)
        header = []
        for line in lines:
            if " vs " in line and ("p=" in line or "p<" in line):
                break
            header.append(line)
        self.summary_text.setPlainText("\n".join(header) if header else "No results.")

        # Populate checklist
        self._updating_list = True
        self.comp_list.clear()
        for comp in self._comparisons:
            text = f"{comp.label_a} vs {comp.label_b}: p={comp.p_value:.4f} ({comp.stars})"
            item = QListWidgetItem(text)
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            # Default: show significant, hide ns
            if comp.stars != "ns":
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(
                    Qt.CheckState.Checked if self.show_ns_check.isChecked()
                    else Qt.CheckState.Unchecked
                )
            self.comp_list.addItem(item)
        self._updating_list = False

    def get_visible_comparisons(self) -> list[ComparisonResult]:
        """Return only the comparisons that are checked (visible)."""
        visible = []
        for i in range(self.comp_list.count()):
            item = self.comp_list.item(i)
            if item.checkState() == Qt.CheckState.Checked and i < len(self._comparisons):
                visible.append(self._comparisons[i])
        return visible

    def get_hidden_indices(self) -> set[int]:
        """Return set of comparison indices that are unchecked."""
        hidden = set()
        for i in range(self.comp_list.count()):
            item = self.comp_list.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                hidden.add(i)
        return hidden

    def get_bracket_linestyle(self) -> str:
        """Return matplotlib linestyle string."""
        mapping = {"Solid": "-", "Dashed": "--", "Dotted": ":", "Dash-dot": "-."}
        return mapping.get(self.bracket_style_combo.currentText(), "-")

    def get_bracket_linewidth(self) -> float:
        return self.bracket_width_spin.value()

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
            "bracket_linestyle": self.get_bracket_linestyle(),
            "bracket_linewidth": self.get_bracket_linewidth(),
            "bracket_style_name": self.bracket_style_combo.currentText(),
            "hidden_comparisons": sorted(self.get_hidden_indices()),
        }
