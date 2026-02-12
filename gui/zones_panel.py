"""
Zones Panel - UI for managing highlight zones/bands on plots.

Allows users to:
- Add horizontal bands, vertical bands, or rectangular regions
- Customize appearance (color, alpha, border)
- Add labels with positioning options
- Manage multiple zones (add, edit, remove, reorder)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, QCheckBox,
    QGroupBox, QListWidget, QListWidgetItem, QColorDialog,
    QFormLayout, QScrollArea, QFrame, QMessageBox, QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

from core.zones_manager import (
    Zone, ZonesConfig, ZoneType, LabelPosition, ZONE_COLORS, create_preset_zone
)


class ColorButton(QPushButton):
    """A button that shows and allows selection of a color."""

    color_changed = pyqtSignal(str)

    def __init__(self, color: str = "#339AF0", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 24)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        # Calculate text color based on background brightness
        qc = QColor(self._color)
        brightness = (qc.red() * 299 + qc.green() * 587 + qc.blue() * 114) / 1000
        text_color = "white" if brightness < 128 else "black"
        self.setStyleSheet(
            f"background-color: {self._color}; color: {text_color}; "
            f"border: 1px solid #888; border-radius: 3px;"
        )
        self.setText(self._color[:7])

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Select Color")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._update_style()


class ZoneEditorWidget(QWidget):
    """Widget for editing a single zone's properties."""

    zone_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Zone name...")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Zone Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Horizontal Band", "Vertical Band", "Rectangle"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Bounds Group
        bounds_group = QGroupBox("Bounds")
        bounds_layout = QFormLayout(bounds_group)

        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-1e9, 1e9)
        self.x_min_spin.setDecimals(4)
        self.x_min_spin.setSpecialValueText("Auto")

        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-1e9, 1e9)
        self.x_max_spin.setDecimals(4)
        self.x_max_spin.setSpecialValueText("Auto")

        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(-1e9, 1e9)
        self.y_min_spin.setDecimals(4)
        self.y_min_spin.setSpecialValueText("Auto")

        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(-1e9, 1e9)
        self.y_max_spin.setDecimals(4)
        self.y_max_spin.setSpecialValueText("Auto")

        bounds_layout.addRow("X min:", self.x_min_spin)
        bounds_layout.addRow("X max:", self.x_max_spin)
        bounds_layout.addRow("Y min:", self.y_min_spin)
        bounds_layout.addRow("Y max:", self.y_max_spin)
        layout.addWidget(bounds_group)

        # Appearance Group
        appear_group = QGroupBox("Appearance")
        appear_layout = QFormLayout(appear_group)

        # Fill color
        color_layout = QHBoxLayout()
        self.fill_color_btn = ColorButton("#339AF0")
        color_layout.addWidget(self.fill_color_btn)

        self.color_preset_combo = QComboBox()
        self.color_preset_combo.addItems(list(ZONE_COLORS.keys()))
        self.color_preset_combo.currentTextChanged.connect(self._on_color_preset)
        color_layout.addWidget(self.color_preset_combo)
        appear_layout.addRow("Fill Color:", color_layout)

        # Alpha
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setValue(0.2)
        appear_layout.addRow("Opacity:", self.alpha_spin)

        # Edge color
        self.edge_color_btn = ColorButton("#1971C2")
        appear_layout.addRow("Edge Color:", self.edge_color_btn)

        # Edge width
        self.edge_width_spin = QDoubleSpinBox()
        self.edge_width_spin.setRange(0.0, 5.0)
        self.edge_width_spin.setSingleStep(0.5)
        self.edge_width_spin.setValue(1.0)
        appear_layout.addRow("Edge Width:", self.edge_width_spin)

        # Edge style
        self.edge_style_combo = QComboBox()
        self.edge_style_combo.addItems(["Solid (-)", "Dashed (--)", "Dotted (:)", "Dash-dot (-.)"])
        appear_layout.addRow("Edge Style:", self.edge_style_combo)

        layout.addWidget(appear_group)

        # Label Group
        label_group = QGroupBox("Label")
        label_layout = QFormLayout(label_group)

        self.show_label_check = QCheckBox()
        self.show_label_check.setChecked(True)
        label_layout.addRow("Show Label:", self.show_label_check)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Zone label text...")
        label_layout.addRow("Text:", self.label_edit)

        self.label_pos_combo = QComboBox()
        self.label_pos_combo.addItems([
            "Top Left", "Top Center", "Top Right",
            "Center", "Left", "Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ])
        self.label_pos_combo.setCurrentText("Top Center")
        label_layout.addRow("Position:", self.label_pos_combo)

        self.label_fontsize_spin = QSpinBox()
        self.label_fontsize_spin.setRange(6, 24)
        self.label_fontsize_spin.setValue(10)
        label_layout.addRow("Font Size:", self.label_fontsize_spin)

        self.label_color_btn = ColorButton("#000000")
        label_layout.addRow("Text Color:", self.label_color_btn)

        layout.addWidget(label_group)

        # Visible checkbox
        self.visible_check = QCheckBox("Visible")
        self.visible_check.setChecked(True)
        layout.addWidget(self.visible_check)

        layout.addStretch()

    def _connect_signals(self):
        self.name_edit.textChanged.connect(self._emit_change)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self.x_min_spin.valueChanged.connect(self._emit_change)
        self.x_max_spin.valueChanged.connect(self._emit_change)
        self.y_min_spin.valueChanged.connect(self._emit_change)
        self.y_max_spin.valueChanged.connect(self._emit_change)
        self.fill_color_btn.color_changed.connect(self._emit_change)
        self.alpha_spin.valueChanged.connect(self._emit_change)
        self.edge_color_btn.color_changed.connect(self._emit_change)
        self.edge_width_spin.valueChanged.connect(self._emit_change)
        self.edge_style_combo.currentIndexChanged.connect(self._emit_change)
        self.show_label_check.stateChanged.connect(self._emit_change)
        self.label_edit.textChanged.connect(self._emit_change)
        self.label_pos_combo.currentIndexChanged.connect(self._emit_change)
        self.label_fontsize_spin.valueChanged.connect(self._emit_change)
        self.label_color_btn.color_changed.connect(self._emit_change)
        self.visible_check.stateChanged.connect(self._emit_change)

    def _emit_change(self):
        self.zone_changed.emit()

    def _on_type_changed(self, index):
        # Enable/disable bounds based on zone type
        zone_type = ["horizontal", "vertical", "rectangle"][index]
        self.x_min_spin.setEnabled(zone_type in ("vertical", "rectangle"))
        self.x_max_spin.setEnabled(zone_type in ("vertical", "rectangle"))
        self.y_min_spin.setEnabled(zone_type in ("horizontal", "rectangle"))
        self.y_max_spin.setEnabled(zone_type in ("horizontal", "rectangle"))
        self._emit_change()

    def _on_color_preset(self, preset_name: str):
        if preset_name in ZONE_COLORS:
            self.fill_color_btn.set_color(ZONE_COLORS[preset_name])
            self._emit_change()

    def get_zone(self) -> Zone:
        """Get the current zone configuration."""
        type_map = {0: "horizontal", 1: "vertical", 2: "rectangle"}
        style_map = {0: "-", 1: "--", 2: ":", 3: "-."}
        pos_map = {
            0: "top_left", 1: "top_center", 2: "top_right",
            3: "center", 4: "left", 5: "right",
            6: "bottom_left", 7: "bottom_center", 8: "bottom_right",
        }

        zone_type = type_map.get(self.type_combo.currentIndex(), "horizontal")

        return Zone(
            name=self.name_edit.text() or "Zone",
            zone_type=zone_type,
            x_min=self.x_min_spin.value() if self.x_min_spin.isEnabled() else None,
            x_max=self.x_max_spin.value() if self.x_max_spin.isEnabled() else None,
            y_min=self.y_min_spin.value() if self.y_min_spin.isEnabled() else None,
            y_max=self.y_max_spin.value() if self.y_max_spin.isEnabled() else None,
            color=self.fill_color_btn.get_color(),
            alpha=self.alpha_spin.value(),
            edge_color=self.edge_color_btn.get_color(),
            edge_width=self.edge_width_spin.value(),
            edge_style=style_map.get(self.edge_style_combo.currentIndex(), "-"),
            label=self.label_edit.text(),
            label_position=pos_map.get(self.label_pos_combo.currentIndex(), "top_center"),
            label_fontsize=self.label_fontsize_spin.value(),
            label_color=self.label_color_btn.get_color(),
            show_label=self.show_label_check.isChecked(),
            visible=self.visible_check.isChecked(),
        )

    def set_zone(self, zone: Zone):
        """Set the editor to display a zone's properties."""
        # Block signals during update
        self.blockSignals(True)

        self.name_edit.setText(zone.name)

        type_idx = {"horizontal": 0, "vertical": 1, "rectangle": 2}.get(zone.zone_type, 0)
        self.type_combo.setCurrentIndex(type_idx)
        self._on_type_changed(type_idx)  # Update enabled state

        if zone.x_min is not None:
            self.x_min_spin.setValue(zone.x_min)
        if zone.x_max is not None:
            self.x_max_spin.setValue(zone.x_max)
        if zone.y_min is not None:
            self.y_min_spin.setValue(zone.y_min)
        if zone.y_max is not None:
            self.y_max_spin.setValue(zone.y_max)

        self.fill_color_btn.set_color(zone.color)
        self.alpha_spin.setValue(zone.alpha)
        self.edge_color_btn.set_color(zone.edge_color)
        self.edge_width_spin.setValue(zone.edge_width)

        style_idx = {"-": 0, "--": 1, ":": 2, "-.": 3}.get(zone.edge_style, 0)
        self.edge_style_combo.setCurrentIndex(style_idx)

        self.show_label_check.setChecked(zone.show_label)
        self.label_edit.setText(zone.label)

        pos_idx = {
            "top_left": 0, "top_center": 1, "top_right": 2,
            "center": 3, "left": 4, "right": 5,
            "bottom_left": 6, "bottom_center": 7, "bottom_right": 8,
        }.get(zone.label_position, 1)
        self.label_pos_combo.setCurrentIndex(pos_idx)

        self.label_fontsize_spin.setValue(zone.label_fontsize)
        self.label_color_btn.set_color(zone.label_color)
        self.visible_check.setChecked(zone.visible)

        self.blockSignals(False)


class ZonesPanel(QWidget):
    """
    Panel for managing all zones on a figure.

    Features:
    - List of zones with add/remove/reorder
    - Editor for selected zone
    - Preset templates
    """

    zones_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zones_config = ZonesConfig()
        self._current_index = -1
        self._updating = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Zones list
        list_group = QGroupBox("Zones")
        list_layout = QVBoxLayout(list_group)

        self.zones_list = QListWidget()
        self.zones_list.currentRowChanged.connect(self._on_zone_selected)
        list_layout.addWidget(self.zones_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("+ Add")
        self.add_btn.clicked.connect(self._on_add_zone)
        btn_layout.addWidget(self.add_btn)

        self.add_preset_combo = QComboBox()
        self.add_preset_combo.addItem("Add Preset...")
        self.add_preset_combo.addItems([
            "Safe Zone", "Danger Zone", "Target Range",
            "Baseline", "Highlight X", "Region of Interest"
        ])
        self.add_preset_combo.currentIndexChanged.connect(self._on_add_preset)
        btn_layout.addWidget(self.add_preset_combo)

        self.remove_btn = QPushButton("- Remove")
        self.remove_btn.clicked.connect(self._on_remove_zone)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)

        list_layout.addLayout(btn_layout)

        # Move up/down
        move_layout = QHBoxLayout()
        self.up_btn = QPushButton("▲ Up")
        self.up_btn.clicked.connect(self._on_move_up)
        self.up_btn.setEnabled(False)
        move_layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("▼ Down")
        self.down_btn.clicked.connect(self._on_move_down)
        self.down_btn.setEnabled(False)
        move_layout.addWidget(self.down_btn)

        list_layout.addLayout(move_layout)

        layout.addWidget(list_group)

        # Zone editor (in scroll area)
        editor_group = QGroupBox("Zone Properties")
        editor_layout = QVBoxLayout(editor_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.editor = ZoneEditorWidget()
        self.editor.zone_changed.connect(self._on_editor_changed)
        scroll.setWidget(self.editor)

        editor_layout.addWidget(scroll)
        layout.addWidget(editor_group, stretch=1)

        # Initially disable editor
        self.editor.setEnabled(False)

    def _refresh_list(self):
        """Refresh the zones list."""
        self._updating = True
        current = self.zones_list.currentRow()
        self.zones_list.clear()

        for zone in self._zones_config.get_all_zones():
            icon = "━" if zone.zone_type == "horizontal" else \
                   "┃" if zone.zone_type == "vertical" else "▢"
            vis = "" if zone.visible else " (hidden)"
            item = QListWidgetItem(f"{icon} {zone.name}{vis}")
            item.setToolTip(f"{zone.zone_type.title()}: {zone.label or 'No label'}")
            self.zones_list.addItem(item)

        if 0 <= current < self.zones_list.count():
            self.zones_list.setCurrentRow(current)
        elif self.zones_list.count() > 0:
            self.zones_list.setCurrentRow(0)

        self._updating = False
        self._update_buttons()

    def _update_buttons(self):
        has_selection = self.zones_list.currentRow() >= 0
        count = self.zones_list.count()
        current = self.zones_list.currentRow()

        self.remove_btn.setEnabled(has_selection)
        self.up_btn.setEnabled(has_selection and current > 0)
        self.down_btn.setEnabled(has_selection and current < count - 1)
        self.editor.setEnabled(has_selection)

    def _on_zone_selected(self, row: int):
        if self._updating:
            return

        self._current_index = row
        self._update_buttons()

        if row >= 0:
            zone = self._zones_config.get_zone(row)
            if zone:
                self._updating = True
                self.editor.set_zone(zone)
                self._updating = False

    def _on_editor_changed(self):
        if self._updating or self._current_index < 0:
            return

        zone = self.editor.get_zone()
        self._zones_config.update_zone(self._current_index, zone)
        self._refresh_list()
        self.zones_changed.emit()

    def _on_add_zone(self):
        # Create a new default zone
        idx = len(self._zones_config.zones) + 1
        zone = Zone(
            name=f"Zone {idx}",
            zone_type="horizontal",
            y_min=0,
            y_max=1,
        )
        self._zones_config.add_zone(zone)
        self._refresh_list()
        self.zones_list.setCurrentRow(len(self._zones_config.zones) - 1)
        self.zones_changed.emit()

    def _on_add_preset(self, index: int):
        if index == 0:  # "Add Preset..." placeholder
            return

        preset_map = {
            1: "safe_zone",
            2: "danger_zone",
            3: "target_range",
            4: "baseline",
            5: "highlight_x",
            6: "region_of_interest",
        }

        preset_name = preset_map.get(index)
        if preset_name:
            zone = create_preset_zone(preset_name)
            # Set some default bounds
            if zone.zone_type == "horizontal":
                zone.y_min = 0
                zone.y_max = 1
            elif zone.zone_type == "vertical":
                zone.x_min = 0
                zone.x_max = 1
            else:
                zone.x_min = 0
                zone.x_max = 1
                zone.y_min = 0
                zone.y_max = 1

            self._zones_config.add_zone(zone)
            self._refresh_list()
            self.zones_list.setCurrentRow(len(self._zones_config.zones) - 1)
            self.zones_changed.emit()

        # Reset combo to placeholder
        self.add_preset_combo.setCurrentIndex(0)

    def _on_remove_zone(self):
        if self._current_index < 0:
            return

        zone = self._zones_config.get_zone(self._current_index)
        if zone:
            reply = QMessageBox.question(
                self, "Remove Zone",
                f"Remove zone '{zone.name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._zones_config.remove_zone(self._current_index)
                self._current_index = -1
                self._refresh_list()
                self.zones_changed.emit()

    def _on_move_up(self):
        if self._current_index <= 0:
            return

        zones = self._zones_config.zones
        zones[self._current_index], zones[self._current_index - 1] = \
            zones[self._current_index - 1], zones[self._current_index]
        self._current_index -= 1
        self._refresh_list()
        self.zones_list.setCurrentRow(self._current_index)
        self.zones_changed.emit()

    def _on_move_down(self):
        if self._current_index < 0 or self._current_index >= len(self._zones_config.zones) - 1:
            return

        zones = self._zones_config.zones
        zones[self._current_index], zones[self._current_index + 1] = \
            zones[self._current_index + 1], zones[self._current_index]
        self._current_index += 1
        self._refresh_list()
        self.zones_list.setCurrentRow(self._current_index)
        self.zones_changed.emit()

    def get_zones_config(self) -> dict:
        """Get zones configuration as dict."""
        return self._zones_config.to_dict()

    def set_zones_config(self, config: dict):
        """Set zones configuration from dict."""
        self._zones_config = ZonesConfig.from_dict(config)
        self._current_index = -1
        self._refresh_list()

    def get_visible_zones(self) -> list[Zone]:
        """Get list of visible Zone objects."""
        return self._zones_config.get_visible_zones()

    def clear_zones(self):
        """Clear all zones."""
        self._zones_config.clear()
        self._current_index = -1
        self._refresh_list()
        self.zones_changed.emit()
