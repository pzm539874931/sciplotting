"""
Data panel - provides UI for loading data files, pasting data,
selecting columns for X/Y/error bars, AND Prism-style replicate grouping
where multiple columns are auto-aggregated to Mean+ErrorBar.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFileDialog, QTextEdit, QGroupBox, QFormLayout,
    QLineEdit, QScrollArea, QFrame, QMessageBox, QTabWidget,
    QListWidget, QAbstractItemView, QCheckBox,
)
from PyQt6.QtCore import pyqtSignal, QTimer

from core.data_manager import DataManager, ERROR_BAR_TYPES, CENTRAL_TYPES


class DataSeriesWidget(QFrame):
    """A single data series — supports BOTH single-column and replicate-group modes."""

    removed = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, columns: list[str], index: int = 0, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "DataSeriesWidget { background: #fafafa; border: 1px solid #ddd; "
            "border-radius: 4px; padding: 4px; }"
        )
        self._columns = columns

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Header row: label + remove button
        header = QHBoxLayout()
        self.label_edit = QLineEdit(f"Series {index + 1}")
        self.label_edit.setPlaceholderText("Series label")
        self.label_edit.textChanged.connect(lambda: self.changed.emit())
        header.addWidget(QLabel("Label:"))
        header.addWidget(self.label_edit)
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(30, 26)
        self.remove_btn.setStyleSheet(
            "QPushButton { color: white; background: #cc4444; font-weight: bold; "
            "border-radius: 3px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #ff3333; }"
        )
        self.remove_btn.setToolTip("Remove this series")
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))
        header.addWidget(self.remove_btn)
        layout.addLayout(header)

        # Mode toggle: single column vs replicate group
        mode_row = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Single Column", "Replicate Group"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        mode_row.addWidget(QLabel("Mode:"))
        mode_row.addWidget(self.mode_combo)
        layout.addLayout(mode_row)

        # --- X column (shared) ---
        x_row = QHBoxLayout()
        col_options = ["(auto index)"] + columns
        self.x_combo = QComboBox()
        self.x_combo.addItems(col_options)
        self.x_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        x_row.addWidget(QLabel("X:"))
        x_row.addWidget(self.x_combo)
        layout.addLayout(x_row)

        # ===== Single Column mode widgets =====
        self.single_frame = QFrame()
        single_layout = QFormLayout(self.single_frame)
        single_layout.setContentsMargins(0, 0, 0, 0)

        self.y_combo = QComboBox()
        self.y_combo.addItems(columns)
        if index < len(columns):
            self.y_combo.setCurrentIndex(min(index, len(columns) - 1))
        self.y_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        single_layout.addRow("Y Column:", self.y_combo)

        self.yerr_combo = QComboBox()
        self.yerr_combo.addItems(["(none)"] + columns)
        self.yerr_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        single_layout.addRow("Y Error:", self.yerr_combo)

        layout.addWidget(self.single_frame)

        # ===== Replicate Group mode widgets =====
        self.rep_frame = QFrame()
        rep_layout = QVBoxLayout(self.rep_frame)
        rep_layout.setContentsMargins(0, 0, 0, 0)
        rep_layout.setSpacing(4)

        rep_layout.addWidget(QLabel("Select replicate columns (Ctrl/Shift click):"))
        self.rep_list = QListWidget()
        self.rep_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.rep_list.addItems(columns)
        self.rep_list.setMaximumHeight(100)
        self.rep_list.itemSelectionChanged.connect(lambda: self.changed.emit())
        rep_layout.addWidget(self.rep_list)

        stat_row = QHBoxLayout()
        self.central_combo = QComboBox()
        self.central_combo.addItems(CENTRAL_TYPES)
        self.central_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        stat_row.addWidget(QLabel("Central:"))
        stat_row.addWidget(self.central_combo)
        self.error_combo = QComboBox()
        self.error_combo.addItems(ERROR_BAR_TYPES)
        self.error_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        stat_row.addWidget(QLabel("Error:"))
        stat_row.addWidget(self.error_combo)
        rep_layout.addLayout(stat_row)

        layout.addWidget(self.rep_frame)
        self.rep_frame.setVisible(False)  # hidden by default

    def _on_mode_change(self, idx):
        is_replicate = idx == 1
        self.single_frame.setVisible(not is_replicate)
        self.rep_frame.setVisible(is_replicate)
        self.changed.emit()

    def is_replicate_mode(self) -> bool:
        return self.mode_combo.currentIndex() == 1

    def get_selection(self) -> dict:
        x_text = self.x_combo.currentText()
        sel = {
            "x_col": None if x_text == "(auto index)" else x_text,
            "label": self.label_edit.text(),
        }
        if self.is_replicate_mode():
            selected_items = self.rep_list.selectedItems()
            sel["replicate_cols"] = [item.text() for item in selected_items]
            sel["central"] = self.central_combo.currentText()
            sel["error_type"] = self.error_combo.currentText()
        else:
            sel["y_col"] = self.y_combo.currentText()
            yerr_text = self.yerr_combo.currentText()
            sel["yerr_col"] = None if yerr_text == "(none)" else yerr_text
        return sel


class DataPanel(QWidget):
    """Panel for managing data input and series configuration."""

    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = DataManager()
        self.series_widgets: list[DataSeriesWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Tab widget for file vs paste input
        tabs = QTabWidget()

        # --- File tab ---
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)
        btn_row = QHBoxLayout()
        self.load_csv_btn = QPushButton("Load CSV")
        self.load_csv_btn.clicked.connect(self._load_csv)
        self.load_excel_btn = QPushButton("Load Excel")
        self.load_excel_btn.clicked.connect(self._load_excel)
        btn_row.addWidget(self.load_csv_btn)
        btn_row.addWidget(self.load_excel_btn)
        file_layout.addLayout(btn_row)
        self.file_info_label = QLabel("No file loaded")
        self.file_info_label.setWordWrap(True)
        file_layout.addWidget(self.file_info_label)
        file_layout.addStretch()
        tabs.addTab(file_tab, "File")

        # --- Paste tab ---
        paste_tab = QWidget()
        paste_layout = QVBoxLayout(paste_tab)
        paste_layout.addWidget(QLabel("Paste tab-separated data (with headers):"))
        self.paste_edit = QTextEdit()
        self.paste_edit.setPlaceholderText("x\ty1\ty2\n1\t2.3\t3.1\n2\t4.5\t5.2\n...")
        self.paste_edit.setMaximumHeight(120)
        paste_layout.addWidget(self.paste_edit)
        self.paste_btn = QPushButton("Parse Pasted Data")
        self.paste_btn.clicked.connect(self._parse_paste)
        paste_layout.addWidget(self.paste_btn)

        # Auto-parse when paste text changes (with debounce via timer)
        self._paste_timer = None
        self.paste_edit.textChanged.connect(self._on_paste_text_changed)
        paste_layout.addStretch()
        tabs.addTab(paste_tab, "Paste")

        # --- Demo tab ---
        demo_tab = QWidget()
        demo_layout = QVBoxLayout(demo_tab)
        demo_layout.addWidget(QLabel("Use built-in demo data to preview plot types."))
        self.demo_btn = QPushButton("Use Demo Data")
        self.demo_btn.clicked.connect(self._use_demo)
        demo_layout.addWidget(self.demo_btn)
        demo_layout.addStretch()
        tabs.addTab(demo_tab, "Demo")

        layout.addWidget(tabs)

        # --- Series configuration area ---
        series_group = QGroupBox("Data Series")
        series_layout = QVBoxLayout(series_group)

        self.add_series_btn = QPushButton("+ Add Series")
        self.add_series_btn.clicked.connect(self._add_series)
        series_layout.addWidget(self.add_series_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.series_container = QWidget()
        self.series_vlayout = QVBoxLayout(self.series_container)
        self.series_vlayout.setContentsMargins(0, 0, 0, 0)
        self.series_vlayout.addStretch()
        scroll.setWidget(self.series_container)
        series_layout.addWidget(scroll)

        layout.addWidget(series_group, stretch=1)

        self._use_demo_data = False

    # ---- Loading ----

    def _load_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv *.tsv *.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            delimiter = "\t" if path.endswith(".tsv") else ","
            cols = self.data_manager.load_csv(path, delimiter=delimiter)
            rows = self.data_manager.get_row_count()
            self.file_info_label.setText(
                f"Loaded: {path}\nColumns: {', '.join(cols)}\nRows: {rows}"
            )
            self._use_demo_data = False
            self._rebuild_series(cols)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load CSV:\n{e}")

    def _load_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if not path:
            return
        try:
            cols = self.data_manager.load_excel(path)
            rows = self.data_manager.get_row_count()
            self.file_info_label.setText(
                f"Loaded: {path}\nColumns: {', '.join(cols)}\nRows: {rows}"
            )
            self._use_demo_data = False
            self._rebuild_series(cols)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load Excel:\n{e}")

    def _on_paste_text_changed(self):
        """Auto-parse paste data after user stops typing (500ms debounce)."""
        if self._paste_timer is not None:
            self._paste_timer.stop()
        self._paste_timer = QTimer()
        self._paste_timer.setSingleShot(True)
        self._paste_timer.setInterval(500)
        self._paste_timer.timeout.connect(self._auto_parse_paste)
        self._paste_timer.start()

    def _auto_parse_paste(self):
        """Silently parse pasted data without showing error dialogs."""
        text = self.paste_edit.toPlainText().strip()
        if not text:
            return
        try:
            cols = self.data_manager.load_from_text(text, delimiter="\t")
            if not cols:
                return
            rows = self.data_manager.get_row_count()
            self.file_info_label.setText(
                f"Parsed pasted data\nColumns: {', '.join(cols)}\nRows: {rows}"
            )
            self._use_demo_data = False
            self._rebuild_series(cols)
        except Exception:
            pass  # Don't show error during auto-parse; user can click Parse button

    def _parse_paste(self):
        text = self.paste_edit.toPlainText().strip()
        if not text:
            return
        try:
            cols = self.data_manager.load_from_text(text, delimiter="\t")
            rows = self.data_manager.get_row_count()
            self.file_info_label.setText(
                f"Parsed pasted data\nColumns: {', '.join(cols)}\nRows: {rows}"
            )
            self._use_demo_data = False
            self._rebuild_series(cols)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to parse data:\n{e}")

    def _use_demo(self):
        self._use_demo_data = True
        self._clear_series()
        self.file_info_label.setText("Using demo data (auto-generated)")
        self.data_changed.emit()

    # ---- Series management ----

    def _rebuild_series(self, columns: list[str]):
        self._clear_series()
        if len(columns) >= 2:
            self._add_series_with_columns(columns, 0)
        self.data_changed.emit()

    def _clear_series(self):
        for sw in self.series_widgets:
            self.series_vlayout.removeWidget(sw)
            sw.deleteLater()
        self.series_widgets.clear()

    def _add_series(self):
        cols = self.data_manager.get_columns()
        if not cols:
            QMessageBox.information(self, "Info", "Please load data first.")
            return
        idx = len(self.series_widgets)
        self._add_series_with_columns(cols, idx)
        self.data_changed.emit()

    def _add_series_with_columns(self, columns: list[str], index: int):
        sw = DataSeriesWidget(columns, index)
        sw.removed.connect(self._remove_series)
        sw.changed.connect(lambda: self.data_changed.emit())
        insert_pos = self.series_vlayout.count() - 1
        self.series_vlayout.insertWidget(insert_pos, sw)
        self.series_widgets.append(sw)

    def _remove_series(self, widget):
        if widget in self.series_widgets:
            self.series_widgets.remove(widget)
            self.series_vlayout.removeWidget(widget)
            widget.deleteLater()
            self.data_changed.emit()

    # ---- Output ----

    def get_datasets(self, plot_type: str = "line") -> list[dict]:
        if self._use_demo_data:
            return DataManager.generate_demo_data(plot_type)
        if not self.series_widgets:
            return DataManager.generate_demo_data(plot_type)
        selections = [sw.get_selection() for sw in self.series_widgets]
        # Validate: skip empty replicate selections
        valid_selections = []
        for sel in selections:
            if sel.get("replicate_cols") is not None:
                if len(sel["replicate_cols"]) == 0:
                    continue  # no columns selected yet
            elif sel.get("y_col") is None:
                continue
            valid_selections.append(sel)
        if not valid_selections:
            return DataManager.generate_demo_data(plot_type)
        datasets = self.data_manager.build_datasets_from_selections(valid_selections)
        if datasets:
            return datasets
        return DataManager.generate_demo_data(plot_type)

    def get_selections(self) -> list[dict]:
        return [sw.get_selection() for sw in self.series_widgets]

    def get_embedded_data(self) -> dict:
        """
        Get raw data for embedding in project file.

        Returns:
            Dict with 'columns', 'data', and 'selections' for full state restore.
        """
        result = self.data_manager.export_raw_data()
        result["selections"] = self.get_selections()
        result["is_demo"] = self._use_demo_data
        return result

    def set_embedded_data(self, embedded: dict):
        """
        Restore data from project file.

        Args:
            embedded: Dict with 'columns', 'data', and 'selections'
        """
        if embedded.get("is_demo", False):
            self._use_demo()
            return

        columns = embedded.get("columns", [])
        data = embedded.get("data", {})
        selections = embedded.get("selections", [])

        if not columns or not data:
            return

        # Import raw data
        imported_cols = self.data_manager.import_raw_data(embedded)
        if not imported_cols:
            return

        # Update UI
        self.file_info_label.setText(
            f"Restored from project\nColumns: {', '.join(imported_cols)}\n"
            f"Rows: {self.data_manager.get_row_count()}"
        )
        self._use_demo_data = False

        # Rebuild series widgets
        self._clear_series()

        # Restore selections
        if selections:
            for i, sel in enumerate(selections):
                sw = DataSeriesWidget(imported_cols, i)
                sw.removed.connect(self._remove_series)
                sw.changed.connect(lambda: self.data_changed.emit())

                # Restore selection state
                sw.label_edit.setText(sel.get("label", f"Series {i+1}"))

                # X column
                x_col = sel.get("x_col")
                if x_col:
                    idx = sw.x_combo.findText(x_col)
                    if idx >= 0:
                        sw.x_combo.setCurrentIndex(idx)

                # Check if replicate mode
                if sel.get("replicate_cols"):
                    sw.mode_combo.setCurrentIndex(1)  # Replicate mode
                    # Select replicate columns
                    for c in sel["replicate_cols"]:
                        for j in range(sw.rep_list.count()):
                            if sw.rep_list.item(j).text() == c:
                                sw.rep_list.item(j).setSelected(True)
                    # Set central and error type
                    sw.central_combo.setCurrentText(sel.get("central", "Mean"))
                    sw.error_combo.setCurrentText(sel.get("error_type", "SD"))
                else:
                    sw.mode_combo.setCurrentIndex(0)  # Single column mode
                    # Y column
                    y_col = sel.get("y_col")
                    if y_col:
                        idx = sw.y_combo.findText(y_col)
                        if idx >= 0:
                            sw.y_combo.setCurrentIndex(idx)
                    # Y error column
                    yerr_col = sel.get("yerr_col")
                    if yerr_col:
                        idx = sw.yerr_combo.findText(yerr_col)
                        if idx >= 0:
                            sw.yerr_combo.setCurrentIndex(idx)

                insert_pos = self.series_vlayout.count() - 1
                self.series_vlayout.insertWidget(insert_pos, sw)
                self.series_widgets.append(sw)
        else:
            # No selections saved, create default
            if len(imported_cols) >= 2:
                self._add_series_with_columns(imported_cols, 0)

        self.data_changed.emit()
