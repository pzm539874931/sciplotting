"""
Data Transform Dialog — apply mathematical transforms to data columns.
Non-destructive: creates new columns with suffix.
"""

import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QGroupBox, QListWidget, QAbstractItemView, QPushButton,
    QLabel, QDialogButtonBox, QSpinBox, QMessageBox,
)
from PyQt6.QtCore import Qt


TRANSFORMS = {
    "Normalize (0-1)": "norm01",
    "Normalize (Z-score)": "zscore",
    "% of Max": "pct_max",
    "% of Control (row 0)": "pct_ctrl",
    "Log10": "log10",
    "Ln (natural log)": "ln",
    "Square Root": "sqrt",
    "Reciprocal (1/x)": "reciprocal",
    "Fold Change vs Control (row 0)": "fold",
    "Subtract Baseline (row 0)": "subtract_baseline",
}


class TransformDialog(QDialog):
    """Dialog for applying data transforms to selected columns."""

    def __init__(self, columns: list[str], data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Transform")
        self.setMinimumWidth(400)
        self._columns = columns
        self._data = data  # dict of column_name -> list of values
        self._result_columns: list[str] = []
        self._result_data: dict = {}

        layout = QVBoxLayout(self)

        # Column selection
        col_group = QGroupBox("Select Columns to Transform")
        col_layout = QVBoxLayout(col_group)
        self.col_list = QListWidget()
        self.col_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.col_list.addItems(columns)
        self.col_list.setMaximumHeight(120)
        col_layout.addWidget(self.col_list)
        layout.addWidget(col_group)

        # Transform selection
        tf_group = QGroupBox("Transform")
        tf_layout = QFormLayout(tf_group)
        self.transform_combo = QComboBox()
        self.transform_combo.addItems(list(TRANSFORMS.keys()))
        tf_layout.addRow("Type:", self.transform_combo)

        self.control_row_spin = QSpinBox()
        self.control_row_spin.setRange(0, 9999)
        self.control_row_spin.setValue(0)
        self.control_row_spin.setToolTip("Row index used as control/baseline (0-based)")
        tf_layout.addRow("Control row:", self.control_row_spin)
        layout.addWidget(tf_group)

        # Preview
        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #555;")
        layout.addWidget(self.preview_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Preview on change
        self.transform_combo.currentIndexChanged.connect(self._update_preview)
        self.col_list.itemSelectionChanged.connect(self._update_preview)
        self._update_preview()

    def _get_selected_columns(self) -> list[str]:
        return [item.text() for item in self.col_list.selectedItems()]

    def _update_preview(self):
        cols = self._get_selected_columns()
        tf_name = self.transform_combo.currentText()
        if not cols:
            self.preview_label.setText("Select columns to preview.")
            return
        self.preview_label.setText(
            f"Will create: {', '.join(c + '_' + TRANSFORMS[tf_name] for c in cols)}"
        )

    def _apply(self):
        cols = self._get_selected_columns()
        if not cols:
            QMessageBox.warning(self, "No Columns", "Select at least one column.")
            return

        tf_key = TRANSFORMS[self.transform_combo.currentText()]
        ctrl_row = self.control_row_spin.value()

        self._result_columns = []
        self._result_data = {}

        for col in cols:
            raw = self._data.get(col, [])
            arr = np.array([v if v is not None else np.nan for v in raw], dtype=float)
            new_name = f"{col}_{tf_key}"
            try:
                transformed = self._transform(arr, tf_key, ctrl_row)
                self._result_columns.append(new_name)
                self._result_data[new_name] = transformed.tolist()
            except Exception as e:
                QMessageBox.warning(self, "Transform Error", f"Error on '{col}': {e}")
                return

        self.accept()

    @staticmethod
    def _transform(arr: np.ndarray, tf_key: str, ctrl_row: int) -> np.ndarray:
        if tf_key == "norm01":
            mn, mx = np.nanmin(arr), np.nanmax(arr)
            return (arr - mn) / (mx - mn) if mx != mn else np.zeros_like(arr)
        elif tf_key == "zscore":
            return (arr - np.nanmean(arr)) / np.nanstd(arr, ddof=1)
        elif tf_key == "pct_max":
            return arr / np.nanmax(arr) * 100
        elif tf_key == "pct_ctrl":
            ctrl = arr[ctrl_row] if ctrl_row < len(arr) else arr[0]
            return arr / ctrl * 100 if ctrl != 0 else arr
        elif tf_key == "log10":
            return np.log10(np.where(arr > 0, arr, np.nan))
        elif tf_key == "ln":
            return np.log(np.where(arr > 0, arr, np.nan))
        elif tf_key == "sqrt":
            return np.sqrt(np.where(arr >= 0, arr, np.nan))
        elif tf_key == "reciprocal":
            return np.where(arr != 0, 1.0 / arr, np.nan)
        elif tf_key == "fold":
            ctrl = arr[ctrl_row] if ctrl_row < len(arr) else arr[0]
            return arr / ctrl if ctrl != 0 else arr
        elif tf_key == "subtract_baseline":
            ctrl = arr[ctrl_row] if ctrl_row < len(arr) else arr[0]
            return arr - ctrl
        else:
            return arr

    def get_results(self) -> tuple[list[str], dict]:
        """Return (new_column_names, new_column_data)."""
        return self._result_columns, self._result_data
