"""
Annotations panel — add text labels, arrows, and reference lines to plots.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QGroupBox, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox, QColorDialog,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from core.annotations_manager import Annotation, ANNOTATION_TYPES, LINE_STYLES


class AnnotationsPanel(QWidget):
    """Panel for managing plot annotations."""

    annotations_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._annotations: list[Annotation] = []
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Annotation list
        list_group = QGroupBox("Annotations")
        list_layout = QVBoxLayout(list_group)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("+ Add")
        self.add_btn.clicked.connect(self._add_annotation)
        btn_row.addWidget(self.add_btn)
        self.remove_btn = QPushButton("- Remove")
        self.remove_btn.clicked.connect(self._remove_annotation)
        btn_row.addWidget(self.remove_btn)
        btn_row.addStretch()
        list_layout.addLayout(btn_row)

        self.ann_list = QListWidget()
        self.ann_list.setMaximumHeight(120)
        self.ann_list.currentRowChanged.connect(self._on_select)
        list_layout.addWidget(self.ann_list)
        layout.addWidget(list_group)

        # Edit group
        edit_group = QGroupBox("Properties")
        edit_layout = QFormLayout(edit_group)

        self.type_combo = QComboBox()
        self.type_combo.addItems(ANNOTATION_TYPES)
        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        edit_layout.addRow("Type:", self.type_combo)

        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Annotation text")
        self.text_edit.textChanged.connect(self._on_prop_change)
        edit_layout.addRow("Text:", self.text_edit)

        # Position
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-1e6, 1e6)
        self.x_spin.setDecimals(3)
        self.x_spin.valueChanged.connect(self._on_prop_change)
        edit_layout.addRow("X:", self.x_spin)

        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-1e6, 1e6)
        self.y_spin.setDecimals(3)
        self.y_spin.valueChanged.connect(self._on_prop_change)
        edit_layout.addRow("Y:", self.y_spin)

        # Arrow end / line value
        self.x2_spin = QDoubleSpinBox()
        self.x2_spin.setRange(-1e6, 1e6)
        self.x2_spin.setDecimals(3)
        self.x2_spin.valueChanged.connect(self._on_prop_change)
        self.x2_label = QLabel("Arrow X2:")
        edit_layout.addRow(self.x2_label, self.x2_spin)

        self.y2_spin = QDoubleSpinBox()
        self.y2_spin.setRange(-1e6, 1e6)
        self.y2_spin.setDecimals(3)
        self.y2_spin.valueChanged.connect(self._on_prop_change)
        self.y2_label = QLabel("Arrow Y2:")
        edit_layout.addRow(self.y2_label, self.y2_spin)

        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(-1e6, 1e6)
        self.value_spin.setDecimals(3)
        self.value_spin.valueChanged.connect(self._on_prop_change)
        self.value_label = QLabel("Value:")
        edit_layout.addRow(self.value_label, self.value_spin)

        # Style
        self.font_spin = QSpinBox()
        self.font_spin.setRange(6, 36)
        self.font_spin.setValue(10)
        self.font_spin.valueChanged.connect(self._on_prop_change)
        edit_layout.addRow("Font size:", self.font_spin)

        self.lw_spin = QDoubleSpinBox()
        self.lw_spin.setRange(0.3, 5.0)
        self.lw_spin.setSingleStep(0.25)
        self.lw_spin.setValue(1.0)
        self.lw_spin.valueChanged.connect(self._on_prop_change)
        edit_layout.addRow("Line width:", self.lw_spin)

        self.ls_combo = QComboBox()
        self.ls_combo.addItems(list(LINE_STYLES.keys()))
        self.ls_combo.currentIndexChanged.connect(self._on_prop_change)
        edit_layout.addRow("Line style:", self.ls_combo)

        self.color_btn = QPushButton("")
        self.color_btn.setFixedSize(60, 24)
        self._color = "#000000"
        self.color_btn.setStyleSheet(f"background: {self._color};")
        self.color_btn.clicked.connect(self._pick_color)
        edit_layout.addRow("Color:", self.color_btn)

        self.visible_check = QCheckBox("Visible")
        self.visible_check.setChecked(True)
        self.visible_check.toggled.connect(self._on_prop_change)
        edit_layout.addRow(self.visible_check)

        layout.addWidget(edit_group)
        layout.addStretch()

        self._on_type_change()

    def _add_annotation(self):
        ann = Annotation(ann_type=self.type_combo.currentText(), text="Label")
        self._annotations.append(ann)
        self._refresh_list()
        self.ann_list.setCurrentRow(len(self._annotations) - 1)
        self.annotations_changed.emit()

    def _remove_annotation(self):
        row = self.ann_list.currentRow()
        if 0 <= row < len(self._annotations):
            self._annotations.pop(row)
            self._refresh_list()
            self.annotations_changed.emit()

    def _refresh_list(self):
        self.ann_list.clear()
        for ann in self._annotations:
            if ann.ann_type in ("H-Line", "V-Line"):
                label = f"{ann.ann_type} @ {ann.value:.2f}"
            elif ann.ann_type == "Arrow":
                label = f"Arrow: {ann.text}"
            else:
                label = f"Text: {ann.text}"
            if ann.text:
                label += f" ({ann.text[:20]})" if ann.ann_type != "Text" else ""
            self.ann_list.addItem(label)

    def _on_select(self, row):
        if row < 0 or row >= len(self._annotations):
            return
        self._updating = True
        ann = self._annotations[row]
        self.type_combo.setCurrentText(ann.ann_type)
        self.text_edit.setText(ann.text)
        self.x_spin.setValue(ann.x)
        self.y_spin.setValue(ann.y)
        self.x2_spin.setValue(ann.x2)
        self.y2_spin.setValue(ann.y2)
        self.value_spin.setValue(ann.value)
        self.font_spin.setValue(ann.font_size)
        self.lw_spin.setValue(ann.line_width)
        self.ls_combo.setCurrentText(ann.line_style)
        self._color = ann.color
        self.color_btn.setStyleSheet(f"background: {self._color};")
        self.visible_check.setChecked(ann.visible)
        self._updating = False
        self._on_type_change()

    def _on_type_change(self):
        t = self.type_combo.currentText()
        is_text = t == "Text"
        is_arrow = t == "Arrow"
        is_line = t in ("H-Line", "V-Line")

        self.text_edit.setVisible(is_text or is_arrow)
        self.x_spin.setVisible(is_text or is_arrow)
        self.y_spin.setVisible(is_text or is_arrow)
        self.x2_spin.setVisible(is_arrow)
        self.x2_label.setVisible(is_arrow)
        self.y2_spin.setVisible(is_arrow)
        self.y2_label.setVisible(is_arrow)
        self.value_spin.setVisible(is_line)
        self.value_label.setVisible(is_line)
        self.font_spin.setVisible(is_text or is_arrow)

        if not self._updating:
            self._on_prop_change()

    def _on_prop_change(self):
        if self._updating:
            return
        row = self.ann_list.currentRow()
        if row < 0 or row >= len(self._annotations):
            return
        ann = self._annotations[row]
        ann.ann_type = self.type_combo.currentText()
        ann.text = self.text_edit.text()
        ann.x = self.x_spin.value()
        ann.y = self.y_spin.value()
        ann.x2 = self.x2_spin.value()
        ann.y2 = self.y2_spin.value()
        ann.value = self.value_spin.value()
        ann.font_size = self.font_spin.value()
        ann.line_width = self.lw_spin.value()
        ann.line_style = self.ls_combo.currentText()
        ann.color = self._color
        ann.visible = self.visible_check.isChecked()
        self._refresh_list()
        self.ann_list.setCurrentRow(row)
        self.annotations_changed.emit()

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self.color_btn.setStyleSheet(f"background: {self._color};")
            self._on_prop_change()

    def get_annotations(self) -> list[Annotation]:
        return [a for a in self._annotations if a.visible]

    def get_all_annotations(self) -> list[Annotation]:
        return list(self._annotations)

    def get_annotations_config(self) -> list[dict]:
        return [a.to_dict() for a in self._annotations]

    def set_annotations_config(self, config: list[dict]):
        self._annotations = [Annotation.from_dict(d) for d in config]
        self._refresh_list()
        if self._annotations:
            self.ann_list.setCurrentRow(0)
