"""
Data Table Widget - Provides an editable spreadsheet-like interface for data entry.

Features:
- Add/delete rows and columns
- Inline editing with validation
- Copy/paste support
- Import from clipboard
- Column header renaming
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox, QMenu,
    QApplication, QLabel, QSpinBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction, QKeySequence, QColor

import numpy as np
from typing import Optional


class DataTableWidget(QWidget):
    """Editable spreadsheet-like data table widget."""

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._setup_context_menu()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()

        self.add_row_btn = QPushButton("+ Row")
        self.add_row_btn.clicked.connect(self._add_row)
        self.add_row_btn.setToolTip("Add a new row at the end")
        toolbar.addWidget(self.add_row_btn)

        self.add_col_btn = QPushButton("+ Column")
        self.add_col_btn.clicked.connect(self._add_column)
        self.add_col_btn.setToolTip("Add a new column")
        toolbar.addWidget(self.add_col_btn)

        self.del_row_btn = QPushButton("- Row")
        self.del_row_btn.clicked.connect(self._delete_selected_rows)
        self.del_row_btn.setToolTip("Delete selected row(s)")
        toolbar.addWidget(self.del_row_btn)

        self.del_col_btn = QPushButton("- Column")
        self.del_col_btn.clicked.connect(self._delete_selected_columns)
        self.del_col_btn.setToolTip("Delete selected column(s)")
        toolbar.addWidget(self.del_col_btn)

        toolbar.addStretch()

        # Row/column count controls
        toolbar.addWidget(QLabel("Rows:"))
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 10000)
        self.row_spin.setValue(10)
        self.row_spin.valueChanged.connect(self._set_row_count)
        toolbar.addWidget(self.row_spin)

        toolbar.addWidget(QLabel("Cols:"))
        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 100)
        self.col_spin.setValue(3)
        self.col_spin.valueChanged.connect(self._set_col_count)
        toolbar.addWidget(self.col_spin)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_all)
        self.clear_btn.setToolTip("Clear all data")
        toolbar.addWidget(self.clear_btn)

        layout.addLayout(toolbar)

        # Table widget
        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["X", "Y1", "Y2"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self._rename_column)
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table)

        # Info label
        self.info_label = QLabel("Double-click column headers to rename. Right-click for more options.")
        self.info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.info_label)

    def _setup_context_menu(self):
        """Setup right-click context menu."""
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """Show context menu at position."""
        menu = QMenu(self)

        # Row operations
        insert_row = QAction("Insert Row Above", self)
        insert_row.triggered.connect(self._insert_row_above)
        menu.addAction(insert_row)

        insert_row_below = QAction("Insert Row Below", self)
        insert_row_below.triggered.connect(self._insert_row_below)
        menu.addAction(insert_row_below)

        delete_row = QAction("Delete Row", self)
        delete_row.triggered.connect(self._delete_selected_rows)
        menu.addAction(delete_row)

        menu.addSeparator()

        # Column operations
        insert_col = QAction("Insert Column Left", self)
        insert_col.triggered.connect(self._insert_column_left)
        menu.addAction(insert_col)

        insert_col_right = QAction("Insert Column Right", self)
        insert_col_right.triggered.connect(self._insert_column_right)
        menu.addAction(insert_col_right)

        delete_col = QAction("Delete Column", self)
        delete_col.triggered.connect(self._delete_selected_columns)
        menu.addAction(delete_col)

        menu.addSeparator()

        # Clipboard operations
        paste_action = QAction("Paste from Clipboard", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        paste_action.triggered.connect(self._paste_from_clipboard)
        menu.addAction(paste_action)

        copy_action = QAction("Copy Selection", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self._copy_selection)
        menu.addAction(copy_action)

        menu.addSeparator()

        # Fill operations
        fill_down = QAction("Fill Down", self)
        fill_down.triggered.connect(self._fill_down)
        menu.addAction(fill_down)

        fill_series = QAction("Fill Series...", self)
        fill_series.triggered.connect(self._fill_series)
        menu.addAction(fill_series)

        menu.exec(self.table.mapToGlobal(pos))

    # ---- Row/Column Operations ----

    def _add_row(self):
        """Add a row at the end."""
        self.table.blockSignals(True)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.row_spin.setValue(self.table.rowCount())
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _add_column(self):
        """Add a column at the end."""
        name, ok = QInputDialog.getText(self, "Add Column", "Column name:")
        if ok and name.strip():
            self.table.blockSignals(True)
            col = self.table.columnCount()
            self.table.insertColumn(col)
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(name.strip()))
            self.col_spin.setValue(self.table.columnCount())
            self.table.blockSignals(False)
            self.data_changed.emit()

    def _insert_row_above(self):
        """Insert row above current selection."""
        row = self.table.currentRow()
        if row < 0:
            row = 0
        self.table.blockSignals(True)
        self.table.insertRow(row)
        self.row_spin.setValue(self.table.rowCount())
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _insert_row_below(self):
        """Insert row below current selection."""
        row = self.table.currentRow()
        if row < 0:
            row = self.table.rowCount() - 1
        self.table.blockSignals(True)
        self.table.insertRow(row + 1)
        self.row_spin.setValue(self.table.rowCount())
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _insert_column_left(self):
        """Insert column to the left of current selection."""
        col = self.table.currentColumn()
        if col < 0:
            col = 0
        name, ok = QInputDialog.getText(self, "Insert Column", "Column name:")
        if ok and name.strip():
            self.table.blockSignals(True)
            self.table.insertColumn(col)
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(name.strip()))
            self.col_spin.setValue(self.table.columnCount())
            self.table.blockSignals(False)
            self.data_changed.emit()

    def _insert_column_right(self):
        """Insert column to the right of current selection."""
        col = self.table.currentColumn()
        if col < 0:
            col = self.table.columnCount() - 1
        name, ok = QInputDialog.getText(self, "Insert Column", "Column name:")
        if ok and name.strip():
            self.table.blockSignals(True)
            self.table.insertColumn(col + 1)
            self.table.setHorizontalHeaderItem(col + 1, QTableWidgetItem(name.strip()))
            self.col_spin.setValue(self.table.columnCount())
            self.table.blockSignals(False)
            self.data_changed.emit()

    def _delete_selected_rows(self):
        """Delete selected rows."""
        rows = set()
        for item in self.table.selectedItems():
            rows.add(item.row())
        if not rows:
            row = self.table.currentRow()
            if row >= 0:
                rows.add(row)

        if not rows:
            return

        self.table.blockSignals(True)
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)
        self.row_spin.setValue(self.table.rowCount())
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _delete_selected_columns(self):
        """Delete selected columns."""
        cols = set()
        for item in self.table.selectedItems():
            cols.add(item.column())
        if not cols:
            col = self.table.currentColumn()
            if col >= 0:
                cols.add(col)

        if not cols:
            return

        self.table.blockSignals(True)
        for col in sorted(cols, reverse=True):
            self.table.removeColumn(col)
        self.col_spin.setValue(self.table.columnCount())
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _rename_column(self, col: int):
        """Rename column header."""
        current_name = self.table.horizontalHeaderItem(col)
        current_text = current_name.text() if current_name else f"Column {col + 1}"
        name, ok = QInputDialog.getText(self, "Rename Column", "Column name:", text=current_text)
        if ok and name.strip():
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(name.strip()))
            self.data_changed.emit()

    def _set_row_count(self, count: int):
        """Set total row count."""
        current = self.table.rowCount()
        if count == current:
            return
        self.table.blockSignals(True)
        self.table.setRowCount(count)
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _set_col_count(self, count: int):
        """Set total column count."""
        current = self.table.columnCount()
        if count == current:
            return
        self.table.blockSignals(True)
        if count > current:
            for i in range(current, count):
                self.table.insertColumn(i)
                self.table.setHorizontalHeaderItem(i, QTableWidgetItem(f"Col{i + 1}"))
        else:
            for i in range(current - 1, count - 1, -1):
                self.table.removeColumn(i)
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _clear_all(self):
        """Clear all data (keep structure)."""
        reply = QMessageBox.question(
            self, "Clear Data",
            "Clear all data? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                self.table.setItem(row, col, QTableWidgetItem(""))
        self.table.blockSignals(False)
        self.data_changed.emit()

    # ---- Clipboard Operations ----

    def _paste_from_clipboard(self):
        """Paste data from clipboard (tab-separated)."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        lines = text.strip().split('\n')
        if not lines:
            return

        # Detect if first row is headers (contains non-numeric values)
        first_row = lines[0].split('\t')
        has_headers = False
        for val in first_row:
            try:
                float(val)
            except ValueError:
                has_headers = True
                break

        self.table.blockSignals(True)

        start_row = self.table.currentRow()
        start_col = self.table.currentColumn()
        if start_row < 0:
            start_row = 0
        if start_col < 0:
            start_col = 0

        if has_headers:
            # Set headers from first row
            for i, header in enumerate(first_row):
                col_idx = start_col + i
                if col_idx >= self.table.columnCount():
                    self.table.insertColumn(col_idx)
                self.table.setHorizontalHeaderItem(col_idx, QTableWidgetItem(header.strip()))
            lines = lines[1:]  # Skip header row

        # Paste data
        for row_offset, line in enumerate(lines):
            values = line.split('\t')
            row_idx = start_row + row_offset

            if row_idx >= self.table.rowCount():
                self.table.insertRow(row_idx)

            for col_offset, value in enumerate(values):
                col_idx = start_col + col_offset
                if col_idx >= self.table.columnCount():
                    self.table.insertColumn(col_idx)
                    self.table.setHorizontalHeaderItem(col_idx, QTableWidgetItem(f"Col{col_idx + 1}"))

                item = QTableWidgetItem(value.strip())
                self.table.setItem(row_idx, col_idx, item)

        self.row_spin.setValue(self.table.rowCount())
        self.col_spin.setValue(self.table.columnCount())
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _copy_selection(self):
        """Copy selected cells to clipboard."""
        selection = self.table.selectedRanges()
        if not selection:
            return

        # Get bounds
        min_row = min(r.topRow() for r in selection)
        max_row = max(r.bottomRow() for r in selection)
        min_col = min(r.leftColumn() for r in selection)
        max_col = max(r.rightColumn() for r in selection)

        lines = []
        for row in range(min_row, max_row + 1):
            row_data = []
            for col in range(min_col, max_col + 1):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            lines.append('\t'.join(row_data))

        QApplication.clipboard().setText('\n'.join(lines))

    # ---- Fill Operations ----

    def _fill_down(self):
        """Fill selected cells down with the top value."""
        selection = self.table.selectedRanges()
        if not selection:
            return

        self.table.blockSignals(True)
        for r in selection:
            for col in range(r.leftColumn(), r.rightColumn() + 1):
                top_item = self.table.item(r.topRow(), col)
                value = top_item.text() if top_item else ""
                for row in range(r.topRow() + 1, r.bottomRow() + 1):
                    self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.blockSignals(False)
        self.data_changed.emit()

    def _fill_series(self):
        """Fill selected cells with a numeric series."""
        selection = self.table.selectedRanges()
        if not selection:
            return

        start, ok1 = QInputDialog.getDouble(self, "Fill Series", "Start value:", 0, -1e9, 1e9, 2)
        if not ok1:
            return
        step, ok2 = QInputDialog.getDouble(self, "Fill Series", "Step value:", 1, -1e9, 1e9, 2)
        if not ok2:
            return

        self.table.blockSignals(True)
        for r in selection:
            for col in range(r.leftColumn(), r.rightColumn() + 1):
                value = start
                for row in range(r.topRow(), r.bottomRow() + 1):
                    self.table.setItem(row, col, QTableWidgetItem(str(value)))
                    value += step
        self.table.blockSignals(False)
        self.data_changed.emit()

    # ---- Cell Change Handler ----

    def _on_cell_changed(self, row: int, col: int):
        """Handle cell value change."""
        self.data_changed.emit()

    # ---- Data I/O ----

    def get_columns(self) -> list[str]:
        """Get column names."""
        cols = []
        for i in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(i)
            cols.append(item.text() if item else f"Col{i + 1}")
        return cols

    def get_data(self) -> dict:
        """
        Get data as dict of columns.

        Returns:
            Dict with column names as keys and list of values.
        """
        columns = self.get_columns()
        data = {col: [] for col in columns}

        for row in range(self.table.rowCount()):
            for col_idx, col_name in enumerate(columns):
                item = self.table.item(row, col_idx)
                if item and item.text().strip():
                    text = item.text().strip()
                    # Try to convert to number
                    try:
                        if '.' in text:
                            data[col_name].append(float(text))
                        else:
                            data[col_name].append(int(text))
                    except ValueError:
                        data[col_name].append(text)
                else:
                    data[col_name].append(None)

        return data

    def get_data_for_export(self) -> dict:
        """
        Get data in format suitable for project export.

        Returns:
            Dict with 'columns' list and 'data' dict.
        """
        columns = self.get_columns()
        data = self.get_data()

        # Filter out completely empty columns
        non_empty_cols = []
        non_empty_data = {}

        for col in columns:
            col_data = data[col]
            if any(v is not None for v in col_data):
                non_empty_cols.append(col)
                non_empty_data[col] = col_data

        return {
            "columns": non_empty_cols,
            "data": non_empty_data,
        }

    def set_data(self, columns: list[str], data: dict):
        """
        Set table data.

        Args:
            columns: List of column names
            data: Dict mapping column names to list of values
        """
        if not columns or not data:
            return

        # Determine row count
        row_count = max(len(data.get(col, [])) for col in columns) if columns else 0

        self.table.blockSignals(True)

        # Set dimensions
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(row_count)

        # Set headers
        for i, col in enumerate(columns):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(col))

        # Set data
        for col_idx, col_name in enumerate(columns):
            col_data = data.get(col_name, [])
            for row_idx, value in enumerate(col_data):
                if value is not None:
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
                else:
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(""))

        self.row_spin.setValue(self.table.rowCount())
        self.col_spin.setValue(self.table.columnCount())
        self.table.blockSignals(False)

    def has_data(self) -> bool:
        """Check if table has any non-empty data."""
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    return True
        return False

    def get_row_count(self) -> int:
        """Get number of data rows (excluding empty rows at end)."""
        for row in range(self.table.rowCount() - 1, -1, -1):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    return row + 1
        return 0

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.matches(QKeySequence.StandardKey.Paste):
            self._paste_from_clipboard()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self._copy_selection()
        elif event.key() == Qt.Key.Key_Delete:
            # Clear selected cells
            self.table.blockSignals(True)
            for item in self.table.selectedItems():
                item.setText("")
            self.table.blockSignals(False)
            self.data_changed.emit()
        else:
            super().keyPressEvent(event)
